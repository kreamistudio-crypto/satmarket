# -*- coding: utf-8 -*-
"""
CHI SCENDE, SE GLI XP CONTANO SOLO IL COMMERCIO (ago 2026, tappa 0 del
cantiere «gli XP sono solo commercio»).

Oggi `utenti.xp` e' la somma di TUTTO il registro `xp_eventi` — sette
tipi, di cui sei sono presenza: visita, pubblicazione, feedback
lasciato, Lightning address, npub, distintivo. La classifica invece
somma i soli `tipo='ordine'`, e da li' il disallineamento che ha aperto
il cantiere: 244 nel Profilo, 123 nel rank.

Quando gli XP conteranno il solo commercio, i numeri caleranno per
tutti — e insieme a loro si muovono TRE cose: il LIVELLO, i tre TITOLI
che chiedono un livello, e la PORTA del banner. Questo script dice chi
si muove PRIMA che si muova, e soprattutto dice fin dove si possono
abbassare le soglie senza far scendere nessuno.

LE SOGLIE SI TARANO SUI DATI VERI, ed e' quel che il roadmap chiede da
sempre: qui non si decide niente, si guardano i numeri. Le soglie di
oggi (150/600/2500/9000 XP) sono scritte per un mondo in cui meta' dei
punti veniva dalla presenza.

I GIUDICI NON VIVONO QUI: `LIVELLI`, `livello_utente`,
`_gradino_livello`, `banner_porta_aperta` e `TITOLI` si estraggono dal
TESTO di server.py — mai importando il modulo, che farebbe partire
init_db e le migrazioni (la lezione di ricategorizza.py). FAIL-CLOSED
(la lezione di recupera_xp_ordini.py): se qualcosa non si trova ci si
ferma, mai una scala a memoria.

IL PERIMETRO E' SCRITTO QUI A MANO (`tipo='ordine'`), come in
classifica_prova.py e per la stessa ragione: oggi nel server non ha
ancora un nome. Il giorno che ce l'ha — `XP_COMMERCIO` — questo script
lo legge da li', e la sentinella di prove.py lo incrocia.

LEGGE E BASTA: il database si apre in SOLA LETTURA (`mode=ro`), non
c'e' una sola INSERT/UPDATE/DELETE in tutto il file, e si puo'
lanciare a server acceso.

USO:   python livelli_prova.py [--id] [percorso/db]
       --id  stampa anche i tg_id (di serie no: quest'uscita finisce
             in chat, e un id non serve a decidere una soglia)
"""

import os
import re
import sys
import sqlite3


# ---------------------- i giudici, dal server ------------------------

def _leggi_server():
    """Estrae dal TESTO di server.py la scala, i suoi giudici e la leva
    del banner.

    La leva si risolve nell'ordine del server: il config vince, il
    default scritto nel codice e' il ripiego. Ritorna None se manca
    qualcosa: chi chiama si ferma."""
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

    def blocco(inizio):
        # fino alla riga vuota tripla, come fa prove.py per gli stessi
        # tre cataloghi: e' la forma con cui sono scritti
        i = src.find(inizio)
        if i < 0:
            return None
        j = src.find("\n\n\n", i)
        return src[i:j] if j > 0 else None

    amb = {}
    # COORTI prima di TITOLI: il catalogo dei titoli la usa dentro una
    # comprehension, e senza esplode invece di mancare
    for b in ("COORTI = [", "LIVELLI = [", "TITOLI = ("):
        testo = blocco(b)
        if not testo:
            return None
        try:
            exec(testo, amb)
        except Exception:
            return None
    for f in ("livello_utente", "_gradino_livello", "banner_porta_aperta"):
        testo = pezzo(f)
        if not testo:
            return None
        try:
            exec(testo, amb)
        except Exception:
            return None

    try:
        import config as _cfg
    except Exception:
        _cfg = None
    v = getattr(_cfg, "BANNER_LIVELLO", None) if _cfg else None
    fonte = "config"
    if v is None:
        m = re.search(r'BANNER_LIVELLO\s*=\s*"([a-z_]+)"', src)
        if not m:
            return None
        v, fonte = m.group(1), "codice"
    amb["BANNER_LIVELLO"] = v
    amb["_fonte_banner"] = fonte
    return amb


# ----------------------------- le letture ----------------------------

def leggi(con, amb):
    """Una riga per utente che abbia XP o affari, piu' il registro
    spaccato per tipo. Nient'altro.

    Gli AFFARI si contano da `vendite_ok`/`acquisti_ok` e NON dagli
    ordini, ed e' voluto: sono quelli che il server passa a
    `livello_utente` e a `banner_porta_aperta`, quindi sono quelli che
    decidono il gradino. (La classifica li conta dagli ordini, ma
    quella e' un'altra domanda.)"""
    try:
        per_tipo = [(r["tipo"], r["n"], r["p"]) for r in con.execute(
            "SELECT tipo, COUNT(*) AS n, COALESCE(SUM(punti),0) AS p "
            "FROM xp_eventi GROUP BY tipo ORDER BY p DESC")]
        xp_ord = {r["tg_id"]: r["p"] for r in con.execute(
            "SELECT tg_id, COALESCE(SUM(punti),0) AS p FROM xp_eventi "
            "WHERE tipo='ordine' GROUP BY tg_id")}
    except sqlite3.OperationalError:
        return None, None

    righe = []
    for u in con.execute("SELECT * FROM utenti"):
        campi = u.keys()
        xp_ora = u["xp"] or 0
        affari = (u["vendite_ok"] or 0) + (u["acquisti_ok"] or 0)
        if not xp_ora and not affari:
            continue        # non ha niente da dire: era nuovo, resta nuovo
        righe.append(dict(
            id=u["tg_id"],
            nome=(u["nome"] or "").strip() or "(senza nome)",
            xp_ora=xp_ora,
            xp_dopo=xp_ord.get(u["tg_id"], 0),
            affari=affari,
            titolo=(u["titolo"] or "") if "titolo" in campi else "",
            # un database di prima del banner non ha le sue colonne: la
            # porta si guarda lo stesso, semplicemente non ha pagato
            # nessuno (il ripiego di classifica_prova.py su `prova`)
            banner=(u["banner_stato"] or "") if "banner_stato" in campi else "",
            pagato=(u["banner_sbloccato_il"] or 0)
            if "banner_sbloccato_il" in campi else 0))
    return per_tipo, righe


def scomponi(righe, amb):
    """Il prima e il dopo di ogni riga: livello, porta, titolo."""
    liv = amb["livello_utente"]
    porta = amb["banner_porta_aperta"]
    grad = amb["_gradino_livello"]
    minimo = amb["BANNER_LIVELLO"]
    # I titoli che chiedono un LIVELLO, derivati dal catalogo e mai
    # scritti a mano: se un domani ne nasce un quarto, entra da solo
    tit_liv = {t["id"]: t["serve"][1] for t in amb["TITOLI"]
               if t["serve"][0] == "livello"}
    # e il NOME, che e' quel che l'utente vede addosso: un id come
    # `t_pratico` non dice a nessuno cosa sta per sparire
    nomi = {t["id"]: t["nome"] for t in amb["TITOLI"]}
    for r in righe:
        r["titolo_nome"] = nomi.get(r["titolo"], r["titolo"])
        r["liv_ora"] = liv(r["xp_ora"], r["affari"])
        r["liv_dopo"] = liv(r["xp_dopo"], r["affari"])
        r["scende"] = r["liv_dopo"]["numero"] < r["liv_ora"]["numero"]
        r["porta_ora"] = porta(r["xp_ora"], r["affari"], minimo, r["pagato"])
        r["porta_dopo"] = porta(r["xp_dopo"], r["affari"], minimo, r["pagato"])
        serve = tit_liv.get(r["titolo"], "")
        r["titolo_cade"] = bool(serve) and (
            grad(serve) > r["liv_dopo"]["numero"])
    return righe


# ------------------------------ le sezioni ---------------------------

def _nome(r, con_id):
    return f"{r['nome']} [{r['id']}]" if con_id else r["nome"]


def sezione_1(per_tipo):
    print("\n1. IL REGISTRO, PER TIPO -- cosa esce dal conto\n")
    if not per_tipo:
        print("   Registro vuoto: non c'e' niente da misurare.")
        return
    print(f"    {'tipo':<14} {'righe':>7} {'punti':>9}")
    dentro = fuori = 0
    for tipo, n, p in per_tipo:
        segno = "commercio" if tipo == "ordine" else "presenza"
        print(f"    {tipo:<14} {n:7d} {p:9d}   {segno}")
        if tipo == "ordine":
            dentro += p
        else:
            fuori += p
    print(f"\n    Restano nel conto (commercio): {dentro}")
    print(f"    Escono dal conto (presenza):   {fuori}")
    if dentro + fuori:
        print(f"    Cioe' il {fuori * 100 // (dentro + fuori)}% dei punti "
              f"di oggi non e' commercio.")
    print("\n    Le righe NON si cancellano: il registro e' append-only,")
    print("    a cambiare e' solo chi entra nella somma.")


def sezione_2(righe, con_id):
    print("\n\n2. CHI SI MUOVE\n")
    if not righe:
        print("   Nessuno ha XP o affari: non si muove niente.")
        return
    print(f"    {'nome':<22} {'xp ora':>7} {'xp dopo':>8} {'aff':>4}  "
          f"{'livello ora':<17} -> {'dopo':<17} note")
    for r in sorted(righe, key=lambda x: (-x["xp_ora"], x["id"])):
        note = []
        if r["scende"]:
            note.append("SCENDE")
        if r["porta_ora"] and not r["porta_dopo"]:
            note.append("perde la porta"
                        + (" (banner attivo)" if r["banner"] == "attivo" else ""))
        if r["titolo_cade"]:
            note.append(f"perde il titolo {r['titolo_nome']}")
        print(f"    {_nome(r, con_id):<22} {r['xp_ora']:7d} "
              f"{r['xp_dopo']:8d} {r['affari']:4d}  "
              f"{r['liv_ora']['nome']:<17} -> {r['liv_dopo']['nome']:<17} "
              + ", ".join(note))


def sezione_3(righe, amb):
    print("\n\n3. I GRADINI, PRIMA E DOPO\n")
    prima, dopo = {}, {}
    for r in righe:
        prima[r["liv_ora"]["nome"]] = prima.get(r["liv_ora"]["nome"], 0) + 1
        dopo[r["liv_dopo"]["nome"]] = dopo.get(r["liv_dopo"]["nome"], 0) + 1
    print(f"    {'gradino':<20} {'prima':>6} {'dopo':>6}")
    for l in amb["LIVELLI"]:
        print(f"    {l[3]:<20} {prima.get(l[3], 0):6d} {dopo.get(l[3], 0):6d}")
    scendono = sum(1 for r in righe if r["scende"])
    print(f"\n    Scendono di gradino: {scendono} su {len(righe)}.")


def sezione_4(righe, amb):
    """LA SEZIONE CHE SERVE A DECIDERE: fin dove si puo' abbassare una
    soglia senza far scendere nessuno.

    Solo l'asse XP si muove: gli affari non cambiano di un'unita',
    quindi le soglie-affari restano quelle che sono."""
    print("\n\n4. LE SOGLIE: fin dove si scende senza far scendere nessuno\n")
    print("    Il TETTO e' il minimo xp-commercio fra chi oggi sta a quel")
    print("    gradino o piu' su: con una soglia fino a li', nessuno perde")
    print("    il grado che ha adesso.\n")
    print(f"    {'gradino':<20} {'soglia ora':>10} {'tetto':>7}  quanti ci stanno")
    for n, l in enumerate(amb["LIVELLI"], 1):
        if n == 1:
            continue        # il primo gradino e' a zero per definizione
        dentro = [r for r in righe if r["liv_ora"]["numero"] >= n]
        if not dentro:
            print(f"    {l[3]:<20} {l[0]:10d} {'--':>7}  nessuno")
            continue
        tetto = min(r["xp_dopo"] for r in dentro)
        print(f"    {l[3]:<20} {l[0]:10d} {tetto:7d}  {len(dentro)}")
        if tetto < l[1] * 10:
            print(f"        ^ attenzione: con {tetto} quel gradino si"
                  f" prenderebbe quasi senza commercio.")
            print("          Qui «nessuno scende» non regge, e va accettato")
            print("          che qualcuno scenda.")
    print("\n    Per riferimento: un affare da venditore vale 10 punti fissi")
    print("    piu' un punto per euro; da compratore il 60%. Quindi una")
    print("    soglia di 100 e' circa 90 euro venduti, o dieci affari da 3.")


def sezione_5(righe, amb, con_id):
    print("\n\n5. COSA SI PERDE, E CHI VA AVVISATO\n")
    porta = [r for r in righe if r["porta_ora"] and not r["porta_dopo"]]
    titoli = [r for r in righe if r["titolo_cade"]]
    if not porta:
        print("    Nessuno perde la porta del banner.")
    else:
        print(f"    Perdono la porta del banner: {len(porta)}")
        print(f"    (livello richiesto: «{amb['BANNER_LIVELLO']}»)")
        for r in porta:
            stato = r["banner"] or "nessun banner"
            print(f"      - {_nome(r, con_id)}: {stato}")
        print("      L'insegna gia' approvata RESTA esposta: la porta serve")
        print("      a chiedere o cambiare un banner, non a mostrarlo. Ma")
        print("      il giorno che vogliono correggere il link, non possono.")
        print("      Chi ha PAGATO lo sblocco non e' in questo elenco.")
    print()
    if not titoli:
        print("    Nessuno perde il titolo che indossa.")
    else:
        print(f"    Perdono il titolo indossato: {len(titoli)}")
        for r in titoli:
            print(f"      - {_nome(r, con_id)}: {r['titolo_nome']}")
    quanti = len({r["id"] for r in righe if r["scende"]}
                 | {r["id"] for r in porta} | {r["id"] for r in titoli})
    print(f"\n    In tutto, persone che vedranno cambiare qualcosa: {quanti}")
    if quanti and quanti <= 5:
        print("    Poche: si avvisano a mano con «Scrivi a un utente».")
    elif quanti:
        print("    Tante: vale la campagna una-tantum col timbro in "
              "`timbri`,")
        print("    il calco di avvisa_sconto_su_mono.")


# ------------------------------- main --------------------------------

def main() -> int:
    args = sys.argv[1:]
    con_id = False
    if "--id" in args:
        con_id = True
        args.remove("--id")

    amb = _leggi_server()
    if amb is None:
        print("Non trovo la scala o i suoi giudici in server.py: mi fermo.")
        print("(fail-closed: mai una scala a memoria -- la lezione di "
              "recupera_xp_ordini.py)")
        return 2

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

    print(f"Livelli di prova su {db} -- sola lettura.")
    print(f"   (scala e giudici letti da server.py; porta del banner: "
          f"«{amb['BANNER_LIVELLO']}», dal {amb['_fonte_banner']})")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        per_tipo, righe = leggi(con, amb)
    finally:
        con.close()
    if righe is None:
        print("\nNessuna tabella xp_eventi: senza registro non c'e' niente")
        print("da misurare (il database e' piu' vecchio degli XP).")
        return 2

    scomponi(righe, amb)
    sezione_1(per_tipo)
    sezione_2(righe, con_id)
    sezione_3(righe, amb)
    sezione_4(righe, amb)
    sezione_5(righe, amb, con_id)
    print("\nNiente e' stato scritto: il database e' stato aperto in "
          "sola lettura.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
