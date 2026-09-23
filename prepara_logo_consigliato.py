# -*- coding: utf-8 -*-
"""Prepara il LOGO di un negozio consigliato per la card «Consigliati»
della home (set 2026): dal PNG che manda il negozio al WebP che la card
fa girare.

PERCHE' UNO SCRIPT E NON UN GIRO A MANO: i loghi arrivano uno per
negozio, a distanza di settimane, e il trattamento deve essere lo
STESSO ogni volta — quello delle altre immagini delle card:

1) IL RITAGLIO SOPRA UNA SOGLIA, non sopra lo zero. Il PNG di To The
   Mooon (900x1350) aveva una velatura quasi invisibile stesa su tutta
   la tela: col confronto a zero risultava gia' tirato, mentre il
   disegno vero ne occupava meno di meta' (738x455). E' la lezione di
   `ritaglia_categorie.py`, con la sua stessa soglia.
2) NITIDO A 3x. Nella card il logo sta in un riquadro che e' il 90% del
   quadrato (lo stesso `inset` della card dello scambio): 84px sul
   telefono, 160 dal browser del computer — cioe' 144px, e a 3x fanno
   432. Il logo entra in un quadrato di 432, col suo rapporto.
3) WEBP CON LA TRASPARENZA, qualita' 90, nessun metadato: la ricetta
   del logo grande del P2P. Il fondo lo mette la card (il bruno delle
   categorie), quindi il logo deve arrivare scontornato.

La cartella e' SUA, `assets/consigliati/`, e mai `assets/categorie/`:
`ritaglia_categorie.py` fa il glob di quella, e un marchio entrerebbe
nella mediana del pareggio spostando le illustrazioni sorelle.

DOPO, NEL CATALOGO, `logo: True` (o `logo: true` nel catalogo del
client, per lo spazio sponsorizzato): e' quello che fa entrare il
negozio fra i Consigliati. `prove.py` controlla che a ogni `logo` vero
corrisponda il suo file, e viceversa.

    python prepara_logo_consigliato.py percorso/del/logo.png slug
"""
import os
import re
import sys

CARTELLA = os.path.join("assets", "consigliati")
# la stessa di ritaglia_categorie.py: sopra l'antialiasing dei bordi,
# sotto il visibile — smaschera la velatura senza mangiare i contorni
SOGLIA_ALPHA = 8
LATO = 432          # il 3x dei 144px della card piu' grande
QUALITA = 90


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1].strip())
        return 1
    sorgente, slug = sys.argv[1], sys.argv[2].strip().lower()
    # la forma degli slug delle rotte dei racconti: niente che possa
    # diventare un percorso fuori dalla cartella
    if not re.fullmatch(r"[a-z0-9-]{2,40}", slug):
        print(f"slug non valido: «{slug}» (minuscole, cifre e trattini)")
        return 1
    try:
        from PIL import Image
    except ImportError:
        print("serve Pillow:  pip install pillow")
        return 1

    im = Image.open(sorgente).convert("RGBA")
    a = im.getchannel("A")
    bb = a.point(lambda v: 255 if v > SOGLIA_ALPHA else 0).getbbox()
    if bb is None:
        print("il PNG e' tutto trasparente: niente da ritagliare")
        return 1
    if bb == (0, 0) + im.size:
        # un logo su fondo PIENO: la card gli metterebbe attorno un
        # rettangolo del suo colore. Si prosegue, ma lo si dice.
        print("⚠ il logo non ha bordi trasparenti: e' scontornato?")
    disegno = im.crop(bb)
    # il ridimensionamento in alfa PREMOLTIPLICATO: sui bordi semitrasparenti
    # il colore dei pixel invisibili non deve colare dentro il disegno
    fattore = min(1.0, LATO / max(disegno.size))
    misura = (max(1, round(disegno.size[0] * fattore)),
              max(1, round(disegno.size[1] * fattore)))
    finale = (disegno.convert("RGBa").resize(misura, Image.LANCZOS)
              .convert("RGBA"))
    # un'immagine NUOVA e non la copia: cosi' non si porta dietro nessun
    # profilo o metadato del file d'origine
    pulita = Image.new("RGBA", finale.size)
    pulita.paste(finale)
    os.makedirs(CARTELLA, exist_ok=True)
    destino = os.path.join(CARTELLA, slug + ".webp")
    pulita.save(destino, "WEBP", quality=QUALITA, method=6)
    print(f"{destino}: {pulita.size[0]}x{pulita.size[1]}, "
          f"{os.path.getsize(destino) / 1024:.1f} KB "
          f"(ritaglio {disegno.size[0]}x{disegno.size[1]} dal PNG "
          f"{im.size[0]}x{im.size[1]})")
    print("adesso nel catalogo: logo vero per «%s»" % slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
