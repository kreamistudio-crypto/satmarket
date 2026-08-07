# -*- coding: utf-8 -*-
"""COME SI VEDE UN LINK DI BARATTOLO, quando qualcuno lo incolla.

Interroga un Barattolo — quello locale o quello vero — con gli
User-Agent dei crawler di Telegram, WhatsApp, Facebook, Slack e dei
client Nostr, legge SOLO i primi byte come fanno loro, e ricostruisce
la card che verrebbe fuori. Poi va a prendere l'og:image e la misura
contro i limiti di ognuno.

Legge e basta: nessuna scrittura, da nessuna parte.

USO
    python anteprime.py http://127.0.0.1:8099 /annuncio/832 /sicurezza
    python anteprime.py https://barattolo.store /negozio/rosina

ATTENZIONE, ed e' il motivo per cui questo script esiste: Telegram e
WhatsApp CACHANO le anteprime a lungo e dal nostro lato non si bustano.
Quindi in produzione si prova con URL USA-E-GETTA — un annuncio di
prova, da rimuovere subito dopo — e mai con quello vero di qualcuno:
una card sbagliata resta in giro per giorni, e viaggia ripubblicata da
chiunque inoltri il messaggio.
"""
import io
import re
import sys
import urllib.request

# Gli UA veri, piu' quanto scaricano prima di decidere. Telegram e
# WhatsApp si fermano presto: e' la ragione per cui i meta vanno in
# cima e non in coda a 900 KB di pagina.
CRAWLER = [
    ("Telegram", "TelegramBot (like TwitterBot)", 64 * 1024),
    ("WhatsApp", "WhatsApp/2.23.20.0 A", 32 * 1024),
    ("Facebook", "facebookexternalhit/1.1", 64 * 1024),
    ("Slack", "Slackbot-LinkExpanding 1.0", 64 * 1024),
    ("Nostr", "Mozilla/5.0 (compatible; opengraph.io)", 64 * 1024),
]

# (nome, lato minimo, byte massimi): sotto il lato la card grande non
# viene disegnata, sopra i byte l'immagine viene scartata del tutto
LIMITI_IMG = [("Telegram", 200, 5_000_000),
              ("WhatsApp", 300, 600_000),
              ("Facebook", 200, 8_000_000)]

DOMINIO = "https://barattolo.store"
META = re.compile(
    rb'<meta\s+(?:property|name)="([^"]+)"\s+content="([^"]*)"\s*/?>', re.I)


def prendi(url, ua, quanti):
    """I primi `quanti` byte, con l'UA di quel crawler."""
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(quanti)


def leggi_meta(pezzo):
    import html as _h
    return {k.decode(): _h.unescape(v.decode("utf-8", "replace"))
            for k, v in META.findall(pezzo)}


def misura_immagine(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl"})
        with urllib.request.urlopen(req, timeout=15) as r:
            dati = r.read()
            tipo = r.headers.get("Content-Type", "?")
    except Exception as e:
        return None, f"NON RISPONDE ({e})"
    try:
        from PIL import Image
        larg, alt = Image.open(io.BytesIO(dati)).size
    except Exception:
        larg = alt = 0            # senza Pillow si misurano i soli byte
    return (len(dati), tipo, larg, alt), None


def card(base, percorso):
    print("\n" + "=" * 66)
    print(f"  {base}{percorso}")
    print("=" * 66)
    visti = {}
    for nome, ua, quanti in CRAWLER:
        try:
            pezzo = prendi(base + percorso, ua, quanti)
        except Exception as e:
            print(f"  {nome:9s} ✗ {e}")
            continue
        m = leggi_meta(pezzo)
        visti[nome] = m
        segno = "✓" if m.get("og:title") and m.get("og:image") else "✗"
        print(f"  {nome:9s} {segno} letti {len(pezzo) // 1024:3d} KB — "
              f"{len(m)} meta")
    if not visti:
        return
    m = list(visti.values())[0]
    diversi = [n for n, x in visti.items() if x != m]
    print(f"\n  Tutti vedono la stessa cosa: "
          f"{'sì' if not diversi else 'NO → ' + str(diversi)}")

    print("\n  ┌─ come si vede la card ─────────────────────────────────")
    print(f"  │ {m.get('og:site_name', '?')}")
    print(f"  │ {m.get('og:title', '(VUOTO)')}")
    desc = m.get("og:description", "(vuota)")
    for i in range(0, min(len(desc), 168), 56):
        print(f"  │ {desc[i:i + 56]}")
    print(f"  │ [img] {m.get('og:image', '(NESSUNA)')}")
    print("  └────────────────────────────────────────────────────────")

    img = m.get("og:image", "")
    if not img:
        print("  ✗ nessuna og:image: card senza immagine")
        return
    # l'og:image porta sempre il dominio vero (i crawler la scaricano
    # da li'): provandola in locale la si rimappa sul server di prova
    if img.startswith(DOMINIO) and not base.startswith(DOMINIO):
        img = base + img[len(DOMINIO):]
        print(f"  (og:image dice {DOMINIO}; qui la provo su {base})")
    dati, errore = misura_immagine(img)
    if errore:
        print(f"  ✗ og:image {errore} — parecchi crawler, non trovandola, "
              f"non disegnano la card affatto")
        return
    peso, tipo, larg, alt = dati
    misura = f"{larg}×{alt} " if larg else ""
    print(f"\n  og:image: {misura}{tipo} {peso // 1024} KB")
    for nome, lato, tetto in LIMITI_IMG:
        perche = []
        if larg and min(larg, alt) < lato:
            perche.append(f"lato {min(larg, alt)} < {lato}")
        if peso > tetto:
            perche.append(f"{peso // 1024} KB > {tetto // 1024} KB")
        print(f"    {'✗' if perche else '✓'} {nome:9s} "
              f"{'NO: ' + ', '.join(perche) if perche else 'card grande'}")

    # dove finiscono i meta dentro la pagina: se scivolassero in fondo
    # a 900 KB, i crawler che si fermano presto non li vedrebbero
    testa = prendi(base + percorso, "curl", 8192)
    ultimo = max((testa.rfind(b'content="' + v.encode("utf-8", "replace"))
                  for v in m.values() if v), default=-1)
    dove = ("in cima, li leggono tutti" if 0 < ultimo < 8192
            else "TROPPO IN BASSO: i crawler si fermano prima")
    print(f"\n  L'ultimo meta sta al byte {ultimo} ({dove})")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    base = sys.argv[1].rstrip("/")
    for percorso in sys.argv[2:]:
        card(base, percorso)
    if base.startswith(DOMINIO):
        print("\n  ⚠️  Sei sul dominio VERO: se stavi collaudando, che "
              "fossero URL usa-e-getta.\n     Telegram e WhatsApp "
              "tengono in cache quello che hanno appena visto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
