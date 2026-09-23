# genera_icone_apk.py — i due livelli dell'icona adattiva per l'APK (TWA),
# e dalla v1.5 anche il tema con cui l'app si apre.
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
#      secondo prima della pagina (android-browser-helper#623);
#   9. da' a LauncherActivity un TEMA SUO, OPACO (v1.5, set 2026): quello
#      traslucido di Bubblewrap spegne la finestra di partenza — a
#      un'attivita' traslucida Android non ne prepara nessuna — e la
#      finestra che cresceva dall'icona restava NERA per un fotogramma.
#      Scrive i due stili (values/ e values-v31/, il secondo con lo
#      splash del SISTEMA di Android 12+), il fondo della finestra
#      (l'arancio col barattolo di splash.png) e l'icona dello splash di
#      sistema (drawable-*/barattolo_avvio_icona.png), e nel manifest
#      mette il tema sulla SOLA LauncherActivity. Nel Java, lo splash di
#      sistema esce di taglio: sotto c'e' lo stesso barattolo;
#  10. nel Java, LE BARRE VERE (v1.5): l'altezza della barra di stato e
#      di quella di navigazione, in pixel, nel parametro `barre` della
#      URL di avvio. La pagina ne sa solo la somma; con la divisione
#      rimette il barattolo del guscio dove stava nello splash, e poi
#      toglie il parametro dall'indirizzo.
#
# I DUE FILE DI TESTO CHE BUBBLEWRAP RIGENERA (LauncherActivity.java e
# AndroidManifest.xml) SI PREPARANO PER PRIMI, IN MEMORIA: se un'ancora
# manca lo script si ferma prima di scrivere qualunque file, e dice di
# non buildare — un APK uscito senza queste cure compila, si firma e si
# installa benissimo, e il difetto si vede solo sul telefono.
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

# L'ICONA DELLO SPLASH DI SISTEMA (Android 12+, v1.5). Il sistema non la
# disegna alla sua misura: la ridipinge su una tela di 108dp e poi la
# ingrandisce a 192dp, che e' il cerchio visibile quando l'icona non ha
# un fondo suo — e la tela dell'icona SBORDA dal cerchio di mezzo lato
# per parte, quindi sullo schermo vale 288dp (letto nel sorgente di WM
# Shell, SplashscreenIconDrawableFactory: AdaptiveForegroundDrawable).
# Perche' il barattolo esca a 160dp, la misura di splash.png — cosi'
# quando lo splash del sistema lascia il posto a quello della libreria
# non cresce e non cala —, deve occupare 160/288 del lato. La tela in
# pixel e' di 162dp perche' e' la misura a cui il sistema la ridipinge
# (108 × 1,5): di piu' sarebbe peso morto nell'APK.
# ⚠️ E NEL CERCHIO CI STA DI UN SOFFIO: fuori dalla forma delle icone
# il sistema taglia (e quella forma il cerchio lo contiene sempre). Il
# RIQUADRO del barattolo, 110×160dp sullo schermo, ne uscirebbe — mezza
# diagonale 97dp contro 96 di raggio —, ma i suoi angoli sono vuoti: il
# barattolo e' tondo, e i pixel veri stanno fra il 96 e il 99% del
# raggio, misurati sulle cinque densita'. Lo tiene fermo una prova: un
# barattolo piu' grande qui verrebbe tagliato in silenzio.
ICONA_AVVIO_TELA_DP = 162
ICONA_AVVIO_QUOTA = SPLASH_DP / 288

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

# L'USCITA DELLO SPLASH DI SISTEMA (Android 12+, v1.5). Col tema opaco
# il tocco sull'icona apre lo splash del SISTEMA (fondo arancio, e il
# barattolo di barattolo_avvio_icona.png alla misura di splash.png). Al
# primo disegno dell'attivita' il sistema lo toglierebbe con la sua
# animazione — l'icona che sfuma e la finestra che sale di 20dp
# (starting_surface_exit_animation_window_shift_length): un barattolo
# che si muove. Sotto c'e' gia' lo splash della libreria, arancio e con
# lo stesso barattolo: si toglie di taglio.
MARCATORE_USCITA = "Barattolo: l'uscita dello splash di sistema"
USCITA_SPLASH = f"""\
// {MARCATORE_USCITA} (Android 12+, v1.5).
// Col tema opaco il tocco sull'icona apre lo splash DEL SISTEMA,
// arancio col barattolo, e al primo disegno di questa attivita' il
// sistema lo toglierebbe con la sua animazione: l'icona che sfuma e la
// finestra che sale di 20dp, cioe' un barattolo che si muove. Sotto c'e'
// lo splash della libreria, con lo stesso barattolo della stessa misura:
// si toglie di taglio. Rimesso a ogni build da genera_icone_apk.py
// (repo satmarket): bubblewrap update lo cancella.
if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {{
    try {{
        getSplashScreen().setOnExitAnimationListener(vista -> vista.remove());
    }} catch (RuntimeException e) {{
        android.util.Log.w("Barattolo", "uscita dello splash non presa", e);
    }}
}}
"""
# l'ancora: la riga di super.onCreate, UNA nel file; il blocco le va
# subito sopra, dopo quello del permesso
ANCORA_SUPER = re.compile(
    r"^([ \t]*)(super\.onCreate\(savedInstanceState\);)", re.M)

# LE BARRE VERE (v1.5). La pagina sa quanto sono alte la barra di stato
# e quella di navigazione INSIEME (schermo meno pagina), non come si
# dividono — e per rimettere il barattolo del guscio dove stava nello
# splash le serve proprio la divisione (miniapp.html, `scartoGuscio`).
# Qui si sanno: in pixel veri, nel parametro `barre` della URL di avvio,
# e la pagina lo toglie dall'indirizzo appena letto. Un parametro e non
# un frammento: `/sicurezza#…` e `/privacy#…` il frammento lo usano
# gia'. Solo da Android 11, che le dice (WindowMetrics) quando la
# finestra non esiste ancora: prima la pagina resta alla sua stima.
MARCATORE_BARRE = "Barattolo: le barre vere alla pagina"
BARRE_VERE = f"""\
// {MARCATORE_BARRE} (Android 11+, v1.5).
// La pagina sa quanto sono alte la barra di stato e quella di
// navigazione INSIEME, non come si dividono — e per rimettere il
// barattolo del guscio dove stava nello splash le serve la divisione.
// Qui si sanno: vanno in pixel veri nel parametro `barre` (sopra,sotto),
// e la pagina lo toglie dall'indirizzo appena letto. Rimesso a ogni
// build da genera_icone_apk.py (repo satmarket).
if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {{
    try {{
        android.view.WindowInsets riquadri =
                getWindowManager().getCurrentWindowMetrics().getWindowInsets();
        int sopra = riquadri.getInsetsIgnoringVisibility(
                android.view.WindowInsets.Type.statusBars()
                        | android.view.WindowInsets.Type.displayCutout()).top;
        int sotto = riquadri.getInsetsIgnoringVisibility(
                android.view.WindowInsets.Type.navigationBars()).bottom;
        uri = uri.buildUpon()
                .appendQueryParameter("barre", sopra + "," + sotto)
                .build();
    }} catch (RuntimeException e) {{
        android.util.Log.w("Barattolo", "barre non passate alla pagina", e);
    }}
}}
"""
# l'ancora: la prima riga di getLaunchingUrl() nel modello di Bubblewrap
# 1.24.1, quella che prende l'indirizzo della libreria; il blocco le va
# subito sotto, e il `return` del modello restituisce quello nuovo
ANCORA_URL = re.compile(
    r"^([ \t]*)Uri uri = super\.getLaunchingUrl\(\);[ \t]*\r?\n", re.M)

# IL TEMA DELL'AVVIO (v1.5). Sulla SOLA LauncherActivity: le altre
# attivita' della libreria (dati del sito, fallback, permessi delle
# notifiche) restano col tema traslucido di Bubblewrap, com'erano.
TEMA_AVVIO = "BarattoloAvvio"
ATTRIBUTO_TEMA = f'android:theme="@style/{TEMA_AVVIO}"'
# l'ancora: l'apertura dell'elemento com'e' nel modello di Bubblewrap
# 1.24.1 (template_project/app/src/main/AndroidManifest.xml)
ANCORA_MANIFEST = '<activity android:name="LauncherActivity"'
# i due stili e il fondo usano il colore dello splash com'e' GIA' nel
# progetto: @color/backgroundColor nasce da questa riga di app/build.gradle
RIGA_COLORE_SPLASH = re.compile(r'resValue\s+"color",\s*"backgroundColor"')

TEMA_AVVIO_XML = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!--
    Scritto da genera_icone_apk.py (repo satmarket), v1.5: il tema di
    LauncherActivity, e lo mette il manifest solo a lei. OPACO apposta:
    a un'attivita' traslucida Android non prepara nessuna finestra di
    partenza (ne' lo splash di Android 12+, ne' l'anteprima dei telefoni
    piu' vecchi), e la finestra che cresceva dall'icona restava nera per
    un fotogramma. Il gemello opaco del Theme.Translucent.NoTitleBar di
    Bubblewrap: stessa famiglia, stesse barre, niente ombra sotto il
    titolo che non c'e', e nessuna animazione di finestra sua, come
    @style/Animation del traslucido.
-->
<resources>
    <style name="{TEMA_AVVIO}Base" parent="@android:style/Theme.NoTitleBar">
        <item name="android:windowBackground">@drawable/barattolo_avvio_fondo</item>
        <item name="android:colorBackground">@color/backgroundColor</item>
        <item name="android:windowContentOverlay">@null</item>
        <item name="android:windowAnimationStyle">@android:style/Animation</item>
    </style>
    <style name="{TEMA_AVVIO}" parent="@style/{TEMA_AVVIO}Base" />
</resources>
"""

TEMA_AVVIO_V31_XML = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!--
    Scritto da genera_icone_apk.py (repo satmarket), v1.5: da Android 12
    la finestra di partenza e' lo splash DEL SISTEMA, e si veste con
    questi due attributi — lo stesso arancio dello splash e il barattolo
    alla misura di splash.png, cosi' la finestra che cresce dall'icona
    e' gia' lo splash, e il passaggio a quello della libreria non si vede.
-->
<resources>
    <style name="{TEMA_AVVIO}" parent="@style/{TEMA_AVVIO}Base">
        <item name="android:windowSplashScreenBackground">@color/backgroundColor</item>
        <item name="android:windowSplashScreenAnimatedIcon">@drawable/barattolo_avvio_icona</item>
    </style>
</resources>
"""

FONDO_AVVIO_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<!--
    Scritto da genera_icone_apk.py (repo satmarket), v1.5: il fondo della
    finestra di LauncherActivity — l'arancio dello splash col barattolo
    di splash.png al centro, alla sua misura. E' la finestra di partenza
    dei telefoni prima di Android 12.
-->
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@color/backgroundColor" />
    <item>
        <bitmap android:gravity="center" android:src="@drawable/splash" />
    </item>
</layer-list>
"""

# il messaggio di chi si ferma: lo stesso per tutti i casi, perche' la
# cosa da NON fare e' una sola
NON_BUILDARE = ("   NON lanciare `bubblewrap build`: l'APK uscirebbe senza "
                "le cure dell'avvio (il permesso dello splash di Chrome "
                "152+, il tema opaco, le barre vere).")


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


def genera_icona_avvio(res, barattolo):
    # lo stesso barattolo di splash.png, a ICONA_AVVIO_QUOTA della tela:
    # il sistema lo riporta a 160dp (vedi ICONA_AVVIO_TELA_DP, qui sopra)
    for dpi, scala in SPLASH_DENSITA:
        lato = round(ICONA_AVVIO_TELA_DP * scala)
        rapporto = round(lato * ICONA_AVVIO_QUOTA) / max(barattolo.size)
        misure = (round(barattolo.width * rapporto),
                  round(barattolo.height * rapporto))
        tela = Image.new("RGBA", (lato, lato), (0, 0, 0, 0))
        # SENZA maschera: la tela e' vuota, e con la maschera Pillow
        # moltiplicherebbe l'alpha per se stessa — bordi piu' sottili di
        # quelli di splash.png, cioe' due barattoli un po' diversi
        tela.paste(barattolo.resize(misure, Image.LANCZOS),
                   ((lato - misure[0]) // 2, (lato - misure[1]) // 2))
        cartella = res / f"drawable-{dpi}"
        cartella.mkdir(exist_ok=True)
        tela.save(cartella / "barattolo_avvio_icona.png", "PNG",
                  optimize=True)
        print(f"🫙 drawable-{dpi}: icona dello splash di sistema "
              f"{lato}x{lato}px (barattolo {misure[0]}x{misure[1]})")


def scrivi_tema_avvio(res):
    # file NOSTRI, coi nomi nostri: Bubblewrap non li conosce e l'update
    # non li tocca, ma si riscrivono lo stesso a ogni giro — cosi' un
    # ritocco qui arriva nel progetto senza pensarci
    for cartella, nome, testo in [
            ("values", "barattolo_avvio.xml", TEMA_AVVIO_XML),
            ("values-v31", "barattolo_avvio.xml", TEMA_AVVIO_V31_XML),
            ("drawable", "barattolo_avvio_fondo.xml", FONDO_AVVIO_XML)]:
        (res / cartella).mkdir(exist_ok=True)
        (res / cartella / nome).write_text(testo, encoding="utf-8")
    print(f"🎭 tema dell'avvio: {TEMA_AVVIO} in values/ e values-v31/ "
          f"(splash di sistema arancio col barattolo), fondo "
          f"drawable/barattolo_avvio_fondo.xml")


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


def _innesta(blocco, rientro, a_capo):
    # il blocco col rientro dell'ancora, riga per riga, e gli a-capo del
    # file (Bubblewrap lo scrive in LF anche su Windows)
    return "".join(rientro + riga + a_capo if riga else a_capo
                   for riga in blocco.splitlines())


def _ancora_una(schema, testo, percorso, cosa, come_rimediare):
    """L'ancora dev'esserci UNA volta: zero vuol dire che Bubblewrap ha
    cambiato il modello, due che si sceglierebbe a caso. In tutt'e due i
    casi si ferma, e senza aver scritto niente."""
    quante = len(schema.findall(testo))
    if quante != 1:
        sys.exit(f"⛔ {percorso.name}: l'ancora {cosa} compare {quante} "
                 f"volte invece di 1 — Bubblewrap ha cambiato il "
                 f"modello.\n{NON_BUILDARE} Guarda il file e "
                 f"{come_rimediare} in genera_icone_apk.py.")


def prepara_launcher(progetto):
    """I tre blocchi di LauncherActivity.java, preparati in MEMORIA:
    restituisce (percorso, testo nuovo, righe da stampare). Non scrive
    niente, e si FERMA con sys.exit in ogni caso dubbio, mai un salto in
    silenzio: l'APK senza le cure compila, si firma e si installa
    benissimo, e il difetto si vede solo aprendolo sul telefono — cioe'
    a release fatta. Ogni blocco ha il suo marcatore: se c'e' gia' non si
    rimette, quindi rilanciato non si muove niente."""
    radice = progetto / "app" / "src" / "main" / "java"
    trovati = sorted(radice.rglob("LauncherActivity.java"))
    if len(trovati) != 1:
        sys.exit(f"⛔ LauncherActivity.java: attesi 1 sotto {radice}, "
                 f"trovati {len(trovati)}.\n{NON_BUILDARE} Guarda il "
                 f"progetto prima di andare avanti.")
    percorso = trovati[0]
    # byte in, byte out: il file resta identico fuori dai blocchi,
    # a-capo compresi
    testo = percorso.read_bytes().decode("utf-8")
    a_capo = "\r\n" if "\r\n" in testo else "\n"
    righe = []

    # 1) il permesso dello splash (v1.4): la prima cosa di onCreate
    if MARCATORE_PERMESSO in testo:
        righe.append("🔑 LauncherActivity: il permesso dello splash "
                     "c'e' gia'")
    else:
        _ancora_una(ANCORA_ONCREATE, testo, percorso,
                    "del permesso dello splash (la prima riga di "
                    "onCreate, `super.onCreate(savedInstanceState);`)",
                    "aggiorna ANCORA_ONCREATE")
        testo = ANCORA_ONCREATE.sub(
            lambda m: (m.group(1) + _innesta(PERMESSO_SPLASH, m.group(2),
                                             a_capo)
                       + m.group(2) + m.group(3)), testo)
        righe.append("🔑 LauncherActivity.java: permesso dello splash "
                     "prima di super.onCreate() (Chrome 152+)")

    # 2) l'uscita dello splash di sistema (v1.5): subito sopra
    #    super.onCreate, cioe' dopo il permesso
    if MARCATORE_USCITA in testo:
        righe.append("🚪 LauncherActivity: l'uscita dello splash di "
                     "sistema c'e' gia'")
    else:
        _ancora_una(ANCORA_SUPER, testo, percorso,
                    "dell'uscita dello splash (la riga "
                    "`super.onCreate(savedInstanceState);`)",
                    "aggiorna ANCORA_SUPER")
        testo = ANCORA_SUPER.sub(
            lambda m: (_innesta(USCITA_SPLASH, m.group(1), a_capo)
                       + m.group(1) + m.group(2)), testo)
        righe.append("🚪 LauncherActivity.java: lo splash di sistema "
                     "esce di taglio (Android 12+)")

    # 3) le barre vere (v1.5): subito sotto la riga che prende la URL
    if MARCATORE_BARRE in testo:
        righe.append("📏 LauncherActivity: le barre vere c'erano gia'")
    else:
        _ancora_una(ANCORA_URL, testo, percorso,
                    "delle barre vere (in getLaunchingUrl, la riga "
                    "`Uri uri = super.getLaunchingUrl();`)",
                    "aggiorna ANCORA_URL")
        testo = ANCORA_URL.sub(
            lambda m: m.group(0) + _innesta(BARRE_VERE, m.group(1), a_capo),
            testo)
        righe.append("📏 LauncherActivity.java: le barre vere nella URL "
                     "di avvio (Android 11+)")
    return percorso, testo, righe


def prepara_manifest(progetto):
    """Il tema dell'avvio sulla SOLA LauncherActivity (v1.5), preparato
    in MEMORIA come prepara_launcher: stessa forma di ritorno, stesso
    fermarsi."""
    gradle = progetto / "app" / "build.gradle"
    if not (gradle.is_file() and RIGA_COLORE_SPLASH.search(
            gradle.read_text(encoding="utf-8"))):
        sys.exit(f"⛔ {gradle}: manca la riga che crea "
                 f"@color/backgroundColor, il colore dello splash che il "
                 f"tema dell'avvio usa — Bubblewrap ha cambiato il "
                 f"modello.\n{NON_BUILDARE} Guarda il file e aggiorna "
                 f"RIGA_COLORE_SPLASH in genera_icone_apk.py.")
    percorso = progetto / "app" / "src" / "main" / "AndroidManifest.xml"
    if not percorso.is_file():
        sys.exit(f"⛔ {percorso}: il manifest non c'e'.\n{NON_BUILDARE}")
    testo = percorso.read_bytes().decode("utf-8")
    quante = testo.count(ANCORA_MANIFEST)
    if quante != 1:
        sys.exit(f"⛔ {percorso.name}: l'ancora del tema dell'avvio "
                 f"(`{ANCORA_MANIFEST}`) compare {quante} volte invece "
                 f"di 1 — Bubblewrap ha cambiato il modello.\n"
                 f"{NON_BUILDARE} Guarda il file e aggiorna "
                 f"ANCORA_MANIFEST in genera_icone_apk.py.")
    dopo = testo.index(ANCORA_MANIFEST) + len(ANCORA_MANIFEST)
    apertura = testo[dopo:testo.index(">", dopo)]
    if ATTRIBUTO_TEMA in apertura:
        return percorso, testo, ["🎭 AndroidManifest: il tema dell'avvio "
                                 "c'e' gia'"]
    if "android:theme" in apertura:
        # un tema che non e' il nostro: Bubblewrap ne da' uno suo, e
        # scegliere fra i due non e' un mestiere da script
        sys.exit(f"⛔ {percorso.name}: LauncherActivity ha gia' un tema "
                 f"suo, e non e' {TEMA_AVVIO}.\n{NON_BUILDARE} Guarda il "
                 f"file: il modello di Bubblewrap e' cambiato.")
    # sulla riga sua, col rientro dell'attributo che segue; se l'elemento
    # fosse scritto su una riga sola, uno spazio e basta
    m = re.match(r"(\r?\n)([ \t]+)android:", testo[dopo:])
    giunta = m.group(1) + m.group(2) if m else " "
    nuovo = testo[:dopo] + giunta + ATTRIBUTO_TEMA + testo[dopo:]
    return percorso, nuovo, [f"🎭 AndroidManifest.xml: LauncherActivity "
                             f"col tema {TEMA_AVVIO} (opaco, splash "
                             f"arancio col barattolo)"]


def _scrivi(percorso, testo, righe):
    if percorso.read_bytes() != testo.encode("utf-8"):
        percorso.write_bytes(testo.encode("utf-8"))
    for riga in righe:
        print(riga)


def patch_launcher(progetto):
    # prepara e scrive i soli blocchi del Java (le prove la girano da sola)
    _scrivi(*prepara_launcher(progetto))


def patch_manifest(progetto):
    # prepara e scrive il solo tema nel manifest (idem)
    _scrivi(*prepara_manifest(progetto))


def genera():
    base = Path(__file__).resolve().parent
    progetto = Path(sys.argv[1]) if len(sys.argv) > 1 \
        else base.parent.parent / "barattolo-twa"
    res = progetto / "app" / "src" / "main" / "res"
    if not (res / "mipmap-anydpi-v26").is_dir():
        sys.exit(f"Progetto TWA non trovato in {progetto}")

    # PRIMA di tutto il resto, e SENZA scrivere: i due file di testo che
    # Bubblewrap rigenera si preparano in memoria, e se un'ancora manca
    # lo script si ferma qui — con nessun file del progetto ancora toccato
    ritocchi = [prepara_launcher(progetto), prepara_manifest(progetto)]
    for ritocco in ritocchi:
        _scrivi(*ritocco)

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
    genera_icona_avvio(res, barattolo)
    scrivi_tema_avvio(res)
    patch_gradle(progetto)
    print(f"🎨 sfondo iconBackground = {esadecimale} (campionato dagli angoli)")
    print("✅ Icone, splash e tema dell'avvio pronti: ora `bubblewrap build`.")


if __name__ == "__main__":
    genera()
