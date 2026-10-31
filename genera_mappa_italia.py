"""LA SAGOMA DELL'ITALIA PER LA MAPPA DEL CONTANTI (31 ott 2026, cantiere
mappa-contanti). Disegna `assets/italia-punti.svg` dai ~7.900 comuni di
`dati/comuni.csv`: un puntino per ogni casella di griglia che ha almeno un
comune, e l'Italia si disegna da sola, isole comprese. Nessun dato di
confini da scaricare, nessun terzo da cui farsi dare i tasselli: la mappa
la serve il nostro server, e chi guarda non lo dice a nessun altro.

LA PROIEZIONE e' una equirettangolare schiacciata sul coseno di 42°
(il parallelo di mezzo), e i suoi numeri sono gli STESSI di
`MAPPA_P2P_PROIEZIONE` in miniapp.html — una prova li tiene uguali:
x = (lon - LON0) * K * COS, y = (LAT1 - lat) * K.

Si rilancia solo se cambia il CSV: `python genera_mappa_italia.py`."""
import csv
import math

LON0, LAT1, K = 6.5, 47.2, 100.0
COS = round(math.cos(math.radians(42)), 4)        # 0.7431
LARGO, ALTO = 920, 1180                           # il viewBox
PASSO = 8                                         # la griglia, in unita'


def proietta(lat: float, lon: float) -> tuple[float, float]:
    return (lon - LON0) * K * COS, (LAT1 - lat) * K


def main():
    caselle = set()
    with open("dati/comuni.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            x, y = proietta(float(r["lat"]), float(r["lon"]))
            caselle.add((round(x / PASSO), round(y / PASSO)))
    tratti = "".join(f"M{cx * PASSO} {cy * PASSO}h0"
                     for cx, cy in sorted(caselle, key=lambda c: (c[1], c[0])))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="0 0 {LARGO} {ALTO}" width="{LARGO}" height="{ALTO}">'
           '<path fill="none" stroke="#8a8f98" stroke-width="6" '
           f'stroke-linecap="round" d="{tratti}"/></svg>\n')
    with open("assets/italia-punti.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"🗺️ {len(caselle)} puntini, {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
