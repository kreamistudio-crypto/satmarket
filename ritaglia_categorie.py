"""Prepara le illustrazioni della pagina Sfoglia: le ritaglia e le
PAREGGIA, cosi' in griglia sembrano tutte della stessa taglia.

PERCHE' ESISTE, in due tempi.

1) IL RITAGLIO. Le illustrazioni arrivano come quadrati 512x512 col
disegno al centro e circa il 30% di margine trasparente attorno. Quel
margine e' spazio che la piastrella paga: il disegno puo' essere alto
al massimo quanto la fascia sotto il nome, e se un terzo e' vuoto, il
disegno si vede piccolo.
L'alpha si guarda SOPRA UNA SOGLIA e non sopra lo zero: un file
arrivava con una velatura quasi invisibile stesa su tutta la tela, e
col confronto a zero risultava gia' tirato mentre il disegno vero ne
occupava meno di meta'.

2) IL PAREGGIO, che e' la parte meno ovvia. Ritagliate e basta, le
illustrazioni sembrano ancora di taglie diverse — e non per colpa del
loro rettangolo: un pallone e una chitarra possono occupare lo stesso
rettangolo, ma il pallone e' pieno e la chitarra e' un filo, quindi il
pallone «pesa» il triplo. A contare e' l'INCHIOSTRO, cioe' quanti
pixel pieni il disegno copre davvero. Qui si misura quello e si mette
un TETTO: chi lo supera riceve un bordo trasparente attorno, che in
pagina lo rende piu' piccolo senza toccare il disegno.
Non si puo' fare il contrario — ingrandire i piu' leggeri — perche'
sono gia' al massimo che la piastrella concede: la chitarra resta la
piu' leggera, ed e' un limite dichiarato.

Idempotente: rilanciarlo non riscrive nulla se i file sono gia' a
posto (i WebP sono lossy, e la regola della compressione unica vale
anche qui). Va rilanciato quando si aggiunge o si rifa'
un'illustrazione; `prove.py` controlla che il tetto sia rispettato.

    python ritaglia_categorie.py            # dice cosa farebbe
    python ritaglia_categorie.py --scrivi   # lo fa
"""
import os
import sys

CARTELLA = os.path.join("assets", "categorie")
QUALITA = 92
# Sotto il visibile, ma sopra l'antialiasing dei bordi: e' la soglia
# che smaschera la velatura invisibile senza mangiare i contorni.
SOGLIA_ALPHA = 8
# Il riquadro del CSS a 360px (.cat-fig: width 54% di 159, e l'altezza
# che resta sotto il nome). Serve solo a sapere CHI e' limitato in
# larghezza e chi in altezza — se quelle misure cambiassero di molto,
# il pareggio andrebbe rifatto.
BOX_W, BOX_H = 85.9, 75.0
# Il tetto, in multipli dell'inchiostro MEDIANO: 1.05 lascia stare la
# meta' piu' leggera e calma solo chi sporge.
TETTO = 1.05
# I RITOCCHI A MANO, guardando la pagina vera: la misura
# dell'inchiostro porta lontano ma non decide tutto — una ciotola vista
# dall'alto «pesa» piu' di quanto dica il suo inchiostro. Qui il
# moltiplicatore sul tetto per le singole voci: sotto 1 = piu' piccola.
# Chi ne aggiunge una lo faccia dopo aver guardato la griglia intera,
# non la singola piastrella.
RITOCCHI = {"animali": .68}
# La SOGLIA per-voce, seconda tabellina dei ritocchi (ago 2026, nata
# col biglietto di «Buoni ed esperienze»): il file arrivava con un
# alone tenue — alpha fra 8 e 32 — steso su TUTTA la tela, quindi con
# la soglia globale risultava gia' tirato mentre il disegno vero
# (378x268) stava appoggiato in ALTO, e in piastrella si vedeva
# piccolo e alto. Alzare la soglia solo per lui ritaglia l'alone senza
# toccare il disegno, che cresce e si ricentra; alzarla per TUTTI
# mangerebbe l'antialiasing dei bordi delle altre 26. Chi aggiunge una
# voce misuri prima il bbox a piu' soglie, come per la velatura di
# Bellezza.
SOGLIE = {"buoni-ed-esperienze": 32}
# Sotto questo scarto non si riscrive: un ritocco da pochi pixel non
# vale una seconda compressione.
MINIMO = .02
# Il francobollo per il foglio-picker di Vendi, dove l'illustrazione
# sta in una pastiglia da ~32px: il file pieno la' dentro sarebbe uno
# spreco (26 file da 512px, 787 KB e 13 MB di bitmap da decodificare,
# per un menu che si apre in due secondi). 128px danno margine anche
# sugli schermi a 3x. Stessa idea delle miniature `_min` delle foto.
LATO_MINI = 128
SUFFISSO_MINI = "-mini"


def _misura(im, soglia=SOGLIA_ALPHA):
    """riquadro del disegno, inchiostro e resa nel riquadro del CSS"""
    from PIL import Image  # noqa: F401  (serve solo al chiamante)
    a = im.getchannel("A")
    bb = a.point(lambda v: 255 if v > soglia else 0).getbbox()
    if bb is None:
        return None, 0, 0
    disegno = im.crop(bb)
    ad = disegno.getchannel("A")
    inchiostro = sum(n * i for i, n in enumerate(ad.histogram())) / 255.0
    w, h = disegno.size
    s = min(BOX_W / w, BOX_H / h)
    return bb, inchiostro, inchiostro * s * s


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

    file = sorted(f for f in os.listdir(CARTELLA)
                  if f.endswith(".webp")
                  and not f.endswith(SUFFISSO_MINI + ".webp"))
    misure = {}
    for nome in file:
        im = Image.open(os.path.join(CARTELLA, nome)).convert("RGBA")
        bb, ink, reso = _misura(im, SOGLIE.get(nome[:-5], SOGLIA_ALPHA))
        if bb is None:
            print(f"  ⚠ {nome}: tutto trasparente, lasciato com'e'")
            continue
        misure[nome] = (im, bb, ink, reso)

    if not misure:
        return 1
    resi = sorted(m[3] for m in misure.values())
    mediana = resi[len(resi) // 2]
    tetto = mediana * TETTO
    print(f"inchiostro mediano {mediana:.0f}, tetto {tetto:.0f}\n")

    fatti = fermi = 0
    for nome, (im, bb, ink, reso) in misure.items():
        disegno = im.crop(bb)
        w, h = disegno.size
        # quanto bordo serve perche' il reso scenda sotto il tetto
        suo = tetto * RITOCCHI.get(nome[:-5], 1.0)
        p = max(1.0, (reso / suo) ** .5) if suo else 1.0
        nw, nh = round(w * p), round(h * p)
        vecchio = im.size
        if (abs(nw - vecchio[0]) <= MINIMO * nw
                and abs(nh - vecchio[1]) <= MINIMO * nh):
            fermi += 1
            continue
        tela = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
        tela.alpha_composite(disegno, ((nw - w) // 2, (nh - h) // 2))
        quanto = "" if p == 1.0 else f"  −{100*(1-1/p):.0f}% in pagina"
        print(f"  {nome[:-5]:26s} {vecchio[0]}x{vecchio[1]} → {nw}x{nh}"
              f"   inchiostro {reso/mediana:.2f}x{quanto}")
        if scrivi:
            tela.save(os.path.join(CARTELLA, nome), "WEBP",
                      quality=QUALITA, method=6)
        fatti += 1

    print(f"\n{fatti} da sistemare, {fermi} gia' a posto")

    # I francobolli per il picker, rifatti SEMPRE dai file finali (cioe'
    # dopo ritaglio e pareggio): cosi' nel menu le proporzioni sono le
    # stesse della griglia, senza un secondo posto dove tararle.
    mini_fatti = mini_fermi = 0
    peso = 0.0
    for nome in file:
        pieno = os.path.join(CARTELLA, nome)
        mini = os.path.join(CARTELLA, nome[:-5] + SUFFISSO_MINI + ".webp")
        im = Image.open(pieno).convert("RGBA")
        s = LATO_MINI / max(im.size)
        atteso = (max(1, round(im.size[0] * s)), max(1, round(im.size[1] * s)))
        if os.path.exists(mini) and Image.open(mini).size == atteso and not scrivi:
            mini_fermi += 1
            peso += os.path.getsize(mini) / 1024
            continue
        if scrivi:
            im.resize(atteso, Image.LANCZOS).save(
                mini, "WEBP", quality=QUALITA, method=6)
            peso += os.path.getsize(mini) / 1024
            if os.path.exists(mini):
                mini_fatti += 1
        else:
            mini_fatti += 1
    if scrivi:
        print(f"{mini_fatti} francobolli da {LATO_MINI}px, "
              f"{peso:.0f} KB in tutto")
    else:
        print(f"{mini_fatti} francobolli da rifare, {mini_fermi} a posto")

    if (fatti or mini_fatti) and not scrivi:
        print("niente e' stato scritto: rilancia con --scrivi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
