"""LA BASE DI CONOSCENZA DI TAPPO, A PEZZI (13 nov 2026, cantiere
tappo-economico, Andrea: «ad ogni commit si devono salvare le info in
file .md, una sorta di RAG»).

Tappo (il bot di n8n) mandava a Claude, a OGNI messaggio, tutto quello
che sa: il libro, il testo di tutte le schermate della Mini App, le
novita'. Circa 50.000 token a domanda, quasi sempre senza cache (con
poche domande al giorno la cache di cinque minuti scade fra una e
l'altra). Qui lo stesso sapere si spezza in PEZZI piccoli, ognuno col
suo titolo, in UN file markdown, `assistente/conoscenza.md`: n8n lo
legge da main, sceglie i pezzi che c'entrano con la domanda e manda
solo quelli. Le fonti sono le stesse di prima, nessuna nuova:
  - il libro `assistente/sapere.md`, a sezioni (`# ...`);
  - le schermate di `miniapp.html`, col testo che si legge sullo
    schermo (la stessa pulizia che faceva n8n, «Estrai le pagine»);
  - le voci di `NOVITA.md`.
Il sito barattolo.online sta in un altro repo: lo legge n8n dal sito
pubblico (vedi Architettura, «TAPPO, IL BOT CHE RISPONDE NEL CANALE»).

SI RIFA' A OGNI COMMIT: `python assistente/conoscenza.py` riscrive il
file, e `prove_conoscenza_tappo` in prove.py e' rossa se il file non e'
quello che uscirebbe adesso dalle fonti. Un git hook non viaggia con le
copie del repo (e le sessioni sono tante); una prova si'.

LA FORMA, che n8n legge a macchina (non cambiarla senza il nodo
«Prepara la domanda del gruppo»): ogni pezzo comincia con una riga
    <!-- pezzo libro-003 | libro | sempre -->
(id, fonte, e «sempre» se va mandato a ogni domanda), poi `## titolo`,
poi il testo. Nient'altro fra un pezzo e l'altro.
"""

import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
FILE = os.path.join(QUI, "conoscenza.md")
MARCA_NOVITA = "<!-- LE VOCI COMINCIANO QUI SOTTO -->"
PEZZO_MAX = 3000          # caratteri: piccoli abbastanza da sceglierli,
                          # grandi abbastanza da non spezzare un discorso
# le sezioni del libro che vanno a ogni domanda: chi e' Barattolo, e le
# regole contro le truffe (Tappo deve saperle anche quando la domanda
# non le nomina)
LIBRO_SEMPRE = ("Cos'è Barattolo", "Sicurezza e truffe",
                "Parlare con una persona")
# i nomi delle schermate per chi legge: gli stessi di n8n
NOMI_SCHERMATE = {
    "p2pinfo": "Lo scambio P2P (info)", "sicurezza": "Il pagamento protetto",
    "privacy": "I tuoi dati", "vendi": "Vendi (pubblicare un annuncio)",
    "profilo": "Profilo", "affari": "Ordini", "p2p": "P2P, libro ordini",
    "p2pmiei": "I miei scambi P2P",
    "onchain": "On-chain e finestre della Mini App"}

INTESTAZIONE = """# La base di conoscenza di Tappo

<!-- FILE GENERATO da assistente/conoscenza.py: non si tocca a mano.
Si rifà con `python assistente/conoscenza.py` dopo ogni ritocco al
libro (assistente/sapere.md), alla Mini App (miniapp.html) o a
NOVITA.md; prove_conoscenza_tappo è rossa finché non è aggiornato. -->
"""


def _leggi(nome: str) -> str:
    with open(os.path.join(RADICE, nome), encoding="utf-8") as f:
        return f.read()


def _a_misura(testo: str, massimo: int = PEZZO_MAX) -> list:
    """Un testo lungo in parti di al piu' `massimo` caratteri, tagliando
    fra un paragrafo (o una riga) e l'altro; una riga sola piu' lunga
    resta intera piuttosto che spezzata a meta' frase."""
    parti, ora = [], ""
    for riga in testo.split("\n"):
        if ora and len(ora) + 1 + len(riga) > massimo:
            parti.append(ora.strip())
            ora = ""
        ora = (ora + "\n" + riga) if ora else riga
    if ora.strip():
        parti.append(ora.strip())
    return [p for p in parti if p]


def pezzi_libro(testo: str) -> list:
    pezzi = []
    sezioni = re.split(r"\n(?=# )", "\n" + testo)
    for s in sezioni:
        s = s.strip()
        if not s.startswith("# "):
            continue          # la riga d'apertura del libro, prima della prima sezione
        titolo, _, corpo = s.partition("\n")
        titolo = titolo[2:].strip()
        sempre = titolo in LIBRO_SEMPRE
        parti = _a_misura(corpo.strip())
        for n, p in enumerate(parti):
            t = titolo if len(parti) == 1 else f"{titolo} ({n + 1}/{len(parti)})"
            pezzi.append(("libro", f"Libro · {t}", p, sempre))
    return pezzi


def _pulisci_html(t: str) -> str:
    """La stessa pulizia del nodo n8n «Estrai le pagine»: il testo che
    si legge sullo schermo, bottoni compresi; i commenti no."""
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", "", t, flags=re.S)
    t = re.sub(r"<(h2|h3)[^>]*>", "\n## ", t)
    t = re.sub(r"<(p|li|br|div|tr|button|label)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                 ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(a, b)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


def pezzi_schermate(html: str) -> list:
    pezzi = []
    viste = [(m.group(1), m.start()) for m in
             re.finditer(r'<div class="view" id="view-([a-z0-9]+)">', html)]
    for k, (vid, i) in enumerate(viste):
        fine = viste[k + 1][1] if k + 1 < len(viste) else html.find("<script", i)
        if fine < 0:
            fine = i + 300000
        testo = _pulisci_html(html[i:fine])
        if len(testo) < 150:
            continue
        nome = NOMI_SCHERMATE.get(vid, vid)
        # dentro la schermata, a sottotitoli (## ), poi a misura
        blocchi = re.split(r"\n(?=## )", "\n" + testo)
        parti = []
        for b in blocchi:
            b = b.strip()
            if b:
                parti += _a_misura(b)
        # i blocchi piccoli si uniscono al vicino: un pezzo da tre parole
        # non dice niente da solo
        unite = []
        for p in parti:
            if unite and len(unite[-1]) + 1 + len(p) <= PEZZO_MAX:
                unite[-1] += "\n" + p
            else:
                unite.append(p)
        sotto = ""
        for n, p in enumerate(unite):
            # il titolo e' l'ultimo sottotitolo visto: un pezzo che
            # continua un discorso porta il nome del discorso
            primo = p.split("\n", 1)[0]
            if primo.startswith("## "):
                sotto = primo[3:].strip()[:60]
            t = f"Schermata «{nome}»" + (f" · {sotto}" if sotto else "")
            if len(unite) > 1:
                t += f" ({n + 1}/{len(unite)})"
            pezzi.append(("schermata", t, p, False))
    return pezzi


def pezzi_novita(testo: str) -> list:
    pezzi = []
    if MARCA_NOVITA not in testo:
        return pezzi
    corpo = testo.split(MARCA_NOVITA, 1)[1]
    for v in re.split(r"\n(?=## )", corpo):
        v = v.strip()
        if not v.startswith("## "):
            continue
        titolo, _, resto = v.partition("\n")
        pezzi.append(("novita", f"Novità · {titolo[3:].strip()}",
                      resto.strip(), False))
    return pezzi


def genera() -> str:
    """Il testo intero di conoscenza.md, dalle fonti di adesso. Pura
    (legge e basta): la prova la confronta col file."""
    tutti = (pezzi_libro(_leggi(os.path.join("assistente", "sapere.md")))
             + pezzi_schermate(_leggi("miniapp.html"))
             + pezzi_novita(_leggi("NOVITA.md")))
    conti = {}
    righe = [INTESTAZIONE]
    for fonte, titolo, testo, sempre in tutti:
        conti[fonte] = conti.get(fonte, 0) + 1
        pid = f"{fonte}-{conti[fonte]:03d}"
        # un «<!-- pezzo» dentro un testo spezzerebbe la lettura di n8n
        testo = testo.replace("<!--", "<!-")
        righe.append(f"<!-- pezzo {pid} | {fonte}"
                     + (" | sempre" if sempre else "") + " -->\n"
                     f"## {titolo}\n\n{testo}\n")
    return "\n".join(righe)


def main() -> int:
    nuovo = genera()
    try:
        with open(FILE, encoding="utf-8") as f:
            vecchio = f.read()
    except OSError:
        vecchio = None
    if "--controlla" in sys.argv:
        if vecchio != nuovo:
            print("❌ assistente/conoscenza.md non è aggiornato: "
                  "python assistente/conoscenza.py")
            return 1
        print("✅ assistente/conoscenza.md aggiornato")
        return 0
    if vecchio == nuovo:
        print("✅ assistente/conoscenza.md era già aggiornato")
        return 0
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(nuovo)
    print(f"✅ assistente/conoscenza.md riscritto "
          f"({nuovo.count('<!-- pezzo ')} pezzi, {len(nuovo)} caratteri)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
