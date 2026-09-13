# -*- coding: utf-8 -*-
"""
SPOGLIA LE FOTO GIA' PUBBLICATE — la passata una-tantum sui file che
stanno gia' in foto/ (set 2026, cantiere «niente GPS nelle foto»).

COS'ERA SUCCESSO: la Mini App non ha mai mandato al server il file
scelto — lo ridisegna in un canvas, e un JPEG che esce da un canvas i
metadati non li sa nemmeno scrivere — quindi le foto caricate a mano
sono sempre state nude. Ma l'import CSV/ZIP e i connettori passavano i
byte VERBATIM (il ramo di `normalizza_foto_import` nato per non
ricomprimere due volte), e da li' una foto poteva arrivare in vetrina
con dentro il GPS di dove era stata scattata.

Il TAPPO e' gia' nel codice: da adesso ogni porta spoglia. Questo
script si occupa dei file gia' sul disco.

COSA FA: legge foto/ e dice quante foto portano ancora dei metadati e
quante portano il GPS. Con --scrivi le riscrive senza — tagliando i
segmenti, mai ricomprimendo: i pixel restano quelli, e lo script lo
VERIFICA file per file prima di sostituire (se i pixel non tornassero
si ferma su quel file e lo dice).

LE FUNZIONI NON SONO UNA COPIA: si estraggono da server.py, che e' la
fonte unica — un gemello scritto qui divergerebbe al primo ritocco.

COSA NON TOCCA, ed e' dichiarato: la busta di ritiro (buste/) e la
foto del contenuto digitale (contenuti/), che sul disco stanno
CIFRATE — per spogliare quelle servirebbe la chiave, e una passata che
chiede la chiave dei contenuti di tutti e' un attrezzo diverso da
questo. Da adesso nascono gia' pulite; quelle vecchie le legge solo la
controparte di quell'ordine.

USO (dalla cartella del progetto):
    python spoglia_foto_esistenti.py            # ANTEPRIMA: cosa c'e'
    python spoglia_foto_esistenti.py --scrivi   # le riscrive

Si puo' girare a server acceso: ogni file si sostituisce intero con
os.replace, che e' atomico — chi lo sta scaricando in quel momento
prende la vecchia o la nuova, mai meta' e meta'. Idempotente:
rilanciarlo a lavoro fatto non trova piu' niente.
"""
import io
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
FOTO_DIR = os.path.join(QUI, "foto")

try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, OSError):
    pass

try:
    from PIL import Image as ImmaginePillow, ImageOps
except ImportError:
    ImmaginePillow = ImageOps = None


def _da_server():
    """I pezzi VERI presi dal sorgente di server.py: importarlo
    vorrebbe dire config.py, anthropic e mezzo mondo, e riscriverli
    qui vorrebbe dire un gemello. Stessa strada di ricategorizza.py."""
    src = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
    amb = {"io": io, "ImmaginePillow": ImmaginePillow, "ImageOps": ImageOps}
    i = src.index("SEGMENTI_JPEG_TENUTI = ")
    exec(src[i:src.index("\n\n\n", i)], amb)
    for nome in ("_spoglia_jpeg", "_spoglia_png", "_spoglia_webp",
                 "_porta_metadati", "spoglia_metadati"):
        i = src.index(f"def {nome}(")
        exec(src[i:src.index("\n\n\n", i)], amb)
    return amb


def _pixel(raw):
    """I pixel, non i byte: e' la misura che dice se qualcosa e' stato
    ricompresso — e qui sarebbe un difetto, non una rifinitura."""
    with ImmaginePillow.open(io.BytesIO(raw)) as im:
        return im.convert("RGB").tobytes()


def _gps(raw):
    with ImmaginePillow.open(io.BytesIO(raw)) as im:
        return dict(im.getexif().get_ifd(0x8825))


def main():
    scrivi = "--scrivi" in sys.argv[1:]
    if not ImmaginePillow:
        print("serve Pillow: pip install pillow")
        return 1
    if not os.path.isdir(FOTO_DIR):
        print(f"cartella non trovata: {FOTO_DIR}")
        return 1
    amb = _da_server()
    spoglia, porta = amb["spoglia_metadati"], amb["_porta_metadati"]

    tot = sporche = con_gps = riscritte = arenate = 0
    for nome in sorted(os.listdir(FOTO_DIR)):
        percorso = os.path.join(FOTO_DIR, nome)
        if not os.path.isfile(percorso):
            continue
        tot += 1
        try:
            raw = open(percorso, "rb").read()
        except OSError as e:
            print(f"  non si legge: {nome} ({e})")
            continue
        if not porta(raw):
            continue
        sporche += 1
        try:
            gps = _gps(raw)
        except Exception:
            gps = {}
        if gps:
            con_gps += 1
        etichetta = "CON GPS" if gps else "metadati"
        pulito = spoglia(raw)
        if pulito is None:
            arenate += 1
            print(f"  ⚠️ {nome}: {etichetta}, ma non si sa spogliarla "
                  f"senza ricomprimere — lasciata com'e'")
            continue
        if not scrivi:
            print(f"  {nome}: {etichetta} — si toglierebbero "
                  f"{len(raw) - len(pulito)} byte")
            continue
        # LA GUARDIA: i pixel devono essere gli stessi. Se non lo sono
        # il file NON si tocca — meglio una foto con dentro un dato di
        # troppo che una vetrina che cambia da sola.
        try:
            if _pixel(raw) != _pixel(pulito):
                arenate += 1
                print(f"  ⚠️ {nome}: i pixel non tornano — lasciata com'e'")
                continue
        except Exception as e:
            arenate += 1
            print(f"  ⚠️ {nome}: non si rilegge dopo la spoliazione "
                  f"({e}) — lasciata com'e'")
            continue
        tmp = percorso + ".nuova"
        with open(tmp, "wb") as out:
            out.write(pulito)
        os.replace(tmp, percorso)      # atomico: mai meta' file servito
        riscritte += 1
        print(f"  ✓ {nome}: {etichetta} tolti "
              f"({len(raw) - len(pulito)} byte in meno)")

    print(f"\nfile guardati: {tot}")
    print(f"con metadati: {sporche}   (di cui col GPS: {con_gps})")
    if arenate:
        print(f"lasciate com'erano: {arenate}")
    if scrivi:
        print(f"riscritte: {riscritte}")
    elif sporche:
        print("\nanteprima: nessun file e' stato toccato. "
              "Per farlo davvero: python spoglia_foto_esistenti.py --scrivi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
