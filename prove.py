# -*- coding: utf-8 -*-
"""
LE PROVE — la rete di sicurezza che gira a ogni commit.

Si collaudano i pezzi PURI, quelli che non hanno bisogno di config,
di database o di rete: il filtro lingua dell'import aperto, i tag di
commercio in andata e ritorno, il catalogo delle categorie. Tutto
cio' che vuole i relay o la chiave Anthropic resta fuori: una prova
che dipende da un server altrui non e' una prova, e' un oroscopo.

USO:  python prove.py          (esce 1 se qualcosa e' rotto)
"""

import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
os.chdir(QUI)                      # carica_comuni legge dati/comuni.csv

PASSATE, FALLITE = 0, 0


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def pezzo(nome, fine="\n\n\n"):
    """Estrae una funzione da server.py senza importarlo tutto (che
    vorrebbe config.py, anthropic e mezzo mondo). La parentesi nel
    cerca-nome e' voluta: 'normalizza(' non deve pescare
    'normalizza_foto_import'."""
    src = _SORGENTE
    i = src.index(f"def {nome}(")
    return src[i:src.index(fine, i)]


_SORGENTE = open("server.py", encoding="utf-8").read()


# ====================================================================
def prove_filtro_italiano():
    """Il filtro lingua dell'import aperto, sui casi VERI incontrati
    sui relay. Il vecchio filtro a sottostringhe li sbagliava quasi
    tutti (vedi i commenti di annuncio_italiano)."""
    print("\n[filtro italiano]")
    import csv
    import re
    import unicodedata

    amb = {"re": re, "unicodedata": unicodedata, "csv": csv, "os": os,
           "COMUNI": {}, "COMUNI_LISTA": [],
           "COMUNI_PAROLA": {"paese", "vita", "sale", "calcio", "none",
                             "parete", "ora", "bella", "dolce"},
           "PREPOSIZIONI_COMUNI": {
               "di", "del", "della", "dell", "delle", "dei", "degli",
               "nel", "nell", "nella", "nello", "sul", "sull", "sulla",
               "sullo", "in", "al", "all", "allo", "alla", "agli",
               "alle", "la", "lo", "l", "de", "d"}}
    # _chiave_comune e' il cuore CONDIVISO dello scanner a n-grammi:
    # coordinate_da_zona ci si appoggia, quindi va estratto anche lui.
    for f in ("normalizza", "carica_comuni", "_chiave_comune",
              "coordinate_da_zona", "annuncio_italiano"):
        exec(pezzo(f), amb)
    i = _SORGENTE.index("PAROLE_FUNZIONE_IT = {")
    exec(_SORGENTE[i:_SORGENTE.index("}", i) + 1], amb)
    amb["carica_comuni"]()
    prova("il dataset comuni si carica", True, len(amb["COMUNI"]) > 7000)
    ita = amb["annuncio_italiano"]

    def ev(titolo="", contenuto="", zona=""):
        tags = [["title", titolo]]
        if zona:
            tags.append(["location", zona])
        return {"tags": tags, "content": contenuto, "kind": 30402}

    prova("comune vero (Brescia)", True, bool(ita(ev("Jade", zona="Brescia"))))
    prova("comune con provincia (Dro (TN))", True,
          bool(ita(ev("Motore", zona="Dro (TN)"))))
    prova("«Spedisco in tutta Italia»", True,
          bool(ita(ev("x", zona="Spedisco in tutta Italia"))))
    prova("spagnolo con «como» NON passa", False,
          bool(ita(ev("Juego de Rol",
                      "Un libro como ningun otro para el juego",
                      zona="valles"))))
    prova("«Italian Language Lessons» NON passa", False,
          bool(ita(ev("Italian Language Lessons (Online)",
                      "Learn Italian with a native speaker"))))
    prova("Croazia NON passa", False,
          bool(ita(ev("Elektromaterijal", zona="Croatia"))))
    prova("italiano riconosciuto senza zona", True,
          bool(ita(ev("Bici da corsa",
                      "Vendo la bici che non uso piu, con freni nuovi "
                      "e spedizione inclusa per tutta la penisola"))))
    prova("inglese senza zona NON passa", False,
          bool(ita(ev("Racing bike", "Selling my bike, great condition"))))


# ====================================================================
def prove_testo_evento():
    """Il testo di un evento e' il cuore CONDIVISO fra chi scrive
    l'annuncio e chi decide se la moderazione l'ha gia' giudicato: se
    i due divergessero, un annuncio fermo sembrerebbe cambiare a ogni
    giro e si ripagherebbe l'AI per nulla."""
    print("\n[testo dell'evento]")
    import importa_nostr as imp

    nip99 = {"kind": 30402, "content": "Come nuova, spedisco",
             "tags": [["title", " Tastiera "], ["summary", "riassunto"]]}
    prova("NIP-99: titolo dal tag, ripulito", "Tastiera",
          imp.testo_evento(nip99)[0])
    prova("NIP-99: il content batte il summary", "Come nuova, spedisco",
          imp.testo_evento(nip99)[1])
    prova("NIP-99: senza content vale il summary", "riassunto",
          imp.testo_evento({"kind": 30402, "content": "",
                            "tags": [["title", "x"],
                                     ["summary", "riassunto"]]})[1])
    # Il caso che l'estrazione fatta a mano nel vaglio sbagliava: per
    # un prodotto NIP-15 il titolo sta nel JSON, non nei tag — e un
    # titolo vuoto vuol dire moderare un annuncio senza leggerlo.
    prova("NIP-15: il titolo si pesca dentro il JSON", "Miele",
          imp.testo_evento({"kind": 30018, "tags": [],
                            "content": '{"name":"Miele","description":"buono"}'})[0])
    prova("NIP-15: JSON storto non esplode", ("", ""),
          imp.testo_evento({"kind": 30018, "tags": [], "content": "{{{"}))
    prova("descrizione vuota diventa il trattino", "—",
          imp.testo_evento({"kind": 30402, "content": "",
                            "tags": [["title", "x"]]})[1])
    # I troncamenti sono quelli con cui l'annuncio finisce nel
    # database: se qui fossero piu' larghi, il confronto direbbe
    # «cambiato» per sempre su ogni testo lungo.
    lungo = {"kind": 30402, "content": "d" * 2000,
             "tags": [["title", "t" * 200]]}
    prova("titolo troncato a 120", 120, len(imp.testo_evento(lungo)[0]))
    prova("descrizione troncata a 1500", 1500, len(imp.testo_evento(lungo)[1]))


# ====================================================================
def prove_tag_commercio():
    """I tag di spedizione/condizione/quantita': andata, ritorno, il
    dialetto Shopstr e le due trappole (costo assente, weight)."""
    print("\n[tag di commercio]")
    import importa_nostr as imp
    amb = {}
    # tag_commercio passa da condizione_da_mostrare, che sa dove la
    # condizione non vuol dire niente: le sue dipendenze vanno nello
    # stesso ambiente, o la prova esplode invece di fallire.
    i = _SORGENTE.index("CATEGORIE_SENZA_CONDIZIONE = frozenset(")
    exec(_SORGENTE[i:_SORGENTE.index("\n\n", i)], amb)
    for f in ("senza_condizione", "condizione_da_mostrare"):
        exec(pezzo(f), amb)
    i = _SORGENTE.index("CONDIZIONE_NIP99 = {")
    exec(_SORGENTE[i:_SORGENTE.index(
        "\n\n\n", _SORGENTE.index("def tag_commercio"))], amb)
    scrivi = amb["tag_commercio"]
    leggi = imp.estrai_commercio

    def ev(tags):
        return {"kind": 30402, "tags": tags, "content": ""}

    prova("spedizione in euro", [["delivery", "shipping", "5.00", "EUR"]],
          scrivi({"consegna": "spedizione", "spedizione_eur": 5.0}))
    prova("«entrambe» diventa due tag",
          [["delivery", "shipping", "3.00", "EUR"], ["delivery", "pickup"]],
          scrivi({"consegna": "entrambe", "spedizione_eur": 3.0}))
    prova("condizione tradotta", [["condition", "like-new"]],
          scrivi({"condizione": "come_nuovo"}))
    prova("un pezzo solo non si scrive", [], scrivi({"quantita": 1}))
    prova("tre pezzi si scrivono", [["stock", "3"]], scrivi({"quantita": 3}))
    prova("chi non dichiara nulla non ha tag", [],
          scrivi({"consegna": "", "condizione": ""}))

    # TRAPPOLA 1: costo assente non e' gratis
    prova("costo NON dichiarato resta indefinito",
          {"consegna": "spedizione", "anche_digitale": 0},
          leggi(ev([["delivery", "shipping"]])))
    prova("costo zero e' gratis davvero",
          0.0, leggi(ev([["delivery", "shipping", "0", "EUR"]]))
          .get("spedizione_eur"))
    # TRAPPOLA 2: il weight di Shopstr e' una variante, non un peso
    prova("il «weight» variante non diventa un peso", {},
          leggi(ev([["weight", "500g", "12.00"]])))

    # dialetto Shopstr
    prova("Shopstr «Added Cost»", 4.5,
          leggi(ev([["shipping", "Added Cost", "4.50", "EUR"]]))
          .get("spedizione_eur"))
    prova("Shopstr «Free» e' gratis, non 4.50", None,
          leggi(ev([["shipping", "Free", "4.50", "EUR"]]))
          .get("spedizione_eur"))
    prova("Shopstr «Free/Pickup» = entrambe", "entrambe",
          leggi(ev([["shipping", "Free/Pickup", "0", "EUR"]]))
          .get("consegna"))
    prova("Shopstr «quantity»", {"quantita": 7},
          leggi(ev([["quantity", "7"]])))
    prova("«unlimited» si ignora", {}, leggi(ev([["stock", "unlimited"]])))

    # Le due guardie che i relay non devono poter scavalcare: l'import
    # scrive dritto nel database, quindi qui non c'e' nessun giudice
    # del payload a fermare un numero assurdo o una promessa che il
    # venditore non puo' mantenere.
    prova("lo stock fuori scala si lima al tetto",
          imp.MAX_QUANTITA_ANNUNCIO,
          leggi(ev([["stock", "999999"]])).get("quantita"))
    prova("uno stock sano non si tocca", 7,
          leggi(ev([["stock", "7"]])).get("quantita"))
    prova("«delivery digital» da solo non fa una consegna digitale",
          None, leggi(ev([["delivery", "digital"]])).get("consegna"))
    prova("e in combo non accende nemmeno anche_digitale", 0,
          leggi(ev([["delivery", "shipping", "0", "EUR"],
                    ["delivery", "digital"]])).get("anche_digitale"))

    # il giro si chiude
    for nome, ann in [
            ("EUR + condizione + quantita",
             {"consegna": "spedizione", "spedizione_eur": 5.0,
              "condizione": "buono", "quantita": 2}),
            ("ritiro", {"consegna": "ritiro", "condizione": "da_sistemare"})]:
        atteso = dict(ann)
        atteso.setdefault("anche_digitale", 0)
        if atteso.get("quantita") == 1:
            atteso.pop("quantita")
        if ann.get("consegna") in ("spedizione", "entrambe"):
            atteso.setdefault("spedizione_eur", 0)
            atteso.setdefault("spedizione_sats", 0)
        prova(f"giro completo: {nome}", atteso, leggi(ev(scrivi(ann))))


# ====================================================================
def prove_anello():
    """Il tappo del bug dell'anello (lug 2026): Barattolo non importa
    Barattolo, e l'import non crede sulla parola al filtro `authors`
    del relay. Sono due righe che un rifattorizzatore distratto
    toglierebbe senza accorgersi, e costano 40 annunci fantasma."""
    print("\n[l'anello non si richiude]")
    import re
    amb = {"npub_to_hex": None}
    # npub_to_hex serve al confronto npub↔hex: si estrae con lui
    for f in ("npub_to_hex", "chiave_di_casa"):
        exec(pezzo(f), amb)
    nostra = "ab" * 32
    amb["_NOSTR"] = (None, nostra)
    di_casa = amb["chiave_di_casa"]
    prova("la nostra hex è di casa", True, di_casa(nostra))
    prova("in maiuscolo lo è lo stesso", True, di_casa(nostra.upper()))
    prova("quella di un altro no", False, di_casa("cd" * 32))
    prova("il vuoto non è di casa", False, di_casa(""))
    prova("una stringa storta non esplode", False, di_casa("npub1zzz"))
    # anche in forma npub, che è come la scrive utenti.npub_accesso
    i = _SORGENTE.index("CHARSET_BECH32 = ")
    exec(_SORGENTE[i:_SORGENTE.index("\n", i)], amb)
    exec(pezzo("_bech32_polymod"), amb)
    exec(pezzo("hex_to_npub"), amb)
    prova("la nostra npub è di casa", True,
          di_casa(amb["hex_to_npub"](nostra)))
    prova("la npub di un altro no", False,
          di_casa(amb["hex_to_npub"]("cd" * 32)))
    # a Nostr spento non deve dire di sì a tutto
    amb["_NOSTR"] = None
    prova("con Nostr spento nessuna chiave è «di casa»", False,
          di_casa(nostra))

    # La sentinella sull'autore: qui non c'è una funzione da chiamare
    # (il filtro è dentro importa_venditore), quindi si guarda che ci
    # sia. Grezza, ma è esattamente il pezzo che sparisce per sbaglio.
    corpo = open("importa_nostr.py", encoding="utf-8").read()
    i = corpo.index("def importa_venditore(")
    corpo = corpo[i:corpo.index("\ndef ", i + 10)]
    prova("l'import confronta l'autore dell'evento con la chiave chiesta",
          True,
          bool(re.search(r'\(e\.get\("pubkey"\)\s*or\s*""\)\.lower\(\)\s*'
                         r'[!=]=\s*hexkey', corpo)))


# ====================================================================
def prove_categorie():
    """Il catalogo e' UNO: server, frontend e import devono dire le
    stesse categorie. Questa prova esiste perche' aggiungerne una
    vuol dire toccare SETTE posti, ed e' facile dimenticarne uno."""
    print("\n[categorie]")
    import re
    amb = {}
    i = _SORGENTE.index("CATEGORIE = (")
    exec(_SORGENTE[i:_SORGENTE.index(")", i) + 1], amb)
    cat = list(amb["CATEGORIE"])
    prova("«Altro» chiude sempre il catalogo", "Altro", cat[-1])
    prova("nessun doppione", len(cat), len(set(cat)))

    html = open("miniapp.html", encoding="utf-8").read()
    i = html.index("const CATS = [")
    front = re.findall(r'"([^"]+)"', html[i:html.index("]", i)])
    prova("le pillole del frontend combaciano col server",
          ["Tutto"] + cat, front)

    i = html.index('<select id="sellCat"')
    sel = re.findall(r"<option>([^<]+)</option>",
                     html[i:html.index("</select>", i)])
    prova("il form Vendi offre tutto il catalogo", cat, sel)

    i = html.index("const EMOJI_CAT = {")
    emoji = re.findall(r"'([^']+)':'", html[i:html.index("};", i)])
    prova("ogni categoria ha la sua emoji", sorted(cat), sorted(emoji))

    # Anche i dati finti della DEMO devono parlare il catalogo vero,
    # o le pillole non li aggancerebbero e la demo mostrerebbe una
    # vetrina vuota — che e' il posto peggiore per una figuraccia.
    demo = sorted(set(re.findall(r'cat:"([^"]+)"', html)))
    prova("le categorie della demo esistono nel catalogo",
          [], [c for c in demo if c not in cat])

    # L'import NON indovina piu' la categoria: gli annunci che
    # arrivano da Nostr nascono in «Altro» e a collocarli e' il
    # venditore. Questa prova esiste perche' l'indovinello e' una
    # tentazione che torna: sbaglia in silenzio, e sugli importati
    # nessuno se ne accorge.
    import importa_nostr as imp
    prova("l'import non indovina piu' le categorie", False,
          hasattr(imp, "categoria_automatica"))

    exec(pezzo("categoria_tollerante"), amb)
    i = _SORGENTE.index("SINONIMI_CATEGORIA = {")
    exec(_SORGENTE[i:_SORGENTE.index("\n}", i) + 2], amb)
    orfani = sorted({v for v in amb["SINONIMI_CATEGORIA"].values()
                     if v not in cat})
    prova("nessun sinonimo punta a una categoria che non esiste",
          [], orfani)
    prova("il CSV che dice «bevande» viene capito", "Alimenti e bevande",
          amb["categoria_tollerante"]("bevande"))
    prova("e chi scrive «profumi» finisce nella bellezza",
          "Bellezza e benessere", amb["categoria_tollerante"]("profumi"))

    # Il SESTO posto, che il cantiere aveva dimenticato: il modello CSV
    # che scaricano i commercianti. Non rompe niente se resta indietro
    # (categoria_tollerante ripiega sulla prima parola), ma insegna
    # nomi che non esistono — ed e' il primo file che un negozio nuovo
    # apre. La colonna della categoria e' la quinta.
    i = _SORGENTE.index("MODELLO_IMPORT = (")
    exec(_SORGENTE[i:_SORGENTE.index("\n\n", i)], amb)
    righe = [r for r in amb["MODELLO_IMPORT"].strip().splitlines() if r]
    del righe[0]                                   # l'intestazione
    prova("le categorie del modello CSV esistono nel catalogo", [],
          [r.split(";")[4] for r in righe if r.split(";")[4] not in cat])
    prova("una categoria inventata finisce in Altro", "Altro",
          amb["categoria_tollerante"]("fantacategoria"))
    for c in cat:
        if amb["categoria_tollerante"](c) != c:
            prova(f"il catalogo passa da categoria_tollerante ({c})",
                  c, amb["categoria_tollerante"](c))

    # Il SETTIMO posto (lug 2026, pagina Sfoglia): l'illustrazione. E'
    # anche l'unico che non si vede finche' non si apre la pagina — una
    # piastrella senza immagine mostra l'emoji di ripiego e sembra
    # quasi giusta. Meglio che a dirlo sia la CI.
    exec(pezzo("slug_categoria"), amb)
    slug = amb["slug_categoria"]
    prova("nessuno slug di categoria si sovrappone a un altro",
          len(cat), len({slug(c) for c in cat}))
    prova("il frontend calcola lo slug come il server", True,
          "c.toLowerCase().replace(/ /g,'-')" in html)
    prova("ogni categoria ha la sua illustrazione", [],
          [c for c in cat
           if not os.path.exists(f"assets/categorie/{slug(c)}.webp")])
    # e il suo francobollo per il foglio-picker di Vendi: si dimentica
    # facilmente, perche' manca solo la' dentro e il ripiego a emoji
    # fa sembrare che vada tutto bene
    prova("ogni categoria ha il suo francobollo -mini", [],
          [c for c in cat
           if not os.path.exists(f"assets/categorie/{slug(c)}-mini.webp")])

    # Le illustrazioni devono essere TIRATE, cioe' senza margine
    # trasparente attorno (ci pensa ritaglia_categorie.py). Non e' una
    # pignoleria: la piastrella le posa in un riquadro tarato al pixel
    # sotto il nome, e un file con margini renderebbe il disegno
    # piccolo dentro quel riquadro — la cosa che si e' appena
    # sistemata. Peggio: il margine sposta il disegno verso l'alto e
    # le sue zone quasi bianche possono tornare sotto le lettere, dove
    # il nome in crema fa 1,00:1 e sparisce. Un testo invisibile non
    # lo nota nessuno finche' non lo segnala un utente: meglio la CI.
    try:
        from PIL import Image
    except ImportError:
        print("  · Pillow assente: salto il controllo del ritaglio")
    else:
        # Le illustrazioni devono essere PAREGGIATE, cioe' nessuna deve
        # coprire molto piu' inchiostro delle altre una volta resa in
        # piastrella (ci pensa ritaglia_categorie.py). Si misura
        # l'inchiostro e non il rettangolo perche' e' quello che
        # l'occhio pesa: un pallone e una chitarra possono avere lo
        # stesso rettangolo, ma il pallone e' pieno e sembra il triplo.
        # Il tetto e' generoso apposta — qui non si insegue la
        # perfezione, si prende il file rifatto che sfonda.
        BOX_W, BOX_H, TETTO = 85.9, 69.0, 1.30
        resi = {}
        for c in cat:
            p = f"assets/categorie/{slug(c)}.webp"
            if not os.path.exists(p):
                continue
            # il file si misura COM'E', bordo trasparente compreso: e'
            # quello che scala il browser, ed e' proprio quel bordo a
            # fare il pareggio. Ritagliarlo qui vorrebbe dire annullare
            # la cosa che si sta verificando (successo per davvero).
            a = Image.open(p).convert("RGBA").getchannel("A")
            ink = sum(n * i for i, n in enumerate(a.histogram())) / 255.0
            s = min(BOX_W / a.size[0], BOX_H / a.size[1])
            resi[c] = ink * s * s
        if resi:
            ordinati = sorted(resi.values())
            mediana = ordinati[len(ordinati) // 2]
            prova("nessuna illustrazione pesa piu' delle altre in griglia",
                  [], [c for c, v in resi.items() if v > mediana * TETTO])


# ====================================================================
def prove_senza_condizione():
    """Le categorie dove la condizione non vuol dire niente (lug 2026).
    Server e frontend tengono lo stesso elenco — il catalogo si
    hardcoda in tutti e due, come le categorie — quindi qui si
    incrociano: se divergessero, il form chiederebbe una condizione che
    il server butta via (o peggio, il contrario)."""
    print("\n[categorie senza condizione]")
    import re
    amb = {}
    i = _SORGENTE.index("CATEGORIE_SENZA_CONDIZIONE = frozenset(")
    exec(_SORGENTE[i:_SORGENTE.index("\n\n", i)], amb)
    exec(pezzo("senza_condizione"), amb)
    senza = amb["senza_condizione"]

    html = open("miniapp.html", encoding="utf-8").read()
    i = html.index("const CAT_SENZA_COND = [")
    front = re.findall(r"'([^']+)'", html[i:html.index("]", i)])
    prova("l'elenco del frontend combacia col server",
          sorted(amb["CATEGORIE_SENZA_CONDIZIONE"]), sorted(front))

    # e le categorie esenti devono ESISTERE nel catalogo, o l'elenco
    # sarebbe una regola che non si applica mai a nessuno
    j = _SORGENTE.index("CATEGORIE = (")
    exec(_SORGENTE[j:_SORGENTE.index(")", j) + 1], amb)
    prova("le categorie esenti esistono nel catalogo", [],
          [c for c in amb["CATEGORIE_SENZA_CONDIZIONE"]
           if c not in amb["CATEGORIE"]])

    prova("la marmellata non ha condizione", True,
          senza("Alimenti e bevande", "spedizione"))
    prova("e nemmeno la crema mani", True,
          senza("Bellezza e benessere", "spedizione"))
    prova("il portatile si', invece", False, senza("Informatica", "spedizione"))
    # il secondo asse: il codice online e' nuovo per definizione, ma
    # SOLO quando e' l'unica strada
    prova("il codice online da solo non ha condizione", True,
          senza("Altro", "digitale"))
    prova("la combo fisica+codice la chiede lo stesso", False,
          senza("Altro", "spedizione"))
    prova("senza consegna dichiarata si chiede", False, senza("Altro", ""))
    prova("la categoria vince anche senza consegna", True,
          senza("Alimenti e bevande", ""))


# ====================================================================
def prove_sottocategorie():
    """L'albero DORMIENTE (ago 2026): definito nel catalogo, mostrato
    da nessuna parte. Le prove difendono il patto scritto sopra
    SOTTOCATEGORIE: id per sempre, unici in TUTTO l'albero (un domani
    un filtro senza categoria non dev'essere ambiguo), niente voci
    «Altro X», e un giudice che non lascia passare niente di storto."""
    print("\n[sottocategorie]")
    amb = {}
    i = _SORGENTE.index("CATEGORIE = (")
    exec(_SORGENTE[i:_SORGENTE.index(")", i) + 1], amb)
    i = _SORGENTE.index("SOTTOCATEGORIE = {")
    exec(_SORGENTE[i:_SORGENTE.index("\n}", i) + 2], amb)
    albero = amb["SOTTOCATEGORIE"]
    cat = list(amb["CATEGORIE"])

    prova("ogni chiave dell'albero e' una categoria vera", [],
          [c for c in albero if c not in cat])
    prova("«Altro» resta piatta per forza", False, "Altro" in albero)
    tutti = [sid for voci in albero.values() for sid, _ in voci]
    prova("id unici in TUTTO l'albero", len(tutti), len(set(tutti)))
    import re
    prova("id kebab-case, mai vuoti", [],
          [s for s in tutti if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s)])
    prova("nessuna voce si chiama «altro»", [],
          [(sid, nome) for voci in albero.values() for sid, nome in voci
           if "altro" in sid or nome.strip().lower().startswith("altro")])
    prova("nessuna etichetta vuota o doppia nella stessa categoria", [],
          [c for c, voci in albero.items()
           if len({n for _, n in voci}) != len(voci)
           or any(not n.strip() for _, n in voci)])

    for f in ("sottocategoria_valida", "sottocategoria_tollerante"):
        exec(pezzo(f), amb)
    valida = amb["sottocategoria_valida"]
    prova("una voce valida passa", "mtb", valida("Biciclette", "mtb"))
    prova("una voce di un'ALTRA categoria non passa", "",
          valida("Biciclette", "gift-card"))
    prova("una voce inventata non passa", "", valida("Biciclette", "carbonio"))
    prova("il vuoto resta vuoto", "", valida("Biciclette", ""))
    prova("None non esplode", "", valida("Biciclette", None))
    prova("una categoria piatta non ha voci", "", valida("Altro", "mtb"))
    prova("una categoria inventata non ha voci", "",
          valida("Fantacategoria", "mtb"))

    tollera = amb["sottocategoria_tollerante"]
    prova("il CSV che dice l'id viene capito", "ebike",
          tollera("Biciclette", "ebike"))
    prova("il CSV che dice l'ETICHETTA viene capito", "ebike",
          tollera("Biciclette", "E-BIKE"))
    prova("l'etichetta con gli spazi viene capita", "olio-condimenti",
          tollera("Alimenti e bevande", "Olio e condimenti"))
    prova("una voce storta e' '' e mai uno scarto", "",
          tollera("Biciclette", "bici volante"))

    # --- il giudice SILENZIOSO (ago 2026): parole chiave dentro la
    # categoria gia' scelta. La proprieta' che le prove difendono e'
    # l'ASTENSIONE: sul dubbio risponde '', mai un'assegnazione tirata
    # a indovinare.
    amb["re"], amb["unicodedata"] = __import__("re"), \
        __import__("unicodedata")
    i = _SORGENTE.index("SINONIMI_SOTTOCATEGORIA = {")
    exec(_SORGENTE[i:_SORGENTE.index("\n}", i) + 2], amb)
    for f in ("normalizza", "_parola_sottocategoria",
              "sottocategoria_indovina"):
        exec(pezzo(f), amb)
    sin = amb["SINONIMI_SOTTOCATEGORIA"]
    prova("il dizionario parla solo di categorie vere", [],
          [c for c in sin if c not in albero])
    prova("ogni voce del dizionario esiste nell'albero", [],
          [(c, v) for c, voci in sin.items() for v in voci
           if v not in {sid for sid, _ in albero[c]}])
    prova("ogni voce dell'albero ha le sue parole", [],
          [(c, sid) for c, voci in albero.items() for sid, _ in voci
           if sid not in sin.get(c, {})])

    g = amb["sottocategoria_indovina"]
    prova("il poster si riconosce", "poster-stampe",
          g("Bitcoin", 'Poster A1 "White Paper"', ""))
    prova("il titolo pesa doppio (il Buono soggiorno)",
          "soggiorni-esperienze",
          g("Buoni ed esperienze", "Buono soggiorno due notti", ""))
    prova("il pareggio e' un dubbio e il dubbio resta ''", "",
          g("Bitcoin", "poster wallet", ""))
    prova("'auto' non prende 'autoradio'", "",
          g("Motori", "Autoradio Pioneer", ""))
    prova("il prefisso lungo invece lavora", "outdoor",
          g("Sport e hobby", "kit per escursioni", ""))
    prova("senza parole si astiene", "",
          g("Libri e media", "bitcoin standard", "nuovo"))
    prova("una categoria piatta non giudica", "",
          g("Altro", "Poster bellissimo", ""))
    prova("gli accenti non contano", "cucina-tavola",
          g("Casa e giardino", "Caffettièra anni 60", ""))


# ====================================================================
def prove_ricategorizza():
    """Lo script di ricategorizzazione legge il catalogo da server.py
    (fonte unica) e non si fida delle risposte dell'AI: un «NON SO» o
    una categoria inventata devono lasciare l'annuncio dov'e'."""
    print("\n[ricategorizzazione]")
    import ricategorizza as ric

    cat = ric.catalogo()
    j = _SORGENTE.index("CATEGORIE = (")
    amb = {}
    exec(_SORGENTE[j:_SORGENTE.index(")", j) + 1], amb)
    prova("lo script legge il catalogo vero", list(amb["CATEGORIE"]), cat)

    leggi = lambda riga: (ric.RIGA.match(riga).groups()
                          if ric.RIGA.match(riga) else None)
    prova("verdetto normale", ("3", "Informatica"), leggi("3: Informatica"))
    prova("verdetto con la parentesi", ("12", "Alimenti e bevande"),
          leggi(" 12) Alimenti e bevande "))
    prova("«NON SO» non e' una categoria del catalogo", False,
          leggi("7: NON SO")[1] in cat)
    prova("una categoria inventata non e' nel catalogo", False,
          leggi("7: Fantacategoria")[1] in cat)
    prova("una riga di chiacchiere non e' un verdetto", None,
          leggi("Ecco i risultati:"))


# ====================================================================
def main():
    print("=" * 58)
    print("  LE PROVE DI BARATTOLO")
    print("=" * 58)
    for f in (prove_filtro_italiano, prove_testo_evento,
              prove_tag_commercio, prove_anello, prove_categorie,
              prove_senza_condizione, prove_sottocategorie,
              prove_ricategorizza):
        try:
            f()
        except Exception as e:
            global FALLITE
            FALLITE += 1
            print(f"  ✗ {f.__name__} è esplosa: {type(e).__name__}: {e}")
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
