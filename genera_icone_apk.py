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
#   5. allinea il fondo dello SPLASH allo stesso arancio campionato
#      (twa-manifest.json backgroundColor + la copia in app/build.gradle):
#      lo splash mostra la tessera quadrata dell'icona, e su un fondo
#      diverso fa l'effetto francobollo — stesso campione, si fonde;
#   6. ridisegna drawable-*/splash.png: Bubblewrap ci mette la tessera
#      intera a 300dp (3/4 dello schermo, un macigno) e la disegna
#      centrata a dimensione intrinseca — non esiste NESSUNA leva di
#      scala nel twa-manifest (splashScreenFadeOutDuration e' solo la
#      dissolvenza), l'unica e' la misura in pixel dei PNG. Qui:
#      barattolo scontornato su fondo trasparente a SPLASH_DP (160dp
#      ~= 40% del lato corto di un telefono da 360-411dp), l'arancio
#      sotto ce lo mette gia' backgroundColor;
#   7. rimette org.gradle.jvmargs=-Xmx1024m in gradle.properties
#      (bubblewrap update lo toglie, e il VPS-di-casa di Andrea ne
#      ha bisogno per non affogare il build);
#   8. rimette in LauncherActivity.java il PERMESSO DELLO SPLASH (set
#      2026), la cura del difetto di Chrome 152+: senza, lo splash non
#      arriva a Chrome e la sua finestra entra da destra SCURA per mezzo
#      secondo prima della pagina (android-browser-helper#623). E' il
#      primo passo, e se l'ancora non c'e' lo script si FERMA prima di
#      toccare qualunque file: un APK uscito senza la cura sembrerebbe
#      giusto in tutto, tranne che sul telefono.
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

# lo splash e' disegnato centrato alla dimensione intrinseca del PNG
# (px / densita' = dp): 160dp ~= 40% del lato corto dei telefoni comuni
SPLASH_DP = 160
SPLASH_DENSITA = [("mdpi", 1.0), ("hdpi", 1.5), ("xhdpi", 2.0),
                  ("xxhdpi", 3.0), ("xxxhdpi", 4.0)]

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

# IL PERMESSO DELLO SPLASH (set 2026). La libreria dello splash
# (androidbrowserhelper 2.6.2, TrustedWebUtils.transferSplashImage) da'
# a CHROME il permesso di leggere il PNG dello splash e poi gli chiede
# di prenderlo. Da Chrome 152 (stabile il 25 ago 2026) receiveFile()
# controlla anche che CHI CONSEGNA abbia il permesso su quell'URI — e il
# proprietario del FileProvider non ha un record esplicito, perche'
# Android non lo scrive a chi possiede gia' la cassetta. Chrome dice no,
# la libreria scrive «Failed to transfer splash image.», lancia Chrome
# SENZA i parametri dello splash e SENZA spegnere l'animazione: la
# finestra entra da destra, scura, finche' la pagina non disegna.
# La cura (android-browser-helper#623): ce lo diamo da soli, col flag
# PERSISTABLE che costringe il sistema a scrivere il record, PRIMA di
# super.onCreate() — che e' il gesto che avvia la consegna.
# ⚠️ I due nomi del file sono costanti della LIBRERIA (FOLDER_NAME e
# FILE_NAME di SplashImageTransferTask, lette col javap sul 2.6.2): se
# un aggiornamento li cambia, il permesso finisce su un URI che nessuno
# usa e il difetto torna in silenzio. L'autorita' invece si legge dalla
# stessa risorsa da cui la legge la libreria (@string/providerAuthority,
# via il meta-data FILE_PROVIDER_AUTHORITY), quindi non puo' divergere.
MARCATORE_PERMESSO = "Barattolo: permesso dello splash"
PERMESSO_SPLASH = f"""\
// {MARCATORE_PERMESSO} (Chrome 152+, android-browser-helper#623).
// Chrome pretende che ANCHE chi consegna il file abbia il permesso
// sull'URI, e il proprietario del FileProvider non ha un record
// esplicito: receiveFile() dice no e la finestra di Chrome entra scura.
// Il permesso ce lo diamo da soli; PERSISTABLE e' il flag che costringe
// il sistema a scriverlo. PRIMA di super.onCreate(), che avvia la
// consegna; il file puo' non esserci ancora. Rimesso a ogni build da
// genera_icone_apk.py (repo satmarket): bubblewrap update lo cancella.
try {{
    java.io.File splash = new java.io.File(
            new java.io.File(getFilesDir(), "twa_splash"), "splash_image.png");
    android.net.Uri uriSplash = androidx.core.content.FileProvider.getUriForFile(
            this, getString(R.string.providerAuthority), splash);
    grantUriPermission(getPackageName(), uriSplash,
            android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | android.content.Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
}} catch (RuntimeException e) {{
    // senza il permesso si torna al difetto di prima, non si rompe niente
    android.util.Log.w("Barattolo", "permesso dello splash non concesso", e);
}}
"""
# l'ancora: la PRIMA riga del corpo di onCreate, com'e' nel modello di
# Bubblewrap 1.24.1 (template_project/app/src/main/java/LauncherActivity.java)
ANCORA_ONCREATE = re.compile(
    r"(protected void onCreate\(Bundle savedInstanceState\) \{\r?\n)"
    r"([ \t]*)(super\.onCreate\(savedInstanceState\);)")


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


def genera_splash(res, barattolo):
    # il barattolo nudo su trasparente: l'arancio sotto e' backgroundColor,
    # che e' lo stesso campione — la sagoma affiora dal fondo senza bordi
    for dpi, scala in SPLASH_DENSITA:
        px = round(SPLASH_DP * scala)
        rapporto = px / max(barattolo.size)
        misure = (round(barattolo.width * rapporto),
                  round(barattolo.height * rapporto))
        cartella = res / f"drawable-{dpi}"
        cartella.mkdir(exist_ok=True)
        barattolo.resize(misure, Image.LANCZOS).save(
            cartella / "splash.png", "PNG", optimize=True)
        print(f"🌄 drawable-{dpi}: splash {misure[0]}x{misure[1]}px "
              f"({SPLASH_DP}dp)")


def patch_splash(progetto, esadecimale):
    # il fondo dello splash deve essere LO STESSO arancio campionato
    # della tessera, o il quadrato dell'icona ci galleggia sopra come
    # un francobollo. twa-manifest.json e' la fonte di verita' (l'update
    # la ricopia in build.gradle), ma si patcha anche la copia: cosi'
    # il colore giusto entra nel build anche senza un nuovo update.
    ritocchi = [
        (progetto / "twa-manifest.json",
         r'("backgroundColor":\s*")#[0-9A-Fa-f]{6}(")'),
        (progetto / "app" / "build.gradle",
         r"(backgroundColor:\s*')#[0-9A-Fa-f]{6}(')"),
    ]
    for percorso, schema in ritocchi:
        testo = percorso.read_text(encoding="utf-8")
        nuovo = re.sub(schema, rf"\g<1>{esadecimale}\g<2>", testo)
        if nuovo != testo:
            percorso.write_text(nuovo, encoding="utf-8")
            print(f"🌅 {percorso.name}: fondo splash = {esadecimale}")


def patch_gradle(progetto):
    percorso = progetto / "gradle.properties"
    testo = percorso.read_text(encoding="utf-8")
    if "-Xmx1024m" not in testo:
        testo = testo.rstrip("\n") + "\n\norg.gradle.jvmargs=-Xmx1024m\n"
        percorso.write_text(testo, encoding="utf-8")
        print("🐘 gradle.properties: rimesso -Xmx1024m")


def patch_launcher(progetto):
    # il permesso dello splash (vedi PERMESSO_SPLASH, qui sopra). Si
    # FERMA con sys.exit in ogni caso dubbio, mai un salto in silenzio:
    # l'APK senza la cura compila, si firma e si installa benissimo, e il
    # difetto si vede solo aprendolo sul telefono — cioe' a release fatta
    radice = progetto / "app" / "src" / "main" / "java"
    trovati = sorted(radice.rglob("LauncherActivity.java"))
    if len(trovati) != 1:
        sys.exit(f"⛔ LauncherActivity.java: attesi 1 sotto {radice}, "
                 f"trovati {len(trovati)}.\n   NON lanciare `bubblewrap "
                 f"build`: l'APK uscirebbe senza il permesso dello splash "
                 f"(Chrome 152+). Guarda il progetto prima di andare avanti.")
    percorso = trovati[0]
    # byte in, byte out: il file resta identico fuori dal blocco, a-capo
    # compresi (Bubblewrap lo scrive in LF anche su Windows)
    testo = percorso.read_bytes().decode("utf-8")
    if MARCATORE_PERMESSO in testo:
        print("🔑 LauncherActivity: il permesso dello splash c'e' gia'")
        return
    ancore = ANCORA_ONCREATE.findall(testo)
    if len(ancore) != 1:
        sys.exit(f"⛔ {percorso.name}: l'ancora del permesso dello splash "
                 f"(la prima riga di onCreate, `super.onCreate("
                 f"savedInstanceState);`) compare {len(ancore)} volte "
                 f"invece di 1 — Bubblewrap ha cambiato il modello.\n"
                 f"   NON lanciare `bubblewrap build`: l'APK uscirebbe "
                 f"senza la cura dello splash (Chrome 152+). Guarda il "
                 f"file e aggiorna ANCORA_ONCREATE in genera_icone_apk.py.")
    a_capo = "\r\n" if "\r\n" in testo else "\n"

    def innesta(m):
        rientro = m.group(2)
        blocco = "".join(rientro + riga + a_capo if riga else a_capo
                         for riga in PERMESSO_SPLASH.splitlines())
        return m.group(1) + blocco + rientro + m.group(3)

    percorso.write_bytes(ANCORA_ONCREATE.sub(innesta, testo).encode("utf-8"))
    print(f"🔑 {percorso.name}: permesso dello splash prima di "
          f"super.onCreate() (Chrome 152+)")


def genera():
    base = Path(__file__).resolve().parent
    progetto = Path(sys.argv[1]) if len(sys.argv) > 1 \
        else base.parent.parent / "barattolo-twa"
    res = progetto / "app" / "src" / "main" / "res"
    if not (res / "mipmap-anydpi-v26").is_dir():
        sys.exit(f"Progetto TWA non trovato in {progetto}")

    # PRIMA di tutto il resto: se l'ancora manca si ferma qui, e nessun
    # file del progetto e' stato ancora toccato
    patch_launcher(progetto)

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
    patch_splash(progetto, esadecimale)
    genera_splash(res, barattolo)
    patch_gradle(progetto)
    print(f"🎨 sfondo iconBackground = {esadecimale} (campionato dagli angoli)")
    print("✅ Icona adattiva a due livelli pronta: ora `bubblewrap build`.")


if __name__ == "__main__":
    genera()
