# -*- coding: utf-8 -*-
"""
RIFAI LE MINIATURE — la passata a mano per le gemelle _min.jpg nate con
una ricetta PIU' GRANDE di quella di oggi (19 ott 2026, cantiere
miniature-leggere).

PERCHE' SERVE: la ricetta e' scesa da 640 q87 (~160KB in produzione) a
480 q82 (`MINIATURA_LATO`/`MINIATURA_QUALITA` in server.py, coi conti).
Il backfill d'avvio, `genera_miniature_mancanti`, rifa' solo le
miniature PIU' PICCOLE della ricetta: quando la ricetta cresce e' lui a
pensarci, quando cala le vecchie restano buone — solo piu' pesanti — e
le rifa' questo script, quando lo decide Andrea.

COSA TOCCA: SOLO i file *_min.jpg di foto/ che hanno accanto il loro
pieno e il lato piu' grande della ricetta di oggi. Salta i francobolli
che non sono foto di annunci (av_, pod_, neg_, ban_: la stessa lista del
backfill). L'ORIGINALE SI LEGGE E BASTA: non si apre mai in scrittura.
Il database non si tocca: nel database c'e' solo il nome pieno.

COME SCRIVE: la miniatura nuova si scrive in un file temporaneo nella
stessa cartella, coi permessi della vecchia, e poi `os.replace` la mette
al suo posto in un colpo: chi la chiede in quell'istante riceve la
vecchia o la nuova, mai un file a meta'. Se la nuova non pesa meno della
vecchia, si tiene la vecchia.

LA RICETTA E' QUELLA DEL SERVER, non una copia: lo script legge
server.py accanto a se' e ne esegue `miniatura_jpeg` con le sue costanti
(e la guardia `_foto_anomala`). Se non le trova, si ferma senza scrivere.

USO (sul VPS, dall'utente del servizio: un file nato da root in foto/
il servizio non lo sa piu' riscrivere):
    cd /srv/barattolo && sudo -u barattolo python3 rifai_miniature.py --prova
    cd /srv/barattolo && sudo -u barattolo python3 rifai_miniature.py --davvero
--prova calcola tutto in memoria e dice quante e quanti KB prima/dopo,
senza scrivere un byte. Idempotente: rilanciato a lavoro fatto non
trova piu' niente. Si puo' girare a server acceso.
"""
import io
import os
import sys
import tempfile
import threading
import warnings

QUI = os.path.dirname(os.path.abspath(__file__))
FOTO_DIR = os.path.join(QUI, "foto")
SALTA = ("av_", "pod_", "neg_", "ban_")

# la console di Windows e le emoji: vedi ripulisci_avatar_min.py
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, OSError):
    pass


def _pezzo(sorgente: str, inizio: str) -> str:
    """Dal testo `inizio` alla prima riga doppia vuota: lo stesso taglio
    di `pezzo` in prove.py."""
    i = sorgente.index(inizio)
    return sorgente[i:sorgente.index("\n\n\n", i)]


def ricetta(percorso_server=None) -> dict:
    """Le funzioni e le costanti della miniatura, prese da server.py."""
    from PIL import Image, ImageOps
    sorgente = open(percorso_server or os.path.join(QUI, "server.py"),
                    encoding="utf-8").read()
    amb = {"io": io, "threading": threading, "warnings": warnings,
           "ImmaginePillow": Image, "ImageOps": ImageOps}
    for inizio in ("MINIATURA_LATO = ", "TETTO_PIXEL_FOTO = ",
                   "def _foto_anomala(", "def miniatura_jpeg("):
        exec(_pezzo(sorgente, inizio), amb)
    # la stessa guardia del server contro le bombe di pixel
    Image.MAX_IMAGE_PIXELS = amb["TETTO_PIXEL_FOTO"]
    warnings.simplefilter("error", Image.DecompressionBombWarning)
    return amb


def da_rifare(nome: str) -> bool:
    return (nome.endswith("_min.jpg") and not nome.startswith(SALTA)
            and not nome.startswith("."))


def main(argv=None, foto_dir=None, percorso_server=None):
    argv = sys.argv[1:] if argv is None else argv
    davvero = "--davvero" in argv
    if davvero == ("--prova" in argv):
        print("uso: rifai_miniature.py --prova | --davvero")
        return 2
    foto_dir = foto_dir or FOTO_DIR
    if not os.path.isdir(foto_dir):
        print(f"cartella non trovata: {foto_dir}")
        return 1
    try:
        r = ricetta(percorso_server)
    except Exception as e:
        print(f"⛔ la ricetta del server non si legge ({type(e).__name__}: "
              f"{e}): non si scrive niente")
        return 1
    from PIL import Image
    lato_ricetta = r["MINIATURA_LATO"]
    print(f"ricetta del server: {lato_ricetta} px, qualita' "
          f"{r['MINIATURA_QUALITA']}"
          + ("" if davvero else " — PROVA, non si scrive niente"))

    rifatte, gia_buone, orfane, saltate = 0, 0, [], []
    prima, dopo = 0, 0
    for nome in sorted(os.listdir(foto_dir)):
        if not da_rifare(nome):
            continue
        p_min = os.path.join(foto_dir, nome)
        p_pieno = os.path.join(foto_dir, nome[:-len("_min.jpg")] + ".jpg")
        if not os.path.exists(p_pieno):
            orfane.append(nome)
            continue
        try:
            with Image.open(p_min) as img:
                lato_ora = max(img.size)
        except Exception as e:
            saltate.append(f"{nome}: la miniatura non si apre ({e})")
            continue
        if lato_ora <= lato_ricetta:
            gia_buone += 1
            continue
        try:
            with open(p_pieno, "rb") as f:
                nuova = r["miniatura_jpeg"](f.read())
        except OSError as e:
            saltate.append(f"{nome}: l'originale non si legge ({e})")
            continue
        vecchia = os.path.getsize(p_min)
        if not nuova:
            saltate.append(f"{nome}: la ricetta non la sa rifare")
            continue
        if len(nuova) >= vecchia:
            saltate.append(f"{nome}: la nuova non pesa meno, resta la vecchia")
            continue
        if davvero:
            # appena prima di scrivere: se nel frattempo l'annuncio ha
            # cambiato foto, la coppia non c'e' piu' e non si ricrea
            if not (os.path.exists(p_pieno) and os.path.exists(p_min)):
                saltate.append(f"{nome}: sparita mentre la rifacevo")
                continue
            fd, tmp = tempfile.mkstemp(dir=foto_dir, prefix=".rifai_",
                                       suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as out:
                    out.write(nuova)
                    out.flush()
                    os.fsync(out.fileno())
                os.chmod(tmp, os.stat(p_min).st_mode & 0o777)
                os.replace(tmp, p_min)
            except OSError as e:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                saltate.append(f"{nome}: non scritta ({e})")
                continue
        rifatte += 1
        prima += vecchia
        dopo += len(nuova)

    verbo = "rifatte" if davvero else "da rifare"
    print(f"\n{rifatte} miniature {verbo}: {prima // 1024} KB → "
          f"{dopo // 1024} KB"
          + (f" (risparmio {(prima - dopo) // 1024} KB)" if rifatte else ""))
    print(f"{gia_buone} gia' alla ricetta di oggi o piu' piccole: lasciate")
    for nome in orfane:
        print(f"· lasciata {nome}: il suo originale non c'e'")
    for riga in saltate:
        print(f"⚠️ {riga}")
    if rifatte and not davvero:
        print("niente e' stato scritto: rilancia con --davvero")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
