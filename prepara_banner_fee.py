"""IL BANNER DELLE COMMISSIONI P2P SENZA CAPSULA (26 set 2026, richiesta di
Andrea): toglie dall'immagine il fondo marrone della capsula — rossiccio
gia' nel disegno — e lo lascia trasparente, tenendo intatte le tre
pillole, le frecce fra le pillole e l'etichetta BETA. La capsula la
disegna il CSS dietro l'immagine, col colore delle card del tema (vedi
il CSS di `.p2p-fee-banner`).

PERCHE' NON BASTA «TOGLIERE IL MARRONE»: attorno alle pillole il disegno
ha un filo scuro-rossiccio di due o tre pixel, che col marrone tolto
diventerebbe un alone su una card chiara. Quindi i bordi si RICOSTRUISCONO
dalla forma: le pillole sono stadi, l'etichetta un rettangolo tondo, e le
frecce stanno in dischi scuri semitrasparenti; le forme si MISURANO sul
file (a meta' strada fra il marrone e il pieno, come la prova che le
rimisura), e per ogni pixel:
  - dentro una forma, oltre la fascia del bordo: il pixel del disegno;
  - nella fascia del bordo: copertura calcolata dalla forma, e il colore
    preso un po' piu' dentro, dove il filo scuro non c'e';
  - dentro un disco, dove sotto c'era il marrone fra due pillole: l'ombra
    del disco, nera e semitrasparente — sopra la card fa quel che faceva
    sopra le pillole; la freccia chiara resta com'e';
  - fuori da tutto: trasparente.

Uso:  python prepara_banner_fee.py <ingresso> <uscita.webp>
L'ingresso e' il banner gia' ridotto a 1000×258 COL SUO MARRONE (la ricetta
di PRODUZIONE, «IL BANNER DELLE COMMISSIONI P2P»): le forme si misurano
partendo dal marrone, quindi su un'uscita non si rilancia — se il disegno
non e' quello atteso, lo script si ferma invece di indovinare."""
import math
import sys

from PIL import Image

FONDO = (52, 32, 25)          # il marrone pieno della capsula
FASCIA = 2.0                  # px dentro il bordo a meta' strada: li' c'e' il filo scuro
DENTRO = 3.0                  # da dove si prende il colore della fascia
OMBRA_DISCO = 0.2             # l'ombra dei dischi, dove sotto non c'e' una pillola


def dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def misura(im):
    px = im.load()
    W, H = im.size

    def bordo(punti, pieno):
        prima, visto = None, False
        for c, (x, y) in punti:
            p = px[x, y]
            if not visto:
                visto = p[3] > 250 and dist(p, FONDO) < 30
                continue
            t = dist(p, FONDO) / (dist(p, FONDO) + dist(p, pieno) + 1e-9)
            if t >= 0.5:
                if prima is None:
                    return c
                c0, t0 = prima
                return c0 + (0.5 - t0) / (t - t0) * (c - c0)
            prima = (c, t)
        raise SystemExit("bordo non trovato: il disegno non e' quello atteso")

    pillole = []
    for cx, sx, dx in ((180, 0, 330), (470, 335, 625), (870, 630, 999)):
        pieno = px[cx, 200][:3]      # sotto le scritte: il pieno della pillola
        top = bordo([(y, (cx, y)) for y in range(0, 129)], pieno)
        bot = bordo([(y, (cx, y)) for y in range(H - 1, 129, -1)], pieno)
        R, cy = (bot - top) / 2, (top + bot) / 2
        estremi = []
        for lato in (-1, 1):
            stime = []
            for dy in (-70, -60, 60, 70):
                y = int(round(cy + dy))
                xs = range(sx, cx) if lato < 0 else range(dx, cx, -1)
                e = bordo([(x, (x, y)) for x in xs], pieno)
                off = math.sqrt(max(R * R - (y - cy) ** 2, 0))
                stime.append(e + off - R if lato < 0 else e - off + R)
            estremi.append(sum(stime) / len(stime))
        pillole.append((estremi[0], top, estremi[1], bot))
    # l'etichetta BETA della terza: fianchi a riga 20, cima a colonna 770
    tag = px[796, 12][:3]
    tl = bordo([(x, (x, 20)) for x in range(725, 796)], tag)
    tr = bordo([(x, (x, 20)) for x in range(870, 796, -1)], tag)
    tt = bordo([(y, (770, y)) for y in range(1, 20)], tag)
    etichetta = (tl, tt, tr, 40.0, 10.5)
    # i dischi delle frecce: dove il pieno delle due pillole si scurisce,
    # sulla riga di mezzo
    dischi = []
    for p_sx, p_dx in ((pillole[0], pillole[1]), (pillole[1], pillole[2])):
        x0 = (p_sx[2] + p_dx[0]) / 2
        cy = (p_sx[1] + p_sx[3]) / 2
        y = int(round(cy))
        fs, fd = px[int(x0 - 45), y][:3], px[int(x0 + 45), y][:3]
        sx = next(x for x in range(int(x0 - 45), int(x0)) if dist(px[x, y], fs) > 25)
        dx = next(x for x in range(int(x0 + 45), int(x0), -1) if dist(px[x, y], fd) > 25)
        dischi.append(((sx + dx) / 2, cy, (dx - sx) / 2 + 0.5))
    return pillole, etichetta, dischi


def sdf_stadio(x, y, box, raggio=None):
    """distanza col segno da un rettangolo tondo (negativa dentro);
    senza raggio e' uno stadio (raggio = meta' altezza)"""
    x0, y0, x1, y1 = box
    r = raggio if raggio is not None else (y1 - y0) / 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    qx = abs(x - cx) - ((x1 - x0) / 2 - r)
    qy = abs(y - cy) - ((y1 - y0) / 2 - r)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r


def main(ingresso, uscita):
    im = Image.open(ingresso).convert("RGBA")
    W, H = im.size
    pillole, etichetta, dischi = misura(im)
    src = im.load()
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dst = out.load()
    forme = [(b, None) for b in pillole] + [(etichetta[:4], etichetta[4])]

    def d_forma(x, y):
        return min(sdf_stadio(x, y, b, r) for b, r in forme)

    for y in range(H):
        for x in range(W):
            X, Y = x + 0.5, y + 0.5
            d = d_forma(X, Y)
            dd = min(math.hypot(X - cx, Y - cy) - r for cx, cy, r in dischi)
            p = src[x, y]
            if dd <= 0.5:
                cov_d = min(1.0, 0.5 - dd)
                if d <= -FASCIA:
                    dst[x, y] = p[:3] + (255,)
                    continue
                # la freccia: chiara, resta com'e'
                if 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] > 150:
                    dst[x, y] = p[:3] + (int(round(255 * cov_d)),)
                    continue
                if d >= 0.5:
                    # sotto c'era il marrone: resta l'ombra del disco
                    dst[x, y] = (0, 0, 0, int(round(255 * OMBRA_DISCO * cov_d)))
                    continue
                # il bordo di una pillola sotto il disco: il suo colore
                # (gia' scurito dal disco) preso piu' dentro
            if d >= 0.5:
                continue                      # fuori: trasparente
            if d <= -FASCIA:
                dst[x, y] = p[:3] + (255,)
                continue
            # LA FASCIA DEL BORDO: copertura dalla forma, colore da dentro
            cov = min(1.0, 0.5 - d)
            e = 0.5
            gx = (d_forma(X + e, Y) - d_forma(X - e, Y))
            gy = (d_forma(X, Y + e) - d_forma(X, Y - e))
            n = math.hypot(gx, gy) or 1.0
            passo = DENTRO + d               # fino a DENTRO px dentro il bordo
            sx = min(W - 1, max(0, int(round(X - gx / n * passo - 0.5))))
            sy = min(H - 1, max(0, int(round(Y - gy / n * passo - 0.5))))
            c = src[sx, sy][:3]
            if dd <= 0.5:
                cov = max(cov, OMBRA_DISCO)
            dst[x, y] = c + (int(round(255 * cov)),)
    out.save(uscita, "WEBP", quality=86, method=6, alpha_quality=100)
    print("pillole:", [tuple(round(v, 2) for v in b) for b in pillole])
    print("etichetta:", tuple(round(v, 2) for v in etichetta))
    print("dischi:", [tuple(round(v, 2) for v in d) for d in dischi])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
