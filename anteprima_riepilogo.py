#!/usr/bin/env python3
"""Guarda com'e' fatto il post del lunedi' PRIMA che parta.

I tre piu' venduti della settimana finiscono dentro i tre barattoli di
`assets/riepilogo-barattoli.png`, e i riquadri dei vetri sono numeri
che si GUARDANO, non si deducono: questo script compone l'immagine su
un file e basta — nessuna notifica, nessuna scrittura sul database,
nessun timbro consumato — cosi' si tara `VETRI_RIEPILOGO` aprendo un
PNG invece di aspettare lunedi'.

    python anteprima_riepilogo.py                # dai dati veri
    python anteprima_riepilogo.py --griglia      # coi riquadri disegnati
    python anteprima_riepilogo.py foto1.jpg foto2.jpg foto3.jpg
    python anteprima_riepilogo.py --db copia.db --fuori prova.jpg

LEGGE E BASTA (il patto di `stima_coda_moderazione.py`): si puo'
lanciare a server acceso.

IL GIUDICE SI LEGGE DAL TESTO di server.py e non si importa — l'import
farebbe partire init_db e le migrazioni su un database che magari non
e' quello che si voleva toccare, ed e' la lezione di
`ricategorizza.py`.
"""
import io
import json
import os
import re
import sqlite3
import sys

SORGENTE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "server.py"), encoding="utf-8").read()


def pezzo(nome: str) -> str:
    """Il corpo di una funzione di server.py, per testo (come in
    prove.py)."""
    m = re.search(rf"^def {nome}\(", SORGENTE, re.M)
    if not m:
        sys.exit(f"non trovo {nome} in server.py")
    i = m.start()
    j = SORGENTE.find("\n\n\n", i)
    return SORGENTE[i:j if j > 0 else len(SORGENTE)]


def carica():
    """Il pezzo di server.py che compone l'immagine, in un ambiente
    suo — con Pillow vero e le stampe di sempre."""
    from PIL import Image as ImmaginePillow
    from PIL import ImageOps, ImageDraw
    amb = {"io": io, "ImmaginePillow": ImmaginePillow,
           "ImageOps": ImageOps, "ImageDraw": ImageDraw, "print": print}
    i = SORGENTE.index("SFONDO_RIEPILOGO = ")
    exec(SORGENTE[i:SORGENTE.index("\n]", i) + 2], amb)
    exec(pezzo("_podio_su_sfondo"), amb)
    return amb


def foto_dal_db(percorso: str, amb) -> list:
    """Le foto dei tre piu' venduti della settimana vera. Sola
    lettura, e la stessa query del server."""
    con = sqlite3.connect(percorso)
    con.row_factory = sqlite3.Row
    amb2 = {"con": con}
    exec(pezzo("_conta_settimana"), amb2)
    import time
    nuovi, ordini, top = amb2["_conta_settimana"](
        con, int(time.time()) - 7 * 86400)
    print(f"📊 {nuovi} annunci, {ordini} ordini, {len(top)} in classifica")
    fuori = []
    for t in top:
        print(f"   • {t['titolo']} ×{t['pezzi']}")
        r = con.execute("SELECT foto FROM annunci WHERE id=?",
                        (t["annuncio_id"],)).fetchone()
        try:
            nomi = json.loads((r["foto"] if r else "") or "[]")
        except Exception:
            nomi = []
        n = nomi[0] if nomi else ""
        if not n or n.startswith("http") or n.startswith("data:"):
            continue
        mini = n[:-4] + "_min.jpg" if n.endswith(".jpg") else ""
        for nome in (mini, n):
            if nome and os.path.exists(os.path.join("foto", nome)):
                fuori.append(os.path.join("foto", nome))
                break
    con.close()
    return fuori


def griglia(amb, fuori: str):
    """I tre riquadri disegnati sullo sfondo nudo: e' il modo piu'
    veloce di vedere se un vetro e' storto di venti pixel."""
    from PIL import Image, ImageDraw
    base = Image.open(amb["SFONDO_RIEPILOGO"]).convert("RGB")
    L, A = base.size
    d = ImageDraw.Draw(base)
    for i, (x0, y0, x1, y1) in enumerate(amb["VETRI_RIEPILOGO"]):
        d.rectangle((x0 * L, y0 * A, x1 * L, y1 * A),
                    outline=(255, 0, 0), width=4)
        d.text((x0 * L + 10, y0 * A + 10), f"{i + 1}°", fill=(255, 0, 0))
    base.save(fuori)
    print(f"🖼  Griglia in {fuori} — lo sfondo è {L}×{A}")


def main():
    args = sys.argv[1:]
    fuori = "anteprima_riepilogo.jpg"
    if "--fuori" in args:
        i = args.index("--fuori")
        fuori = args[i + 1]
        del args[i:i + 2]
    db = "satmarket.db"
    if "--db" in args:
        i = args.index("--db")
        db = args[i + 1]
        del args[i:i + 2]
    amb = carica()
    if not os.path.exists(amb["SFONDO_RIEPILOGO"]):
        sys.exit(f"manca {amb['SFONDO_RIEPILOGO']}: mettici il disegno "
                 "dei tre barattoli (il vetro bianco è dove vanno le foto)")
    if "--griglia" in args:
        return griglia(amb, fuori)
    foto = [a for a in args if not a.startswith("-")]
    if not foto:
        if not os.path.exists(db):
            sys.exit(f"non trovo {db}: passa le foto a mano, o --db")
        foto = foto_dal_db(db, amb)
    if not foto:
        sys.exit("nessuna foto da mettere nei barattoli: lunedì il post "
                 "uscirebbe come testo (ed è il ripiego giusto)")
    print(f"📷 {len(foto)} foto: " + ", ".join(foto))
    figura = amb["_podio_su_sfondo"](foto + [None, None, None])
    if figura is None:
        sys.exit("l'immagine non si è composta (vedi le righe qui sopra): "
                 "lunedì il podio uscirebbe DISEGNATO, che è il ripiego")
    figura.save(fuori, quality=88)
    print(f"🖼  Fatto: {fuori} — guardalo, e se un barattolo è storto "
          "tara VETRI_RIEPILOGO in server.py")


if __name__ == "__main__":
    main()
