# genera_icone_apk.py — i due livelli dell'icona adattiva per l'APK (TWA).
#
# Bubblewrap (verificato sulla 1.24.1) NON sa fare l'icona adattiva vera:
# il suo ic_launcher.xml mette l'INTERA maskable nel layer background
# (su bianco, con 8.5dp di margine) e lascia il foreground trasparente —
# niente parallasse, e ai bordi si vede il confine tra i due arancioni.
# Il monochromeIconUrl del twa-manifest serve solo a notifiche e
# shortcut, non al launcher.
#
# Questo script patcha il progetto generato, e va RILANCIATO DOPO OGNI
# `bubblewrap update` (che cancella e riscrive proprio questi file):
#   1. campiona l'arancio dagli angoli della sorgente (LA STESSA ricetta
#      di genera_icone.py: e' importata, mai duplicata) e lo scrive in
#      res/values/colors.xml come iconBackground — sfondo e barattolo
#      arrivano dalla stessa foto, il confine non puo' esistere;
#   2. scontorna il barattolo (alpha dalla distanza dal fondo, fori
#      interni richiusi col floodfill dall'esterno) e lo posa su canvas
#      trasparente 108dp nei 5 mipmap: ic_launcher_foreground.png.
#      Barattolo al ~51% del lato: la stessa presenza della maskable
#      (67% su cerchio sicuro 80%) riportata al cerchio 66/108dp
#      dell'icona adattiva;
#   3. silhouette bianca con la stessa alpha: ic_launcher_monochrome.png
#      (icone a tema di Android 13+, il launcher la tinge lui);
#   4. riscrive res/mipmap-anydpi-v26/ic_launcher.xml come adaptive-icon
#      vera a tre livelli (richiede compileSdk >= 33 per <monochrome>);
#   5. rimette org.gradle.jvmargs=-Xmx1024m in gradle.properties
#      (bubblewrap update lo toglie, e il VPS-di-casa di Andrea ne
#      ha bisogno per non affogare il build).
#
# Uso (dalla cartella del repo):
#   python genera_icone_apk.py [percorso-progetto-twa]
# default: ..\..\barattolo-twa (il progetto sta fuori dal repo, coi
# keystore: MAI portarlo dentro).

import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from genera_icone import SOGLIA_BBOX, SORGENTE, colore_fondo

# la rampa dell'alpha: sotto T_VUOTO e' fondo (il rumore del JPEG resta
# sotto), sopra T_PIENO e' barattolo, in mezzo la sfumatura del bordo
T_VUOTO, T_PIENO = 12, 40

# barattolo al 67% con cerchio sicuro 80% (la maskable verificata)
# => stessa presenza sul cerchio 66dp del canvas 108dp dell'adattiva
SCALA_FOREGROUND = 0.67 * (66 / 108) / 0.80          # ~0.512

MIPMAP = [("mdpi", 108), ("hdpi", 162), ("xhdpi", 216),
          ("xxhdpi", 324), ("xxxhdpi", 432)]

IC_LAUNCHER_XML = """<!--
    Riscritto da genera_icone_apk.py (repo satmarket): icona adattiva
    vera a due livelli + monochrome. `bubblewrap update` rimette la
    versione piatta di Bubblewrap: rilanciare lo script dopo ogni update.
-->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/iconBackground" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@mipmap/ic_launcher_monochrome" />
</adaptive-icon>
"""


def scontorna(img, fondo):
    # alpha morbida dalla distanza dal colore del fondo...
    diff = ImageChops.difference(img, Image.new("RGB", img.size, fondo))
    dist = diff.convert("L")

    def rampa(p):
        if p <= T_VUOTO:
            return 0
        if p >= T_PIENO:
            return 255
        return round((p - T_VUOTO) * 255 / (T_PIENO - T_VUOTO))

    alpha = dist.point(rampa)

    # ...ma i punti color-fondo DENTRO il barattolo (riflessi sul vetro)
    # non devono bucarlo: si allaga il fondo dai quattro angoli a bassa
    # risoluzione (il floodfill di Pillow e' Python puro: a 1/4 basta,
    # i bordi veri li fa comunque la rampa qui sopra) e cio' che resta
    # non raggiunto e' un foro da richiudere.
    piccolo = dist.resize((img.width // 4, img.height // 4), Image.BILINEAR)
    fondo_bin = piccolo.point(lambda p: 255 if p <= SOGLIA_BBOX else 0)
    w, h = fondo_bin.size
    for angolo in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if fondo_bin.getpixel(angolo) == 255:
            ImageDraw.floodfill(fondo_bin, angolo, 128)
    fori = fondo_bin.point(lambda p: 255 if p == 255 else 0)
    fori = fori.resize(img.size, Image.BILINEAR)
    alpha = ImageChops.lighter(alpha, fori)

    ritagliato = img.convert("RGBA")
    ritagliato.putalpha(alpha)
    # il rettangolo utile: la stessa maschera a soglia di genera_icone.py,
    # cosi' la geometria e' identica a quella delle icone PWA
    bbox = dist.point(lambda p: 255 if p > SOGLIA_BBOX else 0).getbbox()
    return ritagliato.crop(bbox)


def componi(barattolo, lato, bianco=False):
    tela = Image.new("RGBA", (lato, lato), (0, 0, 0, 0))
    rapporto = min(round(lato * SCALA_FOREGROUND) / max(barattolo.size), 1.0)
    misure = (round(barattolo.width * rapporto),
              round(barattolo.height * rapporto))
    soggetto = barattolo.resize(misure, Image.LANCZOS)
    if bianco:
        # la silhouette per i temi: bianco pieno, conta solo l'alpha
        # (l'ombra bassa resta come velo morbido: tagliarla rischierebbe
        # di mangiare la base scura del barattolo)
        bianca = Image.new("RGBA", soggetto.size, (255, 255, 255, 255))
        bianca.putalpha(soggetto.getchannel("A"))
        soggetto = bianca
    posa = ((lato - misure[0]) // 2, (lato - misure[1]) // 2)
    tela.paste(soggetto, posa, soggetto)
    return tela


def patch_colors(res, esadecimale):
    percorso = res / "values" / "colors.xml"
    testo = percorso.read_text(encoding="utf-8")
    riga = f'    <color name="iconBackground">{esadecimale}</color>'
    if "iconBackground" in testo:
        testo = re.sub(r'\s*<color name="iconBackground">[^<]*</color>',
                       "\n" + riga, testo)
    else:
        testo = testo.replace("</resources>", riga + "\n</resources>")
    percorso.write_text(testo, encoding="utf-8")


def patch_gradle(progetto):
    percorso = progetto / "gradle.properties"
    testo = percorso.read_text(encoding="utf-8")
    if "-Xmx1024m" not in testo:
        testo = testo.rstrip("\n") + "\n\norg.gradle.jvmargs=-Xmx1024m\n"
        percorso.write_text(testo, encoding="utf-8")
        print("🐘 gradle.properties: rimesso -Xmx1024m")


def genera():
    base = Path(__file__).resolve().parent
    progetto = Path(sys.argv[1]) if len(sys.argv) > 1 \
        else base.parent.parent / "barattolo-twa"
    res = progetto / "app" / "src" / "main" / "res"
    if not (res / "mipmap-anydpi-v26").is_dir():
        sys.exit(f"Progetto TWA non trovato in {progetto}")

    img = Image.open(base / SORGENTE).convert("RGB")
    fondo = colore_fondo(img)
    esadecimale = "#{:02X}{:02X}{:02X}".format(*fondo)
    barattolo = scontorna(img, fondo)

    for dpi, lato in MIPMAP:
        cartella = res / f"mipmap-{dpi}"
        componi(barattolo, lato).save(
            cartella / "ic_launcher_foreground.png", "PNG", optimize=True)
        componi(barattolo, lato, bianco=True).save(
            cartella / "ic_launcher_monochrome.png", "PNG", optimize=True)
        print(f"🫙 mipmap-{dpi}: foreground + monochrome ({lato}px)")

    (res / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(
        IC_LAUNCHER_XML, encoding="utf-8")
    patch_colors(res, esadecimale)
    patch_gradle(progetto)
    print(f"🎨 sfondo iconBackground = {esadecimale} (campionato dagli angoli)")
    print("✅ Icona adattiva a due livelli pronta: ora `bubblewrap build`.")


if __name__ == "__main__":
    genera()
