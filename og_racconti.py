"""Prepara le ANTEPRIME DEI NEGOZI CON LA STORIA: la copertina di ogni
pagina raccontata (`assets/racconti/<slug>-cop.webp`, l'hero 21:9 col
nome dentro) in JPEG, per l'og:image di /negozio/{chi} (30 set 2026).

PERCHE' NON SI PUNTA LA COPERTINA COM'E'. E' un WebP, e il WebP non lo
digeriscono tutti i crawler — la ragione gia' scritta in testa a
og_categorie.py, che per i reparti ha fatto la stessa strada. Qui il
fondo e' gia' opaco (la copertina e' una foto intera, niente alpha),
quindi non c'e' niente da comporre: si ridimensiona e si cambia
formato, e basta.

LA MISURA E' UNA SOLA, 1200x514, ed e' la ragione per cui il server la
puo' DICHIARARE (`OG_RACCONTO`) invece di omettere width e height: le
copertine si consegnano 21:9 (e' scritto accanto al catalogo), e
ImageOps.fit le porta tutte allo stesso lato — quelle consegnate un
filo fuori rapporto perdono qualche pixel ai bordi, mai il centro dove
sta il nome. NON 1200x630: la tela del 1.91:1 vorrebbe due bande sopra
e sotto il disegno, o un ritaglio che mangia i lati del nome; il 21:9
lo mostra intero Telegram, e WhatsApp lo disegna grande lo stesso
(il lato corto sta sopra i suoi 300).

QUANDO SI GENERANO: a mano, quando arriva una copertina nuova, e i file
si COMMITTANO — il patto di og_categorie.py: niente Pillow dentro la
richiesta di un crawler. Idempotente: scrive SOLO se i byte cambiano.

    python og_racconti.py            # dice cosa farebbe
    python og_racconti.py --scrivi   # lo fa
"""
import io
import os
import re
import sys

SORGENTE = os.path.join("assets", "racconti")
CARTELLA = os.path.join("assets", "og")
# gemella di OG_RACCONTO in server.py, e c'e' la prova che le tiene in pari
LARGO, ALTO = 1200, 514
QUALITA = 85
TETTO_BYTE = 280 * 1024
FORMA = re.compile(r"^([a-z0-9-]{2,40})-cop\.webp$")


def componi(percorso: str) -> bytes:
    from PIL import Image, ImageOps
    with Image.open(percorso) as im:
        tela = ImageOps.fit(im.convert("RGB"), (LARGO, ALTO),
                            Image.LANCZOS, centering=(0.5, 0.5))
    # IL TETTO DI WHATSAPP: sopra i ~300 KB l'anteprima non la disegna
    # affatto, quindi la qualita' scende a passi finche' ci sta sotto
    # con margine. Niente metadati e niente progressive: byte stabili.
    for q in range(QUALITA, 59, -5):
        buf = io.BytesIO()
        tela.save(buf, "JPEG", quality=q, optimize=True)
        if buf.tell() <= TETTO_BYTE:
            break
    return buf.getvalue()


def main(scrivi: bool) -> int:
    fatti = 0
    for nome in sorted(os.listdir(SORGENTE)):
        m = FORMA.match(nome)
        if not m:
            continue
        dest = os.path.join(CARTELLA, f"racconto-{m.group(1)}.jpg")
        nuovi = componi(os.path.join(SORGENTE, nome))
        vecchi = open(dest, "rb").read() if os.path.exists(dest) else b""
        if nuovi == vecchi:
            print(f"= {dest} (uguale)")
            continue
        fatti += 1
        if scrivi:
            with open(dest, "wb") as f:
                f.write(nuovi)
            print(f"✓ {dest} ({len(nuovi) // 1024} KB)")
        else:
            print(f"… {dest} da scrivere ({len(nuovi) // 1024} KB)")
    if fatti and not scrivi:
        print("\nRilancia con --scrivi per scriverli.")
    return 0


if __name__ == "__main__":
    sys.exit(main("--scrivi" in sys.argv))
