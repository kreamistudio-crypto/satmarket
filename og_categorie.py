"""Compone le ANTEPRIME dei reparti: le 29 illustrazioni delle
categorie su una tela opaca, per l'og:image di /categoria/{slug}.

PERCHE' NON SI PUO' USARE L'ILLUSTRAZIONE COM'E'. I file di
assets/categorie/ sono WebP SCONTORNATI su trasparenza: perfetti nella
striscia, dove il fondo bruno lo mette il CSS, e inadatti a un
og:image — un'immagine con l'alpha ogni client la compone sul fondo
che gli pare (e' la stessa ragione per cui IMMAGINE_BRAND e'
l'icona-512 e non l'hero, che il commento la' dichiara). Il WebP in
piu' non lo digeriscono tutti i crawler.

Qui la tela si dipinge col bruno di casa e il disegno ci si posa
sopra: JPEG opaco, un formato che leggono tutti.

NIENTE TESTO NELLA FIGURA, ed e' la stessa decisione del podio del
lunedi': il nome del reparto sta nell'og:title, due righe sotto la
card, dove nessuna piattaforma lo tronca e dove non serve nessun
font. Cosi' la composizione e' DETERMINISTICA — stessa sorgente,
stessi byte — e non c'e' un secondo posto in cui il nome puo' essere
sbagliato.

QUANDO SI GENERANO: **una volta a mano**, e i file si committano. Non
al volo: comporre nel percorso del crawler vorrebbe dire Pillow dentro
una richiesta (che e' un import fail-open, quindi puo' mancare) e una
latenza a ogni anteprima, per un'immagine che cambia solo quando
cambia l'illustrazione. Committati sono trenta file che non si
muovono, e il server non fa altro che servirli.

Idempotente: rigenera in memoria e scrive SOLO se i byte cambiano —
quindi rilanciarlo non ricomprime niente, ed e' la regola della
compressione unica applicata a un formato lossy.

    python og_categorie.py            # dice cosa farebbe
    python og_categorie.py --scrivi   # lo fa
"""
import io
import os
import re
import sys

SORGENTE = os.path.join("assets", "categorie")
CARTELLA = os.path.join("assets", "og")

# 1200x630 e' il rapporto 1.91:1 delle card grandi — quello che
# Telegram, WhatsApp e Facebook disegnano in grande invece che come
# francobollo di fianco al titolo. Il lato corto (630) sta comodamente
# sopra il minimo piu' alto dei tre, che e' WhatsApp a 300.
LARGO, ALTO = 1200, 630
# La scatola in cui il disegno sta: CONTENUTO, mai ritagliato — le
# illustrazioni sono gia' tirate (ci pensa ritaglia_categorie.py) e un
# ritaglio qui mangerebbe il disegno.
# Il rapporto e' ~1,15, quello del riquadro della striscia, ed e' la
# riga che tiene valido il PAREGGIO DELL'INCHIOSTRO: ritaglia_categorie
# bilancia i disegni per un riquadro di quella forma (85.9x75), quindi
# contenerli in una scatola con un rapporto diverso li ripeserebbe uno
# per uno e la fila tornerebbe sbilanciata.
# Si INGRANDISCE, e va detto: le sorgenti stanno fra 240 e 464px di
# lato, cioe' fino a ~1,9x — su un disegno piatto LANCZOS regge (la
# prova e' guardarli, ed e' stata fatta), su una foto non reggerebbe.
BOX = (540, 470)
QUALITA = 85

# Il bruno di casa, il `--cat-fondo` del TEMA CHIARO. Un valore FISSO
# e non i due del token, ed e' il patto del cartellino prezzo: questa
# e' una figura che si compone una volta e vive dentro l'anteprima di
# un'altra app — non ha un tema da seguire, e sceglierne uno la sera
# non vorrebbe dire niente.
FONDO = (0x33, 0x2A, 0x19)


def categorie():
    """Il catalogo e lo slug letti dal TESTO di server.py, mai
    importandolo: l'import farebbe partire init_db e le migrazioni su
    un database che magari non e' quello giusto (la lezione di
    ricategorizza.py)."""
    s = io.open("server.py", encoding="utf-8").read()
    i = s.index("CATEGORIE = (")
    voci = re.findall(r'"([^"]+)"', s[i:s.index(")", i)])
    # lo slug e' quello di `slug_categoria`, LETTERALMENTE: una terza
    # ricetta dello stesso nome e' il posto da cui un giorno divergono
    return [(c, c.lower().replace(" ", "-")) for c in voci]


def componi(percorso, Image, ImageOps):
    im = Image.open(percorso).convert("RGBA")
    # `contain` e non `thumbnail`: quello NON INGRANDISCE MAI, e le
    # illustrazioni sono piu' piccole della scatola — restavano alla
    # loro misura nativa in mezzo a un mare di bruno (visto, non
    # dedotto: il primo giro le faceva larghe un quarto della tela).
    im = ImageOps.contain(im, BOX, Image.LANCZOS)
    tela = Image.new("RGB", (LARGO, ALTO), FONDO)
    # `im` come maschera di se stessa: e' l'alpha a decidere dove il
    # disegno copre il bruno, o attorno resterebbe il nero della tela
    # RGBA appiattita.
    tela.paste(im, ((LARGO - im.width) // 2, (ALTO - im.height) // 2), im)
    b = io.BytesIO()
    tela.save(b, "JPEG", quality=QUALITA, optimize=True, progressive=True)
    return b.getvalue()


def main():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("Serve Pillow: pip install pillow")
        return 1
    scrivi = "--scrivi" in sys.argv
    if scrivi:
        os.makedirs(CARTELLA, exist_ok=True)
    fatti = uguali = 0
    manca = []
    for nome, slug in categorie():
        src = os.path.join(SORGENTE, f"{slug}.webp")
        if not os.path.exists(src):
            manca.append(nome)
            continue
        dati = componi(src, Image, ImageOps)
        dest = os.path.join(CARTELLA, f"{slug}.jpg")
        vecchi = open(dest, "rb").read() if os.path.exists(dest) else b""
        if dati == vecchi:
            uguali += 1
            continue
        fatti += 1
        print(f"  {slug}.jpg  {len(dati)//1024} KB"
              + ("" if scrivi else "   (da scrivere)"))
        if scrivi:
            with open(dest, "wb") as f:
                f.write(dati)
    for nome in manca:
        print(f"  ⚠️  {nome}: manca l'illustrazione, niente anteprima")
    print(f"\n{fatti} da fare, {uguali} gia' a posto"
          if not scrivi else f"\n{fatti} scritte, {uguali} gia' a posto")
    if not scrivi and fatti:
        print("Rilancia con --scrivi per farle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
