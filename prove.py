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
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
os.chdir(QUI)                      # carica_comuni legge dati/comuni.csv

PASSATE, FALLITE, SALTATE = 0, 0, 0

# In CI una prova saltata e' una prova ROTTA: li' le dipendenze si
# installano apposta, quindi se una manca vuol dire che qualcosa e'
# andato storto. In locale invece chi non ha Pillow deve poter girare
# le prove lo stesso, e gli basta vederlo scritto.
SEVERE = bool(os.environ.get("PROVE_SEVERE"))


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def salta(nome, perche):
    """Una prova che non si puo' girare. Va CONTATA, non sussurrata:
    per mesi il controllo dell'inchiostro delle illustrazioni non e'
    mai girato in CI (Pillow non si installava) e a dirlo c'era una
    riga discreta in mezzo a duecento spunte — dal di fuori sembrava
    tutto verde perche' era tutto verde: quella prova non c'era."""
    global SALTATE
    SALTATE += 1
    print(f"  · SALTATA: {nome} — {perche}")


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
        salta("il pareggio dell'inchiostro delle illustrazioni",
              "Pillow non e' installata")
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
def prove_nome_nostr():
    """Come si chiama chi arriva dai relay (lug 2026). Il kind-0 lo
    scrive un estraneo: quel testo finisce sotto i suoi annunci, quindi
    dev'essere una riga sola e corta — e senza nome si deve poter dire
    «non lo so», che e' cio' che tiene la npub abbreviata al suo posto
    invece di cancellarla."""
    print("\n[nome dal kind-0 Nostr]")
    amb = {}
    i = _SORGENTE.index("MAX_NOME_NOSTR = ")
    exec(_SORGENTE[i:_SORGENTE.index("\n", i) + 1], amb)
    exec(pezzo("nome_da_profilo"), amb)
    nome = amb["nome_da_profilo"]

    prova("display_name batte name", "Anna dei Fiori",
          nome({"name": "anna", "display_name": "Anna dei Fiori"}))
    prova("senza display_name vale name", "anna", nome({"name": "anna"}))
    prova("displayName in cammello (i client vecchi)", "Anna",
          nome({"displayName": "Anna"}))
    prova("display_name vuoto ripiega su name", "anna",
          nome({"name": "anna", "display_name": "   "}))
    prova("gli a capo diventano una riga sola", "Anna dei Fiori",
          nome({"name": "Anna\n\ndei   Fiori"}))
    prova("il nome lunghissimo si taglia", amb["MAX_NOME_NOSTR"],
          len(nome({"name": "a" * 200})))
    prova("kind-0 muto = nessun nome", "", nome({}))
    prova("kind-0 senza nome = nessun nome", "",
          nome({"about": "vendo miele", "picture": "http://x/y.jpg"}))
    prova("un nome che non e' testo non conta", "", nome({"name": 42}))


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
    # il caso vero che ha fatto nascere «Mare e piscina» (ago 2026):
    # un telo da MARE in una categoria giusta senza una voce che lo
    # accogliesse. Il titolo normalizzato da' il token «amare», non
    # «mare»: a prenderlo dev'essere «telo».
    prova("il Telo d'Amare trova la sua voce", "mare-piscina",
          g("Sport e hobby", "III° Telo d'Amare, del (primo) trittico "
                            "2026", "canapa antica sulla spoletta di "
                                    "tessitura"))
    prova("e «amare» da solo non accende «mare»", "",
          g("Sport e hobby", "Imparare ad amare", ""))


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
# ====================================================================
def prove_asta():
    """La matematica pura dell'asta: minimo coi suoi arrotondamenti,
    proroga anti-cecchino, etichette anonime e il conto della chiusura
    con l'invariante dei totali. Il caso PARI-CIFRA e' la lezione del
    collaudo del passo 3: due saldi nello stesso secondo esistono, a
    parita' comanda chi ha saldato prima (saldo_seq) — per prendere la
    testa bisogna SUPERARE."""
    print("\n[asta]")
    amb = {}
    for f in ("rilancio_minimo", "nuova_scadenza", "etichetta_offerente",
              "conto_chiusura"):
        exec(pezzo(f), amb)

    rm = amb["rilancio_minimo"]
    prova("minimo: 5% di 100.000", 105_000, rm(100_000, 5))
    prova("minimo: 5% di 19 fa 0 per difetto, vale il +1", 20, rm(19, 5))
    prova("minimo: 5% di 10 sats fa 0, vale il +1", 11, rm(10, 5))
    prova("minimo: mai un pareggio possibile", 2, rm(1, 5))

    ns = amb["nuova_scadenza"]
    prova("proroga: saldo negli ultimi minuti sposta a saldo+proroga",
          1100, ns(1000, 500, 600))
    prova("proroga: fuori finestra non sposta", 1000, ns(1000, 300, 600))
    prova("proroga: al filo della scadenza niente (e' un tardivo)",
          1000, ns(1000, 1000, 600))

    et = amb["etichetta_offerente"]
    prova("etichette: A..Z poi AA, AB", ["A", "B", "Z", "AA", "AB"],
          [et(i) for i in (0, 1, 25, 26, 27)])

    cc = amb["conto_chiusura"]

    def p(i, off, ver, seq, stato="attiva"):
        return {"id": i, "tg_id": 100 + i, "offerto_sats": off,
                "versato_sats": ver, "saldo_seq": seq, "stato": stato}

    v, r = cc([p(1, 100, 100, 1), p(2, 120, 120, 2),
               p(3, 90, 90, 3, "chiusa")])
    prova("chiusura: vince l'offerta piu' alta", 2, v["id"])
    prova("chiusura: le chiuse non entrano nei rimborsi",
          [1], [x["puntata_id"] for x in r])
    prova("chiusura: invariante dei totali (vincitore + rimborsi)",
          100 + 120, v["versato_sats"] + sum(x["importo_sats"] for x in r))
    # Il caso PARI-CIFRA: la corsa di due fatture nate sulla stessa
    # testa. Vince chi ha SALDATO prima, anche se la sua riga di
    # puntata e' nata dopo (id piu' alto).
    v, r = cc([p(1, 140, 140, 9), p(2, 140, 140, 8)])
    prova("pari-cifra: vince chi ha saldato prima", 2, v["id"])
    prova("pari-cifra: l'altro nei rimborsi per il suo versato",
          [(1, 140)], [(x["puntata_id"], x["importo_sats"]) for x in r])
    v, r = cc([p(1, 0, 0, 0)])
    prova("deserta: nessuna vincitrice, nessun rimborso",
          (None, []), (v, r))

    # Il giudice SQL della testa, sul gemello in memoria (ermetico:
    # niente file, niente config — solo la tabella che serve).
    import sqlite3
    exec(pezzo("_leader_asta"), amb)
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE puntate(id INTEGER PRIMARY KEY, "
                "annuncio_id INT, tg_id INT, offerto_sats INT, "
                "versato_sats INT, saldo_seq INT, stato TEXT)")
    con.executemany("INSERT INTO puntate VALUES(?,?,?,?,?,?,?)", [
        (1, 7, 111, 140, 140, 9, "attiva"),
        (2, 7, 333, 140, 140, 8, "attiva"),   # pari-cifra, saldato prima
        (3, 7, 444, 150, 150, 4, "chiusa"),   # ritirato: fuori gara
        (4, 8, 111, 999, 999, 1, "attiva")])  # un'altra asta
    testa = amb["_leader_asta"](con, 7)
    prova("leader SQL: a pari-cifra comanda chi ha saldato prima",
          2, testa["id"])
    prova("leader SQL: il ritirato non conta anche se offre di piu'",
          True, testa["offerto_sats"] == 140)
    con.close()
    # I due giudici devono restare GEMELLI: sentinelle sul testo (e'
    # il tipo di parita' che un refactor spezza in silenzio).
    prova("un solo ordine: _leader_asta ordina su saldo_seq", True,
          "saldo_seq ASC" in pezzo("_leader_asta"))
    prova("un solo ordine: conto_chiusura decide su saldo_seq", True,
          '"saldo_seq"' in pezzo("conto_chiusura"))

    # La guardia delle DURATE (elenco allargato a [1,3,7,14,30], ago
    # 2026): TUTTO passa dall'elenco — validazione, avviso 1h e
    # proroghe non assumono mai 3/7 — e fuori elenco e' un 400, mai un
    # default silenzioso: qui si mette in gioco il denaro altrui.
    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code = code
            super().__init__(detail)
    amb2 = {"ASTA_ABILITATA": True, "MODALITA_COLLAUDO": False,
            "ASTA_DURATE_GIORNI": [1, 3, 7, 14, 30],
            "HTTPException": _H}
    exec(pezzo("durata_asta_da_payload"), amb2)
    dur = amb2["durata_asta_da_payload"]
    prova("durata: 7 giorni in secondi", 7 * 86400,
          dur({"asta": {"durata_giorni": 7}}))
    prova("durata: anche il giorno singolo", 86400,
          dur({"asta": {"durata_giorni": 1}}))
    prova("durata: 30 giorni, il piu' lungo", 30 * 86400,
          dur({"asta": {"durata_giorni": 30}}))
    prova("durata: senza payload asta non e' un'asta", 0, dur({}))
    for storta in (2, 5, 0, "x"):
        try:
            dur({"asta": {"durata_giorni": storta}})
            esito = "passata (!)"
        except _H:
            esito = "400"
        prova(f"durata fuori elenco = 400 ({storta!r})", "400", esito)
    # ...e i due gemelli del config dicono le STESSE durate
    cfg = open("config_esempio.py", encoding="utf-8").read()
    prova("durate: server e config_esempio gemelli", True,
          "[1, 3, 7, 14, 30]" in _SORGENTE
          and "[1, 3, 7, 14, 30]" in cfg)
    # La CINTURA del saldo su puntata ritirata (decisione di Andrea al
    # passo 4): una fattura pagata nei suoi 10 minuti ma mai
    # verificata sopravvive alla finestra del ritiro — quel saldo va
    # nel registro, MAI versato su una puntata 'chiusa'. La sentinella
    # controlla che il gate del ramo fuori-tempo guardi anche lo stato
    # della puntata: e' la riga che un refactor perde in silenzio.
    corpo_verifica = _SORGENTE[_SORGENTE.index("async def verifica_rilancio"):]
    corpo_verifica = corpo_verifica[:corpo_verifica.index("\n\n\n")]
    prova("cintura: il saldo su puntata non-attiva finisce nel registro",
          True, 'p["stato"] != "attiva"' in corpo_verifica
          and "'tardivo'" in corpo_verifica)


def prove_proxy_asta():
    """Il proxy a budget depositato (ago 2026): VERSATO (il budget,
    segreto) vs ESPOSTO (la puntata in gara). Il motore delle
    esposizioni e' una pura IDEMPOTENTE e MONOTONA: due proxy
    convergono in una passata sola, nessun esposto scende mai, e per
    le manuali produce l'identita' di sempre (esposto = versato) —
    che e' la prova di regressione: chi non usa il proxy non deve
    accorgersi di niente."""
    print("\n[proxy d'asta]")
    amb = {}
    for f in ("rilancio_minimo", "esposizioni_proxy", "conto_chiusura"):
        exec(pezzo(f), amb)
    mot = amb["esposizioni_proxy"]
    cc = amb["conto_chiusura"]

    def p(i, ver, off, seq, proxy=0, stato="attiva"):
        return {"id": i, "tg_id": 100 + i, "versato_sats": ver,
                "offerto_sats": off, "saldo_seq": seq, "proxy": proxy,
                "stato": stato}

    prova("solo in gara: il proxy espone la BASE", {1: 1000},
          mot([p(1, 50_000, 0, 1, proxy=1)], 1000, 5))
    prova("manuale: esposto = versato, sempre", {1: 2000},
          mot([p(1, 2000, 2000, 1)], 1000, 5))
    prova("manuale sotto il budget: il proxy si difende al minimo",
          {1: 10_500, 2: 10_000},
          mot([p(1, 50_000, 1000, 1, proxy=1),
               p(2, 10_000, 10_000, 2)], 1000, 5))
    prova("manuale sopra il budget: il proxy e' esausto, esposto tutto",
          {1: 8000, 2: 10_000},
          mot([p(1, 8000, 1000, 1, proxy=1),
               p(2, 10_000, 10_000, 2)], 1000, 5))
    r = mot([p(1, 100_000, 1000, 1, proxy=1),
             p(2, 80_000, 0, 2, proxy=1)], 1000, 5)
    prova("proxy vs proxy: il perdente esposto al suo massimo",
          80_000, r[2])
    prova("proxy vs proxy: il leader un incremento sopra (una passata)",
          84_000, r[1])
    prova("budget esattamente = testa+incremento: copre e prende la testa",
          {1: 10_000, 2: 10_500},
          mot([p(1, 10_000, 10_000, 1),
               p(2, 10_500, 0, 2, proxy=1)], 1000, 5))
    prova("cap: dentro l'incremento si espone il proprio massimo, mai oltre",
          {1: 1000, 2: 999},
          mot([p(1, 1000, 0, 1, proxy=1), p(2, 999, 999, 2)], 100, 5))
    prova("pari-budget: entrambi esposti pieni (decide saldo_seq)",
          {1: 5000, 2: 5000},
          mot([p(1, 5000, 0, 9, proxy=1),
               p(2, 5000, 0, 8, proxy=1)], 100, 5))
    prova("monotonia: l'esposto non scende mai (rivale sparito)",
          {1: 9000, 2: 5000},
          mot([p(1, 20_000, 9000, 1, proxy=1),
               p(2, 5000, 5000, 2)], 100, 5))
    prova("fuori gara: chiuse e mai-salde non compaiono", {1: 1000},
          mot([p(1, 1000, 1000, 1), p(2, 900, 900, 2, stato="chiusa"),
               p(3, 0, 0, 0)], 100, 5))
    campo = [p(1, 100_000, 1000, 1, proxy=1),
             p(2, 80_000, 0, 2, proxy=1), p(3, 5000, 5000, 3)]
    una = mot(campo, 1000, 5)
    campo2 = [dict(x, offerto_sats=una[x["id"]]) for x in campo]
    prova("idempotenza: il motore e' un punto fisso (niente convergenza "
          "eterna)", una, mot(campo2, 1000, 5))
    prova("invariante: versato >= offerto su ogni uscita", True,
          all(una[x["id"]] <= x["versato_sats"] for x in campo))

    # Il conto della chiusura col proxy: la vincitrice paga l'ESPOSTO,
    # l'eccedenza e' una riga sua del registro.
    v, r = cc([p(1, 50_000, 10_500, 1, proxy=1),
               p(2, 10_000, 10_000, 2)])
    prova("chiusura: vince l'esposto piu' alto", 1, v["id"])
    prova("chiusura: perdente col versato pieno e motivo suo",
          [(2, 10_000)],
          [(x["puntata_id"], x["importo_sats"]) for x in r
           if x["motivo"] == "perdente"])
    prova("chiusura: l'eccedenza della vincitrice al registro",
          [(1, 39_500)],
          [(x["puntata_id"], x["importo_sats"]) for x in r
           if x["motivo"] == "eccedenza"])
    prova("chiusura: INVARIANTE nuova (esposto vincitrice + registro)",
          50_000 + 10_000,
          v["offerto_sats"] + sum(x["importo_sats"] for x in r))
    v, r = cc([p(1, 100, 100, 1), p(2, 120, 120, 2)])
    prova("regressione: manuali senza riga eccedenza", [],
          [x for x in r if x["motivo"] == "eccedenza"])

    # Coerenza dei due giudici: sul campo POST-motore il leader per
    # esposto (_leader_asta) e' il leader per capacita' del motore —
    # sul pari-budget decide lo stesso saldo_seq.
    import sqlite3
    exec(pezzo("_leader_asta"), amb)
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE puntate(id INTEGER PRIMARY KEY, "
                "annuncio_id INT, tg_id INT, offerto_sats INT, "
                "versato_sats INT, saldo_seq INT, stato TEXT)")
    con.executemany("INSERT INTO puntate VALUES(?,?,?,?,?,?,?)", [
        (1, 7, 101, 5000, 5000, 9, "attiva"),
        (2, 7, 102, 5000, 5000, 8, "attiva")])
    prova("coerenza: il giudice SQL concorda col motore sul pari-budget",
          2, amb["_leader_asta"](con, 7)["id"])
    con.close()

    # Le due cinture dell'eccedenza: indici PARZIALI distinti — il
    # ritiro volontario una volta sola, e la riga di CHIUSURA che
    # convive sulla stessa puntata (un motivo unico, con la fusione
    # che riaccende il proxy, la farebbe ignorare in silenzio).
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE rimborsi_asta(id INTEGER PRIMARY KEY, "
                "puntata_id INT, motivo TEXT)")
    con.execute("CREATE UNIQUE INDEX ir ON rimborsi_asta(puntata_id) "
                "WHERE motivo = 'eccedenza_ritiro'")
    con.execute("CREATE UNIQUE INDEX ie ON rimborsi_asta(puntata_id) "
                "WHERE motivo = 'eccedenza'")
    for _ in (1, 2):
        con.execute("INSERT OR IGNORE INTO rimborsi_asta(puntata_id,"
                    "motivo) VALUES(7,'eccedenza_ritiro')")
    prova("eccedenza_ritiro: una volta sola (indice parziale)", 1,
          con.execute("SELECT COUNT(*) FROM rimborsi_asta").fetchone()[0])
    con.execute("INSERT OR IGNORE INTO rimborsi_asta(puntata_id,motivo) "
                "VALUES(7,'eccedenza')")
    prova("la riga di chiusura convive col ritiro (motivi distinti)", 2,
          con.execute("SELECT COUNT(*) FROM rimborsi_asta").fetchone()[0])
    con.close()

    # --- le sentinelle: le righe che un refactor perde in silenzio ---
    corpo_mot = pezzo("esposizioni_proxy")
    prova("la proroga NON vive nel motore", True,
          "nuova_scadenza" not in corpo_mot
          and "asta_scadenza" not in corpo_mot)
    corpo_verifica = _SORGENTE[_SORGENTE.index(
        "async def verifica_rilancio"):]
    corpo_verifica = corpo_verifica[:corpo_verifica.index("\n\n\n")]
    prova("il motore gira PRIMA del giudizio della testa", True,
          corpo_verifica.index("esposizioni_proxy")
          < corpo_verifica.index("testa_dopo ="))
    prova("la proroga ha la guardia del top-up (asta eterna a costo "
          "zero)", True,
          "if not era_leader or testa_cambiata:" in corpo_verifica)
    dopo_venditore = corpo_verifica[corpo_verifica.index("Nuova puntata"):]
    prova("il venditore sente l'ESPOSTO, mai il totale dichiarato", True,
          "ril['offerto_sats']" not in dopo_venditore)
    ramo_tardivo = corpo_verifica[corpo_verifica.index("FUORI TEMPO"):
                                  corpo_verifica.index("testa_prima =")]
    prova("il tardivo non alza mai il flag proxy", True,
          "proxy" not in ramo_tardivo)
    corpo_punta = _SORGENTE[_SORGENTE.index("async def fai_puntata"):]
    corpo_punta = corpo_punta[:corpo_punta.index("\n\n\n")]
    prova("da leader si rilancia solo col proxy (top-up)", True,
          "sono_leader and not vuole_proxy" in corpo_punta)
    prova("proxy a leva spenta = porta chiusa", True,
          "vuole_proxy and not ASTA_PROXY_ATTIVO" in corpo_punta)
    prova("eccedenza ritirata = niente piu' proxy su quest'asta", True,
          "eccedenza_ritiro" in corpo_punta)
    corpo_chiusura = pezzo("_chiudi_una_asta")
    prova("l'ordine del vincitore dice l'ESPOSTO", True,
          'vincitrice["offerto_sats"]' in corpo_chiusura
          and 'vincitrice["versato_sats"]' not in corpo_chiusura)
    corpo_racconto = _SORGENTE[_SORGENTE.index(
        "async def _racconta_chiusura"):]
    corpo_racconto = corpo_racconto[:corpo_racconto.index("\n\n\n")]
    prova("il racconto di chiusura non dice mai il versato", True,
          "v['versato_sats']" not in corpo_racconto)
    corpo_fusione = pezzo("esegui_fusione")
    prova("fusione: il motore rimette in riga gli esposti", True,
          "esposizioni_proxy" in corpo_fusione)
    prova("fusione: l'esposto non e' mai la somma", True,
          "somma, somma" not in corpo_fusione)
    prova("cronologia: legge esposto_sats, mai il totale dichiarato",
          True, "r.esposto_sats" in pezzo("stato_asta", "\n\n\n"))
    cfg = open("config_esempio.py", encoding="utf-8").read()
    prova("leva proxy spenta di serie, nei due file", True,
          "ASTA_PROXY_ATTIVO = False" in _SORGENTE
          and "ASTA_PROXY_ATTIVO = False" in cfg)


def prove_annullo():
    """L'annullo vero e il QR vero (ago 2026). Quasi tutte sentinelle
    testuali: sono le righe che un refactor perde in silenzio — il
    controllo del pagamento PRIMA dell'annullo, il CAS sullo stato,
    la lapide al posto del DELETE, il riacciuffo nell'orologio."""
    print("\n[annullo e QR]")

    def corpo(nome):
        i = _SORGENTE.index(f"def {nome}(")
        return _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]

    # --- annulla_ordine: pagamento prima, CAS, lapide (mai DELETE)
    ann = corpo("annulla_ordine")
    prova("annullo ordine: il pagamento si controlla PRIMA", True,
          "invoice_pagata" in ann
          and ann.index("invoice_pagata") < ann.index("stato='annullato'"))
    prova("annullo ordine: CAS sullo stato 'creato'", True,
          "WHERE id=? AND stato='creato'" in ann
          and "rowcount == 0" in ann)
    prova("annullo ordine: lapide, mai DELETE", True,
          "stato='annullato'" in ann and "DELETE FROM ordini" not in ann)
    prova("annullo ordine: le righe dei set restano con la lapide",
          True, "DELETE FROM ordine_righe" not in ann)

    # --- il gemello dei rilanci
    anr = corpo("annulla_rilancio")
    prova("annullo rilancio: pagamento prima + CAS + lapide", True,
          "invoice_pagata" in anr
          and "WHERE id=? AND stato='creato'" in anr
          and "stato='annullato'" in anr
          and "DELETE FROM rilanci" not in anr)

    # --- la corsa: il saldo su una lapide viene riacciuffato
    sw = corpo("controlla_annullati")
    prova("riacciuffo: l'ordine annullato-ma-pagato torna 'creato' e "
          "passa da _incassa_ordine", True,
          "stato='creato'" in sw and "_incassa_ordine" in sw
          and "WHERE id=? AND stato='annullato'" in sw)
    prova("riacciuffo: il rilancio annullato-ma-pagato va nel binario "
          "del fuori-tempo", True,
          "'tardivo'" in sw and "rimborsi_asta" in sw
          and "_paga_rimborso" in sw)
    orologio_corpo = corpo("orologio")
    prova("riacciuffo: agganciato all'orologio", True,
          "controlla_annullati()" in orologio_corpo)

    # --- verifica_pagamento passa dal cuore estratto
    ver = corpo("verifica_pagamento")
    inc = corpo("_incassa_ordine")
    prova("verifica: il cuore e' _incassa_ordine", True,
          "_incassa_ordine" in ver)
    prova("incasso: CAS 'creato' -> 'locked'", True,
          "SET stato='locked'" in inc
          and "WHERE id=? AND stato='creato'" in inc)
    # il riacciuffo in CONFLITTO (oggetto andato a un altro nel
    # frattempo): lo stock non va MAI negativo — e' il MAX del corner
    # del reaper, e il riacciuffo ci passa dentro per costruzione
    prova("incasso: lo stock non va mai negativo (MAX)", True,
          "MAX(quantita-?,0)" in inc)

    # --- la ripresa del pentito in compra()
    cmp_ = corpo("compra")
    prova("ripresa: l'ordine proprio pendente si ripresenta", True,
          '"ripresa": True' in cmp_ and "RIPRESA_INVOICE_S" in cmp_)
    prova("ripresa: la fattura gia' pagata si incassa, mai annullata",
          True, "_incassa_ordine" in cmp_
          and cmp_.index("invoice_pagata") < cmp_.index("stato='annullato'"))

    # --- il reaper spazza le lapidi solo a fattura ormai morta
    reaper = corpo("pulisci_ordini_fantasma")
    prova("reaper: purga delle lapidi ordini (dopo la finestra)", True,
          "stato='annullato'" in reaper and "3600" in reaper)
    prova("reaper: purga delle lapidi rilanci", True,
          "IN ('creato','annullato')" in reaper)
    ris = corpo("_riservati")
    prova("prenotazione: la lapide libera lo stock per costruzione",
          True, "stato='annullato'" not in ris
          and "stato='creato'" in ris)

    # --- il QR: vero, e l'Annulla del foglio che annulla davvero
    mini = open("miniapp.html", encoding="utf-8").read()
    # (il repeating-conic-gradient dell'anello del tappo e' legittimo:
    # la sentinella guarda la scacchiera ink-su-bianco del QR finto)
    prova("QR: la scacchiera decorativa non esiste piu'", False,
          "repeating-conic-gradient(#23282C" in mini)
    prova("QR: la resa vera esiste (lightning: maiuscolo, alfanumerico)",
          True, "mostraQr" in mini and "'Alphanumeric'" in mini
          and "'lightning:'" in mini and ".toUpperCase()" in mini)
    prova("QR: la libreria e' vendorizzata e servita da casa", True,
          os.path.exists("vendor/qrcode.js")
          and '"/vendor/qrcode.js"' in _SORGENTE
          and "/vendor/qrcode.js" in mini)
    swjs = open("sw.js", encoding="utf-8").read()
    prova("QR: in dispensa PWA con la VERSIONE alzata", True,
          "/vendor/qrcode.js" in swjs
          and "barattolo-v2" not in swjs)
    prova("paySheet: l'Annulla annulla davvero (e la chiusura no)", True,
          'onclick="annullaPagamento()">Annulla' in mini
          and "annullaPagamento" in mini)
    prova("paySheet: la conferma avverte chi ha gia' pagato", True,
          "NON annullare" in mini)
    # la regressione del foglio tagliato (ago 2026): il QR aveva
    # allungato il paySheet oltre la viewport e il bordo alto finiva
    # tagliato senza scroll — queste due righe sono la cura
    prova("foglio: scorre quando il contenuto eccede", True,
          "overflow-y:auto;overscroll-behavior:contain" in mini
          and "max-height:calc(100dvh - 16px)" in mini)
    prova("QR: la misura segue l'altezza disponibile (mai sotto i "
          "170px)", True, "max(170px, 30dvh)" in mini)


def prove_ritiro():
    """Il ritiro a mano (ago 2026, dal campo): il compratore conferma
    da 'locked' senza aspettare che il venditore segni nulla — rischia
    solo lui, la semantica del deposito — e il ritiro mai concluso non
    resta muto per sempre: il promemoria gira nell'orologio."""
    print("\n[ritiro a mano]")

    def corpo(nome):
        i = _SORGENTE.index(f"def {nome}(")
        return _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]

    conf = corpo("conferma_ricezione")
    prova("conferma: il server la accetta da 'locked'", True,
          "'locked'" in conf)
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("ordine: il bottone di conferma esiste anche a locked-ritiro",
          True, "s==='locked' && o.consegnaScelta==='ritiro'" in mini
          and "L\\'ho ritirato" in mini)
    soll = corpo("sollecita_ritiri_fermi")
    prova("ritiro fermo: il promemoria guarda locked+ritiro", True,
          "stato='locked'" in soll and "consegna_scelta='ritiro'" in soll)
    prova("ritiro fermo: mai sats mossi, solo parole", True,
          "UPDATE ordini SET sollecito_ritiro_il" in soll
          and "_sblocca_sats" not in soll and "released" not in soll)
    prova("ritiro fermo: agganciato all'orologio", True,
          "sollecita_ritiri_fermi()" in corpo("orologio"))
    # l'auto-sblocco resta ancorato alle DICHIARAZIONI: controlla_scadenze
    # non deve toccare i 'locked' (nessuno ha dichiarato niente)
    scad = corpo("controlla_scadenze")
    prova("auto-sblocco: mai dai 'locked' senza dichiarazioni", False,
          "stato='locked'" in scad)


def prove_disarmo():
    """IL DISARMO DELL'AUTO-SBLOCCO (ago 2026): in questa fase i sats
    non si muovono senza un gesto umano. Una sentinella per ogni riga
    del censimento — quelle che devono tacere e quelle che devono
    restare accese: se un domani qualcuno riarma un ramo per sbaglio,
    qui si accende un rosso."""
    print("\n[disarmo dell'auto-sblocco]")

    def corpo(nome):
        i = _SORGENTE.index(f"def {nome}(")
        return _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]

    cfg = open("config_esempio.py", encoding="utf-8").read()
    # 1-3: le tre leve nuove, col default sicuro e il gemello nel config
    prova("leva: nasce False nel codice", True,
          "AUTO_SBLOCCO_ATTIVO = False" in _SORGENTE)
    prova("leva: gemella in config_esempio", True,
          "AUTO_SBLOCCO_ATTIVO = False" in cfg)
    prova("promemoria: leve gemelle server/config", True,
          "PROMEMORIA_CONFERMA_GIORNI = 3" in _SORGENTE
          and "PROMEMORIA_CONFERMA_GIORNI = 3" in cfg
          and "PROMEMORIA_CONFERMA_MAX = 3" in _SORGENTE
          and "PROMEMORIA_CONFERMA_MAX = 3" in cfg)

    scad = corpo("controlla_scadenze")
    gate = scad.index("if AUTO_SBLOCCO_ATTIVO:")
    # 4-5: i due rami FISICI stanno DENTRO il gate (cioe' dopo di lui)
    prova("ramo 72h: disarmato dalla leva", True,
          scad.index("ORE_CONFERMA * 3600") > gate)
    prova("ramo 10gg: disarmato dalla leva", True,
          scad.index("GIORNI_AUTO_SBLOCCO * 86400") > gate)
    # 6-7: i due rami DIGITALI restano fuori dal gate, sempre armati
    prova("digitale 24h: resta armato (fuori dal gate)", True,
          scad.index("ORE_CONFERMA_DIGITALE") > gate
          and "if AUTO_SBLOCCO_ATTIVO" not in
              scad[scad.index("scaduti_digitale"):])
    prova("digitale 48h: resta armato", True,
          "ORE_SILENZIO_DIGITALE" in scad)
    # 8: la prova storica non deve ingiallire
    prova("auto-sblocco: mai dai 'locked' senza dichiarazioni", False,
          "stato='locked'" in scad)

    prom = corpo("sollecita_conferme_ferme")
    # 9-12: il sostituto non muove sats, e' agganciato, e non dimentica i set
    prova("promemoria: mai sats mossi, solo parole", True,
          "UPDATE ordini SET sollecito_conferma_il" in prom
          and "_sblocca_sats" not in prom and "released" not in prom)
    prova("promemoria: agganciato all'orologio", True,
          "sollecita_conferme_ferme()" in corpo("orologio"))
    prova("promemoria: e' il sostituto, non un'aggiunta", True,
          "if AUTO_SBLOCCO_ATTIVO or PROMEMORIA_CONFERMA_GIORNI <= 0" in prom)
    prova("promemoria: i set non restano fuori (LEFT JOIN)", True,
          "LEFT JOIN annunci" in prom)
    prova("promemoria: il digitale non lo riguarda", True,
          "consegna_scelta != 'digitale'" in prom)
    # 13-14: l'unico ponte timer->fondi, e i gemelli che restano muti
    prova("sblocco automatico: un solo chiamante in tutto il file", True,
          _SORGENTE.count("automatico=True") == 1)
    for g in ("sollecita_incassi", "sollecita_ritiri_fermi",
              "sollecita_rimborsi_puntate"):
        prova(f"{g}: resta senza sblocchi", True,
              "_sblocca_sats" not in corpo(g))
    # 15-16: i timer che RESTITUISCONO restano agganciati (eccezione
    # dichiarata: non spostano sats da una parte a un'altra)
    oro = corpo("orologio")
    prova("asta e riacciuffo: ancora agganciati", True,
          "chiudi_aste()" in oro and "controlla_annullati()" in oro)

    mini = open("miniapp.html", encoding="utf-8").read()
    # 17-19: il client non promette piu' lo sblocco sul FISICO
    prova("client: niente sblocco promesso da soli", False,
          "si sbloccano da soli" in mini or "d'ufficio" in mini)
    prova("client: il countdown resta al solo digitale", True,
          "TEMPI.confermaDig*3600" in mini
          and "oreFinestra = digitale ? 24 : 72" not in mini)
    prova("client: nessun tempo battuto a mano", False,
          "mi prendo 24h" in mini)
    # le voci di TEMPI sono incolonnate: il confronto salta gli spazi
    prova("client: TEMPI e config restano gemelli", True,
          all(re.search(rf"\b{k}:\s+{v},", mini) for k, v in
              (("conferma", 72), ("autoSblocco", 10),
               ("confermaDig", 24), ("silenzioDig", 48)))
          and "ORE_CONFERMA = 72" in cfg
          and "GIORNI_AUTO_SBLOCCO = 10" in cfg
          and "ORE_CONFERMA_DIGITALE = 24" in cfg
          and "ORE_SILENZIO_DIGITALE = 48" in cfg)

    # --- IL PROMEMORIA AL VENDITORE FERMO (ago 2026, buco 1 chiuso) ---
    # Il gemello speculare: li' aspettiamo il compratore, qui il
    # venditore. Buco PREESISTENTE al disarmo, quindi con regole sue.
    ven = corpo("sollecita_venditori_fermi")
    # 20-21: le due leve del primo squillo, gemelle server/config
    prova("venditore fermo: leva spedizione gemella", True,
          "PROMEMORIA_SPEDIZIONE_GIORNI = 5" in _SORGENTE
          and "PROMEMORIA_SPEDIZIONE_GIORNI = 5" in cfg)
    prova("venditore fermo: leva digitale gemella", True,
          "PROMEMORIA_DIGITALE_ORE = 48" in _SORGENTE
          and "PROMEMORIA_DIGITALE_ORE = 48" in cfg)
    # 22: mai sats mossi, solo parole (la regola cardinale)
    prova("venditore fermo: mai sats mossi, solo parole", True,
          "UPDATE ordini SET sollecito_venditore_il" in ven
          and not any(x in ven for x in
                      ("_sblocca_sats", "_rimborsa_compratore",
                       "_paga_rimborso", "paga_venditore", "released")))
    # 23: E' UN'AGGIUNTA, NON UN SOSTITUTO — se un domani la leva torna
    # accesa col tracking verificato, il buco non deve riaprirsi
    # (si cerca la forma della GUARDIA, non il nome: la leva e' nominata
    # apposta nella docstring, ed e' li' che si spiega perche' non c'e')
    prova("venditore fermo: gira anche a leva riaccesa", False,
          "if AUTO_SBLOCCO_ATTIVO" in ven)
    # 24: l'ancora e' `creato`, immutabile — con `aggiornato` il
    # venditore sposterebbe il proprio squillo da deposita_invoice
    prova("venditore fermo: ancora immutabile, non `aggiornato`", True,
          "o.creato + ?" in ven and "o.aggiornato" not in ven)
    # 25: contatore SUO, o al primo giro dopo la spedizione il
    # compratore si troverebbe la sua popolazione gia' al tetto
    prova("venditore fermo: contatore suo, mai quello del compratore", True,
          "solleciti_venditore" in ven and "solleciti_conferma" not in ven)
    # 26-27: i set non restano fuori, il ritiro non squilla due volte
    prova("venditore fermo: i set non restano fuori (LEFT JOIN)", True,
          "LEFT JOIN annunci" in ven)
    # le due strade sono voci di una tupla; il ritiro NON dev'esserci in
    # nessuna forma di virgolette, o squillerebbe due volte
    prova("venditore fermo: il ritiro ha gia' la sua funzione", True,
          '"spedizione", PROMEMORIA_SPEDIZIONE_GIORNI' in ven
          and '"digitale", PROMEMORIA_DIGITALE_ORE' in ven
          and '"ritiro"' not in ven and "'ritiro'" not in ven)
    # 28: agganciato all'orologio, o non suona mai
    prova("venditore fermo: agganciato all'orologio", True,
          "sollecita_venditori_fermi()" in oro)


def _finto_lnbits(uscite, codice=200, muto=False):
    """Un LNbits di cartone che REGISTRA ogni chiamata invece di
    farla. L'asserzione che conta in questa sezione e' sempre la
    stessa: la richiesta di pagamento non e' mai partita.
    Con `muto` il nodo prende la chiamata e non risponde mai: e' il
    caso in cui i sats possono essere usciti senza che lo sappiamo."""
    import types

    class R:
        status_code = codice

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    class C:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kw):
            uscite.append(url)
            if muto:
                raise TimeoutError("il nodo non ha risposto")
            return R()

    return types.SimpleNamespace(AsyncClient=C)


def _finto_lnurl(meta, fattura):
    """Il wallet del beneficiario, che nel LNURL-pay e' chi SCRIVE la
    fattura — qui lo facciamo mentire a comando."""
    import types

    class R:
        def __init__(self, dati):
            self._d = dati

        def raise_for_status(self):
            pass

        def json(self):
            return self._d

    class C:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, **kw):
            return R(meta if ".well-known" in url else {"pr": fattura})

    return types.SimpleNamespace(AsyncClient=C)


def prove_importo_uscita():
    """C-1 (ago 2026): l'importo di ogni bolt11 in uscita si controlla
    contro il DOVUTO. Nel LNURL-pay la fattura la fabbrica il wallet
    del beneficiario: senza questo confronto un ln_address su dominio
    proprio rispondeva con qualunque cifra e LNbits la pagava, col
    saldo della cassaforte come unico tetto. Qui si prova che il
    pagamento NON PARTE — non che 'torna False': che la POST verso
    l'admin key non viene proprio fatta."""
    print("\n[importo in uscita]")
    import asyncio

    def gira(coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def pezzo_async(nome):
        """pezzo() cerca «def nome(» e su una funzione async lascia
        fuori la parola: gliela si rimette, o l'await non ha casa."""
        return "async " + pezzo(nome)

    # --- LA CINTURA: paga_venditore ---------------------------------
    def cintura(dice_la_fattura, dovuti, codice=200):
        """Monta paga_venditore con un giudice dell'importo finto e un
        LNbits di cartone. Torna (esito, quante POST, quanti avvisi)."""
        uscite, avvisi = [], []

        async def _importo(_b):
            return dice_la_fattura

        async def _admin(t):
            avvisi.append(t)

        amb = {"httpx": _finto_lnbits(uscite, codice),
               "importo_invoice": _importo, "notifica_admin": _admin,
               "print": lambda *a, **k: None,
               "LNBITS_URL": "http://x", "LNBITS_ADMIN_KEY": "k",
               # i tre esiti (ago 2026): qui interessa il rifiuto, ma
               # senza i nomi la funzione non gira nemmeno
               "PAGATO": "pagato", "NON_PAGATO": "non_pagato",
               "INCERTO": "incerto"}
        exec(pezzo_async("paga_venditore"), amb)
        return gira(amb["paga_venditore"]("lnbc", dovuti)), len(uscite), len(avvisi)

    # 1: il caso felice deve restare felice — e' meta' della prova
    prova("cintura: importo esatto, il pagamento parte", ("pagato", 1, 0),
          cintura(50_000, 50_000))
    # 2: LA FALLA. Un sat dovuto, cento milioni nella fattura.
    #    (Il rifiuto e' NON_PAGATO e non INCERTO: qui sappiamo
    #    benissimo com'e' andata — non e' partito niente.)
    prova("cintura: ECCESSO rifiutato, zero POST", ("non_pagato", 0, 1),
          cintura(100_000_000, 1))
    # 3: pagare meno non e' un favore — e' un ordine chiuso con un
    #    venditore non pagato, e i sats restano orfani in cassaforte
    prova("cintura: DIFETTO rifiutato, zero POST", ("non_pagato", 0, 1),
          cintura(1, 100))
    # 4: fattura illeggibile (LNbits muto): fail-closed
    prova("cintura: invoice illeggibile rifiutata, zero POST",
          ("non_pagato", 0, 1), cintura(None, 100))
    # 5: un'uscita a zero non ha un mittente legittimo
    prova("cintura: dovuto zero rifiutato, zero POST", ("non_pagato", 0, 1),
          cintura(0, 0))
    # 6: e i moderatori lo sanno sempre — mai dentro un return False
    prova("cintura: il rifiuto avvisa i moderatori", 1, cintura(999, 1)[2])

    # --- LA TOPPA: invoice_da_ln_address ----------------------------
    def lnurl(fattura_vale, chiesti, pr="lnbc1"):
        async def _importo(_b):
            return fattura_vale

        # il `callback` va messo davvero: senza, la funzione morirebbe
        # di KeyError dentro il suo try e tornerebbe None per il motivo
        # sbagliato — tre verdi che non provano niente
        amb = {"httpx": _finto_lnurl(
                   {"tag": "payRequest", "minSendable": 1,
                    "maxSendable": 10 ** 12,
                    "callback": "https://dominio.tld/cb"}, pr),
               "importo_invoice": _importo,
               "print": lambda *a, **k: None}
        exec(pezzo_async("invoice_da_ln_address"), amb)
        return gira(amb["invoice_da_ln_address"]("io@dominio.tld", chiesti))

    prova("address: wallet onesto, la fattura passa", "lnbc1",
          lnurl(50_000, 50_000))
    prova("address: wallet che gonfia, scartata", None,
          lnurl(100_000_000, 1))
    prova("address: wallet che sgonfia, scartata", None, lnurl(1, 100))
    prova("address: nessuna fattura, scartata", None,
          lnurl(100, 100, pr=""))

    # --- SENTINELLE: il controllo non deve sparire in un riordino ----
    # Sono di quelle che se ne vanno in silenzio: nessuna prova
    # funzionale si rompe, e la falla torna. Quindi si difende la
    # FORMA, non solo il comportamento.
    # 0: tutti e quattro i tubi verso LNbits dicono quanto aspettano.
    #    Su quelli in entrata un timeout e' innocuo, ma l'unico senza
    #    numero sembra una dimenticanza — e un giorno lo sara'.
    prova("i quattro tubi LNbits dicono quanto aspettano", [],
          [n for n in ("crea_invoice_escrow", "invoice_pagata",
                       "paga_venditore", "decodifica_invoice")
           if "httpx.AsyncClient(timeout=" not in pezzo(n)])
    pv = pezzo("paga_venditore")
    lna = pezzo("invoice_da_ln_address")
    # 1: obbligatorio SENZA default, o chi scrive la prossima strada
    #    d'uscita puo' dimenticarlo senza che Python fiati
    prova("sentinella: atteso_sats obbligatorio, senza default", True,
          "async def paga_venditore(invoice: str, atteso_sats: int)"
          in _SORGENTE)
    # 2: il rifiuto sta PRIMA della chiamata all'admin key
    prova("sentinella: si rifiuta prima di toccare l'admin key", True,
          "importo_invoice" in pv
          and pv.index("return NON_PAGATO") < pv.index("LNBITS_ADMIN_KEY"))
    # 3: la chiamata a un argomento non deve esistere piu' da nessuna
    #    parte — e' la sentinella che prende il refactor distratto
    prova("sentinella: nessuna chiamata a un solo argomento", [],
          re.findall(r"paga_venditore\([^,)]*\)", _SORGENTE))
    # 4: il cuore e' UNO — se qualcuno ricopia l'aritmetica dei
    #    millisat, le tre strade possono contare in modo diverso
    prova("sentinella: l'aritmetica dei msat vive in un posto solo", 1,
          _SORGENTE.count('int(dec.get("amount_msat"'))
    # 5: la `pr` del callback non torna piu' nuda
    prova("sentinella: la fattura del wallet si rilegge sempre", True,
          "importo_invoice" in lna
          and 'return r.json().get("pr")' not in lna)


def prove_pagamento_incerto():
    """Il timeout di paga_venditore (ago 2026, audit). LNbits puo'
    aver pagato e non essere riuscito a dircelo: prima l'eccezione
    risaliva, il database non registrava NIENTE e il tentativo dopo
    coniava una fattura nuova dal Lightning address — cioe' pagava
    una seconda volta per davvero. Qui si prova il non-fatto: nessuna
    seconda uscita, nessuno stato riscritto."""
    print("\n[il pagamento incerto]")
    import asyncio
    import sqlite3

    def gira(coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def pezzo_async(nome):
        return "async " + pezzo(nome)

    async def _niente(*a, **k):
        return None

    ESITI = {"PAGATO": "pagato", "NON_PAGATO": "non_pagato",
             "INCERTO": "incerto"}

    # --- 1. I tre esiti di paga_venditore ---------------------------
    def paga(codice=200, muto=False, chiesto=1000):
        uscite = []

        async def _importo(_b):
            return chiesto

        amb = {"httpx": _finto_lnbits(uscite, codice, muto),
               "importo_invoice": _importo, "notifica_admin": _niente,
               "print": lambda *a, **k: None,
               "LNBITS_URL": "http://x", "LNBITS_ADMIN_KEY": "k", **ESITI}
        exec(pezzo_async("paga_venditore"), amb)
        return gira(amb["paga_venditore"]("lnbc1", 1000)), len(uscite)

    prova("nodo che risponde ok: PAGATO", ("pagato", 1), paga())
    prova("nodo che risponde no: NON_PAGATO", ("non_pagato", 1),
          paga(codice=500))
    prova("nodo che TACE: INCERTO, non un fallimento", ("incerto", 1),
          paga(muto=True))
    prova("importo storto: NON_PAGATO e zero uscite", ("non_pagato", 0),
          paga(chiesto=999))

    # --- 2. _sblocca_sats: il congelamento --------------------------
    # Un ordine vero in un database vero (in memoria), e tutto il
    # resto di cartone: quello che si guarda e' la riga dopo.
    def mondo(payout_stato="", esiti=("incerto",)):
        vero = sqlite3.connect(":memory:")
        vero.row_factory = sqlite3.Row
        vero.execute(
            "CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INT, "
            "compratore_id INT, venditore_id INT, prezzo_sats INT, "
            "protezione_sats INT, quantita INT, stato TEXT, disputata INT, "
            "invoice_venditore TEXT, aggiornato INT, cambio_eur REAL, "
            "payout_stato TEXT, payout_hash TEXT, payout_verso TEXT)")
        vero.execute(
            "INSERT INTO ordini VALUES(1,7,111,222,1000,0,1,'delivered',0,"
            f"'',0,0,'{payout_stato}','','')")
        vero.execute("CREATE TABLE utenti(tg_id INT, ln_address TEXT, "
                     "vendite_ok INT, acquisti_ok INT)")
        vero.execute("INSERT INTO utenti VALUES(222,'io@wallet.tld',0,0)")
        vero.commit()

        class Con:
            """close() non chiude davvero: il :memory: deve
            sopravvivere fra una chiamata e l'altra."""
            def execute(self, *a):
                return vero.execute(*a)

            def commit(self):
                vero.commit()

            def close(self):
                pass

        tentativi, coniate = [], []
        resto = list(esiti)

        async def _paga(bolt11, atteso):
            tentativi.append((bolt11, atteso))
            return resto.pop(0) if resto else "non_pagato"

        async def _address(addr, importo):
            # OGNI chiamata conia una fattura NUOVA: e' esattamente il
            # motivo per cui un ritentativo pagherebbe due volte
            coniate.append(addr)
            return f"lnbc-nuova-{len(coniate)}"

        amb = {"db": Con, "time": __import__("time"),
               "_lucchetti_ordine": __import__("collections").defaultdict(
                   asyncio.Lock),
               "netto_venditore": lambda p: p,
               "invoice_da_ln_address": _address, "paga_venditore": _paga,
               "_righe_ordine": lambda con, o: [],
               "_titolo_ordine": lambda righe: "una cosa",
               "cambio_btc_eur": _niente, "notifica": _niente,
               "premia_distintivi": _niente, "polso_ordini_admin": _niente,
               "notifica_admin": _niente, "_payment_hash": _niente,
               # Gli XP dell'affare concluso (ago 2026): qui non si
               # misurano, ma _sblocca_sats li chiama — e senza questi
               # due la prova ESPLODE invece di fallire, che e' la
               # trappola scritta in CLAUDE.md sulle funzioni estratte.
               "premia_xp": _niente, "xp_ordine": lambda *a: 0,
               "print": lambda *a, **k: None, **ESITI}
        exec(pezzo_async("_congela_pagamento"), amb)
        exec(pezzo_async("_sblocca_sats"), amb)
        return amb["_sblocca_sats"], vero, tentativi, coniate

    def riga(vero):
        r = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
        return (r["stato"], r["payout_stato"], r["payout_verso"])

    # il nodo tace: si congela e NON si tocca niente
    sblocca, vero, tentativi, coniate = mondo(esiti=("incerto",))
    gira(sblocca(1))
    prova("incerto: lo stato dell'ordine NON si riscrive",
          ("delivered", "incerto", "venditore"), riga(vero))
    prova("incerto: un tentativo solo, e si ferma li'", 1, len(tentativi))
    # ...e ora tutte le strade normali ci riprovano: non deve uscire
    # nemmeno una fattura nuova
    gira(sblocca(1))
    gira(sblocca(1))
    prova("incerto: nessun secondo pagamento, mai", 1, len(tentativi))
    prova("incerto: nessuna fattura nuova coniata dall'address", 1,
          len(coniate))
    vero.close()

    # il nodo risponde di no: il ramo di sempre, invariato
    sblocca, vero, tentativi, _ = mondo(esiti=("non_pagato",))
    gira(sblocca(1))
    prova("fallimento vero: si va in 'confirmed' come sempre",
          ("confirmed", "", ""), riga(vero))
    vero.close()

    # il moderatore ha guardato su LNbits: era uscito
    sblocca, vero, tentativi, coniate = mondo(payout_stato="uscito")
    gira(sblocca(1))
    prova("«è uscito»: si chiude l'ordine SENZA pagare di nuovo",
          ("released", "uscito", ""), riga(vero))
    prova("«è uscito»: zero tentativi e zero fatture coniate",
          (0, 0), (len(tentativi), len(coniate)))
    vero.close()

    # regressione: il giorno buono resta il giorno buono
    sblocca, vero, tentativi, _ = mondo(esiti=("pagato",))
    gira(sblocca(1))
    prova("pagamento riuscito: 'released' come sempre",
          ("released", "", ""), riga(vero))
    vero.close()

    # --- 3. SENTINELLE ----------------------------------------------
    # Il tri-stato sparisce in un riordino: basta che qualcuno rimetta
    # un `if await paga_venditore(...)` e «incerto» torna a leggersi
    # come successo, senza che nessuna prova funzionale si rompa.
    prova("sentinella: paga_venditore non si legge come booleano", [],
          re.findall(r"(?:and|not|if) await paga_venditore\(", _SORGENTE))
    prova("sentinella: tutt'e tre le uscite guardano l'INCERTO", 3,
          _SORGENTE.count("esito == INCERTO"))
    prova("sentinella: tutt'e tre si fermano se sono congelate", 3,
          _SORGENTE.count('payout_stato"] == "incerto"'))
    prova("sentinella: il congelamento scrive CHI aspettava i sats",
          True, "payout_verso=?" in pezzo("_congela_pagamento"))
    # e la coda admin non deve indovinare la strada dallo stato
    prova("sentinella: la coda admin legge payout_verso, non lo stato",
          True, 'payout_verso"] == "compratore"' in pezzo("decidi_pagamento"))


def prove_disputa_incagliata():
    """Una disputa non si chiude da sola (ago 2026, audit). Quando lo
    sblocco non riusciva a pagare, l'ordine passava a 'confirmed' —
    che e' giusto — ma la coda di risolvi_disputa guardava solo gli
    stati di disputa, e da li' il moderatore non poteva piu' decidere
    NIENTE: in particolare non poteva piu' rimborsare il compratore, e
    i sats restavano fermi senza rimedio."""
    print("\n[la disputa incagliata]")
    import sqlite3

    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE ordini(id INTEGER PRIMARY KEY, stato TEXT, "
                "disputata INT)")
    con.executemany("INSERT INTO ordini VALUES(?,?,?)", [
        (1, "dispute", 1),          # la coda di sempre
        (2, "return_shipped", 1),   # idem
        (3, "confirmed", 1),        # incagliato: sblocco fallito
        (4, "refund", 1),           # incagliato: rimborso fallito
        (5, "confirmed", 0),        # un ordine normale: NON e' una disputa
        (6, "released", 1),         # chiuso davvero: mai piu' in coda
        (7, "refunded", 1)])        # idem
    con.commit()

    # la WHERE vera, estratta dal sorgente invece che riscritta a mano
    i = _SORGENTE.index('o = con.execute("SELECT * FROM ordini WHERE id=? AND (')
    where = _SORGENTE[i:_SORGENTE.index('(ordine_id,)', i)]
    where = where[where.index('"SELECT'):]
    sql = "".join(re.findall(r'"([^"]*)"', where))
    visti = [r["id"] for r in con.execute(
        sql.replace("id=?", "id=id") + " ORDER BY id", ())]
    prova("la coda vede le dispute aperte e le due incagliate",
          [1, 2, 3, 4], visti)
    prova("un 'confirmed' normale non e' una disputa", True, 5 not in visti)
    prova("un affare gia' chiuso non torna in coda", True,
          6 not in visti and 7 not in visti)
    con.close()

    # --- SENTINELLE -------------------------------------------------
    rd = pezzo("risolvi_disputa")
    # riaprire e' cio' che permette di cambiare strada senza allentare
    # le guardie: _sblocca_sats non parte da 'refund', e deve restare
    # cosi' — se un domani qualcuno togliesse la riapertura, il
    # ripensamento tornerebbe a essere un no-op silenzioso
    prova("il caso incagliato si RIAPRE prima di ridecidere", True,
          "stato='dispute'" in rd and 'stato in ("confirmed", "refund")' in rd)
    prova("_sblocca_sats continua a non partire da 'refund'", True,
          '"refund"' in pezzo("_sblocca_sats").split("bolt11")[0])
    # l'esito si valida PRIMA di riaprire, o un esito storto lascerebbe
    # il caso riaperto per niente
    prova("l'esito si valida prima di toccare l'ordine", True,
          rd.index('esito not in ("venditore"') < rd.index("stato='dispute'"))
    # e chi perde una disputa lo viene a sapere, una volta sola
    prova("chi perde lo sblocco viene avvisato", True,
          'o["disputata"] and primo_giro' in pezzo("_sblocca_sats"))
    prova("chi perde il rimborso viene avvisato", True,
          'o["disputata"] and primo_giro' in pezzo("_rimborsa_compratore"))
    prova("l'avviso non si ripete a ogni ritentativo", 2,
          _SORGENTE.count("primo_giro = o[\"stato\"] !="))


def prove_idor_verifica():
    """L'ordine e' MIO (ago 2026, audit). verifica-pagamento era
    l'unica rotta /api/orders/{id}/… senza guardia di proprieta': gli
    id sono progressivi, quindi chiamandoli in fila si leggeva lo
    stato di ogni ordine del mercatino — e si poteva innescare in
    anticipo il flusso di un altro. Qui si prova che un estraneo non
    arriva nemmeno a chiedere a LNbits."""
    print("\n[l'ordine è mio]")
    import asyncio
    import sqlite3

    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    vero = sqlite3.connect(":memory:")
    vero.row_factory = sqlite3.Row
    vero.execute("CREATE TABLE ordini(id INTEGER PRIMARY KEY, "
                 "compratore_id INT, stato TEXT, payment_hash TEXT)")
    vero.executemany("INSERT INTO ordini VALUES(?,?,?,?)", [
        (1, 111, "creato", "hash1"),      # del compratore 111
        (2, 333, "creato", "hash2"),      # di un altro
        (3, 333, "shipped", "hash3")])    # di un altro, gia' avanti
    vero.commit()

    class Con:
        def execute(self, *a):
            return vero.execute(*a)

        def close(self):
            pass

    chiesto = []      # ogni riga = una domanda a LNbits

    async def _pagata(h):
        chiesto.append(h)
        return False

    async def _incassa(oid):
        return {"stato": "locked"}

    def guarda(ordine_id, chi):
        # Header/Cookie servono perche' i default della firma si
        # valutano quando la funzione si definisce, non quando si chiama
        amb = {"db": Con, "HTTPException": _H, "invoice_pagata": _pagata,
               "_incassa_ordine": _incassa,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi}}
        exec("async " + pezzo("verifica_pagamento"), amb)
        try:
            return asyncio.new_event_loop().run_until_complete(
                amb["verifica_pagamento"](ordine_id))
        except _H as e:
            return f"{e.code} {e.detail}"

    prova("il compratore vero passa", {"stato": "in_attesa"},
          guarda(1, 111))
    prova("un estraneo sull'ordine altrui: 400",
          "400 Operazione non permessa", guarda(2, 333 + 1))
    prova("...e non chiede NIENTE a LNbits per conto suo", 1, len(chiesto))
    # l'oracolo: prima si distingueva «non esiste» da «esiste, ed e'
    # in questo stato». Ora le due risposte sono la stessa.
    prova("ordine inesistente e ordine altrui rispondono uguale",
          True, guarda(999, 111) == guarda(3, 111))
    prova("il venditore non passa da qui: e' il compratore che paga",
          "400 Operazione non permessa", guarda(3, 111))
    vero.close()

    # SENTINELLA: l'utente si legge e si USA. Buttarlo via era
    # esattamente il difetto, ed e' una riga che si riperde in un
    # riordino senza rompere nessuna prova funzionale.
    vp = pezzo("verifica_pagamento")
    prova("sentinella: l'utente non si butta via", True,
          "user = verifica_utente(" in vp and "compratore_id=?" in vp)


def prove_contenuti_cifrati():
    """La cifratura a riposo dei codici (ago 2026, audit). La chiave
    si derivava con uno SHA-256 nudo: contro una passphrase debole
    costa un hash a tentativo. Ora c'e' scrypt sotto il prefisso
    'f2', e i due formati convivono per sempre — un database nato
    con la ricetta vecchia deve restare leggibile."""
    print("\n[i contenuti cifrati]")
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    except ImportError:
        salta("la cifratura dei contenuti digitali",
              "cryptography non e' installata")
        return
    import base64
    import hashlib

    def mondo(chiave):
        amb = {"CHIAVE_CONTENUTI_DIGITALI": chiave, "Fernet": Fernet,
               "Scrypt": Scrypt, "base64": base64, "hashlib": hashlib}
        i = _SORGENTE.index("_SALE_CONTENUTI = ")
        exec(_SORGENTE[i:_SORGENTE.index("\n\n\n", i)], amb)
        exec(pezzo("_chiave_fernet"), amb)
        exec(pezzo("_cifra_contenuto"), amb)
        exec(pezzo("_decifra_contenuto"), amb)
        return amb

    a = mondo("una-chiave-segreta")
    blob = a["_cifra_contenuto"]("BUONO-1234")
    prova("si cifra con la ricetta nuova", True, blob.startswith("f2:"))
    prova("il codice non si legge nel blob", False, "BUONO-1234" in blob)
    prova("e si rilegge", "BUONO-1234", a["_decifra_contenuto"](blob))

    # il formato VECCHIO deve restare leggibile per sempre: un database
    # scritto ieri non puo' diventare illeggibile con un aggiornamento
    vecchio = "f:" + Fernet(base64.urlsafe_b64encode(
        hashlib.sha256(b"una-chiave-segreta").digest())).encrypt(
            b"CODICE-VECCHIO").decode()
    prova("il formato di ieri si rilegge ancora", "CODICE-VECCHIO",
          a["_decifra_contenuto"](vecchio))
    prova("e il 'plain:' di prima ancora", "in chiaro",
          a["_decifra_contenuto"]("plain:in chiaro"))

    # una chiave diversa non deve dare un'eccezione al chiamante, ma
    # una riga onesta (il venditore il codice ce l'ha comunque)
    altra = mondo("un'altra-chiave")
    prova("chiave sbagliata: una riga onesta, mai un'eccezione", True,
          altra["_decifra_contenuto"](blob).startswith("(contenuto cifrato"))

    # senza chiave si scrive in chiaro, ed e' dichiarato — ma dev'essere
    # DETTO all'avvio, che era la parte che mancava
    spenta = mondo("")
    prova("senza chiave si scrive in chiaro col suo prefisso", True,
          spenta["_cifra_contenuto"]("X").startswith("plain:"))
    prova("il fail-open non e' piu' muto: l'avvio lo dice", True,
          "if not CHIAVE_CONTENUTI_DIGITALI:" in _SORGENTE
          and "IN CHIARO" in _SORGENTE)
    # e le due ricette non devono dare la stessa chiave, o scrypt
    # sarebbe li' per niente
    prova("scrypt e sha256 danno chiavi diverse", True,
          a["_chiave_fernet"]("f2") != a["_chiave_fernet"]("f"))


def prove_ssrf_redirect():
    """Il guardiano anti-SSRF si aggirava con un 302 (ago 2026,
    audit): urllib segue i redirect da solo e `url_foto_ammesso`
    giudicava solo il PRIMO indirizzo, quindi un host pubblico che
    rispondeva «vai a 127.0.0.1» portava il server dentro la sua
    stessa rete. E l'import da Nostr non aveva guardie affatto — e
    gira DENTRO il server ogni ora."""
    print("\n[il redirect ricontrollato]")
    import ipaddress
    import urllib.error
    import urllib.request
    from urllib.parse import urlparse

    class _Dns:
        """Un DNS di cartone: nessuna prova deve dipendere da una
        risoluzione vera — la rete altrui non e' una prova."""
        FINTI = {"pubblico.tld": "93.184.216.34",
                 "interno.tld": "10.0.0.5"}

        @staticmethod
        def getaddrinfo(host, _porta):
            ip = _Dns.FINTI.get(host, host)
            ipaddress.ip_address(ip)      # un nome sconosciuto esplode qui
            return [(2, 1, 6, "", (ip, 0))]

    amb = {"urllib": urllib, "socket": _Dns, "ipaddress": ipaddress,
           "urlparse": urlparse, "print": lambda *a, **k: None}
    exec(pezzo("url_foto_ammesso"), amb)
    i = _SORGENTE.index("class _RedirectControllato")
    exec(_SORGENTE[i:_SORGENTE.index("def scarica_foto_import(", i)], amb)

    ammesso = amb["url_foto_ammesso"]
    prova("un host pubblico va bene", True, ammesso("http://pubblico.tld/a.jpg"))
    prova("un indirizzo privato no", False, ammesso("http://10.0.0.5/a.jpg"))
    prova("e nemmeno il loopback", False, ammesso("http://127.0.0.1/a.jpg"))

    # IL SALTO: e' qui che stava il buco, e si prova sul salto
    class _Testa(dict):
        def get_all(self, n, d=None):
            return d

    guardia = amb["_RedirectControllato"]()
    partenza = urllib.request.Request("http://pubblico.tld/foto.jpg")

    def salto(dove):
        try:
            r = guardia.redirect_request(partenza, None, 302, "Found",
                                         _Testa(), dove)
            return "seguito" if r is not None else "non seguito"
        except urllib.error.HTTPError:
            return "fermato"

    prova("il salto verso il loopback si ferma", "fermato",
          salto("http://127.0.0.1/segreto"))
    prova("il salto verso la rete interna si ferma", "fermato",
          salto("http://interno.tld/admin"))
    prova("il salto verso i metadati del cloud si ferma", "fermato",
          salto("http://169.254.169.254/latest/meta-data/"))
    prova("il salto verso file:// si ferma", "fermato",
          salto("file:///etc/passwd"))
    prova("un salto onesto si segue come sempre", "seguito",
          salto("http://pubblico.tld/altra.jpg"))

    # --- SENTINELLE -------------------------------------------------
    # Uno scaricatore solo: se ne ricompare un altro con urlopen nudo,
    # le guardie tornano a valere per meta' del progetto
    prova("sentinella: in server.py non c'e' piu' un urlopen nudo", True,
          "urllib.request.urlopen(" not in _SORGENTE)
    prova("sentinella: l'apritore controllato e' quello usato", True,
          "_APRITORE_FOTO.open(" in pezzo("scarica_foto_url"))
    prova("sentinella: il guardiano si chiama anche sulla partenza",
          True, "url_foto_ammesso(url)" in pezzo("scarica_foto_url"))
    # e l'import da Nostr lo riceve: il patto del `vaglio`
    prova("sentinella: l'import orario riceve lo scaricatore del server",
          True, "vaglio, scarica_foto_url)" in _SORGENTE)
    imp = open("importa_nostr.py", encoding="utf-8").read()
    prova("sentinella: e l'import lo usa quando ce l'ha", True,
          "def scarica_foto(url: str, annuncio_id: int, indice: int, "
          "scarica=None)" in imp and "esito = scarica(url)" in imp)


def prove_quota_ricerca():
    """Il freno della ricerca AI (ago 2026, audit). Era l'unica rotta
    dove UNA richiesta di un utente qualunque = UNA chiamata ad
    Anthropic, con un prompt di dimensione massima fissa: il credito
    si bruciava con un ciclo banale."""
    print("\n[la quota delle ricerche]")
    import time as _t

    def monta(tetto):
        amb = {"TETTO_RICERCHE_AI_ORA": tetto, "RICERCA_QUOTA": {},
               "time": _t}
        exec(pezzo("_ricerca_ai_concessa"), amb)
        return amb["_ricerca_ai_concessa"], amb["RICERCA_QUOTA"]

    concessa, quota = monta(3)
    prova("le prime tre passano", [True, True, True],
          [concessa(111) for _ in range(3)])
    prova("la quarta no", False, concessa(111))
    prova("...ma solo per lui", True, concessa(222))
    prova("il contatore e' per utente", 2, len(quota))

    concessa, _ = monta(0)
    prova("tetto a 0 = nessun freno", [True] * 50,
          [concessa(111) for _ in range(50)])

    # il gettone si consuma solo quando si passa: chi e' gia' oltre il
    # tetto non deve far crescere il contatore all'infinito
    concessa, quota = monta(2)
    for _ in range(10):
        concessa(111)
    prova("oltre il tetto il contatore si ferma", 2, quota[111][1])

    # --- SENTINELLE -------------------------------------------------
    c = pezzo("cerca")
    prova("sentinella: l'utente della ricerca non si butta via", True,
          "user = verifica_utente(" in c)
    prova("sentinella: il freno sta PRIMA di impaginare il catalogo",
          True, c.index("_ricerca_ai_concessa") < c.index("catalogo = "))
    prova("sentinella: la chiamata AI ha un timeout", True,
          "max_tokens=200, timeout=" in c)
    # a quota finita si risponde lo stesso: il filtro per parole non
    # costa niente, e un vicolo cieco non serve a nessuno
    prova("a quota finita si risponde col filtro per parole", True,
          "return risposta(filtro_semplice(), False)" in c)
    # e la forma vecchia resta per i client in cache
    prova("senza busta resta l'array di sempre", True,
          '{"annunci": righe, "ai": ai_usata} if busta else righe' in c)
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client regge tutte e due le forme", True,
          "Array.isArray(d) ? d : (d.annunci || [])" in mini)


def prove_initdata():
    """La freschezza dell'initData (ago 2026, audit). La firma dice
    CHI, non QUANDO: finche' nessuno guardava `auth_date`, un initData
    catturato apriva quell'account per sempre. Qui si firma per
    davvero, con un token di prova, e si guarda cosa passa e cosa no."""
    print("\n[freschezza dell'initData]")
    import hashlib
    import hmac
    import json
    import time
    from urllib.parse import parse_qsl, urlencode

    TOKEN = "123456:token-di-prova"

    def initdata(quando=None, token=TOKEN):
        """Un initData come lo firma Telegram. `quando=None` = senza
        auth_date: e' il caso che deve fallire da solo."""
        dati = {"query_id": "AAA", "user": '{"id":111,"first_name":"Ada"}'}
        if quando is not None:
            dati["auth_date"] = str(int(quando))
        controllo = "\n".join(f"{k}={v}" for k, v in sorted(dati.items()))
        chiave = hmac.new(b"WebAppData", token.encode(),
                          hashlib.sha256).digest()
        dati["hash"] = hmac.new(chiave, controllo.encode(),
                                hashlib.sha256).hexdigest()
        return urlencode(dati)

    class FintoErrore(Exception):
        def __init__(self, codice, testo=""):
            self.codice, self.testo = codice, testo

    class FintoDb:
        """Un database di cartone: qui non si prova la scrittura, si
        prova CHI ci arriva."""
        def __init__(self, visite):
            self.visite = visite

        def execute(self, *a):
            self.visite.append(a[0][:20])
            return self

        def fetchone(self):
            return None

        def commit(self):
            pass

        def close(self):
            pass

    def monta(ore, visite, in_sessione=None):
        amb = {"parse_qsl": parse_qsl, "hmac": hmac, "hashlib": hashlib,
               "json": json, "time": time, "BOT_TOKEN": TOKEN,
               "MODALITA_COLLAUDO": False, "ORE_INITDATA": ore,
               "MSG_INITDATA_SCADUTO": "scaduta",
               "HTTPException": FintoErrore,
               "db": lambda: FintoDb(visite),
               "nuovo_codice_negozio": lambda con: "abcd1234",
               "utente_da_sessione": lambda t: in_sessione}
        exec(pezzo("verifica_utente"), amb)
        return amb["verifica_utente"]

    def entra(init, ore=24, sessione="", in_sessione=None):
        """Torna l'id di chi entra, o il testo del rifiuto."""
        try:
            return monta(ore, [], in_sessione)(init, sessione)["id"]
        except FintoErrore as e:
            return e.testo

    ora = time.time()
    prova("initData appena firmato: si entra", 111, entra(initdata(ora)))
    prova("di un'ora: si entra", 111, entra(initdata(ora - 3600)))
    prova("di 23 ore e mezza: si entra ancora", 111,
          entra(initdata(ora - 23.5 * 3600)))
    prova("di 25 ore: rifiutato", "scaduta",
          entra(initdata(ora - 25 * 3600)))
    prova("di un anno: rifiutato", "scaduta",
          entra(initdata(ora - 365 * 86400)))
    # il rifiuto della scadenza DEVE essere distinguibile da quello
    # della firma storta, o il client non puo' dire «riaprimi»
    prova("firma storta: rifiutata, con l'ALTRO messaggio",
          "Autenticazione Telegram non valida",
          entra(initdata(ora, token="999:un-altro-token")))
    # fail-closed per costruzione, come importo_invoice: il campo che
    # manca vale 0, cioe' vecchio di un'era
    prova("auth_date assente: rifiutato senza un ramo apposta",
          "scaduta", entra(initdata(None)))
    prova("il rifiuto e' un 401", 401,
          _codice_rifiuto(monta(24, []), initdata(ora - 25 * 3600),
                          FintoErrore))
    # la leva spenta riapre esattamente il buco: e' dichiarato, e la
    # prova lo dice invece di lasciarlo credere
    prova("leva a 0: il vecchio ripassa (buco riaperto, dichiarato)",
          111, entra(initdata(ora - 365 * 86400), ore=0))
    # le altre due porte non sanno nulla di questa finestra
    prova("il cookie di sessione non passa di qui", 222,
          entra("", in_sessione={"id": 222}))

    # una credenziale scaduta non deve nemmeno TOCCARE il database
    visite = []
    try:
        monta(24, visite)(initdata(ora - 25 * 3600))
    except FintoErrore:
        pass
    prova("chi e' scaduto non scrive sul database", [], visite)

    # --- SENTINELLE: il controllo non deve sparire in un riordino ----
    vu = pezzo("verifica_utente")
    prova("sentinella: auth_date si legge davvero", True, "auth_date" in vu)
    # l'INSERT del ramo vero e' l'ULTIMO del pezzo (il primo e' quello
    # del collaudo): rindex, o si confronterebbe col ramo sbagliato
    prova("sentinella: si controlla PRIMA di scrivere sul database",
          True, vu.index("ORE_INITDATA") < vu.rindex("INSERT INTO utenti"))
    # dentro il try l'except si mangerebbe l'HTTPException e la
    # riscriverebbe col messaggio generico: il client perderebbe il
    # solo segnale che gli dice di riaprirsi
    prova("sentinella: il rifiuto della scadenza non e' inghiottito",
          True, vu.index("except Exception") < vu.index("ORE_INITDATA"))
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client distingue la scadenza dalla vetrina", True,
          "r.status === 401 && !!tg?.initData" in mini
          and "BANNER_SCADUTO" in mini)


def prove_foto():
    """La cartella foto/ non e' piu' montata (ago 2026, audit): era
    l'unica directory servita in blocco di tutto il progetto, contro
    la regola ferrea 3. Adesso c'e' una rotta con la whitelist delle
    FORME che i nostri scrittori producono — e le forme vanno tenute
    allineate a loro, o le foto vere spariscono dalla vetrina."""
    print("\n[le foto senza StaticFiles]")
    import re
    amb = {"re": re}
    i = _SORGENTE.index("NOME_FOTO = re.compile")
    exec(_SORGENTE[i:_SORGENTE.index("TIPI_FOTO =", i)], amb)
    ammesso = lambda n: bool(amb["NOME_FOTO"].match(n))

    # I nomi VERI, uno per scrittore
    for nome in ("a12_0.jpg", "a12_0_min.jpg",
                 "a12_0_1785852876.jpg", "a12_0_1785852876_min.jpg",
                 "a7_1.png", "a7_1.webp", "a7_1.gif", "a7_1_min.jpg",
                 "av_0236b74b_1784996031.jpg"):
        prova(f"si serve la foto vera {nome}", True, ammesso(nome))

    # e tutto cio' che in quella cartella non c'e' mai stato — piu'
    # (ago 2026) la gemella degli avatar, che c'era stata eccome: la
    # faceva genera_miniature_mancanti passando su ogni .jpg e non
    # solo sugli annunci, ed e' la forma che al primo giro era
    # sfuggita alla tabella degli scrittori. Adesso non se ne producono
    # piu' e i 75 di produzione sono stati tolti dal disco (613
    # rimasti), quindi il caso ha cambiato lato: da «si serve» a «non
    # si serve», che e' l'affermazione piu' forte delle due — se un
    # domani ne ricomparisse una, la rotta non la pubblicherebbe.
    for nome in ("../config.py", "..%2fconfig.py", "config.py",
                 "satmarket.db", "a1_0.jpg.exe", "", "a1_0.jpg\n",
                 "a1_0.jpg/../x", "av_../x_1.jpg", "a_0.jpg",
                 "av_f29bcbf7_1785852876_min.jpg"):
        prova(f"non si serve {nome!r}", False, ammesso(nome))

    # --- SENTINELLE ---------------------------------------------------
    # La regola ferrea 3 diventa verificabile invece che raccomandata:
    # non si guardano le parole (i commenti la nominano apposta), si
    # guarda il CODICE
    prova("sentinella: nessuna directory montata, in tutto il server",
          True, "app.mount(" not in _SORGENTE
          and "from fastapi.staticfiles import" not in _SORGENTE)
    # la formula dell'ETag e' UNA: due rotte che la calcolassero in
    # modo diverso manderebbero header divergenti, e il 304 delle
    # illustrazioni — che nacque da un caso vero — smetterebbe di
    # scattare senza che nessuno se ne accorga
    prova("sentinella: la formula dell'ETag vive in un posto solo", 1,
          _SORGENTE.count('f"{st.st_mtime}-{st.st_size}"'))
    prova("sentinella: le illustrazioni passano dallo stesso cuore",
          True, "_file_con_etag" in pezzo("asset_categoria"))
    # e la cache delle due resta quella di prima: revalidazione per le
    # illustrazioni (nomi non versionati), un giorno per le foto
    prova("le illustrazioni restano a revalidazione", True,
          '"public, no-cache"' in pezzo("asset_categoria"))
    prova("le foto restano a un giorno", True,
          '"public, max-age=86400"' in pezzo("foto_annuncio"))
    # la forma dell'avatar dice «esadecimale» perche' il codice negozio
    # lo fa token_hex: se un domani cambiasse alfabeto, TUTTE le facce
    # sparirebbero in silenzio (404) e nessuna prova funzionale se ne
    # accorgerebbe. Qui il legame e' scritto.
    prova("sentinella: il codice negozio e' ancora esadecimale", True,
          "secrets.token_hex(" in pezzo("nuovo_codice_negozio"))


def prove_avatar():
    """I francobolli degli avatar non vogliono una miniatura (ago 2026).
    _salva_avatar li scrive gia' a 128px e miniatura_jpeg non ingrandisce
    mai: la gemella usciva della STESSA misura, cioe' una copia — e per
    giunta una copia che nessuno chiede, visto che il nome _min lo deriva
    solo fotoMini per le foto degli annunci. 75 file inutili in
    produzione, uno in piu' a ogni cambio di foto profilo — tolti dal
    disco ad ago 2026 con ripulisci_avatar_min.py (613 file rimasti,
    avatar visibili): da li' la forma e' uscita anche da NOME_FOTO."""
    print("\n[gli avatar non fanno miniature]")
    import io
    import tempfile

    # --- la passata d'avvio, girata per davvero -----------------------
    try:
        from PIL import Image, ImageOps
    except ImportError:
        salta("la passata d'avvio salta i francobolli",
              "Pillow non e' installata")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            Image.new("RGB", (800, 600), (200, 120, 40)).save(
                os.path.join(tmp, "a1_0.jpg"))
            faccia = "av_0236b74b_1784996031.jpg"
            Image.new("RGB", (128, 128), (40, 120, 200)).save(
                os.path.join(tmp, faccia))
            amb = {"os": os, "io": io, "ImmaginePillow": Image,
                   "ImageOps": ImageOps, "FOTO_DIR": tmp,
                   # la riga di riepilogo qui non serve a nessuno: il
                   # print sta nelle globali, quindi lo trova prima dei
                   # builtin e la passata resta muta
                   "print": lambda *a, **k: None}
            i = _SORGENTE.index("MINIATURA_LATO = ")
            exec(_SORGENTE[i:_SORGENTE.index("\n\n\n", i)], amb)
            for f in ("miniatura_jpeg", "_miniatura_da_rifare",
                      "genera_miniature_mancanti"):
                exec(pezzo(f), amb)
            amb["genera_miniature_mancanti"]()
            c_e = lambda n: os.path.exists(os.path.join(tmp, n))
            prova("la foto dell'annuncio la miniatura ce l'ha ancora",
                  True, c_e("a1_0_min.jpg"))
            prova("il francobollo dell'avatar non ne riceve una",
                  False, c_e(faccia[:-4] + "_min.jpg"))

    # --- SENTINELLE ---------------------------------------------------
    prova("sentinella: la passata salta i nomi av_", True,
          'nome.startswith("av_")' in pezzo("genera_miniature_mancanti"))
    # cambiando foto profilo se ne va anche la gemella: senza, gli
    # orfani si riaccumulerebbero uno per cambio, che e' meta' del
    # guaio da cui e' nato questo cantiere
    prova("sentinella: col francobollo vecchio se ne va la sua _min",
          True, "_min.jpg" in pezzo("_scrivi_avatar"))

    # --- la spazzata resta ancorata alla forma del francobollo --------
    # Qui si confrontava lo script con NOME_FOTO sullo STESSO nome, ma
    # da quando la spazzata e' girata in produzione la rotta il _min
    # non lo serve piu' e le due DEVONO divergere. L'invariante giusta
    # e' di un passo di lato: lo script deve riconoscere la GEMELLA di
    # un francobollo che la rotta serve. Cosi' resta legato alla forma
    # di _salva_avatar — e quella, per la sentinella di prove_foto, a
    # secrets.token_hex: se l'alfabeto cambiasse lo si saprebbe qui,
    # invece che rilanciando lo script a vuoto.
    # (importarlo e' sicuro: il config lo chiede dentro main(), la
    # regola degli script puri)
    import ripulisci_avatar_min
    amb = {"re": re}
    i = _SORGENTE.index("NOME_FOTO = re.compile")
    exec(_SORGENTE[i:_SORGENTE.index("TIPI_FOTO =", i)], amb)
    for pieno in ("av_0236b74b_1784996031.jpg",
                  "av_f29bcbf7_1785852876.jpg",
                  "av_XYZ_1.jpg", "avatar.jpg"):
        prova(f"la spazzata riconosce la gemella di {pieno}",
              bool(amb["NOME_FOTO"].match(pieno)),
              bool(ripulisci_avatar_min.AVATAR_MIN.match(
                  pieno[:-4] + "_min.jpg")))
    # e non si tocca mai un pieno (e' la faccia di qualcuno) ne' le
    # miniature degli annunci, che invece servono
    for nome in ("av_0236b74b_1784996031.jpg", "a12_0_min.jpg"):
        prova(f"la spazzata lascia stare {nome}", False,
              bool(ripulisci_avatar_min.AVATAR_MIN.match(nome)))


def prove_tracking_corretto():
    """La correzione del tracciamento (ago 2026, caso vero dal campo:
    il codice dell'intermediario Packlink al posto di quello InPost).
    Tre cose che devono restare vere: la corregge SOLO un moderatore,
    NON tocca spedito_il ne' lo stato, e NON trasforma un ritiro (o
    una consegna a mano, o un codice online) in una spedizione."""
    print("\n[la correzione del tracciamento]")
    intero = pezzo("correggi_tracking")
    # il CODICE senza la prosa: la docstring parla di «stato='locked'»
    # e farebbe scattare da sola la sentinella qui sotto
    ct = intero.split('"""')[-1]

    # --- 1) e' roba da moderatore, e si controlla PRIMA di tutto ----
    prova("la correzione esige e_admin", True, "e_admin(user[" in ct)
    prova("il 403 arriva prima di leggere il body", True,
          ct.index("e_admin") < ct.index("leggi_json"))

    # --- 2) NON si tocca cio' che fa da ancora ai promemoria -------
    # spedito_il e' l'ancora di sollecita_conferme_ferme: riscriverla
    # farebbe ripartire da capo l'attesa del compratore a ogni
    # correzione (la trappola gia' pagata con `aggiornato` in
    # sollecita_venditori_fermi). Nemmeno lo stato si tocca: la
    # correzione e' un dato di servizio, non una transizione.
    for colonna in ("spedito_il=", "stato=", "aggiornato=", "consegnato="):
        prova(f"la UPDATE non scrive {colonna.rstrip('=')}",
              False, colonna in ct)
    # e scrive quel che deve
    prova("la UPDATE timbra tracking_corretto_il", True,
          "tracking_corretto_il=?" in ct)
    prova("il reso ha la sua colonna", True,
          "tracking_reso_corretto_il=?" in ct)

    # --- 3) i corrieri-sentinella non sono corrieri ----------------
    i = _SORGENTE.index("CORRIERI_SENTINELLA = (")
    amb = {}
    exec(_SORGENTE[i:_SORGENTE.index(")", i) + 1], amb)
    sent = amb["CORRIERI_SENTINELLA"]
    for nome in ("Consegna a mano", "Ritiro in zona", "Consegna digitale"):
        prova(f"«{nome}» e' una sentinella", True, nome in sent)
    prova("un corriere vero non lo e'", False, "InPost" in sent)
    # la guardia scatta nei DUE versi: sul corriere NUOVO (non si
    # trasforma una spedizione in un ritiro) e su quello VECCHIO (non
    # si da' un pacco a un ordine che non ne aveva)
    prova("si rifiuta la sentinella in arrivo", True,
          "corriere in CORRIERI_SENTINELLA" in ct)
    prova("si rifiuta la sentinella gia' scritta", True,
          "vecchio_c in CORRIERI_SENTINELLA" in ct)
    prova("ritiro e digitale restano fuori", True,
          '"ritiro", "digitale"' in ct or "'ritiro', 'digitale'" in ct)

    # --- 4) gli stati: dove un pacco viaggia davvero ----------------
    prova("la spedizione si corregge su shipped e delivered", True,
          '("shipped", "delivered")' in ct)
    prova("il reso sul suo stato", True, '("return_shipped",)' in ct)

    # --- 5) resta scritto: il registro e la traccia -----------------
    prova("la correzione finisce nel registro moderazione", True,
          "registra_moderazione(" in ct)
    prova("chi aspetta il pacco viene avvisato", True, "await notifica(" in ct)

    # --- 6) il moderatore puo' ARRIVARCI ---------------------------
    # un ordine 'shipped' fra estranei non compare in nessuna coda:
    # senza il parametro `ordine` di miei_ordini il pannello sarebbe
    # irraggiungibile (buco trovato provandolo dal vivo)
    mo = pezzo("miei_ordini")
    prova("il moderatore puo' aprire un ordine per numero", True,
          "OR o.id=?" in mo)
    prova("...ma solo lui", True,
          mo.index("e_admin(user") < mo.index("OR o.id=?"))


def prove_messaggio_admin():
    """Lo strumento «scrivi a un utente» dei moderatori (ago 2026,
    caso vero: la venditrice senza username ne' npub che nessuno
    poteva contattare). Quattro cose da tenere: e' roba da moderatore
    e il 403 arriva PRIMA di leggere il body; il testo si scappa (le
    notifiche parlano HTML); l'invio passa da notifica() — canale
    preferito, nativi Nostr compresi — mai dal bot diretto; e resta
    nel registro moderazione. Piu' la prevenzione nel client: la
    riga «nessuno puo' scriverti» in Vendi e nel cassetto Identita',
    con la STESSA regola dei ponti di contatto."""
    print("\n[messaggio ai singoli utenti]")
    ma = pezzo("messaggio_utente_admin")
    prova("l'invio esige e_admin", True, "e_admin(user[" in ma)
    prova("il 403 arriva prima di leggere il body", True,
          ma.index("e_admin") < ma.index("leggi_json"))
    prova("il testo del moderatore si scappa", True,
          "html.escape(testo)" in ma)
    prova("si passa da notifica(), mai dal bot diretto", True,
          "await notifica(" in ma)
    prova("...davvero mai", False, "_manda_telegram" in ma)
    prova("l'invio resta nel registro moderazione", True,
          "registra_moderazione(" in ma)
    prova("il destinatario deve esistere (404 sul fantasma)", True,
          "404" in ma)
    prova("il messaggio stesso dichiara il senso unico", True,
          "senso unico" in ma)

    mini = open("miniapp.html", encoding="utf-8").read()
    prova("l'interfaccia admin dichiara il senso unico", True,
          "se l'utente risponde al bot" in mini)
    prova("prima dell'invio si chiede conferma", True,
          "Invii questo messaggio a" in mini)
    # la prevenzione: chi non ha ne' username ne' npub dal possesso
    # dimostrato deve saperlo, in Vendi e nel cassetto Identita'
    prova("la riga di prevenzione esiste in Vendi", True,
          'id="sellContattoHint"' in mini)
    prova("...e nel cassetto Identita'", True,
          "Sei senza username" in mini)
    i = mini.index("const nonContattabile")
    blocco = mini[i:i + 300]
    prova("il giudice usa la regola dei ponti (username o npub "
          "dimostrata)", True,
          "myNpubAccesso || (myNpub && myNpubVerified)" in blocco)


def prove_avviso_contatto():
    """L'avviso una-tantum del venditore irraggiungibile (ago 2026):
    chi pubblica senza username Telegram ne' npub dal possesso
    dimostrato riceve UN messaggio dal bot, alla prima pubblicazione
    e mai piu'. La prova regina e' il timbro: due pubblicazioni = un
    messaggio solo."""
    print("\n[l'avviso del venditore irraggiungibile]")
    import asyncio
    import sqlite3

    def gira(coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def mondo(username="", npub="", verificata=0, accesso=""):
        vero = sqlite3.connect(":memory:")
        vero.row_factory = sqlite3.Row
        vero.execute("CREATE TABLE utenti(tg_id INT, username TEXT, "
                     "npub TEXT, npub_verificata INT, "
                     "npub_accesso TEXT, avvisato_contatto INT)")
        vero.execute("INSERT INTO utenti VALUES(?,?,?,?,?,0)",
                     (111, username, npub, verificata, accesso))
        vero.commit()

        class Con:
            """close() non chiude davvero: il :memory: deve
            sopravvivere fra una chiamata e l'altra."""
            def execute(self, *a):
                return vero.execute(*a)

            def commit(self):
                vero.commit()

            def close(self):
                pass

        mandati = []

        async def _notifica(tg, testo):
            mandati.append((tg, testo))

        amb = {"db": Con, "notifica": _notifica,
               "print": lambda *a, **k: None}
        exec("async " + pezzo("avvisa_contatto_mancante"), amb)
        return amb["avvisa_contatto_mancante"], vero, mandati

    # --- la prova del timbro --------------------------------------
    f, vero, mandati = mondo()
    gira(f(111))
    gira(f(111))
    prova("due pubblicazioni = un messaggio solo", 1, len(mandati))
    prova("il timbro resta scritto", 1, vero.execute(
        "SELECT avvisato_contatto FROM utenti").fetchone()[0])
    prova("il messaggio dice il rimedio", True,
          "username" in mandati[0][1])

    # --- chi e' raggiungibile non riceve niente -------------------
    for nome, m in (("con username", mondo(username="pia")),
                    ("con npub verificata",
                     mondo(npub="npub1x", verificata=1)),
                    ("nativo Nostr (npub d'accesso)",
                     mondo(accesso="npub1x"))):
        f, _, mandati = m
        gira(f(111))
        prova(f"{nome}: nessun avviso", 0, len(mandati))
    # ...e la npub NUDA (dichiarata, mai verificata) non basta: e'
    # la regola dei ponti — una dichiarazione non e' una porta
    f, _, mandati = mondo(npub="npub1x", verificata=0)
    gira(f(111))
    prova("npub nuda: l'avviso parte comunque", 1, len(mandati))

    # --- la forma: il patto del gemello spedizioniere -------------
    am = pezzo("avvisa_contatto_mancante")
    prova("il timbro si scrive PRIMA dell'invio", True,
          am.index("avvisato_contatto=1") < am.index("await notifica("))
    pb = pezzo("pubblica")
    prova("pubblica chiama l'avviso", True,
          "avvisa_contatto_mancante(" in pb)
    prova("...solo sul ramo attivo (dopo il return della revisione)",
          True, pb.index('"revisione": True')
          < pb.index("avvisa_contatto_mancante("))


def prove_barattolo():
    """Il tetto del barattolo (ago 2026: da 20 a 10) e il conteggio
    pubblico dei salvataggi."""
    print("\n[il barattolo]")
    # il tetto e' una leva col default 10, non piu' un 20 murato
    i = _SORGENTE.index("    from config import MAX_PREFERITI")
    coda = _SORGENTE[i:i + 200]
    prova("il tetto nasce a 10", True, "MAX_PREFERITI = 10" in coda)
    tp = pezzo("toggle_preferito")
    prova("il 400 del pieno dice il numero", True,
          "{MAX_PREFERITI}" in tp)
    prova("il tetto si legge senza await in mezzo", True,
          "_conta_barattolo(con, user[\"id\"]) >= MAX_PREFERITI" in tp)
    prova("la risposta porta il conteggio pubblico", True,
          '"barattoli": barattoli' in tp)

    # il conteggio pubblico e' ANONIMO: nessun tg_id esce mai
    cs = pezzo("_conta_savers")
    prova("il conteggio non seleziona nessun tg_id", True,
          "tg_id" not in cs.split('"""')[-1])
    arr = pezzo("arricchisci_righe_vetrina")
    prova("la vetrina conta i salvataggi con UNA query", True,
          'r["barattoli"] = salvati.get' in arr)
    prova("...e non fa nemmeno quella su una pagina vuota", True,
          "if tutti:" in arr)

    # i cinque livelli del vetro, che ora sono in PROPORZIONE al tetto
    # (con le vecchie soglie a mano e il tetto a 10 il livello 3 non
    # sarebbe esistito mai: pieno a 10, ma «<=10» lo fermava a 2).
    # La formula si LEGGE dal client e si esegue davvero: riscriverla
    # qui vorrebbe dire collaudare la copia invece dell'originale.
    src = open("miniapp.html", encoding="utf-8").read()
    i = src.index("const livelloBarattolo = n =>")
    corpo = src[i:src.index(";", src.index("Math.ceil", i))]
    corpo = " ".join(corpo.split("=>", 1)[1].split())   # su una riga sola
    # il ternario JS «a ? b : c» diventa quello di Python
    py = re.sub(r"([^?]+)\?([^:]+):(.+)", r"(\2) if (\1) else (\3)", corpo)
    while "?" in py:
        py = re.sub(r"([^?()]+)\?([^:]+):(.+)", r"((\2) if (\1) else (\3))", py)
    import math as _math

    class _M:
        min = staticmethod(min)
        max = staticmethod(max)
        ceil = staticmethod(lambda x: int(_math.ceil(x)))

    def livello(n, tetto):
        return eval(py.replace("MAX_PREFERITI", str(tetto)),
                    {"Math": _M}, {"n": n})

    for tetto in (10, 20, 6):
        visti = [livello(n, tetto) for n in range(0, tetto + 1)]
        prova(f"tetto {tetto}: vuoto a 0 e pieno al tetto",
              (0, 4), (visti[0], visti[-1]))
        prova(f"tetto {tetto}: tutti e cinque i livelli esistono",
              [0, 1, 2, 3, 4], sorted(set(visti)))
        prova(f"tetto {tetto}: il livello non scende mai",
              visti, sorted(visti))


def prove_ferie():
    """IL NEGOZIO IN FERIE (ago 2026): si guarda, non si compra.
    Le due cose che questa famiglia difende: il gate e' in LETTURA
    sulla data (quindi il rientro e' immediato e non aspetta nessun
    giro d'orologio), e NON SI CHIUDE CON IMPEGNI APERTI — coi set,
    che hanno annuncio_id=0, dentro l'elenco: e' la lezione del LEFT
    JOIN, gia' pagata due volte prima di questa."""
    print("\n[il negozio in ferie]")
    import sqlite3

    def corpo(nome):
        i = _SORGENTE.index(f"def {nome}(")
        return _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]

    def solo_codice(c):
        """Il corpo SENZA la docstring: qui si cercano CHIAMATE, e le
        docstring di questo cantiere nominano apposta le funzioni di
        cui spiegano il rapporto — cercarle nel testo intero da'
        verdetti a caso (successo due volte scrivendo queste prove)."""
        p = c.split('"""')
        return p[0] + "".join(p[2:]) if len(p) > 2 else c

    cfg = open("config_esempio.py", encoding="utf-8").read()
    # 1-3: le tre leve, gemelle server/config
    for riga in ("FERIE_ATTIVE = True", "FERIE_MAX_GIORNI = 90",
                 "FERIE_PREAVVISO_ORE = 24"):
        prova(f"leva gemella server/config: {riga}", True,
              riga in _SORGENTE and riga in cfg)

    # 4-7: il giudice PURO — al filo esatto il negozio e' APERTO,
    # come _asta_viva (e' la riga che decide il rientro immediato)
    amb = {}
    exec(pezzo("in_ferie"), amb)
    inf = amb["in_ferie"]
    prova("in ferie: data nel futuro", True, inf(2000, 1000))
    prova("aperto: data passata", False, inf(1000, 2000))
    prova("aperto: al filo esatto", False, inf(1000, 1000))
    prova("aperto: nessuna data (0 = mai partito)", False, inf(0, 1000))

    # 8: LA REGOLA DEL RIENTRO — il gate e' in lettura, quindi la
    # scopa NON e' cio' che riapre. Se un domani qualcuno spostasse
    # la decisione dentro scadenze_ferie, il rientro smetterebbe di
    # essere immediato e nessun altro test se ne accorgerebbe.
    sc = corpo("scadenze_ferie")
    prova("la scopa azzera soltanto, non decide chi e' aperto", True,
          "UPDATE utenti SET ferie_fino=0" in sc
          and "in_ferie(" not in solo_codice(sc))
    prova("...e rimette a zero il timbro del preavviso", True,
          "ferie_avvisato=0" in sc)

    # 9-11: il preavviso e' gemello della campagna spedizioniere —
    # TIMBRO PRIMA dell'invio (perdere un avviso di cortesia si puo',
    # raddoppiarlo no) e leva che lo spegne
    av = corpo("avvisa_rientro_ferie")
    prova("preavviso: il timbro si scrive prima della notifica", True,
          av.index("ferie_avvisato=1") < av.index("await notifica"))
    prova("preavviso: la leva a 0 lo spegne", True,
          "if FERIE_PREAVVISO_ORE <= 0:" in av)
    prova("preavviso: agganciato all'orologio", True,
          "avvisa_rientro_ferie()" in corpo("orologio")
          and "scadenze_ferie()" in corpo("orologio"))

    # 12-18: TUTTI i varchi dei compratori hanno la guardia
    for f in ("compra", "_compra_set", "preventivo_ordine",
              "_preventivo_set", "fai_offerta", "fai_puntata",
              "rispondi_offerta"):
        prova(f"guardia nei varchi: {f}", True,
              "guardia_ferie(" in corpo(f))
    # 19-21: e i tre del venditore, col messaggio suo
    for f in ("lancia_lampo", "pubblica", "rilancia_asta_deserta"):
        prova(f"guardia venditore: {f}", True,
              "guardia_ferie_venditore(" in corpo(f))

    # 22-23: LA GUARDIA STA PRIMA DELLA INVOICE, ed e' il punto: un
    # rifiuto dopo crea_invoice_escrow lascerebbe una fattura orfana
    for f in ("compra", "_compra_set"):
        c = corpo(f)
        prova(f"{f}: la guardia viene prima della invoice", True,
              c.index("guardia_ferie(") < c.index("crea_invoice_escrow"))

    # 24: chiudere il negozio non muove MAI sats (la regola cardinale)
    imp = corpo("imposta_ferie")
    prova("chiudere il negozio non muove sats, solo parole", True,
          not any(x in imp for x in
                  ("_sblocca_sats", "_rimborsa_compratore",
                   "_paga_rimborso", "paga_venditore", "released")))
    # 25: il rientro (fino=0) non ha guardie — riaprire non e' mai un
    # problema, e la lista degli impegni si guarda solo se si chiude
    impc = solo_codice(imp)
    prova("il rientro non passa dagli impegni aperti", True,
          "if fino:" in impc
          and impc.index("if fino:") < impc.index("_impegni_aperti("))

    # 26: IL LEFT JOIN, la lezione gia' pagata due volte
    ia = corpo("_impegni_aperti")
    prova("impegni: i set non spariscono (LEFT JOIN)", True,
          "LEFT JOIN annunci" in ia)

    # 27-34: gli impegni sul DB gemello in memoria — le sole tabelle
    # che servono, il modo di prove_asta
    amb2 = {"time": __import__("time"), "ORE_PAGAMENTO_OFFERTA": 24}
    i = _SORGENTE.index("MESI_IT = (")
    exec(_SORGENTE[i:_SORGENTE.index("\n\n\n", i)], amb2)
    exec(pezzo("_titolo_ordine"), amb2)
    exec(pezzo("data_ferie"), amb2)
    exec(pezzo("_impegni_aperti"), amb2)
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INT,
      venditore_id INT, stato TEXT, consegna_scelta TEXT, creato INT);
    CREATE TABLE ordine_righe(id INTEGER PRIMARY KEY, ordine_id INT,
      annuncio_id INT, quantita INT, titolo TEXT);
    CREATE TABLE annunci(id INTEGER PRIMARY KEY, venditore_id INT,
      titolo TEXT, stato TEXT, asta_base_sats INT DEFAULT 0,
      asta_scadenza INT DEFAULT 0, lampo_percento INT DEFAULT 0,
      lampo_scadenza INT DEFAULT 0);
    CREATE TABLE offerte(id INTEGER PRIMARY KEY, annuncio_id INT,
      venditore_id INT, stato TEXT, scadenza INT);
    """)
    import time as _t
    ora = int(_t.time())
    # un venditore pulito: niente lo trattiene
    prova("negozio libero: nessun impegno", [],
          amb2["_impegni_aperti"](con, 7))
    # 1) un ordine pagato e mai spedito
    con.execute("INSERT INTO annunci VALUES(1,7,'Bici',"
                "'attivo',0,0,0,0)")
    con.execute("INSERT INTO ordini VALUES(10,1,7,'locked',"
                "'spedizione',?)", (ora,))
    v = amb2["_impegni_aperti"](con, 7)
    prova("impegno: l'ordine locked trattiene, e dice cosa fare",
          True, len(v) == 1 and "#10" in v[0] and "spedizione" in v[0])
    # IL CASO SET: annuncio_id=0, il titolo arriva dalle righe
    con.execute("INSERT INTO ordini VALUES(11,0,7,'locked',"
                "'spedizione',?)", (ora,))
    con.execute("INSERT INTO ordine_righe VALUES(1,11,1,1,'Casco')")
    con.execute("INSERT INTO ordine_righe VALUES(2,11,1,1,'Guanti')")
    v = amb2["_impegni_aperti"](con, 7)
    prova("impegno: il SET non sparisce (annuncio_id=0)", True,
          len(v) == 2 and "#11" in v[1] and "Casco" in v[1])
    con.execute("DELETE FROM ordini")
    con.execute("DELETE FROM ordine_righe")
    # gli ordini gia' spediti NON trattengono (regola di Andrea)
    con.execute("INSERT INTO ordini VALUES(12,1,7,'shipped',"
                "'spedizione',?)", (ora,))
    prova("gli ordini gia' spediti seguono il loro corso", [],
          amb2["_impegni_aperti"](con, 7))
    # 2) un'asta viva
    con.execute("UPDATE annunci SET asta_base_sats=100, asta_scadenza=? "
                "WHERE id=1", (ora + 3600,))
    v = amb2["_impegni_aperti"](con, 7)
    prova("impegno: l'asta viva trattiene", True,
          len(v) == 1 and "asta" in v[0])
    con.execute("UPDATE annunci SET asta_scadenza=? WHERE id=1",
                (ora - 10,))
    prova("...l'asta gia' chiusa no", [],
          amb2["_impegni_aperti"](con, 7))
    con.execute("UPDATE annunci SET asta_base_sats=0 WHERE id=1")
    # 3) un accordo stretto
    con.execute("INSERT INTO offerte VALUES(20,1,7,'accettata',?)",
                (ora + 3600,))
    v = amb2["_impegni_aperti"](con, 7)
    prova("impegno: l'offerta accettata trattiene", True,
          len(v) == 1 and "accettata" in v[0])
    con.execute("UPDATE offerte SET stato='proposta' WHERE id=20")
    prova("...quella solo PROPOSTA no: quella decade da sola", [],
          amb2["_impegni_aperti"](con, 7))
    con.execute("DELETE FROM offerte")
    # 4) un pagamento in viaggio, e il suo gemello stantio
    con.execute("INSERT INTO ordini VALUES(13,1,7,'creato','',?)",
                (ora - 60,))
    v = amb2["_impegni_aperti"](con, 7)
    prova("impegno: il pagamento in corso trattiene", True,
          len(v) == 1 and "pagament" in v[0])
    con.execute("UPDATE ordini SET creato=? WHERE id=13", (ora - 3600,))
    prova("...ma non quello stantio oltre la mezz'ora", [],
          amb2["_impegni_aperti"](con, 7))
    con.execute("DELETE FROM ordini")
    # 5) una lampo in corso, con la sua via d'uscita
    con.execute("UPDATE annunci SET lampo_percento=20, lampo_scadenza=? "
                "WHERE id=1", (ora + 3600,))
    v = amb2["_impegni_aperti"](con, 7)
    prova("impegno: la lampo trattiene, e non si annulla da sola",
          True, len(v) == 1 and "annullala" in v[0])
    con.execute("UPDATE annunci SET lampo_scadenza=? WHERE id=1",
                (ora - 10,))
    prova("...la lampo scaduta no", [], amb2["_impegni_aperti"](con, 7))
    # e gli impegni di un ALTRO venditore non trattengono me
    con.execute("UPDATE annunci SET lampo_scadenza=? WHERE id=1",
                (ora + 3600,))
    prova("gli impegni sono per venditore", [],
          amb2["_impegni_aperti"](con, 999))
    con.close()

    # 35-37: la superficie pubblica e il gemello client
    prova("il campo esce dalla vetrina (JOIN gia' presente)", True,
          "u.ferie_fino AS venditore_ferie" in _SORGENTE)
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client legge il campo in mapListing", True,
          "ferie:a.venditore_ferie||0" in mini)
    prova("il client ha il suo giudice in lettura", True,
          "function inFerie(l){" in mini)

    # 38-40: IL GRIGIO DEL CARTELLINO E' FISSO, mai var(--muted): la
    # carta chiara non cambia di notte e il token sparirebbe sopra.
    i = mini.index(".tag-price.ferie .price{")
    prova("il cartellino usa un grigio fisso, non il token", True,
          "#8A8271" in mini[i:i + 60] and "--muted" not in mini[i:i + 60])
    # nel dettaglio invece il token e' quello giusto (sta sulla pagina)
    j = mini.index(".detail-price.ferie{")
    prova("il dettaglio segue il tema col token", True,
          "var(--muted)" in mini[j:j + 60])
    # e NESSUNA delle due nomina .unit (la regola dichiarata)
    prova("nessuna regola di stato ferie nomina .unit", True,
          ".unit" not in mini[i:i + 60] and ".unit" not in mini[j:j + 60])

    # 41: la barra d'acquisto non nasce a negozio chiuso
    prova("la barra d'acquisto tace in ferie", True,
          "&& !inFerie(l)" in mini)


def prove_bip353():
    """Perche' un Lightning address non ha risposto (ago 2026, dal
    caso vero di Phoenix). Un indirizzo BIP-353 e' scritto benissimo:
    parla via DNS invece che via LNURL, e il vecchio «controlla di
    averlo scritto giusto» mandava a caccia di un refuso inesistente.
    La cosa da NON rompere e' che i tre casi restino tre: dire «non
    hai sbagliato» a chi ha scritto «walletofsatosi.com» sarebbe la
    stessa bugia di prima, al contrario.
    Il DNS qui e' FINTO: una prova che interroga la rete vera diventa
    rossa quando un dominio altrui ha il raffreddore."""
    print("\n[l'indirizzo che non risponde]")

    class _SocketFinto:
        """Risolve solo i domini che gli diciamo noi."""
        VIVI = {"walletofsatoshi.com", "demo.lnbits.com",
                "phoenix.acinq.co"}

        def getaddrinfo(self, host, porta):
            if host not in self.VIVI:
                raise OSError("Name or service not known")
            return [(2, 1, 6, "", ("1.2.3.4", porta))]

    amb = {"socket": _SocketFinto()}
    i = _SORGENTE.index("DOMINI_BIP353 = ")
    exec(_SORGENTE[i:_SORGENTE.index(
        "\n\n\n", _SORGENTE.index("def diagnosi_ln_address"))], amb)
    diagnosi = amb["diagnosi_ln_address"]

    prova("Phoenix sul dominio DNS puro", "bip353",
          diagnosi("phoenixwallet.me"))
    # phoenix.acinq.co un server ce l'ha (e' il sito vetrina): senza
    # l'elenco finirebbe fra i «muti» e nessuno capirebbe perche'
    prova("Phoenix sul dominio col sito vetrina", "bip353",
          diagnosi("phoenix.acinq.co"))
    prova("un LNURL vero e' solo muto", "muto",
          diagnosi("walletofsatoshi.com"))
    prova("LNbits e' solo muto", "muto", diagnosi("demo.lnbits.com"))
    # IL CASO CHE CONTA: un refuso NON si dichiara BIP-353, o gli si
    # direbbe «non hai sbagliato a scriverlo» proprio mentre ha
    # sbagliato a scriverlo
    prova("un refuso resta un refuso", "inesistente",
          diagnosi("walletofsatosi.com"))

    # Il consiglio e' uno solo e lo dicono tutti e tre gli errori: se
    # si sfilacciasse, due utenti nello stesso guaio leggerebbero due
    # cose diverse
    i = _SORGENTE.index("CONSIGLIO_LNURL = (")
    consiglio = _SORGENTE[i:_SORGENTE.index(")\n", i)]
    prova("il consiglio nomina un wallet CONCRETO", True,
          "Wallet of Satoshi" in consiglio)
    prova("...e dice come si fa", True, "Receive" in consiglio)
    prova("...e lascia la via della invoice a mano", True,
          "invoice" in consiglio)
    prova("tutti e tre gli errori lo portano", 3,
          _SORGENTE.count("{CONSIGLIO_LNURL}"))


def prove_forma_tracking():
    """L'euristica sulla forma del codice (ago 2026): riconosce i
    formati tipici dei corrieri in elenco e — soprattutto — NON blocca
    mai. Si collauda sui casi veri, a partire da quello che ha aperto
    il cantiere: il codice Packlink al posto di quello InPost."""
    print("\n[la forma del tracciamento]")
    import json
    src = open("miniapp.html", encoding="utf-8").read()
    i = src.index("const FORME_TRACKING = {")
    blocco = src[i:src.index("\n};", i) + 3]
    # le regex di questo catalogo sono compatibili con Python: si
    # leggono dal client e si eseguono, invece di ricopiarle qui
    forme = {}
    for riga in re.finditer(r"'([^']+)':\s*\[(.+?)\],?\s*$", blocco, re.M):
        forme[riga.group(1)] = [re.compile(x)
                                for x in re.findall(r"/(.+?)/(?=,|\s*$)",
                                                    riga.group(2))]
    prova("il catalogo delle forme si e' letto tutto", 7, len(forme))

    def storto(corriere, codice):
        """True se la forma NON combacia (cioe' si chiede conferma)."""
        f = forme.get(corriere)
        if not f or not codice:
            return False
        nudo = re.sub(r"[\s-]", "", codice.upper())
        return not any(x.fullmatch(nudo) for x in f)

    # IL CASO VERO: Packlink dice IT2026COM…, InPost vuole 24 cifre
    prova("il codice dell'intermediario su InPost fa alzare la mano",
          True, storto("InPost", "IT2026COM8891"))
    prova("le 24 cifre di InPost passano",
          False, storto("InPost", "123456789012345678901234"))
    # gli altri corrieri, sui formati che si incontrano davvero
    buoni = [("Poste Italiane", "RR123456789IT"),
             ("Poste Italiane", "123456789012"),
             ("BRT", "0123456789012"),
             ("GLS", "123456789012"),
             ("SDA", "0123456789"),
             ("DHL", "1234567890"),
             ("DHL", "JJD0099887766554433"),
             ("UPS", "1Z999AA10123456784"),
             ("UPS", "123456789012")]
    for corriere, codice in buoni:
        prova(f"{corriere}: «{codice}» passa", False, storto(corriere, codice))
    # spazi e trattini incollati insieme al codice non contano
    prova("gli spazi incollati non contano", False,
          storto("InPost", "1234 5678 9012 3456 7890 1234"))
    prova("i trattini nemmeno", False, storto("UPS", "1Z-999AA1-0123456784"))
    # 'Altro corriere' e le sentinelle non hanno forma: mai una domanda
    for corriere in ("Altro corriere", "Consegna a mano", "Ritiro in zona"):
        prova(f"«{corriere}» non si controlla mai", False,
              storto(corriere, "qualunque-cosa"))
    prova("il campo vuoto non fa domande", False, storto("BRT", ""))

    # NON BLOCCA MAI, ed e' la parte che conta: il secondo tocco passa
    ft = src[src.index("function trackingDaControllare"):]
    ft = ft[:ft.index("\n}")]
    prova("il secondo tocco sullo stesso codice procede", True,
          "trackingForzato === tracking" in ft)
    prova("il forzato vale per QUEL codice, non per sempre", True,
          "trackingForzato = tracking" in ft)
    # e la prevenzione c'e' in tutti e due i moduli di spedizione
    prova("l'avviso sull'intermediario esiste", True,
          "AVVISO_INTERMEDIARIO" in src)
    prova("...ed e' nel form della spedizione e in quello del reso",
          2, src.count("${AVVISO_INTERMEDIARIO}"))


# ====================================================================
def prove_conto_acquisto():
    """Le pure del conto (ago 2026, pagina d'acquisto): compra(),
    _compra_set() e il preventivo dicono la stessa cifra perche'
    passano TUTTI da queste quattro funzioni. Qui si torturano da
    sole, senza server: e' il giudice unico che si prova, non i
    chiamanti."""
    print("\n[il conto d'acquisto]")
    amb = {}
    for f in ("_importo_accordo", "_prezzo_lampo", "_unitario_effettivo",
              "_eur_effettivo",
              "_tariffa_dichiarata", "_sped_in_sats", "_conto_ordine"):
        exec(pezzo(f), amb)

    def a(**kw):
        base = {"prezzo_sats": 100_000, "prezzo_eur": 0.0,
                "valuta": "sats", "lampo_percento": 0, "lampo_scadenza": 0,
                "spedizione_sats": 500, "spedizione_eur": 0.0,
                "spedizione_punto_sats": 0, "spedizione_punto_eur": 0.0,
                "spedizione_punto_dichiarata": 0}
        base.update(kw)
        return base

    unit = amb["_unitario_effettivo"]
    tarif = amb["_tariffa_dichiarata"]
    sped = amb["_sped_in_sats"]
    conto = amb["_conto_ordine"]

    # --- l'unitario: listino, EUR, lampo e accordo col MIN ----------
    prova("listino sats: l'unitario e' il listino", 100_000,
          unit(a(), None, 1000, 0.0))
    prova("listino EUR al cambio: round(eur/cambio*1e8)", 50_000,
          unit(a(valuta="eur", prezzo_eur=50.0), None, 1000, 100_000.0))
    prova("EUR minuscolo: mai sotto 1 sat", 1,
          unit(a(valuta="eur", prezzo_eur=0.0000004), None, 1000, 100_000.0))
    off = {"contro_sats": 0, "contro_eur": 0.0,
           "importo_sats": 90_000, "importo_eur": 0.0}
    prova("accordo accettato: vale la cifra pattuita", 90_000,
          unit(a(), off, 1000, 0.0))
    prova("lampo viva vs accordo: vince il MINIMO", 80_000,
          unit(a(lampo_percento=20, lampo_scadenza=2000), off, 1000, 0.0))
    prova("lampo scaduta: torna l'accordo", 90_000,
          unit(a(lampo_percento=20, lampo_scadenza=500), off, 1000, 0.0))

    # --- l'euro NATIVO (il dato del giudice del ≈): la cifra su cui
    # il ≈ NON va — esiste solo dove il prezzo e' NATO in euro -------
    eurn = amb["_eur_effettivo"]
    prova("listino sats: nessun euro nativo (0.0)", 0.0,
          eurn(a(), None, 1000))
    prova("listino EUR: l'euro nativo e' il listino", 50.0,
          eurn(a(valuta="eur", prezzo_eur=50.0), None, 1000))
    prova("lampo viva sull'EUR: il nativo e' lo scontato", 40.0,
          eurn(a(valuta="eur", prezzo_eur=50.0, lampo_percento=20,
                 lampo_scadenza=2000), None, 1000))
    off_eur = {"contro_sats": 0, "contro_eur": 45.0,
               "importo_sats": 0, "importo_eur": 48.0}
    prova("accordo EUR vs lampo: vince il MINIMO anche sul nativo",
          40.0, eurn(a(valuta="eur", prezzo_eur=50.0, lampo_percento=20,
                       lampo_scadenza=2000), off_eur, 1000))

    # --- la tariffa della via: il CUORE della retrocompat -----------
    prova("via casa: la tariffa di sempre", (500, 0.0),
          tarif(a(), "casa"))
    prova("via punto NON dichiarata: vale la tariffa casa", (500, 0.0),
          tarif(a(), "punto"))
    prova("via punto dichiarata: la sua tariffa", (300, 0.0),
          tarif(a(spedizione_punto_sats=300,
                  spedizione_punto_dichiarata=1), "punto"))
    # gratis dichiarato ≠ non dichiarato: (0,0) col flag acceso E'
    # gratis, senza flag sarebbe il fallback a 500
    prova("punto dichiarato a 0: GRATIS, non il fallback", (0, 0.0),
          tarif(a(spedizione_punto_dichiarata=1), "punto"))
    prova("punto ancorato all'euro: esce l'euro", (0, 4.5),
          tarif(a(spedizione_punto_eur=4.5,
                  spedizione_punto_dichiarata=1), "punto"))

    # --- la tariffa in sats: l'ancora e il cambio assente -----------
    prova("sats fissi: passano come sono", 500, sped(500, 0.0, 0.0))
    prova("euro ancorato al cambio: round(eur/cambio*1e8)", 4_500,
          sped(0, 4.5, 100_000.0))
    prova("euro ancorato SENZA cambio: None, decide il chiamante",
          None, sped(0, 4.5, 0.0))

    # --- le righe del conto -----------------------------------------
    prova("protezione col floor sul solo articolo", 0,
          conto(33, 500, 3, 0)["protezione"])
    prova("totale = articolo + spedizione + protezione", 100_500,
          conto(100_000, 500, 0, 0)["totale"])
    c = conto(100_000, 500, 5, 10)
    prova("protezione 5%: floor(5000)", 5_000, c["protezione"])
    prova("la commissione e' informativa: MAI nel totale",
          105_500, c["totale"])
    prova("...ma la riga la dice (10%)", 10_000, c["commissione"])

    # --- il MAX del set, per via ------------------------------------
    aa = [a(spedizione_sats=400),
          a(spedizione_sats=700, spedizione_punto_sats=200,
            spedizione_punto_dichiarata=1)]
    prova("set via casa: il MAX dei costi casa", 700,
          max(sped(*tarif(x, "casa"), 0.0) for x in aa))
    # il secondo annuncio al punto costa 200, il primo NON dichiara e
    # ripiega sulla sua casa (400): il MAX della via punto e' 400
    prova("set via punto: il MAX segue la via (col fallback)", 400,
          max(sped(*tarif(x, "punto"), 0.0) for x in aa))


# ====================================================================
def prove_sconto_pacco():
    """LO SCONTO CARRELLO (ago 2026): il venditore premia chi compra
    piu' cose — UNA regola per negozio, soglia di pezzi + percentuale,
    sul SOLO articolo e mai sulla spedizione. La matematica si tortura
    qui da sola, senza database e senza nodo: e' il posto dove un
    errore costa sats veri."""
    print("\n[lo sconto carrello]")
    amb = {}
    for f in ("_importo_accordo", "_prezzo_lampo", "_unitario_effettivo",
              "_sconto_pacco", "_sconto_pacco_eur", "_conto_ordine"):
        exec(pezzo(f), amb)
    sc, sceur = amb["_sconto_pacco"], amb["_sconto_pacco_eur"]
    conto, unit = amb["_conto_ordine"], amb["_unitario_effettivo"]

    # --- LA SOGLIA: e' una PORTA, non una scala ---------------------
    prova("soglia esatta: a 3 pezzi su 3 lo sconto SCATTA", 10_000,
          sc(100_000, 3, 3, 10))
    prova("soglia meno uno: a 2 pezzi non scatta niente", 0,
          sc(100_000, 2, 3, 10))
    prova("un pezzo solo: nemmeno l'ombra", 0, sc(100_000, 1, 3, 10))
    prova("ben oltre la soglia: lo sconto non cresce coi pezzi", 10_000,
          sc(100_000, 9, 3, 10))
    # se un domani qualcuno vorra' gli SCAGLIONI, dovra' rompere questa
    prova("...e' una percentuale sull'articolo, non un premio a pezzo",
          True, sc(100_000, 3, 3, 10) == sc(100_000, 30, 3, 10))
    prova("zero pezzi (payload storto): 0, non un negativo", 0,
          sc(100_000, 0, 3, 10))

    # --- LA REGOLA SPENTA: chi non la usa non paga niente ------------
    prova("percento 0: la regola e' spenta", 0, sc(100_000, 9, 3, 0))
    prova("soglia 0: la regola e' spenta", 0, sc(100_000, 9, 0, 10))
    prova("soglia 1 non e' uno sconto carrello: spenta", 0,
          sc(100_000, 9, 1, 10))
    prova("percento negativo (colonna sporca): spenta", 0,
          sc(100_000, 9, 3, -10))
    # LA REGRESSIONE CHE VALE MEZZO CANTIERE: col quinto argomento a 0
    # il conto e' quello di ieri, riga per riga
    prova("sconto spento: totale = articolo + spedizione + protezione",
          100_500, conto(100_000, 500, 0, 0, 0)["totale"])
    prova("sconto spento: protezione col floor sul solo articolo", 0,
          conto(33, 500, 3, 0, 0)["protezione"])
    c0 = conto(100_000, 500, 5, 10, 0)
    prova("sconto spento: protezione 5% = floor(5000)", 5_000,
          c0["protezione"])
    prova("sconto spento: la commissione resta fuori dal totale",
          105_500, c0["totale"])
    prova("sconto spento: e la riga la dice (10%)", 10_000,
          c0["commissione"])

    # --- GLI ARROTONDAMENTI: il resto va a CHI PAGA ------------------
    prova("999 a -10%: il resto va al COMPRATORE (100, non 99)", 100,
          sc(999, 3, 3, 10))
    prova("...e infatti l'articolo netto e' 899", 899, 999 - sc(999, 3, 3, 10))
    prova("1001 a -10%: 101, e non 100", 101, sc(1001, 3, 3, 10))
    prova("10 a -10%: un sat tondo", 1, sc(10, 3, 3, 10))
    prova("7 a -15%: 1,05 diventa 2 (la regola della lampo)", 2,
          sc(7, 3, 3, 15))
    prova("33% su 100.000: divisione esatta, nessun resto", 33_000,
          sc(100_000, 3, 3, 33))
    # IL LEGAME con la regola vecchia: se un domani qualcuno cambia il
    # verso dell'arrotondamento in UNO dei due posti, questa lo dice
    lampo = amb["_prezzo_lampo"]({"valuta": "sats", "prezzo_sats": 999,
                                  "prezzo_eur": 0.0}, 10)[0]
    prova("lo stesso arrotondamento della lampo, sullo stesso numero",
          lampo, 999 - sc(999, 3, 3, 10))

    # --- I LIMITI: lo sconto non mangia mai l'articolo ---------------
    prova("articolo da 1 sat: non si sconta", 0, sc(1, 5, 2, 10))
    prova("articolo da 2 sat a -90%: si scende a 1, mai a 0", 1,
          sc(2, 5, 2, 90))
    prova("percento 100: l'articolo non e' MAI gratis", 99,
          sc(100, 5, 2, 100))
    prova("percento assurdo (150) si tappa a 100", 99, sc(100, 5, 2, 150))
    prova("lo sconto non supera mai l'articolo", True,
          all(sc(x, 9, 2, 99) < x for x in (1, 2, 3, 10, 999, 100_000)))

    # --- IL CONTO: dove lo sconto entra e dove NON entra -------------
    c = conto(100_000, 500, 0, 0, 10_000)
    prova("il totale scende dello sconto", 90_500, c["totale"])
    prova("...e la spedizione non si muove di un sat", 500, c["spedizione"])
    prova("l'articolo LORDO resta in chiaro nel conto", 100_000,
          c["articolo"])
    prova("...e il netto e' quello che si paga", 90_000, c["netto"])
    prova("lo sconto non tocca MAI la spedizione, a nessun percento",
          500, conto(100_000, 500, 0, 0, 99_999)["spedizione"])
    cp = conto(100_000, 500, 5, 10, 10_000)
    prova("la protezione sta sull'articolo SCONTATO (4.500, non 5.000)",
          4_500, cp["protezione"])
    prova("...e il totale la segue", 95_000, cp["totale"])
    prova("la commissione resta informativa: MAI nel totale", 95_000,
          conto(100_000, 500, 5, 10, 10_000)["totale"])
    prova("...e anche lei guarda lo scontato", 9_000, cp["commissione"])
    # le cinture del chiamante distratto: _sconto_pacco non produce mai
    # questi valori, ma il conto non deve inventare denaro
    prova("sconto piu' grande dell'articolo: il totale non e' negativo",
          500, conto(100, 500, 0, 0, 1000)["totale"])
    prova("...e il netto si ferma a zero", 0,
          conto(100, 500, 0, 0, 1000)["netto"])
    prova("sconto negativo (chiamante distratto): non gonfia il totale",
          100_500, conto(100_000, 500, 0, 0, -50_000)["totale"])

    # --- L'INVARIANTE, come la legge un contabile -------------------
    righe = [(33_333, 2), (12_000, 1)]      # due annunci, TRE pezzi
    lordo = sum(u * q for u, q in righe)
    pezzi = sum(q for _, q in righe)
    s = sc(lordo, pezzi, 3, 10)
    ci = conto(lordo, 700, 5, 0, s)
    prova("l'articolo LORDO e' la somma di unitario x quantita", 78_666,
          lordo)
    prova("il conteggio e' di PEZZI, non di righe (3, non 2)", 3, pezzi)
    prova("lo sconto del carrello a tre pezzi", 7_867, s)
    prova("il netto e' il lordo meno lo sconto", 70_799, ci["netto"])
    prova("la protezione sull'imponibile (5% col floor)", 3_539,
          ci["protezione"])
    prova("IL TOTALE DELLA INVOICE", 75_038, ci["totale"])
    prova("invariante: lordo - sconto + spedizione + protezione = totale",
          ci["totale"],
          lordo - ci["sconto"] + ci["spedizione"] + ci["protezione"])
    cs = conto(lordo, 700, 5, 0, 0)
    prova("invariante: vale anche a sconto spento (gli ordini di ieri)",
          cs["totale"], lordo - 0 + cs["spedizione"] + cs["protezione"])
    prova("le righe restano LORDE: lo sconto non le sfiora", 78_666,
          sum(u * q for u, q in righe))

    # --- LA CASCATA con lampo e accordo (si CUMULA, deciso) ---------
    def a(**kw):
        base = {"prezzo_sats": 100_000, "prezzo_eur": 0.0,
                "valuta": "sats", "lampo_percento": 0, "lampo_scadenza": 0}
        base.update(kw)
        return base
    ul = unit(a(lampo_percento=20, lampo_scadenza=2000), None, 1000, 0.0)
    prova("lampo -20%: l'unitario e' 80.000", 80_000, ul)
    prova("...e sui tre pezzi il carrello sconta ancora (in cascata)",
          24_000, sc(ul * 3, 3, 3, 10))
    prova("...cioe' 216.000 invece di 300.000", 216_000,
          ul * 3 - sc(ul * 3, 3, 3, 10))
    # IL FONDO delle due leve al massimo, detto ad alta voce: chi
    # alzera' SCONTO_PACCO_MAX_PERCENTO trovera' questa riga rossa e
    # dovra' rifare il conto consapevolmente
    fondo = 30_000 - sc(30_000, 3, 3, 30)
    prova("lampo al 70% + carrello al 30%: il fondo e' il 21% del listino",
          21_000, fondo)
    prova("le leve hanno un default sano nel sorgente", True,
          "SCONTO_PACCO_MAX_PERCENTO = 30" in _SORGENTE
          and "SCONTO_PACCO_MIN_SOGLIA = 2" in _SORGENTE)

    # --- L'EURO NATIVO: si sconta in euro, non convertendo i sats ----
    prova("euro nativo: -10% su 100,00 fa 10,00", 10.0,
          sceur(100.0, 3, 3, 10))
    prova("listino in sats: nessuno sconto nativo (0.0)", 0.0,
          sceur(0.0, 3, 3, 10))
    prova("euro nativo sotto soglia: 0.0", 0.0, sceur(100.0, 2, 3, 10))
    prova("euro nativo: due decimali, mai di piu'", 10.0,
          sceur(99.99, 3, 3, 10))
    prova("euro minuscolo: il netto non scende sotto un centesimo", 0.01,
          sceur(0.02, 3, 2, 99))
    prova("i due gemelli scattano SEMPRE insieme", True,
          bool(sc(100_000, 3, 3, 10)) == bool(sceur(100.0, 3, 3, 10)))

    # --- IL MONO non sconta mai: la divisione a ritroso resta esatta -
    amb2 = {}
    exec(pezzo("_righe_ordine"), amb2)

    class _Fila:
        def __init__(self, d): self.d = d
        def __getitem__(self, k): return self.d[k]

    class _Con:                      # un database di cartone
        def execute(self, q, p):
            self.r = _Fila({"titolo": "Tazza"})
            return self
        def fetchone(self): return self.r

    o = {"annuncio_id": 7, "quantita": 3, "prezzo_sats": 90_500,
         "spedizione_sats": 500, "protezione_sats": 0}
    prova("mono: la divisione a ritroso resta esatta (30.000 a pezzo)",
          30_000, amb2["_righe_ordine"](_Con(), o)[0]["unitario_sats"])


# ====================================================================
def prove_consegna_payload_punto():
    """Il giudice unico dei campi di consegna, sul ramo nuovo: la
    dichiarazione della tariffa punto e' la PRESENZA di una chiave,
    mai il suo valore — vuoto ≠ zero."""
    print("\n[consegna_da_payload: la tariffa punto]")
    import asyncio

    def gira(coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    amb = {"MODALITA_CONSEGNA": ("spedizione", "ritiro", "entrambe",
                                 "digitale"),
           "TAGLIE_PACCO": ("busta", "piccolo", "medio", "grande",
                            "ingombrante")}

    async def _cambio():
        return 100_000.0
    amb["cambio_btc_eur"] = _cambio
    exec("async " + pezzo("consegna_da_payload"), amb)

    def giudica(d, valuta="sats"):
        (_, _, _, p_sats, p_eur, p_dich, _, _) = \
            gira(amb["consegna_da_payload"](d, valuta))
        return p_sats, p_eur, p_dich

    prova("chiavi assenti: NON dichiarata (i client di ieri)",
          (0, 0.0, 0), giudica({"consegna": "spedizione"}))
    prova("valore pieno: dichiarata", (300, 0.0, 1),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_sats": "300"}))
    prova("zero ESPLICITO: dichiarata gratis (vuoto ≠ zero)",
          (0, 0.0, 1),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_sats": 0}))
    prova("stringa vuota: come assente", (0, 0.0, 0),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_sats": ""}))
    prova("il flag esplicito del form (campo svuotato) NON dichiara",
          (0, 0.0, 0),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_dichiarata": 0}))
    prova("il flag esplicito acceso dichiara", (0, 0.0, 1),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_dichiarata": 1}))
    prova("col ritiro il punto si azzera, chiavi o no", (0, 0.0, 0),
          giudica({"consegna": "ritiro",
                   "spedizione_punto_sats": "300"}))
    prova("listino EUR: euro + equivalente al cambio", (4_500, 4.5, 1),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_eur": "4.5"}, "eur"))
    prova("listino sats, punto in euro: resta ANCORATO", (0, 4.5, 1),
          giudica({"consegna": "spedizione",
                   "spedizione_punto_eur": "4.5"}))
    # la simmetria con la tariffa casa: stesso aiutante, stessi numeri
    def entrambe(d, valuta="sats"):
        (_, s_sats, s_eur, p_sats, p_eur, _, _, _) = \
            gira(amb["consegna_da_payload"](d, valuta))
        return (s_sats, s_eur) == (p_sats, p_eur)
    prova("stessa cifra nei due campi = stessa lettura", True,
          entrambe({"consegna": "spedizione", "spedizione_sats": "250",
                    "spedizione_punto_sats": "250"}))


# ====================================================================
def prove_pagina_acquisto():
    """Le sentinelle di FORMA del cantiere: righe che un riordino
    farebbe sparire senza rompere nessuna prova funzionale."""
    print("\n[pagina d'acquisto: le sentinelle]")
    src = _SORGENTE

    # 1. Il preventivo non crea NULLA: niente INSERT, niente invoice.
    #    (la docstring si toglie, o le sue parole farebbero scattare
    #    le sentinelle da sole — il trucco di prove_tracking_corretto)
    for nome in ("preventivo_ordine", "_preventivo_set",
                 "_strade_preventivo"):
        corpo = pezzo(nome).split('"""')[-1]
        prova(f"{nome}: nessun INSERT", False, "INSERT" in corpo)
        prova(f"{nome}: nessuna invoice coniata", False,
              "crea_invoice" in corpo)
        prova(f"{nome}: nessun UPDATE", False, "UPDATE" in corpo)

    # 2. Il patto del ricontrollo, ora difeso in CI: tra la invoice e
    #    l'INSERT dell'ordine NESSUN await, nei due compratori.
    inizio = 0
    for chi in ("_compra_set", "compra"):
        i = src.index("crea_invoice_escrow(", src.index(f"def {chi}("))
        j = src.index("INSERT INTO ordini", i)
        prova(f"{chi}: zero await tra invoice e INSERT", False,
              "await " in src[i:j])

    # 3. Il punto NON esce su Nostr (tariffa interna del checkout,
    #    imperfezione dichiarata): ne' il costo ne' il testo.
    for nome in ("tag_commercio", "evento_annuncio"):
        corpo = pezzo(nome)
        prova(f"{nome}: cieco alla tariffa punto", False,
              "spedizione_punto" in corpo)
        prova(f"{nome}: cieco al punto dell'ordine", False,
              "punto_ritiro" in corpo)

    # 4. spedizione_via passa da una whitelist esplicita, nei due rami
    corpo_compra = src[src.index("async def compra("):
                       src.index("def crea_ordine_pagato(")]
    prova("compra: whitelist ('casa', 'punto')", True,
          '("casa", "punto")' in corpo_compra)
    corpo_set = src[src.index("async def _compra_set("):
                    src.index("RIPRESA_INVOICE_S")]
    prova("_compra_set: whitelist ('casa', 'punto')", True,
          '("casa", "punto")' in corpo_set)

    # 5. L'asta resta fuori perimetro: il varco del vincitore non sa
    #    niente di punti di ritiro
    corpo = pezzo("scegli_consegna_ordine").split('"""')[-1]
    prova("scegli_consegna_ordine: niente punto", False,
          "punto" in corpo)

    # 5bis. LA REGOLA ROVESCIATA (secondo giro, decisione di Andrea):
    #    la via punto si offre SEMPRE dove c'e' la spedizione — il
    #    gate sullo spedizioniere e' durato un giro e non deve
    #    tornare di soppiatto (meglio l'accordo in chat che la porta
    #    chiusa). Ne' il 400 di ieri, ne' un filtro nel preventivo.
    prova("il 400 «non spedisce ai punti» non esiste piu'", False,
          "non spedisce ai punti" in src)
    prova("_strade_preventivo non filtra piu' sullo spedizioniere",
          False, "not spedizioniere" in pezzo("_strade_preventivo"))

    # 5ter. IL TERZO GIRO (decisione di Andrea che supera il secondo):
    #    il punto si fissa quando il corriere e' NOTO. Al pagamento e'
    #    obbligatorio SOLO con la rete dichiarata (nei due compratori);
    #    senza, si sceglie la strada (via_punto) e il punto arriva dal
    #    campo dell'ordine — e il venditore non puo' segnare «spedito»
    #    finche' il punto non c'e' (dove spedirebbe?).
    prova("punto obbligatorio al pagamento SOLO con la rete (x2)", 2,
          src.count('if sp and sp["spedizioniere"] and not punto:'))
    corpo_sped = pezzo("segna_spedito").split('"""')[-1]
    prova("segna_spedito: bloccato sulla via punto senza punto", True,
          'o["via_punto"] and not o["punto_ritiro"]' in corpo_sped)
    corpo_pr = pezzo("indica_punto_ritiro").split('"""')[-1]
    prova("il campo dell'ordine e' del COMPRATORE, su 'locked'", True,
          "compratore_id" in corpo_pr and "'locked'" in corpo_pr)
    prova("...esige la via punto", True, 'o["via_punto"]' in corpo_pr)
    prova("...e la notifica al venditore e' STATICA (mai il testo)",
          False, "{punto" in corpo_pr)
    mini3 = open("miniapp.html", encoding="utf-8").read()
    prova("client: il campo al pagamento esiste solo con la rete",
          True, "const campoPunto = !p.spedizioniere ? ''" in mini3)
    prova("client: la riga «lo indicherai dopo l'acquisto» esiste",
          True, "lo indicherai dopo l'acquisto" in mini3)
    prova("client: il campo dentro l'ordine esiste", True,
          "salvaPuntoRitiro" in mini3 and "puntoRitiroInp" in mini3)

    # 6. La modifica firmata non tocca MAI le colonne punto (l'evento
    #    Nostr non le porta: le azzererebbe a ogni sync). L'unico
    #    UPDATE che le scrive e' quello di modifica().
    prova("spedizione_punto_sats=? vive in UN solo UPDATE", 1,
          src.count("spedizione_punto_sats=?"))

    # 6bis. La notifica una-tantum dello spedizioniere: il timbro si
    #    scrive PRIMA degli invii (il patto del cooldown della lampo:
    #    un errore di rete perde un avviso di cortesia, mai lo
    #    raddoppia) e la WHERE lo rispetta.
    camp = pezzo("avvisa_spedizioniere_mancante").split('"""')[-1]
    prova("campagna: la WHERE guarda il timbro", True,
          "avvisato_spedizioniere=0" in camp)
    prova("campagna: il timbro si scrive prima degli invii", True,
          camp.index("avvisato_spedizioniere=1")
          < camp.index("await notifica"))

    # 7. Il modello CSV: la colonna nuova sta IN CODA (i file di ieri
    #    passano intonsi, le colonne si leggono per nome)
    i = src.index("MODELLO_IMPORT = (")
    intest = src[i:src.index("\\n", i)]
    prova("il modello CSV chiude con spedizione_punto", True,
          intest.rstrip().endswith("spedizione_punto"))

    # --- il client ---------------------------------------------------
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il foglio del varco non esiste piu'", False,
          "function apriFoglioConsegna" in mini)
    prova("...e nemmeno la sua scelta", False,
          "function scegliConsegnaFoglio" in mini)
    prova("consegnaEsplicita non si scrive piu'", False,
          "consegnaEsplicita =" in mini)
    # l'ordine nasce solo dai varchi noti: startBuy, startBuySet e
    # confermaCompraSubito — piu' i due lettori del preventivo
    prova("tre POST /orders (i varchi di sempre)", 3,
          mini.count("fetch(`${API_BASE}/orders`"))
    prova("due lettori del preventivo (pagina e pacco)", 2,
          mini.count("fetch(`${API_BASE}/orders/preventivo`"))
    prova("la vista nuova esiste", True, 'id="view-acquisto"' in mini)
    prova("il varco-mappa e' dichiarato dove andra' la mappa", True,
          "VARCO MAPPA" in mini)
    prova("il punto passa da esc() alla resa", True,
          "esc(o.puntoRitiro)" in mini)
    # (CORRIERI del tracking resta legittimamente nel client: qui si
    # guarda che il catalogo SPEDIZIONIERI arrivi dal server)
    prova("il bottone finale della pagina dice «Paga»", True,
          'id="acqCompra" onclick="ctaAcquisto()">Paga<' in mini)
    # IL GIUDICE DEL ≈ (bug dal telefono: ≈ su ENTRAMBE le valute).
    # La regola vive in UNA funzione: il ≈ solo sulla valuta
    # convertita — l'euro nativo dal server la spegne in vista €, e
    # la resa convertita esiste UNA volta sola, dentro il giudice.
    prova("il giudice del ≈ e' UNO (cifraCtrl)", 1,
          mini.count("function cifraCtrl"))
    prova("...e conosce l'euro nativo", True,
          "if (eurNativo > 0)" in mini)
    prova("...e la conversione eur vive solo li' dentro", 1,
          mini.count("fmtEur(sats * eurPerSat)"))
    prova("il server dice l'euro nativo delle strade", True,
          "totale_eur" in pezzo("_strade_preventivo"))
    prova("...e dell'articolo", True,
          "articolo_eur" in pezzo("preventivo_ordine"))
    prova("il catalogo spedizionieri arriva da /api/me", True,
          "me.spedizionieri" in mini)
    prova("...e il client non lo riempie mai da solo", 1,
          mini.count("spedizionieriCatalogo = ["))


# ====================================================================
def prove_libro_mastro():
    """LA RONDA DEL LIBRO MASTRO (ago 2026): i controlli di integrita'
    che l'orologio gira una volta al giorno. Si provano DAVVERO — su
    un database gemello in memoria, ermetico: niente file, niente
    config — perche' una query sbagliata qui non fallisce, TACE, ed e'
    il peggior modo di fallire per un allarme.
    Due giri: schema sano → nessuno deve trovare niente; poi una riga
    rotta per ogni controllo → quel controllo, e solo quello, la
    trova, col suo id."""
    print("\n[la ronda del libro mastro]")
    import sqlite3
    src = open("server.py", encoding="utf-8").read()
    amb = {}
    i = src.index("CONTROLLI_LIBRO_MASTRO = (")
    exec(src[i:src.index("\n_ultimo_libro_mastro", i)], amb)
    controlli = amb["CONTROLLI_LIBRO_MASTRO"]

    # --- la FORMA del catalogo --------------------------------------
    prova("il catalogo non e' vuoto", True, len(controlli) >= 10)
    prova("ogni voce e' (nome, perche', sql)", True,
          all(len(c) == 3 and all(isinstance(x, str) for x in c)
              for c in controlli))
    prova("i nomi sono unici", len(controlli),
          len({c[0] for c in controlli}))
    # SOLA LETTURA: e' la regola del cantiere, e sparirebbe in
    # silenzio se qualcuno «riparasse» al volo una riga storta
    for nome, _, sql in controlli:
        for vietato in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
                        "REPLACE", "PRAGMA"):
            prova(f"«{nome}»: nessun {vietato} (legge e basta)", False,
                  vietato in sql.upper())
        prova(f"«{nome}»: e' una SELECT", True,
              sql.lstrip().upper().startswith("SELECT"))

    # --- lo schema gemello: solo le colonne che i controlli toccano --
    def db_sano():
        con = sqlite3.connect(":memory:")
        con.executescript("""
        CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INT,
          prezzo_sats INT, sconto_sats INT DEFAULT 0,
          sconto_percento INT DEFAULT 0, spedizione_sats INT DEFAULT 0,
          protezione_sats INT DEFAULT 0, quantita INT DEFAULT 1,
          stato TEXT DEFAULT 'locked', payout_stato TEXT DEFAULT '',
          aggiornato INT DEFAULT 0);
        CREATE TABLE ordine_righe(id INTEGER PRIMARY KEY, ordine_id INT,
          annuncio_id INT, quantita INT, unitario_sats INT,
          titolo TEXT DEFAULT '');
        CREATE TABLE puntate(id INTEGER PRIMARY KEY, annuncio_id INT,
          tg_id INT, offerto_sats INT, versato_sats INT, proxy INT
          DEFAULT 0, stato TEXT);
        CREATE TABLE rilanci(id INTEGER PRIMARY KEY, annuncio_id INT,
          delta_sats INT, stato TEXT);
        CREATE TABLE rimborsi_asta(id INTEGER PRIMARY KEY,
          annuncio_id INT, puntata_id INT, rilancio_id INT DEFAULT 0,
          importo_sats INT, motivo TEXT, payout_stato TEXT DEFAULT '');
        CREATE TABLE annunci(id INTEGER PRIMARY KEY, venditore_id INT,
          stato TEXT, contatto_nostr TEXT DEFAULT '',
          nostr_event_id TEXT DEFAULT '');
        CREATE UNIQUE INDEX idx_rimborso_chiusura ON rimborsi_asta(puntata_id)
          WHERE motivo IN ('perdente','annullo_admin');
        CREATE UNIQUE INDEX idx_rimborso_tardivo ON rimborsi_asta(rilancio_id)
          WHERE rilancio_id > 0;
        CREATE UNIQUE INDEX idx_rimborso_ecc_ritiro ON rimborsi_asta(puntata_id)
          WHERE motivo = 'eccedenza_ritiro';
        CREATE UNIQUE INDEX idx_rimborso_eccedenza ON rimborsi_asta(puntata_id)
          WHERE motivo = 'eccedenza';
        -- UN CARRELLO SANO: 3 pezzi, lordo 32.000, sconto 3.200,
        -- spedizione 500 -> 29.300
        INSERT INTO ordini(id,annuncio_id,prezzo_sats,sconto_sats,
          sconto_percento,spedizione_sats,quantita)
          VALUES(1, 0, 29300, 3200, 10, 500, 3);
        INSERT INTO ordine_righe(ordine_id,annuncio_id,quantita,unitario_sats)
          VALUES(1, 7, 2, 10000), (1, 8, 1, 12000);
        -- UN MONO SANO: nessuna riga, nessuno sconto
        INSERT INTO ordini(id,annuncio_id,prezzo_sats,quantita)
          VALUES(2, 9, 50000, 5);
        -- UN'ASTA CHIUSA SANA: entrati 140, vincitrice espone 100,
        -- registro 40 (un perdente rimborsato + l'eccedenza)
        INSERT INTO puntate(id,annuncio_id,tg_id,offerto_sats,versato_sats,stato)
          VALUES(1, 5, 111, 100, 120, 'vincitrice'),
                (2, 5, 222, 20, 20, 'chiusa');
        INSERT INTO rilanci(annuncio_id,delta_sats,stato)
          VALUES(5, 120, 'saldato'), (5, 20, 'saldato'),
                (5, 999, 'creato');      -- mai saldato: non conta
        INSERT INTO rimborsi_asta(annuncio_id,puntata_id,importo_sats,motivo)
          VALUES(5, 2, 20, 'perdente'), (5, 1, 20, 'eccedenza');
        INSERT INTO annunci(id,venditore_id,stato,contatto_nostr)
          VALUES(7, 222, 'attivo', 'npub1xxx');
        INSERT INTO annunci(id,venditore_id,stato,nostr_event_id)
          VALUES(8, 222, 'attivo', 'evento123');
        """)
        return con

    def gira(con):
        """{nome: [id trovati]} dei soli controlli che hanno trovato
        qualcosa — cioe' esattamente cio' su cui l'orologio suona."""
        fuori = {}
        for nome, _, sql in controlli:
            ids = [str(r[0]) for r in con.execute(sql).fetchall()]
            if ids:
                fuori[nome] = ids
        return fuori

    # --- GIRO 1: tutto sano, nessuno deve fiatare -------------------
    con = db_sano()
    trovati = gira(con)
    prova("database sano: NESSUN controllo trova niente (silenzio)",
          {}, trovati)
    con.close()

    # --- GIRO 2: una riga rotta alla volta --------------------------
    # (sql da eseguire, nome del controllo che DEVE svegliarsi, id atteso)
    casi = [
        ("UPDATE ordini SET prezzo_sats=29299 WHERE id=1",
         "aritmetica della testata", "1"),
        ("UPDATE ordini SET sconto_sats=500, sconto_percento=10 WHERE id=2",
         "mono scontato", "2"),
        ("UPDATE ordini SET sconto_sats=99999 WHERE id=1",
         "sconto fuori scala", "1"),
        ("UPDATE ordini SET sconto_percento=0 WHERE id=1",
         "sconto e percentuale scordati", "1"),
        ("UPDATE ordini SET quantita=4 WHERE id=1",
         "pezzi della testata", "1"),
        ("INSERT INTO ordine_righe(ordine_id,annuncio_id,quantita,"
         "unitario_sats) VALUES(2, 9, 1, 50000)",
         "mono con righe", "2"),
        ("INSERT INTO ordine_righe(id,ordine_id,annuncio_id,quantita,"
         "unitario_sats) VALUES(77, 4242, 9, 1, 100)",
         "righe orfane", "77"),
        ("INSERT INTO ordini(id,annuncio_id,prezzo_sats,quantita) "
         "VALUES(3, 0, 1000, 1)",
         "carrello senza merce", "3"),
        ("UPDATE puntate SET offerto_sats=101 WHERE id=1",
         "cassa dell'asta chiusa", "5"),
        ("DELETE FROM rimborsi_asta WHERE puntata_id=2",
         "puntata chiusa senza rimborso", "2"),
        ("UPDATE puntate SET versato_sats=50 WHERE id=1",
         "esposto senza copertura", "1"),
        ("INSERT INTO rimborsi_asta(annuncio_id,puntata_id,importo_sats,"
         "motivo) VALUES(5, 2, 20, 'ritiro'), (5, 2, 20, 'ritiro')",
         "doppio rimborso da ritiro", "2"),
        ("DROP INDEX idx_rimborso_eccedenza",
         "cinture d'idempotenza cadute", "idx_rimborso_eccedenza"),
        ("UPDATE annunci SET nostr_event_id='ev999' WHERE id=7",
         "annuncio a due teste", "7"),
        ("UPDATE ordini SET payout_stato='boh' WHERE id=1",
         "payout fuori contratto", "1"),
    ]
    for sql, atteso, id_atteso in casi:
        con = db_sano()
        con.executescript(sql)
        trovati = gira(con)
        con.close()
        prova(f"rotto «{atteso}»: il controllo lo trova", True,
              atteso in trovati)
        prova(f"...con l'id giusto ({id_atteso})", True,
              id_atteso in trovati.get(atteso, []))
    prova("ogni controllo del catalogo ha il suo caso rotto",
          {c[0] for c in controlli}, {c[1] for c in casi})

    # --- il patto della RONDA: silenzio, timbro, sola lettura -------
    corpo = pezzo("controlla_libro_mastro")
    prova("a libro mastro sano esce senza dire niente", True,
          "if not rotti:" in corpo and "return" in corpo)
    prova("il timbro e' il GIORNO e si scrive PRIMA delle query", True,
          corpo.index("_ultimo_libro_mastro = oggi")
          < corpo.index("for nome, perche, sql"))
    prova("la leva puo' spegnerla", True,
          "if not CONTROLLO_LIBRO_MASTRO:" in corpo)
    prova("una query che esplode conta come guasto", True,
          "la query non gira" in corpo)
    prova("non corregge NULLA", False,
          any(v in corpo.split('"""')[-1].upper()
              for v in ("UPDATE ", "INSERT ", "DELETE ")))
    prova("il titolo dell'allarme e' il 🧊 dei moderatori", True,
          "🧊" in corpo and "notifica_admin(" in corpo)
    prova("gli id passano da html.escape (le notifiche sono HTML)",
          True, "html.escape(elenco)" in corpo)
    # lo strumento a mano resta nel repo, e l'allarme lo nomina
    import os
    prova("il file delle query a mano esiste", True,
          os.path.exists("query_libro_mastro.sql"))
    prova("...e l'avviso dice come lanciarlo", True,
          "query_libro_mastro.sql" in corpo)


# ====================================================================
def prove_forma_sconto_pacco():
    """Le righe che un riordino farebbe sparire senza rompere nessuna
    prova funzionale — e che sono tutto cio' che tiene lo sconto
    carrello dove deve stare: fuori dal mono, fuori dal payload del
    compratore, e fuori da ogni strada del denaro in USCITA."""
    print("\n[lo sconto carrello: la forma]")
    src = open("server.py", encoding="utf-8").read()

    # 1) UN giudice solo, e due chiamanti soli (i due rami SET): il
    # preventivo e la invoice devono dire la stessa cifra per
    # costruzione, non per disciplina.
    prova("lo sconto ha UN giudice solo", 1, src.count("def _sconto_pacco("))
    # (si contano le CHIAMATE, non le occorrenze del nome: l'endpoint
    # si chiama imposta_sconto_pacco e finirebbe nel conto)
    prova("...e due chiamanti soli (compra set, preventivo set)", 2,
          src.count("= _sconto_pacco("))
    prova("il gemello in euro e' UNO", 1,
          src.count("def _sconto_pacco_eur("))
    prova("la regola si legge da UN lettore solo", 1,
          src.count("def _regola_sconto("))

    # 2) Le pure restano PURE: e' il patto scritto nel commento del
    # blocco, e senza sentinella la prima SELECT infilata li' dentro fa
    # esplodere la suite (e qualcuno la commenterebbe).
    for nome in ("_sconto_pacco", "_sconto_pacco_eur"):
        corpo = pezzo(nome).split('"""')[-1]
        for vietato in ("INSERT", "UPDATE", "SELECT", "await", "con.",
                        "SCONTO_PACCO"):
            prova(f"{nome}: niente {vietato} (e' una pura)", False,
                  vietato in corpo)

    # 3) LO SCONTO NON ARRIVA MAI DAL COMPRATORE. E' la sentinella di
    # sicurezza numero uno: uno sconto scelto da chi paga sarebbe un
    # furto con la ricevuta.
    corpo_set = src[src.index("async def _compra_set("):
                    src.index("async def _preventivo_set(")]
    prova("_compra_set: lo sconto non si legge dal payload", False,
          any(k in corpo_set for k in ('d.get("sconto', 'd.get("soglia',
                                       'd.get("percento', 'd.get("totale')))
    prova("_compra_set: la regola arriva dalla riga del VENDITORE", True,
          "_regola_sconto(" in corpo_set and "WHERE tg_id=?" in corpo_set)

    # 4) IL MONO NON SCONTA MAI, in nessun ramo (decisione di Andrea).
    # _righe_ordine e' il punto in cui si romperebbe in silenzio: la
    # divisione a ritroso dell'unitario non tornerebbe piu'.
    corpo_mono = src[src.index("async def compra("):
                     src.index("def crea_ordine_pagato(")]
    prova("compra (mono): la parola sconto non esiste", False,
          "_sconto_pacco" in corpo_mono or "sconto_sats" in corpo_mono)
    # (si guarda il CODICE e non i commenti: dentro _righe_ordine c'e'
    # apposta la nota che dice cosa servirebbe SE un giorno il mono
    # scontasse — quella riga deve poter restare)
    codice_righe = "\n".join(
        r for r in pezzo("_righe_ordine").splitlines()
        if not r.strip().startswith("#"))
    prova("_righe_ordine: la divisione a ritroso non sconta", False,
          "sconto_sats" in codice_righe)
    prova("crea_ordine_pagato (asta) non sconta", False,
          "sconto" in pezzo("crea_ordine_pagato").split('"""')[-1])

    # 5) LA CIFRA DELLA INVOICE E' LA CIFRA DELL'INSERT. E' il buco da
    # cui uscirebbero i sats DI ALTRI ORDINI: se la bolt11 chiedesse il
    # netto e prezzo_sats finisse col lordo, il payout pretenderebbe
    # dalla cassaforte piu' di quanto quell'ordine ha versato — e la
    # cintura di paga_venditore non lo vedrebbe.
    i = corpo_set.index("crea_invoice_escrow(")
    j = corpo_set.index("INSERT INTO ordini", i)
    prova("_compra_set: zero await tra invoice e INSERT", False,
          "await " in corpo_set[i:j])
    prova("_compra_set: il totale non si riscrive li' in mezzo", 0,
          corpo_set[i:j].count("totale ="))
    prova("_compra_set: la invoice si conia sul TOTALE", True,
          "crea_invoice_escrow(\n        totale," in corpo_set)

    # 6) Il tetto di rodaggio giudica il LORDO, PRIMA dello sconto: e'
    # un vincolo del listino, non del checkout — altrimenti si
    # pubblicherebbe sopra il tetto rientrandoci con una regola.
    for chi, corpo in (("_compra_set", corpo_set),
                       ("_preventivo_set", pezzo("_preventivo_set"))):
        prova(f"{chi}: il tetto giudica PRIMA dello sconto", True,
              corpo.index("TETTO_SATS_ANNUNCIO") < corpo.index("_sconto_pacco("))

    # 7) IL DOVUTO IN USCITA NON CONOSCE LO SCONTO. La colonna e' un
    # TESTIMONE: chi ne facesse un netto_venditore(prezzo + sconto)
    # farebbe uscire dall'escrow di altri ordini la differenza.
    prova("netto_venditore non conosce lo sconto", False,
          "sconto" in pezzo("netto_venditore"))
    for nome in ("_sblocca_sats", "_rimborsa_compratore", "deposita_invoice"):
        prova(f"{nome}: il dovuto NON riaggiunge lo sconto", False,
              "sconto_sats" in pezzo(nome).split('"""')[-1])

    # 8) Lo sconto e' un costrutto del checkout: non esce sui relay
    # (il NIP-99 resta col prezzo pieno, come per lampo e tariffa
    # punto) e non cambia la forma del CSV, che e' contabilita'.
    for nome in ("tag_commercio", "evento_annuncio"):
        prova(f"{nome}: cieco allo sconto carrello", False,
              "sconto_pacco" in pezzo(nome))
    prova("un solo UPDATE scrive la regola", 1,
          src.count("sconto_pacco_soglia=?"))

    # 9) IL CLIENT MOSTRA, NON CALCOLA: nessuna aritmetica della
    # percentuale, e la cifra del conto viene sempre dal server.
    mini = open("miniapp.html", encoding="utf-8").read()
    import re
    prova("il client non moltiplica mai per la percentuale dello sconto",
          0, len(re.findall(r"\(\s*100\s*-\s*[A-Za-z_.]*[Ss]conto", mini)))
    prova("l'invito del carrello non porta cifre in sats", False,
          "artStima" in mini[mini.index("function aggiornaInvitoSconto"):
                             mini.index("function aggiornaInvitoSconto") + 1200])
    prova("i lettori del preventivo restano due", 2,
          mini.count("fetch(`${API_BASE}/orders/preventivo`"))
    prova("il giudice del ≈ resta UNO anche col meno", 1,
          mini.count("function cifraCtrl"))
    prova("...e il meno sta DENTRO di lui", True,
          "const m = meno ? '−' : '';" in mini)


def _codice_rifiuto(funzione, init, errore):
    """Il codice HTTP del rifiuto (401), non il suo testo."""
    try:
        funzione(init)
    except errore as e:
        return e.codice
    return None


def prove_conta_feedback():
    """Da quante PERSONE arrivano i feedback (ago 2026). Il conteggio
    esiste per una ragione sola: sul negozio pubblico i voti escono
    senza nomi, quindi 40 feedback dallo stesso account si vedono
    identici a 40 di 40 persone. Qui si guardano le tre righe che lo
    tengono in piedi — e sono tre righe SENTINELLA, del tipo che
    sparisce in un refactor senza che nessuno se ne accorga."""
    print("\n[da quante persone]")
    ric = pezzo("_ricalcola_rating")
    prova("il ricalcolo conta le persone DISTINTE", True,
          "COUNT(DISTINCT da_tg_id)" in ric)
    prova("e le scrive in colonna", True, "n_recensori=?" in ric)
    prova("il negozio pubblico la porta fuori", True,
          "rating, n_feedback, n_recensori, vendite_ok" in _SORGENTE)

    html = open("miniapp.html", encoding="utf-8").read()
    prova("il client ha un giudice unico", True,
          "function contaFeedback(" in html)
    # Due soli posti la mostrano (negozio e Profilo) e devono passare
    # entrambi da li', o diventano due rese diverse della stessa cosa
    prova("i due posti lo usano tutti e due", 2,
          html.count("contaFeedback(") - 1)   # -1 = la definizione

    # La regola della soglia, rifatta qui: la seconda cifra parla SOLO
    # quando i due numeri differiscono
    def conta(n, persone):
        if not n:
            return ""
        return (f" ({n} da {persone} "
                f"{'persona' if persone == 1 else 'persone'})"
                if persone and persone < n else f" ({n})")

    prova("40 voti da 1 persona lo dicono", " (40 da 1 persona)",
          conta(40, 1))
    prova("40 voti da 38 persone lo dicono", " (40 da 38 persone)",
          conta(40, 38))
    prova("40 voti da 40 persone tacciono", " (40)", conta(40, 40))
    prova("senza voti non c'e' riga", "", conta(0, 0))
    prova("un server vecchio non rompe niente", " (5)", conta(5, 0))


# ====================================================================
def prove_xp():
    """Gli XP (ago 2026). Due cose si guardano qui: la FORMULA, che
    porta dentro tre decisioni di Andrea (nessun tetto, la spedizione
    conta, il venditore prende piu' del compratore), e l'IDEMPOTENZA
    del registro — che e' la sola parte di questo cantiere che non si
    puo' riparare a posteriori, perche' gli XP non si ricalcolano dai
    dati veri come i distintivi: un evento non scritto e' perso."""
    print("\n[gli XP]")
    import sqlite3
    import tempfile
    import time

    amb = {"time": time}
    i = _SORGENTE.index("FISSO_XP_ORDINE = ")
    exec(_SORGENTE[i:_SORGENTE.index("AZIONI_XP = {", i)], amb)
    for f in ("oggi_locale", "_ricalcola_xp", "assegna_xp", "xp_ordine"):
        exec(pezzo(f), amb)
    xp_ordine, assegna_xp = amb["xp_ordine"], amb["assegna_xp"]

    # 100.000 € per BTC, cosi' 1 sat = 0,001 € e i conti si leggono
    C = 100_000.0
    prova("libro da 8 €, venditore", 18, xp_ordine(8_000, C, "venditore"))
    prova("libro da 8 €, compratore", 10, xp_ordine(8_000, C, "compratore"))
    prova("cuffie da 120 €, venditore", 130,
          xp_ordine(120_000, C, "venditore"))
    # NESSUN TETTO: chi affida 4.000 € al deposito di garanzia prende
    # quello che vale. Se qualcuno rimettesse un limite, cade qui.
    prova("4.000 € non si limano", 4010,
          xp_ordine(4_000_000, C, "venditore"))
    # La base e' il TOTALE: chi paga 300 € di spedizione ha speso 300 €
    prova("la spedizione conta", 310, xp_ordine(300_000, C, "venditore"))
    # Cambio mai arrivato: resta il fisso, mai un numero inventato
    prova("senza cambio resta il fisso", 10,
          xp_ordine(4_000_000, 0, "venditore"))

    db = os.path.join(tempfile.mkdtemp(), "xp.db")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0);
    CREATE TABLE xp_eventi(id INTEGER PRIMARY KEY AUTOINCREMENT,
      tg_id INTEGER NOT NULL, tipo TEXT NOT NULL, punti INTEGER NOT NULL,
      riferimento TEXT NOT NULL DEFAULT '', creato INTEGER,
      UNIQUE(tg_id, tipo, riferimento));
    INSERT INTO utenti(tg_id) VALUES(900),(901);
    """)

    def somma(t):
        return con.execute("SELECT xp FROM utenti WHERE tg_id=?",
                           (t,)).fetchone()["xp"]

    prova("il primo pagamento passa", 300,
          assegna_xp(con, 900, "ordine", 300, "ordine:1:venditore"))
    prova("IL RETRY NON PAGA", 0,
          assegna_xp(con, 900, "ordine", 300, "ordine:1:venditore"))
    prova("...e la somma non si muove", 300, somma(900))
    # Il ruolo sta nel riferimento, o le due parti dello stesso ordine
    # si pesterebbero sulla UNIQUE e una delle due resterebbe a zero
    prova("l'altro ruolo dello stesso ordine paga", 180,
          assegna_xp(con, 900, "ordine", 180, "ordine:1:compratore"))
    prova("punti a zero non scrivono", 0,
          assegna_xp(con, 900, "visita", 0, "x"))
    # La visita: il tetto giornaliero non e' scritto da nessuna parte,
    # lo fa il riferimento col giorno dentro
    prova("la visita di oggi", 1,
          assegna_xp(con, 901, "visita", 1, "giorno:2026-08-05"))
    prova("la stessa visita non ripaga", 0,
          assegna_xp(con, 901, "visita", 1, "giorno:2026-08-05"))
    prova("quella di domani si'", 1,
          assegna_xp(con, 901, "visita", 1, "giorno:2026-08-06"))

    # Il ricalcolo e' la rete: la cache si puo' sporcare, il registro no
    con.execute("UPDATE utenti SET xp=99999 WHERE tg_id=900")
    prova("il ricalcolo rimette in pari", 480,
          amb["_ricalcola_xp"](con, 900))

    # FUSIONE: unione, non somma cieca — la visita dello stesso giorno
    # fatta dalle due meta' resta UNA riga, ed e' cio' che la UNIQUE
    # vuol dire
    assegna_xp(con, 900, "visita", 1, "giorno:2026-08-06")
    con.execute("UPDATE OR IGNORE xp_eventi SET tg_id=900 WHERE tg_id=901")
    con.execute("DELETE FROM xp_eventi WHERE tg_id=901")
    prova("fondendo, il giorno doppio conta una volta", 482,
          amb["_ricalcola_xp"](con, 900))
    con.close()


# ====================================================================
def prove_coorti_titoli():
    """Coorti, livelli e titoli (ago 2026). Il pezzo che vale di piu'
    e' il LIVELLO A DUE CHIAVI: e' la conseguenza diretta del «nessun
    tetto» sugli XP — senza il secondo requisito, una vendita da 4.000
    € basterebbe a fare un maestro, e il grado direbbe «ha venduto una
    cosa cara» invece di «commercia»."""
    print("\n[coorti, livelli, titoli]")
    import sqlite3
    import tempfile
    import time

    amb = {"time": time}
    for blocco in ("COORTI = [", "LIVELLI = [", "TITOLI = ("):
        i = _SORGENTE.index(blocco)
        exec(_SORGENTE[i:_SORGENTE.index("\n\n\n", i)], amb)
    for f in ("coorte_da_posizione", "assegna_coorte", "livello_utente",
              "titoli_disponibili"):
        exec(pezzo(f), amb)
    coorte = amb["coorte_da_posizione"]
    livello = amb["livello_utente"]

    prova("il primo iscritto e' pioniere", "pioniere", coorte(1))
    prova("il centesimo ancora pioniere", "pioniere", coorte(100))
    prova("il 101esimo e' fondatore", "fondatore", coorte(101))
    # Oltre l'ultima soglia NON c'e' coorte: e' un fatto, non un
    # premio da dare a tutti — se ce l'hanno tutti non dice niente
    prova("oltre l'ultima soglia nessuna coorte", "", coorte(10001))

    prova("appena arrivato", "Nuovo arrivato", livello(0, 0)["nome"])
    # LA REGOLA DELLE DUE CHIAVI, nei due sensi
    prova("4010 XP con UN affare solo resta avviato", "Bottega avviata",
          livello(4010, 1)["nome"])
    prova("...con quindici affari e' esperto", "Mercante esperto",
          livello(4010, 15)["nome"])
    prova("venti affari da poco non bastano", "Bottega avviata",
          livello(200, 20)["nome"])
    prova("in cima non c'e' un prossimo", "",
          livello(99999, 99)["nome_prossimo"])

    db = os.path.join(tempfile.mkdtemp(), "t.db")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY, registrato INTEGER DEFAULT 0,
      coorte TEXT DEFAULT '', xp INTEGER DEFAULT 0, titolo TEXT DEFAULT '',
      vendite_ok INTEGER DEFAULT 0, acquisti_ok INTEGER DEFAULT 0);
    CREATE TABLE badge_utente(tg_id INTEGER, badge_id TEXT,
      ottenuto_il INTEGER, PRIMARY KEY(tg_id,badge_id));
    INSERT INTO utenti(tg_id,registrato) VALUES(1,1001),(5,1005);
    """)
    amb["assegna_coorte"](con, 1)
    amb["assegna_coorte"](con, 5)
    prova("il primo iscritto prende la coorte", "pioniere",
          con.execute("SELECT coorte FROM utenti WHERE tg_id=1"
                      ).fetchone()["coorte"])
    # CONGELATA: arrivano mille utenti prima di lui e non cambia nulla
    for i in range(100, 1200):
        con.execute("INSERT INTO utenti(tg_id,registrato) VALUES(?,1)", (i,))
    amb["assegna_coorte"](con, 5)
    prova("la coorte scritta non si ricalcola mai piu'", "pioniere",
          con.execute("SELECT coorte FROM utenti WHERE tg_id=5"
                      ).fetchone()["coorte"])

    t = amb["titoli_disponibili"](con, 1)
    prova("il pioniere ha il suo titolo", True, "coorte_pioniere" in t)
    prova("non quello di un'altra coorte", False, "coorte_fondatore" in t)
    prova("senza distintivo niente titolo nostrano", False, "t_nostrano" in t)
    con.execute("INSERT INTO badge_utente VALUES(1,'nostrano',0)")
    con.execute("UPDATE utenti SET xp=3000, vendite_ok=10, acquisti_ok=6 "
                "WHERE tg_id=1")
    t = amb["titoli_disponibili"](con, 1)
    prova("col distintivo arriva il titolo", True, "t_nostrano" in t)
    prova("il livello raggiunto sblocca il suo", True, "t_esperto" in t)
    # I livelli sono una SCALA: li ha attraversati tutti
    prova("...e anche i gradini di sotto", True, "t_pratico" in t)
    prova("ma non quello sopra", False, "t_maestro" in t)
    con.close()

    # Il client ripete le soglie XP per disegnare la barra DENTRO il
    # gradino (senza, non saprebbe da dove parte il tratto). E' una
    # copia, quindi si incrocia — la lezione delle categorie senza
    # condizione: due cataloghi che divergono sono un catalogo solo
    # scritto male, e qui la barra mentirebbe in silenzio.
    import re
    html = open("miniapp.html", encoding="utf-8").read()
    i = html.index("const SOGLIE_LIV = [")
    front = [int(n) for n in
             re.findall(r"\d+", html[i:html.index("]", i)])]
    prova("le soglie del client combaciano col server",
          [l[0] for l in amb["LIVELLI"]], front)


# ====================================================================
class _ConfigFinto(dict):
    """Un config finto dove le chiavi che NON abbiamo messo a mano
    valgono 7 — un numero qualunque.

    Serve a non tenere allineato un elenco di settanta nomi: una leva
    aggiunta domani entra da sola nel censimento senza rompere niente.
    SE LA PROVA ESPLODE con un TypeError su _elenco, la leva nuova e'
    una LISTA: mettila a mano qui sotto accanto alle altre."""

    def __missing__(self, nome):
        # I builtins vanno lasciati passare: con __missing__ definito
        # la ricerca di un nome globale non arriva MAI da sola fino a
        # loro, e senza questa riga perfino `bool` varrebbe 7.
        import builtins
        if hasattr(builtins, nome):
            raise KeyError(nome)
        return 7


# I segreti veri, con un valore riconoscibile a occhio: se uno di
# questi finisce nel censimento, la prova lo trova nel JSON. Il
# nome della chiave invece PUO' uscire (serve per andarla a
# cambiare, ed e' scritto in chiaro in config_esempio.py): a essere
# controllato e' il VALORE.
_SEGRETI_FINTI = {
    "BOT_TOKEN": "SEGRETO-token-del-bot",
    "ANTHROPIC_API_KEY": "SEGRETO-chiave-anthropic",
    "LNBITS_URL": "SEGRETO-url-lnbits",
    "LNBITS_INVOICE_KEY": "SEGRETO-invoice-key",
    "LNBITS_ADMIN_KEY": "SEGRETO-admin-key",
    "NOSTR_NSEC_PIATTAFORMA": "SEGRETO-nsec-piattaforma",
    "TELEGRAM_WEBHOOK_SEGRETO": "SEGRETO-webhook",
    "TELEGRAM_CANALE_ID": "SEGRETO-canale",
    "CHIAVE_CONTENUTI_DIGITALI": "SEGRETO-contenuti",
    "DB": "SEGRETO-percorso-database",
}


def _censimento(acceso):
    """Gira il censimento con tutte le leve accese o tutte spente, e
    restituisce (voci per chiave, JSON di tutto)."""
    import json
    amb = _ConfigFinto(_SEGRETI_FINTI)
    amb["__builtins__"] = __builtins__
    # Le leve che sono LISTE: _elenco ci itera sopra.
    for nome in ("ASTA_DURATE_GIORNI", "LAMPO_SCONTI", "ORE_LAMPO_OPZIONI",
                 "SCONTO_PACCO_SOGLIE", "SCONTO_PACCO_SCONTI"):
        amb[nome] = [1, 2, 3]
    # ADMIN_IDS esce come CONTEGGIO: gli id dei moderatori non sono
    # roba da mostrare, nemmeno a un moderatore.
    amb["ADMIN_IDS"] = [111111111, 222222222]
    # Le leve booleane e i numeri che l'interruttore governa.
    for nome in ("MODALITA_COLLAUDO", "AUTO_SBLOCCO_ATTIVO",
                 "ASTA_ABILITATA", "ASTA_PROXY_ATTIVO", "LAMPO_ATTIVE",
                 "SCONTO_PACCO_ATTIVO", "FERIE_ATTIVE", "BANNER_TEST",
                 "BANNER_TEST_LINK", "CONTATORE_UTENTI", "POST_AUTOMATICI",
                 "IMPORT_NOSTR_APERTO", "RICATEGORIZZA_AUTO",
                 "MODERAZIONE_REVISIONE", "AVVISI_ISCRITTI",
                 "AVVISI_ORDINI_ADMIN", "TERMOMETRO_SOTTOCATEGORIE",
                 "CONTROLLO_LIBRO_MASTRO", "ORE_INITDATA",
                 "TETTO_RICERCHE_AI_ORA", "COMMISSIONE_PERCENTO",
                 "PROTEZIONE_PERCENTO", "TETTO_SATS_ANNUNCIO",
                 "SOLLECITO_INCASSO_GIORNI", "PROMEMORIA_CONFERMA_GIORNI",
                 "PROMEMORIA_SPEDIZIONE_GIORNI", "PROMEMORIA_DIGITALE_ORE",
                 "REVISIONE_SOLLECITO_GIORNI", "FERIE_PREAVVISO_ORE",
                 "GIORNI_DATA_ANNUNCIO", "TETTO_DIGITALE_NUOVI",
                 "DIGITALE_MIN_VENDITE"):
        amb[nome] = acceso and 24
    # I due che dipendono da un pacchetto oltre che dalla chiave.
    amb["Fernet"] = object() if acceso else None
    amb["_NOSTR"] = ("chiave", "pubkey") if acceso else None
    if not acceso:
        amb["TELEGRAM_WEBHOOK_SEGRETO"] = ""
        amb["TELEGRAM_CANALE_ID"] = ""
        amb["CHIAVE_CONTENUTI_DIGITALI"] = ""
        amb["ADMIN_IDS"] = []
    for f in ("webhook_attivo", "_leva", "_elenco", "_leve_stato"):
        exec(pezzo(f), amb)
    gruppi = amb["_leve_stato"]()
    voci = {v["chiave"]: v for g in gruppi for v in g["voci"]}
    return gruppi, voci, json.dumps(gruppi, default=str, ensure_ascii=False)


def prove_leve():
    """Lo stato delle leve nel pannello admin (ago 2026).

    Due cose sole, e la prima e' la ragione per cui la pagina puo'
    esistere: che il valore DETTO sia quello con cui il server sta
    girando, e che nessun segreto esca mai — nemmeno quando e' il
    segreto stesso a fare da interruttore."""
    print("\n[stato delle leve]")
    gruppi_on, voci_on, json_on = _censimento(True)
    gruppi_off, voci_off, json_off = _censimento(False)

    # --- 1) I SEGRETI, che e' il punto di tutto -------------------
    for chiave, valore in _SEGRETI_FINTI.items():
        prova(f"il valore di {chiave} non esce (leve accese)",
              True, valore not in json_on)
        prova(f"il valore di {chiave} non esce (leve spente)",
              True, valore not in json_off)
    prova("nessun id di moderatore nel censimento", True,
          "111111111" not in json_on and "222222222" not in json_on)
    prova("i moderatori escono come CONTEGGIO", 2, voci_on["ADMIN_IDS"]["valore"])
    # Il segreto che E' l'interruttore: esce il fatto, mai la chiave.
    prova("Nostr acceso col fatto, non con la nsec",
          True, voci_on["NOSTR_NSEC_PIATTAFORMA"]["valore"])
    prova("Nostr spento senza nsec",
          False, voci_off["NOSTR_NSEC_PIATTAFORMA"]["valore"])
    prova("webhook: acceso col segreto vero",
          True, voci_on["TELEGRAM_WEBHOOK_SEGRETO"]["valore"])
    prova("webhook: spento senza segreto",
          False, voci_off["TELEGRAM_WEBHOOK_SEGRETO"]["valore"])
    prova("cifratura dei codici: accesa con chiave e pacchetto",
          True, voci_on["CHIAVE_CONTENUTI_DIGITALI"]["valore"])
    prova("cifratura dei codici: spenta senza chiave",
          False, voci_off["CHIAVE_CONTENUTI_DIGITALI"]["valore"])
    prova("canale Telegram: solo acceso/spento",
          (True, False), (voci_on["TELEGRAM_CANALE_ID"]["valore"],
                          voci_off["TELEGRAM_CANALE_ID"]["valore"]))
    prova("il percorso del database non e' una leva",
          False, "DB" in voci_on)

    # --- 2) LA FORMA ---------------------------------------------
    prova("ogni gruppo ha delle voci", True,
          all(g["voci"] for g in gruppi_on) and len(gruppi_on) >= 8)
    prova("ogni voce ha nome, chiave e valore", True,
          all(v.get("nome") and v.get("chiave") and "valore" in v
              for v in voci_on.values()))
    prova("le chiavi sono nomi di config, non valori", True,
          all(c.isupper() or c.startswith("_") for c in voci_on))
    prova("acceso e spento censiscono le stesse leve",
          set(voci_on), set(voci_off))

    # --- 3) LA NOTA COMPARE SOLO DOVE SERVE ----------------------
    # Settanta righe di spiegazione tutte insieme sono un muro.
    prova("l'auto-sblocco spiega il disarmo quando e' spento", True,
          "gesto umano" in voci_off["AUTO_SBLOCCO_ATTIVO"].get("nota", "")
          or "timer" in voci_off["AUTO_SBLOCCO_ATTIVO"].get("nota", ""))
    prova("e acceso dice l'altra cosa (i testi da rimettere)", True,
          "testi" in voci_on["AUTO_SBLOCCO_ATTIVO"].get("nota", ""))
    prova("la commissione spiega solo da sospesa", True,
          "nota" in voci_off["COMMISSIONE_PERCENTO"]
          and "nota" not in voci_on["COMMISSIONE_PERCENTO"])
    prova("le durate d'asta non hanno niente da spiegare", True,
          "nota" not in voci_on["ASTA_DURATE_GIORNI"])

    # --- 4) L'ALLARME, che e' un'altra cosa dalla nota -------------
    # Il valore che fa paura non e' sempre lo stesso: il collaudo
    # spaventa ACCESO, la scadenza dell'initData SPENTA.
    prova("collaudo acceso = allarme", True,
          voci_on["MODALITA_COLLAUDO"].get("allarme", False))
    prova("collaudo spento = nessun allarme", False,
          voci_off["MODALITA_COLLAUDO"].get("allarme", False))
    prova("initData senza scadenza = allarme", True,
          voci_off["ORE_INITDATA"].get("allarme", False))
    prova("initData con scadenza = nessun allarme", False,
          voci_on["ORE_INITDATA"].get("allarme", False))
    prova("nessun moderatore = allarme", True,
          voci_off["ADMIN_IDS"].get("allarme", False))

    # --- 5) SI GUARDA E BASTA -------------------------------------
    # Una leva che si accende da un telefono e' una leva che si
    # accende per sbaglio: le tre che nascono spente nel codice
    # vogliono un gesto sul VPS, e qui non deve nascere una scorciatoia.
    prova("nessuna rotta che SCRIVE le leve", True,
          '@app.post("/api/admin/leve' not in _SORGENTE
          and '@app.put("/api/admin/leve' not in _SORGENTE)
    i = _SORGENTE.index("def leve_admin(")
    corpo = _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]
    prova("la rotta e' riservata ai moderatori", True,
          "e_admin" in corpo and "403" in corpo)


# ====================================================================
def main():
    print("=" * 58)
    print("  LE PROVE DI BARATTOLO")
    print("=" * 58)
    for f in (prove_filtro_italiano, prove_testo_evento,
              prove_tag_commercio, prove_anello, prove_categorie,
              prove_nome_nostr,
              prove_senza_condizione, prove_sottocategorie,
              prove_ricategorizza, prove_asta, prove_proxy_asta,
              prove_annullo,
              prove_ritiro, prove_disarmo, prove_importo_uscita,
              prove_initdata, prove_foto, prove_avatar,
              prove_pagamento_incerto, prove_disputa_incagliata,
              prove_idor_verifica, prove_contenuti_cifrati,
              prove_ssrf_redirect, prove_quota_ricerca,
              prove_tracking_corretto, prove_barattolo,
              prove_messaggio_admin, prove_avviso_contatto,
              prove_forma_tracking, prove_bip353, prove_conta_feedback,
              prove_ferie,
              prove_xp, prove_coorti_titoli, prove_conto_acquisto,
              prove_sconto_pacco, prove_forma_sconto_pacco,
              prove_libro_mastro, prove_leve,
              prove_consegna_payload_punto, prove_pagina_acquisto):
        try:
            f()
        except Exception as e:
            global FALLITE
            FALLITE += 1
            print(f"  ✗ {f.__name__} è esplosa: {type(e).__name__}: {e}")
    print("\n" + "=" * 58)
    conto = f"  {PASSATE} passate, {FALLITE} fallite"
    if SALTATE:
        conto += f", {SALTATE} SALTATA" if SALTATE == 1 else \
                 f", {SALTATE} SALTATE"
    print(conto)
    if SALTATE and SEVERE:
        print("  (con PROVE_SEVERE una saltata vale una fallita)")
    print("=" * 58)
    return 1 if FALLITE or (SALTATE and SEVERE) else 0


if __name__ == "__main__":
    sys.exit(main())
