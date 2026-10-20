#!/usr/bin/env python3
"""LA COPIA DEL DATABASE, UNA SOLA PER TUTTI I BACKUP (20 ott 2026,
cantiere «backup-database-occupato»).

Il 20 ott, nel deploy delle 15:07, la copia locale di deploy.sh e' riuscita
e un attimo dopo quella di backup-fuori.sh e' caduta con «Error: database
is locked»: il comando `sqlite3` aspetta ZERO secondi, e il nostro database
(rollback journal, niente WAL) per l'istante di un commit del server chiude
la porta a chi legge. Il python di deploy.sh invece riprovava da solo, ma
SENZA un tetto, e la copia non la controllava nessuno.

Qui, una volta per tutti (deploy, giornaliero, LNbits):
  - l'API di backup di sqlite in UN passo solo (`pages=-1`): tutta la copia
    dentro una lettura sola, quindi consistente anche a server acceso;
  - un'attesa vera sul lucchetto (`busy_timeout`, 30 s) e poi altri giri,
    ma con un TETTO (90 s): passato quello si rinuncia e lo si dice;
  - la copia nasce come `<destinazione>.parziale` e prende il suo nome solo
    se e' finita: un file a meta' non si scambia mai per un backup;
  - `PRAGMA integrity_check` sulla COPIA, non sul vivo: non tiene il
    lucchetto del server, e l'API copia le pagine tali e quali, quindi un
    database rotto da' una copia rotta e il controllo lo vede.

Uso:  copia-db.py <sorgente> <destinazione> [--anche-scrittura]
                  [--tetto=SECONDI] [--attesa=SECONDI]
Stampa UNA riga su stdout, ed esce con:
  0  copia fatta e integra
  3  copia fatta ma NON integra (il file resta: e' la prova del guasto)
  4  database occupato oltre il tetto: nessuna copia
  1  copia non riuscita per un altro motivo (file che non si apre, rotto
     nella testata, disco...): nessuna copia
(2 lo usa python stesso quando lo script manca: chi chiama lo legge come
«non riuscita».)

La sorgente si apre in SOLA LETTURA (`mode=ro`, come la copia di deploy.sh
da sempre): un backup non scrive mai il file vivo. `--anche-scrittura` e'
per LNbits, il cui database non e' nostro: un `mode=ro` su un WAL senza
`-shm` puo' dire «unable to open» (Cantieri, «IL WAL, VALUTATO E NON
ACCESO»), e il `sqlite3` di prima lo apriva in scrittura.

`--tetto=` e `--attesa=` (20 ott 2026, cantiere backup-ritocchi) le
stringono per un giro solo: la copia di LNbits PRIMA DEL DEPLOY sta dentro
i 120 s dell'archivio, e non puo' prenderseli tutti lei. L'attesa non
supera mai il tetto: un passo bloccato aspetta al piu' quella, quindi il
giro intero sta sotto tetto + attesa. Dall'ambiente le misure si
spostano solo per il banco di prove.py.
"""
import os
import sqlite3
import sys
import time

ATTESA = float(os.environ.get("BARATTOLO_COPIA_ATTESA", "30"))  # busy_timeout
TETTO = float(os.environ.get("BARATTOLO_COPIA_TETTO", "90"))    # poi si rinuncia


# i codici di sqlite per «la porta e' chiusa»: scritti a mano, cosi' non
# dipendono dalla versione di python della macchina
OCCUPATO = (5, 6)    # SQLITE_BUSY, SQLITE_LOCKED


class Occupato(Exception):
    pass


def copia(sorgente, destinazione, anche_scrittura=False, tetto=None,
          attesa=None):
    """(codice, riga) — vedi in cima."""
    tetto = TETTO if tetto is None else tetto
    attesa = min(ATTESA if attesa is None else attesa, tetto)
    parziale = destinazione + ".parziale"
    try:
        os.remove(parziale)
    except FileNotFoundError:
        pass
    if not os.path.isfile(sorgente):
        return 1, f"non riuscita: {sorgente} non c'e'"
    inizio = time.monotonic()

    def guarda_il_tetto(stato, restano, totale):
        # CPython chiama qui dopo OGNI passo, anche quelli finiti in
        # BUSY/LOCKED (poi dorme 250 ms e riprova): e' il solo punto da
        # cui si puo' fermare un giro che altrimenti non finirebbe mai.
        if stato in OCCUPATO and time.monotonic() - inizio > tetto:
            raise Occupato()

    src = dst = None
    try:
        uri = f"file:{sorgente}" + ("" if anche_scrittura else "?mode=ro")
        src = sqlite3.connect(uri, uri=True, timeout=attesa)
        dst = sqlite3.connect(parziale)
        src.backup(dst, pages=-1, progress=guarda_il_tetto)
        dst.close()
        dst = None
    except Occupato:
        return 4, (f"occupato: il database e' rimasto bloccato per piu' di "
                   f"{int(time.monotonic() - inizio)} s")
    except sqlite3.OperationalError as e:
        if "locked" in str(e) or "busy" in str(e):
            return 4, (f"occupato: {e} (dopo "
                       f"{int(time.monotonic() - inizio)} s)")
        return 1, f"non riuscita: {e}"
    except Exception as e:
        return 1, f"non riuscita: {type(e).__name__}: {e}"
    finally:
        for c in (dst, src):
            if c is not None:
                try:
                    c.close()
                except Exception:
                    pass
    # la copia c'e': ora il controllo, sulla copia
    try:
        c = sqlite3.connect(f"file:{parziale}?mode=ro", uri=True)
        try:
            righe = [r[0] for r in c.execute("PRAGMA integrity_check")]
        finally:
            c.close()
    except Exception as e:
        righe = [f"{type(e).__name__}: {e}"]
    os.replace(parziale, destinazione)
    if righe == ["ok"]:
        return 0, f"integra ({int(time.monotonic() - inizio)} s)"
    return 3, "non integra: " + " · ".join(str(r) for r in righe[:3])


def main(argv):
    pos = [a for a in argv if not a.startswith("--")]
    if len(pos) != 2:
        print("non riuscita: uso copia-db.py <sorgente> <destinazione>")
        return 1
    misure = {}
    for a in argv:
        for nome in ("tetto", "attesa"):
            if a.startswith(f"--{nome}="):
                try:
                    misure[nome] = float(a.split("=", 1)[1])
                except ValueError:
                    print(f"non riuscita: {a} non e' un numero")
                    return 1
    codice, riga = copia(pos[0], pos[1], "--anche-scrittura" in argv, **misure)
    if codice not in (0, 3):
        try:
            os.remove(pos[1] + ".parziale")
        except FileNotFoundError:
            pass
    print(riga.replace("\n", " "))
    return codice


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
