# -*- coding: utf-8 -*-
"""
SPOSTA A MANO — mette in coda gli spostamenti di categoria che decidi
tu, senza passare dall'AI (lug 2026).

A COSA SERVE: ricategorizza.py chiede a Haiku, e ogni tanto Haiku
sbaglia o dice NON SO. Quando sai gia' dove va un annuncio — anche di
un altro venditore — questo script scrive la proposta direttamente
nella coda dei moderatori, come se l'avesse proposta l'AI.

COSA NON FA, e non e' una dimenticanza: NON tocca annunci.categoria.
Lo spostamento vero resta uno solo — il bottone «✅ Sposta» della coda
nel Profilo — perche' e' li' che vivono l'UPDATE condizionato (il
secondo moderatore trova il fatto compiuto), l'aggiornamento
dell'evento NIP-99 e il registro di chi ha deciso cosa. Scriverlo una
seconda volta qui vorrebbe dire tenere allineati due posti che fanno
la stessa cosa, ed e' esattamente il tipo di doppione che prima o poi
diverge.

USO (dalla cartella del progetto):
    python sposta_a_mano.py "Cyberpunk=Bitcoin" "Telo d'Amare=Sport e hobby"
    python sposta_a_mano.py --scrivi "Cyberpunk=Bitcoin"
    python sposta_a_mano.py --scrivi "417=Bitcoin"      # per id, se lo sai

Ogni argomento e' `cosa=Categoria`. A sinistra un id numerico oppure
un pezzo di titolo (maiuscole e accenti non contano): un frammento che
pesca cinque poster mette in coda tutti e cinque, ed e' voluto. A
destra il nome ESATTO di una categoria del catalogo.

Di serie non scrive: stampa cosa metterebbe in coda, con id, titolo,
categoria di adesso e venditore — cosi' un frammento troppo largo si
vede PRIMA. Con --scrivi riempie la coda, e poi si approva dal
Profilo (le proposte escono raggruppate per spostamento).

Si puo' passare un percorso di database diverso da quello del config.
Idempotente: la coda ha una riga per annuncio, quindi rilanciarlo
riscrive la stessa proposta invece di aggiungerne un'altra.
"""

import os
import sqlite3
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

from ricategorizza import catalogo                     # noqa: E402

try:
    from config import DB
except ImportError:
    DB = "satmarket.db"


def main():
    scrivi = "--scrivi" in sys.argv
    voci, db = [], DB
    for a in sys.argv[1:]:
        if a.startswith("--"):
            continue
        if "=" in a:
            voci.append(a)
        else:
            db = a                       # percorso di database
    if not voci:
        print(__doc__)
        return 1

    cat = catalogo()
    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(db, timeout=15)
    con.row_factory = sqlite3.Row
    print(f"🗂  Spostamenti a mano — database {db}")
    print("   " + ("SCRIVO le proposte nella coda" if scrivi
                   else "prova a vuoto (--scrivi per riempire la coda)"))

    proposte, guai = {}, []
    for v in voci:
        chiave, _, nuova = v.rpartition("=")
        chiave, nuova = chiave.strip(), nuova.strip()
        if nuova not in cat:
            guai.append(f"«{nuova}» non e' una categoria del catalogo")
            continue
        if chiave.isdigit():
            righe = con.execute(
                "SELECT a.id, a.titolo, a.categoria, u.nome AS venditore "
                "FROM annunci a JOIN utenti u ON u.tg_id=a.venditore_id "
                "WHERE a.id=? AND a.stato='attivo'", (int(chiave),)).fetchall()
        else:
            righe = con.execute(
                "SELECT a.id, a.titolo, a.categoria, u.nome AS venditore "
                "FROM annunci a JOIN utenti u ON u.tg_id=a.venditore_id "
                "WHERE a.stato='attivo' AND a.titolo LIKE ? "
                "ORDER BY a.id", (f"%{chiave}%",)).fetchall()
        if not righe:
            guai.append(f"«{chiave}»: nessun annuncio attivo lo pesca")
            continue
        print(f"\n  «{chiave}» → {nuova}  ({len(righe)} trovati)")
        for r in righe:
            if r["categoria"] == nuova:
                print(f"    · #{r['id']} {r['titolo'][:52]} — c'e' gia'")
                continue
            print(f"    · #{r['id']} {r['categoria']} → {nuova}  "
                  f"{r['titolo'][:46]}  ({r['venditore']})")
            proposte[r["id"]] = (r["categoria"], nuova)

    for g in guai:
        print(f"\n  ⚠️ {g}")

    if scrivi and proposte:
        adesso = int(time.time())
        con.executemany(
            "INSERT INTO categoria_proposta(annuncio_id, categoria_ora, "
            "categoria_nuova, motivo, creato, stato, deciso_da, deciso_il) "
            "VALUES(?,?,?,'scelta a mano',?,'proposta',0,0) "
            "ON CONFLICT(annuncio_id) DO UPDATE SET "
            "categoria_ora=excluded.categoria_ora, "
            "categoria_nuova=excluded.categoria_nuova, "
            "motivo='scelta a mano', creato=excluded.creato, "
            "stato='proposta', deciso_da=0, deciso_il=0",
            [(i, ora, nuova, adesso) for i, (ora, nuova) in proposte.items()])
        con.commit()
        print(f"\n✅ {len(proposte)} proposte in coda. Ora aprile dal "
              f"Profilo → «🗂 Categorie da sistemare» e approvale: e' li' "
              f"che lo spostamento avviene davvero, con l'evento Nostr "
              f"che si aggiorna da se'.")
    elif proposte:
        print(f"\n({len(proposte)} pronte, ma non ho scritto niente. "
              f"--scrivi per metterle in coda)")
    else:
        print("\nNiente da mettere in coda.")
    con.close()
    return 1 if guai else 0


if __name__ == "__main__":
    sys.exit(main())
