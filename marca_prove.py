"""Marca come PROVA gli ordini di collaudo fatti in produzione.

Gli ordini di prova (luglio 2026, cifre piccole, titoli «Prova»/«Test»)
sono ordini `released` VERI per il database — sats mossi davvero su
LNbits — ma non sono commercio: nella classifica pubblica fanno
curriculum e rendono «reali» dei recensori che reali non sono.

NON si cancellano, si MARCANO (`ordini.prova=1`), ed e' la decisione
che regge tutto: la riconciliazione con LNbits incrocia i suoi incassi
coi payment_hash di queste righe, e un DELETE fabbricherebbe proprio
gli orfani che quel metodo esiste per trovare. Il CSV contabile li
tiene; a saltarli sono i lettori del COMMERCIO (classifica,
distintivi), che dal deploy guardano `prova=0`.

Cosa fa, per ogni id passato IN LISTA ESPLICITA (mai un'euristica sui
titoli — a decidere cos'e' una prova e' Andrea, non una regex):
  1. timbra `prova=1` (solo su `released`: altro si ferma dicendolo);
  2. toglie gli eventi XP `ordine:{id}:{ruolo}` — e dal set 2026 le
     quote d'invito nate da loro, `invito:{chi}:ordine:{id}:{ruolo}` —
     e ricalcola la cache `utenti.xp` dei coinvolti e di chi ha perso
     una quota;
  3. decrementa `vendite_ok`/`acquisti_ok` delle due parti — sono
     contatori INCREMENTALI, nessun ricalcolo li rimette in pari da
     solo — mai sotto zero, e SOLO quando il timbro passa davvero da
     0 a 1 (il secondo giro e' un no-op: idempotente);
  4. ELENCA i feedback su quegli ordini senza toccarli: si tolgono
     con la valvola admin (/api/admin/feedback/{id}/rimuovi), che
     ricalcola rating e recensori da sola;
  5. stampa i distintivi dei coinvolti coi conteggi rifatti senza le
     prove: quali badge togliere e' una decisione a mano (sono
     append-only per regola), qui si danno solo i numeri.

Anteprima di serie; `--scrivi` per farla davvero; un percorso di
database come primo argomento per la prova generale su una copia
(il pattern di ripulisci_anello_nostr.py).

    python marca_prove.py [percorso.db] ID [ID...] [--scrivi]
"""

import sqlite3
import sys
from datetime import datetime, timezone


def _giorno(ts):
    if not ts:
        return "?"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _nome(con, tg_id):
    r = con.execute("SELECT nome FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    return (r["nome"] if r and r["nome"] else f"#{tg_id}")


def marca(con, ids):
    """Il cuore, importabile e provabile: marca gli ordini nella
    transazione del chiamante (nessun commit qui). Ritorna il
    rapporto; su un id fuori perimetro ritorna None SENZA aver
    scritto niente — si ferma dicendolo, mai a meta'."""
    rapporto = {"marcati": [], "saltati": [], "xp_tolti": 0,
                "feedback": [], "utenti": set(), "invitanti": set()}
    ordini = []
    for oid in ids:
        o = con.execute("SELECT * FROM ordini WHERE id=?",
                        (oid,)).fetchone()
        if not o:
            print(f"✗ ordine {oid}: NON ESISTE — mi fermo, "
                  f"nessuna scrittura")
            return None
        if o["stato"] != "released":
            print(f"✗ ordine {oid}: stato '{o['stato']}', non "
                  f"'released' — mi fermo, nessuna scrittura")
            return None
        ordini.append(o)

    for o in ordini:
        oid = o["id"]
        v, c = o["venditore_id"], o["compratore_id"]
        rapporto["utenti"].update((v, c))
        if o["prova"]:
            print(f"= ordine {oid}: gia' marcato, non tocco niente")
            rapporto["saltati"].append(oid)
            continue
        refs = (f"ordine:{oid}:venditore", f"ordine:{oid}:compratore")
        eventi = list(con.execute(
            "SELECT tg_id, punti, riferimento FROM xp_eventi "
            "WHERE tipo='ordine' AND riferimento IN (?,?)", refs))
        # LE QUOTE NATE DA QUESTI XP (set 2026, i codici invito): chi
        # aveva invitato una delle due parti ha preso il 5% di questi
        # accrediti, e un collaudo non e' commercio nemmeno di riflesso.
        # Il riferimento della quota porta dentro quello dell'accredito
        # (`invito:{chi}:ordine:{id}:{ruolo}`), quindi si trovano per
        # nome esatto, senza LIKE.
        # E DAL SET 2026 ANCHE LE ACCANTONATE ('invito_attesa'), le quote
        # in attesa dei tre invitati attivi: un collaudo non deve poter
        # arrivare nemmeno il giorno del rilascio.
        refs_quote = (f"invito:{v}:{refs[0]}", f"invito:{c}:{refs[1]}")
        quote = list(con.execute(
            "SELECT tg_id, punti, riferimento FROM xp_eventi "
            "WHERE tipo IN ('invito','invito_attesa') "
            "AND riferimento IN (?,?)", refs_quote))
        fb = list(con.execute(
            "SELECT id, da_tg_id, per_tg_id, voto FROM feedback "
            "WHERE ordine_id=?", (oid,)))
        print(f"• ordine {oid} — {_giorno(o['creato'])}, "
              f"{o['prezzo_sats']} sats, "
              f"{_nome(con, v)} → {_nome(con, c)}"
              + (" [AUTO]" if v == c else ""))
        for e in eventi:
            print(f"    − XP: {e['punti']} a {_nome(con, e['tg_id'])} "
                  f"({e['riferimento']})")
        for q in quote:
            print(f"    − quota d'invito: {q['punti']} a "
                  f"{_nome(con, q['tg_id'])} ({q['riferimento']})")
        for f in fb:
            print(f"    ⭐ feedback #{f['id']}: {f['voto']}/5 da "
                  f"{_nome(con, f['da_tg_id'])} a "
                  f"{_nome(con, f['per_tg_id'])} — DA TOGLIERE con la "
                  f"valvola admin")
            rapporto["feedback"].append(f["id"])
        con.execute("UPDATE ordini SET prova=1 WHERE id=?", (oid,))
        con.execute("DELETE FROM xp_eventi WHERE tipo='ordine' "
                    "AND riferimento IN (?,?)", refs)
        con.execute("DELETE FROM xp_eventi WHERE tipo IN "
                    "('invito','invito_attesa') AND riferimento IN (?,?)",
                    refs_quote)
        rapporto["invitanti"].update(q["tg_id"] for q in quote)
        # Il decremento vive SOLO nel giro in cui il timbro passa
        # 0→1: cosi' il secondo lancio non toglie due volte.
        con.execute("UPDATE utenti SET vendite_ok=MAX(0, vendite_ok-1) "
                    "WHERE tg_id=?", (v,))
        con.execute("UPDATE utenti SET acquisti_ok=MAX(0, acquisti_ok-1) "
                    "WHERE tg_id=?", (c,))
        rapporto["marcati"].append(oid)
        rapporto["xp_tolti"] += len(eventi) + len(quote)

    # La cache degli XP si RIFA' dal registro (la ricetta di
    # _ricalcola_xp: mai un -=, che a meta' strada mentirebbe) — per le
    # parti E per chi ha perso una quota.
    for tg in sorted(rapporto["utenti"] | rapporto["invitanti"]):
        # SOLO IL COMMERCIO, come `_ricalcola_xp` e come il
        # riallineamento d'avvio: senza il filtro questo UPDATE
        # rimetterebbe dentro i punti di presenza, e il riavvio dopo
        # li ritoglierebbe. Il perimetro vero e' XP_COMMERCIO in
        # server.py; qui si ricopia perche' lo script gira da solo,
        # e a tenerli in pari c'e' una prova.
        # E DAL SET 2026 CON LA REGOLA DEGLI INVITI (`xp_contati`): i
        # propri piu' le quote, queste mai oltre i propri. Una somma nuda
        # direbbe un altro numero da quello del server, e il riavvio dopo
        # lo correggerebbe — un numero che oscilla attraverso un reboot.
        propri, inviti = con.execute(
            "SELECT COALESCE(SUM(CASE WHEN tipo IN ('ordine') "
            "THEN punti END),0), COALESCE(SUM(CASE WHEN tipo='invito' "
            "THEN punti END),0) FROM xp_eventi WHERE tg_id=?",
            (tg,)).fetchone()
        con.execute("UPDATE utenti SET xp=? WHERE tg_id=?",
                    (propri + min(inviti, propri), tg))

    # I distintivi sono append-only («non si revocano mai»): qui i
    # NUMERI rifatti senza le prove, la decisione resta a mano.
    print("\nDistintivi dei coinvolti (conteggi senza le prove — "
          "toglierli e' una decisione a mano):")
    for tg in sorted(rapporto["utenti"]):
        badge = [r["badge_id"] for r in con.execute(
            "SELECT badge_id FROM badge_utente WHERE tg_id=?", (tg,))]
        vv = con.execute(
            "SELECT COUNT(*) AS n FROM ordini WHERE venditore_id=? "
            "AND stato='released' AND prova=0", (tg,)).fetchone()["n"]
        aa = con.execute(
            "SELECT COUNT(*) AS n FROM ordini WHERE compratore_id=? "
            "AND stato='released' AND prova=0", (tg,)).fetchone()["n"]
        print(f"  {_nome(con, tg)}: vendite vere {vv}, acquisti veri "
              f"{aa}, badge: {', '.join(badge) or 'nessuno'}")
    return rapporto


def main():
    argv = sys.argv[1:]
    scrivi = "--scrivi" in argv
    argv = [a for a in argv if a != "--scrivi"]
    db = "satmarket.db"
    if argv and not argv[0].isdigit():
        db, argv = argv[0], argv[1:]
    ids = [int(a) for a in argv]
    if not ids:
        print(__doc__)
        return 2
    # il database e' quello VIVO, e il server ci scrive mentre giriamo:
    # quindici secondi di pazienza sul lucchetto, come `db()` (ott 2026)
    con = sqlite3.connect(db, timeout=15)
    con.row_factory = sqlite3.Row
    colonne = {r[1] for r in con.execute("PRAGMA table_info(ordini)")}
    if "prova" not in colonne:
        print("✗ manca la colonna ordini.prova: prima il deploy "
              "(la migrazione gira all'avvio del server)")
        return 1
    print("ANTEPRIMA — nessuna scrittura (aggiungi --scrivi)\n"
          if not scrivi else "SCRITTURA VERA\n")
    r = marca(con, ids)
    if r is None:
        con.rollback()
        return 1
    if scrivi:
        con.commit()
        print(f"\nFatto: {len(r['marcati'])} marcati, "
              f"{r['xp_tolti']} eventi XP tolti, "
              f"{len(r['feedback'])} feedback da togliere a mano.")
    else:
        con.rollback()
        print(f"\nAnteprima: {len(r['marcati'])} da marcare, "
              f"{r['xp_tolti']} eventi XP da togliere, "
              f"{len(r['feedback'])} feedback da valvola admin.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
