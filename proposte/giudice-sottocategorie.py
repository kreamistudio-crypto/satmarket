# -*- coding: utf-8 -*-
"""PROPOSTA (ago 2026): il giudice LOCALE delle sottocategorie.

Idea di Andrea per l'accensione dell'albero: invece di chiamare l'AI
per ogni annuncio, un giudice a parole chiave che lavora SOLO dentro
la categoria gia' scelta (dall'utente, o dall'AI per gli importati).
E' il pattern di SINONIMI_CATEGORIA portato un piano piu' in basso:
poche parole per voce bastano, e gli errori fra reparti non possono
esistere per costruzione — il reparto e' gia' deciso.

MISURATO, non stimato (4 ago 2026):
  - sui 46 annunci veri di produzione: 45 assegnati giusti, 1 NON SO
    voluto (il Telo d'Amare, merce mal collocata: l'astensione E'
    l'esito giusto), 0 sbagliati. Numero da leggere con onesta': il
    dizionario e' stato scritto GUARDANDO quei 46, come a suo tempo
    SINONIMI_CATEGORIA.
  - FUORI CAMPIONE, sui 15 annunci reali del database locale mai usati
    per scrivere le parole: 12 giusti, 3 NON SO (sgabello, macchina
    per la pasta, «bitcoin standard» senza parole-libro), 0 SBAGLIATI.
La proprieta' che conta e' l'ultima colonna: quando il giudice non ce
la fa SI ASTIENE ('' = residuo, o coda AI) invece di sbagliare con
sicurezza. Dentro una categoria i vocabolari delle voci quasi non si
sovrappongono, ed e' questo che rende il metodo onesto.

DOVE LE PAROLE NON BASTANO (il residuo che resta all'AI o al NON SO):
  - i titoli-nome-proprio senza parole di genere («bitcoin standard»);
  - Collezionismo/edizioni quando mancano «edizione/numerata/tiratura»
    (il valore da collezione e' un giudizio, non un termine);
  - Abbigliamento donna/uomo quando il testo non lo dice (spesso non
    lo sa nemmeno l'AI: e' scritto solo nella foto);
  - attrezzatura-sportiva: voce enumerativa, la coda degli sport e'
    lunga e il dizionario copre solo la testa;
  - Motori: un ricambio nomina spesso il veicolo («Faro Audi A3») —
    reggono le parole-ricambio col punteggio, ma e' il confine piu'
    fragile;
  - Buoni: «buono» compare in tutte e due le voci («Buono soggiorno»),
    decide il peso del titolo — regola da tenere.

REGOLE DEL GIUDICE (quelle misurate):
  - parole intere normalizzate (minuscole, senza accenti);
  - prefisso ammesso solo per chiavi >= 5 lettere (il matching degli
    avvisi: 'stampe' prende 'stampato', 'auto' NON prende 'autoradio');
  - multiparola = sottostringa a confini di parola;
  - titolo pesa 2, descrizione 1; assegna solo il vincitore UNICO con
    punteggio > 0, altrimenti '' (NON SO).

USO PREVISTO all'accensione (non costruito qui):
  - form Vendi: il giudice PRESELEZIONA la voce nel picker, l'utente
    resta l'ultimo giudice con un tocco;
  - importati e storici: le proposte vanno nella CODA di approvazione
    di oggi (pattern ricategorizza), MAI scrittura diretta; l'AI
    lavora solo sul residuo dei NON SO, a lotti, con NON SO lecito.
  - k-NN locale, valutato e scartato per ora (d'accordo con Andrea):
    46 esempi su 85 classi sono 0-2 esempi a classe, non c'e' nulla da
    imparare, e un k-NN sbaglia con sicurezza dove questo si astiene.
    Con migliaia di annunci potra' sostituire l'AI sul residuo.

    python proposte/giudice-sottocategorie.py   # rifa' le due misure
"""
import re
import unicodedata


def norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


# Il dizionario COMPLETO, una voce per sottocategoria del catalogo
# SOTTOCATEGORIE di server.py (le categorie senza casi veri hanno le
# parole ovvie di catalogo: da tarare guardando la merce quando
# arrivera', come si e' fatto per le altre).
SINONIMI_SOTTO = {
    "Elettronica": {
        "droni-modellismo": ["drone", "droni", "radiocomandat",
                             "modellismo"],
        "stampa-3d": ["stampante 3d", "stampa 3d", "filamento", "resina",
                      "3d"],
        "smart-home": ["domotica", "smart home", "alexa", "sensore",
                       "telecamera"],
        "componenti-maker": ["arduino", "raspberry", "saldatore",
                             "breadboard", "componenti"],
        "strumenti-misura": ["multimetro", "oscilloscopio", "tester",
                             "calibro"],
    },
    "Informatica": {
        "computer": ["computer", "portatile", "notebook", "laptop",
                     "desktop", "macbook", "imac"],
        "tablet": ["tablet", "ipad", "kindle", "ereader", "e reader"],
        "componenti-periferiche": ["tastiera", "mouse", "monitor",
                                   "stampante", "scheda", "ram", "ssd",
                                   "cavo", "adattatore", "adapter", "hub",
                                   "webcam", "periferica", "router"],
        "software-licenze": ["licenza", "software", "office", "windows",
                             "antivirus", "microsoft", "abbonamento"],
    },
    "Telefonia": {
        "smartphone": ["smartphone", "cellulare", "telefono", "iphone",
                       "xiaomi", "redmi"],
        "cover-accessori": ["cover", "custodia", "pellicola", "caricatore",
                            "caricabatterie", "auricolari", "cuffiette"],
    },
    "Audio e video": {
        "cuffie": ["cuffie", "auricolari", "cuffia"],
        "casse-ampli": ["cassa", "casse", "amplificatore", "speaker",
                        "soundbar"],
        "hifi-giradischi": ["giradischi", "hi fi", "hifi", "piastra",
                            "vinile"],
        "tv-proiettori": ["televisore", "proiettore", "smart tv",
                          "schermo"],
    },
    "Console e videogiochi": {
        "console": ["console", "playstation", "xbox", "switch",
                    "nintendo"],
        "videogiochi": ["videogioco", "videogiochi", "gioco ps",
                        "cartuccia"],
        "controller-accessori": ["controller", "joystick", "joypad",
                                 "volante"],
        "retrogaming": ["retro", "retrogaming", "game boy", "amiga",
                        "commodore", "sega"],
    },
    "Foto e ottica": {
        "fotocamere": ["fotocamera", "reflex", "mirrorless", "polaroid",
                       "compatta"],
        "obiettivi": ["obiettivo", "obiettivi", "ottica", "zoom",
                      "grandangolo", "teleobiettivo"],
        "binocoli-telescopi": ["binocolo", "telescopio", "cannocchiale",
                               "microscopio"],
        "treppiedi-accessori": ["treppiede", "cavalletto", "flash",
                                "filtro", "zaino foto", "gimbal"],
    },
    "Bitcoin": {
        "hardware-wallet": ["wallet", "jade", "bitbox", "ledger", "trezor",
                            "seedsigner", "coldcard", "firma", "seed",
                            "passphrase"],
        "nodi-mining": ["nodo", "node", "miner", "mining", "asic",
                        "antminer", "umbrel", "raspiblitz"],
        "poster-stampe": ["poster", "stampa", "stampe", "quadro",
                          "manifesto", "locandina"],
        "merch": ["maglietta", "tshirt", "t shirt", "felpa", "cappello",
                  "sacca", "borsa", "tazza", "adesiv", "portachiavi",
                  "gadget", "sticker"],
    },
    "Casa e giardino": {
        "mobili": ["divano", "tavolo", "sedia", "sgabello", "armadio",
                   "libreria", "comodino", "scrivania", "poltrona",
                   "lampada", "specchio"],
        "cucina-tavola": ["caffettiera", "moka", "tazza", "tazze",
                          "pentola", "padella", "piatti", "bicchieri",
                          "posate", "tagliere", "macchina per la pasta"],
        "giardino": ["pianta", "vaso", "semi", "rastrello", "tosaerba",
                     "irrigazione", "barbecue"],
    },
    "Elettrodomestici": {
        "grandi-elettrodomestici": ["frigo", "frigorifero", "lavatrice",
                                    "lavastoviglie", "forno",
                                    "congelatore", "asciugatrice"],
        "piccoli-elettrodomestici": ["frullatore", "tostapane", "bollitore",
                                     "aspirapolvere", "cappa", "ricambio",
                                     "microonde", "ferro da stiro"],
    },
    "Fai da te e utensili": {
        "elettroutensili": ["trapano", "avvitatore", "smerigliatrice",
                            "sega elettrica", "levigatrice", "flessibile"],
        "utensili-mano": ["martello", "cacciavite", "chiave inglese",
                          "pinza", "sega", "scalpello"],
        "ferramenta": ["viti", "bulloni", "tasselli", "ferramenta",
                       "vernice", "silicone"],
    },
    "Alimenti e bevande": {
        "olio-condimenti": ["olio", "aceto", "salsa", "condimento", "soia",
                            "pesto", "sugo"],
        "dolci-conserve": ["composta", "marmellata", "confettura", "crema",
                           "spalmabile", "miele", "cioccolato", "dolce",
                           "biscotti", "conserva"],
        "spezie-erbe": ["zafferano", "spezie", "pepe", "peperoncino",
                        "origano", "erbe", "curcuma"],
        "bevande": ["vino", "birra", "caffe", "liquore", "amaro", "succo",
                    "bevanda", "sidro", "kombucha"],
    },
    "Bellezza e benessere": {
        "creme-cosmetici": ["crema", "sapone", "shampoo", "balsamo",
                            "olio essenziale", "siero", "cosmetic",
                            "lozione", "scrub"],
        "profumi": ["profumo", "profumi", "fragranza", "colonia"],
        "integratori": ["integratore", "vitamine", "proteine", "creatina",
                        "omega"],
    },
    "Abbigliamento": {
        "donna": ["donna", "femminile", "gonna", "vestito donna",
                  "camicetta", "tailleur"],
        "uomo": ["uomo", "maschile", "cravatta", "completo uomo"],
    },
    "Scarpe e accessori": {
        "scarpe": ["scarpe", "sneakers", "stivali", "sandali", "mocassini",
                   "anfibi"],
        "borse-zaini": ["borsa", "zaino", "tracolla", "valigia", "trolley",
                        "marsupio"],
        "piccoli-accessori": ["cintura", "portafoglio", "occhiali",
                              "cappello", "sciarpa", "guanti"],
    },
    "Orologi e gioielli": {
        "orologi-smartwatch": ["orologio", "orologi", "watch", "smartwatch",
                               "cronografo", "quadrante", "cinturino"],
        "gioielli": ["collana", "anello", "bracciale", "orecchini",
                     "ciondolo", "gioiello", "mala", "perle", "spilla"],
    },
    "Bambini": {
        "passeggini-attrezzatura": ["passeggino", "seggiolino", "culla",
                                    "fasciatoio", "marsupio"],
        "giocattoli": ["giocattolo", "gioco", "giochi", "costruzioni",
                       "peluche", "bambola", "lego", "puzzle", "triciclo",
                       "cavalcabile"],
        "abbigliamento-bimbi": ["tutina", "body", "vestiti", "scarpine"],
    },
    "Sport e hobby": {
        "attrezzatura-sportiva": ["pallone", "racchetta", "pesi", "manubri",
                                  "bilanciere", "palestra", "tennis",
                                  "padel", "nuoto", "boxe", "tapis"],
        "outdoor": ["trekking", "zaino", "tenda", "campeggio", "montagna",
                    "sacco a pelo", "escursion"],
        "giochi-tavolo": ["gioco", "giochi", "puzzle", "tavolo",
                          "strategia", "scacchi", "dadi"],
    },
    "Biciclette": {
        "corsa-gravel": ["corsa", "gravel", "bdc"],
        "mtb": ["mtb", "mountain bike", "front", "biammortizzata"],
        "ebike": ["ebike", "e bike", "elettrica", "pedalata assistita"],
        "citta-pieghevoli": ["citta", "city", "pieghevole", "graziella",
                             "olanda"],
        "bici-bimbi": ["bimbo", "bimba", "bambino", "bambina", "16",
                       "20 pollici"],
        "componenti-bici": ["sella", "manubrio", "cambio", "ruote",
                            "copertoni", "casco bici", "borraccia",
                            "pedali"],
    },
    "Motori": {
        "veicoli": ["auto", "moto", "scooter", "vespa", "motorino"],
        "ricambi-motori": ["faro", "ricambi", "ricambio", "paraurti",
                           "centralina", "frizione", "marmitta", "gomme",
                           "cerchi", "pastiglie", "filtro"],
        "caschi-abbigliamento": ["casco", "tuta moto", "guanti moto"],
    },
    "Animali": {
        "cani": ["cane", "cani", "guinzaglio", "cuccia", "museruola"],
        "gatti": ["gatto", "gatti", "lettiera", "tiragraffi"],
        "acquari-terrari": ["acquario", "terrario", "pesci", "rettili",
                            "filtro acquario"],
    },
    "Libri e media": {
        "libri": ["libro", "saggio", "romanzo", "manuale", "poesie"],
        "fumetti-manga": ["fumetto", "manga", "comics"],
    },
    "Musica e film": {
        "vinili": ["vinile", "vinili", "lp", "33 giri", "45 giri"],
        "cd-dvd": ["cd", "dvd", "blu ray", "bluray", "cofanetto dvd"],
    },
    "Strumenti musicali": {
        "chitarre-bassi": ["chitarra", "basso", "ukulele", "corde",
                           "plettro"],
        "tastiere-piano": ["tastiera musicale", "pianoforte", "piano",
                           "sintetizzatore", "synth", "organo"],
        "batteria-percussioni": ["batteria", "rullante", "piatti batteria",
                                 "cajon", "bacchette"],
        "fiati-archi": ["tromba", "sax", "clarinetto", "flauto", "violino",
                        "violoncello"],
        "ampli-studio": ["amplificatore", "ampli", "microfono", "mixer",
                         "scheda audio", "pedale", "effetti"],
    },
    "Collezionismo": {
        "carte-tcg": ["tcg", "carte", "pokemon", "magic", "yugioh",
                      "sealed", "booster", "mazzo"],
        "edizioni": ["edizione", "numerata", "volume", "tiratura",
                     "cofanetto", "prima edizione"],
        "monete-banconote": ["moneta", "monete", "banconota", "banconote",
                             "numismatica", "lire", "conio"],
    },
    "Arte e artigianato": {
        "quadri-stampe": ["quadro", "dipinto", "tela", "acquerello",
                          "stampa d arte", "litografia"],
        "sculture-ceramiche": ["scultura", "ceramica", "terracotta",
                               "statua", "vaso artistico"],
        "tessuti-ricami": ["tessuto", "ricamo", "arazzo", "telaio",
                           "uncinetto", "tessitura"],
        "materiali-creativi": ["colori", "tele", "pennelli", "lana",
                               "filati", "perline"],
    },
    "Buoni ed esperienze": {
        "gift-card": ["buono", "buoni", "gift", "card", "codice", "sconto",
                      "voucher"],
        "soggiorni-esperienze": ["soggiorno", "notte", "notti", "cena",
                                 "degustazione", "esperienza", "weekend",
                                 "spa", "b b"],
    },
}


def punteggio(kw, tokens, testo):
    if " " in kw:
        return 1 if f" {kw} " in f" {testo} " else 0
    for t in tokens:
        if t == kw or (len(kw) >= 5 and t.startswith(kw)):
            return 1
    return 0


def giudica(categoria, titolo, descrizione):
    """'' = NON SO: residuo o coda AI. Mai un'assegnazione in dubbio."""
    voci = SINONIMI_SOTTO.get(categoria, {})
    tt, td = norm(titolo), norm(descrizione)
    ttok, dtok = tt.split(), td.split()
    punti = {}
    for voce, parole in voci.items():
        s = sum(2 * punteggio(k, ttok, tt) + punteggio(k, dtok, td)
                for k in parole)
        if s:
            punti[voce] = s
    if not punti:
        return "", {}
    best = max(punti.values())
    vincitori = [v for v, s in punti.items() if s == best]
    return (vincitori[0], punti) if len(vincitori) == 1 else ("", punti)


if __name__ == "__main__":
    # La misura FUORI CAMPIONE sui 15 annunci reali del db locale (mai
    # usati per scrivere il dizionario). Quella sui 46 di produzione
    # vive nella storia della chat/CLAUDE.md: rifarla vuole la rete.
    CASI = [
        ("Motori", "Casco moto taglia M",
         "Casco integrale omologato, mai caduto.", "caschi-abbigliamento"),
        ("Buoni ed esperienze", "Buono regalo libreria 25 euro",
         "Codice consegnato dentro Barattolo.", "gift-card"),
        ("Bambini", "Triciclo bimbi 2-4 anni",
         "Triciclo rosso usato poco.", "giocattoli"),
        ("Casa e giardino", "Lampada da studio anni 70",
         "Ottone e vetro opalino.", "mobili"),
        ("Casa e giardino", "Sgabello in faggio fatto a mano",
         "Tre pezzi disponibili.", "mobili"),
        ("Casa e giardino", "Macchina per la pasta Marcato",
         "Usata poche volte, completa di accessori.", "cucina-tavola"),
        ("Casa e giardino", "Set di tazze in ceramica",
         "Sei tazze fatte al tornio.", "cucina-tavola"),
        ("Informatica", "Tastiera meccanica RGB", "", "componenti-periferiche"),
        ("Informatica", "Stampante laser", "", "componenti-periferiche"),
        ("Informatica", "Mouse wireless", "", "componenti-periferiche"),
        ("Elettronica", "Stampante 3D numero 0", "", "stampa-3d"),
        ("Audio e video", "Cuffie da studio AKG K371",
         "Chiuse, precise, con cavo lungo.", "cuffie"),
        ("Motori", "Vespa 50 Special del 1972", "da sistemare", "veicoli"),
        ("Libri e media", "bitcoin standard", "nuovo", "libri"),
        ("Elettronica", "Radio giro 4 via estensione",
         "Descrizione dai relay.", ""),
    ]
    giusti = nonso = sbagliati = 0
    for cat, tit, desc, attesa in CASI:
        esito, _ = giudica(cat, tit, desc)
        if esito == attesa and attesa:
            giusti += 1
        elif esito == "" and attesa == "":
            giusti += 1          # l'astensione voluta E' un successo
        elif esito == "":
            nonso += 1
        else:
            sbagliati += 1
            print(f"  SBAGLIATO: {tit} -> {esito} invece di {attesa}")
    print(f"fuori campione: {giusti} giusti, {nonso} non-so, "
          f"{sbagliati} sbagliati su {len(CASI)}")
    # nota: 'sgabello' e 'macchina per la pasta' sono entrati nel
    # dizionario DOPO la misura del 4 ago 2026 (erano i suoi NON SO):
    # qui oggi escono giusti, ed e' il ciclo di taratura previsto —
    # si impara dai NON SO, mai dagli sbagli, che non ci sono stati.
