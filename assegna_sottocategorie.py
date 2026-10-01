# -*- coding: utf-8 -*-
"""La passata del giudice silenzioso sugli annunci ESISTENTI, e la
misura della colonna quando la si vuole guardare.

Il giudice delle sottocategorie (vedi SINONIMI_SOTTOCATEGORIA in
server.py) lavora da solo sui flussi nuovi — pubblica, modifica, gli
import. Questo script copre il pregresso e fa da termometro:

    python assegna_sottocategorie.py            # ANTEPRIMA: cosa farebbe
    python assegna_sottocategorie.py --scrivi   # lo fa
    python assegna_sottocategorie.py --conta    # la misura: assegnate,
                                                # vuote, e DOVE il giudice
                                                # si astiene di piu'

Regole:
- tocca solo le righe con sottocategoria VUOTA (un valore scritto non
  si rigiudica mai) negli stati attivo, revisione e venduto — il
  venduto puo' tornare in vendita con la ricarica;
- il giudice si astiene = la riga resta '', mai un errore;
- idempotente: rilanciarlo dopo aver arricchito il dizionario riempie
  solo i buchi nuovi coperti. Niente coda admin, ed e' deciso: il dato
  non esce da nessuna parte finche' l'albero non si accende, e
  correggerlo allora costera' un rilancio.
- accetta un percorso di database (la prova generale si fa su una
  COPIA, come per ripulisci_anello_nostr.py); senza, usa quello del
  config, con ripiego su satmarket.db.

Il giudice si legge dal TESTO di server.py, senza importarlo: la
lezione di ricategorizza.py — l'import farebbe partire init_db e
le migrazioni, e il config verrebbe preteso anche in CI dove non
esiste per progetto."""
import os
import re
import sqlite3
import sys
import unicodedata

QUI = os.path.dirname(os.path.abspath(__file__))


def _pezzo(src: str, nome: str) -> str:
    i = src.index(f"def {nome}(")
    return src[i:src.index("\n\n\n", i)]


def _blocco(src: str, testa: str) -> str:
    i = src.index(testa)
    return src[i:src.index("\n}", i) + 2]


def carica_giudice():
    src = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
    amb = {"re": re, "unicodedata": unicodedata}
    exec(_pezzo(src, "normalizza"), amb)
    exec(_blocco(src, "SOTTOCATEGORIE = {"), amb)
    exec(_blocco(src, "SINONIMI_SOTTOCATEGORIA = {"), amb)
    exec(_pezzo(src, "_parola_sottocategoria"), amb)
    exec(_pezzo(src, "sottocategoria_indovina"), amb)
    return amb


STATI = ("attivo", "revisione", "venduto")


def main():
    argv = sys.argv[1:]
    scrivi = "--scrivi" in argv
    conta = "--conta" in argv
    percorsi = [a for a in argv if not a.startswith("--")]
    if percorsi:
        db_path = percorsi[0]
    else:
        try:
            from config import DB as db_path
        except ImportError:
            db_path = "satmarket.db"
    if not os.path.exists(db_path):
        print(f"database non trovato: {db_path}")
        return 1

    amb = carica_giudice()
    giudica = amb["sottocategoria_indovina"]
    etichette = {sid: nome for voci in amb["SOTTOCATEGORIE"].values()
                 for sid, nome in voci}

    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(db_path, timeout=15)
    con.row_factory = sqlite3.Row
    segna = ",".join("?" * len(STATI))

    if conta:
        # --- il termometro: com'e' messa la colonna ADESSO ----------
        # SOLO gli attivi (ago 2026, da un caso vero: sul VPS il conto
        # a tre stati pescava i venduti delle prove di rodaggio —
        # «Test», «Prova» — e il termometro misurava fantasmi). La
        # PASSATA invece tiene anche revisione e venduto: un venduto
        # puo' tornare in vendita con la ricarica, e assegnarli non
        # sporca nessuna misura.
        righe = con.execute(
            "SELECT categoria, sottocategoria, titolo FROM annunci "
            "WHERE stato='attivo'").fetchall()
        con.close()
        per_cat = {}
        for r in righe:
            tot, piene, esempi = per_cat.setdefault(r["categoria"],
                                                    [0, 0, []])
            per_cat[r["categoria"]][0] += 1
            if r["sottocategoria"]:
                per_cat[r["categoria"]][1] += 1
            elif len(per_cat[r["categoria"]][2]) < 5:
                per_cat[r["categoria"]][2].append(r["titolo"])
        tot = sum(v[0] for v in per_cat.values())
        piene = sum(v[1] for v in per_cat.values())
        print(f"{tot} annunci ATTIVI (la vetrina vera): "
              f"{piene} con sottocategoria, {tot - piene} vuote"
              + (f" ({piene * 100 // tot}%)" if tot else ""))
        print("\nle astensioni, dalla categoria che ne ha di piu' — e' "
              "QUI che si legge dove il dizionario va arricchito:")
        for cat, (n, p, esempi) in sorted(per_cat.items(),
                                          key=lambda kv: kv[1][1] - kv[1][0]):
            if n == p:
                continue
            print(f"  {cat}: {n - p} vuote su {n}")
            for t in esempi:
                print(f"      · {t[:64]}")
        return 0

    # --- la passata: anteprima di serie, --scrivi per farla ---------
    righe = con.execute(
        f"SELECT id, categoria, titolo, descrizione FROM annunci "
        f"WHERE sottocategoria='' AND stato IN ({segna})",
        STATI).fetchall()
    assegnate, astenute = [], 0
    for r in righe:
        sotto = giudica(r["categoria"], r["titolo"], r["descrizione"] or "")
        if sotto:
            assegnate.append((r["id"], r["categoria"], r["titolo"], sotto))
        else:
            astenute += 1
    for aid, cat, titolo, sotto in assegnate:
        print(f"  #{aid} [{cat}] {titolo[:48]:50s} -> "
              f"{etichette.get(sotto, sotto)}")
        if scrivi:
            # condizionato sul vuoto: se nel frattempo qualcuno ha
            # scritto (un payload, il giro d'import), si rispetta
            con.execute("UPDATE annunci SET sottocategoria=? "
                        "WHERE id=? AND sottocategoria=''", (sotto, aid))
    if scrivi:
        con.commit()
    con.close()
    print(f"\n{len(assegnate)} da assegnare, {astenute} astensioni "
          f"(restano vuote), su {len(righe)} righe senza sottocategoria")
    if assegnate and not scrivi:
        print("niente e' stato scritto: rilancia con --scrivi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
