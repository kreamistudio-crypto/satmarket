# -*- coding: utf-8 -*-
"""
RIPULISCI I _min DEGLI AVATAR — la spazzata una-tantum dei francobolli
gemelli che non sarebbero mai dovuti nascere (ago 2026).

COS'ERA SUCCESSO: genera_miniature_mancanti, la passata d'avvio che
da' una miniatura alle foto degli annunci, guardava OGNI .jpg della
cartella foto/ — e li' dentro ci sono anche i francobolli degli avatar,
che _salva_avatar scrive gia' a 128px. Siccome miniatura_jpeg non
ingrandisce mai, la "miniatura" usciva della STESSA misura: una copia.
Che per giunta nessuno chiede mai — il nome _min lo deriva solo
fotoMini, per le foto degli annunci, mentre avatarImg usa il nome
pieno. E _scrivi_avatar, cambiando foto profilo, cancellava il pieno
vecchio ma non la sua gemella: un file in piu' a ogni cambio.
In produzione erano 75 file su 688.

Il TAPPO e' gia' nel codice (la passata salta i nomi av_, e ora il
_min se ne va insieme al suo pieno): da li' in poi non se ne creano
di nuovi. Questo script si occupa di quelli gia' sul disco.

COSA FA: cancella da foto/ i file 'av_{negozio}_{ts}_min.jpg'. Nessuna
riga di database si tocca — quei nomi nel database non ci sono mai
stati, e' proprio questo il punto.

LA GUARDIA: prima di cancellare si legge la colonna utenti.avatar e
si controlla che nessuno di quei file sia la faccia di qualcuno. Se lo
fosse, lo si lascia stare e lo si dice: vorrebbe dire che da qualche
parte un _min ci e' finito davvero, e allora non e' una spazzatura ma
un dato.

Non e' un guasto che si vede: oggi nessuna immagine e' rotta, si
spreca solo spazio. Si puo' girare a server acceso — un file che non
chiede nessuno non manca a nessuno.

USO (dalla cartella del progetto):
    python ripulisci_avatar_min.py            # ANTEPRIMA: cosa farebbe
    python ripulisci_avatar_min.py --scrivi   # lo fa

Si puo' passare un percorso di database diverso da quello del config
(la cartella foto/ resta pero' quella del progetto: e' li' che stanno
i file veri). Idempotente: rilanciarlo a lavoro fatto non trova piu'
niente.
"""
import os
import re
import sqlite3
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
FOTO_DIR = os.path.join(QUI, "foto")

# Sul VPS la console e' UTF-8 e le emoji si vedono; su un terminale
# Windows no, e li' la ⚠️ della guardia faceva ESPLODERE lo script
# proprio nella riga piu' importante — l'unica che va letta per forza.
# Con 'replace' il carattere diventa un punto interrogativo e il
# messaggio arriva lo stesso.
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, OSError):
    pass

# La forma la scrive _salva_avatar, e questa e' la sua gemella: la
# stessa che NOME_FOTO ammette sulla rotta /foto (l'esadecimale viene
# da secrets.token_hex del codice negozio). Un av_...  che non
# combacia non si cancella: si dice e si lascia dov'e'.
AVATAR_MIN = re.compile(r"^av_[0-9a-f]+_\d+_min\.jpg\Z")


def main():
    argv = sys.argv[1:]
    scrivi = "--scrivi" in argv
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
    if not os.path.isdir(FOTO_DIR):
        print(f"cartella non trovata: {FOTO_DIR}")
        return 1

    # Le facce VERE, quelle che il database dice di servire: nessuna
    # dovrebbe essere un _min, ed e' quello che si va a verificare.
    con = sqlite3.connect(db_path)
    facce = {r[0] for r in con.execute(
        "SELECT avatar FROM utenti WHERE avatar!=''")}
    con.close()

    da_togliere, in_uso, strani, spazio = [], [], [], 0
    for nome in sorted(os.listdir(FOTO_DIR)):
        if not (nome.startswith("av_") and nome.endswith("_min.jpg")):
            continue
        if nome in facce:
            in_uso.append(nome)
        elif not AVATAR_MIN.match(nome):
            strani.append(nome)
        else:
            da_togliere.append(nome)
            try:
                spazio += os.path.getsize(os.path.join(FOTO_DIR, nome))
            except OSError:
                pass

    for nome in da_togliere:
        print(f"  {nome}")
        if scrivi:
            try:
                os.remove(os.path.join(FOTO_DIR, nome))
            except OSError as e:
                print(f"      ⚠️ non si e' riusciti a cancellarlo: {e}")

    print(f"\n{len(da_togliere)} francobolli gemelli inutili "
          f"({spazio // 1024} KB)")
    for nome in in_uso:
        print(f"⚠️ LASCIATO: {nome} e' la faccia di qualcuno nel "
              f"database — non e' spazzatura, va capito perche'")
    for nome in strani:
        print(f"· lasciato {nome}: non ha la forma di _salva_avatar")
    if da_togliere and not scrivi:
        print("niente e' stato cancellato: rilancia con --scrivi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
