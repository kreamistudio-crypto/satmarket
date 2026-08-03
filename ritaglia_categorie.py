"""Ritaglia il vuoto attorno alle illustrazioni di Sfoglia.

PERCHE' ESISTE. Le illustrazioni arrivano come quadrati 512x512 con il
disegno al centro e circa il 30% di margine trasparente attorno. Quel
margine e' spazio che la piastrella paga: il disegno puo' essere alto
al massimo quanto la fascia libera sotto il nome, e se un terzo di
quell'altezza e' vuoto, il disegno si vede piccolo. Ritagliando, la
stessa fascia contiene un disegno grande un terzo di piu', senza
togliere niente al nome.

E' anche l'INVARIANTE su cui poggia il CSS: la piastrella posa
l'immagine in un riquadro in basso a destra con object-fit:contain, e
quel riquadro e' tarato assumendo che l'immagine sia TUTTA disegno. Se
un file torna ad avere margini, il disegno rimpicciolisce; se il
ritaglio non venisse fatto affatto, si vedrebbe la differenza subito.
`prove.py` controlla che i file siano tirati, quindi la CI se ne
accorge prima della vetrina.

Idempotente: rilanciarlo su file gia' ritagliati non fa nulla. Va
rilanciato quando si aggiunge o si rifa' un'illustrazione.

    python ritaglia_categorie.py            # dice cosa farebbe
    python ritaglia_categorie.py --scrivi   # lo fa
"""
import os
import sys

CARTELLA = os.path.join("assets", "categorie")
QUALITA = 92          # una sola ricompressione, su arte piatta e' invisibile
# L'alpha si guarda SOPRA una soglia, non sopra lo zero: un file
# arrivava con una velatura quasi invisibile stesa su tutta la tela, e
# col confronto a zero il riquadro restava 512x512 — il ritaglio non
# faceva nulla e quel disegno si vedeva molto piu' piccolo degli altri
# (era 329x236 dentro il quadrato). Otto su 255 e' sotto il visibile e
# non intacca l'antialiasing dei bordi: sugli altri 25 file il
# riquadro cambia di 4px in tutto.
SOGLIA_ALPHA = 8
# Sotto questo scarto non si riscrive: un ritaglio da due pixel non
# vale una seconda compressione, e cosi' rilanciare lo script non
# ricomprime ogni volta tutto quanto.
MINIMO = .02


def main():
    scrivi = "--scrivi" in sys.argv
    try:
        from PIL import Image
    except ImportError:
        print("serve Pillow:  pip install pillow")
        return 1
    if not os.path.isdir(CARTELLA):
        print(f"cartella {CARTELLA} assente")
        return 1

    fatti = gia_a_posto = 0
    for nome in sorted(os.listdir(CARTELLA)):
        if not nome.endswith(".webp"):
            continue
        p = os.path.join(CARTELLA, nome)
        im = Image.open(p).convert("RGBA")
        sodo = im.getchannel("A").point(
            lambda v: 255 if v > SOGLIA_ALPHA else 0)
        bb = sodo.getbbox()
        if bb is None:
            print(f"  ⚠ {nome}: tutto trasparente, lasciato com'e'")
            continue
        w, h = im.size
        scarto = max(bb[0], bb[1], w - bb[2], h - bb[3])
        if scarto <= MINIMO * max(w, h):
            gia_a_posto += 1
            continue
        prima = os.path.getsize(p) / 1024
        ritagliata = im.crop(bb)
        larg = bb[2] - bb[0]
        alt = bb[3] - bb[1]
        print(f"  {nome[:-5]:26s} {w}x{h} → {larg}x{alt}"
              f"   ({100*larg//w}% x {100*alt//h}%)")
        if scrivi:
            ritagliata.save(p, "WEBP", quality=QUALITA, method=6)
            print(f"{'':30s}{prima:.0f}KB → {os.path.getsize(p)/1024:.0f}KB")
        fatti += 1

    print(f"\n{fatti} da ritagliare, {gia_a_posto} gia' a posto")
    if fatti and not scrivi:
        print("niente e' stato scritto: rilancia con --scrivi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
