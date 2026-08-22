# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL PROMPT DI RICATEGORIZZA (ago 2026).

Il prompt di ricategorizza.py ha gia' sbagliato in produzione: 19
proposte, e UNDICI erano annunci da tirare fuori da «Bitcoin» —
sacche, poster cypherpunk, magliette. Non era il modello a
disobbedire: era il prompt che non aveva imparato una decisione gia'
presa. L'albero delle sottocategorie, sotto «Bitcoin», ha
«poster-stampe» e «merch» con dentro alla lettera `maglietta`,
`sacca`, `borsa`: quel reparto e' TEMATICO da quando e' stato
disegnato sui 46 annunci veri, e il prompt insegnava ancora «hardware
e nodi» — quattro esempi tutti apparecchi, la lezione della coppia
bici/cuffie: gli esempi insegnano il confine piu' della regola.

Le prove di prove.py difendono la FORMA del prompt; quello che non
possono fare e' dire se il MODELLO risponde giusto — la chiave sta
fuori dalla CI apposta. Questo script chiude il buco a mano, come
collaudo_impersonazione.py fa per la moderazione, e va rilanciato a
OGNI ritocco del prompt.

A differenza del fratello, qui il pezzo VERO si puo' IMPORTARE:
ricategorizza.py chiede il config dentro main() apposta, quindi
catalogo() e chiedi() si usano cosi' come sono — niente estrazione
dal testo (quel trucco serve solo per server.py), niente copie che
divergono.

LA REGOLA DEL CONFRONTO, una sola per tutti i casi: chiedi() ritorna
SOLO gli spostamenti, quindi

    dove_finisce = fuori.get(id, categoria_ora)   # assente = fermo
    ok = dove_finisce == atteso

e nella tabella l'atteso e' sempre il reparto dove l'annuncio deve
FINIRE — «resta dov'e'» non ha bisogno di un valore speciale.

I DUE SBAGLI NON PESANO UGUALE, ed e' la stessa asimmetria che la
docstring di chiedi() dichiara: un annuncio lasciato dov'e' non fa
danno, uno SPOSTATO MALE si' — tira un annuncio fuori da casa sua, e
se ne accorge solo il venditore. Il conto li tiene separati, come il
fratello separa i falsi positivi.

L'ATTESO SEGUE IL PROMPT, MAI IL MODELLO (la regola del caso
«Assistenza Barattolo»): un atteso che cambia due volte non e' piu'
un atteso. Se un caso oscilla si dichiara CASO INSTABILE qui sotto e
non lo si rincorre una terza volta.

USO:  python collaudo_ricategorizza.py           # il giro vero
      python collaudo_ricategorizza.py --secco   # stampa prompt e corpo
                                                 # SENZA chiamare niente
      python collaudo_ricategorizza.py --crudo   # anche la risposta grezza
      (chiave da $ANTHROPIC_API_KEY, oppure da config.py)

Codici d'uscita: 0 tutto come atteso, 1 casi sbagliati, 2 non ho
potuto girare (chiave assente) — un giro saltato non deve potersi
scambiare per un giro riuscito.
"""

import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

from ricategorizza import catalogo, chiedi  # noqa: E402

# (titolo, descrizione, ORA STA IN, dove deve FINIRE, perche')
CASI = [
    # --- la cura: «Bitcoin» e' un reparto TEMATICO ------------------
    ("Sacca in cotone col logo Bitcoin",
     "Sacca zaino con cordoncino, stampa arancione, mai usata.",
     "Bitcoin", "Bitcoin",
     "il caso vero di produzione: le sacche erano fra gli undici "
     "spostamenti sbagliati verso «Altro»"),
    ("Poster cypherpunk, stampa numerata",
     "Stampa 50x70 su carta opaca, edizione numerata a mano.",
     "Bitcoin", "Bitcoin",
     "«poster-stampe» e' una sottovoce di Bitcoin: il tema decide"),
    ("Maglietta nera col simbolo ₿, taglia L",
     "Cotone 100%, stampa serigrafica, indossata una volta.",
     "Bitcoin", "Bitcoin",
     "la meta' tematica della coppia delle magliette"),
    ("Maglietta nera taglia L, cotone pesante",
     "Tinta unita, senza stampe, come nuova.",
     "Bitcoin", "Abbigliamento",
     "AFFILATO APPOSTA: sta in «Bitcoin» e deve USCIRNE. Senza questo "
     "caso «reparto tematico» diventerebbe «tutto quello che qualcuno "
     "ci ha messo»"),
    ("NerdMiner V2 montato e testato",
     "Miner lottery su ESP32, schermo funzionante, con cavo USB.",
     "Elettronica", "Bitcoin",
     "quello che il prompt VECCHIO indovinava gia': deve continuare"),

    # --- il secondo giro (ago 2026, dal campo): la regola tematica
    #     assorbiva TROPPO — tre «Sat's Oil» proposti da Alimenti a
    #     Bitcoin per il «Sat» nel nome, e il «Manifesto Hacker»
    #     spinto verso Arte. Da qui la contro-regola: il tema
    #     dev'essere L'OGGETTO, non il nome del prodotto — la stessa
    #     lezione gia' pagata dal prompt della moderazione («sat» e'
    #     la moneta, una somiglianza di nome non e' mai un motivo).
    ("Sat's Oil 🫒 GENESIS EDITION",
     "Olio extravergine di oliva, raccolta 2025, bottiglia da 500ml.",
     "Alimenti e bevande", "Alimenti e bevande",
     "il caso vero del secondo giro: e' olio, non merce a tema — "
     "«sat» nel nome non basta a spostare un prodotto d'uso"),
    ("Birra artigianale 21 Million, IPA da 33cl",
     "Luppolata, piccolo lotto, etichetta a tema bitcoin.",
     "Alimenti e bevande", "Alimenti e bevande",
     "la gemella con altre parole: se cade solo questa, la cura ha "
     "imparato il nome invece della regola"),
    ("Manifesto Hacker, stampa 70x100",
     "The Conscience of a Hacker in serigrafia, edizione limitata.",
     "Bitcoin", "Bitcoin",
     "l'altro caso del secondo giro: il poster a tema resta "
     "«Bitcoin», non migra verso «Arte e artigianato» solo perche' "
     "e' una stampa"),

    # --- le regressioni: il file guarda tutto il prompt, non solo
    #     la cura -----------------------------------------------------
    ("Portatile Dell i5",
     "Dell Latitude, i5 di ottava generazione, 8GB di RAM, SSD 256GB.",
     "Elettronica", "Informatica",
     "regressione: la regola computer→Informatica non deve rompersi"),
    ("Jade hardware wallet sigillata",
     "Blockstream Jade, mai aperta, scatola sigillata.",
     "Elettronica", "Bitcoin",
     "regressione: l'hardware bitcoin resta «Bitcoin»"),
    ("Alimentatore da banco 30V 5A",
     "Alimentatore da laboratorio regolabile, display digitale.",
     "Bitcoin", "Elettronica",
     "sorveglia la clausola che RESTA: l'elettronica generica non sta "
     "in «Bitcoin», nemmeno se ce l'ha messa qualcuno"),
    ("Vendo, scrivimi in privato",
     "",
     "Altro", "Altro",
     "il NON SO deve sopravvivere: niente da capire, niente da "
     "spostare"),
]


class _Spia:
    """Il finto client di --secco: registra quel che chiedi()
    spedirebbe e risponde a vuoto. Cosi' si stampano il prompt e il
    corpo VERI — quelli composti da chiedi(), non una copia — senza
    chiamare nessun modello. E' l'unica verifica possibile su una
    macchina dove la chiave e' un segnaposto."""

    def __init__(self):
        self.spediti = []
        self.messages = self          # chiedi() fa ai.messages.create

    def create(self, **kw):
        from types import SimpleNamespace as NS
        self.spediti.append(kw)
        return NS(content=[], usage=NS(input_tokens=0, output_tokens=0))


def main() -> int:
    cat = catalogo()
    voci = [(n, t, d, ora)
            for n, (t, d, ora, _, _) in enumerate(CASI, 1)]

    if "--secco" in sys.argv:
        spia = _Spia()
        chiedi(spia, cat, voci)
        kw = spia.spediti[0]
        print("=== SYSTEM (il prompt, gia' formattato col catalogo) ===")
        print(kw["system"])
        print("\n=== CORPO (gli annunci, come li vede il modello) ===")
        print(kw["messages"][0]["content"])
        print(f"\n(modello: {kw['model']} — non ho chiamato niente)")
        return 0

    chiave = os.environ.get("ANTHROPIC_API_KEY", "")
    if not chiave:
        try:
            import config
            chiave = getattr(config, "ANTHROPIC_API_KEY", "")
        except Exception:
            pass
    if not chiave or chiave.startswith("INCOLLA"):
        print("Serve la chiave Anthropic: nel config.py di questa "
              "macchina non c'e'.\nGirami sul VPS, o esporta "
              "ANTHROPIC_API_KEY. (--secco stampa cosa spedirei)")
        return 2

    import anthropic
    ai = anthropic.Anthropic(api_key=chiave)

    # La spia di --crudo: chiedi() non restituisce la risposta grezza
    # — mette «NON SO», riga storta e categoria inventata nello STESSO
    # secchio — e per distinguere serve il testo di passaggio. Cinque
    # righe attorno a messages.create: nessuna seconda chiamata e
    # nessuna copia di chiedi().
    grezze = []
    if "--crudo" in sys.argv:
        vero = ai.messages.create

        def crea(**kw):
            r = vero(**kw)
            grezze.append("".join(b.text for b in r.content
                                  if b.type == "text"))
            return r
        ai.messages.create = crea

    print(f"casi: {len(CASI)} — un lotto solo\n")
    fuori, (tok_in, tok_out) = chiedi(ai, cat, voci)
    if not fuori and (tok_in, tok_out) == (0, 0):
        # chiedi() e' fail-open per lotto: se la chiamata esplode
        # stampa il perche' e torna a mani vuote. Qui un lotto saltato
        # non e' un giro riuscito.
        print("Il lotto e' esploso (vedi sopra): niente da contare.")
        return 2

    sbagliati, spostati_male = 0, []
    for n, (titolo, _, ora, atteso, perche) in enumerate(CASI, 1):
        dove = fuori.get(n, ora)          # assente = non si e' mosso
        ok = dove == atteso
        sbagliati += not ok
        # I due sbagli non pesano uguale (la docstring di chiedi):
        # lasciato dov'e' = nessun danno; SPOSTATO MALE = un annuncio
        # tirato fuori da casa sua, e se ne accorge solo il venditore.
        male = not ok and dove != ora
        if male:
            spostati_male.append(titolo)
        segno = "‼" if male else ("✗" if not ok else "✓")
        print(f"  {segno} [{ora} → atteso {atteso} | detto {dove}] "
              f"{titolo[:48]}")
        print(f"      {perche}")

    if grezze:
        print("\n=== RISPOSTA GREZZA ===")
        for g in grezze:
            print(g)

    print(f"\n  {len(CASI) - sbagliati}/{len(CASI)} come atteso")
    if spostati_male:
        print(f"  ‼ {len(spostati_male)} SPOSTATO/I MALE — e' il caso "
              f"GRAVE: un annuncio tirato fuori\n    da casa sua, e se "
              f"ne accorge solo il venditore. "
              + " · ".join(f"«{t[:40]}»" for t in spostati_male))
    if sbagliati - len(spostati_male):
        print(f"  {sbagliati - len(spostati_male)} non spostato/i: meno "
              f"grave (l'annuncio resta dov'era), ma la\n    regola non "
              f"ha insegnato abbastanza.")
    if sbagliati:
        print("  Si corregge il prompt A MANO: la macchina raccoglie, "
              "l'umano decide.")

    # Haiku: 1 $ per milione di token in ingresso, 5 in uscita — il
    # conto di ricategorizza.py. Un lotto solo: ~0,005 $.
    costo = tok_in / 1e6 * 1 + tok_out / 1e6 * 5
    print(f"\n💸 {tok_in} token in, {tok_out} out — circa {costo:.3f} $")
    return 1 if sbagliati else 0


if __name__ == "__main__":
    sys.exit(main())
