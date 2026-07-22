# genera_icone.py — la ricetta delle icone PWA di Barattolo.
#
# Prende il barattolo scontornato (assets/barattolo-hero.png, PNG con
# trasparenza) e lo appoggia su una tessera arancio Bitcoin piena, come
# le altre tessere del brand. Si rilancia una volta sola quando la
# grafica cambia: python genera_icone.py
#
# Due geometrie:
#  - "any" (icona-*.png, apple-touch-icon.png): barattolo all'85% del
#    lato — l'icona classica, l'OS al massimo arrotonda gli angoli.
#  - "maskable" (icona-*-maskable.png): barattolo al 62% del lato —
#    Android puo' ritagliare cerchi e squircle, la zona sicura e' il
#    cerchio di diametro 80% (quadrato inscritto ~66%): al 62% il
#    barattolo resta sempre intero, con un filo di respiro.

from PIL import Image

ARANCIO = (247, 147, 26)          # #F7931A, l'arancio ₿ del brand
SORGENTE = "assets/barattolo-hero.png"

# (nome file, lato in px, scala del barattolo sul lato)
ICONE = [
    ("assets/icona-192.png",          192, 0.85),
    ("assets/icona-512.png",          512, 0.85),
    ("assets/icona-192-maskable.png", 192, 0.62),
    ("assets/icona-512-maskable.png", 512, 0.62),
    ("assets/apple-touch-icon.png",   180, 0.85),
]


def genera():
    barattolo = Image.open(SORGENTE).convert("RGBA")
    # il PNG sorgente ha i suoi margini trasparenti: si ritaglia il
    # rettangolo utile, cosi' la scala vale sul barattolo VERO e non
    # sull'aria che gli sta intorno (senza, uscirebbe rimpicciolito due
    # volte)
    barattolo = barattolo.crop(barattolo.getbbox())
    for nome, lato, scala in ICONE:
        tela = Image.new("RGBA", (lato, lato), ARANCIO + (255,))
        # il barattolo e' piu' alto che largo: si scala sul lato lungo
        # e si conserva la proporzione
        massimo = round(lato * scala)
        rapporto = massimo / max(barattolo.size)
        misure = (round(barattolo.width * rapporto),
                  round(barattolo.height * rapporto))
        soggetto = barattolo.resize(misure, Image.LANCZOS)
        posa = ((lato - misure[0]) // 2, (lato - misure[1]) // 2)
        tela.alpha_composite(soggetto, posa)
        # niente alpha nel file finale: il fondo e' pieno per scelta
        tela.convert("RGB").save(nome, "PNG", optimize=True)
        print(f"🫙 {nome} ({lato}px, barattolo al {round(scala*100)}%)")


if __name__ == "__main__":
    genera()
