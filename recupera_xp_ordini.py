"""Recupera gli XP-ordine del pregresso: gli affari VERI chiusi prima
che il gancio degli XP esistesse (gamification parte 3, ago 2026).

Il registro `xp_eventi` e' append-only e non ha mai avuto una passata
retroattiva — a differenza dei distintivi, che si ricalcolano. Ma gli
XP d'ordine SONO ricostruibili in modo deterministico: `ordini` porta
il totale in cassaforte e il cambio, e il riferimento
`ordine:{id}:{ruolo}` con la sua UNIQUE rende la passata idempotente
per costruzione.

IL PERIMETRO E' DERIVATO, CON LA LISTA COME GUARDIA: «released,
`prova=0`, zero eventi» dopo marca_prove.py deve dare ESATTAMENTE gli
id passati sulla riga di comando — se ne trova altri, o gliene manca
uno, si ferma dicendolo invece di scrivere su righe che nessuno ha
guardato. Per lo stesso motivo VA LANCIATO DOPO marca_prove.py:
girato prima, regalerebbe XP proprio agli ordini di collaudo.

IL CAMBIO, in ordine di onesta': `cambio_eur` (la chiusura — lo
stesso che il gancio vivo avrebbe usato), poi `cambio_ordine` (la
creazione: un fatto REGISTRATO di pochi giorni prima), e dove
mancano tutti e due restano i soli punti fissi — la regola dichiarata
della formula, «meglio 10 che un numero inventato». MAI il cambio di
oggi. La FORMULA e le sue costanti si leggono dal TESTO di server.py
(la lezione di ricategorizza.py: mai importarlo, farebbe partire
init_db) — se non si trovano ci si ferma, mai numeri a memoria.

La data dell'evento e' `ordini.aggiornato`: sui `released` e' il
momento dello sblocco (il nascondere non la tocca, l'ha messo per
iscritto), cioe' quando il gancio vivo avrebbe scritto.

Anteprima di serie; `--scrivi` per farla; un percorso di database
come primo argomento per la prova generale su una copia.

    python recupera_xp_ordini.py [percorso.db] ID [ID...] [--scrivi]
"""

import re
import sqlite3
import sys
from pathlib import Path


def estrai_costanti(testo):
    """FISSO_XP_ORDINE, XP_PER_EURO e XP_RUOLO dal testo di server.py.
    Fail-closed: se una manca si alza, perche' scrivere punti con
    costanti sbagliate e' peggio di non scriverli."""
    fisso = re.search(r"^FISSO_XP_ORDINE\s*=\s*(\d+)", testo, re.M)
    per_euro = re.search(r"^XP_PER_EURO\s*=\s*(\d+)", testo, re.M)
    ruoli = re.search(
        r'^XP_RUOLO\s*=\s*\{"venditore":\s*([\d.]+),\s*'
        r'"compratore":\s*([\d.]+)\}', testo, re.M)
    if not (fisso and per_euro and ruoli):
        raise RuntimeError("costanti XP non trovate in server.py")
    return {"fisso": int(fisso.group(1)),
            "per_euro": int(per_euro.group(1)),
            "ruoli": {"venditore": float(ruoli.group(1)),
                      "compratore": float(ruoli.group(2))}}


def punti_ordine(prezzo_sats, cambio, ruolo, cost):
    """La formula di xp_ordine, coi numeri estratti dal server."""
    euro = (prezzo_sats / 100_000_000 * cambio) if cambio > 0 else 0.0
    return int((cost["fisso"] + euro * cost["per_euro"])
               * cost["ruoli"][ruolo])


def perimetro(con):
    """Gli ordini che il gancio vivo non ha mai visto: released, non
    prova, zero eventi. E' la domanda da cui la guardia deriva."""
    return [r["id"] for r in con.execute(
        "SELECT id FROM ordini o WHERE stato='released' AND prova=0 "
        "AND NOT EXISTS (SELECT 1 FROM xp_eventi x WHERE "
        "x.tipo='ordine' AND x.riferimento IN "
        "('ordine:'||o.id||':venditore','ordine:'||o.id||':compratore'))"
        " ORDER BY id")]


def recupera(con, attesi, cost):
    """Il cuore, importabile e provabile: scrive nella transazione del
    chiamante. Ritorna il rapporto, o None se il perimetro derivato
    non combacia con la lista attesa (si ferma dicendolo)."""
    derivati = perimetro(con)
    if sorted(derivati) != sorted(attesi):
        print(f"✗ il perimetro derivato non combacia con la lista:\n"
              f"    derivato: {derivati}\n"
              f"    atteso:   {sorted(attesi)}\n"
              f"  mi fermo senza scrivere — o manca marca_prove.py, "
              f"o c'e' un ordine che nessuno ha guardato")
        return None
    rapporto = {"eventi": 0, "utenti": set()}
    for oid in derivati:
        o = con.execute("SELECT * FROM ordini WHERE id=?",
                        (oid,)).fetchone()
        cambio, fonte = 0.0, "nessuno → solo i punti fissi"
        if o["cambio_eur"] and o["cambio_eur"] > 0:
            cambio, fonte = o["cambio_eur"], "chiusura (cambio_eur)"
        elif o["cambio_ordine"] and o["cambio_ordine"] > 0:
            cambio, fonte = o["cambio_ordine"], "creazione (cambio_ordine)"
        print(f"• ordine {oid} — {o['prezzo_sats']} sats, "
              f"cambio {cambio or '—'} [{fonte}]")
        for tg, ruolo in ((o["venditore_id"], "venditore"),
                          (o["compratore_id"], "compratore")):
            p = punti_ordine(o["prezzo_sats"], cambio, ruolo, cost)
            print(f"    + {p} XP a #{tg} ({ruolo})")
            r = con.execute(
                "INSERT OR IGNORE INTO xp_eventi"
                "(tg_id, tipo, punti, riferimento, creato) "
                "VALUES(?,?,?,?,?)",
                (tg, "ordine", p, f"ordine:{oid}:{ruolo}",
                 o["aggiornato"] or o["creato"] or 0))
            rapporto["eventi"] += r.rowcount
            rapporto["utenti"].add(tg)
    for tg in sorted(rapporto["utenti"]):
        # SOLO IL COMMERCIO, come `_ricalcola_xp` e come il
        # riallineamento d'avvio: senza il filtro questo UPDATE
        # rimetterebbe dentro i punti di presenza, e il riavvio dopo
        # li ritoglierebbe. Il perimetro vero e' XP_COMMERCIO in
        # server.py; qui si ricopia perche' lo script gira da solo,
        # e a tenerli in pari c'e' una prova.
        # E DAL SET 2026 CON LA REGOLA DEGLI INVITI (`xp_contati`): i
        # propri piu' le quote, queste mai oltre i propri. Il pregresso
        # NON fa nascere quote — erano accrediti di prima degli inviti —
        # ma chi ne ha gia' non deve vedersele sparire dalla cache.
        propri, inviti = con.execute(
            "SELECT COALESCE(SUM(CASE WHEN tipo IN ('ordine') "
            "THEN punti END),0), COALESCE(SUM(CASE WHEN tipo='invito' "
            "THEN punti END),0) FROM xp_eventi WHERE tg_id=?",
            (tg,)).fetchone()
        con.execute("UPDATE utenti SET xp=? WHERE tg_id=?",
                    (propri + min(inviti, propri), tg))
    return rapporto


def main():
    argv = sys.argv[1:]
    scrivi = "--scrivi" in argv
    argv = [a for a in argv if a != "--scrivi"]
    db = "satmarket.db"
    if argv and not argv[0].isdigit():
        db, argv = argv[0], argv[1:]
    attesi = [int(a) for a in argv]
    if not attesi:
        print(__doc__)
        return 2
    try:
        cost = estrai_costanti(
            Path(__file__).with_name("server.py").read_text(
                encoding="utf-8"))
    except Exception as e:
        print(f"✗ {e} — mi fermo, mai punti a memoria")
        return 1
    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(db, timeout=15)
    con.row_factory = sqlite3.Row
    colonne = {r[1] for r in con.execute("PRAGMA table_info(ordini)")}
    if "prova" not in colonne:
        print("✗ manca la colonna ordini.prova: prima il deploy, "
              "poi marca_prove.py, poi questo")
        return 1
    print("ANTEPRIMA — nessuna scrittura (aggiungi --scrivi)\n"
          if not scrivi else "SCRITTURA VERA\n")
    print(f"Formula dal server: fissi {cost['fisso']}, "
          f"{cost['per_euro']} XP/€, ruoli {cost['ruoli']}\n")
    r = recupera(con, attesi, cost)
    if r is None:
        con.rollback()
        return 1
    if scrivi:
        con.commit()
        print(f"\nFatto: {r['eventi']} eventi scritti per "
              f"{len(r['utenti'])} utenti. Ora `classifica_prova.py` "
              f"per il prima/dopo.")
    else:
        con.rollback()
        print(f"\nAnteprima: {r['eventi']} eventi da scrivere per "
              f"{len(r['utenti'])} utenti.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
