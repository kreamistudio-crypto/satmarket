# genera_icone.py — la ricetta delle icone PWA di Barattolo.
#
# Dal lug 2026 la sorgente e' assets/barattolo-icona-sorgente.jpeg
# (2048px): il barattolo GIA' composto sul suo fondo arancione. Niente
# piu' tessera costruita a mano — si ritaglia da qui, e il colore per
# estendere i bordi si CAMPIONA dagli angoli dell'immagine stessa
# (e' un filo diverso dal #F7931A di palette: comanda la foto).
# Si rilancia una volta sola quando la grafica cambia:
#   python genera_icone.py
# (e chi la rilancia alza VERSIONE in sw.js: le icone sono in dispensa)
#
# Due geometrie:
#  - "any" (icona-*.png, apple-touch-icon.png): barattolo al 90%
#    dell'altezza — bello presente, l'OS al massimo arrotonda gli angoli
#    e il barattolo e' stretto (rapporto ~0.69): non li tocca.
#  - "maskable" (icona-*-maskable.png): barattolo al 67% — Android puo'
#    ritagliare cerchi e squircle, la zona sicura e' il cerchio di
#    diametro 80%. Gli angoli del RETTANGOLO utile sforano di un pelo,
#    ma li' c'e' solo aria arancione: il barattolo vero (spalle tonde,
#    ombra bassa) resta intero. Verificato sull'anteprima col cerchio.

from PIL import Image, ImageChops

SORGENTE = "assets/barattolo-icona-sorgente.jpeg"
SOGLIA_BBOX = 20                  # sotto, e' fondo; sopra, e' barattolo

# (nome file, lato in px, scala del barattolo sul lato)
ICONE = [
    ("assets/icona-192.png",          192, 0.90),
    ("assets/icona-512.png",          512, 0.90),
    ("assets/icona-192-maskable.png", 192, 0.67),
    ("assets/icona-512-maskable.png", 512, 0.67),
    ("assets/apple-touch-icon.png",   180, 0.90),
]


def colore_fondo(img):
    # media dei quattro angoli (quadratini 20x20): il fondo e' piatto,
    # ma il JPEG ha il suo rumore e un pixel solo sarebbe un azzardo
    w, h = img.size
    somma = [0, 0, 0]
    for box in [(0, 0, 20, 20), (w - 20, 0, w, 20),
                (0, h - 20, 20, h), (w - 20, h - 20, w, h)]:
        angolo = img.crop(box).resize((1, 1), Image.LANCZOS)
        px = angolo.getpixel((0, 0))
        for i in range(3):
            somma[i] += px[i]
    return tuple(c // 4 for c in somma)


def genera():
    img = Image.open(SORGENTE).convert("RGB")
    fondo = colore_fondo(img)
    # il rettangolo utile: dove l'immagine si stacca dal fondo piatto
    # (ombra compresa: tagliarla a meta' lascerebbe una riga visibile)
    diff = ImageChops.difference(img, Image.new("RGB", img.size, fondo))
    maschera = diff.convert("L").point(lambda p: 255 if p > SOGLIA_BBOX else 0)
    barattolo = img.crop(maschera.getbbox())
    for nome, lato, scala in ICONE:
        tela = Image.new("RGB", (lato, lato), fondo)
        # il barattolo e' piu' alto che largo: si scala sul lato lungo
        # e si conserva la proporzione. Mai upscale: la sorgente a
        # 2048px basta e avanza, ma la guardia resta
        rapporto = min(round(lato * scala) / max(barattolo.size), 1.0)
        misure = (round(barattolo.width * rapporto),
                  round(barattolo.height * rapporto))
        soggetto = barattolo.resize(misure, Image.LANCZOS)
        posa = ((lato - misure[0]) // 2, (lato - misure[1]) // 2)
        # il ritaglio e' un rettangolo pieno, ma i suoi bordi SONO il
        # fondo campionato: appoggiato sulla tela dello stesso colore
        # non si vede la giuntura
        tela.paste(soggetto, posa)
        tela.save(nome, "PNG", optimize=True)
        print(f"🫙 {nome} ({lato}px, barattolo al {round(scala*100)}%)")


if __name__ == "__main__":
    genera()
