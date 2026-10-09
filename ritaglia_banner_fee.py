"""La prima pillola del banner delle commissioni P2P SENZA la barra rossa
(9 ott 2026, cantiere «banner-fee-primo-ingresso», richiesta di Andrea).

La prima volta che il banner si fa personale, il «2%» deve COMPARIRE e
poi essere barrato sotto gli occhi: ma la barra rossa e' disegnata DENTRO
`assets/p2p-banner-fee.webp`. Questo script ne ricava la prima pillola
pulita, `assets/p2p-banner-fee-senza-barra.webp`: il ritaglio dei primi
340 px (su 1000) a tutta altezza, dove solo i pixel sotto la barra (piu'
3 px di bordo sfumato) sono rifatti; tutto il resto e' il file com'e'.

COME SI RIFA' QUEL CHE LA BARRA COPRE, pezzo per pezzo:
- il «%» e' simmetrico a 180° (e' un carattere geometrico): il cerchietto
  in basso e' intatto, e ruotato attorno al centro del simbolo — cercato
  a mezzo decimo di pixel, minimizzando lo scarto fuori dalla barra —
  ridà il pezzo coperto;
- il «2» sotto la barra e' fatto di rette: la base (un rettangolo, i
  quattro lati misurati dove la barra non arriva) e il bordo destro della
  diagonale (prolungato dalle ultime righe visibili), con l'orlo sfumato
  di un pixel come quello del file;
- il fondo, per direzioni: ogni pixel prende la direzione in cui i due
  punti appena fuori dalla barra si somigliano di piu';
- e ogni colore rifatto torna sulla riga fondo–inchiostro, cosi' del
  rosso non resta niente.
Le strade scartate (la media lungo la normale, il ricucito per direzioni
anche sul «%»: tacche visibili) stanno in CANTIERI, «Il banner delle
commissioni, la prima volta».

FINITA LA BETA SI SOSTITUISCE IL BANNER (PRODUZIONE, «IL BANNER DELLE
COMMISSIONI P2P"): le misure qui sotto sono del file di oggi, e
`prove_banner_fee_primo_ingresso` confronta il ritaglio col banner fuori
dalla barra — un banner nuovo fa rosso la', e si rifa' girando questo.
Solo Pillow, niente rete. Uso: python ritaglia_banner_fee.py
"""
import math
import sys

SORGENTE = "assets/p2p-banner-fee.webp"
USCITA = "assets/p2p-banner-fee-senza-barra.webp"
LARGO = 340                       # il ritaglio: i primi 340 px su 1000
# la barra rossa del disegno, misurata sul file (le stesse misure di
# `.fee-barra` nel CSS): centro, lunghezza, spessore, inclinazione
CX, CY, LUNGA, SPESSA, ANGOLO = 177.6, 145.6, 175.8, 7.0, -36.88
BORDO = 3.0                       # i px di sfumatura rifatti attorno
# il «2» sotto la barra: la base e il bordo destro della diagonale,
# misurati fuori dalla barra (righe e colonne dove non arriva)
BASE = (111.7, 169.45, 161.8, 183.0)        # x0, y0, x1, y1
DIAGONALE_RIGHE = range(160, 168)            # le righe del bordo visibile

_th = math.radians(ANGOLO)
_UX, _UY = math.cos(_th), math.sin(_th)
_NX, _NY = -_UY, _UX


def sotto_la_barra(x, y, bordo=BORDO):
    """il pixel (x, y) sta sotto la barra, o nella sua sfumatura?"""
    dx, dy = x - CX, y - CY
    u = dx * _UX + dy * _UY
    v = dx * _NX + dy * _NY
    h = SPESSA / 2 + bordo
    if abs(v) > h:
        return False
    if abs(u) > LUNGA / 2:
        return math.hypot(abs(u) - LUNGA / 2, v) <= h
    return True


def _lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def ritaglia(im):
    """dal banner intero (PIL RGBA) al ritaglio senza barra. PURA."""
    px = im.load()

    def campiona(x, y):
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - x0, y - y0
        q = [px[x0, y0], px[x0 + 1, y0], px[x0, y0 + 1], px[x0 + 1, y0 + 1]]
        w = [(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy]
        return [sum(q[k][c] * w[k] for k in range(4)) for c in range(4)]

    # i due colori: il fondo della pillola e l'inchiostro del «2%»
    fondo, inch = [], []
    for y in range(95, 200):
        for x in range(95, 265):
            if sotto_la_barra(x, y) or math.hypot(x - CX, y - CY) > 140:
                continue
            p = px[x, y]
            (fondo if _lum(p) > 215 else inch if _lum(p) < 60 else []).append(p)
    B = [sum(p[c] for p in fondo) / len(fondo) for c in range(3)]
    K = [sum(p[c] for p in inch) / len(inch) for c in range(3)]
    BK = [K[c] - B[c] for c in range(3)]
    BK2 = sum(v * v for v in BK)

    def alfa(p):
        a = sum((p[c] - B[c]) * BK[c] for c in range(3)) / BK2
        return min(1.0, max(0.0, a))

    def colore(a, trasp):
        return [B[c] + a * BK[c] for c in range(3)] + [trasp]

    # il «%»: il riquadro e il centro della simmetria a 180°
    xs, ys = [], []
    for y in range(95, 200):
        for x in range(168, 262):
            if _lum(px[x, y]) < 100 and not sotto_la_barra(x, y):
                xs.append(x)
                ys.append(y)
    X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)

    def scarto(cx, cy):
        s, n = 0.0, 0
        for y in range(Y0 - 2, Y1 + 3, 2):
            for x in range(X0 - 2, X1 + 3, 2):
                rx, ry = 2 * cx - x, 2 * cy - y
                if sotto_la_barra(x, y) or sotto_la_barra(rx, ry):
                    continue
                s += abs(_lum(px[x, y]) - _lum(campiona(rx, ry)))
                n += 1
        return s / n

    cx, cy, passo = (X0 + X1) / 2, (Y0 + Y1) / 2, 2.0
    while passo > 0.05:
        m = min((scarto(cx + a, cy + b), cx + a, cy + b)
                for a in (-passo, 0, passo) for b in (-passo, 0, passo))
        if (m[1], m[2]) == (cx, cy):
            passo /= 2
        cx, cy = m[1], m[2]

    # il «2»: il bordo destro della diagonale, una retta x = a*y + b
    def incrocio_h(y, xa, xb):
        for x in range(xa, xb):
            a, b = alfa(px[x, y]), alfa(px[x + 1, y])
            if (a - .5) * (b - .5) <= 0 and a != b \
                    and not sotto_la_barra(x, y) and not sotto_la_barra(x + 1, y):
                return x + (a - .5) / (a - b)
        return None
    punti = []
    for y in DIAGONALE_RIGHE:
        s = incrocio_h(y, 112, 150)
        d = incrocio_h(y, int(s) + 3, 165) if s is not None else None
        if d is not None:
            punti.append((y, d))
    my = sum(p[0] for p in punti) / len(punti)
    mx = sum(p[1] for p in punti) / len(punti)
    pend = (sum((p[0] - my) * (p[1] - mx) for p in punti)
            / sum((p[0] - my) ** 2 for p in punti))
    norma = math.sqrt(1 + pend * pend)

    def alfa_due(x, y):
        bx0, by0, bx1, by1 = BASE
        d_base = max(bx0 - x, x - bx1, by0 - y, y - by1)
        a_base = min(1.0, max(0.0, .5 - d_base))
        a_diag = 0.0
        if 150 <= y <= by0 + 1:
            d_diag = (x - (mx + pend * (y - my))) / norma
            a_diag = min(1.0, max(0.0, .5 - d_diag))
        return max(a_base, a_diag)

    # il fondo, per direzioni
    def uscita(x, y, dx, dy):
        s = 0.0
        while sotto_la_barra(x + dx * s, y + dy * s):
            s += 0.5
            if s > 40:
                return None
        return s + 1.0
    angoli = [math.radians(a) for a in range(0, 180, 3)]

    def per_direzioni(x, y):
        scelte = []
        for a in angoli:
            dx, dy = math.cos(a), math.sin(a)
            s1, s2 = uscita(x, y, dx, dy), uscita(x, y, -dx, -dy)
            if s1 is None or s2 is None:
                continue
            p1 = campiona(x + dx * s1, y + dy * s1)
            p2 = campiona(x - dx * s2, y - dy * s2)
            t = s2 / (s1 + s2)
            scelte.append((sum(abs(p1[c] - p2[c]) for c in range(3)) + 1.2 * (s1 + s2),
                           [p2[c] * (1 - t) + p1[c] * t for c in range(4)]))
        scelte.sort(key=lambda z: z[0])
        m = scelte[:3]
        w = [1.0 / (1 + z[0]) for z in m]
        return [sum(z[1][c] * q for z, q in zip(m, w)) / sum(w) for c in range(4)]

    fuori = im.crop((0, 0, LARGO, im.size[1]))
    opx = fuori.load()
    for y in range(int(CY - 80), int(CY + 80)):
        for x in range(int(CX - 100), int(CX + 100)):
            if not sotto_la_barra(x, y):
                continue
            rx, ry = 2 * cx - x, 2 * cy - y
            if X0 - 3 <= x <= X1 + 3 and Y0 - 3 <= y <= Y1 + 3 \
                    and not sotto_la_barra(rx, ry):
                v = colore(alfa(campiona(rx, ry)), px[x, y][3])
            elif x < 165:
                v = colore(alfa_due(x, y), px[x, y][3])
            else:
                v = colore(alfa(per_direzioni(x, y)), px[x, y][3])
            opx[x, y] = tuple(int(c + .5) for c in v)
    return fuori


def main():
    from PIL import Image
    with Image.open(SORGENTE) as im:
        fuori = ritaglia(im.convert("RGBA"))
    # la stessa ricetta del banner: WebP con trasparenza, niente ICC,
    # EXIF ne' XMP (Pillow non ne scrive se non glieli si da')
    fuori.save(USCITA, "WEBP", quality=90, method=6)
    print("fatto: %s, %dx%d" % (USCITA, fuori.size[0], fuori.size[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
