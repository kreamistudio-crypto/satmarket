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

import ast
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


def codice(testo):
    """Le sole righe di CODICE: via i commenti. Serve alle sentinelle
    che cercano una parola-spia (`await `, `INSERT`...) dentro una
    fetta di sorgente — in un progetto che commenta molto, quella
    parola finisce prima o poi in una riga di prosa che la spiega, e
    la sentinella diventa rossa per il motivo sbagliato. Peggio: chi
    la vede rossa impara a riscrivere la frase invece di guardare il
    codice. Le stringhe non si toccano (qui non servono, e togliere
    un `#` da dentro una stringa sarebbe un altro genere di bugia)."""
    return "\n".join(r for r in testo.split("\n")
                     if not r.strip().startswith("#"))


_SORGENTE = open("server.py", encoding="utf-8").read()


def reale(nome):
    """Il pezzo VERO, per gli ambienti finti che ne hanno bisogno.
    Meglio di uno stub scritto a mano, e la ragione l'ha insegnata
    _fmt_sats: il finto sollevava sul None esattamente come quello
    vero PRIMA della cura, quindi la prova restava rossa anche a
    guasto riparato — uno stub che imita un pezzo finisce per
    imitarne anche i bug."""
    amb = {}
    exec(pezzo(nome), amb)
    return amb[nome]


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
    sorgente_imp = open("importa_nostr.py", encoding="utf-8").read()

    def pezzo_imp(nome):
        """pezzo(), ma sull'altro file: `pezzo` legge solo server.py."""
        i = sorgente_imp.index(f"def {nome}(")
        return sorgente_imp[i:sorgente_imp.index("\n\n\n", i)]

    i = sorgente_imp.index("def importa_venditore(")
    corpo = sorgente_imp[i:sorgente_imp.index("\ndef ", i + 10)]
    prova("l'import confronta l'autore dell'evento con la chiave chiesta",
          True,
          bool(re.search(r'\(e\.get\("pubkey"\)\s*or\s*""\)\.lower\(\)\s*'
                         r'[!=]=\s*hexkey', corpo)))

    # --- Il riflesso non e' una fonte (ago 2026) --------------------
    # Il gemello di chiave_di_casa un piano piu' in basso: un evento
    # che abbiamo composto NOI e fatto firmare al venditore e' lo
    # specchio di una riga nata qui, e importarlo «adottava» quella
    # riga (via il match per TITOLO), togliendo al venditore la
    # modifica dal form e consegnando a una sua NIP-09 il potere di
    # spegnerla su Barattolo.
    amb2 = {}
    exec(pezzo_imp("id_riflesso"), amb2)
    exec(pezzo_imp("e_riflesso"), amb2)
    idr, erifl = amb2["id_riflesso"], amb2["e_riflesso"]
    # 1ª condizione: la coordinata e' una NOSTRA
    prova("«barattolo-42» nomina la riga 42", 42, idr("barattolo-42"))
    prova("una coordinata di un altro non nomina niente", 0,
          idr("mio-annuncio-42"))
    # ...nemmeno una lunga uguale, che senza il prefisso finirebbe per
    # nominare la riga 89 di un altro mercatino (torturato: togliendo
    # il controllo del prefisso, questa riga diventa rossa e le altre
    # no — era l'unico buco della mutazione)
    prova("...nemmeno una che ha le cifre al posto giusto", 0,
          idr("altrosito-89"))
    prova("il vuoto non nomina niente", 0, idr(""))
    prova("«barattolo-» senza numero non nomina niente", 0,
          idr("barattolo-"))
    prova("un id non numerico non nomina niente", 0, idr("barattolo-89x"))
    # 2ª e 3ª: la riga e' NATIVA ed e' firmata proprio da quella chiave
    mia = "bb" * 32
    prova("riga nativa firmata da lui: e' un riflesso", True,
          erifl(("", mia), mia))
    prova("...anche se la colonna e' in maiuscolo", True,
          erifl(("", mia.upper()), mia))
    prova("riga IMPORTATA: non e' un riflesso (l'import e' a casa sua)",
          False, erifl(("npub1qualcosa", mia), mia))
    prova("riga mai firmata: non e' un riflesso", False, erifl(("", ""), mia))
    prova("due vuoti non sono una prova", False, erifl(("", ""), ""))
    prova("firmata da un ALTRO: non e' un riflesso", False,
          erifl(("", "cc" * 32), mia))
    prova("riga sparita: non e' un riflesso", False, erifl(None, mia))
    # E che il filtro sia ancora attaccato al giro d'import: sono tre
    # righe che un riordino porta via senza rompere nessun'altra prova.
    prova("l'import chiama i due giudici del riflesso", True,
          "id_riflesso(" in corpo and "e_riflesso(" in corpo)
    # find() e non index(): se la chiamata sparisce questa prova deve
    # FALLIRE, non esplodere — una prova che si schianta fa rossa la CI
    # senza dire quale patto e' saltato.
    dove = corpo.find("e_riflesso(")
    prova("...e li chiama PRIMA del vaglio (l'AI non giudica i nostri)",
          True, 0 <= dove < corpo.index("if vaglio:"))


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
    # ago 2026: questa ha CAMBIATO LATO. Prima chiedeva che il reaper
    # spazzasse anche i 'creato' — cioe' certificava il buco: quel
    # DELETE si portava via il payment_hash di fatture che nessuno
    # aveva mai verificato. Ora i 'creato' li dichiara morti
    # controlla_abbandonati, DOPO aver guardato (vedi prove_abbandonati).
    prova("reaper: purga delle lapidi rilanci", True,
          "DELETE FROM rilanci WHERE stato='annullato'" in reaper)
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
          # dall'ago 2026 l'altezza si divide per la scala del testo:
          # le unita' di viewport non si zoomano (vedi --fs-zoom) — e
          # si sottrae la TASTIERA, che il layout viewport non vede e
          # 100dvh su iOS non accorcia
          and "max-height:calc(100dvh / var(--fs-zoom,1) - 16px "
              "- var(--tastiera,0px))" in mini)
    prova("QR: la misura segue l'altezza disponibile (mai sotto i "
          "170px)", True, "max(170px, 30dvh)" in mini)


def prove_abbandonati():
    """L'ULTIMO SGUARDO (ago 2026). Il reaper cancellava gli ordini
    'creato' scaduti con un DELETE secco — «nessun sat e' coinvolto,
    e' solo pulizia», vero SOLO se qualcuno ha chiesto a LNbits, e a
    chiedere c'e' un poll che vive nel telefono del compratore. Chi
    pagava e chiudeva l'app lasciava dei sats in cassaforte senza un
    ordine, e col payment_hash cancellato nemmeno LNbits sa a chi
    renderli. Mai successo in produzione (incrociati gli incassi coi
    payment_hash noti: zero orfani), ma il buco era aperto.
    Qui si prova l'INVARIANTE — nessuna riga si cancella senza che
    qualcuno abbia guardato — sulla forma E sul pezzo vero, con un
    database in memoria e LNbits di cartone."""
    print("\n[l'ultimo sguardo]")
    import asyncio
    import sqlite3
    import time as _t

    def gira(coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def pezzo_async(nome):
        return "async " + pezzo(nome)

    # --- L'invariante sulla FORMA: sono le righe che un riordino
    #     rimetterebbe senza accorgersi di riaprire il buco ----------
    reaper = pezzo("pulisci_ordini_fantasma")
    prova("reaper: non cancella piu' nessun ordine 'creato'", False,
          "stato='creato'" in reaper)
    prova("reaper: non cancella piu' nessun rilancio 'creato'", False,
          "'creato','annullato'" in reaper)
    prova("reaper: le lapidi si spazzano ancora (quelle si', le ha "
          "gia' guardate qualcuno)", True,
          "DELETE FROM ordini WHERE stato='annullato'" in reaper
          and "DELETE FROM rilanci WHERE stato='annullato'" in reaper)
    # La RIGA intera e non la sottostringa: cercando il nome, un
    # «pass  # await controlla_abbandonati()» lascerebbe la sentinella
    # verde con la funzione mai chiamata — provato, restava verde.
    prova("ultimo sguardo: agganciato all'orologio", True,
          any(r.strip() == "await controlla_abbandonati()"
              for r in pezzo("orologio").splitlines()))
    # la vita della fattura vive in UN posto solo: due copie a mano, e
    # quella sbagliata dichiara annullato un ordine ancora pagabile
    prova("scadenza della fattura: un nome, non un numero a mano", True,
          "expiry: int = INVOICE_EXPIRY" in _SORGENTE
          and "adesso - INVOICE_EXPIRY" in _SORGENTE)

    # --- Il giro VERO: i tre esiti su un database vero --------------
    def mondo(muto=False):
        vero = sqlite3.connect(":memory:")
        vero.row_factory = sqlite3.Row
        vero.execute("CREATE TABLE ordini(id INTEGER PRIMARY KEY, "
                     "stato TEXT, payment_hash TEXT, creato INT, "
                     "aggiornato INT)")
        vero.execute("CREATE TABLE offerte(id INTEGER PRIMARY KEY, "
                     "ordine_id INT, stato TEXT)")
        vero.execute("CREATE TABLE rilanci(id INTEGER PRIMARY KEY, "
                     "stato TEXT, payment_hash TEXT, creato INT, "
                     "aggiornato INT, annuncio_id INT, tg_id INT, "
                     "puntata_id INT, delta_sats INT)")
        vero.execute("CREATE TABLE rimborsi_asta(id INTEGER PRIMARY KEY, "
                     "annuncio_id INT, tg_id INT, puntata_id INT, "
                     "rilancio_id INT, importo_sats INT, motivo TEXT, "
                     "stato TEXT, creato INT, aggiornato INT)")
        ora = int(_t.time())
        vero.executemany("INSERT INTO ordini VALUES(?,?,?,?,?)", [
            (1, "creato", "hash-pagato", ora - 2000, 0),   # pagato, mai visto
            (2, "creato", "hash-muto",   ora - 2000, 0),   # abbandonato
            (3, "creato", "hash-pagato", ora - 60,   0)])  # fattura ancora VIVA
        vero.execute("INSERT INTO offerte VALUES(9,2,'accettata')")
        vero.executemany("INSERT INTO rilanci VALUES(?,?,?,?,?,?,?,?,?)", [
            (1, "creato", "hash-pagato", ora - 900, 0, 7, 111, 5, 300),
            (2, "creato", "hash-muto",   ora - 900, 0, 7, 222, 6, 400),
            (3, "creato", "hash-pagato", ora - 60,  0, 7, 333, 7, 500)])
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

        incassati, avvisati, rimborsati = [], [], []

        async def _pagata(h):
            if muto:
                raise RuntimeError("LNbits non risponde")
            return h == "hash-pagato"

        async def _incassa(oid):
            incassati.append(oid)
            return {"stato": "locked"}

        async def _notifica(tg, testo):
            avvisati.append(tg)

        async def _rimborso(rid):
            rimborsati.append(rid)

        amb = {"db": Con, "time": _t, "invoice_pagata": _pagata,
               "_incassa_ordine": _incassa, "notifica": _notifica,
               "_paga_rimborso": _rimborso,
               "print": lambda *a, **k: None,
               "INVOICE_EXPIRY": 900, "RILANCIO_EXPIRY": 600}
        exec(pezzo_async("controlla_abbandonati"), amb)
        return (amb["controlla_abbandonati"], vero,
                incassati, avvisati, rimborsati)

    corri, vero, incassati, avvisati, rimborsati = mondo()
    gira(corri())

    def stato(tab, i):
        return vero.execute(f"SELECT stato FROM {tab} WHERE id=?",
                            (i,)).fetchone()["stato"]

    # 1. pagato e mai verificato: si incassa. La riga NON diventa una
    #    lapide (qui _incassa_ordine e' di cartone: quello vero la
    #    porta a 'locked', e ha le sue prove)
    prova("ordine pagato e mai verificato: passa da _incassa_ordine",
          ([1], "creato"), (incassati, stato("ordini", 1)))
    # 2. non pagato: LAPIDE, mai DELETE — un saldo deve avere sempre
    #    una riga su cui posarsi (la regola di annulla_ordine)
    prova("ordine abbandonato: lapide 'annullato', mai DELETE",
          ("annullato", 3), (stato("ordini", 2),
           vero.execute("SELECT COUNT(*) FROM ordini").fetchone()[0]))
    prova("lapide: l'offerta si scioglie e resta ripagabile",
          (0, "accettata"),
          tuple(vero.execute("SELECT ordine_id, stato FROM offerte "
                             "WHERE id=9").fetchone()))
    # 3. fattura ancora viva: non si tocca, o si direbbe «annullato» a
    #    chi sta per pagare
    prova("ordine con la fattura ancora VIVA: non si guarda nemmeno",
          "creato", stato("ordini", 3))

    prova("rilancio pagato fuori tempo: 'tardivo', i sats al registro",
          ("tardivo", 1, "tardivo"),
          (stato("rilanci", 1),
           vero.execute("SELECT COUNT(*) FROM rimborsi_asta").fetchone()[0],
           vero.execute("SELECT motivo FROM rimborsi_asta").fetchone()[0]))
    prova("rilancio pagato: chi ha pagato lo viene a sapere, e la "
          "riscossione parte", ([111], 1), (avvisati, len(rimborsati)))
    prova("rilancio abbandonato: lapide", "annullato", stato("rilanci", 2))
    prova("rilancio con la fattura viva: non si tocca", "creato",
          stato("rilanci", 3))

    # --- FAIL-OPEN NEL VERSO GIUSTO --------------------------------
    # LNbits muto: meglio una riga che si attarda che un pagamento
    # buttato via. Nessuno la cancella piu' alle sue spalle.
    corri, vero, incassati, _, _ = mondo(muto=True)
    gira(corri())
    prova("LNbits muto: nessuna riga si muove, si riprova al giro dopo",
          (["creato"] * 3, ["creato"] * 3, []),
          ([r["stato"] for r in vero.execute("SELECT stato FROM ordini "
                                             "ORDER BY id")],
           [r["stato"] for r in vero.execute("SELECT stato FROM rilanci "
                                             "ORDER BY id")],
           incassati))


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
    detti = []          # il TESTO degli avvisi, per chi vuole leggerlo

    def cintura(dice_la_fattura, dovuti, codice=200):
        """Monta paga_venditore con un giudice dell'importo finto e un
        LNbits di cartone. Torna (esito, quante POST, quanti avvisi);
        il testo degli avvisi si ritrova in `detti`."""
        uscite, avvisi = [], []

        async def _importo(_b):
            return dice_la_fattura

        async def _admin(t):
            avvisi.append(t)
            detti.append(t)

        amb = {"httpx": _finto_lnbits(uscite, codice),
               "importo_invoice": _importo, "notifica_admin": _admin,
               "print": lambda *a, **k: None,
               "LNBITS_URL": "http://x", "LNBITS_ADMIN_KEY": "k",
               # i tre esiti (ago 2026): qui interessa il rifiuto, ma
               # senza i nomi la funzione non gira nemmeno
               "PAGATO": "pagato", "NON_PAGATO": "non_pagato",
               "INCERTO": "incerto",
               # e il formattatore dei sats, che l'avviso ai
               # moderatori usa da quando un satoshi si scrive in un
               # modo solo: chi estrae una funzione ne eredita le
               # dipendenze, ed e' cosi' che questa prova e' esplosa
               "_fmt_sats": reale("_fmt_sats")}
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
    # ...e l'avviso DICE che era illeggibile. Sembra cosmesi e non lo
    # e': i motivi del rifiuto sono tre e chi legge deve capire al
    # primo sguardo se ha davanti un wallet rotto o un tentativo di
    # prelievo. Fino all'ago 2026 diceva «chiedeva None sats», che
    # era il modo di non dirlo.
    prova("...e l'avviso dice ILLEGGIBILE, non «None sats»", True,
          "illeggibile" in detti[-1] and "None" not in detti[-1])
    prova("...mentre il rifiuto per cifra sbagliata dice la cifra", True,
          "100.000.000 sats" in (cintura(100_000_000, 1), detti)[1][-1])
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
               # chi estrae una funzione ne eredita le dipendenze
               "_fmt_sats": reale("_fmt_sats"),
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
               "_fmt_sats": reale("_fmt_sats"),
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
               # ...e il titolo delle notifiche passa da html.escape
               # (ago 2026, la famiglia di B6): stessa trappola, secondo
               # giro — chi estrae una funzione ne eredita le dipendenze.
               "html": __import__("html"),
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


def prove_busta_ritiro():
    """La busta di consegna (ago 2026): nome del destinatario e codice
    di ritiro DENTRO l'ordine, cifrati col trasporto dei contenuti
    digitali ma MAI con la sua semantica — aprire la busta non e' una
    ricevuta, e la macchina dell'escrow non sa che esiste. NIENTE gate
    su segna_spedito (decisione di Andrea): il codice arriva quando il
    pacco e' GIA' al punto."""
    print("\n[la busta di consegna]")
    import asyncio
    import shutil
    import sqlite3
    import tempfile
    import time as _t

    # la whitelist delle firme e' una costante, non una funzione:
    # si estrae per testo come tutto il resto, o la prova giudicherebbe
    # una tabella scritta a mano invece di quella vera
    _i = _SORGENTE.index("FIRME_DOC_BUSTA = (")
    _firme_doc = _SORGENTE[_i:_SORGENTE.index("\n)\n", _i) + 3]
    buste_dir = tempfile.mkdtemp(prefix="buste-prove-")

    # --- le sentinelle di forma: la SEPARAZIONE dall'escrow ---------
    dep = pezzo("deposita_busta_ritiro").split('"""')[-1]
    let = pezzo("leggi_busta_ritiro").split('"""')[-1]
    sped = pezzo("segna_spedito").split('"""')[-1]
    prova("deposito: solo venditore, su locked/shipped/dispute", True,
          "venditore_id=?" in dep
          and "'locked','shipped','dispute'" in dep)
    prova("deposito: esige la via punto", True, 'o["via_punto"]' in dep)
    prova("deposito: UN solo UPDATE, e tocca SOLO le colonne busta", 1,
          dep.count("UPDATE"))
    prova("deposito: non tocca stato, spedito_il, consegnato", [],
          [x for x in ("stato='", "spedito_il", "consegnato")
           if x in dep])
    prova("deposito: cifra col trasporto dei contenuti digitali", True,
          "_cifra_contenuto(" in dep)
    prova("deposito: il journal porta l'impronta, mai il testo", True,
          "hashlib.sha256(codice" in dep and "[:16]" in dep)
    prova("deposito: notifiche statiche, mai il contenuto", [],
          [x for x in ("{nome", "{codice") if x in dep])
    # il GET e' PURO: aprire la busta significa poter andare a
    # ritirare, NON aver ricevuto — qui vive la separazione
    prova("lettura: GET puro, nessuna scrittura", [],
          [x for x in ("UPDATE", "INSERT", "commit") if x in let])
    prova("lettura: non sa nemmeno cosa sia `consegnato`", False,
          "consegnato" in let)
    prova("lettura: l'admin non ha strada", False, "e_admin" in let)
    prova("lettura: autorizzazione PRIMA dell'esistenza (anti-oracolo)",
          True, "compratore_id=? OR venditore_id=?" in let
          and let.index("Operazione non permessa")
          < let.index("Nessuna istruzione"))
    # il gate NON esiste (decisione di Andrea che ha rovesciato il
    # brief): in segna_spedito la busta compare solo DOPO l'UPDATE,
    # cioe' nel ramo delle notifiche — mai in una guardia
    prova("segna_spedito: nessun gate sulla busta", True,
          sped.index("UPDATE ordini SET stato='shipped'")
          < sped.index("busta_il"))
    # il segnale d'arrivo e' UNO e parte da due strade: la costante
    # e' definita una volta e usata due
    prova("il «ti aspetta» e' UNA costante per due strade", 3,
          _SORGENTE.count("MSG_BUSTA_PRONTA"))
    # le finestre dell'escrow non sanno che la busta esiste
    prova("controlla_scadenze e' cieca alla busta", False,
          "busta" in pezzo("controlla_scadenze"))
    # lo strip: nome e codice non escono MAI da /api/orders
    mo = pezzo("miei_ordini")
    prova("lo strip di /api/orders copre nome e codice", True,
          'r.pop("busta_nome"' in mo and 'r.pop("busta_codice"' in mo)
    # la nota in disputa dice SE e QUANDO (e le correzioni), mai cosa
    ad = pezzo("apri_disputa")
    prova("la disputa racconta la busta senza aprirla", True,
          "nota_punto" in ad and "busta_correzioni" in ad
          and "_decifra_contenuto" not in ad)
    # il promemoria al posto del gate: popolazione e ancora giuste
    sb = pezzo("sollecita_buste_ferme").split('"""')[-1]
    prova("il promemoria pesca shipped+via_punto+busta assente", True,
          "o.stato='shipped' AND o.via_punto=1 AND o.busta_il=0" in sb)
    prova("...con l'ancora spedito_il e le colonne SUE", True,
          "MAX(o.spedito_il + ?" in sb and "sollecito_busta_il" in sb)
    prova("...ed e' agganciato all'orologio", 1,
          _SORGENTE.count("await sollecita_buste_ferme()"))
    prova("il libro mastro sorveglia la busta fuori contratto", True,
          "busta fuori contratto" in _SORGENTE)
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("client: bustaIl in mapOrder e pannello presente", True,
          "bustaIl:o.busta_il" in mini and "pannelloBustaRitiro" in mini)
    prova("client: nome e codice resi sotto esc()", True,
          "esc(b.nome)" in mini and "esc(b.codice)" in mini)
    prova("client: aprire la busta non chiede conferme", False,
          "confirm" in pezzo_js(mini, "async function mostraBusta"))

    # --- IL CODICE DENTRO IL BOTTONE (ago 2026, dal campo) ---------
    # Tre cose in un cantiere solo: la pagina non salta piu', il
    # codice nasce DOVE STAVA IL DITO, e toccandolo si copia.
    # IL SALTO NON ERA IL FUOCO, ed e' la parte da non riscrivere a
    # memoria: si sospettavano due cause — il focus() che trascina
    # (curato altrove con preventScroll) e il ridisegno che ricomincia
    # da capo. La spia su window.scrollTo ha dato lo stack, e diceva
    # mostraBusta -> openOrder -> go -> scrollTo(0, 0), da y=578 a
    # y=0; di focus() non ce n'era NESSUNA. Quindi la cura non e' un
    # preventScroll: e' non passare piu' da openOrder.
    mb = pezzo_js(mini, "async function mostraBusta")
    prova("il ridisegno della busta non passa da openOrder", False,
          "openOrder" in mb)
    prova("...e passa dal ridisegno del solo pannello", True,
          "ridisegnaBusta()" in mb)
    rb = pezzo_js(mini, "function ridisegnaBusta(){")
    prova("ridisegnaBusta riscrive UN nodo, mai la vista", True,
          "bustaPannello" in rb and "outerHTML" in rb
          and "openOrder" not in rb and "go(" not in rb)
    # l'ancora del nodo c'e' su TUTTI i pannelli che il costruttore
    # sa restituire: senza, il ridisegno non trova casa e il tocco
    # diventa muto proprio sul ramo che qualcuno aggiungera' domani
    prova("ogni pannello della busta porta la sua ancora", 3,
          mini.count('<div class="payout" id="bustaPannello">'))
    # LA TESTA NON CAMBIA: e' cio' che fa atterrare il piatto dove
    # stava il bottone. Se il ramo `b` avesse un return SUO — il nome
    # sopra e il codice sotto, com'era ieri — il piatto nascerebbe
    # piu' in basso e il gesto tornerebbe a «rivelare altrove».
    _pb = pezzo_js(mini, "function pannelloBustaRitiro(o){")
    _buy = _pb[_pb.index("if (o.role===\'buyer\'){"):_pb.index("/* venditore:")]
    prova("compratore: una testa sola, prima e dopo la rivelazione", 1,
          _buy.count("Depositate il ${quando}${corr}"))
    prova("...e il piatto sta nello slot del bottone", True,
          "${b ? piattoCodice(b, svelato)" in _buy)
    # con find(), non index(): una sentinella che ESPLODE quando la
    # riga sparisce e' rossa lo stesso, ma si porta dietro tutte le
    # prove che vengono dopo — e allora non si sa piu' quale ha
    # morso (visto in tortura, su due mutazioni su sedici)
    _i_p, _i_n = _buy.find("piattoCodice"), _buy.find("Nome del destinatario")
    prova("...col nome DOPO il codice (al banco serve prima il codice)",
          True, 0 <= _i_p < _i_n)
    # UN GESTO SOLO: il vecchio «Copia il codice» era un secondo
    # bottone per la stessa cosa, e adesso a copiare e' il codice
    prova("niente piu' un bottone-copia accanto al codice", False,
          ">📋 Copia il codice</button>" in mini)
    # L'ANELLO parte al GESTO e non a ogni ridisegno: la bandierina si
    # legge e si AZZERA nel costruttore (il patto di navSpingi)
    prova("l'impulso ha la sua bandierina, letta e azzerata", True,
          "const svelato = bustaSvelata === o.id;" in _pb
          and "if (svelato) bustaSvelata = 0;" in _pb)
    prova("...e la alza il gesto, non il render", True,
          "bustaSvelata = currentOrder.id;" in mb)
    prova("l'anello e' un keyframe SUO, non il verde delle promesse",
          True, "@keyframes impulsoCodice" in mini
          and ".codice-svelato{animation:impulsoCodice .5s" in mini)
    prova("...mezzo secondo, una volta sola", True,
          ".5s ease-out 1 both}" in mini)
    prova("...e reduced-motion lo SPEGNE, non lo ferma", (1, False),
          (mini.count(".codice-svelato{animation:none}"),
           "codice-svelato{animation-play-state" in mini))
    # il ripiego di copiaBusta promette «tieni premuto sul testo»:
    # senza la selezione dentro il bottone sarebbe una promessa falsa
    prova("il codice resta selezionabile a mano dentro il bottone",
          True, "user-select:all;-webkit-user-select:all}" in mini)
    # l'overlay diceva «Invio sats in corso» su una LETTURA
    prova("l'attesa non parla di sats: qui non se ne muove nessuno",
          True, "attesaRitardata(btn, \'Apro le istruzioni…\')" in mb)

    # --- L'ATTESA CHE ASPETTA (ago 2026, dal campo) ----------------
    # Il barattolino compariva e spariva: un segnale piu' corto di un
    # battito di ciglia si legge come un guasto, non come un'attesa.
    # Sotto pero' c'e' una richiesta VERA — nome e codice il server li
    # poppa da /api/orders apposta — quindi il segnale non si toglie:
    # si fa aspettare, la cura del velo dello stepper della pagina
    # Paga. Sotto la soglia non compare mai, oltre compare una volta.
    prova("la lettura non alza piu' il velo immediato", False,
          "bottoneInAttesa" in mb)
    _ar = pezzo_js(mini, "function attesaRitardata(btn, testo){")
    prova("l'attesa ritardata arma un timer e non tocca subito il DOM",
          True, "setTimeout(" in _ar
          and _ar.index("setTimeout(") < _ar.index("classList.add('on')"))
    prova("...e il ripristino lo ANNULLA (mai un velo dopo la risposta)",
          True, "clearTimeout(t);" in _ar and "if (!acceso) return;" in _ar)
    # lo stesso numero del velo del ±: due soglie da tenere in pari
    # direbbero due attese diverse per la stessa idea
    prova("il ritardo e' quello del velo dello stepper", (True, True),
          ("const RITARDO_ATTESA = 180;" in mini, "}, 180);" in mini))
    # IL CENSIMENTO: la ritardata NON si usa dove si muovono i sats —
    # li' il velo immediato e' la guardia contro il secondo tocco su
    # una cosa irreversibile. Definizione + l'unico chiamante.
    prova("l'attesa ritardata ha un chiamante solo, ed e' una lettura",
          2, mini.count("attesaRitardata("))
    # e la guardia del doppio tocco e' una bandierina in memoria: col
    # velo ritardato il bottone resta vivo per 180ms, e due letture
    # rialzerebbero `bustaSvelata` facendo ripartire l'anello su un
    # piatto gia' svelato (disabilitarlo sarebbe un altro lampo)
    prova("il doppio tocco lo ferma una bandierina, non il bottone",
          (True, False),
          ("if (bustaInCorso) return;" in mb and "bustaInCorso = true;" in mb,
           "disabled" in mb))

    # E SI FA GIRARE ANCHE L'ATTESA, che una sentinella sulla forma
    # dice che il timer c'e', mai che il velo resti spento quando la
    # risposta e' svelta — ed e' precisamente quello il difetto da cui
    # nasce il cantiere. Due scenari sullo stesso pezzo vero, con
    # timer VERI: la risposta prima della soglia non deve accendere
    # niente, quella dopo deve accendere UNA volta e poi spegnere,
    # rimettendo al bottone l'etichetta di prima.
    import json as _js4, shutil as _sh4, subprocess as _sp4, tempfile as _tf4
    _node4 = _sh4.which("node")
    if not _node4:
        salta("l'attesa ritardata risponde giusto", "node non installato")
    else:
        _sog = int(re.search(r"const RITARDO_ATTESA = (\d+);", mini).group(1))
        _ar_js = pezzo_js(mini, "const RITARDO_ATTESA = ", "\n\n")
        _banco = ("const registro = [];\n"
                  "const finti = {attesaTesto:{textContent:''},"
                  " attesaOverlay:{classList:{"
                  "  add:()=>registro.push('acceso'),"
                  "  remove:()=>registro.push('spento')}}};\n"
                  "const el = id => finti[id];\n")
        _prog4 = (_banco + _ar_js + "\n"
                  "const dorme = ms => new Promise(r=>setTimeout(r, ms));\n"
                  "(async ()=>{\n"
                  "  const esito = [];\n"
                  f"  for (const ms of [20, {_sog} + 140]) {{\n"
                  "    registro.length = 0;\n"
                  "    const btn = {innerHTML:'👁 Mostra il codice', disabled:false};\n"
                  "    const ripristina = attesaRitardata(btn, 'Apro le istruzioni…');\n"
                  "    await dorme(ms);\n"
                  "    ripristina();\n"
                  f"    await dorme({_sog} + 120);\n"
                  "    esito.push({velo: registro.join('+'),"
                  "      etichetta: btn.innerHTML, spento: btn.disabled});\n"
                  "  }\n"
                  "  console.log(JSON.stringify(esito));\n"
                  "})();")
        _f4 = _tf4.NamedTemporaryFile("w", suffix=".js", delete=False,
                                      encoding="utf-8")
        _f4.write(_prog4)
        _f4.close()
        _r4 = _sp4.run([_node4, _f4.name], capture_output=True, text=True,
                       timeout=60, encoding="utf-8")
        os.unlink(_f4.name)
        prova("l'attesa ritardata: muta se la risposta e' svelta, una "
              "volta sola se e' lenta, e il bottone torna com'era",
              [{"velo": "", "etichetta": "👁 Mostra il codice",
                "spento": False},
               {"velo": "acceso+spento", "etichetta": "👁 Mostra il codice",
                "spento": False}],
              _js4.loads(_r4.stdout.strip()) if _r4.returncode == 0
              else f"ERRORE: {_r4.stderr[:160]}")

    # E SI FA GIRARE, che le sentinelle qui sopra dicono che il piatto
    # ESISTE, mai che risponda giusto (la lezione presa sette volte).
    import json as _js3, shutil as _sh3, subprocess as _sp3, tempfile as _tf3
    _node3 = _sh3.which("node")
    if not _node3:
        salta("piattoCodice risponde giusto", "node non installato")
    else:
        _esc = mini[mini.index("const esc = s =>"):
                    mini.index("const el = id =>")]
        _pc = pezzo_js(mini, "function piattoCodice(b, svelato){", "\n}") + "\n}"
        _prog = (_esc + _pc + "\nconst casi = ["
                 "piattoCodice({codice:'8842-7193'}, true),"
                 "piattoCodice({codice:'8842-7193'}, false),"
                 "piattoCodice({codice:''}, true),"
                 "piattoCodice({codice:'<b>X</b>'}, false)];"
                 "console.log(JSON.stringify(casi.map(h => ({"
                 "  vuoto: h === '',"
                 "  anello: h.includes('codice-svelato'),"
                 "  copia: h.includes('onclick=\"copiaBusta()\"'),"
                 "  parola: h.includes('Tocca per copiare'),"
                 "  crudo: h.includes('<b>X')}))));")
        _f3 = _tf3.NamedTemporaryFile("w", suffix=".js", delete=False,
                                      encoding="utf-8")
        _f3.write(_prog)
        _f3.close()
        _r3 = _sp3.run([_node3, _f3.name], capture_output=True, text=True,
                       timeout=60, encoding="utf-8")
        os.unlink(_f3.name)
        prova("piattoCodice: anello solo al gesto, copia sempre, "
              "codice vuoto = niente piatto",
              [{"vuoto": False, "anello": True, "copia": True,
                "parola": True, "crudo": False},
               {"vuoto": False, "anello": False, "copia": True,
                "parola": True, "crudo": False},
               {"vuoto": True, "anello": False, "copia": False,
                "parola": False, "crudo": False},
               {"vuoto": False, "anello": False, "copia": True,
                "parola": True, "crudo": False}],
              _js3.loads(_r3.stdout.strip()) if _r3.returncode == 0
              else f"ERRORE: {_r3.stderr[:160]}")

    # --- il funzionale su sqlite in memoria -------------------------
    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    vero = sqlite3.connect(":memory:")
    vero.row_factory = sqlite3.Row
    vero.executescript("""
      CREATE TABLE ordini(
        id INTEGER PRIMARY KEY, compratore_id INT, venditore_id INT,
        stato TEXT, consegna_scelta TEXT DEFAULT 'spedizione',
        via_punto INT DEFAULT 0, punto_ritiro TEXT DEFAULT '',
        corriere TEXT DEFAULT '', tracking TEXT DEFAULT '',
        spedito_il INT DEFAULT 0, aggiornato INT DEFAULT 0,
        consegnato INT DEFAULT 0, annuncio_id INT DEFAULT 1,
        prezzo_sats INT DEFAULT 1000,
        busta_nome TEXT DEFAULT '', busta_codice TEXT DEFAULT '',
        busta_il INT DEFAULT 0, busta_corretta_il INT DEFAULT 0,
        busta_correzioni INT DEFAULT 0,
        busta_file TEXT DEFAULT '', busta_file_tipo TEXT DEFAULT '',
        busta_file_nome TEXT DEFAULT '',
        indirizzo TEXT DEFAULT '', indirizzo_il INT DEFAULT 0,
        indirizzo_atteso INT DEFAULT 0,
        sollecito_busta_il INT DEFAULT 0, solleciti_busta INT DEFAULT 0);
      CREATE TABLE annunci(id INTEGER PRIMARY KEY, titolo TEXT,
        asta_base_sats INT DEFAULT 0);
      INSERT INTO annunci(id, titolo) VALUES(1, 'Un oggetto');
      -- 1: via punto, gia' spedito (il caso normale del deposito)
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        via_punto, punto_ritiro, spedito_il)
        VALUES(1, 111, 222, 'shipped', 1, 'Locker InPost', 1000);
      -- 2: spedizione a casa (la busta non c'entra)
      INSERT INTO ordini(id, compratore_id, venditore_id, stato)
        VALUES(2, 111, 222, 'shipped');
      -- 3: via punto ancora 'locked' (il caso del codice immediato)
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        via_punto, punto_ritiro)
        VALUES(3, 111, 222, 'locked', 1, 'Punto Poste');
    """)
    vero.commit()

    class Con:
        def execute(self, *a):
            return vero.execute(*a)

        def commit(self):
            vero.commit()

        def close(self):
            pass

    avvisi = []

    async def _notifica(tg, testo):
        avvisi.append((tg, testo))

    class _Req:
        def __init__(self, d):
            self._d = d

    async def _leggi(req):
        return req._d

    def _amb(chi):
        amb = {"db": Con, "HTTPException": _H, "Request": object,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi},
               "leggi_json": _leggi, "notifica": _notifica,
               "hashlib": __import__("hashlib"), "time": _t,
               "html": __import__("html"),   # segna_spedito scappa i suoi
               "CHIAVE_CONTENUTI_DIGITALI": "", "Fernet": None,
               "MSG_BUSTA_PRONTA": "TI-ASPETTA",
               # il documento di ritiro: cartella usa-e-getta, cosi'
               # la prova scrive davvero un file e lo si puo' guardare
               "os": __import__("os"), "re": __import__("re"),
               "base64": __import__("base64"),
               "secrets": __import__("secrets"),
               "BUSTE_DIR": buste_dir, "MAX_DOC_BUSTA": 15 * 1024 * 1024,
               "_e_immagine": lambda raw: True}
        exec(pezzo("_cifra_contenuto"), amb)
        exec(pezzo("_decifra_contenuto"), amb)
        exec(pezzo("_cifra_blob"), amb)
        exec(pezzo("_decifra_blob"), amb)
        exec(_firme_doc, amb)
        exec(pezzo("_documento_busta"), amb)
        exec(pezzo("_etichetta_documento"), amb)
        return amb

    def corri(amb, nome, *args):
        try:
            return asyncio.new_event_loop().run_until_complete(
                amb[nome](*args))
        except _H as e:
            return f"{e.code} {e.detail}"

    def deposita(chi, oid, body):
        amb = _amb(chi)
        exec("async " + pezzo("deposita_busta_ritiro"), amb)
        return corri(amb, "deposita_busta_ritiro", oid, _Req(body))

    def leggi(chi, oid):
        amb = _amb(chi)
        exec("async " + pezzo("leggi_busta_ritiro"), amb)
        return corri(amb, "leggi_busta_ritiro", oid)

    busta = {"nome": "Mario Rossi", "codice": "PIN 4321"}
    prova("il compratore non deposita", "400 Operazione non permessa",
          deposita(111, 1, busta))
    prova("l'estraneo nemmeno", "400 Operazione non permessa",
          deposita(999, 1, busta))
    prova("niente busta fuori dalla via punto", True,
          str(deposita(222, 2, busta)).startswith("400 Questo ordine"))
    prova("il nome serve sempre", True,
          str(deposita(222, 1, {"codice": "PIN"})).startswith(
              "400 Serve il nome"))
    prova("...e poi una strada: senza codice ne' documento, no", True,
          str(deposita(222, 1, {"nome": "Mario"})).startswith(
              "400 Serve il codice"))
    prima = [tuple(r) for r in vero.execute(
        "SELECT stato, spedito_il, consegnato, aggiornato FROM ordini")]
    r1 = deposita(222, 1, busta)
    prova("il deposito riesce e timbra busta_il", True,
          isinstance(r1, dict) and r1["busta_il"] > 0)
    o1 = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
    prova("nel DB il codice non e' nudo... e' il trasporto di casa",
          True, o1["busta_codice"].startswith("plain:")
          and o1["busta_nome"].startswith("plain:"))
    prova("l'escrow non si e' mosso di un millimetro", prima,
          [tuple(r) for r in vero.execute(
              "SELECT stato, spedito_il, consegnato, aggiornato "
              "FROM ordini")])
    prova("a pacco in viaggio parte il «ti aspetta», una volta",
          [(111, "TI-ASPETTA")], avvisi)
    avvisi.clear()
    primo_timbro = o1["busta_il"]
    deposita(222, 1, {"nome": "Mario Rossi", "codice": "PIN 9999"})
    o1 = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
    prova("la correzione NON riscrive il primo deposito", primo_timbro,
          o1["busta_il"])
    prova("...ma si conta e si timbra", True,
          o1["busta_correzioni"] == 1
          and o1["busta_corretta_il"] >= primo_timbro)
    prova("...e l'avviso e' quello statico dell'aggiornamento", True,
          len(avvisi) == 1 and "aggiornate" in avvisi[0][1])
    avvisi.clear()
    # il caso del codice immediato: deposito su 'locked' SILENZIOSO...
    deposita(222, 3, busta)
    prova("su 'locked' il deposito tace (parlera' segna_spedito)",
          [], avvisi)
    # ...e il segnale d'arrivo parte da segna_spedito, senza doppione
    amb = _amb(222)
    exec("async " + pezzo("segna_spedito"), amb)
    corri(amb, "segna_spedito", 3,
          _Req({"corriere": "InPost", "tracking": "1234567890"}))
    prova("segna_spedito col codice gia' li': UN «ti aspetta»",
          [(111, "TI-ASPETTA")], avvisi)
    prova("...e l'ordine e' spedito davvero", "shipped",
          vero.execute("SELECT stato FROM ordini "
                       "WHERE id=3").fetchone()["stato"])
    avvisi.clear()
    # la lettura: le parti si', l'estraneo e l'inesistente uguali,
    # e il database non cambia di un byte
    dump = [tuple(r) for r in vero.execute(
        "SELECT * FROM ordini ORDER BY id")]
    letto = leggi(111, 1)
    prova("il compratore legge nome e codice in chiaro", True,
          isinstance(letto, dict) and letto["nome"] == "Mario Rossi"
          and letto["codice"] == "PIN 9999")
    prova("il venditore rilegge cio' che ha depositato", True,
          isinstance(leggi(222, 1), dict))
    prova("estraneo e ordine inesistente rispondono uguale", True,
          leggi(999, 1) == leggi(111, 777))
    prova("l'ordine senza busta e' un 404 onesto", True,
          str(leggi(111, 2)).startswith("404"))
    prova("la lettura non scrive NIENTE (la prova regina)", dump,
          [tuple(r) for r in vero.execute(
              "SELECT * FROM ordini ORDER BY id")])

    # --- il documento di ritiro: l'altra strada per il codice --------
    # (ago 2026: un PIN si trascrive, un QR no)
    import base64 as _b64
    import os as _os
    PDF = "data:application/pdf;base64," + _b64.b64encode(
        b"%PDF-1.4 finto ma con la firma giusta").decode()
    JPG = "data:image/jpeg;base64," + _b64.b64encode(
        b"\xff\xd8\xff finto").decode()
    prova("il tipo lo dicono i BYTE, non l'etichetta", True,
          str(deposita(222, 1, {"nome": "Mario", "codice": "P",
                                "file": "data:image/jpeg;base64," +
                                _b64.b64encode(b"%PDF- travestito"
                                               ).decode()})
              ).startswith("400") is False
          # il PDF travestito da jpeg entra COME PDF, non come foto
          and vero.execute("SELECT busta_file_tipo FROM ordini WHERE "
                           "id=1").fetchone()[0] == "application/pdf")
    prova("cio' che non si riconosce non entra", True,
          str(deposita(222, 1, {"nome": "Mario", "codice": "P",
                                "file": "data:text/plain;base64," +
                                _b64.b64encode(b"ciao").decode()})
              ).startswith("400 Si possono caricare"))
    prova("il troppo pesante lo dice, non tronca", True,
          str(deposita(222, 1, {"nome": "Mario", "codice": "P",
                                "file": "data:image/jpeg;base64," +
                                _b64.b64encode(b"\xff\xd8\xff" +
                                               b"x" * (16 * 1024 * 1024)
                                               ).decode()})
              ).startswith("400 Il documento è troppo pesante"))
    avvisi.clear()
    deposita(222, 1, {"nome": "Mario Rossi", "codice": "",
                      # il nome del file lo scrive il telefono del
                      # venditore e finisce nel Content-Disposition:
                      # il percorso lo toglie il basename, la
                      # VIRGOLETTA e l'a-capo solo la ripulitura — e
                      # una virgoletta li' dentro spezza l'header
                      "file": JPG,
                      "file_nome": '../etc/qr "locker"\n.jpg'})
    o1 = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
    prova("il documento basta da solo: niente codice, e passa", True,
          bool(o1["busta_file"]) and o1["busta_codice"] == "plain:")
    prova("il nome del file e' ripulito (percorso, virgolette, a capo)",
          "qr locker.jpg", o1["busta_file_nome"])
    prova("il nome sul disco non si indovina dall'ordine", True,
          o1["busta_file"].startswith("b1_")
          and len(o1["busta_file"]) > 12)
    su_disco = _os.path.join(buste_dir, o1["busta_file"])
    grezzi = open(su_disco, "rb").read()
    prova("sul disco NON c'e' un JPEG nudo: c'e' il trasporto di casa",
          True, grezzi.startswith(b"plain:")
          and not grezzi.startswith(b"\xff\xd8\xff"))
    prova("...e i byte tornano indietro interi", True,
          _amb(222)["_decifra_blob"](grezzi).startswith(b"\xff\xd8\xff"))
    letto = leggi(111, 1)
    prova("la lettura dice che c'e', il nome e il tipo", True,
          letto["documento"] is True and letto["documento_tipo"]
          == "image/jpeg" and letto["documento_nome"] == "qr locker.jpg")
    prova("...ma MAI il nome sul disco (e' la maniglia, non un dato)",
          [], [k for k, v in letto.items()
               if isinstance(v, str) and v == o1["busta_file"]])
    vecchio = o1["busta_file"]
    deposita(222, 1, {"nome": "Mario Rossi", "codice": "", "file": PDF})
    o1 = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
    prova("il documento nuovo si porta via il vecchio", True,
          o1["busta_file"] != vecchio
          and not _os.path.exists(_os.path.join(buste_dir, vecchio)))
    prova("...e il tipo lo segue", "application/pdf",
          o1["busta_file_tipo"])
    resta = o1["busta_file"]
    deposita(222, 1, {"nome": "Mario Rossi", "codice": "PIN 1"})
    prova("chiave assente = si CONSERVA (il patto dello stock)", resta,
          vero.execute("SELECT busta_file FROM ordini "
                       "WHERE id=1").fetchone()[0])
    prova("togliere e' un gesto ESPLICITO", "",
          (deposita(222, 1, {"nome": "Mario Rossi", "codice": "PIN 1",
                             "file_togli": 1}),
           vero.execute("SELECT busta_file FROM ordini "
                        "WHERE id=1").fetchone()[0])[1])
    prova("...e col documento tolto il file sparisce dal disco", False,
          _os.path.exists(_os.path.join(buste_dir, resta)))
    prova("togliere l'ultima strada rimasta, no", True,
          str(deposita(222, 1, {"nome": "Mario", "codice": "",
                                "file_togli": 1})
              ).startswith("400 Serve il codice"))

    # --- la rotta dei byte, girata PER DAVVERO -----------------------
    # e' la rotta che consegna la credenziale di ritiro: una sentinella
    # sul testo dice che le righe ci sono, non che escono i byte giusti
    # a chi di dovere. `Response` di cartone, il resto e' il pezzo vero.
    class _Resp:
        def __init__(self, content=None, media_type="", headers=None):
            self.content, self.media_type = content, media_type
            self.headers = headers or {}

    deposita(222, 1, {"nome": "Mario Rossi", "codice": "",
                      "file": JPG, "file_nome": "qr.jpg"})

    def byte(chi, oid):
        amb = _amb(chi)
        amb["Response"] = _Resp
        exec("async " + pezzo("leggi_documento_busta"), amb)
        return corri(amb, "leggi_documento_busta", oid)

    veri = _b64.b64decode(JPG.split(",", 1)[1])
    r = byte(111, 1)
    prova("il compratore riceve i byte VERI, decifrati", True,
          isinstance(r, _Resp) and r.content == veri)
    prova("...col tipo che il venditore ha caricato", "image/jpeg",
          r.media_type)
    prova("...e senza cache: una copia e' una copia del codice", True,
          "no-store" in r.headers.get("Cache-Control", ""))
    prova("il venditore rilegge il suo", True,
          isinstance(byte(222, 1), _Resp))
    prova("l'estraneo e l'ordine inesistente rispondono UGUALE", True,
          byte(999, 1) == byte(111, 777) == "400 Operazione non permessa")
    prova("l'ordine senza documento e' un 404 onesto", True,
          str(byte(111, 2)).startswith("404"))
    dump = [tuple(x) for x in vero.execute(
        "SELECT * FROM ordini ORDER BY id")]
    byte(111, 1); byte(111, 1)
    prova("aprire il documento non scrive NIENTE (non e' una ricevuta)",
          dump, [tuple(x) for x in vero.execute(
              "SELECT * FROM ordini ORDER BY id")])
    # il file sparito da sotto: si dice, non si consegnano byte rotti
    _os.remove(_os.path.join(buste_dir, vero.execute(
        "SELECT busta_file FROM ordini WHERE id=1").fetchone()[0]))
    prova("documento sparito dal disco: 503 onesto, mai byte a caso",
          True, str(byte(111, 1)).startswith("503"))
    shutil.rmtree(buste_dir, ignore_errors=True)
    avvisi.clear()   # i depositi qui sopra hanno avvisato: chi viene
                     # dopo conta i SUOI squilli, non i nostri

    # la rotta dei byte: le stesse regole della busta, riga per riga
    fil = pezzo("leggi_documento_busta").split('"""')[-1]
    prova("i byte: solo le due parti, mai l'admin", True,
          "(compratore_id=? OR venditore_id=?)" in fil
          and "e_admin" not in fil)
    prova("i byte: l'autorizzazione PRIMA dell'esistenza", True,
          fil.index("Operazione non permessa")
          < fil.index("Nessun documento"))
    prova("i byte: GET puro, nessuna scrittura", [],
          [x for x in ("UPDATE", "INSERT", "commit()") if x in fil])
    prova("i byte non si mettono MAI in cache", True,
          "no-store" in fil)
    prova("...e non si eseguono: nosniff e sandbox", True,
          "nosniff" in fil and "sandbox" in fil)
    prova("i documenti NON stanno in foto/", True,
          "BUSTE_DIR" in fil and "FOTO_DIR" not in fil
          and "BUSTE_DIR" in dep and "FOTO_DIR" not in dep)
    prova("nessuna rotta serve la cartella dei documenti", 0,
          _SORGENTE.count('"/buste'))
    prova("dal client il documento viaggia col flag e basta", True,
          'r.pop("busta_file_tipo"' in mo and 'r.pop("busta_file_nome"'
          in mo and 'r.pop("busta_file", "")' in mo)

    # --- il promemoria al posto del gate -----------------------------
    vero.execute("INSERT INTO ordini(id, compratore_id, venditore_id, "
                 "stato, via_punto, spedito_il) "
                 "VALUES(9, 111, 222, 'shipped', 1, ?)",
                 (int(_t.time()) - 4 * 86400,))
    vero.commit()
    amb = {"db": Con, "notifica": _notifica,
           "notifica_admin": _notifica_admin_spia(avvisi),
           "_titolo_ordine": lambda righe: "un set",
           "html": __import__("html"),
           "_fmt_sats": lambda n: str(n), "time": _t,
           "PROMEMORIA_BUSTA_GIORNI": 3, "PROMEMORIA_CONFERMA_GIORNI": 3,
           "PROMEMORIA_CONFERMA_MAX": 3}
    exec("async " + pezzo("sollecita_buste_ferme"), amb)
    asyncio.new_event_loop().run_until_complete(
        amb["sollecita_buste_ferme"]())
    prova("a 4 giorni senza busta squilla il SOLO venditore",
          [222], [a[0] for a in avvisi])
    avvisi.clear()
    asyncio.new_event_loop().run_until_complete(
        amb["sollecita_buste_ferme"]())
    prova("e non ribussa subito: la cadenza e' delle sorelle", [], avvisi)
    amb["PROMEMORIA_BUSTA_GIORNI"] = 0
    vero.execute("UPDATE ordini SET sollecito_busta_il=0, "
                 "solleciti_busta=0 WHERE id=9")
    vero.commit()
    asyncio.new_event_loop().run_until_complete(
        amb["sollecita_buste_ferme"]())
    prova("la leva a 0 spegne la popolazione", [], avvisi)
    vero.close()


def prove_indirizzo_casa():
    """L'INDIRIZZO DI CASA (ago 2026): lo SPECCHIO della busta — li'
    scrive il venditore e legge il compratore, qui il contrario.
    Barattolo non lo conserva, lo TRASPORTA: la scopa lo cancella una
    finestra dopo la chiusura, ed e' quella riga a rendere vera la
    promessa scritta nella pagina pubblica."""
    print("\n[l'indirizzo di casa]")
    import asyncio
    import sqlite3
    import time as _t

    src = _SORGENTE
    giu = pezzo("_indirizzo_da_payload").split('"""')[-1]
    post = pezzo("indica_indirizzo").split('"""')[-1]
    get = pezzo("leggi_indirizzo").split('"""')[-1]
    sped = pezzo("segna_spedito").split('"""')[-1]
    scopa = pezzo("pulisci_indirizzi").split('"""')[-1]

    # --- le sentinelle di forma ------------------------------------
    prova("il giudice CIFRA lui: un posto solo, tre chiamanti", 1,
          giu.count("_cifra_contenuto("))
    prova("...e la chiave manca = 503, mai un'anagrafica in chiaro",
          True, "503" in giu and "MODALITA_COLLAUDO" in giu)
    prova("...la dichiarazione e' la PRESENZA della chiave", True,
          '"indirizzo" not in d' in giu)
    prova("...e i 400 non rimandano mai il valore scritto", 0,
          giu.count("{valore"))
    # il lettore difensivo: _decifra_contenuto e' fail-open e su una
    # chiave cambiata restituisce PROSA, che non e' JSON — senza il
    # try, riaprire un ordine sarebbe un 500 per tutte e due le parti
    prova("il lettore para il parse (la prosa non e' JSON)", True,
          "except Exception" in pezzo("_indirizzo_letto"))
    prova("il deposito e' del COMPRATORE, su 'locked'", True,
          "compratore_id=?" in post and "'locked'" in post)
    prova("...ed esige la spedizione a casa", True,
          'o["via_punto"]' in post and "consegna_scelta" in post)
    prova("...il vuoto si rifiuta: si corregge, non si svuota", True,
          "if not ind:" in post)
    prova("...UN solo UPDATE, e tocca solo le colonne indirizzo", 1,
          post.count("UPDATE"))
    # (si guarda l'UPDATE e non tutto il corpo: 'locked' nella SELECT
    #  e' la GUARDIA, non una scrittura — la sentinella larga
    #  scambiava le due cose)
    _set = post[post.index("UPDATE ordini SET"):post.index("WHERE id=?")]
    prova("...non tocca stato, aggiornato, consegnato", [],
          [x for x in ("stato=", "aggiornato=", "consegnato=")
           if x in _set])
    prova("...e la notifica al venditore e' STATICA", [],
          [x for x in ("{ind", "{corpo", "{dati") if x in post])
    prova("...il journal non porta il testo, solo il fatto", False,
          "{ind}" in post)
    # il GET: puro, delle due parti, e l'admin mai
    prova("lettura: GET puro, nessuna scrittura", [],
          [x for x in ("UPDATE", "INSERT", "commit") if x in get])
    prova("lettura: l'admin non ha strada", False, "e_admin" in get)
    prova("lettura: autorizzazione PRIMA dell'esistenza", True,
          "compratore_id=? OR venditore_id=?" in get
          and get.index("Operazione non permessa")
          < get.index("Nessun indirizzo"))
    prova("lettura: il purgato lo DICE, non finge un vuoto", True,
          "indirizzo_purgato_il" in get and "cancellato il" in get)
    # il gate: ancorato all'attesa e MAI alla via, o al primo riavvio
    # bloccherebbe ogni ordine 'locked' gia' in corso
    prova("il gate guarda indirizzo_atteso, non la via", True,
          'o["indirizzo_atteso"] and not o["indirizzo_il"]' in sped)
    # LA RIPRESA: l'indirizzo NON entra nel confronto «stessa
    # richiesta», e non e' una svista — Fernet non e' deterministico
    # (IV casuale), quindi due blob dello stesso indirizzo sono sempre
    # diversi e `stessa` sarebbe falsa per sempre: ogni secondo tocco
    # su «Paga» conierebbe una fattura nuova. E senza chiave i blob
    # sono 'plain:', quindi funzionerebbe in collaudo e si romperebbe
    # in produzione. Ma va RISCRITTO, o chi corregge un refuso si
    # rivede la fattura con l'indirizzo di prima.
    _compra = pezzo("compra")
    _rip = _compra[_compra.index("stessa = ("):_compra.index("# Rinnovo")]
    prova("la ripresa non confronta il blob cifrato", False,
          'mio["indirizzo"] ==' in _rip
          or '== mio["indirizzo"]' in _rip)
    prova("...ma riscrive l'indirizzo cambiato", True,
          'ind != mio["indirizzo"]' in _rip
          and "UPDATE ordini SET indirizzo=?" in _rip)
    # la scopa
    prova("la scopa non riscrive tutto il database ogni giro", 2,
          scopa.count("indirizzo<>'' AND indirizzo_purgato_il=0"))
    prova("...e NON tocca `aggiornato` (l'ancora dei fermi)", False,
          "aggiornato=" in scopa)
    prova("...solo gli stati assorbenti, mai un ordine vivo", True,
          "('released','refunded')" in scopa)
    # LE DUE VELOCITA': la corsia veloce guarda `disputata` e mai
    # `consegnato` — conferma_ricezione accetta anche 'locked' e
    # 'shipped', quindi quasi nessuno passa da 'delivered' (misurato:
    # 14 released su 14 col campo a zero) e una purga ancorata li' non
    # scatterebbe quasi mai, credendo di essere piu' severa.
    prova("la corsia veloce guarda la disputa, non `consegnato`", True,
          "disputata=0" in scopa and "consegnato" not in scopa)
    # ...ed e' gated sulla leva: a auto-sblocco riacceso «released e
    # non disputato» comprende anche gli sblocchi automatici, dove
    # nessuno ha confermato niente
    prova("...ed e' spenta se l'auto-sblocco torna", True,
          "if not AUTO_SBLOCCO_ATTIVO:" in scopa)
    # la RIGA intera e con la sua indentazione, o la definizione
    # («def pulisci_indirizzi():») entrerebbe nel conto e un
    # «pass  # pulisci_indirizzi()» la lascerebbe verde: la lezione
    # della sentinella del reaper
    prova("...ed e' agganciata all'orologio", 1,
          src.count("\n            pulisci_indirizzi()"))
    # le strade del denaro non sanno che esiste
    for nome in ("_sblocca_sats", "_rimborsa_compratore"):
        prova(f"{nome} e' cieco all'indirizzo", False,
              "indirizzo" in pezzo(nome))
    prova("lo strip di /api/orders copre l'indirizzo", True,
          'r.pop("indirizzo"' in pezzo("miei_ordini"))
    prova("la disputa racconta l'indirizzo senza aprirlo", True,
          "nota_indirizzo" in pezzo("apri_disputa"))
    prova("il libro mastro sorveglia la promessa mantenuta", True,
          "indirizzo fuori contratto" in src)
    prova("il numero dei giorni viaggia al CLIENT", True,
          'risposta["giorni_indirizzo"]' in src)
    # LA STESSA REGOLA PER LA DEDUP DEGLI AVVISI (ago 2026): era un 30
    # scritto a mano dentro la scopa, e da quando la pagina «I tuoi
    # dati» dice per quanto teniamo le cose quel numero deve avere UN
    # posto solo — se un domani cambia, la pagina non deve mentire.
    scopa = pezzo("pulisci_avvisi")
    prova("la dedup degli avvisi ha una durata con un nome", True,
          "GIORNI_DEDUP_AVVISI = 30" in _SORGENTE
          and "GIORNI_DEDUP_AVVISI * 86400" in scopa)
    prova("...e nessun numero di giorni battuto a mano nella scopa",
          None, re.search(r"\d+\s*\*\s*86400", scopa))
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("client: il pannello si gatea sull'attesa, mai sulla via",
          True, "o.indirizzoAtteso || o.indirizzoIl" in mini)
    prova("client: i campi hanno i token dell'autofill", True,
          "address-line1" in mini and "postal-code" in mini
          and "address-level2" in mini)
    prova("client: e stanno in un <form>, che l'autofill preferisce",
          True, 'onsubmit="return false" class="ind-form"' in mini)
    prova("client: i sei campi si rendono sotto esc()", True,
          "esc(v[c.k]||'')" in mini and "esc(iVal[c.k]||'')" in mini)
    prova("client: la pagina non hardcoda i giorni", True,
          "data-giorni-ind" in mini and "scriviGiorniIndirizzo" in mini)
    prova("client: la guardia di «Paga» APRE prima del fuoco", True,
          "apriIndirizzoAcquisto();" in mini)

    # --- il funzionale: gli endpoint VERI su un database vero -------
    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    vero = sqlite3.connect(":memory:")
    vero.row_factory = sqlite3.Row
    vero.executescript("""
      CREATE TABLE ordini(
        id INTEGER PRIMARY KEY, compratore_id INT, venditore_id INT,
        stato TEXT, consegna_scelta TEXT DEFAULT 'spedizione',
        via_punto INT DEFAULT 0, aggiornato INT DEFAULT 0,
        spedito_il INT DEFAULT 0, consegnato INT DEFAULT 0,
        indirizzo TEXT DEFAULT '', indirizzo_il INT DEFAULT 0,
        indirizzo_corretto_il INT DEFAULT 0,
        indirizzo_correzioni INT DEFAULT 0,
        indirizzo_purgato_il INT DEFAULT 0,
        indirizzo_atteso INT DEFAULT 0, disputata INT DEFAULT 0);
      -- 1: spedizione a casa, in attesa dell'indirizzo
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        indirizzo_atteso) VALUES(1, 111, 222, 'locked', 1);
      -- 2: la via del locker, che di indirizzi non ne vuole
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        via_punto) VALUES(2, 111, 222, 'locked', 1);
      -- 3: chiuso da un pezzo, con l'indirizzo ancora dentro
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        indirizzo, indirizzo_il, aggiornato)
        VALUES(3, 111, 222, 'released', 'plain:{}', 500, 1000);
      -- 4: chiuso IERI da una DISPUTA (rispetto all'adesso finto della
      --    scopa, che e' 9_000_000_000): nessuna conferma del
      --    compratore, quindi vale la finestra e oggi resta
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        indirizzo, indirizzo_il, aggiornato, disputata)
        VALUES(4, 111, 222, 'released', 'plain:{}', 500, 8999913600, 1);
      -- 5: chiuso IERI dalla CONFERMA del compratore: la corsia
      --    veloce lo prende comunque, la finestra non c'entra
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        indirizzo, indirizzo_il, aggiornato)
        VALUES(5, 111, 222, 'released', 'plain:{}', 500, 8999913600);
      -- 6: RIMBORSATO ieri: nessuno ha confermato niente, finestra
      INSERT INTO ordini(id, compratore_id, venditore_id, stato,
        indirizzo, indirizzo_il, aggiornato)
        VALUES(6, 111, 222, 'refunded', 'plain:{}', 500, 8999913600);
    """)
    vero.commit()

    class Con:
        def execute(self, q, p=()):
            return vero.execute(q, p)

        def commit(self):
            vero.commit()

        def close(self):
            pass

    avvisi = []

    async def _notifica(tg, testo):
        avvisi.append((tg, testo))

    class _Req:
        def __init__(self, d):
            self._d = d

    async def _leggi(req):
        return req._d

    def _campi_ind():
        """Il catalogo dei campi si estrae per TESTO come le altre
        costanti (FIRME_DOC_BUSTA docet): una copia scritta a mano qui
        giudicherebbe una tabella diversa da quella vera."""
        i = src.index("CAMPI_INDIRIZZO = (")
        return src[i:src.index("\n)\n", i) + 3]

    def _amb(chi, collaudo=True):
        amb = {"db": Con, "HTTPException": _H, "Request": object,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi},
               "leggi_json": _leggi, "notifica": _notifica,
               "time": _t, "json": __import__("json"),
               "CHIAVE_CONTENUTI_DIGITALI": "", "Fernet": None,
               "MODALITA_COLLAUDO": collaudo}
        exec(pezzo("_cifra_contenuto"), amb)
        exec(pezzo("_decifra_contenuto"), amb)
        exec(_campi_ind(), amb)
        exec(pezzo("_indirizzo_da_payload"), amb)
        exec(pezzo("_indirizzo_letto"), amb)
        return amb

    def corri(amb, nome, *args):
        try:
            return asyncio.new_event_loop().run_until_complete(
                amb[nome](*args))
        except _H as e:
            return f"{e.code} {e.detail}"

    def scrivi(chi, oid, body, collaudo=True):
        amb = _amb(chi, collaudo)
        exec("async " + pezzo("indica_indirizzo"), amb)
        return corri(amb, "indica_indirizzo", oid, _Req(body))

    def leggi(chi, oid):
        amb = _amb(chi)
        exec("async " + pezzo("leggi_indirizzo"), amb)
        return corri(amb, "leggi_indirizzo", oid)

    pieno = {"indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                           "cap": "27100", "citta": "Pavia",
                           "provincia": "PV", "telefono": "333 111",
                           "note": "Citofono Rossi"}}
    prova("il venditore non lo scrive", "400 Operazione non permessa",
          scrivi(222, 1, pieno))
    prova("l'estraneo nemmeno, e con la STESSA risposta",
          "400 Operazione non permessa", scrivi(999, 1, pieno))
    prova("niente indirizzo sulla via del locker", True,
          str(scrivi(111, 2, pieno)).startswith("400 Questo ordine"))
    prova("un indirizzo a meta' si rifiuta", True,
          str(scrivi(111, 1, {"indirizzo": {"nome": "Mario"}}))
          .startswith("400 Per la spedizione"))
    prova("...e senza la chiave, fuori dal collaudo, e' un 503", True,
          str(scrivi(111, 1, pieno, collaudo=False)).startswith("503"))

    prima = [tuple(r) for r in vero.execute(
        "SELECT stato, aggiornato, spedito_il, consegnato FROM ordini")]
    r1 = scrivi(111, 1, pieno)
    prova("il compratore lo scrive, e il timbro nasce", True,
          isinstance(r1, dict) and r1["indirizzo_il"] > 0)
    o1 = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
    prova("nel database non e' nudo: passa dal trasporto di casa",
          True, o1["indirizzo"].startswith("plain:"))
    prova("...e l'ordine non si e' mosso di un millimetro", prima,
          [tuple(r) for r in vero.execute(
              "SELECT stato, aggiornato, spedito_il, consegnato "
              "FROM ordini")])
    prova("il venditore riceve l'avviso, senza il testo dentro", True,
          len(avvisi) == 1 and avvisi[0][0] == 222
          and "Via Roma" not in avvisi[0][1])

    letto = leggi(222, 1)
    prova("il venditore lo legge", True,
          isinstance(letto, dict)
          and letto["campi"]["via"] == "Via Roma 1")
    prova("...e anche il compratore", True,
          isinstance(leggi(111, 1), dict))
    prova("l'estraneo no, e non impara se l'ordine esiste",
          "400 Operazione non permessa", leggi(999, 1))
    prova("l'ordine che non c'e' risponde IDENTICO",
          "400 Operazione non permessa", leggi(999, 4242))
    dump = [tuple(r) for r in vero.execute("SELECT * FROM ordini")]
    leggi(222, 1)
    leggi(111, 1)
    prova("leggere non scrive NIENTE (due letture, dump identico)",
          dump, [tuple(r) for r in vero.execute("SELECT * FROM ordini")])

    avvisi.clear()
    scrivi(111, 1, {"indirizzo": dict(pieno["indirizzo"], cap="27011")})
    o1 = vero.execute("SELECT * FROM ordini WHERE id=1").fetchone()
    prova("la correzione si conta e timbra", True,
          o1["indirizzo_correzioni"] == 1
          and o1["indirizzo_corretto_il"] > 0)
    prova("...ma il PRIMO timbro non si sposta", 1,
          len({r1["indirizzo_il"], o1["indirizzo_il"]}))
    prova("...e il venditore lo viene a sapere", 1, len(avvisi))

    # --- LA SCOPA, girata davvero, a DUE VELOCITA' -----------------
    # (decisione di Andrea: alla conferma di ricezione si cancella
    #  SUBITO — garantiamo la transazione, non la consegna — e i
    #  giorni restano solo per chi si chiude senza quella conferma.)
    _t_finto = type("T", (), {"time": staticmethod(lambda: 9_000_000_000)})

    def scopa(leva=False):
        amb = {"db": Con, "time": _t_finto, "GIORNI_INDIRIZZO": 10,
               "AUTO_SBLOCCO_ATTIVO": leva,
               "print": lambda *a, **k: None}
        exec(pezzo("pulisci_indirizzi"), amb)
        amb["pulisci_indirizzi"]()

    def riga(i):
        return vero.execute("SELECT * FROM ordini WHERE id=?", (i,)).fetchone()

    # PRIMA a leva ACCESA: la corsia veloce non deve esistere, o il
    # giorno del rientro dell'auto-sblocco cancelleremmo l'indirizzo
    # di ordini che NESSUNO ha confermato
    scopa(leva=True)
    prova("a auto-sblocco ACCESO la corsia veloce e' spenta", True,
          riga(5)["indirizzo"] == "plain:{}"
          and riga(5)["indirizzo_purgato_il"] == 0)
    prova("...ma la finestra lavora lo stesso", True,
          riga(3)["indirizzo"] == "" and riga(3)["indirizzo_purgato_il"] > 0)
    prova("...e il resto della riga resta intero", True,
          riga(3)["indirizzo_il"] == 500 and riga(3)["aggiornato"] == 1000
          and riga(3)["stato"] == "released")

    scopa()
    prova("chi ha confermato perde l'indirizzo SUBITO, senza finestra",
          True, riga(5)["indirizzo"] == ""
          and riga(5)["indirizzo_purgato_il"] > 0)
    prova("la disputa decisa ieri passa dalla finestra e oggi resta",
          True, riga(4)["indirizzo"] == "plain:{}"
          and riga(4)["indirizzo_purgato_il"] == 0)
    prova("...e il rimborso di ieri pure", True,
          riga(6)["indirizzo"] == "plain:{}"
          and riga(6)["indirizzo_purgato_il"] == 0)
    prova("e l'ordine VIVO non si tocca", True, bool(riga(1)["indirizzo"]))
    dopo = [tuple(r) for r in vero.execute("SELECT * FROM ordini")]
    scopa()
    prova("la scopa e' idempotente: il secondo giro non fa niente",
          dopo, [tuple(r) for r in vero.execute("SELECT * FROM ordini")])
    prova("il purgato lo dice a chi lo cerca", True,
          str(leggi(111, 3)).startswith("404 L'indirizzo è stato "
                                        "cancellato"))
    vero.close()


def prove_nascondi_ordine():
    """IL NASCONDERE DEGLI AFFARI CONCLUSI (ago 2026): nascondere, MAI
    cancellare — la riga resta nel database (libro mastro, feedback,
    export e registro ci poggiano). Qui si prova che il gate ammette
    SOLO released/refunded (gli stati assorbenti), che nessuno
    nasconde per conto dell'altra parte, che l'estraneo e l'ordine
    inesistente rispondono uguale (anti-oracolo), e che nascondere non
    muove NIENTE oltre alla colonna della propria parte. Piu' la foto
    della riga: /api/orders esce con foto0 (primo nome; per i set il
    primo pezzo) e mai con la lista intera."""
    print("\n[il nascondere degli affari conclusi]")
    import asyncio
    import sqlite3

    # --- le sentinelle di forma -------------------------------------
    na = pezzo("nascondi_ordine").split('"""')[-1]
    prova("gate: released/refunded e basta", True,
          "stato IN ('released','refunded')" in na)
    prova("guardia a due parti nella stessa WHERE (anti-oracolo)", True,
          "(compratore_id=? OR " in na and "venditore_id=?)" in na
          and "Operazione non permessa" in na)
    prova("UN solo UPDATE, e non scrive mai `aggiornato` ne' lo stato",
          True, na.count("UPDATE") == 1 and "aggiornato=?" not in na
          and "stato='" not in na)
    prova("nessuna notifica: e' un fatto privato di una parte", False,
          "notifica(" in na)
    prova("la colonna e' un ternario su due letterali NOSTRI", True,
          '"nascosto_compratore" if' in na
          and '"nascosto_venditore")' in na)
    mo = pezzo("miei_ordini")
    prova("/api/orders: escono foto0 e nascosto, mai le colonne grezze",
          True, 'r["foto0"]' in mo and 'r["nascosto"]' in mo
          and 'r.pop("nascosto_compratore"' in mo
          and 'r.pop("nascosto_venditore"' in mo
          and 'r.pop("foto"' in mo)
    prova("/api/orders: il WHERE di sempre non e' cambiato", True,
          "WHERE o.compratore_id=? OR o.venditore_id=?" in mo)
    prova("il libro mastro sorveglia il nascosto fuori posto", True,
          "ordine nascosto su uno stato non finale" in _SORGENTE)
    # la parita' col client (pattern CAT_SENZA_COND): il gate del
    # server e la ✕ del client devono dire lo stesso elenco
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("client: NASCONDIBILI == il gate del server", True,
          "const NASCONDIBILI = ['released','refunded']" in mini)
    ro = pezzo_js(mini, "function renderOrders(){")
    prova("client: il filtro vive in renderOrders, orders resta intero",
          True, "orders.filter" in ro
          and "filter" not in pezzo_js(mini, "async function loadOrders"))
    prova("client: il toast dice dove ritrovarlo", True,
          "Nascosto — lo ritrovi da «mostrali»" in mini)
    prova("client: la ✕ non apre l'ordine (stopPropagation)", True,
          "ev.stopPropagation()"
          in pezzo_js(mini, "async function nascondiOrdine"))

    # --- il funzionale su sqlite in memoria -------------------------
    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    vero = sqlite3.connect(":memory:")
    vero.row_factory = sqlite3.Row
    vero.executescript("""
      CREATE TABLE ordini(
        id INTEGER PRIMARY KEY, annuncio_id INT DEFAULT 1,
        compratore_id INT, venditore_id INT, stato TEXT,
        prezzo_sats INT DEFAULT 1000, quantita INT DEFAULT 1,
        consegna_scelta TEXT DEFAULT '', aggiornato INT DEFAULT 42,
        creato INT DEFAULT 7,
        contenuto_digitale TEXT DEFAULT '',
        busta_nome TEXT DEFAULT '', busta_codice TEXT DEFAULT '',
        nascosto_compratore INT DEFAULT 0,
        nascosto_venditore INT DEFAULT 0);
      CREATE TABLE annunci(id INTEGER PRIMARY KEY, titolo TEXT,
        zona TEXT DEFAULT '', foto TEXT DEFAULT '',
        taglia_pacco TEXT DEFAULT '', asta_base_sats INT DEFAULT 0);
      CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '', npub TEXT DEFAULT '',
        npub_accesso TEXT DEFAULT '', npub_verificata INT DEFAULT 0);
      CREATE TABLE feedback(ordine_id INT, da_tg_id INT, per_tg_id INT,
        voto INT, commento TEXT);
      CREATE TABLE ordine_righe(id INTEGER PRIMARY KEY, ordine_id INT,
        annuncio_id INT, quantita INT DEFAULT 1, unitario_sats INT,
        titolo TEXT DEFAULT '');
      INSERT INTO utenti(tg_id, username) VALUES(111, 'compra'),
        (222, 'vende');
      INSERT INTO annunci(id, titolo, foto) VALUES
        (1, 'Vaso di ceramica', '["a1_0.jpg","a1_1.jpg"]'),
        (2, 'Senza foto', ''),
        (3, 'Tazza al tornio', '["a3_0.jpg"]');
    """)
    stati = ("creato", "locked", "shipped", "delivered", "confirmed",
             "dispute", "return_pending", "return_shipped", "refund",
             "annullato", "released", "refunded")
    for n, s in enumerate(stati, start=1):
        vero.execute("INSERT INTO ordini(id, compratore_id, "
                     "venditore_id, stato) VALUES(?, 111, 222, ?)",
                     (n, s))
    vero.commit()

    class Con:
        def execute(self, *a):
            return vero.execute(*a)

        def commit(self):
            vero.commit()

        def close(self):
            pass

    class _Req:
        def __init__(self, d):
            self._d = d

    async def _leggi(req):
        return req._d

    def nascondi(chi, oid, body):
        amb = {"db": Con, "HTTPException": _H, "Request": object,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi},
               "leggi_json": _leggi}
        exec("async " + pezzo("nascondi_ordine"), amb)
        try:
            return asyncio.new_event_loop().run_until_complete(
                amb["nascondi_ordine"](oid, _Req(body)))
        except _H as e:
            return f"{e.code} {e.detail}"

    # il gate, stato per stato: TUTTI i non assorbenti rifiutano —
    # confirmed e refund SEMBRANO conclusi ma sono un limbo, e
    # annullato e' una lapide che il reaper gestisce da solo
    for n, s in enumerate(stati[:10], start=1):
        prova(f"non si nasconde un ordine '{s}'",
              "400 Operazione non permessa", nascondi(111, n, {}))
    dump = [tuple(r) for r in vero.execute("SELECT * FROM ordini")]
    prova("...e dieci rifiuti non hanno scritto NIENTE", dump,
          [tuple(r) for r in vero.execute("SELECT * FROM ordini")])
    prova("il compratore nasconde il released",
          {"ok": True, "nascosto": 1}, nascondi(111, 11, {}))
    o = vero.execute("SELECT * FROM ordini WHERE id=11").fetchone()
    prova("...sulla SUA colonna e solo quella", (1, 0),
          (o["nascosto_compratore"], o["nascosto_venditore"]))
    prova("...senza toccare stato ne' aggiornato", ("released", 42),
          (o["stato"], o["aggiornato"]))
    prova("il venditore nasconde il suo refunded",
          {"ok": True, "nascosto": 1}, nascondi(222, 12, {"nascosto": 1}))
    prova("...sulla colonna del venditore", (0, 1),
          tuple(vero.execute(
              "SELECT nascosto_compratore, nascosto_venditore "
              "FROM ordini WHERE id=12").fetchone()))
    prova("rimettere in vista funziona (nessuna guardia in piu')",
          {"ok": True, "nascosto": 0},
          nascondi(111, 11, {"nascosto": 0}))
    prova("...e la colonna torna 0", 0,
          vero.execute("SELECT nascosto_compratore FROM ordini "
                       "WHERE id=11").fetchone()[0])
    prova("estraneo e ordine inesistente rispondono uguale", True,
          nascondi(999, 11, {}) == nascondi(111, 777, {}))

    # --- il GET: foto0 e il flag per-parte, dal pezzo vero ----------
    vero.execute("UPDATE ordini SET annuncio_id=1, "
                 "nascosto_compratore=1 WHERE id=11")
    vero.execute("UPDATE ordini SET annuncio_id=2 WHERE id=12")
    # un mono il cui annuncio e' SPARITO (LEFT JOIN a vuoto)
    vero.execute("INSERT INTO ordini(id, compratore_id, venditore_id, "
                 "stato, annuncio_id) VALUES(20, 111, 222, "
                 "'released', 999)")
    # un SET: la foto e' quella del PRIMO pezzo, l'altro e' orfano
    vero.execute("INSERT INTO ordini(id, compratore_id, venditore_id, "
                 "stato, annuncio_id, consegna_scelta) "
                 "VALUES(21, 111, 222, 'locked', 0, 'ritiro')")
    vero.executescript("""
      INSERT INTO ordine_righe(ordine_id, annuncio_id, quantita,
        unitario_sats, titolo) VALUES(21, 3, 1, 500, 'Tazza al tornio'),
        (21, 999, 1, 500, 'Pezzo sparito');
    """)
    vero.commit()

    def miei(chi):
        amb = {"db": Con, "HTTPException": _H,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi},
               "pulisci_ordini_fantasma": lambda con: None,
               "e_admin": lambda tg: False,
               "stima_taglia_set": lambda t: "",
               "json": __import__("json")}
        exec(pezzo("_titolo_ordine"), amb)
        exec(pezzo("miei_ordini"), amb)
        return {r["id"]: r for r in amb["miei_ordini"](0, "", "")}

    lato_c, lato_v = miei(111), miei(222)
    prova("mono con foto: esce il PRIMO nome e la lista non esce",
          ("a1_0.jpg", False),
          (lato_c[11]["foto0"], "foto" in lato_c[11]))
    prova("mono senza foto: foto0 vuota (il client tiene il 📦)", "",
          lato_c[12]["foto0"])
    prova("annuncio sparito: foto0 vuota, mai un errore", "",
          lato_c[20]["foto0"])
    prova("set: la foto del PRIMO pezzo, quello che il titolo nomina",
          ("a3_0.jpg", "Tazza al tornio + 1 altri"),
          (lato_c[21]["foto0"], lato_c[21]["titolo"]))
    prova("il nascosto del compratore per il compratore e' 1", 1,
          lato_c[11]["nascosto"])
    prova("...e per il VENDITORE e' 0: il flag altrui non esce", 0,
          lato_v[11]["nascosto"])
    prova("le colonne grezze non escono da nessun lato", True,
          all("nascosto_compratore" not in r and
              "nascosto_venditore" not in r
              for r in list(lato_c.values()) + list(lato_v.values())))
    vero.close()


def prove_lista_ordini():
    """LA LISTA ORDINI: LE LAPIDI NON SI VEDONO, E I VERBI SEGUONO IL
    TEMPO (ago 2026). L'annullato sparisce dalla VISTA e da nient'altro
    — la lapide serve alla macchina (un saldo che atterra nella corsa
    annulla-vs-saldo deve trovare una riga) e la spazza il reaper a
    un'ora: qui si prova che il database e la scopa restano intatti.
    E che la riga dice «stai comprando» finche' l'affare e' vivo e
    «hai comprato per X» quando e' finito, con la cifra che ognuno ha
    davvero mosso: il TOTALE a chi paga, il NETTO a chi incassa."""
    print("\n[la lista ordini: lapidi e verbi]")

    def solo_codice(js):
        """Via i commenti: senza, una sentinella che cerca 'annullato'
        pesca la PROSA che racconta il cantiere invece del programma
        (la lezione dei fogli di casa)."""
        js = re.sub(r"/\*[\s\S]*?\*/", "", js)
        return "\n".join(r for r in js.split("\n")
                         if not r.strip().startswith("//"))

    mini = open("miniapp.html", encoding="utf-8").read()
    ro = solo_codice(pezzo_js(mini, "function renderOrders(){"))

    # ---- 1-4: la lapide fuori dalla vista, e solo da li' ----
    prova("la vista parte dai vivi, l'annullato ne resta fuori", True,
          "o.state !== 'annullato'" in ro)
    # TORTURA: se vista o nNascosti tornassero a leggere `orders`, il
    # conteggio salirebbe a 2 e questa diventerebbe rossa da sola —
    # ed e' l'errore che verrebbe naturale, perche' non rompe nulla
    # di visibile finche' non si guarda un checkout abbandonato.
    prova("...e `orders` si legge UNA volta sola, per derivarli", 1,
          ro.count("orders.filter"))
    prova("il velo dei nascosti conta sui vivi, mai sulle lapidi", True,
          "const nNascosti = vivi.filter(" in ro)
    prova("«ancora nessun ordine» guarda i vivi: un checkout "
          "abbandonato non e' un filtro acceso", True,
          "if (!vivi.length)" in ro and "if (!orders.length)" not in ro)

    # ---- 5-7: il database e la scopa non si toccano ----
    pf = pezzo("pulisci_ordini_fantasma")
    prova("il reaper spazza ancora le lapidi a un'ora", True,
          "DELETE FROM ordini WHERE stato='annullato' " in pf
          and "aggiornato < ?" in pf)
    prova("il riacciuffo cerca ancora i pagamenti sulle lapidi", True,
          "WHERE stato='annullato' " in pezzo("controlla_annullati"))
    prova("il server non ha imparato a filtrare la lista", True,
          "WHERE o.compratore_id=? OR o.venditore_id=?"
          in pezzo("miei_ordini"))

    # ---- 8-14: i verbi ----
    # LA DATA E L'ORDINE SONO QUELLI DELL'AFFARE (ago 2026, dal
    # campo): con `aggiornato` un ordine di una settimana fa sembrava
    # di oggi appena il venditore segnava la spedizione — e saltava
    # anche in cima alla lista. Le due cose vanno insieme: la data
    # corretta sopra un ordinamento per movimento farebbe sembrare la
    # lista disordinata.
    mo2 = pezzo("miei_ordini")
    prova("la lista si ordina per data dell'affare", True,
          'ORDER BY o.creato DESC, o.id DESC' in mo2
          and "ORDER BY o.aggiornato DESC" not in mo2)
    # ...e l'id in coda: `creato` e' al secondo, e due ordini nati
    # nello stesso istante altrimenti si scambiano di posto a ogni
    # richiesta (la lista «balla» senza che nulla sia cambiato)
    prova("...con l'id a fare il pareggio", True,
          "o.id DESC" in mo2)
    # L'EXPORT invece tiene `aggiornato`, ed e' la scelta giusta: li'
    # escono solo released/refunded e per la contabilita' conta il
    # giorno in cui i sats si sono mossi, non quello dell'acquisto.
    ex = pezzo("scarica_export")
    if ex:
        prova("il CSV della contabilita' resta all'ultimo movimento",
              True, "ORDER BY o.aggiornato DESC" in ex
              and 'time.localtime(r["aggiornato"])' in ex)

    mp = solo_codice(pezzo_js(mini, "function mapOrder(o){"))
    prova("la riga mostra la data dell'affare, non dell'ultimo "
          "movimento", True,
          "new Date(o.creato*1000)" in mp
          and "new Date(o.aggiornato*1000)" not in mp)
    # ...e la SOLA data: a colpo d'occhio in lista l'orario non serve
    # a nessuno, e ruba spazio al titolo. Dove serve davvero — la
    # busta di ritiro e la rivelazione del codice — resta, e li' e'
    # una scelta: vedi i pannelli dell'ordine.
    prova("...e senza l'orario", True,
          "toLocaleDateString" in mp
          and "hour:'2-digit'" not in mp)
    # IL BADGE E LA TESTA DEL RIQUADRO NON SONO LA STESSA COSA (ago
    # 2026): l'etichetta dice cosa e' SUCCESSO («Sats depositati»), la
    # testa dice DOVE sono adesso («Sats nel deposito di garanzia»).
    # Uniformarle e' l'errore che verrebbe naturale.
    prova("il badge della lista dice il fatto", True,
          "label:'Sats depositati'" in mini
          and "label:'Sats in deposito'" not in mini)
    prova("...e la testa del riquadro resta il posto", True,
          "b:'Sats nel deposito di garanzia'" in mini)

    vo = solo_codice(pezzo_js(mini, "function verboOrdine(o){"))
    prova("il concluso e' CONCLUSI, non una seconda lista", True,
          "CONCLUSI.includes(o.state)" in vo
          and "'released'," not in vo)
    prova("chi compra legge il TOTALE in cassaforte", True,
          "Hai comprato per ${cifra(o.listing.price)}" in vo)
    prova("chi vende legge il NETTO, che e' un altro numero", True,
          "Hai venduto per ${cifra(nettoVenditore(o))}" in vo)
    # il rimborso (e la lapide, che in lista non si vede) non porta
    # cifra: li' nessuno ha comprato e nessuno ha venduto
    ramo = vo[vo.index("if (CONCLUSI.includes"):
              vo.index("return `${compra")]
    prova("il non-concluso NON porta nessuna cifra", False,
          "cifra(" in ramo)
    prova("...e non ripete il «Rimborsato» del badge accanto", True,
          "non conclus" in ramo and "imborsat" not in ramo)
    prova("finche' e' vivo il verbo e' al presente, con la sua cifra",
          True, "'Stai comprando' : 'Stai vendendo'" in vo
          and "cifra(o.listing.price)}`" in vo)
    prova("il moderatore non compra e non vende", True,
          "'⚖️ Da moderare'" in vo)
    prova("la riga della lista passa dal giudice", True,
          "${verboOrdine(o)} · ${o.when}" in ro)

    # ---- 15-16: il netto e' UNO (il giorno della commissione) ----
    prova("nettoVenditore e' definito una volta sola", 1,
          mini.count("function nettoVenditore(o)"))
    prova("...e la formula del netto non ha copie: la dicono la riga, "
          "la testa dell'ordine e il pannello d'incasso", (1, 3),
          (mini.count("o.listing.price - (o.protSats||0)"),
           mini.count("nettoVenditore(o)") - 1))


def prove_dettaglio_ordine():
    """IL DETTAGLIO PARLA A CHI LEGGE (ago 2026): la vista e' UNA per
    tutti e due i lati, quindi ogni frase che nomina una parte va
    girata a chi la sta leggendo — e correggere per uno non deve
    rompere per l'altro: qui si prova che dove nasce un «hai» resta la
    terza persona sull'altro ramo. Piu' la modalita' che non si ripete
    (la diceva la riga in alto e la dice gia' quella sotto) e la
    spedizione che torna INCISO accanto alla cifra invece che riga a
    se' — muta quando la promessa del negozio l'ha resa gratis, che
    «di cui 0» non direbbe niente."""
    print("\n[il dettaglio dell'ordine: chi legge e chi paga]")
    mini = open("miniapp.html", encoding="utf-8").read()
    det = mini[mini.index("function openOrder(id){"):
               mini.index("function trasportoScopri()")]
    ic = pezzo_js(mini, "function incisoConto(o){")

    # ---- 1-5: l'inciso ----
    # (dall'ago 2026 la cifra passa dal giudice del cambio congelato:
    #  quello che si sorveglia qui resta lo stesso — l'inciso attaccato
    #  alla cifra, dentro la sua riga, e non una riga a se')
    prova("l'inciso sta ACCANTO alla cifra, dentro la riga del prezzo",
          True, '${cifraOrdine(o, o.listing.price)}${incisoConto(o)}</div>'
          in det)
    prova("...e non e' rimasta una riga a se' col «di cui»", 1,
          det.count("di cui ") + ic.count("di cui "))
    prova("l'inciso porta la spedizione e, quando c'e', la protezione",
          True, "di spedizione" in ic and "di protezione" in ic)
    prova("TACE se la spedizione non si e' pagata (promessa del "
          "negozio compresa: «di cui 0» sarebbe muto)", True,
          "o.spedSats>0 ?" in ic and "spedGratis" not in ic)
    prova("la riga «Spedizione gratuita» resta a dirlo, con la cifra",
          True, "🚚 Spedizione <b>gratuita</b>" in det
          and "cifraOrdine(o, o.spedGratisSats)} di spedizione" in det)

    # ---- 4-bis: LA FOTO VERA, IN LISTA E NEL DETTAGLIO ----
    # La catena di ripiego (miniatura versionata → foto piena → 📦) e'
    # la parte delicata: una fabbrica SOLA, o le due copie divergono
    # al primo ritocco e una delle due mostra un'immagine rotta.
    fo = pezzo_js(mini, "function fotoOrdine(o, grande){")
    # la catena degli ORDINI si riconosce dal 📦 finale: le miniature
    # delle altre liste hanno la loro, a due gradini e senza emoji
    prova("la catena di ripiego dell'ordine vive in un posto solo", 1,
          mini.count("replaceWith('📦')"))
    prova("...ed e' dentro fotoOrdine", True,
          "this.src=this.dataset.full" in fo
          and "replaceWith('📦')" in fo)
    prova("la miniatura e' quella versionata", True,
          "fotoMini(o.foto0)" in fo and "fotoUrl(o.foto0)" in fo)
    prova("senza foto resta il 📦 (o l'emoji della DEMO)", True,
          "o.listing.emoji || '📦'" in fo)
    prova("il nome del file passa sempre da esc()", 2, fo.count("esc(foto"))
    prova("la lista chiama la fabbrica", True, "${fotoOrdine(o)}" in mini)
    prova("...e il dettaglio pure, col quadratino grande", True,
          "${fotoOrdine(o, true)}" in det)
    prova("...al posto del 📦 accanto al titolo", False,
          "${o.listing.emoji} ${esc(o.listing.title)}" in det)
    # Senza min-width:0 sul figlio flex, una parola lunga senza spazi
    # allarga la PAGINA (la lezione del riquadro venditore; misurato
    # ago 2026: 375 → 780px). Da quando la testa porta anche il numero
    # dell'ordine il figlio flex e' la COLONNA e non piu' il titolo,
    # quindi la guardia si e' TRASLOCATA li' — sull'h2, che flex non
    # vede piu', non farebbe niente.
    prova("il titolo del dettaglio non può allargare la pagina", True,
          ".ordine-testa .ord-col{min-width:0" in mini)

    # ---- 5-bis: IL PUNTO NON SI DICE DUE VOLTE ----
    # Sotto il prezzo c'era anche il punto GIA' scelto, mentre due dita
    # piu' sotto lo stesso testo si puo' ancora CORREGGERE. Via di li';
    # e a spedizione fatta — campo chiuso, pannello del venditore
    # sparito — ricompare nel banner del pacco, che e' dove si guarda
    # «dov'e' la mia roba».
    pb = pezzo_js(mini, "function puntoBanner(o){")
    prova("il punto non si ripete piu' sotto il prezzo", False,
          "Il punto di ritiro che hai indicato" in det)
    prova("...ma resta l'invito quando ancora non c'e'", True,
          "Spedizione a un locker/punto di ritiro: indica il punto "
          "qui sotto." in det)
    prova("il banner del pacco lo ridice a chi compra", True,
          "'Il tuo punto di ritiro'" in pb)
    prova("...e all'altro lato in terza persona", True,
          "'Punto di ritiro dell\\'acquirente'" in pb)
    prova("...col testo del compratore sempre scappato", True,
          "esc(o.puntoRitiro)" in pb)
    # IL BANNER E' DEL PUNTO, E DI NIENT'ALTRO (ago 2026): questa prova
    # ha CAMBIATO LATO — chiedeva «il banner nasce anche senza
    # tracciamento», cioe' certificava la meta' che diceva «Spedito con
    # X — tracciamento Y», parola per parola il passo «Oggetto spedito»
    # del recinto due dita piu' su. Il codice resta LI', dove ora si
    # tocca; qui resta il punto, e senza punto il banner non nasce.
    prova("il banner e' del punto, e di nient'altro", True,
          "(['shipped','delivered'].includes(s) && o.puntoRitiro)" in det)
    prova("...quindi il tracciamento non si ripete sotto il recinto",
          False, "Spedito con <b>" in det)
    # e il «segui il pacco» di 17track e' uscito dall'ordine: la strada
    # delle notifiche e' @trackbot, e due strade per la stessa cosa
    # sono un bivio davanti a chi aspetta un pacco. Ne resta UNO, quello
    # del RESO (lato venditore, altro cantiere): il conto lo dice, cosi'
    # se un domani ne ricompare uno qui la riga diventa rossa.
    righe17 = [r for r in mini.splitlines() if "t.17track.net" in r]
    prova("di 17track ne resta uno solo", 1, len(righe17))
    prova("...ed e' quello del reso", True,
          bool(righe17) and "trackingReso" in righe17[0])

    # ---- 5-ter: LA TESTATA STA SOPRA IL RECINTO ----
    # Lo stato dell'affare e' l'intestazione dell'ORDINE, non un
    # contenuto della cassaforte: e' uscito dal riquadro, che comincia
    # dritto coi passi e NON prende una seconda testata (ogni passo ha
    # gia' il suo titolo). Il CSS ha dovuto perdere il discendente
    # `.vault .vault-head`, o la testata resterebbe senza vestito.
    prova("la testata sta FUORI dal recinto", True,
          '<div class="vault-head">' in det and '<div class="vault">' in det
          and det.index('<div class="vault-head">')
              < det.index('<div class="vault">'))
    prova("...e dentro il recinto ci sono solo i passi", True,
          '<div class="vault">\n        <div class="steps">' in det)
    prova("il CSS non cerca piu' la testata dentro .vault", False,
          ".vault .vault-head" in mini)
    prova("...ma la veste lo stesso", True, ".vault-head{" in mini)
    # le monete della festa partono da li': se la classe cambiasse nome
    # uscirebbero dal nulla
    prova("la festa dei sats trova ancora la testata", True,
          "#orderContent .vault-head" in mini)

    # ---- 6-8: la modalita' non si ripete ----
    for detto in ("📦 spedizione a un punto di ritiro",
                  "🚚 con spedizione", "💾 codice online"):
        prova(f"la riga in alto non ripete piu' «{detto}»", False,
              detto in det)
    prova("il conto dei pezzi resta: non lo dice nessun altro", True,
          "pezzi × ${cifraOrdine(o, (o.listing.price" in det)

    # ---- 9-16: le terze persone, e la PARITA' fra i due lati ----
    # ogni voce: (nome, il testo girato a chi legge, quello che
    # l'altro lato deve continuare a leggere)
    for nome, mio, suo in (
            ("il reso da rispedire", "Devi rispedire l\\'oggetto al venditore",
             "L\\'acquirente deve rispedire l\\'oggetto al venditore"),
            ("la disputa vinta", "Disputa risolta a tuo favore",
             "Disputa risolta a favore dell\\'acquirente"),
            ("la consegna al corriere", "Hai consegnato al corriere",
             "Il venditore ha consegnato al corriere"),
            ("il contenuto digitale", "Hai consegnato il contenuto",
             "Il venditore ha consegnato il contenuto"),
            ("la spedizione offerta", "'hai':'il venditore ha'", ""),
            # l'attesa della conferma: il gesto e' di chi compra, e
            # questa riga la leggono tutti e due
            ("l'attesa del fisico",
             "I sats restano nel deposito finché non confermi",
             "I sats restano nel deposito finché l\\'acquirente non conferma"),
            ("la finestra del digitale",
             "Restano ~${oreRestanti} ore per confermare o aprire disputa",
             "L'acquirente ha ~${oreRestanti} ore per confermare o aprire disputa"),
            ("il reso ancora da spedire",
             "Rispedisci l\\'oggetto: al rientro ti rimborsiamo",
             "L\\'acquirente sta rispedendo l\\'oggetto")):
        prova(f"{nome}: chi legge si sente dare del tu", True, mio in det)
        if suo:
            prova(f"...e l'altro lato non si rompe: resta «{suo[:28]}…»",
                  True, suo in det)

    # ---- 17-21: la prima riga del riquadro dice un GESTO ----
    # (ago 2026) «Sats nel deposito di garanzia» raccontava un fatto
    # della piattaforma, non quel che e' successo a chi legge. La riga
    # e' CONDIVISA, quindi vale la regola qui sopra — e il verso in
    # cui si sbaglia e' dare l'«hai depositato» anche a chi VENDE, che
    # i sats non li ha depositati: ce li ha in garanzia.
    prova("chi ha comprato ha DEPOSITATO i sats", True,
          "'Hai depositato i sats'" in det)
    prova("...chi vende ce li ha IN GARANZIA, non in tasca", True,
          "'Hai il pagamento in garanzia'" in det
          and "o.role==='seller' ? 'Hai depositato" not in det)
    prova("...e il moderatore, che guarda da fuori, resta neutro", True,
          "'Sats nel deposito di garanzia'" in det)
    prova("la riga sotto resta vera per tutti e due", True,
          "d: 'Il pagamento è custodito dalla piattaforma'" in det)
    prova("e la dicono ENTRAMBI i rami del riquadro (disputa compresa)",
          2, det.count("passoDeposito,"))

    # ---- IL TRACCIAMENTO NON SPARISCE QUANDO SERVE (ago 2026, dal
    # campo: su un ordine SDA da 9 cifre il codice non lo vedeva piu'
    # nessuno, ne' chi compra ne' chi vende). IL SOSPETTO ERA IL
    # FILTRO DI TRACKBOT, E NON ERA LUI: riprodotto, in disputa il
    # codice spariva con QUALUNQUE corriere — anche con quelli che il
    # filtro lo passano — perche' questo ramo ha una storia sua e non
    # ha mai avuto un passo per la spedizione. Il ramo e' identico
    # byte per byte a prima del cantiere trackbot: un buco vecchio,
    # visto il giorno in cui qualcuno e' andato a cercare il codice
    # proprio dove serve come prova.
    passi = mini[mini.index("const rigaSpedizione"):
                 mini.index("progress = {creato:")]
    disputa = passi[:passi.index("progress = {dispute")]
    prova("in disputa il passo della spedizione c'e'", True,
          "{t:'Oggetto spedito', d:rigaSpedizione()}" in disputa)
    # LA GUARDIA E' LA PRESENZA DEL CODICE E NIENTE ALTRO: una
    # disputa aperta da 'locked', o una consegna a mano, non hanno
    # niente da mostrare — ma la FORMA del codice non deve entrarci
    # mai, o si ricompra il difetto che questa prova sorveglia.
    prova("...e la guardia e' il solo tracciamento", True,
          "...(o.tracking ? [{t:'Oggetto spedito'" in disputa)
    # LA PROVA CHE IL CAMPO HA CHIESTO, e si scrive come CENSIMENTO
    # invece che come elenco: nella strada che RENDE il codice il
    # filtro non deve comparire mai — cosi' un codice fuori filtro si
    # vede comunque, oggi e il giorno che qualcuno aggiungera' un
    # ramo nuovo allo stepper.
    ct = pezzo_js(mini, "function codiceTracking")
    for nome, corpo in (("lo stepper", passi),
                        ("la fabbrica del codice", ct)):
        prova("un codice fuori filtro si vede comunque: " + nome, True,
              "passaTrackbot" not in corpo
              and "FILTRO_TRACKBOT" not in corpo)
    # LA RIGA E' UNA SOLA per i due rami: due copie sono due che un
    # giorno divergono, con la traccia del moderatore appresso a una
    # sola.
    prova("la riga della spedizione e' una fabbrica sola", 1,
          mini.count("const rigaSpedizione"))
    prova("...e la usano tutti e due i rami", 2,
          passi.count("rigaSpedizione()"))
    # `progress` E' UN INDICE dentro `steps`: il passo in piu' sposta
    # di uno tutti quelli dopo, o il pallino «adesso» si accende sul
    # passo sbagliato — un difetto che non si vede leggendo.
    prova("il passo in piu' sposta il progress della disputa", True,
          "+ (o.tracking ? 1 : 0)" in passi)

    # ---- 22-23: il reso gia' in viaggio non si fa rispedire ----
    # I due stati del reso NON si possono dire con la stessa frase: a
    # pacco gia' partito «Rispedisci» sarebbe una bugia a chi ha
    # appena fatto quel che gli si chiedeva.
    prova("la testa del reso distingue i due stati", True,
          "d:s==='return_pending'" in det)
    prova("...e a reso partito dice che e' in viaggio", True,
          "Il reso è in viaggio: al rientro ti rimborsiamo" in det
          and "L\\'acquirente ha rispedito l\\'oggetto" in det)

    # ---- 24-26: il passo del reso parla a TRE, non a due ----
    # Qui acquirente e venditore sono nominati TUTTI E DUE nella
    # stessa frase, quindi il taglio buyer/non-buyer non basta: al
    # venditore restava una terza persona su SE' STESSO.
    prova("chi vende non si sente più chiamare «il venditore»", True,
          "L\\'acquirente deve rispedirti l\\'oggetto" in det)
    prova("...e il reso in viaggio arriva «verso di te»", True,
          "Il reso è in viaggio verso di te" in det)
    prova("...mentre il moderatore tiene le due terze persone", True,
          "L\\'acquirente deve rispedire l\\'oggetto al venditore" in det
          and "Il reso è in viaggio verso il venditore" in det)


def _notifica_admin_spia(avvisi):
    async def _n(testo):
        avvisi.append(("admin", testo))
    return _n


def pezzo_js(mini, firma, fine="\n\n"):
    """Il gemello di pezzo() per miniapp.html: estrae una funzione JS
    per testo, dalla firma alla prima riga vuota."""
    i = mini.index(firma)
    return mini[i:mini.index(fine, i)]


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
    # e l'import da Nostr lo riceve: il patto del `vaglio` — insieme al
    # cambio, che dall'ago 2026 viaggia sulla stessa strada
    prova("sentinella: l'import orario riceve lo scaricatore del server",
          True, "vaglio, scarica_foto_url, cambio_import)" in _SORGENTE)
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


def prove_foto_scarti():
    """NESSUNA FOTO SPARISCE IN SILENZIO (ago 2026, caso dal campo).
    Ogni scarto di salva_foto era un `continue` muto: l'annuncio
    nasceva con meno foto e nessuno lo diceva. Adesso salva_foto torna
    anche i MOTIVI, e la risposta della pubblicazione li porta fino
    all'utente. Qui si gira il pezzo VERO su una cartella usa-e-getta,
    piu' le sentinelle sulle righe che in un riordino sparirebbero
    riportandosi dentro il bug."""
    print("\n[le foto che sparivano in silenzio]")
    import base64
    import io
    import re
    import tempfile

    try:
        from PIL import Image, ImageOps
    except ImportError:
        salta("gli scarti di salva_foto, girati per davvero",
              "Pillow non e' installata")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            amb = {"os": os, "io": io, "re": re, "base64": base64,
                   "ImmaginePillow": Image, "ImageOps": ImageOps,
                   "pillow_heif": None, "FOTO_DIR": tmp,
                   "print": lambda *a, **k: None}
            i = _SORGENTE.index("MINIATURA_LATO = ")
            exec(_SORGENTE[i:_SORGENTE.index("\n\n\n", i)], amb)
            for f in ("converti_in_jpeg", "miniatura_jpeg", "_salva_una_foto",
                      "_e_immagine", "salva_foto"):
                exec(pezzo(f), amb)

            def uri(raw, tipo="jpeg"):
                return (f"data:image/{tipo};base64,"
                        + base64.b64encode(raw).decode())

            out = io.BytesIO()
            Image.new("RGB", (60, 40), (200, 120, 40)).save(out, "JPEG")
            buona = out.getvalue()
            pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"

            # il giudice dei byte, sui casi nudi
            prova("un JPEG e' un'immagine", True, amb["_e_immagine"](buona))
            prova("un PDF no", False, amb["_e_immagine"](pdf))
            prova("il vuoto no", False, amb["_e_immagine"](b""))

            # IL CASO DAL CAMPO: un PDF rinominato .jpg. Il data-URI lo
            # scrive il browser dall'ESTENSIONE, quindi arriva qui
            # etichettato image/jpeg e prima finiva SCRITTO sul disco.
            nomi, scarti = amb["salva_foto"](7, [uri(buona), uri(pdf)])
            prova("il PDF vestito da foto non si salva", 1, len(nomi))
            prova("...e il motivo si dice", ["non è una foto"], scarti)
            prova("...e sul disco non ci finisce", ["a7_0.jpg", "a7_0_min.jpg"],
                  sorted(f for f in os.listdir(tmp) if f.startswith("a7_")))

            # gli altri motivi, uno per uno
            for foto, atteso in (
                    (["non sono un data-uri"], "formato non riconosciuto"),
                    # base64 che non torna: b64decode butta i caratteri
                    # fuori alfabeto, quindi per farlo INCIAMPARE serve
                    # una lunghezza storta, non solo spazzatura — la
                    # spazzatura pura decodifica a vuoto e la ferma
                    # _e_immagine, un passo piu' in la'
                    (["data:image/jpeg;base64,!!!non-base64!!!"],
                     "foto illeggibile"),
                    (["data:image/jpeg;base64,!!!"], "non è una foto"),
                    ([uri(b"\xff\xd8" + bytes(16_000_000))],
                     "troppo grande (oltre 15MB)"),
                    ([uri(b"nemmeno per sogno", "heic")],
                     "foto HEIC: questo server non sa convertirla")):
                nomi, scarti = amb["salva_foto"](8, foto)
                prova(f"scarto detto: {atteso}", ([], [atteso]), (nomi, scarti))

            # e il caso normale non inventa avvisi
            nomi, scarti = amb["salva_foto"](9, [uri(buona), uri(buona)])
            prova("due foto buone, zero scarti", (2, []), (len(nomi), scarti))
            prova("nessuna foto chiesta, nessuno scarto", ([], []),
                  amb["salva_foto"](10, []))

    # --- SENTINELLE ---------------------------------------------------
    mini = open("miniapp.html", encoding="utf-8").read()
    # 1) IL TRASCINAMENTO. Il riquadro e' tratteggiato e si chiama
    # photo-drop: sul desktop chiede di essere usato cosi', e per un
    # anno ha avuto il solo onclick — senza preventDefault sul dragover
    # il browser non emette nemmeno l'evento drop, quindi trascinare una
    # foto non faceva ASSOLUTAMENTE NIENTE (riprodotto). Se queste
    # righe spariscono, il caso dal campo torna identico.
    riquadro = mini[mini.index('<div class="photo-drop"'):]
    riquadro = riquadro[:riquadro.index(">")]
    for gancio in ("ondragenter", "ondragover", "ondragleave", "ondrop"):
        prova(f"sentinella: il riquadro ascolta {gancio}", True,
              gancio in riquadro)
    i = mini.index("function fotoSopra(")
    prova("sentinella: ed e' il preventDefault a renderlo un bersaglio",
          True, "ev.preventDefault()" in mini[i:mini.index("\n}", i)])
    # 2) l'errore dell'anteprima si LEGGE e si DICE: prima era un
    # `if (r.ok)` senza else, e in pagina restava il segnaposto «verra'
    # convertita alla pubblicazione» — una promessa mai verificata
    prova("sentinella: il motivo del server arriva all'utente", True,
          "d.detail || 'Non riesco a preparare questa foto'" in mini)
    prova("sentinella: il segnaposto bugiardo non c'e' piu'", False,
          "verrà convertita" in mini)
    # 3) il FileReader che fallisce non e' piu' muto
    prova("sentinella: il FileReader che fallisce lo dice", True,
          "Non riesco a leggere «" in mini)
    # 4) quante ne sono entrate: il server lo dice e il client lo mostra
    prova("sentinella: la pubblicazione conta le foto", 2,
          _SORGENTE.count('"foto_salvate": len(nomi)'))
    # due chiamate (pubblicazione e modifica) piu' la definizione
    prova("sentinella: e il client lo racconta in due posti", 2,
          mini.count("= avvisoFoto("))
    # 5) salva_foto ha DUE valori di ritorno, e chi la chiama li prende
    # entrambi: con un solo nome l'unpacking esplode subito, ma un
    # terzo chiamante distratto potrebbe scrivere `nomi = salva_foto(...)`
    # e ritrovarsi una tupla dove aspetta una lista
    prova("sentinella: i chiamanti di salva_foto scompattano in due", 2,
          len(re.findall(r"\w+, \w+ = await asyncio.to_thread\(\s*salva_foto|"
                         r"\w+, \w+ = await asyncio\.to_thread\(salva_foto",
                         _SORGENTE)))


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


def prove_savers_proprietario():
    """LO STESSO NUMERO, VISTO DAL PROPRIETARIO (ago 2026): sui propri
    annunci il barattolino non nasce, e col bottone se ne andava il
    conteggio — cioe' il dato che al venditore interessa. Le cinque
    cose che questa famiglia difende, ognuna torturata rompendo il
    codice:
    1) la soglia e' UNO (le due ragioni della soglia pubblica qui non
       valgono) e lo ZERO non scrive niente;
    2) le guardie sono ROVESCIATE: e' un dato del PROPRIETARIO, e a
       chiunque altro il giudice risponde zero;
    3) sui PROPRI annunci il barattolino C'E' (decisione di Andrea che
       ha rovesciato la guardia di sempre) e il tocco SPIEGA col foglio
       di casa invece di non fare niente;
    4) le due rese fuori dal bottone non sono toccabili — un'icona che
       sembra toccabile e non lo e' e' peggio di niente;
    5) l'angolo in alto a destra della card resta di UNO solo: sui
       propri esauriti vince il rifornimento, e la card non guadagna
       mai un terzo bersaglio."""
    print("\n[il conteggio visto dal proprietario]")
    src = open("miniapp.html", encoding="utf-8").read()

    def fun(nome):
        i = src.index(f"function {nome}(")
        return src[i:src.index("\n}", i)]

    g = fun("saversMio")
    prova("il giudice risponde zero a chi non e' il proprietario", True,
          "l.sellerId !== myTgId" in g)
    prova("...e in DEMO e in vetrina non risponde affatto", True,
          "DEMO || VETRINA || !myTgId" in g)
    prova("la soglia del proprietario NON e' quella pubblica", True,
          "contaSavers" not in g and "SOGLIA_SAVERS" not in g)
    # lo zero non scrive niente: tutte e due le rese sono gated su `n`
    for nome in ("saversPunto", "saversFrase"):
        c = fun(nome)
        prova(f"{nome}: lo zero non scrive niente", True,
              "n ?" in c or "if (!n) return ''" in c)
        prova(f"{nome}: non e' un bottone", [],
              [s for s in ("onclick", "<button", "cursor:pointer")
               if s in c])
    prova("la resa in card e' morta col ritorno del barattolino", True,
          "function saversCard" not in src and ".card .meta .savers" not in src)

    # IL BOTTONE C'E' ANCHE SUI PROPRI ANNUNCI, e il tocco spiega
    b = fun("bottoneJar")
    prova("il barattolino nasce anche sui propri annunci", True,
          "l.sellerId===myTgId) return ''" not in b
          and "l.sellerId === myTgId) return ''" not in b)
    prova("...e in DEMO e in vetrina continua a non nascere", True,
          "if (DEMO || VETRINA || !myTgId) return ''" in b)
    prova("sul proprio il tocco apre l'avviso, non il toggle", True,
          "mio ? 'avvisoBarattoloMio()'" in b)
    prova("...e il titolo non promette un gesto che non c'e'", True,
          "mio ? 'Quante persone" in b)
    a = fun("avvisoBarattoloMio")
    prova("l'avviso passa dal foglio di casa", True, "chiediConferma(" in a)
    prova("...in modo avviso: un bottone solo, niente da confermare",
          True, "avviso: true" in a)
    prova("...e non da un dialogo di sistema", [],
          [s for s in ("alert(", "confirm(", "prompt(") if s in a])
    cc = fun("chiediConferma")
    prova("il foglio in modo avviso nasconde il ripensamento", True,
          "el('confNo').style.display = c.avviso ? 'none' : ''" in cc)
    prova("...e l'azione vuota esiste davvero (o il bottone non "
          "chiuderebbe)", True, "c.avviso ? (()=>{}) : null" in cc)
    # la cintura: le altre strade dicono la stessa cosa
    t = fun("togglePreferito")
    prova("togglePreferito non parte sul proprio annuncio", True,
          "avvisoBarattoloMio(); return;" in t)
    # una soglia sola per il bottone e per la riga
    cj = fun("contaJar")
    prova("il numero del bottone passa dal giudice del proprietario",
          True, "saversMio(l) || contaSavers(" in cj)
    prova("...e il bottone chiama LUI, non contaSavers a mano", True,
          "const n = contaJar(l);" in b and "contaSavers" not in b)
    # il barattolino proprio non si fa riscrivere il titolo addosso
    aj = fun("aggiornaJarCards")
    prova("il ripasso dei barattolini salta i propri", True,
          "if (b.dataset.mio) return;" in aj)
    prova("...e il bottone si marca da se'", True, 'data-mio="1"' in b)

    # L'ANGOLO DELLA CARD E' DI UNO SOLO DEI DUE
    i = src.index("const rif = bottoneRifornisci(l);")
    coda = src[i:i + 160]
    prova("sui propri esauriti l'angolo resta del rifornimento", True,
          "const jar = rif ? ''" in coda)

    # ---- E LA REGOLA VALE ANCHE DALL'API (ago 2026, decisione di
    # Andrea: una regola che vive solo nel client e' mezza regola).
    # ESEGUIBILE e non una sentinella sulla forma: il corpo VERO gira
    # su un database di cartone, e si guarda la RIGA — che il rifiuto
    # non abbia scritto niente, e che il proprio annuncio si possa
    # ancora TOGLIERE se una riga di ieri esiste davvero.
    import sqlite3

    class _Err(Exception):
        def __init__(self, codice, testo=""):
            self.codice, self.testo = codice, testo
            super().__init__(f"{codice}: {testo}")

    class _SenzaClose:
        def __init__(self, c): self._c = c
        def __getattr__(self, n): return getattr(self._c, n)
        def close(self): pass

    def apparecchia():
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.executescript("""
        CREATE TABLE annunci(id INTEGER PRIMARY KEY, venditore_id INT,
          stato TEXT);
        CREATE TABLE preferiti(tg_id INT, annuncio_id INT, creato INT,
          PRIMARY KEY(tg_id, annuncio_id));
        INSERT INTO annunci VALUES(7,222,'attivo'),(8,333,'attivo');
        """)
        return con

    def gira(con, chi, annuncio):
        colpi = []
        amb = {"Header": lambda d: d, "Cookie": lambda d: d,
               "HTTPException": _Err, "db": lambda: _SenzaClose(con),
               "verifica_utente": lambda *a: {"id": chi},
               "_conta_barattolo": reale("_conta_barattolo"),
               "_conta_savers": reale("_conta_savers"),
               "MAX_PREFERITI": 10, "MSG_BARATTOLO_MIO": "MIO!",
               "accoda_colpo": lambda a: colpi.append(a),
               "time": type("t", (), {"time": staticmethod(lambda: 1)}),
               "app": type("a", (), {"post": lambda *a, **k:
                                     (lambda f: f)})()}
        exec(corpo_api, amb)
        # si chiama LISCIA: `pezzo` taglia da «def», quindi l'`async`
        # resta fuori — e il corpo non ha un solo await (vedi la prova
        # qui sotto: e' il patto anti-doppione, niente await fra il
        # COUNT del tetto e l'INSERT)
        return amb["toggle_preferito"](annuncio), colpi

    corpo_api = pezzo("toggle_preferito")
    # senza i commenti, o la riga che VIETA l'await lo fa trovare (ci
    # si e' inciampati scrivendo questa prova: il commento nomina
    # apposta quel che proibisce)
    codice_api = "\n".join(r.split("#")[0] for r in corpo_api.splitlines())
    prova("nel toggle non c'e' un solo await (il blocco resta atomico)",
          False, "await " in codice_api)

    con = apparecchia()
    righe = lambda: con.execute("SELECT COUNT(*) FROM preferiti").fetchone()[0]
    try:
        gira(con, 222, 7)                      # il proprio: rifiutato
        prova("l'API rifiuta il proprio annuncio", True, False)
    except _Err as e:
        prova("l'API rifiuta il proprio annuncio", (400, "MIO!"),
              (e.codice, e.testo))
    prova("...e il rifiuto non scrive NIENTE", 0, righe())
    d, colpi = gira(con, 111, 7)               # un altro: passa
    prova("l'annuncio altrui si salva come sempre", True, d["salvato"])
    prova("...e il colpo parte solo per lui", [7], colpi)
    prova("...e la riga c'e'", 1, righe())
    # la riga di un client di ieri si toglie ANCORA: il rifiuto sta
    # nel ramo dell'INSERT, dopo il DELETE
    con.execute("INSERT INTO preferiti VALUES(222,7,1)")
    try:
        d, _ = gira(con, 222, 7)
        esito = (d["ok"], d["salvato"])
    except _Err as e:
        # se il rifiuto salisse sopra il DELETE, quella riga
        # resterebbe li' per sempre: nessuno potrebbe piu' toglierla
        esito = f"rifiutato ({e.codice}): la riga non si toglie piu'"
    prova("una riga vecchia sul proprio si puo' ancora togliere",
          (True, False), esito)
    prova("...e a toglierla resta solo quella dell'altro", 1, righe())
    # la frase e' l'unica che insegna cosa vuol dire il numero
    f = fun("saversFrase")
    prova("la frase nomina il barattolo", True,
          "messo nel barattolo" in f)
    prova("...e concorda al singolare con una persona sola", True,
          "'persona' : 'persone'" in f and "'ha' : 'hanno'" in f)
    prova("...e veste la superficie NEUTRA, non il verde della fiducia",
          True, "trust-note nota-savers" in f)

    # la riga meta della card e' tornata quella di sempre: il comune
    # resta al suo posto per tutti, e il numero vive nella pastiglia
    i = src.find('<div class="meta">')
    riga = src[i:i + 200] if i >= 0 else ""
    prova("in card il comune non cede il posto a nessuno", True,
          '<div class="meta"><span class="luogo">${luogoTesto(l)}'
          '</span>${iconeCard(l)}</div>' in riga)

    # la riga di «I tuoi annunci» e la scheda del proprietario
    prova("«I tuoi annunci» porta il conteggio in coda alla meta", True,
          "${luogoPunto(l)}${saversPunto(l)}</div>" in src)
    prova("la frase sta in testa al blocco del proprietario, fuori dai "
          "tre rami", True, "${mio ? saversFrase(l) : ''}${mio" in src)
    prova("...e si chiama una volta sola (la ereditano tutti e tre)", 1,
          src.count("saversFrase(l)") - src.count("function saversFrase(l)"))

    # LA REGRESSIONE DEL CANTIERE: il commento CSS scritto con «\\*»
    # invece di «/*» non apre niente, e il parser si mangia la regola
    # che segue — qui si e' portato via .nota-punto, che esisteva da
    # prima. Il selettore le veste tutte e due.
    i = src.index(".trust-note.nota-punto")
    prova("la superficie neutra veste il punto E il conteggio", True,
          ".trust-note.nota-punto,.trust-note.nota-savers{" in src[i - 40:i + 90])


def prove_barattolo_in_testata():
    """LA SCORCIATOIA AL BARATTOLO (ago 2026, richiesta di Andrea): la
    stessa icona che si riempie nel cassetto del Profilo, in testata
    accanto alla levetta del tema. E' una SCORCIATOIA e non una vista
    nuova — la lista dei preferiti resta disegnata in un posto solo, ed
    e' la prima cosa che queste prove difendono.
    Prima di oggi questa zona non aveva NESSUNA sentinella: ne' il
    tappo, ne' la levetta, ne' la regia del riempimento."""
    print("\n[il barattolo in testata]")
    import re as _re
    mini = open("miniapp.html", encoding="utf-8").read()
    css = mini[mini.index("<style"):mini.index("</style>")]
    r = pezzo_js(mini, "function renderJarTesta(){", "\n}\n")
    testa = "".join(_re.findall(r'<button class="jar-testa".*?</button>',
                                mini, _re.S))

    # --- 1) LA CLASSE NON PUO' CADERE NELL'ESCLUSIONE ---
    # L'elenco si LEGGE dal codice invece di ribatterlo: il giorno che
    # qualcuno aggiunge una terza classe a quell'esclusione, questa
    # sentinella la copre da sola.
    ag = pezzo_js(mini, "function aggiornaBarattolo(n){", "\n}\n")
    sel = _re.search(r"\.closest\('([^']+)'\)", ag).group(1)
    escluse = [c.strip().lstrip(".") for c in sel.split(",")]
    prova("l'esclusione di aggiornaBarattolo si legge dal codice",
          ["card-jar", "jar-btn"], escluse)
    prova("la scorciatoia non porta nessuna classe esclusa", [],
          [c for c in escluse if c in testa])
    prova("...e la sua icona nasce dalla fabbrica unica", True, "jarSVG(" in r)

    # --- 2) DUE ISTANZE, UNA CLASSE, UN GIRO SOLO ---
    prova("le istanze in markup sono DUE", 2, mini.count('class="jar-testa"'))
    prova("...e la regia le prende per classe, in un giro solo", 1,
          r.count("querySelectorAll('.jar-testa')"))
    prova("...mai per id: un id non si riusa in due", [],
          [s for s in ("getElementById", "el('jarTesta", "#jarTesta") if s in r])
    prova("una in testata e una in topbar", (1, 1),
          (mini[:mini.index("</header>")].count('class="jar-testa"'),
           mini[mini.index("<nav"):mini.index("</nav>")].count('class="jar-testa"')))

    # --- 3) LA GUARDIA E' QUELLA DI bottoneJar, NON QUELLA DEL TAPPO ---
    b = pezzo_js(mini, "function bottoneJar(l, classe, misura, prima){", "\n}\n")
    guardia = _re.search(r"if \((DEMO[^)]+)\) return ''", b).group(1)
    prova("la guardia del barattolino e' quella di sempre",
          "DEMO || VETRINA || !myTgId", guardia)
    prova("la scorciatoia porta LA STESSA guardia", True, guardia in r)
    prova("...cioe' guarda anche DEMO, non il solo !VETRINA del tappo",
          True, "DEMO" in r)
    rp = pezzo_js(mini, "function renderPreferiti(){", "\n}\n")
    prova("in DEMO il cassetto e' nascosto: e' la ragione della guardia",
          True, "if (DEMO || VETRINA) {" in rp and "display = 'none'" in rp)

    # --- 4) LA DESTINAZIONE E' LA STESSA VISTA, NON UNA COPIA ---
    prova("la scorciatoia porta al cassetto che c'e' gia'", 2,
          mini.count("apriCassettoProfilo('accPreferiti')"))
    prova("...e quel cassetto e' uno solo", 1, mini.count('id="accPreferiti"'))
    prova("...e non si inventa una vista sua", [],
          [s for s in ("go('preferiti')", "go('barattolo')",
                       "view-preferiti", "view-barattolo") if s in mini])
    prova("LA LISTA SI DISEGNA IN UN POSTO SOLO", (1, 1, 1, 1),
          (mini.count("myPreferiti.map(l =>"),
           mini.count('id="preferitiBlocco"'),
           mini.count("function renderPreferiti("),
           mini.count("el('preferitiBlocco')")))

    # --- 5) L'ORDINE NEL MARKUP E LA CATENA DEI MARGINI ---
    def fetta(dopo, prima):
        i = mini.index(dopo)
        return mini[i:mini.index(prima, i)]

    for nome, f in (("testata", fetta('<div class="brand">', "</header>")),
                    ("topbar", fetta('<button id="nav-affari"', "</nav>"))):
        prova(f"{nome}: l'ordine e' levetta → barattolo → tappo", True,
              f.index('class="tema-btn"') < f.index('class="jar-testa"')
              < f.index('class="avatar-btn"'))
    prova("la spinta a destra e' della levetta, che c'e' sempre", True,
          ".tema-btn{display:inline-flex;margin-left:auto}" in css)
    i = css.index(".jar-testa{")
    prova("...e non del barattolo, che si spegne", True,
          "margin-left:auto" not in css[i:i + 90])
    # col + la regola smette di combaciare col barattolo in mezzo, e il
    # tappo ricade sul suo auto: DUE auto-margini, e la levetta migra
    # in mezzo alla riga. Silenzioso, e si vede solo sui telefoni larghi.
    prova("il tappo non dipende piu' dall'ADIACENZA della levetta", 0,
          css.count(".tema-btn + .avatar-btn"))
    prova("...ma dalla sola PRECEDENZA, in tutte e due le regole", 2,
          css.count(".tema-btn ~ .avatar-btn"))
    prova("la scorciatoia nasce spenta", True, ".jar-testa{display:none" in css)
    prova("...e si accende solo dove deve, mai nuda", (1, 1, 0),
          (css.count("header .brand .jar-testa.on{display:inline-flex}"),
           css.count("nav .jar-testa.on{display:inline-flex"),
           css.count("\n  .jar-testa.on{")))
    prova("il bersaglio di tocco e' piu' largo del cerchietto", True,
          ".jar-testa::after{content:'';position:absolute;inset:-6px" in css)

    # --- 6) UN DISEGNO SOLO, INIETTATO UNA VOLTA, AL LIVELLO GIUSTO ---
    prova("il vetro e' disegnato in un posto solo", 1,
          mini.count("<clipPath id="))
    prova("...e la clip resta a id unico per istanza", True,
          "'jarClip' + (++jarClipN)" in mini)
    prova("l'icona nasce gia' al livello del barattolo", True,
          "jarSVG(livelloBarattolo(contaBarattolo())" in r)
    prova("...e si inietta una volta sola per nodo", True,
          "!b.querySelector('svg')" in r)
    prova("il vetro PRIMA, l'accensione DOPO", True,
          r.index("innerHTML") < r.index("classList.toggle('on'"))
    prova("nessuna regia nuova: a livellare resta aggiornaBarattolo", 0,
          r.count("classList.add('lv") + r.count("lv4"))

    # --- 7) LE CHIAMATE, E L'ORDINE IN avvia() ---
    prova("la scorciatoia si monta agli stessi punti del tappo",
          mini.count("renderAvatar()"), mini.count("renderJarTesta()"))
    i_avvia = mini.index("async function avvia(){")
    prova("...e in avvia() esiste PRIMA che il riempimento giri", True,
          mini.index("renderJarTesta()", i_avvia)
          < mini.index("await caricaPreferiti()", i_avvia))

    # --- 8) NIENTE NUMERO IN TESTATA ---
    prova("in testata nessun numero: il livello E' il numero", [],
          [s for s in ("jar-conta", "con-conta", "preferitiConta") if s in testa])
    prova("...e il numero del cassetto resta uno solo", 1,
          mini.count('id="preferitiConta"'))

    # --- 9) SCORCIATOIA E DESTINAZIONE SI CHIAMANO UGUALE ---
    prova("la scorciatoia ha il nome del cassetto a cui porta", (2, 2),
          (mini.count('title="Nel tuo barattolo"'),
           mini.count('aria-label="Nel tuo barattolo"')))
    i_acc = mini.index('id="accPreferiti"')
    prova("...ed e' il nome che il cassetto porta davvero", True,
          "Nel tuo barattolo" in mini[i_acc:i_acc + 400])

    # --- 10) LO SPAZIO: LA TESSERA CEDE, E C'E' L'AIRBAG ---
    # A 320px il terzo cerchietto non ci stava: il lockup chiede 124px,
    # la sottolinea 139, il fisso 152, e di contenuto ce n'e' 288.
    prova("sotto i 360 la tessera del logo cede il posto", True,
          "@media (max-width:359.98px){" in css
          and "header .brand-jar{display:none}" in css)
    prova("...ed e' scopata su header: quella classe veste anche la topbar",
          0, css.count("\n    .brand-jar{display:none}"))
    prova("l'airbag: il testo cede invece di far scorrere la PAGINA", True,
          ".brand > div{min-width:0}" in css)
    prova("...e a cedere e' la sottolinea, coi puntini", True,
          ".brand small{overflow:hidden;text-overflow:ellipsis" in css)


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
    # La regola si legge dall'ancora alla graffa e non a finestra
    # fissa: dal cantiere dello stock questi selettori sono CONDIVISI
    # con l'esaurito (stessa lingua, un posto solo da tarare), e una
    # finestra a lunghezza fissa smetterebbe di provare quel che dice
    # al prossimo che li estende.
    def regola(ancora):
        i = mini.index(ancora)
        return mini[i:mini.index("}", i) + 1]

    tag = regola(".tag-price.ferie .price")
    prova("il cartellino usa un grigio fisso, non il token", True,
          "#8A8271" in tag and "--muted" not in tag)
    # nel dettaglio invece il token e' quello giusto (sta sulla pagina)
    det = regola(".detail-price.ferie")
    prova("il dettaglio segue il tema col token", True,
          "var(--muted)" in det)
    # e NESSUNA delle due nomina .unit (la regola dichiarata)
    prova("nessuna regola di stato ferie nomina .unit", True,
          ".unit" not in tag and ".unit" not in det)

    # 41: la barra d'acquisto non nasce a negozio chiuso
    prova("la barra d'acquisto tace in ferie", True,
          "&& !inFerie(l)" in mini)


def prove_stock_raccontato():
    """«Lo stock raccontato bene» (ago 2026): l'annuncio esaurito non
    sparisce piu' del tutto — resta raggiungibile dal link condiviso e
    nello scaffale in fondo al negozio — e il badge «ultimo pezzo»
    parla SOLO dove la scarsita' e' una notizia.
    Il pezzo che conta e' `quantita_max`: non scende MAI, e la scopa
    che la ripara e' anche il backfill onesto dello storico. Se
    qualcuno la assegnasse secca, una ricarica a un pezzo dopo averne
    avuti dieci cancellerebbe quella memoria in silenzio — e il badge
    direbbe di no proprio quando dice il vero."""
    print("\n[lo stock raccontato bene]")
    import sqlite3

    def corpo(nome):
        i = _SORGENTE.index(f"def {nome}(")
        return _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]

    def solo_codice(c):
        """Il corpo SENZA la docstring — la lezione di prove_ferie,
        ripagata subito: la docstring di `un_annuncio` NOMINA apposta
        i due stati che restano 404, quindi cercarli nel testo intero
        dava verdetti rovesciati."""
        p = c.split('"""')
        return p[0] + "".join(p[2:]) if len(p) > 2 else c

    # ---- 1-7: il giudice puro, sui casi che decidono ----
    amb = {}
    exec(pezzo("ultimo_pezzo"), amb)
    up = amb["ultimo_pezzo"]
    # L'OGGETTO UNICO: e' la ragione per cui la colonna esiste. Su un
    # mercatino dell'usato quasi tutto e' cosi', e un badge acceso qui
    # sarebbe vero e insignificante.
    prova("ultimo: un pezzo unico NON e' una notizia", False, up(1, 1))
    prova("ultimo: ne aveva due, ne resta uno", True, up(1, 2))
    prova("ultimo: ne aveva cinque, ne resta uno", True, up(1, 5))
    prova("ultimo: gliene restano due, non e' ancora l'ultimo",
          False, up(2, 5))
    prova("ultimo: l'esaurito e' falso da solo", False, up(0, 5))
    # Nel dubbio si tace: un massimo a zero e' «non lo so ancora»
    # (storico non riallineato, importato appena nato), mai un'urgenza.
    prova("ultimo: massimo sconosciuto = si tace", False, up(1, 0))
    # E la finestra dell'import, che il libro mastro NON sorveglia
    # apposta: quantita sopra il massimo non e' un guasto, e' la scopa
    # che deve ancora passare.
    prova("ultimo: quantita sopra il massimo non accende niente",
          False, up(5, 1))

    # ---- 8-13: la scopa, girata DAVVERO su un database di cartone ----
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE annunci(id INTEGER PRIMARY KEY, "
                "quantita INT, quantita_max INT)")
    con.executemany("INSERT INTO annunci VALUES(?,?,?)", [
        (1, 7, 0),    # lo storico: non lo sappiamo, ne ha almeno 7
        (2, 3, 3),    # gia' in pari
        (3, 1, 9),    # ne ha avuti nove: NON deve scendere
        (4, 0, 4),    # esaurito: non si tocca
    ])
    amb2 = {}
    exec(pezzo("riallinea_quantita_max"), amb2)
    amb2["riallinea_quantita_max"](con)
    leggi = lambda i: tuple(con.execute(
        "SELECT quantita, quantita_max FROM annunci WHERE id=?",
        (i,)).fetchone())
    prova("scopa: il backfill onesto dello storico", (7, 7), leggi(1))
    prova("scopa: chi e' in pari non si tocca", (3, 3), leggi(2))
    prova("scopa: NON abbassa mai il massimo", (1, 9), leggi(3))
    prova("scopa: l'esaurito resta com'e'", (0, 4), leggi(4))
    prima = [leggi(i) for i in (1, 2, 3, 4)]
    amb2["riallinea_quantita_max"](con)
    prova("scopa: idempotente al secondo giro", prima,
          [leggi(i) for i in (1, 2, 3, 4)])
    # La scopa LEGGE E ALZA, mai il contrario
    prova("scopa: una riga sola, e non abbassa", True,
          "quantita>quantita_max" in corpo("riallinea_quantita_max")
          and "MIN(" not in corpo("riallinea_quantita_max"))

    # ---- 14-19: il massimo si alza col MAX, mai secco ----
    # E' la sentinella che vale di piu': un'assegnazione secca non
    # rompe niente di visibile, cancella solo la memoria.
    for nome in ("ricarica_quantita", "modifica_annuncio"):
        prova(f"il massimo sale col MAX: {nome}", True,
              "quantita_max=MAX(quantita_max," in corpo(nome))
    # il rimborso: aveva 3, li vende tutti, ricarica a 1, e una disputa
    # gliene rimborsa 3 — cioe' 4, sopra il massimo di ieri
    prova("il massimo sale col MAX anche nel rimborso", True,
          "quantita_max=MAX(quantita_max,quantita+?)" in _SORGENTE)
    # i due INSERT, che sono DUE: l'import CSV ha una vita sua
    prova("i due INSERT scrivono il massimo", 2,
          _SORGENTE.count("quantita,quantita_max,stato"))
    # e chi SCENDE non lo tocca mai
    prova("la vendita non tocca il massimo (SCENDE)", False,
          "quantita_max" in corpo("_incassa_ordine"))
    # la scopa gira in DUE posti: avvio e dopo-import
    prova("la scopa gira all'avvio e dopo l'import", 3,
          _SORGENTE.count("riallinea_quantita_max("))

    # ---- 20-22: il numero grezzo non esce da NESSUNA rotta ----
    arr = corpo("arricchisci_righe_vetrina")
    prova("il massimo grezzo se ne va col pop", True,
          'r.pop("quantita_max")' in arr)
    prova("il flag lo decide il giudice, non un confronto a mano", True,
          "ultimo_pezzo(" in arr)
    # importa_nostr.py deve restare CIECO alla colonna, o smette di
    # girare da solo su un Barattolo piu' vecchio
    imp = open("importa_nostr.py", encoding="utf-8").read()
    prova("l'import Nostr non conosce la colonna", False,
          "quantita_max" in imp)

    # ---- 23-26: la porta del link condiviso ----
    un = solo_codice(corpo("un_annuncio"))
    prova("il singolo serve anche gli esauriti", True,
          "a.stato IN ('attivo','venduto')" in un)
    prova("...e manda lo stato, o la scheda lo disegna comprabile",
          True, "a.stato" in un)
    prova("il rimosso resta un 404", False, "'rimosso'" in un)
    prova("la revisione resta un 404", False, "'revisione'" in un)

    # ---- 27-30: cio' che NON deve cambiare ----
    prova("la vetrina resta ai soli attivi", True,
          'dove = "a.stato=\'attivo\'"' in corpo("lista_annunci"))
    prova("la ricerca AI resta ai soli attivi", True,
          "WHERE a.stato='attivo'" in corpo("cerca"))
    neg = corpo("negozio")
    prova("nel negozio gli attivi tengono il loro filtro", True,
          "dove = \"a.venditore_id=? AND a.stato='attivo'\"" in neg)
    # lo scaffale e' una query A PARTE: non entra nel `dove`, quindi
    # non tocca ne' `totale` ne' il cursore
    prova("lo scaffale non entra nel conteggio degli attivi", True,
          neg.index("totale = con.execute") < neg.index("a.stato='venduto'"))

    # ---- 31-40: il client ----
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client ha il suo giudice dell'esaurito", True,
          "function esaurito(l){" in mini)
    # L'ASTA NON E' MAI ESAURITA: ha un aggiudicatario, non stock — ed
    # e' la stessa riga che il server ha gia' scritto nella ricarica.
    prova("l'asta non e' mai esaurita (client)", True,
          "&& !astaE(l)" in pezzo_js(mini, "function esaurito(l){"))
    prova("...e il server la rifiuta per natura", True,
          'asta_base_sats"] > 0' in corpo("ricarica_quantita"))
    prova("il flag arriva dal server, non si deriva da quantita===1",
          True, "l.ultimo" in mini and "ultimo:!!a.ultimo," in mini)
    # il badge di casa non inventa un colore: e' la CARTA
    i = mini.index(".card-ultimo{")
    reg = mini[i:mini.index("}", i)]
    prova("il badge ultimo non prende un colore nuovo", True,
          "255,248,234" in reg and "--lampo" not in reg
          and "--asta" not in reg and "--sats" not in reg)
    prova("il rifornimento sulla card ha le guardie del server", True,
          "astaE(l) || l.nostr" in pezzo_js(
              mini, "function bottoneRifornisci(l){"))
    prova("il prompt() del rifornimento non esiste piu'", False,
          "ricaricaAnnuncio" in pezzo_js(mini, "function renderMyListings"))
    prova("il foglio si chiude con gli altri", True,
          "el('rifornisciSheet').classList.remove('open')" in mini)
    # La scheda dell'esaurito non deve mai arrivare al recinto — e fra
    # i due c'e' la CINTURA che ferma ogni altro stato non attivo. Si
    # legge il tratto FRA le due ancore invece di confrontare due
    # offset: cosi' l'ordine e la presenza si provano insieme, e
    # nessuna delle due puo' pescare un'occorrenza di un altro ramo.
    i = mini.index(": esa\n")
    fra = mini[i:mini.index('`<div class="escrow-zone">', i)]
    prova("fra l'esaurito e il recinto c'e' la cintura degli stati",
          True, "(l.stato||'attivo') !== 'attivo'" in fra)
    # e la lampo tace: le colonne restano vive anche a scorte finite
    prova("il countdown della lampo tace su un esaurito", True,
          "${!esa && !ferie && !asta && lampoAttiva(l)?" in mini)


def prove_firme_nostr():
    """L'annuncio di un doppio cittadino va sul SUO account Nostr
    (ago 2026). Il pezzo che conta e' il NON FATTO: quando il
    venditore ha una chiave provata, la piattaforma non deve firmare
    niente — ne' l'annuncio, ne' il «venduto», ne' la cancellazione.
    Se un domani qualcuno togliesse il bivio, quegli eventi
    tornerebbero a nome di Barattolo in silenzio."""
    print("\n[le firme dei doppi cittadini]")

    # 1. Chi ha una chiave PROVATA (la regola di notifica() e dei ponti)
    amb = {}
    exec(pezzo("npub_to_hex"), amb)
    exec(pezzo("chiave_nostr_provata"), amb)
    prova_k = amb["chiave_nostr_provata"]
    HEX = "a" * 64

    class Riga(dict):
        def keys(self):
            return dict.keys(self)

    npub = amb["hex_to_npub"](HEX) if "hex_to_npub" in amb else None
    prova("senza utente nessuna chiave", "", prova_k(None))
    prova("npub NUDA non basta (e' una dichiarazione)", "",
          prova_k(Riga(npub="npub1storta", npub_verificata=0,
                       npub_accesso="")))

    # 2. IL BIVIO nel funnel: se il venditore ha una chiave sua, si
    #    accoda invece di firmare. Si guarda il corpo, che e' l'unico
    #    posto dove quella decisione vive.
    corpo = pezzo("annuncio_su_nostr")
    prova("il funnel guarda la chiave del venditore", True,
          "chiave_nostr_provata" in corpo)
    prova("...e in quel caso ACCODA", True, "accoda_firma" in corpo)
    # Il ramo dell'utente deve uscire PRIMA di firmare: se il return
    # sparisse, si firmerebbe due volte lo stesso annuncio
    i = corpo.index("chiave_nostr_provata")
    j = corpo.index("evento_annuncio(dict(a)")
    prova("...e esce prima che la piattaforma firmi", True,
          "return" in corpo[i:j])

    # 3. La cancellazione: una NIP-09 nostra su un evento altrui non
    #    la accetta nessun relay serio, e sarebbe pure scorretta
    ritiro = pezzo("ritira_da_nostr")
    prova("il ritiro guarda chi ha firmato", True, "nostr_autore" in ritiro)
    prova("...e su un evento altrui accoda", True, "accoda_firma" in ritiro)

    # 4. Una firma sola per annuncio: l'ultima vince (venduto e poi
    #    rimborsato fa 'active', non due firme da chiedere)
    coda = _SORGENTE[_SORGENTE.index("CREATE TABLE IF NOT EXISTS firme_nostr"):]
    coda = coda[:coda.index(");")]
    prova("una riga per annuncio", True, "annuncio_id INTEGER PRIMARY KEY" in coda)
    prova("l'ultima azione vince", True,
          "DO UPDATE SET" in pezzo("accoda_firma"))

    # 5. Il sollecito e' OPT-IN, e il gate sta nella QUERY cioe' PRIMA
    #    del timbro: se contasse anche a levetta spenta, chi la
    #    accendesse fra un mese troverebbe il contatore gia' al tetto
    #    e non riceverebbe mai il promemoria appena chiesto. E' la
    #    trappola gia' pagata con completamento_avvisato.
    soll = pezzo("sollecita_firme_nostr")
    prova("il sollecito e' opt-in", True,
          "u.suggerimenti_annunci=1" in soll)
    i = soll.index("suggerimenti_annunci=1")
    j = soll.index("solleciti_firme=solleciti_firme+1")
    prova("...e il gate viene PRIMA del timbro", True, i < j)
    # Nessun 🧊 ai moderatori: qui non ci sono sats fermi
    prova("nessuna segnalazione ai moderatori", False,
          "notifica_admin" in soll)


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
    # SI LEGGE A VOCI E NON A RIGHE (ago 2026): il lettore vecchio
    # prendeva una riga alla volta, e la prima voce che ha avuto
    # bisogno di due righe — Poste, coi formati veri del registro —
    # e' sparita dal conto senza che nessuna prova sui suoi codici
    # diventasse rossa: erano semplicemente smesse di girare. Adesso
    # si taglia fra una chiave e l'altra e si pescano le regex, che
    # cominciano tutte per ^ e finiscono per $.
    chiavi = [(m.start(), m.group(1))
              for m in re.finditer(r"'([^']+)':\s*\[", blocco)]
    forme = {}
    for k, (pos, nome) in enumerate(chiavi):
        fine = chiavi[k + 1][0] if k + 1 < len(chiavi) else len(blocco)
        forme[nome] = [re.compile(x) for x in
                       re.findall(r"/(\^.+?\$)/", blocco[pos:fine])]
    prova("il catalogo delle forme si e' letto tutto", 7, len(forme))
    # ...e nessuna voce e' rimasta VUOTA: una voce senza forme non fa
    # rossa nessuna prova, si limita a non controllare piu' niente.
    prova("...e nessuna voce e' rimasta senza forme", [],
          [n for n, f in forme.items() if not f])

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
             # I TRE CODICI VERI del registro (ago 2026, dal caso dal
             # campo): stavano tutti fuori dalle due forme di prima, e
             # senza di loro togliere le forme nuove non faceva rossa
             # nessuna prova — l'ha detto la tortura.
             ("Poste Italiane", "281665J055082"),
             ("Poste Italiane", "281665J056083"),
             ("Poste Italiane", "JF40001609169"),
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

    # LE NOTIFICHE DEL PACCO via @trackbot (ago 2026): il giudice
    # della forma e' lo STESSO dell'euristica qui sopra — il codice
    # dell'intermediario, che per il corriere dichiarato ha la forma
    # storta, non arriva mai a trackbot.
    # Dall'ago 2026 il giudice e' anche UNO SOLO per i due posti da cui
    # ci si arriva — il bottone e il codice dentro il recinto: due
    # strade che rispondessero diverso sullo stesso codice sarebbero
    # una che promette quel che l'altra nega.
    tp = pezzo_js(src, "function trackbotPossibile")
    # QUESTA PROVA HA CAMBIATO LATO DUE VOLTE NELLO STESSO GIORNO
    # (12 ago 2026, decisione di Andrea): chiedeva «solo il
    # compratore», poi «le due parti» — il venditore segue la stessa
    # spedizione e verso un punto di ritiro deve sapere quando il
    # pacco arriva per mandare la busta — e infine il ruolo e' sparito
    # del tutto: il moderatore incontra uno shipped solo da «apri un
    # ordine per numero», che esiste proprio per i tracciamenti
    # storti, e li' il tocco sul codice e' una diagnosi. In disputa il
    # codice resta testo per TUTTI: e' la regola dello STATO, non del
    # ruolo, e questa riga chiede che il ruolo non rientri di
    # soppiatto.
    prova("trackbot: il ruolo non decide — la porta e' dello stato",
          True, "o.role" not in tp)
    prova("trackbot: solo col tracciamento", True, "!!o.tracking" in tp)
    prova("trackbot: solo mentre il pacco viaggia", True,
          "['shipped','delivered'].includes(s)" in tp)
    # QUESTA PROVA HA CAMBIATO LATO (ago 2026, decisione di Andrea):
    # chiedeva che il giudice del bottone fosse `formaTracking`, cioe'
    # che il codice avesse la FORMA del corriere dichiarato. Il motivo
    # era buono — a trackbot serve il codice del CORRIERE — ma il
    # prezzo lo pagavano i codici che NON conosciamo, che sono quelli
    # su cui sbagliamo noi: un Poste `281665J056083` vero, fuori dalle
    # nostre forme, perdeva il grassetto e il bottone IN SILENZIO. E
    # `FORME_TRACKING` e' dichiarata un'euristica che «non blocca
    # MAI»: di qui bloccava lo stesso, per interposta persona.
    # SI TOGLIE SU QUEL CHE SAPPIAMO, non su quel che non sappiamo.
    prova("trackbot: il giudice NON e' piu' l'euristica delle forme",
          True, "formaTracking" not in tp)
    prova("...e' il riconoscimento dell'intermediario", True,
          "!intermediarioNoto(o.tracking)" in tp)
    prova("...e formaTracking resta UNO", 1,
          src.count("function formaTracking"))
    # L'EURISTICA NON PERDE IL SUO MESTIERE: continua a chiedere «sei
    # sicuro?» al VENDITORE mentre scrive, che e' dove l'errore si
    # ripara — con chi l'ha fatto e col codice sotto le dita.
    prova("...e continua a chiedere al venditore quando spedisce", True,
          "formaTracking(corriere, tracking)" in
          pezzo_js(src, "function trackingDaControllare"))
    # GLI INTERMEDIARI SI RICONOSCONO PER NOME, la sola cosa certa: un
    # codice di corriere non contiene mai la parola «packlink». Le
    # regex non c'entrano — si guardano le lettere.
    ino = pezzo_js(src, "function intermediarioNoto")
    prova("l'intermediario si riconosce per nome, non per forma", True,
          "INTERMEDIARI.find" in ino and "toLowerCase()" in ino)
    prova("...e le cifre non nascondono il nome", True,
          "replace(/[^a-z]/g, '')" in ino)
    # LA PROVA CHE IL CASO HA CHIESTO: il codice che non conosciamo
    # tiene il bottone. Si esegue il giudice VERO, tradotto dal
    # sorgente, sui codici veri del registro.
    nomi = re.search(r"const INTERMEDIARI = \[(.+?)\];", src, re.S)
    prova("il catalogo degli intermediari si e' letto", True, bool(nomi))
    # IL CATALOGO E' TUTTO MINUSCOLO, o la voce e' MORTA: il client
    # abbassa il tracciamento e confronta le voci COSI' COME SONO,
    # quindi una scritta in maiuscolo non matcherebbe mai — e non lo
    # direbbe nessuno.
    voci = re.findall(r"'([^']*)'", nomi.group(1) if nomi else "")
    prova("...e le sue voci sono tutte minuscole", [],
          [v for v in voci if v != v.lower() or not v.isalpha()])
    elenco = re.findall(r"'([a-z]+)'", nomi.group(1) if nomi else "")
    def noto(t):
        lettere = re.sub(r"[^a-z]", "", (t or "").lower())
        return next((n for n in elenco if n in lettere), "")
    for codice in ("281665J055082", "281665J056083", "JF40001609169",
                   "RR123456789IT", "820123387637068013332765",
                   "IT2026COM8891"):
        prova("il codice che non conosciamo tiene il bottone: " + codice,
              "", noto(codice))
    prova("...e quello che si dichiara Packlink no", "packlink",
          noto("PACKLINK-4471-0093"))
    prova("il giudice serve tutti e due i posti", 2,
          src.count("trackbotPossibile(o, s)")
          - src.count("function trackbotPossibile(o, s)"))
    prova("...e il bottone non ne tiene uno suo", 1,
          pezzo_js(src, "function bottoneNotifichePacco").count("if ("))
    # IL CODICE SI TOCCA DOVE SI LEGGE, dentro il passo «Oggetto
    # spedito»; senza porta resta TESTO, che un link a vuoto e' peggio
    # di nessun link — e in tutti e due i rami passa da esc(), che e'
    # testo di chi vende su un tubo HTML.
    ct = pezzo_js(src, "function codiceTracking")
    prova("il codice cliccabile chiama attivaNotifichePacco", True,
          "attivaNotifichePacco()" in ct)
    prova("...e senza porta resta testo", 2, ct.count("esc(o.tracking)"))
    # UN CODICE SI LEGGE COME UN CODICE (ago 2026, dal caso di un
    # ordine vero): quando il riquadro col tracciamento e' sparito, il
    # codice e' rimasto in una riga grigia di prosa e non lo trovava
    # piu' nessuno. Mono e grassetto in TUTTI E DUE i rami, come
    # l'aveva nel riquadro — senza la tortura questa riga tornava
    # prosa senza far rossa nessuna prova.
    prova("il codice si legge come un codice, non come prosa", 2,
          ct.count('mono"'))
    prova("...anche dove non e' toccabile", True,
          '`<b class="mono">${esc(o.tracking)}</b>`' in ct)
    prova("il passo «Oggetto spedito» usa la fabbrica", True,
          "tracking ${codiceTracking(o, s)}" in src)
    # la traccia della correzione del moderatore ha seguito il codice:
    # stava nel banner sparito, e la vedono ENTRAMBE le parti come prima
    prova("...e si porta dietro la traccia del moderatore", True,
          "${codiceTracking(o, s)}${rigaCorretto(o.trackingCorretto)}"
          in src)
    prova("trackbot: il deep link e' uno e vive nell'helper", 1,
          src.count("https://t.me/trackbot?start="))
    prova("trackbot: dentro Telegram passa da openTelegramLink", True,
          "tg.openTelegramLink(url)" in
          pezzo_js(src, "async function attivaNotifichePacco"))
    prova("trackbot: la riga dice CHI manda le notifiche", True,
          "te le manda @trackbot, non Barattolo" in src)
    # IL CODICE NON GLIELO SAPPIAMO CONSEGNARE (ago 2026, dal campo):
    # il payload resta attaccato al link — costa zero — ma la riga non
    # promette piu' che il bot lo capisca: dice che il codice sta negli
    # appunti e va incollato. Se un domani trackbot lo accettasse,
    # queste tre righe sono l'unica cosa da cambiare.
    an = pezzo_js(src, "async function attivaNotifichePacco")
    prova("...e che il codice va INCOLLATO a mano", True,
          "<b>incollalo nel bot</b>" in src)
    prova("...il toast dice la stessa cosa", True,
          "Codice copiato — incollalo nel bot" in an)
    prova("...e se la copia non riesce non lo dice", True,
          "copiato = false" in an and "Copia il codice qui sopra" in an)
    # IL FILTRO DI TRACKBOT (ago 2026, detto da loro): la funzione
    # /start c'e' dal 2018, e il payload lo guarda contro
    # ^[A-Z0-9]{8,26}$ — una minuscola, uno spazio o un trattino lo
    # fanno cadere, e cade in SILENZIO. La prova non rilegge la riga:
    # ESTRAE la classe di caratteri dal sorgente, la applica ai codici
    # come la gente li scrive e chiede che il payload ci rientri —
    # chi rimette il trattino (o il trattino basso, che ammetteva
    # Telegram e non trackbot) nella classe la fa rossa.
    # I DUE GIUDICI VIVONO IN UN POSTO SOLO, e la prova li LEGGE di
    # li' invece di ricopiarli: il numero del filtro e' di TRACKBOT,
    # e una copia in prove.py sarebbe il secondo posto dove tenerlo
    # in pari — cioe' quello che un giorno dice un'altra cosa.
    nt = pezzo_js(src, "function nudoTrackbot")
    classe = re.search(r"\.replace\(/(\[[^/]+\])/g", nt)
    prova("trackbot: il payload si normalizza in un posto solo", True,
          bool(classe) and "toUpperCase()" in nt)
    nudo = ((lambda t: re.sub(classe.group(1), '', t.upper()))
            if classe else (lambda t: t))
    tetto = re.search(r"const FILTRO_TRACKBOT = /(\^\[A-Z0-9\]"
                      r"\{\d+,\d+\}\$)/", src)
    prova("trackbot: il filtro vive nel client, non qui", True,
          bool(tetto))
    FILTRO = re.compile(tetto.group(1) if tetto else r"$^")
    # IL NUMERO E' LORO: se questa riga diventa rossa, o trackbot ha
    # mosso il tetto (e allora si aggiorna qui, con la data) o
    # qualcuno l'ha allargato per conto suo, che e' la cosa da non
    # fare — un filtro nostro piu' largo del loro rimette il
    # fallimento silenzioso da cui e' partito tutto.
    # SI GUARDA LA COSTANTE E NON IL FILE: scritta come «"{10,26}" in
    # src» questa prova NON POTEVA FALLIRE, perche' il numero compare
    # anche nel commento due righe sopra la costante — l'ha detto la
    # tortura, non la rilettura.
    prova("trackbot: i due bordi sono quelli che dicono loro "
          "(12 ago 2026)",
          "^[A-Z0-9]{8,26}$", tetto.group(1) if tetto else '')
    for come, scritto in (("minuscole",       "rr123456789it"),
                          ("spazi",           "RR 123 456 789 IT"),
                          ("trattini",        "1Z-999AA1-0123-456784"),
                          ("trattino basso",  "JJD_01_4600_0035_2246")):
        prova("trackbot: il payload passa il filtro con " + come, True,
              bool(FILTRO.match(nudo(scritto))))
    # QUESTA PROVA HA CAMBIATO LATO (ago 2026): chiedeva che negli
    # appunti andasse `vero`, cioe' il codice con gli spazi che il
    # corriere ci stampa sopra — e quel testo ha UN mestiere solo,
    # essere incollato in trackbot, quindi con un parser di chat
    # severo quanto quello del payload la copia falliva per la stessa
    # ragione del link. Ora negli appunti va il nudo.
    prova("trackbot: negli appunti va il codice nudo", True,
          "writeText(nudo)" in an)
    # E QUEL CHE SI MOSTRA NON SI TOCCA, che e' l'altra meta': in
    # pagina il codice resta quello del venditore (lo dice gia'
    # `esc(o.tracking)` nei due rami di codiceTracking, sopra) e nel
    # database non lo tocca nessuno — di qui non parte nessuna POST.
    prova("...ma quel che si mostra resta il codice del venditore",
          True, "esc(o.tracking)" in ct and "vero" not in ct)
    prova("...e la copia non riscrive niente", 0,
          an.count("fetch(") + an.count("POST"))
    # QUESTA PROVA HA CAMBIATO LATO (11 ago 2026): chiedeva che i 24
    # dell'InPost restassero FUORI dal filtro, ed era il segnale
    # armato apposta — trackbot ha alzato il tetto da 22 a 26 su
    # nostra richiesta, e da allora ci rientrano l'InPost (misurato:
    # 3 codici veri su 3, e uno provato dal vivo) e i DHL eCommerce
    # lunghi, che arrivano a 26 tondi. Il codice qui e' SINTETICO
    # della stessa forma: un tracciamento vero e' di una spedizione
    # di qualcuno, e nel repo non ci va.
    prova("trackbot: i 24 dell'InPost ci rientrano", True,
          bool(FILTRO.match(nudo("6300 0123 4567 8901 2345 6789"))))
    prova("...e i DHL eCommerce lunghi arrivano a 26 tondi", True,
          bool(FILTRO.match(nudo("JVGL-0123456789-0123456789-12"))))
    # QUESTA PROVA HA CAMBIATO LATO (12 ago 2026): chiedeva che i 9
    # cifre di GLS/SDA/UPS restassero FUORI — trackbot ha abbassato il
    # pavimento da 10 a 8 di sua iniziativa, e ci sono rientrati. Era
    # l'ultima famiglia di corriere che restava fuori: adesso nessuna
    # forma del nostro catalogo sta sotto il minimo (la piu' corta e'
    # 9), e sotto gli 8 ci finiscono solo i codici liberi di «Altro
    # corriere».
    prova("trackbot: i 9 cifre dei GLS Europe ci rientrano", True,
          bool(FILTRO.match(nudo("1234-56789"))))
    # ...e IL PAVIMENTO VA SORVEGLIATO LO STESSO, o un domani lo si
    # alza senza che nessuno lo veda: sette caratteri restano fuori.
    prova("trackbot: sotto il pavimento si resta fuori", False,
          bool(FILTRO.match(nudo("12-34567"))))
    # ...e il filtro NON e' una guardia del bottone: chi non ci rientra
    # ha comunque la strada di sempre, incollare a mano. Si guarda la
    # FORMA della ripetizione e non i numeri, o alla prossima volta
    # che trackbot muove un bordo questa riga passa senza dire niente
    # (e i bordi si sono gia' mossi due volte in due giorni).
    prova("...ma il bottone non li esclude", True,
          not re.search(r"\{\d+,", tp) and "passaTrackbot" not in tp)
    # IL FILTRO DECIDE LE PAROLE, MAI LA PRESENZA DEL BOTTONE (11 ago
    # 2026): la didascalia si sdoppia — a chi il codice il bot lo
    # prende si dice che ci pensiamo noi, a chi resta fuori resta
    # l'istruzione di ieri. Dire «apri e ci pensa lui» a chi il bot
    # non lo prende sarebbe il fallimento silenzioso riscritto in
    # italiano.
    bn = pezzo_js(src, "function bottoneNotifichePacco")
    prova("la didascalia si sdoppia sul filtro", True,
          "passaTrackbot(o.tracking)" in bn)
    prova("...un ramo dice che il codice glielo passiamo noi", True,
          "apri e il codice glielo passiamo noi" in bn)
    prova("...l'altro resta l'istruzione di ieri", True,
          "<b>incollalo nel bot</b>" in bn)
    # «te le manda @trackbot, non Barattolo» sta nei DUE rami: e'
    # l'onesta' sul terzo, e non dipende da come e' fatto il codice.
    # Si contano i due TESTI e non le occorrenze — il commento qui
    # sopra la nomina, e conterebbe tre.
    prova("...e tutti e due dicono CHI manda le notifiche", 2,
          bn.count("te le manda @trackbot, non Barattolo: "))
    # IL TOAST SEGUE LE PAROLE: dove il bot prende il codice non si
    # dice niente — un toast che invita a incollare a mano una cosa
    # appena consegnata e' peggio del silenzio. Ma la COPIA si fa
    # sempre: e' la rete, e non costa niente.
    prova("il toast parla solo a chi resta fuori dal filtro", True,
          "if (!passaTrackbot(vero)) {" in an)
    prova("...ma la copia si fa comunque", True,
          an.index("writeText(nudo)") < an.index("passaTrackbot(vero)"))
    # IL FATTO su come arriva il codice (ago 2026): una costante, due
    # pannelli — la busta del venditore e il form di spedizione via
    # punto. Il fatto, mai l'istruzione.
    prova("la riga del codice: una costante", 1,
          src.count("const RIGA_CODICE_CORRIERE"))
    prova("...detta nei due pannelli", 2,
          src.count("${RIGA_CODICE_CORRIERE}"))
    prova("...e dice il fatto, non l'istruzione", True,
          "ai recapiti che hai indicato come destinatario" in src
          and "metti i tuoi recapiti" not in src)


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
def prove_supplemento_spedizione():
    """IL SUPPLEMENTO PER PEZZO (ago 2026, caso dal campo: il riso da
    4 kg venduto a sacchi con la spedizione di UNO dichiarata). La
    regola sta in una riga — la spedizione piu' cara fa da base, e
    ogni altro pezzo aggiunge il suo supplemento — e qui si tortura
    da sola: e' il posto dove un errore costa sats veri, e la pura
    nasce provata PRIMA che i quattro chiamanti la usino."""
    print("\n[il supplemento di spedizione per pezzo]")
    amb = {}
    for f in ("_tariffa_dichiarata", "_sped_in_sats", "_sped_pacco"):
        exec(pezzo(f), amb)
    pacco = amb["_sped_pacco"]
    CAMBIO = 100_000.0                 # 1.000 sats = 1 euro, tondo

    def a(base=0, extra=0, base_eur=0.0, extra_eur=0.0, punto=None):
        """Un annuncio ridotto ai soli campi della spedizione."""
        return {"spedizione_sats": base, "spedizione_eur": base_eur,
                "spedizione_punto_sats": (punto or 0),
                "spedizione_punto_eur": 0.0,
                "spedizione_punto_dichiarata": 1 if punto is not None else 0,
                "spedizione_extra_sats": extra,
                "spedizione_extra_eur": extra_eur}

    def sats(righe, via="casa", cambio=0.0):
        return pacco(righe, via, cambio)["sats"]

    # --- IL PATTO COL MONDO DI IERI: campo vuoto ⇒ identico a oggi ---
    # se questo cantiere spostasse di un sat il conto di prima, queste
    # quattro diventano rosse tutte insieme
    for q in (1, 2, 10):
        prova(f"vuoto, mono x{q}: e' la tariffa di sempre", 500,
              sats([(a(base=500), q)]))
    prova("vuoto, set a 3 righe: e' il MAX di sempre", 700,
          sats([(a(base=400), 2), (a(base=700), 1), (a(base=300), 5)]))

    # --- LA FORMULA, sugli esempi del cantiere -----------------------
    prova("10 sacchi (base 6.000, supp 3.000) → 33.000", 33_000,
          sats([(a(base=6_000, extra=3_000), 10)]))
    prova("...ed e' base + (q-1) x supp", 33_000, 6_000 + 9 * 3_000)
    prova("un pezzo solo non paga MAI il supplemento", 6_000,
          sats([(a(base=6_000, extra=3_000), 1)]))
    prova("riso + collanina → 7.000 (base del riso + supp della collanina)",
          7_000, sats([(a(base=6_000, extra=3_000), 1),
                       (a(base=2_000, extra=1_000), 1)]))

    # --- IL PAREGGIO: si assorbe il supplemento piu' GRANDE ----------
    coppia = [(a(base=5_000, extra=3_000), 1), (a(base=5_000, extra=1_000), 1)]
    prova("pareggio: si assorbe il supplemento piu' grande", 6_000,
          sats(coppia))
    prova("...e le due permutazioni dicono lo stesso numero",
          sats(coppia), sats(list(reversed(coppia))))

    # --- LE DUE PROPRIETA' STRUTTURALI, a fuzz con seme fisso --------
    import random
    rnd = random.Random(20260806)
    sotto, giu = 0, 0
    for _ in range(200):
        righe = [(a(base=rnd.randrange(0, 9_000),
                    extra=rnd.randrange(0, 4_000)), rnd.randint(1, 6))
                 for _ in range(rnd.randint(1, 5))]
        max_ieri = max(x["spedizione_sats"] for x, _ in righe)
        if sats(righe) < max_ieri:
            sotto += 1
        # monotonia: un pezzo in piu' non abbassa mai il totale
        piu = [(x, q + 1) for x, q in righe]
        if sats(piu) < sats(righe):
            giu += 1
    prova("mai sotto il MAX di ieri (200 combinazioni)", 0, sotto)
    prova("un pezzo in piu' non abbassa mai il totale", 0, giu)

    # --- BASE ZERO + SUPPLEMENTO: e qui la vetrina NON deve dire
    #     «gratuita» (il primo pezzo lo offro io, gli altri no) -------
    prova("base 0 + supp 1.000 x3 → 2.000, e NON e' spedizione gratuita",
          2_000, sats([(a(base=0, extra=1_000), 3)]))

    # --- IL CAMBIO ASSENTE: fail-closed, come _sped_in_sats ----------
    prova("base ancorata senza cambio → None", None,
          sats([(a(base_eur=5.0), 1)]))
    prova("SUPPLEMENTO ancorato senza cambio → None (il caso nuovo)",
          None, sats([(a(base=500, extra_eur=3.0), 4)]))
    prova("...e anche a UN pezzo solo, che il supplemento non paga",
          None, sats([(a(base=500, extra_eur=3.0), 1)]))
    prova("col cambio, l'ancora diventa sats", 500 + 3_000 * 3,
          sats([(a(base=500, extra_eur=3.0), 4)], cambio=CAMBIO))

    # --- L'EURO NATIVO: «contribuisce in sats», non «eur == 0» -------
    tutto_eur = pacco([(a(base_eur=6.0, extra_eur=3.0), 10)], "casa", CAMBIO)
    prova("tutte in euro: l'euro nativo e' esatto", 33.0, tutto_eur["eur"])
    prova("...e i sats combaciano", 33_000, tutto_eur["sats"])
    misto = pacco([(a(base_eur=6.0, extra_eur=3.0), 1),
                   (a(base=2_000, extra=1_000), 1)], "casa", CAMBIO)
    prova("una nata in sats: l'euro nativo si azzera (compare il ≈)",
          0.0, misto["eur"])
    zero = pacco([(a(base_eur=6.0, extra=0), 3)], "casa", CAMBIO)
    prova("una tariffa a ZERO non azzera l'euro nativo", 6.0, zero["eur"])

    # --- LA STIMA (il ≈) e i due campi per il client -----------------
    prova("stima: vera se una contribuente e' nata in euro", True,
          pacco([(a(base=500, extra_eur=3.0), 2)], "casa", CAMBIO)["stima"])
    prova("stima: falsa se sono tutte in sats", False,
          pacco([(a(base=500, extra=300), 2)], "casa", CAMBIO)["stima"])
    p = pacco([(a(base=6_000, extra=3_000), 10)], "casa", 0.0)
    prova("supplemento: la sola parte per-pezzo", 27_000, p["supplemento"])
    prova("...e sats == max(base) + supplemento", 33_000,
          6_000 + p["supplemento"])
    prova("pezzi: la somma delle quantita'", 12,
          pacco([(a(base=500), 10), (a(base=300), 2)], "casa", 0.0)["pezzi"])

    # --- L'ARROTONDAMENTO: si converte PRIMA, si moltiplica DOPO -----
    # 0,01 € al cambio tondo fa 10 sats: dieci pezzi fanno 10x10=100.
    # Con round(10 x 0,01/cambio) sarebbe lo stesso numero solo per
    # caso; il caso che le separa e' un cambio non tondo.
    storto = 97_531.0
    uno = round(0.01 / storto * 100_000_000)
    q = 10
    prova("converte prima e moltiplica dopo (mai il contrario)",
          uno * q, sats([(a(base=0, extra_eur=0.01), q + 1)], cambio=storto))

    # --- LA VIA e i casi degeneri ------------------------------------
    prova("il ritiro non spedisce: zero e nessuna eccezione", 0,
          sats([(a(base=6_000, extra=3_000), 10)], via="ritiro"))
    prova("lista vuota: zero, mai un ValueError da max()", 0,
          sats([]))
    prova("la via punto segue la sua tariffa, il supplemento e' UNO",
          400 + 3_000 * 2,
          sats([(a(base=9_000, extra=3_000, punto=400), 3)], via="punto"))
    prova("punto NON dichiarato: ripiega sulla base casa", 900 + 300 * 2,
          sats([(a(base=900, extra=300), 3)], via="punto"))

    # ================================================================
    # LA FORMA: le sentinelle del cantiere
    # ================================================================
    src = _SORGENTE
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("la spedizione dell'ordine ha UN giudice solo", 1,
          src.count("def _sped_pacco("))
    # ...e le TRE copie del MAX scritte a mano sono sparite: e' la
    # prova che il cantiere ha unificato invece di aggiungere un
    # quarto posto da tenere in pari.
    prova("il MAX a mano di _compra_set non c'e' piu'", False,
          "max(sped, costo)" in src)
    prova("...e nemmeno quello di _strade_preventivo", False,
          "if costo > sped:" in src)
    prova("i chiamanti della pura sono tre (mono, set, preventivo)", 3,
          src.count("_sped_pacco(") - 1)
    # LA PURA RESTA PURA: se un domani ci entrasse una query o un
    # await, compra e preventivo potrebbero cominciare a divergere
    # senza che nessuna prova funzionale se ne accorga.
    corpo = pezzo("_sped_pacco").split('"""')[-1]
    for vietato in ("INSERT", "SELECT", "await", "con.", "HTTPException",
                    "cambio_btc_eur", "PROTEZIONE_", "SPED_GRATIS"):
        prova(f"_sped_pacco: niente {vietato} (e' una pura)", False,
              vietato in corpo)
    # IL SUPPLEMENTO NON ARRIVA MAI DAL COMPRATORE: una tariffa che
    # chi paga puo' scrivere non e' piu' una tariffa.
    corpo_mono2 = src[src.index("async def compra("):
                      src.index("def crea_ordine_pagato(")]
    corpo_set2 = src[src.index("async def _compra_set("):
                     src.index("async def _preventivo_set(")]
    for chi, c2 in (("compra", corpo_mono2), ("_compra_set", corpo_set2)):
        prova(f"{chi}: il supplemento non si legge dal payload", False,
              'd.get("spedizione_extra' in c2)
    # LA QUANTITA' ARRIVA AL PREVENTIVO, ed e' la riga che tiene
    # insieme preventivo e invoice sul mono: con [a] al posto di
    # [(a, richiesti)] la pagina direbbe la spedizione di UN pezzo.
    corpo_prev = src[src.index("async def preventivo_ordine("):
                     src.index("async def _preventivo_set(")]
    prova("preventivo mono: la quantita' arriva alla pura", True,
          "_strade_preventivo([(a, richiesti)]" in corpo_prev)
    corpo_pset = src[src.index("async def _preventivo_set("):][:20_000]
    prova("preventivo set: le quantita' si prendono da `richieste`",
          True, "[(tutti[aid], q) for aid, q" in corpo_pset)
    prova("...e MAI zippando due dizionari diversi", False,
          "zip(tutti.values()" in src)
    # LA PROMESSA OFFRE TUTTO: se azzerasse la sola base, la pagina
    # direbbe «gratuita» e sotto «spedizione per 10 pezzi».
    for chi, c2 in (("compra", corpo_mono2), ("_compra_set", corpo_set2)):
        prova(f"{chi}: la spedizione gratis azzera anche il supplemento",
              True, "supplemento = sped, 0, 0" in c2)
    # E' un costrutto del CHECKOUT: non esce sui relay, come la
    # tariffa punto (NIP-99 non ha un vocabolario per il per-pezzo).
    for nome in ("tag_commercio", "evento_annuncio"):
        prova(f"{nome}: cieco al supplemento", False,
              "spedizione_extra" in pezzo(nome))
    prova("la modifica firmata non tocca il supplemento", False,
          "spedizione_extra" in src[src.index("async def modifica_firmata("):
                                    src.index("async def modifica_firmata(") + 9000])
    # LA COLONNA SI CONSERVA se il client vecchio non la nomina, il
    # patto della tariffa punto.
    corpo_mod = src[src.index("async def modifica_annuncio("):
                    src.index("async def modifica_firmata_prepara(")]
    prova("modifica: il supplemento assente si CONSERVA", True,
          '"spedizione_extra_sats",' in corpo_mod
          and 'a["spedizione_extra_sats"]' in corpo_mod)
    # NESSUNA COLONNA su ordini: l'aritmetica quadra gia', e una
    # colonna nella tabella del denaro per un dato ornamentale e'
    # quello che questo progetto tiene fuori.
    prova("nessuna colonna `supplemento` su ordini", False,
          "supplemento_sats INTEGER" in src)
    # IL CLIENT: il giudice della gratuita' guarda il supplemento, o
    # scriverebbe «gratis» dove solo il primo pezzo lo e'.
    g = mini[mini.index("const spedGratis ="):]
    g = g[:g.index(";")]
    prova("il client non promette una gratuita' a meta'", True,
          "spedExtra" in g)
    # ...e la riga breve arriva fino al paySheet: se comparisse nella
    # pagina d'acquisto e sparisse un istante dopo, si leggerebbe come
    # «il prezzo e' cambiato» un attimo prima di pagare.
    prova("il server dice supplemento e pezzi nelle risposte d'ordine",
          2, src.count('"supplemento_sats": supplemento'))
    prova("...e in ogni strada del preventivo", 1,
          src.count('"supplemento_sats": p["supplemento"]'))
    prova("il paySheet sa scrivere «per N pezzi»", True,
          "Spedizione per ${fmt(nSped)} pezzi" in mini)
    prova("...e la pagina d'acquisto pure", True,
          'class="ctrl-nota">per ${fmt(c.pezzi)} pezzi' in mini)


# ====================================================================
def prove_sconto_pacco():
    """LO SCONTO CARRELLO (ago 2026): il venditore premia chi compra
    piu' cose — UNA regola per negozio, soglia + percentuale, sul SOLO
    articolo e mai sulla spedizione. La matematica si tortura qui da
    sola, senza database e senza nodo: e' il posto dove un errore costa
    sats veri.
    Dal cantiere del CRITERIO (ago 2026) `sc` e `sceur` restano gli
    shim a criterio PEZZI: le prove di ieri girano identiche riga per
    riga, ed e' la regressione dei negozi esistenti a costo zero — se
    il criterio nuovo avesse spostato di un sat il mondo di prima,
    queste diventerebbero rosse tutte insieme."""
    print("\n[lo sconto carrello]")
    amb = {}
    for f in ("_importo_accordo", "_prezzo_lampo", "_unitario_effettivo",
              "_eur_interi", "_sconto_pacco", "_sconto_pacco_eur",
              "_conto_ordine"):
        exec(pezzo(f), amb)
    conto, unit = amb["_conto_ordine"], amb["_unitario_effettivo"]
    # Un cambio tondo per tutte le prove: 1 BTC = 100.000 €, cioe'
    # MILLE SATS = UN EURO. Cosi' ogni cifra si legge in tutt'e due le
    # unita' a mente, e gli asserti dicono quello che sembrano dire.
    CAMBIO = 100_000.0

    def eur(sats):
        return amb["_eur_interi"](sats, CAMBIO)

    def sc(art, pezzi, soglia, pct, art_eur=None):
        """il criterio a PEZZI. `art_eur` sta a None di proposito: cosi'
        ogni prova qui sotto dimostra anche che i pezzi non guardano
        mai l'euro — cioe' che a cambio muto continuano a scattare.
        La valuta e' 'eur' e non conta: a criterio pezzi non si guarda."""
        return amb["_sconto_pacco"](art, art_eur, pezzi, "pezzi",
                                    soglia, pct, "eur")

    def scv(art, soglia_eur, pct, pezzi=2, art_eur=...):
        """il gemello a VALORE in EURO: i pezzi restano 2 (un carrello
        vero) e non contano mai — la misura e' l'articolo, in EURO.
        `art_eur` si deriva dal cambio, come fa il conto vero; passarlo
        a mano serve al caso del cambio muto."""
        return amb["_sconto_pacco"](
            art, eur(art) if art_eur is ... else art_eur,
            pezzi, "valore", soglia_eur, pct, "eur")

    def scs(art, soglia_sats, pct, pezzi=2, art_eur=None):
        """il gemello a VALORE in SATS (ago 2026, la scelta della
        valuta): la misura e' l'articolo COM'E', senza conversione.
        `art_eur` sta a None apposta — cosi' ogni prova qui sotto
        dimostra anche che la soglia in sats non guarda l'euro, cioe'
        che scatta anche a cambio muto."""
        return amb["_sconto_pacco"](art, art_eur, pezzi, "valore",
                                    soglia_sats, pct, "sats")

    def sceur(art_eur, pezzi, soglia, pct):
        """il gemello in euro NON decide piu' da solo: la porta la apre
        il fratello in sats, e qui si riproduce il gate del chiamante
        (`... if sconto else 0.0`) — cosi' la prova misura la stessa
        cosa che gira in produzione"""
        return (amb["_sconto_pacco_eur"](art_eur, pct)
                if sc(100_000, pezzi, soglia, pct) else 0.0)

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

    # ================================================================
    # IL CRITERIO A VALORE (ago 2026): stessa regola, altra misura.
    # ================================================================
    # La soglia e' in EURO dall'ago 2026: 100.000 sats fanno 100 € al
    # cambio delle prove, quindi le cifre di ieri si rileggono a mente.
    prova("valore, soglia esatta: a 100 € su 100 € SCATTA", 10_000,
          scv(100_000, 100, 10))
    prova("valore, un euro sotto: non scatta niente", 0,
          scv(99_000, 100, 10))
    prova("...e il floor lo decide: 99.999 sats sono 99 €, non 100", 0,
          scv(99_999, 100, 10))
    prova("valore, ben sopra: sconta il 10% di quello che c'e'", 25_000,
          scv(250_000, 100, 10))
    prova("valore: e' una percentuale, non un premio a soglia", True,
          scv(200_000, 100, 10) == 2 * scv(100_000, 100, 10))
    prova("valore, soglia 0 (colonna sporca): spenta", 0,
          scv(500_000, 0, 10))
    prova("valore, soglia negativa: spenta", 0, scv(500_000, -5, 10))
    prova("valore, percento 0: spenta", 0, scv(500_000, 100, 0))

    # IL CAMBIO MUTO (ago 2026): una promessa in EURO non si valuta
    # senza cambio, e allora NON scatta — fail-closed dentro il giudice
    # e non con un «if» nei quattro percorsi del conto. Il carrello di
    # queste due righe sopra soglia ci arriverebbe comodamente.
    prova("cambio muto: a valore la promessa non scatta", 0,
          scv(500_000, 100, 10, art_eur=None))
    prova("...e non e' la soglia a essere sbagliata (col cambio scatta)",
          50_000, scv(500_000, 100, 10))
    prova("cambio muto: a PEZZI si sconta lo stesso", 50_000,
          sc(500_000, 3, 3, 10))
    prova("...perche' i pezzi non guardano mai l'euro", True,
          sc(500_000, 3, 3, 10) == sc(500_000, 3, 3, 10, art_eur=500))
    prova("_eur_interi: None quando il cambio manca", None,
          amb["_eur_interi"](500_000, 0))
    prova("_eur_interi: per difetto, mai per eccesso", 99,
          amb["_eur_interi"](99_999, CAMBIO))
    prova("_eur_interi: al filo esatto e' il numero tondo", 100,
          amb["_eur_interi"](100_000, CAMBIO))

    # I DUE CRITERI NON SI CONTAMINANO, ed e' il cuore del cantiere ---
    prova("a valore i PEZZI non contano: due o nove, stesso sconto",
          True, scv(200_000, 100, 10, 2) == scv(200_000, 100, 10, 9))
    prova("...nemmeno UN pezzo solo cambia la porta a valore", 20_000,
          scv(200_000, 100, 10, 1))
    prova("a pezzi il VALORE non conta: un carrello da 10 sats sconta",
          1, sc(10, 3, 3, 10))
    prova("...e uno da dieci milioni pure, con gli stessi 3 pezzi",
          1_000_000, sc(10_000_000, 3, 3, 10))
    # IL CASO MISTO, nei due versi: e' la ragione per cui il criterio
    # esiste — lo stesso carrello risponde in modo opposto secondo la
    # regola del negozio (il computer contro le cianfrusaglie)
    caro = (300_000, 2)        # due pezzi cari
    tanti = (30_000, 9)        # nove pezzi da poco
    prova("il computer: 2 pezzi cari scontano a VALORE", 30_000,
          scv(caro[0], 100, 10, caro[1]))
    prova("...e NON scontano a pezzi con soglia 3", 0,
          sc(caro[0], caro[1], 3, 10))
    prova("le cianfrusaglie: 9 pezzi da poco scontano a PEZZI", 3_000,
          sc(tanti[0], tanti[1], 3, 10))
    prova("...e NON scontano a valore con soglia 100 €", 0,
          scv(tanti[0], 100, 10, tanti[1]))

    # UN CRITERIO CHE NON CONOSCIAMO NON RIPIEGA SUI PEZZI ------------
    # (applicherebbe una soglia in pezzi che nessuno ha promesso in
    # pezzi: una colonna scritta a mano, o il rollback da un criterio
    # futuro, farebbero scontare a caso)
    for storto in ("", "peso", "PEZZI", "Valore", None, 0):
        prova(f"criterio {storto!r}: nessuno sconto, mai",
              0, amb["_sconto_pacco"](500_000, 500, 9, storto, 3, 10, "eur"))

    # ...E NEMMENO UNA VALUTA CHE NON CONOSCIAMO (ago 2026): stessa
    # ragione, un piano piu' sotto — misurerebbe il carrello in
    # un'unita' che il venditore non ha scelto. Il ripiego naturale
    # («sara' euro») e' proprio quello che non si deve fare.
    for storto in ("", "usd", "EUR", "Sats", None, 0):
        prova(f"valuta {storto!r} a criterio valore: nessuno sconto",
              0, amb["_sconto_pacco"](500_000, 500, 2, "valore", 100, 10,
                                      storto))

    # --- LA SOGLIA IN SATS: la stessa porta, un'altra unita' ---------
    # e soprattutto SENZA CONVERSIONE, cioe' senza bisogno del cambio
    prova("in sats, sopra soglia: scatta", 10_000, scs(100_000, 50_000, 10))
    prova("in sats, al filo esatto: scatta", 5_000, scs(50_000, 50_000, 10))
    prova("in sats, un sat sotto: non scatta", 0, scs(49_999, 50_000, 10))
    # LA PROVA CHE VALE PIU' DELLE ALTRE, ed e' il guadagno del
    # cantiere: `art_eur` e' None (cambio muto) e la promessa scatta
    # lo stesso — mentre la gemella in euro, sotto, tace.
    prova("in sats scatta ANCHE a cambio muto (art_eur None)",
          10_000, scs(100_000, 50_000, 10, art_eur=None))
    prova("...mentre in euro, a cambio muto, non scatta",
          0, scv(100_000, 100, 10, art_eur=None))
    # e le due unita' NON si confondono: 100 (euro) e 100 (sats) sullo
    # stesso carrello danno esiti opposti, che e' tutto il punto
    prova("100 come soglia in EURO su 100.000 sats: scatta",
          10_000, scv(100_000, 100, 10))
    prova("...e 100 come soglia in SATS scatta anche su 200 sats",
          20, scs(200, 100, 10))

    # LA MISURA E' IL LORDO DOPO LAMPO E ACCORDO (decisione di Andrea,
    # e la prova esiste perche' sembra un bug quando un venditore la
    # nota): il carrello che a listino superava la soglia puo' finirci
    # sotto per una lampo generosa. E' giusto cosi' — la soglia guarda
    # quel che si paga davvero per la merce.
    pieno = a(prezzo_sats=60_000)
    scontato = a(prezzo_sats=60_000, lampo_percento=50,
                 lampo_scadenza=2000)
    lordo_pieno = unit(pieno, None, 1000, 0.0) * 2
    lordo_lampo = unit(scontato, None, 1000, 0.0) * 2
    prova("a listino il carrello vale 120.000", 120_000, lordo_pieno)
    prova("...con la lampo al 50% ne vale 60.000", 60_000, lordo_lampo)
    prova("sopra soglia a listino: lo sconto carrello scatta", 12_000,
          scv(lordo_pieno, 100, 10))
    prova("SOTTO soglia per colpa della lampo: NON scatta, ed e' voluto",
          0, scv(lordo_lampo, 100, 10))
    prova("...ma a criterio PEZZI la lampo non sposta niente", 6_000,
          sc(lordo_lampo, 2, 2, 10))

    # L'INVARIANTE CONTABILE vale identica a valore ------------------
    lv = 150_000
    sv = scv(lv, 100, 10)
    cv = conto(lv, 700, 5, 0, sv)
    prova("valore: lo sconto del carrello", 15_000, sv)
    prova("valore: il netto e' il lordo meno lo sconto", 135_000,
          cv["netto"])
    prova("valore: invariante lordo - sconto + sped + prot = totale",
          cv["totale"],
          lv - cv["sconto"] + cv["spedizione"] + cv["protezione"])

    # L'EURO segue il fratello in sats anche a valore ----------------
    def sceur_v(art_eur_nativo, art, soglia_eur, pct):
        """ATTENZIONE ai due «euro» diversi, che qui stanno nella stessa
        riga: `art_eur_nativo` e' la cifra in cui il prezzo e' NATO (il
        giudice del ≈), la misura della soglia e' invece la conversione
        dell'articolo. Scambiarli sconterebbe in euro un conto in sats."""
        return (amb["_sconto_pacco_eur"](art_eur_nativo, pct)
                if scv(art, soglia_eur, pct) else 0.0)
    prova("valore: euro sopra soglia, l'euro nativo si sconta", 12.0,
          sceur_v(120.0, 120_000, 100, 10))
    prova("valore: sats SOTTO soglia, l'euro tace (la porta e' una)",
          0.0, sceur_v(120.0, 99_999, 100, 10))
    prova("i due gemelli scattano insieme anche a valore", True,
          all(bool(scv(x, 100, 10))
              == bool(sceur_v(x / 1000.0, x, 100, 10))
              for x in (50_000, 99_999, 100_000, 250_000)))
    prova("la leva del minimo a valore ha un default nel sorgente",
          True, "SCONTO_PACCO_MIN_VALORE_EUR = 1" in _SORGENTE)

    # --- IL MONO SCONTA (ago 2026): la divisione a ritroso RIAGGIUNGE
    # lo sconto e resta esatta. Il caso a sconto zero e' la regressione
    # (il mondo di ieri, byte per byte); quello con lo sconto e' il
    # gemello nuovo — prezzo_sats nasce gia' scontato, e l'unitario
    # deve tornare al LORDO del listino.
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
         "spedizione_sats": 500, "protezione_sats": 0, "sconto_sats": 0}
    prova("mono: la divisione a ritroso resta esatta (30.000 a pezzo)",
          30_000, amb2["_righe_ordine"](_Con(), o)[0]["unitario_sats"])
    o2 = {"annuncio_id": 7, "quantita": 3, "prezzo_sats": 81_500,
          "spedizione_sats": 500, "protezione_sats": 0,
          "sconto_sats": 9_000}
    prova("mono scontato: l'unitario torna al LORDO (30.000 a pezzo)",
          30_000, amb2["_righe_ordine"](_Con(), o2)[0]["unitario_sats"])
    # e su un ordine di ieri sconto_sats puo' essere NULL: l'or 0
    o3 = dict(o, sconto_sats=None)
    prova("mono con sconto NULL: come a zero",
          30_000, amb2["_righe_ordine"](_Con(), o3)[0]["unitario_sats"])

    # ================================================================
    # IL LETTORE DELLA REGOLA e la sua faccia PUBBLICA. La docstring di
    # _regola_sconto prometteva «la prova in CI» dal giorno in cui e'
    # nata e non l'aveva mai avuta: col criterio quel buco costerebbe
    # caro, perche' e' qui che si decide quale delle due soglie
    # comanda — e quale delle due esce in vetrina.
    # ================================================================
    amb3 = {"SCONTO_PACCO_ATTIVO": True,
            "SCONTO_PACCO_CRITERI": ("pezzi", "valore", "entrambi"),
            "VALUTE_SOGLIA": ("eur", "sats"),
            "SCONTO_PACCO_MIN_SOGLIA": 2,
            "SCONTO_PACCO_MIN_VALORE_EUR": 1,
            "SCONTO_PACCO_MIN_VALORE_SATS": 1,
            "SCONTO_PACCO_MAX_PERCENTO": 30}
    exec(pezzo("_valuta_soglia"), amb3)
    exec(pezzo("_regola_sconto"), amb3)
    exec(pezzo("_regole_sconto"), amb3)
    exec(pezzo("_sconto_pubblico"), amb3)
    reg, pub = amb3["_regola_sconto"], amb3["_sconto_pubblico"]
    regs = amb3["_regole_sconto"]
    # firma: (criterio, valuta, soglia_pezzi, valore_sats, valore_eur, pct)

    prova("regola a pezzi: esce la soglia in pezzi", ("pezzi", 3, 10, ""),
          reg("pezzi", "eur", 3, 9_999, 50_000, 10))
    prova("regola a valore in EURO: esce la soglia in euro",
          ("valore", 50, 10, "eur"), reg("valore", "eur", 3, 9_999, 50, 10))
    prova("regola a valore in SATS: esce la soglia in sats",
          ("valore", 9_999, 10, "sats"),
          reg("valore", "sats", 3, 9_999, 50, 10))
    prova("criterio vuoto = pezzi: e' il mondo di ieri", ("pezzi", 3, 10, ""),
          reg("", "eur", 3, 0, 0, 10))
    prova("criterio None = pezzi (colonna mai scritta)", ("pezzi", 3, 10, ""),
          reg(None, "eur", 3, 0, 0, 10))
    # LA RETROCOMPATIBILITA' DEL DEFAULT: valuta vuota = euro, cioe'
    # letteralmente il mondo di prima della scelta. E' lei che rende la
    # migrazione un DEFAULT invece di uno script.
    prova("valuta vuota = euro (il mondo di prima della scelta)",
          ("valore", 50, 10, "eur"), reg("valore", "", 3, 9_999, 50, 10))
    prova("valuta None = euro (colonna mai scritta)",
          ("valore", 50, 10, "eur"), reg("valore", None, 3, 9_999, 50, 10))
    prova("criterio fuori catalogo: niente sconto", ("", 0, 0, ""),
          reg("peso", "eur", 3, 0, 50, 10))
    prova("valuta fuori catalogo: niente sconto", ("", 0, 0, ""),
          reg("valore", "usd", 3, 9_999, 50, 10))
    prova("soglia sotto il minimo: niente sconto", ("", 0, 0, ""),
          reg("pezzi", "eur", 1, 0, 0, 10))
    prova("valore sotto il minimo (mezzo euro non e' una soglia)",
          ("", 0, 0, ""), reg("valore", "eur", 3, 9_999, 0, 10))
    prova("...e lo stesso in sats: la cifra dell'altra unita' non salva",
          ("", 0, 0, ""), reg("valore", "sats", 3, 0, 50, 10))
    prova("percento a zero: niente sconto", ("", 0, 0, ""),
          reg("pezzi", "eur", 3, 0, 0, 0))
    prova("il percento si tappa al massimo della leva",
          ("pezzi", 3, 30, ""), reg("pezzi", "eur", 3, 0, 0, 99))
    prova("la soglia dell'altro criterio non lo disturba mai",
          ("valore", 50, 10, "eur"), reg("valore", "eur", 0, 0, 50, 10))
    amb3["SCONTO_PACCO_ATTIVO"] = False
    prova("leva generale spenta: niente sconto in nessun criterio",
          [("", 0, 0, ""), ("", 0, 0, "")],
          [reg("pezzi", "eur", 3, 0, 0, 10),
           reg("valore", "eur", 0, 0, 50, 10)])
    amb3["SCONTO_PACCO_ATTIVO"] = True
    amb3["SCONTO_PACCO_CRITERI"] = ("pezzi",)
    prova("criterio tolto dalla leva: chi l'aveva scelto non sconta piu'",
          ("", 0, 0, ""), reg("valore", "eur", 0, 0, 50, 10))
    # si rimette INTERA, 'entrambi' compreso: le prove sotto girano su
    # questo stesso ambiente, e una leva lasciata a meta' le farebbe
    # fallire per un motivo che non e' il loro
    amb3["SCONTO_PACCO_CRITERI"] = ("pezzi", "valore", "entrambi")
    # ...e lo stesso per la VALUTA: e' una leva col patto dei criteri,
    # cioe' un freno d'emergenza che spegne chi l'aveva scelta
    amb3["VALUTE_SOGLIA"] = ("eur",)
    prova("valuta tolta dalla leva: chi l'aveva scelta non sconta piu'",
          ("", 0, 0, ""), reg("valore", "sats", 0, 9_999, 0, 10))
    prova("...ma l'altra valuta continua a scattare",
          ("valore", 50, 10, "eur"), reg("valore", "eur", 0, 0, 50, 10))
    amb3["VALUTE_SOGLIA"] = ("eur", "sats")

    # LA REGOLA D'ORO, torturata: ogni chiave porta il numero SOLO
    # nella sua unita', e le altre restano a zero. E' il lucchetto dei
    # client vecchi, che di campi ne leggono uno solo — senza, uno
    # direbbe «−10% da 100000 pezzi» e un altro «da 25 sats» dove ci
    # sono 25 euro: non promesse piu' avare, promesse assurde.
    prova("pubblico a pezzi: le due cifre a valore tacciono",
          {"criterio": "pezzi", "soglia": 3, "valore": 0, "valore_eur": 0,
           "valuta": "", "percento": 10},
          pub("pezzi", "eur", 3, 9_999, 50, 10))
    prova("pubblico a valore in EURO: pezzi e sats tacciono",
          {"criterio": "valore", "soglia": 0, "valore": 0, "valore_eur": 50,
           "valuta": "eur", "percento": 10},
          pub("valore", "eur", 3, 9_999, 50, 10))
    prova("pubblico a valore in SATS: pezzi ed euro tacciono",
          {"criterio": "valore", "soglia": 0, "valore": 9_999,
           "valore_eur": 0, "valuta": "sats", "percento": 10},
          pub("valore", "sats", 3, 9_999, 50, 10))
    prova("pubblico a regola spenta: tacciono tutti",
          {"criterio": "", "soglia": 0, "valore": 0, "valore_eur": 0,
           "valuta": "", "percento": 0}, pub("peso", "eur", 3, 9_999, 50, 10))
    prova("MAI degli euro nel campo dei PEZZI", True,
          all(pub("valore", "eur", p, 0, v, 10)["soglia"] == 0
              for p in (0, 3, 99) for v in (1, 50, 9_999)))
    # IL DENTE CHE HA CAMBIATO LATO (ago 2026): fino a ieri `valore`
    # usciva a zero SEMPRE, e quella prova certificava il mondo in cui
    # i sats non erano piu' una soglia possibile. Adesso la regola e'
    # piu' forte e vale in tutte e due le direzioni: il numero esce SE
    # E SOLO SE quella e' l'unita' dichiarata. Un client di prima del
    # passaggio all'euro, che `valore` lo legge in sats, su un negozio
    # in sats la trova finalmente GIUSTA — e altrove non trova niente.
    prova("`valore` porta un numero SE E SOLO SE la valuta e' sats",
          True, all((pub(c, va, p, 500, 50, 10)["valore"] > 0)
                    == (c in ("valore", "entrambi") and va == "sats")
                    for c in ("pezzi", "valore", "entrambi", "peso")
                    for va in ("eur", "sats", "usd", "")
                    for p in (0, 3)))
    prova("...e `valore_eur` SE E SOLO SE la valuta e' euro",
          True, all((pub(c, va, p, 500, 50, 10)["valore_eur"] > 0)
                    == (c in ("valore", "entrambi") and va in ("eur", ""))
                    for c in ("pezzi", "valore", "entrambi", "peso")
                    for va in ("eur", "sats", "usd", "")
                    for p in (0, 3)))
    # LA PROVA CHE HA CAMBIATO LATO (ago 2026, i due criteri insieme):
    # diceva «le tre cifre si escludono SEMPRE a vicenda», e col criterio
    # 'entrambi' non e' piu' vero — le piene diventano DUE. Quel che
    # regge, ed e' la proprieta' su cui il client poggia davvero, e' che
    # non siano mai due NELLA STESSA UNITA': «quella piena» resta una
    # domanda con una risposta sola per ogni unita' di misura.
    prova("le due cifre A VALORE non parlano mai insieme", True,
          all(not (pub(c, va, p, s, e, 10)["valore"] > 0
                   and pub(c, va, p, s, e, 10)["valore_eur"] > 0)
              for c in ("pezzi", "valore", "entrambi", "peso")
              for va in ("eur", "sats", "usd", "")
              for p in (0, 3) for s in (0, 500) for e in (0, 50)))
    prova("a criterio SINGOLO si escludono ancora tutte e tre", True,
          all(sum(1 for k in ("soglia", "valore", "valore_eur")
                  if pub(c, va, p, s, e, 10)[k] > 0) <= 1
              for c in ("pezzi", "valore", "peso")
              for va in ("eur", "sats", "usd", "")
              for p in (0, 3) for s in (0, 500) for e in (0, 50)))
    prova("a 'entrambi' le piene sono DUE: i pezzi e una a valore",
          {"criterio": "entrambi", "soglia": 3, "valore": 0,
           "valore_eur": 50, "valuta": "eur", "percento": 10},
          pub("entrambi", "eur", 3, 9_999, 50, 10))
    prova("...e in sats la seconda e' quella in sats",
          {"criterio": "entrambi", "soglia": 3, "valore": 9_999,
           "valore_eur": 0, "valuta": "sats", "percento": 10},
          pub("entrambi", "sats", 3, 9_999, 50, 10))
    # IL CLIENT VECCHIO IN CACHE ne esce con un'OMISSIONE e non con una
    # bugia: legge `soglia`, disegna «−10% da 3 articoli», e quella meta'
    # di promessa e' vera. E' la sola ragione per cui si poteva fare.
    prova("il client di ieri legge i PEZZI e non sbaglia unita'", 3,
          pub("entrambi", "eur", 3, 9_999, 50, 10)["soglia"])
    # una gamba morta non fa dichiarare 'entrambi' in pubblico: si
    # promette quel che il negozio puo' mantenere
    prova("a 'entrambi' con la gamba a valore morta esce 'pezzi'",
          ("pezzi", 3, 0), tuple(pub("entrambi", "eur", 3, 0, 0, 10)[k]
                                 for k in ("criterio", "soglia",
                                           "valore_eur")))
    prova("...e con la gamba a pezzi morta esce 'valore'",
          ("valore", 0, 50), tuple(pub("entrambi", "eur", 1, 0, 50, 10)[k]
                                   for k in ("criterio", "soglia",
                                             "valore_eur")))

    # ================================================================
    # IL LETTORE PLURALE (_regole_sconto): zero, una o DUE gambe.
    # ================================================================
    prova("a criterio singolo la lista ha UNA gamba sola",
          [("pezzi", 3, 10, "")], regs("pezzi", "eur", 3, 9_999, 50, 10))
    prova("a 'entrambi' le gambe sono DUE, pezzi per primo",
          [("pezzi", 3, 10, ""), ("valore", 50, 10, "eur")],
          regs("entrambi", "eur", 3, 9_999, 50, 10))
    prova("...e in sats la seconda porta la soglia in sats",
          [("pezzi", 3, 10, ""), ("valore", 9_999, 10, "sats")],
          regs("entrambi", "sats", 3, 9_999, 50, 10))
    prova("una gamba sotto il minimo cade, l'altra resta",
          [("valore", 50, 10, "eur")],
          regs("entrambi", "eur", 1, 9_999, 50, 10))
    prova("regola spenta: lista vuota", [],
          regs("entrambi", "eur", 3, 9_999, 50, 0))
    prova("criterio ignoto: lista vuota", [],
          regs("peso", "eur", 3, 9_999, 50, 10))
    # IL KILL-SWITCH di 'entrambi', e quello PER GAMBA: togliere il
    # terzo valore dalla leva spegne tutto per chi l'aveva scelto —
    # fail-closed, mai meta' promessa; togliere una GAMBA spegne quella
    # e lascia l'altra, che e' il comportamento giusto.
    amb3["SCONTO_PACCO_CRITERI"] = ("pezzi", "valore")
    prova("'entrambi' fuori dalla leva: non sconta piu' niente", [],
          regs("entrambi", "eur", 3, 9_999, 50, 10))
    amb3["SCONTO_PACCO_CRITERI"] = ("valore", "entrambi")
    prova("la gamba 'pezzi' tolta dalla leva cade da sola",
          [("valore", 50, 10, "eur")],
          regs("entrambi", "eur", 3, 9_999, 50, 10))
    amb3["SCONTO_PACCO_CRITERI"] = ("pezzi", "valore", "entrambi")
    amb3["SCONTO_PACCO_ATTIVO"] = False
    prova("leva generale spenta: niente gambe", [],
          regs("entrambi", "eur", 3, 9_999, 50, 10))
    amb3["SCONTO_PACCO_ATTIVO"] = True
    # 'entrambi' NON E' UNA GAMBA: il lettore singolo lo rifiuta, o
    # cadrebbe nel ramo dei PEZZI e misurerebbe una soglia che il
    # venditore non ha promesso da sola (e' il caso che
    # avvisa_sconto_su_mono gli passa grezzo).
    prova("il lettore SINGOLO rifiuta 'entrambi'", ("", 0, 0, ""),
          reg("entrambi", "eur", 3, 9_999, 50, 10))

    # ================================================================
    # BASTA CHE NE SCATTI UNA (_sconto_regole) e LA PIU' VICINA
    # (_gamba_invito): il calcolo e la scelta, che sono due mestieri.
    # ================================================================
    exec(pezzo("_sconto_regole"), amb)
    exec(pezzo("_gamba_invito"), amb)
    sreg, ginv = amb["_sconto_regole"], amb["_gamba_invito"]
    DUE = [("pezzi", 3, 10, ""), ("valore", 50, 10, "eur")]
    # articolo 30.000 sats = 30 € col cambio tondo delle prove
    prova("nessuna gamba scatta: niente sconto", 0,
          sreg(30_000, 30, 2, DUE))
    prova("scatta la gamba a PEZZI: lo sconto c'e'", 3_000,
          sreg(30_000, 30, 3, DUE))
    prova("scatta la gamba a VALORE con un pezzo solo", 6_000,
          sreg(60_000, 60, 1, DUE))
    # LE DUE GAMBE SONO DUE STRADE PER LO STESSO SCONTO: quando
    # scattano tutte e due la cifra e' la stessa di quando ne scatta
    # una, mai la somma. E' la proprieta' che rende il max un «almeno
    # una» — e la prova che si accorge di una somma travestita.
    prova("scattano tutte e due: la cifra NON raddoppia", (6_000, 6_000),
          (sreg(60_000, 60, 3, DUE), sreg(60_000, 60, 1, DUE)))
    prova("lista vuota: nessuno sconto e nessuna esplosione", 0,
          sreg(60_000, 60, 9, []))
    # LA PIU' VICINA, in PROPORZIONE e non in valore assoluto: «1 pezzo
    # su 3» e «30 € su 50» non si confrontano altrimenti.
    prova("a parita' di gambe vince chi e' piu' avanti (valore)",
          "valore", ginv(DUE, 2, 40_000, 40)[0])
    prova("...e i pezzi quando sono loro i piu' vicini", "pezzi",
          ginv(DUE, 2, 10_000, 10)[0])
    # chi e' SCATTATA vince subito: li' non c'e' piu' un invito da fare
    prova("la gamba scattata vince, e non manca niente",
          ("valore", 0), (lambda g: (g[0], g[4]))(ginv(DUE, 1, 60_000, 60)))
    prova("...anche quando l'altra e' piu' avanti in proporzione",
          "pezzi", ginv(DUE, 3, 10_000, 10)[0])
    # QUANTO MANCA, nell'unita' della gamba scelta
    prova("quanto manca: pezzi", ("pezzi", 1), (lambda g: (g[0], g[4]))(
        ginv([("pezzi", 3, 10, "")], 2, 10_000, 10)))
    prova("quanto manca: euro", ("valore", 20), (lambda g: (g[0], g[4]))(
        ginv([("valore", 50, 10, "eur")], 2, 30_000, 30)))
    # LA GAMBA CHE NON SI SA MISURARE ESCE DAL GIRO, non vale zero: a
    # cambio muto (articolo_eur None) un negozio con tutte e due
    # continua a invitare sui PEZZI, dove prima la promessa spariva.
    prova("a cambio muto resta la gamba a pezzi", "pezzi",
          ginv(DUE, 2, 40_000, None)[0])
    prova("...e con la sola gamba in euro non si dice niente", None,
          ginv([("valore", 50, 10, "eur")], 2, 40_000, None))
    prova("...mentre quella in SATS si misura sempre", "valore",
          ginv([("valore", 9_999, 10, "sats")], 2, 40_000, None)[0])


# ====================================================================
def prove_valuta_soglia():
    """LA VALUTA DELLA SOGLIA LA SCEGLIE IL VENDITORE (ago 2026), e qui
    si tortura la meta' che vive negli ENDPOINT — quella che le pure non
    possono difendere.
    IL CUORE E' IL CLIENT VECCHIO: le chiavi di ieri restano ignorate
    per sempre, ma «ignorata» NON deve voler dire «letta come zero».
    Il difetto e' nato col passaggio all'euro e si presentava in due
    modi — un salvataggio a vuoto sullo sconto, uno SPEGNIMENTO
    SILENZIOSO sulla spedizione gratis, dove `soglia` assente valeva 0,
    che li' e' lo spegnimento. Un venditore che crede di aver salvato e
    non ha salvato e' il difetto che si scopre settimane dopo, quindi
    queste prove asseriscono il NON FATTO: 400, e la colonna RILETTA
    dal database ancora quella di prima."""
    print("\n[la valuta della soglia: gli endpoint]")
    import asyncio
    import sqlite3

    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    vero = sqlite3.connect(":memory:")
    vero.row_factory = sqlite3.Row
    vero.executescript("""
      CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY,
        sconto_pacco_criterio TEXT DEFAULT 'pezzi',
        sconto_pacco_soglia INT DEFAULT 0,
        sconto_pacco_valore INT DEFAULT 0,
        sconto_pacco_valore_eur INT DEFAULT 0,
        sconto_pacco_valore_valuta TEXT DEFAULT 'eur',
        sconto_pacco_percento INT DEFAULT 0,
        sped_gratis_soglia INT DEFAULT 0,
        sped_gratis_soglia_eur INT DEFAULT 0,
        sped_gratis_valuta TEXT DEFAULT 'eur');
      -- il negozio di partenza: sconto a valore in EURO da 25, e la
      -- spedizione gratis in EURO da 50. E' esattamente lo stato in cui
      -- il passaggio all'euro ha lasciato i negozi.
      INSERT INTO utenti(tg_id, sconto_pacco_criterio, sconto_pacco_soglia,
        sconto_pacco_valore, sconto_pacco_valore_eur,
        sconto_pacco_valore_valuta, sconto_pacco_percento,
        sped_gratis_soglia, sped_gratis_soglia_eur, sped_gratis_valuta)
        VALUES(1, 'valore', 3, 90000, 25, 'eur', 10, 80000, 50, 'eur');
    """)
    vero.commit()

    class Con:
        def execute(self, *a):
            return vero.execute(*a)

        def commit(self):
            vero.commit()

        def close(self):
            pass

    class _Req:
        def __init__(self, d):
            self._d = d

    async def _leggi(req):
        return req._d

    def _amb():
        amb = {"db": Con, "HTTPException": _H, "Request": object,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": 1},
               "leggi_json": _leggi, "_fmt_sats": lambda n: str(n),
               "SCONTO_PACCO_ATTIVO": True, "SPED_GRATIS_ATTIVO": True,
               "SCONTO_PACCO_CRITERI": ("pezzi", "valore", "entrambi"),
               "VALUTE_SOGLIA": ("eur", "sats"),
               "SCONTO_PACCO_MIN_SOGLIA": 2,
               "SCONTO_PACCO_MIN_VALORE_EUR": 1,
               "SCONTO_PACCO_MIN_VALORE_SATS": 1,
               "SCONTO_PACCO_MAX_PERCENTO": 30,
               "SPED_GRATIS_MIN_EUR": 1, "SPED_GRATIS_MIN_SATS": 1,
               "MSG_CLIENT_VECCHIO": "RIAPRI"}
        return amb

    def corri(nome, body):
        amb = _amb()
        exec("async " + pezzo(nome), amb)
        try:
            return asyncio.new_event_loop().run_until_complete(
                amb[nome](_Req(body)))
        except _H as e:
            return f"{e.code} {e.detail}"

    def stato():
        r = vero.execute("SELECT * FROM utenti WHERE tg_id=1").fetchone()
        return dict(r)

    prima = stato()

    # ================================================================
    # IL CLIENT VECCHIO: 400 esplicito, e la colonna NON si tocca
    # ================================================================
    # Lo sconto: il body di prima del passaggio all'euro porta `valore`
    # (sats) e nessun `valore_eur`. Prima di questo cantiere prendeva un
    # 400 col messaggio SBAGLIATO («parte da almeno 1 €» a chi ne ha
    # scritti novantamila), che manda a cercare il guasto dalla parte
    # opposta.
    r = corri("imposta_sconto_pacco",
              {"criterio": "valore", "soglia": 3, "valore": 90000,
               "percento": 10})
    prova("sconto, client vecchio: 400 che dice cosa fare", "400 RIAPRI", r)
    prova("...e la promessa e' rimasta ESATTAMENTE com'era", prima, stato())

    # La spedizione gratis: il caso peggiore. `soglia` (sats) senza
    # `soglia_eur` valeva 0, e zero li' e' lo SPEGNIMENTO — il venditore
    # premeva «Aggiorna la soglia» e la promessa si spegneva in silenzio.
    r = corri("imposta_sped_gratis", {"soglia": 80000})
    prova("spedizione, client vecchio: 400 che dice cosa fare",
          "400 RIAPRI", r)
    prova("...e la promessa NON si e' spenta", prima, stato())
    # ...e nemmeno un body vuoto la spegne: e' lo stesso caso, ed e'
    # quello che arriva da un client a cui e' sfuggito il campo
    r = corri("imposta_sped_gratis", {})
    prova("spedizione, body vuoto: 400 e niente si muove",
          ("400 RIAPRI", prima), (r, stato()))
    # LA VARIANTE NUOVA, che la valuta porta con se': la cifra c'e' ma
    # nella chiave dell'ALTRA unita'. Senza la guardia finirebbe in una
    # colonna che la promessa non guarda, e la promessa morirebbe zitta.
    r = corri("imposta_sped_gratis", {"valuta": "sats", "soglia_eur": 50})
    prova("spedizione, cifra nell'unita' sbagliata: 400", "400 RIAPRI", r)
    prova("...e niente si e' mosso", prima, stato())
    r = corri("imposta_sconto_pacco",
              {"criterio": "valore", "valuta": "sats", "valore_eur": 25,
               "percento": 10})
    prova("sconto, cifra nell'unita' sbagliata: 400", "400 RIAPRI", r)
    prova("...e niente si e' mosso", prima, stato())

    # ================================================================
    # LO SPEGNIMENTO ESPLICITO CONTINUA A FUNZIONARE: e' la regressione
    # che la guardia qui sopra poteva rompere.
    # ================================================================
    r = corri("imposta_sconto_pacco", {"percento": 0})
    prova("sconto: `percento: 0` resta lo spegnimento",
          (True, 0, "pezzi", "eur"),
          (isinstance(r, dict), stato()["sconto_pacco_percento"],
           stato()["sconto_pacco_criterio"],
           stato()["sconto_pacco_valore_valuta"]))
    prova("...e azzera TUTTE le soglie, mai una promessa a mezz'aria",
          (0, 0, 0),
          (stato()["sconto_pacco_soglia"], stato()["sconto_pacco_valore"],
           stato()["sconto_pacco_valore_eur"]))
    r = corri("imposta_sped_gratis", {"soglia_eur": 0})
    prova("spedizione: uno zero in una chiave RICONOSCIUTA spegne",
          (True, 0, 0, "eur"),
          (isinstance(r, dict), stato()["sped_gratis_soglia"],
           stato()["sped_gratis_soglia_eur"],
           stato()["sped_gratis_valuta"]))

    # ================================================================
    # 'ENTRAMBI' VUOLE DUE SOGLIE SERIE (ago 2026): chi accende due
    # gambe e ne ha una sola valida promette meta' di quel che crede, e
    # in vetrina non se ne accorge nessuno. I due «if» dell'endpoint
    # devono aprirsi tutti e due al terzo valore, e il messaggio dire
    # QUALE delle due manca.
    # ================================================================
    prima = stato()
    r = corri("imposta_sconto_pacco",
              {"criterio": "entrambi", "valuta": "eur", "soglia": 1,
               "valore_eur": 25, "percento": 10})
    prova("'entrambi' con la gamba PEZZI sotto il minimo: 400",
          True, isinstance(r, str) and r.startswith("400")
          and "pezzi" in r)
    prova("...e niente si e' mosso", prima, stato())
    r = corri("imposta_sconto_pacco",
              {"criterio": "entrambi", "valuta": "eur", "soglia": 3,
               "valore_eur": 0, "percento": 10})
    prova("'entrambi' con la gamba VALORE sotto il minimo: 400",
          True, isinstance(r, str) and r.startswith("400")
          and "valore" in r)
    prova("...e niente si e' mosso", prima, stato())
    # ...e con due soglie serie si salva, e si ritrovano ENTRAMBE
    r = corri("imposta_sconto_pacco",
              {"criterio": "entrambi", "valuta": "eur", "soglia": 3,
               "valore_eur": 25, "percento": 10})
    d = stato()
    prova("'entrambi' con due soglie serie si salva",
          ("entrambi", 3, 25, 10),
          (d["sconto_pacco_criterio"], d["sconto_pacco_soglia"],
           d["sconto_pacco_valore_eur"], d["sconto_pacco_percento"]))
    # e lo spegnimento lo rimette a posto senza chiedere niente
    corri("imposta_sconto_pacco", {"percento": 0})
    prova("...e lo spegnimento vale anche per lui", ("pezzi", 0),
          (stato()["sconto_pacco_criterio"],
           stato()["sconto_pacco_percento"]))

    # ================================================================
    # IL TOGGLE CONSERVA: salvare in una valuta non tocca la cifra
    # dell'altra. E' la promessa che il cassetto fa al venditore —
    # «torni indietro e ritrovi la tua cifra» — e senza il COALESCE
    # sarebbe una bugia.
    # ================================================================
    corri("imposta_sped_gratis", {"valuta": "eur", "soglia_eur": 30,
                                  "soglia_sats": 70000})
    corri("imposta_sped_gratis", {"valuta": "sats", "soglia_sats": 60000,
                                  "soglia_eur": 30})
    d = stato()
    prova("spedizione: la valuta scelta comanda", ("sats", 60000),
          (d["sped_gratis_valuta"], d["sped_gratis_soglia"]))
    prova("...e la cifra in EURO e' rimasta dov'era", 30,
          d["sped_gratis_soglia_eur"])
    # e il client che NON conosce la valuta nuova non la cancella: manda
    # la sola chiave che sa, e l'altra resta (il patto dello stock)
    corri("imposta_sped_gratis", {"soglia_eur": 45})
    d = stato()
    prova("un client che manda una sola unita' non cancella l'altra",
          (45, 60000, "eur"),
          (d["sped_gratis_soglia_eur"], d["sped_gratis_soglia"],
           d["sped_gratis_valuta"]))

    corri("imposta_sconto_pacco",
          {"criterio": "valore", "valuta": "sats", "soglia": 4,
           "valore_sats": 55000, "valore_eur": 20, "percento": 15})
    d = stato()
    prova("sconto: le TRE soglie convivono", (4, 55000, 20, "sats"),
          (d["sconto_pacco_soglia"], d["sconto_pacco_valore"],
           d["sconto_pacco_valore_eur"], d["sconto_pacco_valore_valuta"]))
    # ...e tornando in euro si ritrova la cifra di prima, non una
    # conversione: e' la decisione «conserva, non converte»
    corri("imposta_sconto_pacco",
          {"criterio": "valore", "valuta": "eur", "valore_eur": 20,
           "valore_sats": 55000, "percento": 15})
    d = stato()
    prova("...e il ritorno in euro ritrova la SUA cifra, non un cambio",
          (20, 55000, "eur"),
          (d["sconto_pacco_valore_eur"], d["sconto_pacco_valore"],
           d["sconto_pacco_valore_valuta"]))
    # IL COALESCE si vede SOLO da un body che porta UNA chiave sola:
    # col client di casa, che le manda tutte, un UPDATE secco darebbe
    # lo stesso risultato — ed e' precisamente il motivo per cui questa
    # riga esiste (la mutazione «COALESCE tolto» sopravviveva senza).
    corri("imposta_sconto_pacco",
          {"criterio": "valore", "valuta": "eur", "valore_eur": 18,
           "percento": 15})
    d = stato()
    prova("un body con UNA chiave sola non cancella le altre soglie",
          (18, 55000, 4),
          (d["sconto_pacco_valore_eur"], d["sconto_pacco_valore"],
           d["sconto_pacco_soglia"]))

    # una valuta fuori catalogo si rifiuta alla PORTA, col suo messaggio
    r = corri("imposta_sped_gratis", {"valuta": "usd", "soglia_eur": 50})
    prova("valuta fuori catalogo: 400 alla porta", True,
          str(r).startswith("400 La soglia si può dichiarare"))
    r = corri("imposta_sconto_pacco",
              {"criterio": "valore", "valuta": "usd", "valore_eur": 50,
               "percento": 10})
    prova("...e lo stesso nel gemello", True,
          str(r).startswith("400 La soglia a valore"))

    # ================================================================
    # LA FORMA: le righe che un riordino toglie per prime
    # ================================================================
    src = open("server.py", encoding="utf-8").read()
    # LE CHIAVI VECCHIE restano ignorate PER SEMPRE: rianimarle vorrebbe
    # dire scrivere una cifra senza sapere in che unita' sia — la stessa
    # trappola dei nomi delle leve senza suffisso.
    ep_sc = src[src.index("async def imposta_sconto_pacco("):
                src.index("async def imposta_sped_gratis(")]
    ep_sg = src[src.index("async def imposta_sped_gratis("):
                src.index("async def imposta_ferie(")]
    prova("lo sconto non legge piu' la chiave `valore` nuda", False,
          'd.get("valore")' in ep_sc or 'd["valore"]' in ep_sc)
    prova("la spedizione non legge piu' la chiave `soglia` nuda", False,
          'd.get("soglia")' in ep_sg or 'd["soglia"]' in ep_sg)
    # LA GUARDIA DELLA CHIAVE ASSENTE, in tutti e due: e' la riga che
    # trasforma un salvataggio muto in un errore che dice cosa fare
    for chi, c2 in (("sconto", ep_sc), ("spedizione", ep_sg)):
        prova(f"{chi}: la chiave assente e' un 400, non uno zero", True,
              "MSG_CLIENT_VECCHIO" in c2)
    prova("il messaggio del client vecchio e' scritto UNA volta", 1,
          src.count("MSG_CLIENT_VECCHIO = ("))
    prova("...e lo usano tutti e due gli endpoint", 2,
          src.count("raise HTTPException(400, MSG_CLIENT_VECCHIO)"))
    # ...e dice cosa fare, che un 400 che dice la cosa sbagliata manda a
    # cercare il guasto dalla parte opposta
    prova("...e dice di riaprire l'app", True,
          "riapri Barattolo" in src[src.index("MSG_CLIENT_VECCHIO = ("):
                                    src.index("MSG_CLIENT_VECCHIO = (") + 400])

    # «SOGLIA EURO A ZERO» NON VUOL PIU' DIRE «PROMESSA SPENTA», ed e'
    # la lezione strutturale del cantiere: TRE posti lo codificavano, e
    # tutti e tre sarebbero diventati bugiardi su ogni negozio in sats.
    # Il censimento batte l'elenco (la lezione del titolo nudo): si
    # cerca ogni confronto con zero su quelle colonne e si pretende la
    # valuta accanto, cosi' il quarto posto di fra sei mesi entra nel
    # conto da solo.
    # DUE forme sono ammesse, e sono le due che dicono la verita':
    # nominare la VALUTA (cioe' «e' spenta in quella dichiarata»),
    # oppure chiedere lo zero anche all'ALTRA unita' (cioe' «e' spenta
    # in tutte e due»). Quel che non passa piu' e' il solo euro a zero,
    # che su un negozio in sats e' semplicemente falso.
    # E si guarda LA STESSA FAMIGLIA, non «una valuta qualsiasi qui
    # intorno»: le due promesse vivono spesso nella stessa WHERE, e con
    # un contorno generico la valuta della spedizione copriva il buco
    # dello sconto (provato con la mutazione: sopravviveva).
    import re
    FAMIGLIE = {
        "sped_gratis_soglia_eur": ("sped_gratis_valuta",
                                   "sped_gratis_soglia="),
        "sconto_pacco_valore_eur": ("sconto_pacco_valore_valuta",
                                    "sconto_pacco_valore<",
                                    "sconto_pacco_valore >"),
    }
    sospetti = []
    for m in re.finditer(r"[^\n]*(sped_gratis_soglia_eur|"
                         r"sconto_pacco_valore_eur)\s*(=|<)\s*(0|1)[^\n]*",
                         src):
        riga, col = m.group(0), m.group(1)
        if riga.strip().startswith("#"):
            continue     # i commenti raccontano il difetto, non lo fanno
        # il contorno stretto: le WHERE del progetto vanno a capo, e la
        # valuta (o la colonna gemella in sats) sta nella riga accanto
        intorno = src[max(0, m.start() - 120):m.end() + 120]
        if not any(k in intorno for k in FAMIGLIE[col]):
            sospetti.append(riga.strip()[:70])
    prova("nessun «euro a zero» senza la valuta accanto", [], sospetti)
    # e la prova che il censimento VEDE davvero qualcosa: a predicato
    # rotto uno «zero sospetti» sembrerebbe una promozione invece che
    # una cecita'
    prova("...e il censimento guarda davvero delle righe", True,
          len(re.findall(r"(sped_gratis_soglia_eur|sconto_pacco_valore_eur)"
                         r"\s*(=|<)\s*(0|1)", src)) >= 4)

    # ================================================================
    # IL CLIENT: dove un'unita' puo' diventare un'altra in silenzio
    # ================================================================
    mini = open("miniapp.html", encoding="utf-8").read()
    # IL CAMPO LIBERO scrive nel campo dell'unita' SCELTA, e per questo
    # `campo` e' una FUNZIONE della bozza: con una stringa fissa, chi
    # scrive 50.000 pensando sats se li ritroverebbe in `valoreEur` —
    # una soglia da cinquantamila euro, cioe' una promessa morta zitta.
    # E' il posto piu' facile del cantiere in cui sbagliare unita'.
    _sl = mini[mini.index("const SOGLIE_LIBERE = {"):
               mini.index("function sogliaBozza(")]
    prova("il campo libero dipende dalla VALUTA, non e' fisso", 2,
          _sl.count("campo: b => b.valuta === 'sats'"))
    prova("...e nessuna delle due mappe ha un campo fisso", False,
          "campo: '" in _sl)
    # e le pillole scrivono nello stesso campo del campo libero: una
    # pillola da 50.000 sats in `sogliaEur` sarebbe lo stesso danno
    prova("le pillole della spedizione scelgono il campo dalla valuta",
          True, "spedGratisBozza.valuta === 'sats'"
          in pezzo_js(mini, "function spedGratisPill"))
    # LA QUINTA SUPERFICIE (la riga nel form Vendi) passa dal giudice
    # unico come le altre quattro: era l'unica che la promessa se la
    # scriveva a mano, con l'euro cotto dentro — col toggle avrebbe
    # detto «gratis da 50.000 €» al venditore, sul suo negozio.
    _hp = pezzo_js(mini, "function aggiornaHintPolitiche")
    prova("la riga del form passa dal giudice della promessa", True,
          "regolaSpedGratis(" in _hp
          and "frasePromessaSpedGratis(" in _hp)
    # ...e nel CODICE non c'e' piu' un euro scritto a mano (i commenti
    # si tolgono: quello che racconta il difetto lo nomina apposta)
    prova("...e non scrive piu' l'euro a mano", False,
          "€" in re.sub(r"/\*.*?\*/", "", _hp, flags=re.S))

    # ---- LA RIGA DELLO SCONTO E' VIVA (ago 2026, chiesto da Andrea):
    # diceva che la regola esiste, adesso dice anche quando QUESTO
    # prezzo la fa scattare DA SOLO. Il caso e' nato col mono che
    # sconta: prima un articolo solo non scattava mai.
    _rs = pezzo_js(mini, "function rigaScontoForm(rs){", "\n}")
    prova("la riga ha un giudice solo", 1,
          mini.count("function rigaScontoForm("))
    prova("...e a chiamarla e' aggiornaHintPolitiche", True,
          "rigaScontoForm(rs)" in _hp)
    # I DUE STATI: la regola quando il prezzo non la tocca, l'EFFETTO
    # quando la fa scattare. Il generico e' quello di sempre.
    prova("...e gli stati sono due", (True, True),
          ("Il tuo negozio fa " in _rs, "scatta da" in _rs))
    # IL VERDETTO PASSA DAL GIUDICE CONDIVISO, mai un confronto scritto
    # qui: la riga del form e la card devono dire la stessa cosa sullo
    # stesso prezzo — promettere lo sconto e poi non mostrarlo e' il
    # difetto peggiore, perche' a scoprirlo e' chi ha appena pubblicato.
    prova("il verdetto viene da scontoScatta", True,
          "scontoScatta(r, art, sellValuta, 1)" in _rs)
    prova("...e la riga non confronta niente per conto suo", False,
          ">= r.quanto" in _rs)
    # A QUANTITA' 1: i pezzi li sceglie chi compra, e la domanda del
    # venditore e' «questa cifra basta gia'?»
    prova("...a quantita' UNO, l'articolo da solo", False,
          "qtaForm(" in _rs)
    # IL NETTO passa dalle funzioni condivise, mai l'aritmetica a mano
    prova("il netto lo fanno scontaSats/scontaEur", (True, True),
          ("scontaEur(pieno, pct)" in _rs, "scontaSats(pieno, pct)" in _rs))
    prova("...e la riga non sconta per conto suo", False,
          "100 -" in _rs.replace("−", ""))
    # IL PREZZO IN SATS con la ricetta di satsAnnuncio, o la riga del
    # form e la card convertirebbero diverso lo stesso listino in euro
    _pf = pezzo_js(mini, "function prezzoFormSats(){", "\n}")
    prova("il listino in euro si converte come in vetrina", True,
          "Math.round(e / eurPerSat)" in _pf)
    prova("...e a cambio muto vale 0, cioe' «non lo so»", True,
          "(e > 0 && cambioVivo) ?" in _pf)
    # SU UN'ASTA LA RIGA TACE: l'ordine nasce da crea_ordine_pagato,
    # che NON sconta. Senza, lo stato specifico direbbe «chi lo compra
    # paga X» di una cifra che nessuno paghera' mai.
    prova("su un'asta la riga tace", True,
          "const asta = astaAccesa();" in _hp
          and "sc.style.display = (rs.length && !asta) ? '' : 'none';" in _hp)
    # LE DUE CHIAMATE SI GUARDANO IN CODA e non «da qualche parte nel
    # corpo»: la tortura ha smascherato la forma debole — un
    # `if (0) aggiornaHintPolitiche();` messo davanti lasciava la
    # sentinella verde con la chiamata vera tolta. E' la lezione del
    # reaper, terza volta: una sentinella si scrive rompendo il codice.
    prova("...e il toggle dell'asta la rifa', per ultima cosa", True,
          pezzo_js(mini, "function aggiornaAstaForm(){", "\n}")
          .rstrip().endswith("\n  aggiornaHintPolitiche();"))
    # IL MOMENTO DI QUIETE (chiesto da Andrea): digitando «80 000» la
    # riga attraverserebbe la soglia sotto le dita — un lampeggio
    # invece di un avviso. Mentre si digita non si tocca niente.
    prova("il campo prezzo non riscrive la riga a ogni carattere", True,
          'id="sellPrice"' in mini
          and 'oninput="scontoHintFraPoco()"' in mini)
    prova("...e la differita e' una sola", 1,
          mini.count("function scontoHintFraPoco("))
    _fp = pezzo_js(mini, "function scontoHintFraPoco(){", "\n}")
    prova("...e aspetta la quiete invece di riscrivere subito", True,
          "setTimeout(aggiornaHintPolitiche, SCONTO_HINT_QUIETE)" in _fp)
    # LA RIGA DA NON TOGLIERE: la chiamata immediata SPEGNE il timer in
    # sospeso, o un render vecchio si riscriverebbe addosso a quello
    # nuovo mezzo secondo dopo.
    prova("...e la chiamata immediata spegne quella in sospeso", True,
          _hp.split("{", 1)[1].lstrip()
             .startswith("clearTimeout(scontoHintTimer);"))
    # IL TOGGLE DELLA VALUTA e' immediato — un gesto, non digitazione —
    # e da li' passano anche i due AZZERAMENTI del form
    prova("il toggle della valuta rifa' la riga subito", True,
          pezzo_js(mini, "function impostaSellValuta(v){", "\n}")
          .rstrip().endswith("\n  aggiornaHintPolitiche();"))
    # E IN MODIFICA LA RIGA PARLA UGUALE, che e' il caso in cui serve
    # di piu': l'annuncio esiste gia' e puo' gia' star scontando. Vale
    # solo se il prezzo E' GIA' NEL CAMPO quando il ricalcolo parte —
    # editListing riempie e POI chiama go('vendi'), che e' l'unico
    # posto da cui la riga si rifa' entrando nella vista.
    # `rfind` e non `find`: col primo, una seconda scrittura del campo
    # infilata DOPO il go() lasciava la sentinella verde (l'ha detto la
    # tortura). Quello che deve valere e' che quando il ricalcolo parte
    # NESSUNA scrittura del prezzo sia ancora in arrivo.
    _ed = pezzo_js(mini, "function editListing(id){", "\n}")
    prova("la modifica precompila il prezzo PRIMA di aprire il form",
          True,
          0 < _ed.rfind("el('sellPrice').value")
            < _ed.find("go('vendi')"))
    prova("...e entrando in Vendi la riga si rifa'", True,
          "aggiornaHintPolitiche();"
          in pezzo_js(mini, "if (view==='vendi') {", "\n  }"))
    # L'UNITA' si scrive in UN posto solo: sette superfici che se la
    # scrivono da se' sono sette posti dove un giorno una dice «€» su
    # una soglia in sats.
    # DALL'AGO 2026 (le promesse a badge) la sentinella non e' piu' un
    # numero magico ma BINARIA: nessuna superficie mette in fila un
    # numero e la sua unita' per conto suo — lo fa cifraSoglia, e
    # unitaSoglia ha un chiamante solo. Col conto a mano ogni badge
    # nuovo faceva alzare il numero, che e' il modo in cui una
    # sentinella smette di sorvegliare e diventa un promemoria.
    prova("l'unita' della soglia ha UNA fonte sola", 1,
          mini.count("function unitaSoglia("))
    prova("...e la cifra pure", 1, mini.count("function cifraSoglia("))
    # DALL'AGO 2026 il posto che li mette in fila e' cifraConUnita: la
    # riga viva del form Vendi scrive un PREZZO, che in euro ha i
    # centesimi, e non poteva passare da cifraSoglia (che formatta con
    # `fmt` perche' una soglia e' intera). La fessura si e' spostata di
    # un gradino, il conto NO: unitaSoglia ha ancora un chiamante solo.
    prova("...e unitaSoglia la chiama solo cifraConUnita", 2,
          mini.count("unitaSoglia("))
    prova("...e il posto che mette numero e unita' in fila e' uno", 1,
          mini.count("function cifraConUnita("))
    # ...e tutte le superfici della promessa passano da li': le due
    # frasi lunghe, le due etichette corte, i due inviti del carrello e
    # i QUATTRO siti della pagina Paga (le due sospese e i due «quanto
    # manca», 12 ago 2026 — i verdi non portano cifra) — dieci
    # chiamate piu' la definizione
    prova("...e tutte le superfici della promessa passano da cifraSoglia",
          11, mini.count("cifraSoglia("))
    # IL CONFRONTO DEL CARRELLO non converte piu' a soglia in SATS:
    # li' e' sats contro sats, esatto, e la riga compare anche a
    # cambio muto. E' il guadagno della scelta. Dal 13 ago 2026 il
    # confronto vive nel giudice statoScontoPacco (lo chiamano badge
    # E totale scontato), non piu' dentro l'invito.
    # ...e dai DUE CRITERI INSIEME (ago 2026) il confronto e' PER GAMBA:
    # ognuna dice in che unita' sta contando, e quella che il cambio non
    # sa misurare torna `null` — gambaInvito la salta invece di darle
    # zero, cosi' l'altra continua a invitare.
    _gsp = pezzo_js(mini, "function statoScontoPacco(tot){", "\n}")
    prova("il confronto del carrello converte SOLO in euro", True,
          "if (r.criterio !== 'valore') return pezziSet();" in _gsp)
    prova("...e a soglia in sats non chiede il cambio", True,
          "if (r.valuta === 'sats') return tot || 0;" in _gsp)
    # la cintura di ieri resta intatta: senza cambio vivo, in EURO, la
    # gamba non si misura e non compare (meglio un'assenza che una cifra
    # inventata) — ma adesso a cadere e' la sola gamba, non la promessa
    prova("...ma in euro senza cambio vivo tace ancora", True,
          "cambioVivo ? Math.floor((tot || 0) * eurPerSat) : null" in _gsp)


# ====================================================================
def prove_suggerimenti():
    """I SUGGERIMENTI DAL BOT (ago 2026): accesi di serie, ma col
    RITMO. Qui si torturano le due cose che li rendono non-spam — il
    giudice che sa distinguere «mai toccato» da «spento da lui», e il
    tetto per PERSONA — piu' le righe di forma che un riordino
    farebbe sparire senza rompere niente."""
    print("\n[i suggerimenti dal bot]")
    import sqlite3

    # ---- IL GIUDICE DELL'INTERRUTTORE ------------------------------
    # Quattro casi, e sono tutti quelli che esistono: il gesto c'e' o
    # non c'e', il default e' acceso o spento.
    for di_serie in (True, False):
        amb = {"SUGGERIMENTI_DI_SERIE": di_serie}
        exec(pezzo("suggerimenti_accesi"), amb)
        acc = amb["suggerimenti_accesi"]
        prova(f"default {di_serie}: mai toccato → vale il default",
              di_serie, acc(0, 0))
        # ...e il valore grezzo di chi non ha mai scelto NON conta: e'
        # 0 per tutti, anche per chi i suggerimenti li riceve
        prova(f"default {di_serie}: mai toccato, valore 1 → il default",
              di_serie, acc(0, 1))
        prova(f"default {di_serie}: ACCESO da lui → acceso comunque",
              True, acc(1, 1))
        prova(f"default {di_serie}: SPENTO da lui → spento comunque",
              False, acc(1, 0))
    # LA PROVA CHE VALE IL CANTIERE: rovesciare il default non tocca
    # chi ha scelto. Se un domani `suggerimenti_scelti` sparisse in un
    # riordino, questa diventa rossa — ed e' l'unica cosa che protegge
    # chi ha detto no.
    amb_on = {"SUGGERIMENTI_DI_SERIE": True}
    amb_off = {"SUGGERIMENTI_DI_SERIE": False}
    exec(pezzo("suggerimenti_accesi"), amb_on)
    exec(pezzo("suggerimenti_accesi"), amb_off)
    prova("chi ha SCELTO non lo scavalca nessun default", True,
          amb_on["suggerimenti_accesi"](1, 0)
          == amb_off["suggerimenti_accesi"](1, 0) is False
          and amb_on["suggerimenti_accesi"](1, 1)
          == amb_off["suggerimenti_accesi"](1, 1) is True)

    # ---- IL RITMO, su un database di cartone -----------------------
    def db_finto():
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.executescript("""
        CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY,
          suggerimenti_annunci INT DEFAULT 0,
          suggerimenti_scelti INT DEFAULT 0,
          suggerito_il INT DEFAULT 0,
          suggerito_sconto INT DEFAULT 0,
          suggerito_sped INT DEFAULT 0);
        INSERT INTO utenti(tg_id) VALUES(1), (2), (3);
        -- 2 ha SPENTO a mano, 3 ha ricevuto un consiglio ieri
        UPDATE utenti SET suggerimenti_scelti=1, suggerimenti_annunci=0
          WHERE tg_id=2;
        """)
        return con

    ADESSO = 1_800_000_000
    amb = {"SUGGERIMENTI_DI_SERIE": True, "SUGGERIMENTI_OGNI_GIORNI": 7}
    exec(pezzo("suggerimenti_accesi"), amb)
    exec(pezzo("_puo_suggerire"), amb)
    # il catalogo dei timbri si ripete qui, e una prova di forma piu'
    # sotto lo incrocia col sorgente: se divergessero, la whitelist
    # proverebbe qualcosa che in produzione non esiste
    amb["TIMBRI_SUGGERIMENTO"] = ("suggerito_sconto", "suggerito_sped")
    exec(pezzo("_timbra_suggerimento"), amb)
    puo, timbra = amb["_puo_suggerire"], amb["_timbra_suggerimento"]

    con = db_finto()
    prova("mai toccato e mai servito: si puo'", True, puo(con, 1, ADESSO))
    prova("chi l'ha SPENTO a mano: mai", False, puo(con, 2, ADESSO))
    prova("utente che non esiste: mai (fail-closed)", False,
          puo(con, 999, ADESSO))
    # il timbro chiude la porta per N giorni, ed e' il cuore del giro
    timbra(con, 1, ADESSO)
    con.commit()
    prova("subito dopo il timbro: chiuso", False, puo(con, 1, ADESSO))
    prova("dopo 6 giorni: ancora chiuso", False,
          puo(con, 1, ADESSO + 6 * 86400))
    prova("al settimo giorno esatto: riapre", True,
          puo(con, 1, ADESSO + 7 * 86400))
    # IL «MAI INSIEME» non e' una regola scritta: e' questo timbro.
    # Due suggerimenti di funzione nello stesso giro passano dallo
    # stesso giudice, e il secondo trova la porta chiusa dal primo.
    prova("il secondo suggerimento dello stesso giro non parte", False,
          puo(con, 1, ADESSO))
    con.close()

    # il ritmo a 0 e' il freno d'emergenza: la raffica di ieri
    amb["SUGGERIMENTI_OGNI_GIORNI"] = 0
    con = db_finto()
    timbra(con, 1, ADESSO)
    con.commit()
    prova("ritmo a 0: nessun tetto (la raffica di ieri)", True,
          puo(con, 1, ADESSO))
    prova("...ma chi l'ha spento resta spento anche senza ritmo", False,
          puo(con, 2, ADESSO))
    con.close()
    amb["SUGGERIMENTI_OGNI_GIORNI"] = 7

    # ---- IL TIMBRO SCRIVE SOLO COLONNE DI CASA ---------------------
    # Il nome finisce dentro una query: un nome che arriva da altrove
    # non deve poterci entrare mai, nemmeno oggi che i chiamanti sono
    # due e passano due letterali.
    con = db_finto()
    timbra(con, 1, ADESSO, "suggerito_sconto")
    prova("il timbro di funzione si scrive", 1,
          con.execute("SELECT suggerito_sconto AS s FROM utenti "
                      "WHERE tg_id=1").fetchone()["s"])
    rotto = False
    try:
        timbra(con, 1, ADESSO, "xp=999, suggerito_sped")
    except ValueError:
        rotto = True
    prova("un nome fuori catalogo non entra nella query", True, rotto)
    con.close()

    # ---- LA MIGRAZIONE DEL PREGRESSO -------------------------------
    # Fa l'unica cosa dimostrabile (chi e' acceso ha scelto), ed e'
    # idempotente: chi spegne DOPO non viene ripescato mai piu'.
    con = db_finto()
    con.execute("UPDATE utenti SET suggerimenti_annunci=1 WHERE tg_id=3")
    SQL = ("UPDATE utenti SET suggerimenti_scelti=1 "
           "WHERE suggerimenti_annunci=1 AND suggerimenti_scelti=0")
    prova("registra il gesto di chi li aveva accesi", 1,
          con.execute(SQL).rowcount)
    prova("...e al secondo giro non trova piu' nessuno", 0,
          con.execute(SQL).rowcount)
    con.execute("UPDATE utenti SET suggerimenti_annunci=0 WHERE tg_id=3")
    prova("chi spegne dopo la migrazione non si riaccende", 0,
          con.execute(SQL).rowcount)
    prova("...e resta spento davvero", False, puo(con, 3, ADESSO))
    con.close()

    # ---- LA FORMA --------------------------------------------------
    src = open("server.py", encoding="utf-8").read()
    prova("l'interruttore ha UN giudice solo", 1,
          src.count("def suggerimenti_accesi("))
    prova("la whitelist dei timbri e' quella che si e' provata", True,
          'TIMBRI_SUGGERIMENTO = ("suggerito_sconto", "suggerito_sped")'
          in src)
    prova("il ritmo ha UN giudice solo", 1, src.count("def _puo_suggerire("))
    # IL TIMBRO PRIMA DELL'INVIO, il patto delle campagne: un errore di
    # rete puo' perdere un consiglio, mai raddoppiarlo — e qui
    # raddoppiarlo sarebbe la raffica che il ritmo esiste per togliere
    corpo = pezzo("suggerisci_funzioni")
    prova("suggerisci_funzioni: timbra PRIMA di notificare", True,
          corpo.index("_timbra_suggerimento(") < corpo.index("await notifica("))
    compl = pezzo("_chiedi_completamento")
    prova("_chiedi_completamento: timbra PRIMA di notificare", True,
          compl.index("_timbra_suggerimento(") < compl.index("await notifica("))
    # ...e il gate viene PRIMA del timbro per-annuncio, o gli annunci
    # resterebbero «avvisati» senza che nessuno abbia avvisato niente
    prova("...e il gate viene prima del timbro per annuncio", True,
          compl.index("_puo_suggerire(")
          < compl.index("completamento_avvisato=1"))
    # LA CODA CON L'INTERRUTTORE in fondo a OGNI messaggio: chi riceve
    # un consiglio deve sempre vedere come farlo smettere
    prova("la coda esiste in un posto solo", 1,
          src.count("CODA_SUGGERIMENTI = ("))
    prova("...e la portano tutti e due i mittenti", 2,
          src.count("CODA_SUGGERIMENTI.format("))
    prova("la coda dice dove si spengono", True,
          "Profilo" in src[src.index("CODA_SUGGERIMENTI = ("):
                           src.index("def suggerimenti_accesi(")])
    # I due suggerimenti di funzione non si mandano dove non
    # potrebbero servire: lo sconto vuole ALMENO DUE annunci (sotto
    # non scatterebbe mai), la spedizione gratis solo a chi spedisce
    cat = src[src.index("SUGGERIMENTI_FUNZIONE = ("):
              src.index("async def suggerisci_funzioni(")]
    prova("lo sconto non si suggerisce a chi ha un annuncio solo", True,
          "COUNT(*) >= 2" in cat)
    prova("la spedizione gratis solo a chi spedisce davvero", True,
          "consegna IN ('spedizione','entrambe')" in cat)
    prova("ognuno guarda la SUA leva", 2, cat.count('"leva": lambda:'))
    # e /api/me dice lo STATO EFFETTIVO, non il valore grezzo: col
    # grezzo il bottone direbbe «Attiva» a chi li ha gia' accesi, e il
    # suo tocco li spegnerebbe
    prova("/api/me passa dal giudice", 1,
          src.count('profilo["suggerimenti_annunci"] = suggerimenti_accesi('))


# ====================================================================
def prove_sped_gratis():
    """LA SPEDIZIONE GRATIS SOPRA SOGLIA (ago 2026): la seconda
    promessa di negozio. Qui si tortura la matematica e — soprattutto —
    l'INDIPENDENZA dalla prima: le due guardano lo stesso numero senza
    vedersi, e se un domani una cominciasse a misurare l'altra queste
    prove diventerebbero rosse tutte insieme."""
    print("\n[la spedizione gratis sopra soglia]")
    amb = {"SPED_GRATIS_ATTIVO": True, "SPED_GRATIS_MIN_EUR": 1,
           "SPED_GRATIS_MIN_SATS": 1, "VALUTE_SOGLIA": ("eur", "sats")}
    for f in ("_importo_accordo", "_prezzo_lampo", "_unitario_effettivo",
              "_eur_interi", "_sped_gratis", "_sconto_pacco",
              "_conto_ordine", "_valuta_soglia", "_regola_sped_gratis"):
        exec(pezzo(f), amb)
    conto, unit = amb["_conto_ordine"], amb["_unitario_effettivo"]
    _sg, _rg = amb["_sped_gratis"], amb["_regola_sped_gratis"]
    CAMBIO = 100_000.0        # 1 BTC = 100.000 €, cioe' 1.000 sats = 1 €

    def eur(sats):
        return amb["_eur_interi"](sats, CAMBIO)

    def gratis(misura_eur, soglia):
        """lo shim a valuta EURO (ago 2026, la scelta della valuta): le
        prove di ieri girano identiche riga per riga, ed e' la
        regressione dei negozi in euro a costo zero. `articolo` sta a 0
        apposta — a valuta 'eur' non si guarda mai, e se un domani lo
        guardasse queste diventerebbero rosse."""
        return _sg(0, misura_eur, soglia, "eur")

    def gratis_sats(articolo, soglia):
        """il gemello in SATS: la misura e' l'articolo COM'E', e
        `articolo_eur` sta a None — cosi' ogni prova dimostra anche che
        quella soglia non ha bisogno di nessuna conversione."""
        return _sg(articolo, None, soglia, "sats")

    def reg(soglia_eur):
        """lo shim del lettore in EURO: esce la sola soglia, come ieri"""
        return _rg(0, soglia_eur, "eur")[0]

    def sconta(art, soglia, pct, valuta="eur"):
        """lo sconto carrello a valore, per i quadranti qui sotto"""
        return amb["_sconto_pacco"](art, eur(art), 2, "valore", soglia,
                                    pct, valuta)

    # --- LA SOGLIA E' UNA PORTA, e al filo esatto e' APERTA -----------
    # La soglia e' in EURO dall'ago 2026, e la misura arriva gia'
    # convertita dal chiamante: la pura non ha mai visto il cambio.
    prova("soglia esatta: a 100 € su 100 € la spedizione e' gratis",
          True, gratis(eur(100_000), 100))
    prova("un euro sotto: si paga", False, gratis(eur(99_000), 100))
    prova("...e il floor lo decide: 99.999 sats sono 99 €", False,
          gratis(eur(99_999), 100))
    prova("ben sopra: gratis e basta (non c'e' una scala)", True,
          gratis(eur(9_000_000), 100))
    prova("soglia 0 = promessa spenta: non e' mai gratis", False,
          gratis(eur(9_000_000), 0))
    prova("articolo 0 (payload storto): non regala niente", False,
          gratis(eur(0), 100))
    prova("soglia negativa (colonna sporca): spenta", False,
          gratis(eur(9_000_000), -100))
    # IL CAMBIO MUTO: la misura arriva None e la promessa non scatta —
    # fail-closed dentro il giudice, come per lo sconto a valore.
    prova("cambio muto: la spedizione NON e' gratis", False,
          gratis(None, 100))
    prova("...e non e' la soglia (col cambio sarebbe gratis)", True,
          gratis(eur(9_000_000), 100))
    prova("None non si legge come uno zero qualunque", False,
          gratis(None, 0))

    # --- LA SOGLIA IN SATS: la stessa porta, senza conversione --------
    prova("in sats, al filo esatto: gratis", True,
          gratis_sats(100_000, 100_000))
    prova("in sats, un sat sotto: si paga", False,
          gratis_sats(99_999, 100_000))
    prova("in sats, ben sopra: gratis", True,
          gratis_sats(9_000_000, 100_000))
    # LA PROVA CHE VALE PIU' DELLE ALTRE, ed e' il guadagno del
    # cantiere: `articolo_eur` e' None — cioe' CoinGecko muto — e la
    # promessa scatta lo stesso, perche' la sua misura non ha mai avuto
    # bisogno di una conversione. La gemella in euro, sopra, tace.
    prova("in sats la promessa scatta ANCHE a cambio muto", True,
          gratis_sats(9_000_000, 100_000))
    prova("soglia 0 in sats: spenta come in euro", False,
          gratis_sats(9_000_000, 0))
    # e una valuta che non sappiamo misurare non regala niente: il
    # ripiego naturale («sara' euro») e' proprio quello da non fare
    for storto in ("", "usd", "EUR", "Sats", None, 0):
        prova(f"valuta {storto!r}: la spedizione non e' gratis", False,
              _sg(9_000_000, eur(9_000_000), 100, storto))

    # --- IL LETTORE DELLE LEVE ---------------------------------------
    prova("regola normale: la soglia passa", 100, reg(100))
    prova("sotto il minimo: nessuna promessa", 0, reg(0))
    prova("il minimo esatto passa", 1, reg(1))
    prova("zero resta zero (spenta)", 0, reg(0))
    prova("None (colonna mai scritta): 0", 0, reg(None))
    prova("stringa illeggibile: 0, non un'esplosione", 0, reg("ciao"))
    amb["SPED_GRATIS_ATTIVO"] = False
    prova("leva generale spenta: nessuna promessa scatta", 0, reg(100))
    amb["SPED_GRATIS_ATTIVO"] = True
    # LA VALUTA nel lettore: esce accanto alla soglia, ed e' GIA'
    # quella dell'unita' scelta — un numero solo da guardare
    prova("lettore in euro: (soglia, valuta)", (25, "eur"),
          _rg(50_000, 25, "eur"))
    prova("lettore in sats: esce l'ALTRA cifra", (50_000, "sats"),
          _rg(50_000, 25, "sats"))
    prova("valuta vuota = euro (il mondo di prima della scelta)",
          (25, "eur"), _rg(50_000, 25, ""))
    prova("valuta None = euro (colonna mai scritta)", (25, "eur"),
          _rg(50_000, 25, None))
    prova("valuta fuori catalogo: nessuna promessa", (0, ""),
          _rg(50_000, 25, "usd"))
    prova("in sats sotto il minimo: nessuna promessa", (0, ""),
          _rg(0, 25, "sats"))
    amb["VALUTE_SOGLIA"] = ("eur",)
    prova("valuta tolta dalla leva: chi l'aveva scelta non promette piu'",
          (0, ""), _rg(50_000, 25, "sats"))
    prova("...ma l'altra continua", (25, "eur"), _rg(50_000, 25, "eur"))
    amb["VALUTE_SOGLIA"] = ("eur", "sats")

    # --- IL PUBBLICO: ogni chiave nella sua unita' --------------------
    exec(pezzo("_sped_gratis_pubblico"), amb)
    pubg = amb["_sped_gratis_pubblico"]
    prova("pubblico in euro: la chiave in sats tace",
          {"soglia": 0, "eur": 25, "valuta": "eur"},
          pubg(50_000, 25, "eur"))
    prova("pubblico in sats: la chiave in euro tace",
          {"soglia": 50_000, "eur": 0, "valuta": "sats"},
          pubg(50_000, 25, "sats"))
    prova("pubblico a promessa spenta: tacciono tutte",
          {"soglia": 0, "eur": 0, "valuta": ""}, pubg(0, 0, "eur"))
    prova("le due cifre non parlano MAI insieme", True,
          all(not (pubg(s, e, v)["soglia"] > 0 and pubg(s, e, v)["eur"] > 0)
              for s in (0, 50_000) for e in (0, 25)
              for v in ("eur", "sats", "usd", "")))

    # ================================================================
    # I DUE CATALOGHI DI SELECT DICONO LE STESSE PROMESSE
    # ================================================================
    # «I tuoi annunci» passa da CAMPI_MIEI e non da CAMPI_VETRINA:
    # senza gli stessi alias, il PROPRIETARIO e' l'unico a non vedere
    # la propria promessa sul proprio oggetto. E' successo davvero —
    # la prima stesura portava il solo lato EURO, perche' era di prima
    # che la valuta la scegliesse il venditore, e chi aveva messo la
    # soglia in SATS restava fuori.
    # E' un CENSIMENTO e non un elenco (la lezione del titolo nudo): si
    # estraggono gli alias dai due cataloghi e si chiede che la vetrina
    # non ne abbia uno in piu'. Il campo che qualcuno aggiungera' di la'
    # fra sei mesi entra nel conto da solo, e il diff lo NOMINA invece
    # di dire «due insiemi diversi».
    def _alias(nome):
        s = _SORGENTE[_SORGENTE.index(f"{nome} = ("):]
        return set(re.findall(r"u\.(\w+) AS (venditore_\w+)",
                              s[:s.index("\n\n")]))

    def _promesse(alias):
        return {a for c, a in alias
                if c.startswith(("sconto_pacco", "sped_gratis", "ferie_fino"))}

    in_vetrina = _promesse(_alias("CAMPI_VETRINA"))
    in_miei = _promesse(_alias("CAMPI_MIEI"))
    prova("CAMPI_MIEI porta tutte le promesse di CAMPI_VETRINA",
          set(), in_vetrina - in_miei)
    # ...e che il censimento VEDA davvero: con un predicato rotto, un
    # insieme vuoto meno un insieme vuoto fa vuoto, e la riga qui sopra
    # sembrerebbe una promozione invece che una cecita'.
    prova("il censimento vede le promesse della vetrina", True,
          len(in_vetrina) >= 9)
    prova("...e i due lati della soglia, con la valuta che decide", True,
          {"venditore_sconto_valore", "venditore_sconto_valore_eur",
           "venditore_sconto_valuta", "venditore_sped_gratis",
           "venditore_sped_gratis_eur",
           "venditore_sped_gratis_valuta"} <= in_miei)

    # ================================================================
    # LE DUE PROMESSE SONO INDIPENDENTI (decisione 3 di Andrea), ed e'
    # la parte che vale il cantiere: misurano ENTRAMBE l'articolo
    # LORDO, quindi nessuna delle due puo' spegnere l'altra. I quattro
    # quadranti, uno per uno.
    # ================================================================
    # 105.000 e non un numero tondo qualunque: e' scelto perche' il
    # NETTO (94.500) caschi SOTTO la soglia della spedizione. E' il
    # caso che smaschera una dipendenza, e con un lordo generoso non
    # succederebbe mai.
    lordo = 105_000          # sopra tutte e due le soglie: 105 €
    sog_sped, sog_sconto, pct = 100, 100, 10     # in EURO
    quadranti = [
        ("nessuna delle due", 50_000, False, 0),
        ("solo la spedizione", 120_000, True, 0),
        ("solo lo sconto", 120_000, False, 12_000),
        ("tutte e due", 120_000, True, 12_000)]
    for nome, art, att_g, att_s in quadranti:
        g = gratis(eur(art),
                   sog_sped if att_g or nome == "nessuna delle due" else 0)
        s = sconta(art, sog_sconto if att_s or
                   nome == "nessuna delle due" else 0, pct)
        if nome == "nessuna delle due":
            prova("quadrante: sotto soglia non scatta niente", (False, 0),
                  (g, s))
        else:
            prova(f"quadrante «{nome}»: spedizione", att_g, g)
            prova(f"quadrante «{nome}»: sconto", att_s, s)
    # LA PROVA CHE CONTA: lo sconto NON sposta la spedizione, e
    # viceversa. Se un domani la spedizione misurasse il NETTO, questo
    # carrello — 120.000 lordi, 108.000 netti — smetterebbe di avere la
    # spedizione gratis, e la riga qui sotto diventerebbe rossa.
    sconto = sconta(lordo, sog_sconto, pct)
    prova("lo sconto NON fa scendere la spedizione sotto soglia", True,
          gratis(eur(lordo), sog_sped) and sconto > 0
          and eur(lordo - sconto) < sog_sped)
    # ...e vale anche a VALUTE MISTE (ago 2026): un negozio puo' avere
    # lo sconto in euro e la spedizione gratis in sats, e le due
    # restano indipendenti — guardano lo stesso lordo, in due unita'
    prova("valute miste: le due promesse restano indipendenti", True,
          gratis_sats(lordo, 100_000) and sconta(lordo, 100, pct) > 0)
    prova("...e la spedizione gratis non tocca lo sconto", 10_500, sconto)
    c = conto(lordo, 0, 0, 0, sconto)      # la spedizione gia' azzerata
    prova("il totale col carrello scontato E la spedizione offerta",
          94_500, c["totale"])
    prova("invariante: lordo - sconto + 0 + protezione = totale",
          c["totale"], lordo - c["sconto"] + c["spedizione"] + c["protezione"])

    # --- LA LAMPO PUO' FAR SCENDERE SOTTO SOGLIA (decisione 5) -------
    # gemella della prova dello sconto: la misura e' quel che si paga
    # davvero per la merce, non un listino che in quel momento non e'
    # il prezzo di nessuno.
    a = {"prezzo_sats": 60_000, "prezzo_eur": 0, "valuta": "sats",
         "lampo_percento": 50, "lampo_scadenza": 2_000_000_000}
    pieno = 60_000 * 2
    scontato = unit(a, None, 1_000_000_000, 0.0) * 2
    prova("a listino il carrello arriva alla soglia", True,
          gratis(pieno, 100_000))
    prova("con la lampo −50% ci scende sotto: la spedizione si paga",
          False, gratis(scontato, 100_000))

    # --- IL MONO: la forma della promessa --------------------------
    # spedizione azzerata = spedizione_sats 0 in colonna, cioe' lo
    # stato di ogni annuncio con tariffa gratis dichiarata: la
    # divisione a ritroso di _righe_ordine resta esatta senza un ramo
    # nuovo. (Dall'ago 2026 anche lo sconto vale sul mono — li' la
    # divisione riaggiunge sconto_sats, e l'asimmetria fra le due
    # promesse non esiste piu'.)
    amb2 = {}
    exec(pezzo("_righe_ordine"), amb2)

    class _Fila:
        def __init__(self, d): self.d = d
        def __getitem__(self, k): return self.d[k]

    class _Con:
        def execute(self, q, p):
            self.r = _Fila({"titolo": "Tazza"})
            return self
        def fetchone(self): return self.r

    o = {"annuncio_id": 7, "quantita": 3, "prezzo_sats": 90_000,
         "spedizione_sats": 0, "protezione_sats": 0, "sconto_sats": 0}
    prova("mono con spedizione offerta: unitario esatto (30.000)",
          30_000, amb2["_righe_ordine"](_Con(), o)[0]["unitario_sats"])

    # ================================================================
    # LA FORMA: le righe che un riordino farebbe sparire senza rompere
    # nessuna prova funzionale.
    # ================================================================
    src = open("server.py", encoding="utf-8").read()
    prova("la promessa ha UN giudice solo", 1,
          src.count("def _sped_gratis("))
    prova("la regola si legge da UN lettore solo", 1,
          src.count("def _regola_sped_gratis("))
    # QUATTRO chiamanti e quattro soli — i due preventivi e i due
    # rami di compra —: se ne spuntasse un quinto, il conto si
    # deciderebbe in un posto che nessuno ha confrontato con gli altri
    # (il -1 e' la definizione, che porta lo stesso testo)
    prova("...e i chiamanti sono i quattro percorsi del conto", 4,
          src.count("_sped_gratis(articolo, misura_eur"))
    # ...e ricevono TUTTE E DUE le facce dell'articolo, sempre nello
    # stesso ordine: se un domani un percorso passasse solo l'euro, la
    # sua soglia in sats smetterebbe di scattare in silenzio
    prova("...e nessuno passa una faccia sola", 0,
          src.count("_sped_gratis(misura_eur"))
    # ...e la MISURA si conta una volta sola per percorso: e' cosi' che
    # «le due promesse guardano lo stesso numero» resta vero per
    # costruzione invece che per disciplina
    prova("la misura in euro si conta UNA volta per percorso", 4,
          src.count("misura_eur = _eur_interi("))
    # LA PURA RESTA PURA: senza sentinella, la prima SELECT infilata li'
    # dentro fa esplodere la suite (e qualcuno la commenterebbe)
    corpo = pezzo("_sped_gratis").split('"""')[-1]
    for vietato in ("INSERT", "UPDATE", "SELECT", "await", "con.",
                    "SPED_GRATIS", "cambio"):
        prova(f"_sped_gratis: niente {vietato} (e' una pura)", False,
              vietato in corpo)

    # LA PROMESSA NON ARRIVA MAI DAL COMPRATORE: una spedizione
    # azzerata da chi paga sarebbe un furto con la ricevuta.
    corpo_set = src[src.index("async def _compra_set("):
                    src.index("async def _preventivo_set(")]
    corpo_mono = src[src.index("async def compra("):
                     src.index("def crea_ordine_pagato(")]
    for chi, c2 in (("_compra_set", corpo_set), ("compra", corpo_mono)):
        prova(f"{chi}: la soglia non si legge dal payload", False,
              any(k in c2 for k in ('d.get("sped_gratis',
                                    'd.get("gratis', 'd.get("soglia')))
        prova(f"{chi}: la regola arriva dalla riga del VENDITORE", True,
              "_regola_sped_gratis(" in c2 and "WHERE tg_id=?" in c2)

    # LA PROMESSA SI LEGGE GUARDANDO LA STRADA, MAI IL SUO PREZZO (ago
    # 2026): in compra() il gate era «if sped:», cioe' i soli sats, e su
    # un listino in SATS con la tariffa ancorata all'EURO quei sats sono
    # 0 — la promessa non si leggeva nemmeno e la spedizione si pagava,
    # mentre la pagina Paga scriveva «gratuita». Una cifra come guardia
    # e' sempre il posto dove entra questo bug: a 0 sembra «non c'e'
    # spedizione», e a 0 ci si arriva in due modi onesti (l'ancora
    # all'euro e la tariffa gratis dichiarata).
    # La sentinella nomina il gate INSIEME a cio' che protegge: il solo
    # 'if scelta == "spedizione":' compare tre volte in compra() e
    # passerebbe col bug ancora dentro — provato rimettendolo.
    # (Dall'ago 2026 la SELECT e' unica e incondizionata — porta anche
    # la regola dello SCONTO, che vale su ogni strada — e sotto il gate
    # della strada resta la sola lettura della promessa di spedizione.)
    prova("compra: la promessa si legge sulla STRADA, non sulla cifra",
          True, ('if scelta == "spedizione":\n'
                 '        sog_gratis, val_sg = _regola_sped_gratis(')
          in corpo_mono)
    prova("compra: il gate a cifra non torna", False,
          "\n    if sped:\n" in corpo_mono)

    # IL DOVUTO IN USCITA NON CONOSCE LA TARIFFA OFFERTA. E' la stessa
    # riga della colonna testimone dello sconto, e il danno sarebbe
    # identico: un netto_venditore(prezzo + sped_gratis_sats) farebbe
    # uscire dall'escrow DI ALTRI ORDINI la differenza, e la cintura di
    # paga_venditore non lo vedrebbe (per lei dovuto e bolt11
    # combacerebbero).
    prova("netto_venditore non conosce la spedizione offerta", False,
          "sped_gratis" in pezzo("netto_venditore"))
    for nome in ("_sblocca_sats", "_rimborsa_compratore",
                 "deposita_invoice"):
        prova(f"{nome}: il dovuto NON riaggiunge la tariffa offerta",
              False, "sped_gratis" in pezzo(nome).split('"""')[-1])
    # e nemmeno il CSV, che e' contabilita': li' conta cio' che e'
    # stato pagato davvero
    prova("l'export non conosce la tariffa offerta", False,
          "sped_gratis" in pezzo("esporta_csv")
          if "def esporta_csv(" in src else False)

    # E' un costrutto del CHECKOUT: non esce sui relay (il NIP-99 resta
    # col prezzo pieno, come per lampo, sconto e tariffa punto).
    for nome in ("tag_commercio", "evento_annuncio"):
        prova(f"{nome}: cieco alla spedizione gratis", False,
              "sped_gratis" in pezzo(nome))
    # UN SOLO ENDPOINT scrive le soglie, e le scrive TUTTE E DUE nello
    # stesso UPDATE: lo spegnimento (che azzera entrambe) e il
    # salvataggio (che conserva l'altra col COALESCE). Due UPDATE in
    # due punti sarebbero il mezzo secondo con la promessa a meta'.
    corpo_epg = src[src.index("async def imposta_sped_gratis("):
                    src.index("async def imposta_ferie(")]
    # (fuori dall'endpoint le due colonne compaiono solo in LETTURA —
    # le WHERE dell'avviso, del suggerimento e del libro mastro —
    # quindi si contano gli UPDATE, non le occorrenze del nome)
    # DUE: lo spegnimento (che azzera tutto) e il salvataggio (che
    # conserva l'altra unita'), e non uno di piu'
    prova("le soglie si scrivono SOLO nel loro endpoint", 2,
          src.count("UPDATE utenti SET sped_gratis_"))
    prova("...e tutti e due gli UPDATE stanno li' dentro", 2,
          corpo_epg.count("UPDATE utenti SET sped_gratis_"))
    prova("lo spegnimento azzera TUTTE E DUE le unita'", True,
          "sped_gratis_soglia=0" in corpo_epg
          and "sped_gratis_soglia_eur=0" in corpo_epg)
    # LA PROVA CHE HA CAMBIATO LATO (ago 2026): fino a ieri diceva «la
    # colonna in sats non si scrive piu'», e certificava il mondo in cui
    # i sats non erano piu' una soglia possibile. Adesso si scrive
    # eccome — dietro il COALESCE, cosi' salvare in una valuta non
    # cancella la cifra dell'altra, che e' cio' che rende il toggle
    # reversibile senza chiedere niente a nessuno.
    prova("la colonna in sats si scrive, dietro COALESCE", True,
          "sped_gratis_soglia=COALESCE(?, sped_gratis_soglia)" in corpo_epg)
    prova("...e mai secca, che cancellerebbe l'altra unita'", 0,
          corpo_epg.count("sped_gratis_soglia=?"))
    # LA DECISIONE STA NELLO STESSO PUNTO nei tre percorsi: DOPO il
    # conto della tariffa. Se il preventivo decidesse prima, la pagina
    # direbbe «gratuita» dove la invoice risponde 503.
    for chi, c2 in (("_compra_set", corpo_set), ("compra", corpo_mono)):
        prova(f"{chi}: si decide DOPO aver contato la tariffa", True,
              c2.index("_sped_gratis(articolo, misura_eur")
              < c2.index("_conto_ordine("))

    # ================================================================
    # IL PASSAGGIO ALL'EURO (ago 2026)
    # ================================================================
    # LA MISURA HA UN GIUDICE SOLO, e la sua purezza e' il perno del
    # cantiere: riceve gli euro, non va a prenderli. Se un domani
    # `cambio` comparisse nel corpo di _sped_gratis, la pura avrebbe
    # cominciato a fare I/O e la CI lo direbbe (vedi il loop dei
    # vietati qui sopra, dove «cambio» c'e' apposta).
    prova("la conversione della misura ha UN giudice solo", 1,
          src.count("def _eur_interi("))
    corpo_eur = pezzo("_eur_interi").split('"""')[-1]
    for vietato in ("INSERT", "SELECT", "await", "con.", "SPED_GRATIS",
                    "SCONTO_PACCO"):
        prova(f"_eur_interi: niente {vietato} (e' una pura)", False,
              vietato in corpo_eur)
    # IL CAMBIO SI CHIEDE SOLO SE SERVE: un negozio senza promesse in
    # euro non deve pagare un giro di rete che ieri non faceva.
    # ...e dall'ago 2026 la guardia nomina anche la VALUTA: a soglia in
    # SATS quel giro di rete non si fa affatto, perche' la misura e'
    # l'articolo stesso. E' il guadagno della scelta, e senza questa
    # riga un riordino lo rimetterebbe in piedi senza rompere niente.
    # (Col mono che sconta la guardia copre le DUE promesse insieme:
    # spedizione gratis in euro, o soglia dello sconto a valore in
    # euro — e a tutte e due in sats il giro di rete non parte.)
    prova("compra: il cambio per la promessa ha una guardia", True,
          ('if cambio_misura <= 0 and ((sog_gratis > 0 and '
           'val_sg == "eur")') in corpo_mono)
    # LE QUATTRO GUARDIE del cambio nominano tutte la valuta: se una se
    # ne dimenticasse, quel percorso pagherebbe un giro di rete che non
    # gli serve — e su un negozio tutto-sats a CoinGecko muto la
    # promessa continuerebbe a scattare, quindi il difetto sarebbe
    # invisibile fino alla bolletta.
    # Si guarda PERCORSO PER PERCORSO e non con un conteggio: un
    # numero direbbe «quattro» anche se tre stessero nella stessa
    # funzione e una mancasse del tutto.
    # LE FETTE QUI SONO STRETTE, e non e' pignoleria: `corpo_set` qui
    # sopra arriva fino a _preventivo_set, quindi si porta dentro anche
    # preventivo_ordine — e una guardia tolta al SET passerebbe
    # inosservata perche' quella del preventivo e' ancora li' (provato
    # con la mutazione: sopravviveva).
    corpo_cset = src[src.index("async def _compra_set("):
                     src.index("def _strade_preventivo(")]
    corpo_prev = src[src.index("async def preventivo_ordine("):
                     src.index("async def _preventivo_set(")]
    corpo_pset = src[src.index("async def _preventivo_set("):
                     src.index("async def compra(")]
    for chi, c2 in (("_compra_set", corpo_cset), ("compra", corpo_mono),
                    ("preventivo_ordine", corpo_prev),
                    ("_preventivo_set", corpo_pset)):
        prova(f"{chi}: la guardia del cambio nomina la valuta", True,
              'sog_gratis > 0 and val_sg == "eur"' in c2)
    # e lo sconto la nomina su TUTTI E QUATTRO i percorsi (ago 2026,
    # il mono sconta): a valore in euro il cambio serve anche a lui.
    # Dai due criteri insieme la domanda non e' piu' «di che criterio e'
    # la regola» ma «ce n'e' UNA che lo chiede», e vive in un giudice
    # solo — scritta a mano quattro volte sarebbe il posto in cui un
    # giorno una resta indietro.
    for chi, c2 in (("_compra_set", corpo_cset), ("compra", corpo_mono),
                    ("preventivo_ordine", corpo_prev),
                    ("_preventivo_set", corpo_pset)):
        prova(f"{chi}: ...e quella dello sconto pure", True,
              "_sconto_vuole_cambio(regole_sc)" in c2)
    prova("...e il giudice di quella domanda e' UNO", 1,
          src.count("def _sconto_vuole_cambio("))
    # ...e a cambio muto NON nasce un 503 nuovo: si rinuncia alla
    # promessa, non all'acquisto. Il 503 resta dei due casi di sempre.
    prova("compra: i 503 restano due (listino EUR, tariffa ancorata)",
          2, corpo_mono.count("raise HTTPException(503"))
    prova("_compra_set: il 503 scatta solo sul bisogno DURO", True,
          "if serve_cambio_duro and cambio_misura <= 0:" in corpo_set
          or "if serve_cambio_duro:" in corpo_set)
    # `cambio_ordine` HA DUE MESTIERI, in quest'ordine (ago 2026):
    # prima e' il metro della CONVERSIONE — e le pure del conto lo
    # guardano SOLO dove un 503 ne ha gia' garantito il valore, quindi
    # deve restare zero dove non si converte niente — e poi, subito
    # prima dell'INSERT, si allarga al cambio del GIORNO, che e' quel
    # che finisce in colonna. La misura delle promesse resta in una
    # variabile SUA: se quel giro di rete in piu' finisse dentro
    # `cambio_ordine`, a cambiare non sarebbe un racconto ma il CONTO.
    prova("compra: la conversione viene dai due rami veri", 2,
          corpo_mono.count("cambio_ordine = await cambio_btc_eur()"))
    prova("...e la misura della promessa ha il suo giro", 1,
          corpo_mono.count("cambio_misura = await cambio_btc_eur()"))
    prova("_compra_set: idem, un giro solo e la conversione dietro guardia",
          (1, 1), (corpo_set.count("cambio_misura = await cambio_btc_eur()"),
                   corpo_set.count("cambio_ordine = cambio_misura")
                   - corpo_set.count("cambio_ordine = cambio_misura or ")))
    prova("_compra_set: cambio_ordine non si scrive mai dalla rete", 0,
          corpo_set.count("cambio_ordine = await"))

    # IL CAMBIO DEL GIORNO SI SCRIVE SEMPRE, e in colonna ci va QUELLO
    # (ago 2026). Senza, di un ordine tutto-sats non resta scritto
    # quanto valeva, e l'unico modo di raccontarlo dopo sarebbe il
    # cambio di OGGI: un numero che cambia ogni giorno su un fatto che
    # non cambia piu'.
    # (la fetta del set e' `corpo_cset`, quella STRETTA: `corpo_set`
    # arriva fino al preventivo e si porta dentro il suo _sped_pacco e
    # il suo giro di rete — con quella, due di queste righe restavano
    # verdi guardando codice di un'altra funzione)
    RIGA_GIORNO = "cambio_ordine = cambio_misura or cambio_noto_ora()"
    for chi, c2 in (("compra", corpo_mono), ("_compra_set", corpo_cset)):
        pos = c2.find(RIGA_GIORNO)
        prova(f"{chi}: il cambio del giorno si scrive sempre", 1,
              c2.count(RIGA_GIORNO))
        # ...e il METRO DELLA CONVERSIONE nasce a zero: scritto con un
        # cambio gia' dentro, il conto ne avrebbe uno anche dove
        # nessun 503 ne ha garantito il valore. Oggi non cambierebbe
        # una cifra (le pure lo guardano solo nei rami che il 503
        # copre), ma e' la riga che tiene vera quella frase.
        prova(f"{chi}: ...e il metro della conversione nasce a zero", 1,
              c2.count("cambio_ordine = 0.0"))
        # DALLA CACHE E MAI DALLA RETE: `cambio_noto_ora` non ha await,
        # o salterebbe il patto «niente await fra il ricontrollo e
        # l'INSERT» — e un ordine tutto-sats si legherebbe a CoinGecko
        # per un dato che serve solo a raccontarlo. (Riga assente = si
        # guarda tutto il corpo, cioe' rossa: mai un verde per finta.)
        prova(f"{chi}: ...e viene dalla cache, mai dalla rete", False,
              "await cambio_btc_eur()" in (c2[pos:] if pos >= 0 else c2))
        # E STA DOPO L'ULTIMA RIGA DI CONTO: spostata piu' su, il conto
        # vedrebbe un cambio dove nessun 503 ne ha garantito il valore
        # — cioe' una tariffa ancorata all'euro convertita con un
        # numero che potrebbe non esserci.
        prova(f"{chi}: ...dopo l'ultima riga di conto", True,
              pos > c2.rfind("_sped_pacco("))
        # ...e prima dell'INSERT, o la colonna prenderebbe lo zero
        prova(f"{chi}: ...e prima dell'INSERT", True,
              0 <= pos < c2.find("INSERT INTO ordini"))

    # TUTTE E TRE LE STRADE che creano un ordine scrivono il cambio
    # (la terza e' crea_ordine_pagato, l'asta gia' aggiudicata: il
    # cambio glielo passa chiudi_aste, una volta per giro). Chi ne
    # aprisse una quarta senza quella colonna lascerebbe un buco che
    # si vede solo mesi dopo, guardando un ordine che non sa dire
    # quanto valeva.
    teste = [m.start() for m in re.finditer(r"INSERT INTO ordini", _SORGENTE)]
    prova("le strade che creano un ordine sono tre", 3, len(teste))
    # si guarda l'ELENCO DELLE COLONNE, non «i primi N caratteri»: con
    # la finestra a caratteri togliere la colonna lasciava la riga
    # verde, perche' `cambio_ordine` ricompare poco sotto nella tupla
    # dei valori — l'ha detto la mutazione, non la rilettura.
    prova("...e tutte e tre scrivono il cambio del giorno", 3,
          sum("cambio_ordine" in _SORGENTE[i:_SORGENTE.index("VALUES", i)]
              for i in teste))

    # OGNI TARIFFA ANCORABILE ALL'EURO DEV'ESSERE NOMINATA NEI DUE
    # BLOCCHI DEL CAMBIO, e questa e' la prova che sostituisce un ramo
    # difensivo (ago 2026, cantiere del supplemento). Se una tariffa
    # nuova non entra nella guardia, _sped_pacco torna None e il conto
    # esplode: era `max(sped, None)` in _compra_set e `netto + None`
    # nel mono, cioe' un 500 col database aperto invece di un 503.
    # L'elenco NON si scrive a mano: si legge dalle colonne vere di
    # `annunci`, cosi' la quarta tariffa che qualcuno aggiungera' fa
    # diventare rossa questa riga da sola. (`spedizione_punto_eur` la
    # nominano via _tariffa_dichiarata, che le sceglie per via: si
    # accetta l'una o l'altra forma.)
    colonne_eur = sorted(set(re.findall(r'"(spedizione\w*_eur) REAL', _SORGENTE)))
    prova("le tariffe ancorabili all'euro sono tre", 3, len(colonne_eur))
    for chi, c2, tramite in (("compra", corpo_mono, "_tariffa_dichiarata(a, via)"),
                             ("_compra_set", corpo_set,
                              "_tariffa_dichiarata(a, via)")):
        for col in colonne_eur:
            prova(f"{chi}: il cambio guarda {col}", True,
                  f'["{col}"] > 0' in c2
                  or (col.startswith("spedizione_punto") and tramite in c2)
                  or (col == "spedizione_eur" and tramite in c2))

    # IL CLIENT: il giudice unico che alla prima promessa c'era e alla
    # seconda no (buco trovato col cantiere dell'euro). Sono QUATTRO le
    # superfici che la mostrano — testata negozio, «Altri oggetti»,
    # scheda annuncio, cassetto — e basta che una guardi la chiave
    # sbagliata perche' degli euro si leggano come sats.
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client ha UN giudice solo della promessa", 1,
          mini.count("function regolaSpedGratis("))
    prova("...e UNA sola frase pubblica", 1,
          mini.count("function frasePromessaSpedGratis("))
    # LE DUE NOTE DEI CASSETTI NON CI SONO PIU' (ago 2026, decisione
    # di Andrea): quella sulla lampo — «e' normale che una lampo incida
    # sulla cifra, non serve ripeterlo» — e quella su come si misura la
    # soglia nelle due valute. Le prove CAMBIANO LATO: chiedevano che
    # ci fossero in un posto solo e che le portassero tutti e due i
    # cassetti, adesso chiedono che non ci sia piu' nessuna fonte —
    # l'affermazione piu' forte, e impedisce che rientrino a meta'.
    prova("la nota su come si misura la soglia non c'e' piu'", 0,
          mini.count("notaSoglia"))
    prova("...e nemmeno quella sulla lampo", 0,
          mini.count("notaLampo"))
    # «TU INCASSI SEMPRE IN SATS» E' TORNATA (ago 2026, rimessa da
    # Andrea il giorno dopo averla persa col taglio delle note): e'
    # l'unica riga di quelle tolte a coprire un caso VERO — una soglia
    # in EURO accanto a un negozio che incassa in bitcoin si legge come
    # «mi pagano in euro», e nel cassetto non c'e' nient'altro che dica
    # il contrario. Il patto della nota che l'ospitava le sopravvive:
    # UN posto solo, e la portano tutti e due i cassetti.
    prova("la riga «incassi in sats» e' scritta UNA volta", 1,
          mini.count("function notaIncasso("))
    prova("...e la portano tutti e due i cassetti", 2,
          mini.count("notaIncasso()}"))
    # ...e dice i SATS, non «una nota» qualunque: senza questa, svuotare
    # la riga lascerebbe verdi le due qui sopra (la lezione della
    # tortura sulla nota della lampo, due giorni fa).
    _ni = pezzo_js(mini, "function notaIncasso")
    prova("...e nomina i sats", True, "sats" in _ni)

    # L'ARIA SOPRA IL BOTTONE DEL CASSETTO (ago 2026, bug dal campo:
    # «Aggiorna lo sconto» tagliava le pillole delle percentuali).
    # `.btn` non ha margine di base — lo spazio e' della COPPIA — e
    # dove sopra c'e' una fila di pillole, che margine sotto non ne ha,
    # il bottone arrivava a ZERO. La regola sta sul CASSETTO e non sui
    # due blocchi che l'hanno scoperta: cosi' la eredita anche il
    # cassetto di domani. E' la terza volta che questa famiglia
    # inciampa, e si trova solo misurando la pagina vera.
    prova("i bottoni dei cassetti hanno aria sopra", 1,
          mini.count(".acc-b .btn{margin-top"))

    # IL CAMPO LIBERO delle due soglie (ago 2026): le pillole non
    # riproducono le cifre nate dal travaso (14 €, 56 €), e chi se le
    # ritrova non potrebbe piu' rimetterle. UNA funzione per tutti e
    # due i cassetti: erano gia' due gemelle una volta, e sono
    # divergute.
    for f in ("sogliaLibera", "campoSogliaLibera", "sogliaMancante"):
        prova(f"il campo libero: {f} e' scritta UNA volta", 1,
              mini.count(f"function {f}("))
    prova("...e il campo lo montano tutti e due i cassetti", 2,
          mini.count("campoSogliaLibera('"))
    prova("...e tutti e due si fermano sul campo vuoto", 2,
          mini.count("sogliaMancante('"))
    # L'ANTEPRIMA IN GRASSETTO NON C'E' PIU' (ago 2026, decisione di
    # Andrea: «guardando il cassetto le pillole mi sembrano gia'
    # chiare»). La prova CAMBIA LATO — chiedeva che l'anteprima avesse
    # una fonte sola, adesso chiede che non ci sia piu' nessuna fonte:
    # e' l'affermazione piu' forte, e impedisce che rientri a meta'.
    prova("l'anteprima in grassetto non c'e' piu'", 0,
          mini.count("anteprimaSoglia"))
    # ...E QUEL CHE DICEVA SOLO LEI E' SALITO NELLA RIGA IN CIMA, che
    # e' l'unica prosa rimasta nel cassetto: il perimetro per criterio.
    # Senza queste due la riga si accorcia in un riordino e nessuno se
    # ne accorge — sono le stesse asserzioni di prima, spostate.
    _rs = pezzo_js(mini, "function renderScontoPacco")
    _riga = _rs[_rs.index("La spedizione è a parte"):]
    _riga = _riga[:_riga.index("</div>")]
    prova("la riga in cima dice che a valore basta un oggetto solo",
          True, "anche su un oggetto solo" in _riga)
    prova("...e a pezzi che le copie contano", True,
          "copie dello stesso articolo" in _riga)
    prova("...e con tutti e due i criteri, che ne basta una", True,
          "Basta che scatti una delle due" in _riga)
    prova("...e «un oggetto solo paga pieno» non torna da nessuna porta",
          False, "paga pieno, per quanto costi" in mini)
    # I DUE BLOCCHI SONO INDIPENDENTI (ago 2026): a 'entrambi' si
    # mostrano INSIEME, e le variabili non dicono piu' «quale criterio
    # e'» ma «questo blocco serve?». Se una delle due torna a un
    # confronto secco, il cassetto accende una gamba e ne nasconde
    # l'altra — e il venditore salva una promessa a meta' senza vederla.
    prova("il blocco dei PEZZI si apre anche a 'entrambi'", True,
          "const aPezzi = b.criterio === 'pezzi' "
          "|| b.criterio === 'entrambi';" in _rs)
    prova("...e quello a VALORE pure", True,
          "const aValore = b.criterio === 'valore' "
          "|| b.criterio === 'entrambi';" in _rs)
    prova("...e la terza pillola compare solo se la leva la offre", True,
          "criteri.includes('entrambi')" in _rs)
    # ...e il campo vuoto si ferma anche a 'entrambi', dove la gamba a
    # valore c'e' lo stesso: senza, si salverebbe uno zero
    prova("il campo vuoto ferma il salvataggio anche a 'entrambi'", True,
          "(b.criterio === 'valore' || b.criterio === 'entrambi')" in mini)
    # NIENTE CLAMP MUTO: a limare al minimo sarebbe il client, e il
    # venditore vedrebbe un numero che non ha scritto. A dire la cifra
    # e' il 400 del server, che il cassetto rende dentro di se'.
    _sl = mini[mini.index("function sogliaLibera("):
               mini.index("function sogliaMancante(")]
    for vietato in ("Math.max", "Math.min", "min_eur", "min_valore_eur"):
        prova(f"il campo libero non lima: niente {vietato}", False,
              vietato in _sl)
    prova("...e scrive INTERI (la colonna del server e' un INTEGER)",
          True, "parseInt(" in _sl and "parseFloat(" not in _sl)
    # LE CHIAVI VECCHIE, che portavano SATS, non si leggono piu' dal
    # body: scriverle in una colonna che ora parla euro farebbe di
    # «50.000» una soglia da cinquantamila euro, cioe' una promessa
    # spenta in silenzio. Il client vecchio prende un 400 onesto.
    corpo_ep = src[src.index("async def imposta_sped_gratis("):
                   src.index("async def imposta_ferie(")]
    prova("l'endpoint legge soglia_eur e non la chiave in sats", True,
          'd.get("soglia_eur")' in corpo_ep
          and 'd.get("soglia")' not in corpo_ep)


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
        (_, _, _, p_sats, p_eur, p_dich, _, _, _, _) = \
            gira(amb["consegna_da_payload"](d, valuta))
        return p_sats, p_eur, p_dich

    def supplemento(d, valuta="sats"):
        (_, _, _, _, _, _, e_sats, e_eur, _, _) = \
            gira(amb["consegna_da_payload"](d, valuta))
        return e_sats, e_eur

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
    # IL SUPPLEMENTO (ago 2026): stesso aiutante, ma NIENTE
    # dichiarazione — «0» e «assente» sono la stessa cosa, ed e' la
    # differenza dalla tariffa punto qui sopra. Chi lo svuota in
    # modifica manda 0, e 0 vuol dire «nessun supplemento».
    prova("supplemento assente: zero", (0, 0.0),
          supplemento({"consegna": "spedizione"}))
    prova("supplemento in sats", (300, 0.0),
          supplemento({"consegna": "spedizione",
                       "spedizione_extra_sats": "300"}))
    prova("supplemento a zero esplicito: zero, come l'assenza", (0, 0.0),
          supplemento({"consegna": "spedizione",
                       "spedizione_extra_sats": 0}))
    prova("listino sats, supplemento in euro: resta ANCORATO", (0, 1.5),
          supplemento({"consegna": "spedizione",
                       "spedizione_extra_eur": "1.5"}))
    prova("listino EUR: euro + equivalente al cambio", (1_500, 1.5),
          supplemento({"consegna": "spedizione",
                       "spedizione_extra_eur": "1.5"}, "eur"))
    prova("col ritiro il supplemento si azzera", (0, 0.0),
          supplemento({"consegna": "ritiro",
                       "spedizione_extra_sats": "300"}))
    prova("col codice online idem", (0, 0.0),
          supplemento({"consegna": "digitale",
                       "spedizione_extra_sats": "300"}))

    # la simmetria con la tariffa casa: stesso aiutante, stessi numeri
    def entrambe(d, valuta="sats"):
        (_, s_sats, s_eur, p_sats, p_eur, _, _, _, _, _) = \
            gira(amb["consegna_da_payload"](d, valuta))
        return (s_sats, s_eur) == (p_sats, p_eur)
    prova("stessa cifra nei due campi = stessa lettura", True,
          entrambe({"consegna": "spedizione", "spedizione_sats": "250",
                    "spedizione_punto_sats": "250"}))


# ====================================================================
def prove_reti_corriere():
    """CHI SPEDISCE DICHIARA, CHI COMPRA SCEGLIE (ago 2026).

    Il caso da cui nasce: il compratore sceglie un locker InPost, il
    venditore spedisce con Poste, il punto piu' vicino di quella rete
    e' a 50 km e l'affare si blocca coi sats in cassaforte.

    Le tre cose che questa famiglia difende, e sono quelle che un
    riordino toglierebbe per prime:
    · il RIPIEGO sulla colonna singolare — e' quel che fa vivere il
      dato di ieri prima che il backfill sia girato;
    · le DUE COLONNE scritte INSIEME, in un UPDATE solo;
    · la rete validata contro le reti DI QUEL VENDITORE e non contro
      il catalogo, che e' la riga in cui il cantiere sta tutto."""
    print("\n[le reti del corriere]")
    src = _SORGENTE
    mini = open("miniapp.html", encoding="utf-8").read()

    # L'AMBIENTE: le tre pure vogliono il catalogo e HTTPException —
    # chi estrae una funzione ne eredita le dipendenze (la lezione di
    # _fmt_sats). Il catalogo si legge dal SORGENTE e non si ricopia,
    # o la prova certificherebbe una lista che il server non ha.
    class _HTTP(Exception):
        def __init__(self, codice, detail=""):
            self.status_code, self.detail = codice, detail
            super().__init__(detail)
    amb = {"HTTPException": _HTTP}
    i = src.index('SPEDIZIONIERI = ("')
    exec(src[i:src.index("\n", i)], amb)
    for nome in ("_reti_serializza", "reti_venditore", "rete_da_payload"):
        exec(pezzo(nome), amb)
    reti_venditore = amb["reti_venditore"]
    _reti_serializza = amb["_reti_serializza"]
    rete_da_payload = amb["rete_da_payload"]
    prova("il catalogo di prova e' quello VERO del server",
          ("InPost", "Poste Italiane", "Altro"), amb["SPEDIZIONIERI"])

    # --- il giudice puro delle reti ---------------------------------
    prova("le reti si leggono dai pipe", ["InPost", "Poste Italiane"],
          reti_venditore("|InPost|Poste Italiane|", ""))
    prova("...nell'ordine del CATALOGO, non in quello scritto",
          ["InPost", "Poste Italiane"],
          reti_venditore("|Poste Italiane|InPost|", ""))
    prova("colonna vuota: si ripiega sulla singolare (il dato di ieri)",
          ["InPost"], reti_venditore("", "InPost"))
    prova("...ma la nuova VINCE quando c'e'", ["Poste Italiane"],
          reti_venditore("|Poste Italiane|", "InPost"))
    prova("niente da nessuna parte = nessuna rete", [],
          reti_venditore("", ""))
    prova("una rete fuori catalogo si butta: non la sappiamo mappare",
          [], reti_venditore("|Bartolini|", ""))
    prova("il ripiego non inventa nulla da un valore storto", [],
          reti_venditore("", "Bartolini"))

    # --- la serializzazione ----------------------------------------
    prova("in colonna vanno i pipe ai bordi", "|InPost|",
          _reti_serializza(["InPost"]))
    prova("...nell'ordine del catalogo", "|InPost|Poste Italiane|",
          _reti_serializza(["Poste Italiane", "InPost"]))
    prova("...senza doppioni", "|InPost|",
          _reti_serializza(["InPost", "InPost"]))
    prova("...e senza le voci fuori catalogo", "|InPost|",
          _reti_serializza(["InPost", "Bartolini"]))
    prova("lista vuota = '' = non dichiarato", "",
          _reti_serializza([]))

    # --- LA DECISIONE: chi valida la rete scelta --------------------
    # e' la riga che chiude il caso del cantiere: chi dichiara InPost
    # e Poste non deve poter ricevere un ordine per una terza rete
    def rifiuta(grezza, reti):
        try:
            rete_da_payload(grezza, reti)
            return False
        except _HTTP:
            return True

    due = ["InPost", "Poste Italiane"]
    prova("due reti: la scelta buona passa", "InPost",
          rete_da_payload("InPost", due))
    prova("...senza scelta si rifiuta", True, rifiuta("", due))
    prova("...e una rete che il venditore NON ha si rifiuta", True,
          rifiuta("Altro", due))
    prova("una rete sola: si fissa, anche se il client tace", "InPost",
          rete_da_payload("", ["InPost"]))
    prova("...e il client non puo' contraddirla", "InPost",
          rete_da_payload("Poste Italiane", ["InPost"]))
    prova("nessuna rete: '' e nessun rifiuto (il mondo di ieri)", "",
          rete_da_payload("", []))
    prova("...nemmeno se il client manda qualcosa", "",
          rete_da_payload("InPost", []))
    corpo_rete = codice(pezzo("rete_da_payload").split('"""')[-1])
    prova("la rete si valida contro le reti DEL VENDITORE", True,
          "scelta not in reti" in corpo_rete)
    prova("...e MAI contro il catalogo intero", False,
          "SPEDIZIONIERI" in corpo_rete)
    prova("una rete sola si fissa alla nascita, senza chiedere", True,
          "len(reti) == 1" in corpo_rete)
    prova("nessuna rete = nessuna scelta (il mondo di ieri)", True,
          "if not reti:" in corpo_rete)

    # --- le due colonne, un UPDATE solo ----------------------------
    corpo_ep = codice(pezzo("scegli_spedizioniere").split('"""')[-1])
    prova("il cassetto scrive le DUE colonne insieme", 1,
          corpo_ep.count("UPDATE utenti SET spedizionieri=?, "
                         "spedizioniere=?"))
    prova("...e la singolare tiene la PRIMA voce", True,
          'reti[0] if reti else ""' in corpo_ep)
    prova("la chiave di IERI si accetta ancora (stesso significato)",
          True, 'd.get("spedizioniere")' in corpo_ep)

    # --- il backfill ------------------------------------------------
    corpo_bf = codice(pezzo("riallinea_spedizionieri").split('"""')[-1])
    prova("il backfill tocca solo le righe ancora vuote (idempotente)",
          True, "spedizionieri = ''" in corpo_bf)
    prova("...e solo chi una rete l'aveva davvero", True,
          "spedizioniere <> ''" in corpo_bf)
    # LA RIGA INTERA e non la stringa: un «pass  #
    # riallinea_spedizionieri(con)» lascerebbe la parola nel file col
    # backfill mai chiamato — e' la lezione del reaper, che una
    # sentinella si scrive rompendo il codice e non rileggendola
    # (questa mutazione e' sopravvissuta al primo giro di tortura)
    prova("...e gira all'avvio, come RIGA e non come parola", True,
          bool(re.search(r"^\s*riallinea_spedizionieri\(con\)\s*$",
                         src, re.M)))

    # --- il client ---------------------------------------------------
    prova("il client riceve le SUE reti da una chiave nuova", True,
          "me.spedizionieri_miei" in mini)
    prova("...e il catalogo resta dov'era (il client in cache lo legge)",
          True, 'profilo["spedizionieri"] = list(SPEDIZIONIERI)' in src)
    prova("il giudice del «manca il corriere» e' UNO", 1,
          mini.count("function reteMancante"))
    prova("...e lo chiamano le DUE strade che pagano", 2,
          mini.count("reteMancante(") - mini.count("function reteMancante("))
    prova("...e vale solo da DUE reti in su", True,
          "reti.length >= 2 && !d.rete" in mini)
    prova("la rete viaggia nel body solo se scelta", True,
          "out.rete_punto = acqDati.rete" in mini)

    # --- il foglio dell'invito --------------------------------------
    inv = pezzo_js(mini, "function apriInvitoCorrieri(){", "\n}")
    prova("il contatore dell'invito sale all'APERTURA del foglio", True,
          "myInvitoCorrieri++" in inv and "/me/invito-corrieri" in inv)
    prova("...e il flag di sessione spezza la ricorsione di publish",
          True, "corrieriChiesto = true" in inv)
    serve = pezzo_js(mini, "function serveInvitoCorrieri(){", "\n}")
    prova("l'invito guarda il TETTO", True,
          "myInvitoCorrieri < invitoCorrieriMax" in serve)
    prova("...e chi ha gia' dichiarato non lo vede mai", True,
          "!mieRetiSped.length" in serve)
    prova("...ne' chi non spedisce: ritiro e codice online fuori "
          "per costruzione", True,
          "el('sellConsSped')?.checked" in serve)
    prova("...ne' un'asta", True, "!astaAccesa()" in serve)
    prova("il tetto arriva dal server, mai un numero nel client", True,
          "me.invito_corrieri_max" in mini)
    # L'INVITO NON BLOCCA: e' la meta' della decisione di Andrea, e la
    # prova e' che TUTTI E DUE i bottoni richiamino publish()
    prova("«Pubblica lo stesso» pubblica davvero", True,
          "publish();" in pezzo_js(mini, "function pubblicaLoStesso(){",
                                   "\n}"))
    prova("...e anche «Salva e pubblica» finisce in publish()", True,
          "publish();" in pezzo_js(mini,
              "async function salvaCorrieriEPubblica(){", "\n}"))
    prova("il foglio si registra in closeSheet (o resta il velo)", True,
          "el('corrieriSheet').classList.remove('open')" in
          pezzo_js(mini, "function closeSheet(){", "\n}"))
    # l'aggancio in publish: DOPO le validazioni e PRIMA dell'overlay
    pub = pezzo_js(mini, "async function publish(){", "\n}")
    prova("l'invito sta PRIMA dello scudo anti-doppione", True,
          pub.index("serveInvitoCorrieri()")
          < pub.index("bottoneInAttesa("))
    prova("...e DOPO l'ultima validazione (la zona)", True,
          pub.index("controllaZona()") < pub.index("serveInvitoCorrieri()"))

    # --- la riga del form -------------------------------------------
    prova("la riga del form guarda le RETI, non piu' la stringa", True,
          "&& !mieRetiSped.length) ? '' : 'none'" in mini)
    prova("...e resta senza dismiss (e' derivata dai dati veri)", False,
          "dismettiHint('spedizioniere'" in mini)

    # ================================================================
    # LA SECONDA META': LOCKER O PUNTO COL BANCO
    # Un locker e una tabaccheria non sono la stessa consegna — chi
    # vende compra un'ETICHETTA DIVERSA, ed e' il costo da cui nasce
    # tutto il cantiere. La rete da sola non basta: InPost e Poste
    # hanno tutt'e due sia i locker sia i negozi convenzionati.
    print("  — il tipo di punto —")
    i = src.index("TIPI_PUNTO = ((")
    exec(src[i:src.index("\nID_TIPI_PUNTO", i)], amb)
    exec(src[src.index("ID_TIPI_PUNTO = "):
             src.index("\n", src.index("ID_TIPI_PUNTO = "))], amb)
    exec(pezzo("tipo_punto_da_payload"), amb)
    tipo_da_payload = amb["tipo_punto_da_payload"]

    prova("i due tipi, cogli id per sempre e le etichette ritoccabili",
          [("locker", "Locker automatico", "Locker"),
           ("banco", "Punto di ritiro", "Punto")],
          list(amb["TIPI_PUNTO"]))
    prova("il tipo buono passa", "locker", tipo_da_payload("locker"))
    prova("...e si normalizza", "banco", tipo_da_payload(" BANCO "))
    prova("il vuoto passa: il 400 vive nel CLIENT (la tolleranza "
          "verso il client di ieri, come per la rete)", "",
          tipo_da_payload(""))

    def rifiuta_tipo(v):
        try:
            tipo_da_payload(v)
            return False
        except _HTTP:
            return True

    prova("un tipo inventato si rifiuta", True, rifiuta_tipo("locker2"))
    # NIENTE DEFAULT, ed e' la riga da non ammorbidire: preselezionare
    # «locker» perche' e' il caso comune fa comprare l'etichetta
    # sbagliata a chi sceglie una tabaccheria senza toccare niente
    corpo_tipo = codice(pezzo("tipo_punto_da_payload").split('"""')[-1])
    prova("nessun default nel giudice: il vuoto resta vuoto", False,
          '"locker"' in corpo_tipo.replace('ID_TIPI_PUNTO', ''))
    # E NON SI DEDUCE DAL TESTO DEL PUNTO, e la prova piu' forte non e'
    # cercare «tabaccheria» nel sorgente (che sta nei commenti, dove
    # spiega proprio questa regola): e' che il giudice NON RICEVE il
    # punto — non puo' dedurlo nemmeno volendo
    firma = re.search(r"def tipo_punto_da_payload\(([^)]*)\)", src).group(1)
    prova("il giudice del tipo non vede nemmeno il testo del punto",
          ["grezzo"],
          [p.split(":")[0].strip() for p in firma.split(",")])

    # il tipo si scrive in colonna nei due rami d'acquisto
    prova("il tipo si legge dal payload nei due rami d'acquisto",
          [1, 1],
          [codice(pezzo(f)).count(
              'tipo = tipo_punto_da_payload(d.get("tipo_punto"))')
           for f in ("compra", "_compra_set")])
    prova("...e finisce in colonna nei due INSERT", 2,
          codice(src).count("tipo_punto,"))
    # la correzione dentro l'ordine, che e' la rete di sicurezza degli
    # ordini nati senza: chiave ASSENTE = si CONSERVA (patto dello stock)
    corpo_pr2 = codice(pezzo("indica_punto_ritiro").split('"""')[-1])
    prova("nell'ordine il tipo si corregge col punto", True,
          "tipo_punto=?" in corpo_pr2)
    prova("...e la chiave assente CONSERVA quel che c'era", True,
          'if "tipo_punto" in d else (o["tipo_punto"] or "")' in corpo_pr2)

    # --- il client ---------------------------------------------------
    prova("il catalogo client e' il gemello del server (id per id)",
          [t[0] for t in amb["TIPI_PUNTO"]],
          re.findall(r"\{id:'(\w+)'", mini[mini.index("const TIPI_PUNTO"):
                                           mini.index("function nomePunto")]))
    prova("...e le etichette combaciano", True,
          all(t[1] in mini and t[2] in mini for t in amb["TIPI_PUNTO"]))
    prova("il nome che il venditore legge ha un giudice UNO", 1,
          mini.count("function nomePunto"))
    prova("...e lo chiamano le superfici che lo scrivono", 2,
          mini.count("nomePunto(") - mini.count("function nomePunto("))
    # E SI FA GIRARE, non si guarda soltanto: le sentinelle qui sopra
    # dicono che il giudice ESISTE ed e' uno, mai che risponda giusto
    # — la mutazione che gli toglie il tipo e lascia la sola rete le
    # passava tutte (trovata dalla tortura, ed e' la sesta volta che
    # una prova sulla FORMA certifica un ramo disonesto).
    import json as _js, shutil as _sh2, subprocess as _sp2, tempfile as _tf2
    _node = _sh2.which("node")
    if not _node:
        salta("nomePunto risponde giusto", "node non installato")
    else:
        _cat = mini[mini.index("const TIPI_PUNTO"):
                    mini.index("function nomePunto")]
        _fn = pezzo_js(mini, "function nomePunto(tipo, rete){", "\n}") + "\n}"
        _casi = [("locker", "InPost", "Locker InPost"),
                 ("banco", "InPost", "Punto InPost"),
                 ("locker", "Poste Italiane", "Locker Poste Italiane"),
                 ("locker", "", "Locker"),
                 ("", "InPost", "InPost"),
                 ("", "", "Punto di ritiro")]
        _prog = (_cat + _fn + "\nconst esiti = "
                 + _js.dumps([[t, r] for t, r, _a in _casi])
                 + ".map(([t,r]) => nomePunto(t,r));"
                 "console.log(JSON.stringify(esiti));")
        _f = _tf2.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8")
        _f.write(_prog)
        _f.close()
        _r = _sp2.run([_node, _f.name], capture_output=True, text=True,
                      timeout=60, encoding="utf-8")
        os.unlink(_f.name)
        prova("nomePunto risponde giusto sui sei casi",
              [a for _t, _r2, a in _casi],
              _js.loads(_r.stdout.strip()) if _r.returncode == 0
              else f"ERRORE: {_r.stderr[:120]}")
    prova("il giudice del «manca il tipo» e' UNO", 1,
          mini.count("function tipoPuntoMancante"))
    prova("...e lo chiamano le DUE strade che pagano", 2,
          mini.count("tipoPuntoMancante(")
          - mini.count("function tipoPuntoMancante("))
    prova("...e vale SEMPRE sulla via punto (non dipende dalle reti)",
          True, "d?.via === 'punto' && !d.tipoPunto" in mini)
    prova("il tipo viaggia sempre nel body sulla via punto", True,
          "out.tipo_punto = acqDati.tipoPunto || ''" in mini)
    prova("la scelta e' DUE FILE e non una matrice rete×tipo", True,
          "Che tipo di punto?" in mini and "Con quale corriere?" in mini)
    # e le pillole del tipo portano la SOLA etichetta del catalogo: se
    # ci finisse dentro il nome della rete saremmo tornati alla
    # matrice — tre righe a 320px invece di due, e sei voci alla prima
    # rete aggiunta. (Si guarda la fabbrica della pillola, non il file
    # intero: «Locker InPost» vive legittimamente nel placeholder del
    # campo e nei commenti che spiegano questa scelta.)
    fabbrica = pezzo_js(mini, "  const tipoPill = (t) =>", "`;")
    prova("...e la pillola del tipo non nomina mai la rete", True,
          "esc(t.nome)" in fabbrica and "rete" not in fabbrica)


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
              "await " in codice(src[i:j]))

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

    # 5. L'asta resta fuori dal perimetro del PUNTO: il varco del
    #    vincitore non scrive ne' la via ne' il punto.
    #    ⚠️ La prova cercava la PAROLA «punto» nel corpo, e bastava un
    #    commento a farla rossa: dall'ago 2026 (l'indirizzo di casa,
    #    che invece il varco dichiara) guarda i due NOMI VERI delle
    #    colonne. Piu' stretta, non piu' larga: e' la scrittura che
    #    non deve esserci, non la parola.
    corpo = pezzo("scegli_consegna_ordine").split('"""')[-1]
    prova("scegli_consegna_ordine: niente via_punto", False,
          "via_punto" in corpo)
    prova("scegli_consegna_ordine: niente punto_ritiro", False,
          "punto_ritiro" in corpo)

    # 5bis. LA REGOLA ROVESCIATA (secondo giro, decisione di Andrea):
    #    la via punto si offre SEMPRE dove c'e' la spedizione — il
    #    gate sullo spedizioniere e' durato un giro e non deve
    #    tornare di soppiatto (meglio l'accordo in chat che la porta
    #    chiusa). Ne' il 400 di ieri, ne' un filtro nel preventivo.
    prova("il 400 «non spedisce ai punti» non esiste piu'", False,
          "non spedisce ai punti" in src)
    prova("_strade_preventivo non filtra piu' sullo spedizioniere",
          False, "not spedizioniere" in pezzo("_strade_preventivo"))

    # 5ter. IL QUARTO GIRO (decisione di Andrea che ROVESCIA il terzo):
    #    la scelta del punto torna SEMPRE prima di «Paga», come su
    #    Subito e Vinted — il campo c'e' anche senza rete dichiarata,
    #    con tutte e due le mappe e la riga onesta. LA REGOLA VIVE NEL
    #    CLIENT: il server esige il punto solo con la rete dichiarata,
    #    ed e' TOLLERANZA per il client di ieri (che senza rete non ha
    #    il campo: un 400 senza campo sarebbe un vicolo cieco), non la
    #    regola del prodotto. Il residuo — ordini nati senza punto —
    #    lo coprono il campo dell'ordine (la rete di sicurezza: il
    #    punto si corregge finche' il venditore non spedisce) e il
    #    gate di segna_spedito, che non puo' riscattare dopo: il vuoto
    #    si rifiuta, un punto scritto si corregge e non si svuota mai.
    prova("server: il 400 del punto resta sul solo ramo con rete (x2, "
          "tolleranza per il client di ieri)", 2,
          src.count("if reti and not punto:"))
    corpo_sped = pezzo("segna_spedito").split('"""')[-1]
    prova("segna_spedito: bloccato sulla via punto senza punto", True,
          'o["via_punto"] and not o["punto_ritiro"]' in corpo_sped)
    corpo_pr = pezzo("indica_punto_ritiro").split('"""')[-1]
    prova("il campo dell'ordine e' del COMPRATORE, su 'locked'", True,
          "compratore_id" in corpo_pr and "'locked'" in corpo_pr)
    prova("...esige la via punto", True, 'o["via_punto"]' in corpo_pr)
    prova("...rifiuta il vuoto: il punto si corregge, non si svuota",
          True, "if not punto:" in corpo_pr)
    prova("...e la notifica al venditore e' STATICA (mai il testo)",
          False, "{punto" in corpo_pr)
    mini3 = open("miniapp.html", encoding="utf-8").read()
    prova("client: il campo del punto non gatea piu' sulla rete",
          False, "campoPunto = !p.spedizioniere" in mini3)
    prova("client: le due guardie del punto non guardano la rete", 0,
          mini3.count("spedizioniere && !"))
    prova("client: la riga «lo indicherai dopo l'acquisto» e' morta "
          "col quarto giro", False, "lo indicherai dopo l'acquisto" in mini3)
    prova("client: la riga onesta senza rete esiste", True,
          "senza sapere con che rete" in mini3)
    prova("client: il campo dentro l'ordine esiste", True,
          "salvaPuntoRitiro" in mini3 and "puntoRitiroInp" in mini3)

    # 5quater. IL QUINTO GIRO (ago 2026, col punto diventato il
    #    DEFAULT della via): il campo del punto non sta piu' aperto in
    #    pagina — lo espande il bottone «📍 Indica il punto di
    #    ritiro», cosi' la pagina apre su un conto da leggere e non su
    #    un modulo da compilare (l'argomento contro il punto come
    #    default). Lo stato vive in acqDati e mai nel DOM (il corpo si
    #    ridisegna a ogni ±); col punto scritto la riga compatta lo
    #    MOSTRA con «Cambia» — mai ricominciare da capo — e le due
    #    guardie di «Paga»/⚡ APRONO il cassetto prima del fuoco: mai
    #    il fuoco su un campo nascosto.
    prova("quinto giro: il bottone del punto esiste", True,
          '>Indica il punto di ritiro</button>' in mini3)
    # NUDO, senza 📍 (ago 2026, decisione di Andrea): il riquadro che
    # lo ospita ha gia' il locker della via, e due icone nello stesso
    # riquadro sono una di troppo — vale per il bottone E per la riga
    # compatta del punto scritto
    prova("...nudo: il riquadro ha gia' il locker della via", False,
          "📍 Indica il punto di ritiro" in mini3)
    prova("...e anche la riga compatta ha perso il 📍", False,
          '>📍 <span class="punto-testo">' in mini3)
    prova("...lo stato del cassetto nasce in acqDati (due costruttori)",
          2, mini3.count("punto:'', puntoAperto:false"))
    prova("...il campo riapre PRECOMPILATO, mai ricominciare da capo",
          True, 'value="${esc(d.punto)}"' in mini3)
    # dal cantiere delle reti la riga compatta porta anche il nome del
    # punto (tipo + rete, dal giudice unico): il punto resta SCAPPATO
    # e il Cambia al suo posto — cambia il prefisso, non la regola
    prova("...la riga compatta mostra il punto SCAPPATO, col Cambia",
          True,
          "esc(nomePunto(d.tipoPunto, d.rete))+' — '" in mini3
          and '${esc(puntoScritto)}</span>' in mini3)
    prova("...e il nome del punto passa anch'esso da esc()",
          True, "esc(nomePunto(d.tipoPunto, d.rete))" in mini3)
    prova("...e a cedere coi puntini e' l'indirizzo, mai il Cambia",
          True, ".punto-testo{flex:1 1 auto;min-width:0;" in mini3)
    # SEI ora: ogni strada che paga fa TRE domande in fila — il
    # corriere, che tipo di punto, e dove — e tutte e sei aprono il
    # cassetto invece di mettere il fuoco su un campo fuori pagina
    prova("le guardie del cassetto lo APRONO (x6: due strade, "
          "tre domande)", 6, mini3.count("apriPuntoAcquisto();"))
    prova("...col toast identico nelle due copie", 2,
          mini3.count("Indica il punto di ritiro: al venditore serve "
                      "per spedire"))
    prova("...e nessuna mette piu' il fuoco su un campo nascosto",
          False, "el('acqPunto')?.focus(); return;" in mini3)
    _cta = pezzo_js(mini3, "function ctaAcquisto(){", "\n}")
    prova("...in ctaAcquisto l'apertura sta PRIMA del toast", True,
          _cta.index("apriPuntoAcquisto()") < _cta.index("toast("))
    _nwc = pezzo_js(mini3, "function compraSubito(){", "\n}")
    prova("...e in compraSubito idem", True,
          _nwc.index("apriPuntoAcquisto()")
          < _nwc.index("Indica il punto di ritiro"))

    # 5quater-bis. IL SESTO GIRO — IL CAMPO ARRIVA DOPO LE SCELTE (ago
    #    2026, decisione di Andrea): prima il corriere, poi locker o
    #    banco, e SOLO ALLORA il campo dove si scrive dov'e' il punto.
    #    Non e' un vezzo d'interfaccia, e' l'ordine in cui
    #    l'informazione esiste — il punto si trova sulla MAPPA, che
    #    dipende dalla rete — e un campo aperto prima invita a
    #    scrivere un indirizzo che poi va ripensato.
    #    L'ECCEZIONE E' DICHIARATA: senza NESSUN corriere dichiarato
    #    il campo resta disponibile SUBITO, com'era, perche' li' non
    #    c'e' nessuna cascata da rispettare (la mappa non si sa quale
    #    sia e si mostrano tutte). Il tipo resta comunque obbligatorio
    #    e a chiederlo e' la guardia di «Paga», le cui pillole sono in
    #    pagina — ed e' l'ORDINE delle tre guardie (rete → tipo →
    #    punto, sorvegliato qui sopra) a garantire che quando scatta
    #    la terza il campo ci sia davvero: nessun toast manda mai a un
    #    campo che non esiste.
    prova("sesto giro: il gate delle scelte esiste", True,
          "const scelteFatte = (!sceglieRete || !!d.rete) && !!d.tipo"
          in mini3)
    prova("...e il campo si disegna solo a scelte fatte (o senza reti)",
          True,
          "(!reti.length || scelteFatte) ? campoDove : ''" in mini3)
    prova("...il segnaposto non ripete il tipo: li' va solo il dove",
          False, "Locker — Via Roma" in mini3)
    prova("...e la riga «scegli prima il corriere» e' morta con lui: "
          "quel caso non ha piu' un campo da spiegare",
          False, "la mappa dei punti è diversa per ognuno" in mini3)
    # E SI FA GIRARE, che una sentinella sulla forma dice com'e'
    # scritto il ramo e mai cosa risponde — la lezione ormai settima.
    # Gli otto casi sono la matrice intera (due reti / una / nessuna,
    # per rete scelta e tipo scelto): la mutazione che toglie
    # l'eccezione dei venditori senza corriere fa rosso il settimo, e
    # quella che si accontenta della rete fa rosso il secondo.
    import json as _js4, shutil as _sh4, subprocess as _sp4, tempfile as _tf4
    _node4 = _sh4.which("node")
    _casi4 = [
        (["InPost", "Poste"], {"rete": "",       "tipoPunto": ""},       False),
        (["InPost", "Poste"], {"rete": "InPost", "tipoPunto": ""},       False),
        (["InPost", "Poste"], {"rete": "",       "tipoPunto": "locker"}, False),
        (["InPost", "Poste"], {"rete": "InPost", "tipoPunto": "locker"}, True),
        (["InPost"],          {"rete": "",       "tipoPunto": ""},       False),
        (["InPost"],          {"rete": "",       "tipoPunto": "banco"},  True),
        ([],                  {"rete": "",       "tipoPunto": ""},       True),
        ([],                  {"rete": "",       "tipoPunto": "locker"}, True),
    ]
    if not _node4:
        salta("il gate del campo risponde giusto", "node non installato")
    else:
        try:
            _sr4 = mini3[mini3.index("const sceglieRete ="):]
            _sr4 = _sr4[:_sr4.index("\n")]
            _sf4 = mini3[mini3.index("const scelteFatte ="):]
            _sf4 = _sf4[:_sf4.index("\n")]
            _cond4 = mini3[mini3.index("${(!reti.length") + 2:
                           mini3.index(" ? campoDove")]
            _prog4 = ("function campoCe(reti, d){" + _sr4 + _sf4
                      + " return !!" + _cond4 + ";}\n"
                      "const casi = "
                      + _js4.dumps([[r, d] for r, d, _a in _casi4])
                      + ";console.log(JSON.stringify("
                      "casi.map(([r,d]) => campoCe(r,d))));")
            _f4 = _tf4.NamedTemporaryFile("w", suffix=".js", delete=False,
                                          encoding="utf-8")
            _f4.write(_prog4)
            _f4.close()
            _r4 = _sp4.run([_node4, _f4.name], capture_output=True,
                           text=True, timeout=60, encoding="utf-8")
            os.unlink(_f4.name)
            _esiti4 = (_js4.loads(_r4.stdout.strip()) if _r4.returncode == 0
                       else f"ERRORE: {_r4.stderr[:120]}")
        except ValueError as _e4:
            _esiti4 = f"ANCORA PERSA: {_e4}"
        prova("...e il gate risponde giusto sugli otto casi",
              [a for _r5, _d5, a in _casi4], _esiti4)

    # 5quater-ter. LE DUE RIGHE TOLTE DALLA PAGINA (ago 2026,
    #    decisioni di Andrea). La prima nominava il corriere del
    #    venditore sotto il riquadro della via: ormai quel nome sta
    #    DENTRO il riquadro (le pillole della rete, o la label del
    #    campo con una rete sola), e ripeterlo era la stessa cosa
    #    detta due volte a due dita di distanza. La seconda spiegava
    #    il ≈ della conversione: era la didascalia di un segno che si
    #    dice da se'.
    #    ⚠️ Le due formule non si citano nei commenti del client —
    #    queste sentinelle leggono anche quelli, ed e' il modo in cui
    #    una prova diventa vacua (o rossa per colpa della prosa).
    prova("la riga che nominava il corriere e' morta", False,
          "Spedisce con" in mini3)
    prova("...e quella che spiegava la conversione idem", False,
          "convertito ora al cambio" in mini3
          or "si fissa con la invoice" in mini3)
    # IL ≈ RESTA, ed e' la meta' che conta: a sparire e' la
    # didascalia, non il segno — le cifre convertite lo portano
    # ancora, dal giudice unico.
    prova("...ma il ≈ delle cifre resta vivo", True,
          "(p.stima || (stradaSel && stradaSel.stima)) ? '≈ ' : ''"
          in mini3)
    # e la riga onesta di chi NON ha dichiarato un corriere non e' fra
    # quelle tolte: quella dice una cosa che nessun altro dice
    prova("...mentre la riga onesta senza corriere resta", True,
          "senza sapere con che rete" in mini3)

    # 5quinquies. LE CIFRE DELLE VIE SOLO QUANDO DICONO QUALCOSA e IL
    #    CASSETTO DENTRO IL RIQUADRO (ago 2026, decisioni di Andrea).
    #    Le cifre di casa/punto compaiono solo quando DIVERGONO — il
    #    giudice e' uno (costiVieUguali) e confronta il costo FINALE
    #    nella stessa unita' NATIVA: mai attraverso una conversione
    #    (un'uguaglianza al cambio di adesso e' di un istante, la
    #    invoice riconverte), fallback_casa = identita' e non
    #    confronto, cambio muto = non confrontabile e la via viva
    #    mostra la sua.
    prova("il giudice delle cifre delle vie e' UNO", 1,
          mini3.count("function costiVieUguali"))
    prova("...e le cifre di casa/punto ci passano", True,
          "&& !cifreMute" in mini3)
    prova("...fallback_casa e' un'identita', non un confronto", True,
          "if (p.fallback_casa) return true;" in mini3)
    prova("...mai «uguali» attraverso una conversione", True,
          "if (cE>0 && pE>0) return cE === pE;" in mini3
          and "!c.stima && !p.stima" in mini3)
    prova("...e a cambio muto non si confronta niente", True,
          "c.cambio_assente || p.cambio_assente" in mini3)
    #    Il cassetto del punto vive DENTRO il riquadro della via punto
    #    e si disegna solo a via selezionata; la radio che lo ospita
    #    e' un DIV role="radio" (HTML vieta interattivi annidati, la
    #    lezione dello stepper dentro Acquista) e i tocchi restano
    #    separati per propagazione: il cassetto la ferma, o un click
    #    nell'input rifarebbe il render sotto le dita; la tastiera ha
    #    la guardia event.target===this.
    # (ago 2026: le vie col cassetto sono diventate DUE — il punto e
    #  la casa, che ospita l'indirizzo — quindi il ramo e' condiviso e
    #  ognuna sceglie il suo. La prova resta la stessa: il cassetto si
    #  disegna SOLO dentro la radio selezionata.)
    prova("il cassetto del punto vive dentro la radio della via", True,
          "cassettoPunto : cassettoIndirizzo" in mini3
          and "${s.via===d.via ? cass : ''}" in mini3)
    prova("...la radio ospite e' un DIV, mai un button annidato", True,
          '<div role="radio" tabindex="0"' in mini3)
    _i_cass = mini3.index('id="acqPuntoCampo"')
    prova("...e il cassetto ferma la propagazione del tocco", True,
          "event.stopPropagation()" in mini3[_i_cass:_i_cass + 120])
    # (ancorata al frammento dell'onkeydown: «event.target===this» nudo
    # vive anche altrove e la sentinella sarebbe vacua — la lezione
    # della tortura)
    prova("...con la guardia gemella sulla tastiera", True,
          'onkeydown="if(event.target===this' in mini3)
    #    La via punto parla col LOCKER e si chiama «Spedizione a un
    #    locker/punto di ritiro» (13 ago 2026, secondo giro: «locker»
    #    secco era piu' stretto del vero — con Poste la rete e' in gran
    #    parte banchi — e i MARCHI sono stati scartati, ogni corriere
    #    ha i suoi). SVG a currentColor, e il wrapper <span> tiene
    #    icona e testo in riga dentro .via-nome, che e' un flex in
    #    COLONNA — chi lo toglie mette il disegno SOPRA il testo.
    #    E DALL'AGO 2026 LA BARRA E' SPAZIATA e la coda cade («a un
    #    locker / punto»): la doppia formula resta — e' lei a dire che
    #    la via non e' solo l'armadietto — ma «di ritiro» non serve
    #    piu' qui, perche' il bottone che apre il campo lo dice a un
    #    centimetro («Indica il punto di ritiro»).
    #    L'ARTICOLO E' TORNATO col posto che «di ritiro» ha liberato
    #    (ago 2026): era caduto per la MISURA — chiedeva 276px dove a
    #    320 la colonna ne da' 258 — e rimisurato col font vero il nome
    #    ne chiede 230,8: una riga, con 27 di margine. Cosi' l'etichetta
    #    dice la stessa cosa della prosa delle notifiche, che «a un»
    #    l'ha sempre avuto — era l'ultima superficie fuori riga.
    prova("la via punto parla col locker, e si chiama con la doppia "
          "formula", True,
          "${ICO_LOCKER} Spedizione a un locker / punto</span>"
          in mini3)
    #    ...e l'articolo non si riperde: e' l'affermazione piu' forte
    #    delle due, perche' un «un» che cade in un riordino non rompe
    #    niente di visibile — la riga resta bella e dice un'altra cosa
    #    dalle otto prose. (Il letterale senza articolo non va scritto
    #    da nessun'altra parte del client, o questa diventa rossa.)
    prova("...con l'articolo, come le prose che nominano il posto", 0,
          mini3.count("Spedizione a locker"))
    #    la barra spaziata vale per l'ETICHETTA DELLA VIA e basta: le
    #    prose che nominano il posto fisico (l'ordine, il pannello del
    #    venditore, le notifiche del bot) tengono «locker/punto di
    #    ritiro» come sempre — li' non e' un'etichetta da leggere in
    #    fretta dentro una colonna stretta, e' una frase
    prova("...con gli spazi attorno alla barra", 0,
          pezzo_js(mini3, "const nomeVia = v =>", "\n").count("locker/punto"))
    prova("...il locker e' inchiostro che si accende (currentColor)",
          True, 'class="ico-locker"' in mini3
          and 'stroke="currentColor"' in mini3)
    prova("...e il nome vecchio della via non torna", 0,
          mini3.count("Spedizione a un punto di ritiro"))
    #    LA VESTE DELLA FILA (ago 2026, decisione di Andrea: la
    #    POSIZIONE resta sopra la Consegna — il modo «dentro la card»
    #    e' stato costruito, guardato e scartato). Dal 13 ago 2026 la
    #    veste e' CONDIVISA: la classe .fila-promesse la portano Paga,
    #    il carrello e «Altri oggetti» — un posto solo, e la quarta
    #    superficie di domani mette la classe e ha finito, invece di
    #    allungare sei liste di selettori.
    prova("la veste della fila e' una classe sola", True,
          ".fila-promesse{flex-direction:column" in mini3)
    prova("...e la portano tutte e tre le superfici", (True, True, True),
          ('`<div class="pills fila-promesse">${pillole}</div>`' in mini3,
           '<div id="paccoPromesse" class="fila-promesse">' in mini3,
           '<div class="pills altri-promo fila-promesse">' in mini3))
    #    display:block sulla pillola non e' ozioso: nel carrello vive
    #    dentro lo span-scatola e resterebbe INLINE — e width:100% su
    #    un inline non fa niente; in Paga e «Altri oggetti» era gia'
    #    blockificata dal flex.
    prova("...e la pillola della fila e' un blocco a tutta larghezza",
          True, ".fila-promesse .pill{display:block;width:100%" in mini3)
    #    LA BARRA DI RIEMPIMENTO delle promesse (13 ago 2026, decisione
    #    di Andrea sui prototipi: la saturazione del colore e' stata
    #    scartata — 67% e 73% indistinguibili, e il quasi-verde si
    #    leggeva come promessa gia' scattata). Il progresso viene dai
    #    numeri del SERVER nell'unita' della promessa; il TETTO A 99
    #    tiene la barra piena SOLO alla pill-trust — chi lo alza fa
    #    dire «scattata» a una promessa che non lo e'; e lo style c'e'
    #    SEMPRE, anche a 0%, o il background-image coprirebbe la
    #    pillola intera.
    prova("la barra delle promesse esiste, col tetto a 99", True,
          "const barraPromessa" in mini3 and "Math.min(99," in mini3)
    #    IL COLORE VIRA COL PROGRESSO (terzo giro, 13 ago 2026,
    #    chiesto da Andrea): la coppia --barra-da/--barra-a — verde
    #    SLAVATO che si accende salendo, mescolato dal progresso col
    #    color-mix nello style. MAI dal rosso (nell'app e' problema, e
    #    una promessa in corsa e' un invito) e mai dal grigio,
    #    prototipato e SCARTATO: la mescola di mezzo fa un olivastro
    #    spento e si perde la famiglia della fiducia. Ogni token ha i
    #    suoi due valori (chiaro/scuro): si abbassa la luce, non si
    #    cambia il segno.
    prova("...la tinta vira col progresso, dentro la famiglia", True,
          "color-mix(in srgb, var(--barra-a) ${p}%, var(--barra-da))"
          in mini3)
    prova("...e la coppia del viraggio ha i suoi due valori", True,
          mini3.count("--barra-da:") == 2
          and mini3.count("--barra-a:") == 2)
    #    Il fill vive su un ::before (quarto giro): larghezza in
    #    --barra-p e colore in --barra-c, perche' width e
    #    background-color si transizionano davvero e un gradiente no —
    #    e' cosi' che ANCHE il viraggio e' morbido. Il ripiego della
    #    custom property resta sul verde slavato.
    prova("...il fill e' un ::before con larghezza e colore", True,
          "width:var(--barra-p,0%)" in mini3
          and "background:var(--barra-c,var(--barra-da))" in mini3)
    prova("...che transiziona larghezza E colore insieme", True,
          "transition:width .35s ease,background-color .35s ease"
          in mini3)
    prova("...le QUATTRO pillole sotto soglia la portano (Paga e "
          "carrello, 13 ago 2026)", 4,
          mini3.count('class="pill pill-barra"'))
    prova("...e lo style del progresso c'e' sempre, anche a 0%", True,
          'style="--barra-p:${p}%;--barra-c:${c}"' in mini3)
    #    LA SCATTATA E' PIENA E ACCESA (quarto giro, visto da Andrea a
    #    schermo nei due temi: la barra si accendeva salendo e allo
    #    scatto la pillola tornava al tenue — il traguardo perdeva
    #    forza). Dal 13 ago 2026 vale ANCHE nel carrello, che corre la
    #    stessa barra (ROVESCIA il «solo in Paga» di mezza giornata
    #    prima: due traguardi diversi per la stessa promessa erano una
    #    divergenza senza motivo) — quindi la regola vive sulla BASE
    #    .pill.pill-trust, una volta sola, e il tenue di .trust-soft
    #    non lo veste piu' nessuno.
    prova("la scattata e' piena e ACCESA, con l'inchiostro",
          1, mini3.count("background:var(--barra-a);color:var(--ink)"))
    prova("...sulla base .pill.pill-trust, una regola sola", True,
          ".pill.pill-trust{border-color:var(--barra-a)" in mini3)
    prova("...e la conferma tenue non la veste piu' nessuno", False,
          ".pill.pill-trust{background:var(--trust-soft)" in mini3)
    #    LA CORSA MORBIDA (13 ago 2026, chiesta da Andrea): il «da» si
    #    RECUPERA dal computed — che a meta' corsa e' il valore
    #    INTERPOLATO, quindi i + veloci ritargetizzano e non si
    #    accodano mai — e il nodo nuovo nasce alla larghezza vecchia,
    #    reflow, bersaglio (il giro FLIP). Allo scatto la pill-trust
    #    corre nel SUO verde e a fine corsa il fondo e' quello di
    #    riposo della scattata: nessun secondo stato da mantenere.
    #    La partenza e' in DUE FOTOGRAMMI e A PARTENZE RIUNITE: la
    #    prima stesura faceva il giro per pillola (void offsetWidth
    #    fra il «da» e il bersaglio), e il reflow della PRIMA pillola
    #    fissava lo stile «prima» della SECONDA al suo bersaglio — il
    #    suo FLIP era un no-op, e animava solo la prima della fila
    #    (la spedizione: e' il caso visto dal campo). In headless le
    #    transizioni non avanzano (la lezione della tastiera): si
    #    prova la STRUTTURA, il movimento lo dice il telefono.
    prova("la corsa recupera il «da» dal computed del fill", True,
          "getComputedStyle(el, '::before')" in mini3)
    #    LA SCATOLA DELLA MISURA (13 ago 2026, lo «scattino indietro»
    #    visto dal telefono e trovato campionando): il % del ::before
    #    si risolve sul PADDING BOX — clientWidth — mentre il rect
    #    porta anche il bordo: ogni cattura usciva fino a ~1% piu'
    #    bassa (2-3px ad alto progresso, ridipinti indietro e
    #    ri-percorsi in avanti), e la scattata reduce dallo scatto
    #    rifaceva una mini-corsa 99→100 a ogni tocco.
    #    Dal 13 ago 2026 cattura e via sono FERRI CONDIVISI
    #    (barreCattura/barreCorri): li corre anche il carrello, e una
    #    seconda stesura della corsa e' il posto dove il prossimo «si
    #    anima solo la spedizione» tornerebbe a nascondersi.
    _cat = pezzo_js(mini3, "function barreCattura(box){", "\n}")
    prova("...e misura sulla scatola del ::before (clientWidth)", True,
          "el.clientWidth" in _cat
          and "getBoundingClientRect" not in _cat)
    _cor = pezzo_js(mini3, "function barreCorri(box, barraDa){", "\n}")
    prova("...e parte in due fotogrammi, mai con un reflow", True,
          "requestAnimationFrame(()=>requestAnimationFrame(" in _cor
          and "void el.offsetWidth" not in mini3)
    prova("...i ferri sono UNO: mai una seconda cattura o corsa",
          (1, 1), (mini3.count("function barreCattura"),
                   mini3.count("function barreCorri")))
    #    ...e a chiamarli sono in TRE: renderAcquisto e le due scatole
    #    del carrello. SI CHIEDE LA RIGA INTERA, ancorata all'a-capo e
    #    all'indentazione — un conteggio di sottostringhe restava
    #    verde con la chiamata COMMENTATA (l'ha detto la tortura, per
    #    la seconda volta: e' la lezione del reaper).
    prova("...e Paga e carrello chiamano i ferri, mai una copia",
          (True, 2, True, 2),
          ("\n  const barraDa = barreCattura(box);" in mini3,
           mini3.count("\n  const da = barreCattura(box);"),
           "\n  barreCorri(box, barraDa);" in mini3,
           mini3.count("\n  barreCorri(box, da);")))
    prova("...le OTTO pillole portano la chiave della corsa "
          "(quattro di Paga, quattro del carrello)", 8,
          mini3.count('data-barra="s'))
    prova("...allo scatto l'ultimo tratto corre nell'ACCESO", True,
          "barra-scatto" in mini3 and "'var(--barra-a)'" in mini3
          and ".barra-scatto{background:var(--card)" in mini3)
    prova("...e reduced-motion la spegne", 1,
          mini3.count(".barra-scatto::before{transition:none}"))
    #    L'IMPULSO DELLO SCATTO (13 ago 2026, chiesto da Andrea): quando
    #    la promessa scatta, un anello del suo stesso verde si allarga
    #    dalla pillola e svanisce — mezzo secondo, una volta sola,
    #    perche' fino a ieri quel momento lo diceva il solo colore e un
    #    colore lo vede solo chi in quell'istante stava guardando.
    #    E' UN ANELLO E NON UNA BANDA DI LUCE CHE ATTRAVERSA LA
    #    PILLOLA, ed e' una MISURA e non un gusto: la banda e' stata
    #    costruita e fotografata, e in tema chiaro era perfino un
    #    guadagno (l'inchiostro e' scuro: 8,01 → 12,60), ma di sera
    #    l'inchiostro e' CREMA e la stessa banda lo portava da 5,34 a
    #    1,25 — le parole sparivano per un decimo di secondo, proprio
    #    nell'istante che l'animazione esiste per far notare. Al buio
    #    QUALUNQUE schiarita del fondo abbassa il contrasto di un testo
    #    chiaro, e da 5,34 il margine finisce prima di vedersi: non c'e'
    #    taratura che salvi quel verso, e una forma che cambia col tema
    #    e' proprio cio' che qui non si fa. L'anello le parole non le
    #    tocca MAI (sta fuori dalla pillola) e vale identico nei due
    #    temi. L'ultimo fotogramma e' un anello TRASPARENTE: la pillola
    #    a riposo resta identica a ieri senza ripulire niente.
    prova("l'impulso dello scatto e' un anello FUORI dalla pillola",
          (True, True, False),
          ("@keyframes impulsoScatto" in mini3,
           "to{box-shadow:0 0 0 9px transparent}" in mini3,
           ".barra-impulso::after" in mini3))
    prova("...mezzo secondo, una volta sola, senza residuo", True,
          "animation:impulsoScatto .5s ease-out "
          "var(--impulso-ritardo,0ms) 1 both}" in mini3)
    #    SI CHIAMA «IMPULSO» E NON «LAMPO» APPOSTA: in questo progetto
    #    la lampo e' l'offerta a tempo (--lampo, .lampo-was, il rosso
    #    ⚡), e due significati per la stessa parola nello stesso foglio
    #    sono il posto dove fra sei mesi si sbaglia riga.
    prova("...e non si chiama «lampo», che qui e' l'offerta a tempo",
          False, "barra-lampo" in mini3 or "--lampo-ritardo" in mini3)
    #    PARTE SOLO ALLO SCATTO, E LA GUARDIA E' LO STATO DI PRIMA
    #    (`!da.t`) E NON LA CORSA (13 ago 2026, difetto dal campo:
    #    premendo veloce lo stepper l'anello ripartiva a ogni tocco).
    #    Qui c'era scritto che bastava il filtro dei 0.5 — «su una verde
    #    a riposo la cattura vale 100» — ed era FALSO: campionando
    #    durante una raffica, la cattura vale 100 solo a corsa FINITA.
    #    Nei primi due fotogrammi vale ancora la PARTENZA appena
    #    scritta (il render successivo arriva prima del doppio rAF che
    #    mette il bersaglio) e per i 350ms dopo vale l'INTERPOLATO:
    #    misurati 82, 82, 83,57, 87,91, 94,26, 99,06 — il filtro morde
    #    solo oltre i 350ms, cioe' dove il difetto non c'era.
    #    LA LEZIONE STA NELLA SENTINELLA DI IERI, che chiedeva la classe
    #    «dentro il ramo dello scatto»: era VERA e certificava comunque
    #    il difetto, perche' guardava dove sta la riga e non cosa la
    #    riapre. Adesso si chiede il DATO che risponde alla domanda
    #    giusta — `t` nella cattura, `!da.t` nella guardia — che e' un
    #    fatto del DOM di prima e non cambia sotto le dita.
    prova("...parte solo allo scatto: la guardia e' lo STATO di prima",
          (True, True),
          ("} else if (scatto && !da.t){" in _cor,
           "t: trust," in _cat))
    #    ...E UNA VOLTA PARTITO ARRIVA IN FONDO (13 ago 2026, il
    #    rovescio della cura di stamattina, difetto dal campo):
    #    l'anello vive sul NODO, e ogni render lo rifa' — a raffica
    #    l'animazione moriva col nodo vecchio, misurata a 60ms su 500.
    #    La cura e' il giro FLIP che la barra fa da sempre, applicato
    #    all'impulso: la cattura registra QUANTO E' AVANZATO e la corsa
    #    lo rimette sul nodo nuovo con un ritardo NEGATIVO, cioe' lo
    #    CONTINUA. Misurato dopo: avanzamento monotono (67, 117, 167,
    #    217, 267, 317, 367) e «finished» a 500 — vivo a ogni tocco
    #    entro la mezza corsa, e mai ripartito da capo.
    #    L'AVANZAMENTO SI PRENDE SOLO DA UN'ANIMAZIONE IN VOLO
    #    (`playState === 'running'`): quella finita non si riporta, o
    #    l'anello rinascerebbe morto a ogni tocco per sempre.
    prova("...e una volta partito arriva in fondo, sul nodo nuovo",
          (True, True, True),
          ("a.playState === 'running'" in _cat,
           "i: inVolo ? inVolo.currentTime" in _cat,
           "`${-Math.round(da.i)}ms`" in _cor))
    #    CONTINUARE NON E' RIPARTIRE, ed e' la riga che tiene insieme
    #    le due richieste: il ramo della continuazione NON incrementa
    #    `impulsi` (un anello che continua non deve sfasare un vero
    #    scatto che partisse nello stesso giro) e i due rami non
    #    possono sovrapporsi — l'anello esiste solo su una pillola gia'
    #    scattata, quindi `da.i` pieno implica `da.t` vero, che e'
    #    esattamente cio' che il ramo di partenza nega.
    prova("...ma continuare non e' ripartire: un solo conteggio",
          (1, True),
          (_cor.count("impulsi++"), "if (da.i != null && scatto){" in _cor))
    #    E IL BLOCCO STA SOPRA IL FILTRO DELLA CORSA: sotto, un tocco
    #    che non fa correre la barra — la cattura gia' a 100, il caso
    #    normale a raffica larga — uscirebbe dal giro senza riportare
    #    l'anello, che morirebbe li'. Sono due cose che capitano
    #    insieme, non una dentro l'altra.
    prova("...e l'impulso non dipende dal filtro della corsa", True,
          _cor.index("barra-impulso") < _cor.index("< 0.5) return"))
    #    IL GUARDIANO SU getAnimations non e' pignoleria: barreCattura
    #    sta nel mezzo del render, e una WebView che non ce l'ha
    #    alzerebbe li' dentro — una pagina bianca per un ornamento.
    prova("...e la cattura non alza dove getAnimations non c'e'", True,
          "el.getAnimations ? el.getAnimations() : []" in _cat)
    #    DUE PROMESSE INSIEME NON PULSANO INSIEME (decisione di Andrea):
    #    la seconda parte quando la prima e' a meta' corsa — un gesto in
    #    due battute invece di un doppio colpo. Il ritardo si scrive
    #    dalla SECONDA in poi: senza quel `if (impulsi)` partirebbero
    #    insieme, e scritto al rovescio ritarderebbe anche la prima.
    prova("...e la seconda e' sfalsata, mai insieme alla prima", True,
          "if (impulsi)" in _cor
          and "'--impulso-ritardo', `${IMPULSO_PASSO}ms`" in _cor)
    #    LA LEVA E' UNA RIGA: IMPULSO_SCATTO a false e si torna
    #    ESATTAMENTE a ieri — la classe non si attacca piu' e il blocco
    #    CSS resta inerte perche' non veste piu' nessuno.
    prova("...e la leva per toglierlo e' una riga sola", 1,
          mini3.count("const IMPULSO_SCATTO = true;"))
    #    ...e reduced-motion lo SPEGNE, non lo ferma: con
    #    animation-play-state resterebbe un anello piantato attorno alla
    #    pillola per sempre.
    prova("...reduced-motion lo spegne, non lo ferma", (1, False),
          (mini3.count(".barra-impulso{animation:none}"),
           "barra-impulso{animation-play-state" in mini3))
    #    IL FONDO DI PAGA E' APPICCICATO (ago 2026): «Paga» resta in
    #    vista mentre si scorre — STICKY e mai fixed (dentro Telegram
    #    le misure di viewport mentono, e sticky occupa layout: a fine
    #    scorrimento l'ultima riga del conto non e' mai coperta) — con
    #    la safe-area SUA e il padding-bottom del corpo a zero, o a
    #    fine pagina ci sarebbero due safe-area impilate.
    #    DALL'AGO 2026 LO EREDITA ANCHE IL CARRELLO, che questa pagina
    #    se l'e' presa: qui c'era «SOLO la pagina Paga: il riepilogo
    #    del pacco tiene il fondo di sempre», e quella riga e' morta
    #    con la vista che nominava. Al suo posto il fatto nuovo, che e'
    #    l'affermazione piu' forte: di fondi appiccicati ce n'e' UNO in
    #    tutto il foglio — una prova sulla vista che non esiste piu'
    #    sarebbe una che non puo' fallire.
    prova("il fondo di Paga e' appiccicato (sticky, mai fixed)", True,
          "#view-acquisto .ctrl-fondo{position:sticky" in mini3)
    prova("...con la safe-area sua e il corpo senza doppio fondo", True,
          "#view-acquisto .ctrl-corpo{padding-bottom:0}" in mini3
          and mini3.count("#view-acquisto .ctrl-fondo{position:sticky;"
                          "bottom:0") == 1)
    prova("...ed e' l'unico fondo appiccicato del client", 1,
          mini3.count(".ctrl-fondo{position:sticky"))
    #    «SCONTO» SECCO COL SUO TAG (ago 2026, decisione di Andrea che
    #    ROVESCIA il taglio della percentuale): «sugli articoli» qui
    #    non serve — la riga «Spedizione» sta due righe piu' giu' COL
    #    SUO IMPORTO, quindi si vede da sola che sono voci diverse — e
    #    lo spazio guadagnato fa stare la percentuale, che l'etichetta
    #    lunga mozzava a 320 in sats. MISURATO dopo: 95px su 178, con
    #    83 di margine (prima ne chiedeva ~168 su 158).
    #    La formula lunga RESTA dove risponde a una domanda aperta: il
    #    cassetto del venditore, l'hint del form Vendi e la ricevuta
    #    dell'ordine, che e' una riga sola senza nessuna «Spedizione»
    #    accanto a fare il contrasto.
    #    il corpo si ripulisce dai COMMENTI prima di cercare: quello
    #    che introduce la riga CITA la formula vecchia — è la storia
    #    del rovesciamento, e vale più di una prova comoda — e senza
    #    questo la sentinella sarebbe rossa sul codice buono (la
    #    trappola già pagata col «punto» e con la nota della valuta)
    _cr = re.sub(r"/\*[\s\S]*?\*/", "",
                 pezzo_js(mini3, "function contoRighe(c){", "\n}"))
    prova("nel conto l'etichetta dello sconto e' secca", (True, False),
          ("r(`Sconto${c.scontoPct" in _cr,
           "Sconto sugli articoli" in _cr))
    #    E LO STESSO NEL paySheet (ago 2026): le righe sono le stesse
    #    — Articolo, Sconto, Spedizione, Totale — quindi il contrasto
    #    c'e' e vale lo stesso ragionamento. La percentuale e' il NONO
    #    argomento posizionale, e il CENSIMENTO qui sotto e' la sua
    #    rete: chi ne aggiunge una chiamata e la dimentica lascia
    #    «Sconto» nudo, che e' un difetto che non alza niente e non si
    #    vede finche' non lo guarda qualcuno col conto scontato aperto.
    _cs = re.sub(r"/\*[\s\S]*?\*/", "",
                 pezzo_js(mini3, "function contoScomposto(", "\n}"))
    prova("anche nel paySheet l'etichetta e' secca", (True, False),
          ("r(sconto, `Sconto${scontoPct" in _cs,
           "Sconto sugli articoli" in _cs))
    # le parentesi si contano DAVVERO invece di una regex annidata a
    # un livello: una chiamata ne ha due (`(via && via.pezzi)||0`) e
    # sfuggiva — cioe' il censimento avrebbe detto «tutte a posto»
    # guardandone una in meno, che e' il modo in cui una rete mente
    def _chiamata(js, dalla):
        i, prof = dalla + len("contoScomposto("), 1
        while i < len(js) and prof:
            prof += (js[i] == "(") - (js[i] == ")")
            i += 1
        return js[dalla:i]
    # la DEFINIZIONE si esclude guardando il «function» che la precede,
    # mai il nome del primo argomento: `contoScomposto(artS, ...)` di
    # startBuy comincia per «art» come lei, e un filtro sul prefisso se
    # la portava via — il censimento avrebbe detto «tutte a posto»
    # guardandone CINQUE su sei
    _pulito = re.sub(r"/\*[\s\S]*?\*/", "", mini3)
    _chiamate = [_chiamata(_pulito, m.start())
                 for m in re.finditer(r"(?<!function )contoScomposto\(",
                                      _pulito)]
    prova("...e OGNI chiamata le passa la percentuale",
          (6, []), (len(_chiamate),
                    [c[:40] for c in _chiamate if "_percento" not in c]))
    prova("...e porta la percentuale, dal server e mai dedotta", True,
          '<span class="sconto-tag">−${c.scontoPct}%</span>' in _cr
          and "scontoPct: p.sconto_percento" in mini3)
    prova("...e la formula lunga resta dov'e' una risposta", (True, True),
          ("🎁 Sconto sugli articoli${o.scontoPct" in mini3,
           ">Sconto sugli articoli <span class=\"conta\"" in mini3))
    #    IL TOGGLE €/₿ VIVE ACCANTO AL CONTO (ago 2026, decisione di
    #    Andrea): stava in testata, e da li' governava cifre che a
    #    volte erano fuori schermo. La fabbrica e' UNA (toggleValuta) e
    #    la chiamano i due rami del render — lo scheletro e la pagina
    #    piena — o toccando ± sparirebbe finche' il conto non torna.
    #    MISURATO a 320: titolo 72 + toggle 56 sulla riga da 256, con
    #    108px di linea puntinata in mezzo e i due centri allineati.
    prova("il toggle valuta e' uscito dalla testata della cassa", True,
          '<div class="ctrl-corpo" id="acqCorpo"></div>' in mini3
          and "pacco-tit\"><b id=\"acqTit\"" in mini3
          and mini3.index('id="view-acquisto"')
              < mini3.index('id="acqCorpo"'))
    _testa = mini3[mini3.index('id="view-acquisto"'):
                   mini3.index('id="acqCorpo"')]
    prova("...e la sua testata non ne porta piu' uno", 0,
          _testa.count("cur-seg"))
    prova("...la fabbrica del toggle e' una sola", 1,
          mini3.count("function toggleValuta("))
    #    e il censimento delle SUPERFICI del toggle: otto in tutto il
    #    client (searchbar, carrello, i due dell'offerta, il dettaglio,
    #    LA CASSA — che e' l'unica a passare da una fabbrica invece che
    #    dal markup — l'ordine e il pannello). Chi ne aggiunge una lo
    #    sente da qui, invece di scoprirlo da un toggle che non si
    #    accende: e' aggiornaCurToggle a doverli conoscere tutti.
    prova("...e le superfici del toggle sono otto", 8,
          mini3.count('class="cur-seg'))
    prova("...tutte pescate per data-cur, mai per id", True,
          "'.cur-seg button[data-cur]'" in mini3)
    prova("...e la chiamano i due rami del render", 2,
          pezzo_js(mini3, "function renderAcquisto(){",
                   "\n}").count("${toggleValuta()}"))
    prova("...accanto al titolo del conto, che pesa un gradino in piu'",
          (True, True),
          ('class="section-label conto-tit">Il conto${toggleValuta()}'
           in mini3, ".conto-tit{font-size:13px}" in mini3))
    prova("...e sta a destra DOPO la linea puntinata", True,
          ".conto-tit .conto-cur{order:2}" in mini3
          and ".section-label::after{" in mini3
          and "order:1}" in mini3)
    #    LA CASSA E' UNA SOLA E SERVE I DUE ACQUISTI (ago 2026): il
    #    carrello ci arriva diritto, e quel che e' SUO — i due
    #    secondari e il bottone che riporta a comporre — vive gated su
    #    d.tipo==='set'. Non basta contare i frammenti: si chiede che
    #    la condizione sia nella stessa const, o domani ne nasce uno
    #    che compare anche sul singolo.
    _rac = pezzo_js(mini3, "function renderAcquisto(){", "\n}")
    prova("i secondari sono del solo carrello", True,
          "const secondari = d.tipo==='set'" in _rac)
    prova("...e ci sono tutti e due", True,
          'onclick="ctrlChiediInfo()"' in _rac
          and "onclick=\"go('offertapresto')\"" in _rac)
    #    IL BOTTONE CHE RIPORTA AL CARRELLO: solo sul carrello, e solo
    #    con un invito APERTO — sotto un «✅ Sconto −10%» sarebbe un
    #    invito a fare una cosa che non serve (decisione di Andrea).
    prova("il «torna al carrello» e' del solo carrello, e solo con un"
          " invito aperto", True,
          "const tornaCarrello = (d.tipo==='set'"
          " && pillole.includes('pill-barra'))" in _rac)
    prova("...e sul singolo non nasce mai", 1,
          _rac.count("tornaCarrello = "))
    #    IL ⚡ RESTA DEL SOLO SINGOLO: il set paga dal paySheet (il suo
    #    confermaSetSubito e' morto col foglio del riepilogo). La
    #    regola viveva nel codice senza nessuna sentinella, e dopo la
    #    fusione e' una riga che si puo' rompere senza accorgersene.
    prova("il ⚡ Compra subito resta del solo singolo", True,
          "d.tipo==='mono' && !DEMO && !VETRINA && walletNwc()" in _rac)
    #    IL CARRELLO POTATO RIFA' IL CONTO (ago 2026): rileggiVenditore
    #    MUTA setScelte, e renderAcquisto disegna dalla CACHE — senza
    #    questa riga si vedrebbero due articoli a schermo e tre nel
    #    totale. Prima era la cache per firma del riepilogo a salvare
    #    la faccia; da quando quella pagina non c'e' piu', tocca qui.
    #    E la soglia e' DUE: il set a una riga il server lo rifiuta.
    _rs = pezzo_js(mini3, "async function rinfrescaSet(){", "\n}")
    prova("il carrello potato rifa' il conto", True,
          "caricaPreventivo()" in _rs)
    prova("...e sotto i due articoli esce invece di restare", True,
          "setScelte.size < 2" in _rs and "navIndietro()" in _rs)
    #    LA PROVENIENZA SI RIALLINEA PRIMA DEL CONTO: currentListing
    #    puo' essere rimasto su un annuncio di un ALTRO venditore (le
    #    celle del carrello sono card, e il tocco apre il dettaglio), e
    #    rinfrescaSet legge proprio lui per rileggere il negozio. La
    #    riga arriva da controllaPacco, che non esiste piu': senza,
    #    dopo un 409 si poterebbe il pacco col catalogo sbagliato.
    _aas = pezzo_js(mini3, "function apriAcquistoSet(){", "\n}")
    prova("la provenienza si riallinea prima del conto", True,
          "currentListing = orig" in _aas)
    #    IL RIENTRO E' ISTANTANEO: la cassa si apre e si chiude mentre
    #    si compone, e la firma dice se il conto in mano e' ancora
    #    quello — e' quel che la cache del riepilogo dava gia'.
    prova("...e il rientro a composizione ferma non richiede il conto",
          True, "acqDati.firma === f && acqDati.preventivo" in _aas)
    #    E L'UNITARIO RESTA IL PIENO col tag della regola quando lo
    #    sconto scatta (la via (c)): mai un numero unitario scontato —
    #    non esiste come intero e non torna moltiplicando — e mai un
    #    ≈, che significa gia' un'altra cosa (la conversione).
    prova("il tag −X% compare solo a sconto scattato", True,
          "((p.sconto_sats||0) > 0 && (p.sconto_percento||0) > 0)"
          in mini3)
    prova("...e dice la PERCENTUALE", True,
          'class="sconto-tag">−${p.sconto_percento}%' in mini3)
    #    E LA CIFRA SCONTATA, SOLO QUANDO E' ESATTA (13 ago 2026,
    #    rovesciamento di Andrea sulla misura vera: ZERO divisioni
    #    inesatte su 52 annunci scontati in produzione — il ramo
    #    solo-tag e' una cintura, non il caso). La cifra la calcola il
    #    SERVER sulla faccia NATIVA (sats, o CENTESIMI per i listini
    #    in euro) e il client la MOSTRA solo se c'e'; MAI un ≈ da
    #    arrotondamento — in quella casella il ≈ della conversione
    #    compare gia', e due significati sulla stessa cifra nello
    #    stesso posto sono peggio di nessuna cifra.
    prova("la cifra scontata arriva dal server, il client mostra",
          True, "p.articolo_unitario_netto_sats || 0" in mini3)
    prova("...col pieno BARRATO sotto, la resa della lampo", True,
          'class="mono acq-barrato"' in mini3)
    prova("...e la barratura non taglia l'unita'", True,
          ".acq-barrato .unit{display:inline-block}" in mini3)
    prova("server: la cifra nasce solo dalla divisione esatta", True,
          "(unitario * pct) % 100 == 0" in src
          and "(_cents * pct) % 100 == 0" in src)
    prova("server: la chiave esiste, a zero quando non e' vera", True,
          '"articolo_unitario_netto_sats": unit_netto' in src)

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
    # ...e ci resta anche quando ne arriva un'altra dopo: le colonne si
    # AGGIUNGONO in coda, mai in mezzo, o i CSV gia' compilati
    # comincerebbero a leggere il valore sbagliato sotto l'intestazione
    # giusta. Dall'ago 2026 l'ultima e' il supplemento per pezzo.
    prova("il modello CSV chiude con spedizione_extra", True,
          intest.rstrip().endswith("spedizione_extra"))
    prova("...e spedizione_punto e' rimasta al suo posto, prima", True,
          "spedizione_punto;" in intest)

    # --- il client ---------------------------------------------------
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il foglio del varco non esiste piu'", False,
          "function apriFoglioConsegna" in mini)
    prova("...e nemmeno la sua scelta", False,
          "function scegliConsegnaFoglio" in mini)
    prova("consegnaEsplicita non si scrive piu'", False,
          "consegnaEsplicita =" in mini)
    # l'ordine nasce solo dai varchi noti: startBuy, startBuySet e
    # confermaCompraSubito — piu' l'UNICO lettore del preventivo
    prova("tre POST /orders (i varchi di sempre)", 3,
          mini.count("fetch(`${API_BASE}/orders`"))
    # UN CONTO SOLO (ago 2026, il cantiere della cassa): i lettori del
    # preventivo erano DUE — caricaPreventivo e caricaPreventivoPacco,
    # col riepilogo che teneva la sua cache per firma — e adesso e'
    # uno. E' la sentinella piu' preziosa del cantiere: certifica che
    # non sia rinato un secondo posto che chiede il conto.
    prova("un lettore solo del preventivo", 1,
          mini.count("fetch(`${API_BASE}/orders/preventivo`"))
    prova("...e il secondo non e' tornato", (False, False),
          ("function caricaPreventivoPacco" in mini, "ctrlPrev =" in mini))
    prova("la vista nuova esiste", True, 'id="view-acquisto"' in mini)
    # LA PAGINA DEL RIEPILOGO NON ESISTE PIU' (ago 2026): il carrello
    # pagava in tre pagine e quella di mezzo non decideva niente.
    prova("il riepilogo del carrello non esiste piu'",
          (False, False, False),
          ('id="view-controllapacco"' in mini,
           "function renderControlla" in mini,
           "function controllaPacco(" in mini))
    prova("...e il carrello entra dalla porta della cassa", True,
          'id="paccoControlla" onclick="apriAcquistoSet()"' in mini)
    prova("il varco-mappa e' dichiarato dove andra' la mappa", True,
          "VARCO MAPPA" in mini)
    prova("il punto passa da esc() alla resa", True,
          "esc(o.puntoRitiro)" in mini)
    # (CORRIERI del tracking resta legittimamente nel client: qui si
    # guarda che il catalogo SPEDIZIONIERI arrivi dal server)
    prova("il bottone finale della pagina dice «Paga»", True,
          'id="acqCompra" onclick="ctaAcquisto()">Paga<' in mini)
    # IL DEFAULT DELLA VIA E' IL PUNTO DI RITIRO (ago 2026, che AFFINA
    # il 12 ago: la spedizione batte il ritiro — i numeri di
    # produzione, 35 schede su 82 col badge 🚚 sopra un ritiro
    # preselezionato che nessuno aveva scelto, restano veri — e fra le
    # due spedizioni vince il PUNTO, perche' e' la via marcata
    # «Consigliato»: default e consiglio devono dire la stessa cosa,
    # non indicare due strade diverse). Il giudice e' UNO — precedenza
    # punto → casa → ritiro → digitale — e i chiamanti DUE, la pagina
    # vera e il ramo DEMO: chi torna a vive[0], a strade[0] o a
    # casa-prima fa rosse queste righe.
    prova("il default della via e' una precedenza, punto prima",
          True,
          "for (const v of ['punto','casa','ritiro','digitale'])" in mini)
    prova("...il giudice e' uno coi suoi due chiamanti", 3,
          mini.count("viaDefault("))
    prova("...e il ramo DEMO non fa piu' da se'", False,
          ".strade[0] || {}).via" in mini)
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
    # le mappe dei punti (ago 2026): due link alle mappe ufficiali,
    # niente widget ne' API. Gli URL vivono in MAPPE_PUNTI e mai
    # dentro un onclick, e dentro Telegram si apre con tg.openLink —
    # la strada documentata: un target="_blank" nella WebView di
    # certi client non apre niente.
    prova("le mappe dei punti: l'URL InPost vive nel catalogo, una volta",
          1, mini.count("https://inpost.it/trova-un-locker"))
    prova("...e quello di Poste", 1,
          mini.count("https://www.poste.it/cerca-mappe-app/?vieni-in-poste"))
    prova("dentro Telegram si apre con tg.openLink", True,
          "tg.openLink(m.url)" in mini)
    prova("il giudice dei link e' UNO (linkMappePunti)", 1,
          mini.count("function linkMappePunti"))
    # i CHIAMANTI, contati togliendo la definizione: col cantiere
    # delle reti uno dei due e' finito dentro un ternario e non ha
    # piu' il `${` davanti — cercare quello contava una superficie
    # sola e la prova diceva il falso proprio mentre le due c'erano
    prova("...e lo chiamano le due superfici del punto", 2,
          mini.count("linkMappePunti(")
          - mini.count("function linkMappePunti("))
    # DAL CANTIERE DELLE RETI il giudice prende una LISTA, e la regola
    # «una rete senza mappa non aggiunge niente» vive nel filtro:
    # 'Altro' non sta in RETE_MAPPA, quindi cade da se'. La sentinella
    # ha cambiato FORMA, non lato — resta l'affermazione che un link
    # fuorviante e' peggio di nessun link.
    prova("il giudice delle mappe prende una LISTA di reti", True,
          "function linkMappePunti(reti)" in mini)
    prova("con 'Altro' nessun link: la mappa sbagliata e' peggio di "
          "nessuna", True,
          ".map(r => RETE_MAPPA[r]).filter(Boolean)" in mini)
    prova("...e 'Altro' non ha una mappa nel catalogo", False,
          "'Altro':" in mini.split("const RETE_MAPPA")[1][:200])
    prova("nessuna rete dichiarata = tutte le mappe (il «non lo so» "
          "detto onestamente)", True,
          ": ['inpost', 'poste']" in mini)
    # IL DIFETTO CHIUSO (ago 2026): per un anno il campo DENTRO
    # l'ordine ha chiamato il giudice con un '' hardcodato, quindi
    # mostrava sempre tutte e due le mappe anche a rete dichiarata —
    # e il commento del giudice diceva il contrario. Adesso la rete
    # viaggia nell'ordine e gliela si passa.
    prova("il campo dell'ordine non passa piu' un '' hardcodato",
          False, "linkMappePunti('')" in mini)
    prova("...gli passa la rete dell'ordine", True,
          "linkMappePunti(o.retePunto ? [o.retePunto] : [])" in mini)
    prova("la nota consiglia il locker automatico", True,
          "NOTA_LOCKER" in mini and "locker automatico" in mini)

    # ---- LA MISURA DEL TESTO (ago 2026) ----
    # Il cuore e' UNO: `zoom` sulla radice. La trappola che questa
    # famiglia sorveglia e' l'altra meta' della ricetta — le unita' di
    # VIEWPORT non si zoomano, quindi ogni altezza in vh/dvh dentro la
    # radice DEVE dividersi per la scala, o le colonne alte uno
    # schermo (pagina d'acquisto, riepilogo, fogli) sborderebbero e il
    # fondo scivolerebbe sotto la piega. E' esattamente il tipo di
    # riga che qualcuno riscrive «pulendo» un calc.
    srv = open("server.py", encoding="utf-8").read()
    prova("la scala del testo si applica in UN posto solo", 1,
          mini.count("html{zoom:var(--fs-zoom,1)}"))
    for riga_vh in re.findall(r"(?:min|max)-height:calc\([^;]*?d?vh[^;]*\)",
                              mini):
        prova("altezza di viewport divisa per la scala: "
              + riga_vh[:44], True, "var(--fs-zoom,1)" in riga_vh)
    prova("la misura vive anche in colonna (segue la persona)", True,
          "font_scala INTEGER DEFAULT 100" in srv
          and "SET font_scala=?" in srv)
    prova("...e il server accetta solo le misure del catalogo", True,
          "if scala not in SCALE_FONT" in srv)
    prova("...con 100 nel catalogo: la misura di sempre resta a un "
          "tocco", True,
          bool(re.search(r"SCALE_FONT = \([^)]*\b100\b", srv)))
    prova("le voci arrivano da /api/me, mai hardcodate", True,
          '"scale_font"' in srv and "me.scale_font" in mini)
    prova("la scala si accende prima del primo paint (anti-flash)",
          True, "barattolo_font" in mini.split("</head>")[0])


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
    exec(src[i:src.index("\nTIMBRO_LIBRO_MASTRO", i)], amb)
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
          sped_gratis_sats INT DEFAULT 0,
          consegna_scelta TEXT DEFAULT 'spedizione',
          stato TEXT DEFAULT 'locked', payout_stato TEXT DEFAULT '',
          aggiornato INT DEFAULT 0, via_punto INT DEFAULT 0,
          busta_nome TEXT DEFAULT '', busta_codice TEXT DEFAULT '',
          busta_il INT DEFAULT 0, busta_corretta_il INT DEFAULT 0,
          busta_correzioni INT DEFAULT 0,
          indirizzo TEXT DEFAULT '', indirizzo_il INT DEFAULT 0,
          indirizzo_purgato_il INT DEFAULT 0,
          nascosto_compratore INT DEFAULT 0,
          nascosto_venditore INT DEFAULT 0);
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
        CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY,
          sconto_pacco_criterio TEXT DEFAULT 'pezzi',
          sconto_pacco_soglia INT DEFAULT 0,
          sconto_pacco_valore INT DEFAULT 0,
          sconto_pacco_valore_eur INT DEFAULT 0,
          sconto_pacco_valore_valuta TEXT DEFAULT 'eur',
          sconto_pacco_percento INT DEFAULT 0,
          sped_gratis_soglia INT DEFAULT 0,
          sped_gratis_soglia_eur INT DEFAULT 0,
          sped_gratis_valuta TEXT DEFAULT 'eur');
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
        -- UN MONO SCONTATO SANO (ago 2026, il mono sconta): 3 pezzi,
        -- lordo 30.000, sconto 3.000, spedizione 500 -> 27.500. La
        -- divisione a ritroso torna esatta, e nessuno deve fiatare.
        INSERT INTO ordini(id,annuncio_id,prezzo_sats,sconto_sats,
          sconto_percento,spedizione_sats,quantita)
          VALUES(6, 9, 27500, 3000, 10, 500, 3);
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
        -- UNA BUSTA SANA: via punto, nome+codice+timbro insieme
        INSERT INTO ordini(id,annuncio_id,prezzo_sats,stato,via_punto,
          busta_nome,busta_codice,busta_il)
          VALUES(4, 9, 1000, 'shipped', 1,
                 'plain:Mario Rossi', 'plain:PIN 4321', 123);
        -- UN NASCOSTO SANO: released, il compratore l'ha messo via —
        -- e' il caso LEGITTIMO, e non deve suonare
        INSERT INTO ordini(id,annuncio_id,prezzo_sats,stato,
          nascosto_compratore)
          VALUES(5, 9, 1000, 'released', 1);
        -- SEI NEGOZI SANI: uno sconta a pezzi, uno a valore in EURO,
        -- uno a valore in SATS, uno e' spento (e uno spento non deve
        -- suonare mai), uno offre la spedizione in sats, e uno (777)
        -- ha TUTTI E DUE i criteri accesi — le sue due gambe sono
        -- serie, quindi non deve fiatare nemmeno lui.
        -- I DUE IN SATS sono la ragione per cui questi controlli hanno
        -- dovuto imparare la valuta: hanno legittimamente la colonna
        -- in euro a ZERO, e senza il CASE suonerebbero per sempre.
        INSERT INTO utenti(tg_id,sconto_pacco_criterio,sconto_pacco_soglia,
          sconto_pacco_valore,sconto_pacco_valore_eur,
          sconto_pacco_valore_valuta,sconto_pacco_percento,
          sped_gratis_soglia,sped_gratis_soglia_eur,sped_gratis_valuta)
          VALUES(222, 'pezzi',  3, 0,     0,   'eur',  10, 0,     0,  'eur'),
                (333, 'valore', 0, 0,     100, 'eur',  15, 0,     25, 'eur'),
                (555, 'valore', 0, 50000, 0,   'sats', 12, 0,     0,  'eur'),
                (666, 'pezzi',  2, 0,     0,   'eur',  10, 50000, 0,  'sats'),
                (777, 'entrambi', 3, 0,   25,  'eur',  10, 0,     0,  'eur'),
                (444, 'pezzi',  0, 0,     0,   'eur',  0,  0,     0,  'eur');
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
        # «mono scontato» e' morto col rovesciamento (ago 2026, il mono
        # sconta): al suo posto i due invarianti veri della testata.
        # (27500-500+2999) = 29999, che per 3 non si divide:
        ("UPDATE ordini SET sconto_sats=2999 WHERE id=6",
         "aritmetica del mono", "6"),
        ("UPDATE ordini SET sconto_sats=99999 WHERE id=1",
         "sconto fuori scala", "1"),
        # prezzo 497 < sped 500: il netto e' negativo, cioe' lo sconto
        # supera la merce — e (497-500+3000)=2997 si divide per 3, cosi'
        # a svegliarsi e' SOLO il controllo giusto
        ("UPDATE ordini SET prezzo_sats=497 WHERE id=6",
         "sconto fuori scala (mono)", "6"),
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
        # la promessa che non puo' scattare, nei suoi tre modi: qui non
        # si perdono sats, si perde una vendita — e in silenzio
        ("UPDATE utenti SET sconto_pacco_criterio='peso' WHERE tg_id=222",
         "promessa di sconto che non puo' scattare", "222"),
        ("UPDATE utenti SET sconto_pacco_soglia=1 WHERE tg_id=222",
         "promessa di sconto che non puo' scattare", "222"),
        ("UPDATE utenti SET sconto_pacco_valore_eur=0 WHERE tg_id=333",
         "promessa di sconto che non puo' scattare", "333"),
        # ...e i due modi NUOVI, che la valuta porta con se': la cifra
        # a zero NELL'UNITA' DICHIARATA (in sats, dove prima nessuno
        # guardava) e una valuta che nessun ramo sa misurare
        ("UPDATE utenti SET sconto_pacco_valore=0 WHERE tg_id=555",
         "promessa di sconto che non puo' scattare", "555"),
        ("UPDATE utenti SET sconto_pacco_valore_valuta='usd' "
         "WHERE tg_id=555",
         "promessa di sconto che non puo' scattare", "555"),
        # ...e col criterio 'entrambi' (ago 2026) devono essere serie
        # TUTTE E DUE le gambe: chi ne accende due e ne ha una sola
        # valida promette meta' di quel che crede, e in vetrina non se
        # ne accorge nessuno. Due casi, uno per gamba.
        ("UPDATE utenti SET sconto_pacco_criterio='entrambi', "
         "sconto_pacco_soglia=1 WHERE tg_id=333",
         "promessa di sconto che non puo' scattare", "333"),
        ("UPDATE utenti SET sconto_pacco_criterio='entrambi', "
         "sconto_pacco_valore_eur=0 WHERE tg_id=222",
         "promessa di sconto che non puo' scattare", "222"),
        # il gemello della spedizione gratis, che prima della valuta
        # non aveva ragione di esistere: una promessa accesa in
        # un'unita' che nessuno sa misurare e' spenta in silenzio
        ("UPDATE utenti SET sped_gratis_valuta='usd' WHERE tg_id=666",
         "promessa di spedizione gratis che non puo' scattare", "666"),
        # la spedizione gratis: le due colonne si escludono per
        # costruzione (stesso INSERT), quindi una riga qui vuol dire
        # che una delle due cifre e' falsa
        ("UPDATE ordini SET sped_gratis_sats=800 WHERE id=1",
         "spedizione risparmiata e pagata insieme", "1"),
        ("UPDATE ordini SET sped_gratis_sats=800, consegna_scelta='ritiro' "
         "WHERE id=2",
         "spedizione risparmiata dove non si spediva", "2"),
        # la busta fuori contratto, nei suoi quattro modi: flag, nome
        # e codice si scrivono nello stesso UPDATE dietro la stessa
        # guardia — una riga spaiata e' un deposito a meta' o una
        # guardia caduta
        ("UPDATE ordini SET busta_nome='' WHERE id=4",
         "busta fuori contratto", "4"),
        ("UPDATE ordini SET busta_codice='' WHERE id=4",
         "busta fuori contratto", "4"),
        ("UPDATE ordini SET via_punto=0 WHERE id=4",
         "busta fuori contratto", "4"),
        ("UPDATE ordini SET busta_il=0, busta_nome='', busta_codice='', "
         "busta_corretta_il=99 WHERE id=4",
         "busta fuori contratto", "4"),
        # il nascondere e' ammesso solo sugli stati assorbenti: un
        # flag su un ordine vivo e' una guardia caduta — e un ordine
        # che una parte non vede piu'
        ("UPDATE ordini SET nascosto_venditore=1 WHERE id=2",
         "ordine nascosto su uno stato non finale", "2"),
        # l'indirizzo di casa, nei suoi quattro modi. L'ULTIMO E'
        # QUELLO CHE CONTA: se la scopa ha timbrato la cancellazione
        # ma il testo e' ancora li', la promessa scritta nella pagina
        # pubblica e' falsa — ed e' cio' che la rende verificabile
        # invece che raccontata.
        ("UPDATE ordini SET indirizzo='via Roma 1' WHERE id=4",
         "indirizzo fuori contratto", "4"),
        ("UPDATE ordini SET indirizzo_il=99 WHERE id=4",
         "indirizzo fuori contratto", "4"),
        ("UPDATE ordini SET indirizzo='via Roma 1', indirizzo_il=99, "
         "via_punto=1 WHERE id=4",
         "indirizzo fuori contratto", "4"),
        ("UPDATE ordini SET indirizzo='via Roma 1', indirizzo_il=99, "
         "indirizzo_purgato_il=100 WHERE id=4",
         "indirizzo fuori contratto", "4"),
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
          corpo.index("timbro_scrivi(TIMBRO_LIBRO_MASTRO, oggi)")
          < corpo.index("for nome, perche, sql"))
    prova("...e sta nel DATABASE, non in un globale che muore al deploy",
          True, "timbro_letto(TIMBRO_LIBRO_MASTRO)" in corpo)
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
def prove_divisione_a_ritroso():
    """IL CENSIMENTO DELLE DIVISIONI A RITROSO (ago 2026, il mono
    sconta): l'unitario del mono si ricava dalla testata in TRE copie
    — _righe_ordine, la ripresa del pentito in compra(), e la riga
    «N pezzi x unitario» del client — e una copia che dimentica di
    riaggiungere sconto_sats non fa fallire niente: mostra un unitario
    storto in ordine, notifiche e CSV, in silenzio. Percio' qui non
    c'e' un elenco a memoria ma un CENSIMENTO che guarda i file (la
    lezione del titolo nudo): la quarta copia di domani entra nel
    conto da sola, e ogni copia ha la sua prova che il + dello sconto
    ci sia davvero. Le ancore si confrontano a spazi COLLASSATI, cosi'
    gli a-capo (e i CRLF dei due file) non le spezzano."""
    print("\n[le divisioni a ritroso: il censimento]")
    src = _SORGENTE
    mini = open("miniapp.html", encoding="utf-8").read()
    nudo = lambda s: re.sub(r"\s+", "", s)

    # --- il censimento: la forma della sottrazione dalla testata ----
    # server: prezzo - spedizione - protezione coi nomi tra parentesi
    # quadre (l'SQL del libro mastro, che e' senza quadre, resta fuori
    # da se'; netto_venditore non ha la spedizione e non matcha)
    forma_srv = re.compile(
        r'\w+\["prezzo_sats"\]-\w+\["spedizione_sats"\]'
        r'-\w+\["protezione_sats"\]')
    srv_nudo = nudo(codice(src))
    prova("server: le copie della sottrazione sono DUE", 2,
          len(forma_srv.findall(srv_nudo)))
    # client: la stessa sottrazione coi nomi di mapOrder
    mini_vivo = re.sub(r"/\*.*?\*/", "", mini, flags=re.S)
    forma_cli = re.compile(
        r"\.price-\(\w+\.spedSats\|\|0\)-\(\w+\.protSats\|\|0\)")
    prova("client: la copia della sottrazione e' UNA", 1,
          len(forma_cli.findall(nudo(mini_vivo))))

    # --- copia n.1: _righe_ordine riaggiunge lo sconto --------------
    prova("copia 1 (_righe_ordine): +sconto_sats nella divisione", True,
          nudo('(o["prezzo_sats"]-o["spedizione_sats"]'
               '-o["protezione_sats"]+(o["sconto_sats"]or0))//qta')
          in nudo(codice(pezzo("_righe_ordine"))))

    # --- copia n.2: la ripresa del pentito in compra() --------------
    # (qui la sottrazione da sola e' GIUSTA — art e' il netto, che e'
    # cio' che articolo_sats promette — ed e' la DIVISIONE a dover
    # riaggiungere lo sconto)
    corpo_mono = src[src.index("async def compra("):
                     src.index("def crea_ordine_pagato(")]
    mono_nudo = nudo(codice(corpo_mono))
    prova("copia 2 (ripresa): lo sconto si legge dall'ordine", True,
          nudo('sc = mio["sconto_sats"] or 0') in mono_nudo)
    prova("...e la divisione lo riaggiunge", True,
          nudo('(art + sc) // (mio["quantita"] or 1)') in mono_nudo)

    # --- copia n.3: la riga «N pezzi x unitario» del client ---------
    prova("copia 3 (client): +scontoSats nella divisione", True,
          nudo("(o.listing.price-(o.spedSats||0)-(o.protSats||0)"
               "+(o.scontoSats||0))/o.qta") in nudo(mini_vivo))


# ====================================================================
def prove_forma_sconto_pacco():
    """Le righe che un riordino farebbe sparire senza rompere nessuna
    prova funzionale — e che sono tutto cio' che tiene lo sconto
    carrello dove deve stare: nei quattro percorsi del conto (dall'ago
    2026 il mono sconta), fuori dal payload del compratore, e fuori da
    ogni strada del denaro in USCITA."""
    print("\n[lo sconto carrello: la forma]")
    src = open("server.py", encoding="utf-8").read()

    # 1) UN giudice solo, e i chiamanti sono i quattro percorsi del
    # conto (compra mono, compra set, i due preventivi — ago 2026, il
    # mono sconta): il preventivo e la invoice devono dire la stessa
    # cifra per costruzione, non per disciplina.
    prova("lo sconto ha UN giudice solo", 1, src.count("def _sconto_pacco("))
    # I QUATTRO PERCORSI ORA PASSANO DALL'HELPER (ago 2026, i due
    # criteri insieme): _sconto_regole prende la lista delle gambe vive
    # e ne fa il MAX, cosi' «basta che ne scatti una» vive in un posto
    # solo. La sentinella si e' spostata su di lui e il conto resta
    # QUATTRO — chi ne aggiungesse un quinto, o tornasse a chiamare il
    # giudice singolo dentro un percorso, lo sente dalla CI.
    prova("...e i chiamanti sono i quattro percorsi del conto", 4,
          src.count("= _sconto_regole("))
    prova("l'helper delle gambe e' UNO", 1,
          src.count("def _sconto_regole("))
    # nessun percorso del conto chiama piu' il giudice singolo: le sue
    # due chiamate vive sono dentro _sconto_regole e nella
    # raggiungibilita' del preventivo mono (che e' una LETTURA, non il
    # conto), piu' quella di _regole_sconto sul lettore
    prova("...e nessuno di loro chiama piu' il giudice a una gamba", 0,
          src.count("= _sconto_pacco("))
    prova("il gemello in euro e' UNO", 1,
          src.count("def _sconto_pacco_eur("))
    prova("la regola si legge da UN lettore solo", 1,
          src.count("def _regola_sconto("))
    prova("...e il lettore plurale pure", 1,
          src.count("def _regole_sconto("))
    # 'entrambi' NON E' UNA GAMBA: senza questa riga il lettore singolo
    # lo lascerebbe passare (e' in catalogo) e cadrebbe nel ramo dei
    # PEZZI, misurando una soglia mai promessa da sola.
    prova("il lettore singolo rifiuta esplicitamente i non-gamba", True,
          'criterio not in ("pezzi", "valore")' in pezzo("_regola_sconto"))
    # la guardia di 'entrambi' sta PRIMA del giro sulle gambe, o la sola
    # presenza delle due in catalogo basterebbe a dichiararlo lecito
    _rs = pezzo("_regole_sconto")
    prova("...e la guardia di 'entrambi' viene prima delle gambe", True,
          _rs.index('"entrambi" not in SCONTO_PACCO_CRITERI')
          < _rs.index('gambe = ("pezzi", "valore")'))
    # LA PERCENTUALE E' UNA SOLA: il max e' «almeno una», e il giorno
    # che le percentuali fossero due sarebbe «vince il maggiore» — mai
    # una somma, che bucherebbe SCONTO_PACCO_MAX_PERCENTO.
    prova("le gambe si compongono col MAX, mai con una somma", (True, False),
          ("max(" in pezzo("_sconto_regole"),
           "sum(" in pezzo("_sconto_regole")))
    # IL GEMELLO IN EURO NON DECIDE MAI DA SOLO (ago 2026, col
    # criterio): a valore la porta la apre un numero in SATS, che
    # l'euro non ha. Quindi ogni sua chiamata e' dietro al fratello —
    # se un domani qualcuno lo invocasse nudo, l'euro sconterebbe un
    # carrello che in sats non ha raggiunto la soglia. La riga e'
    # LETTERALE apposta: i due preventivi devono usare la stessa.
    prova("...e si aziona SOLO dietro al fratello in sats (x2)", 2,
          src.count("_sconto_pacco_eur(articolo_eur, pct) if sconto"))
    prova("la regola pubblica passa da UNA pura sola", 1,
          src.count("def _sconto_pubblico("))
    # ...che e' l'unico posto dove vive la regola d'oro della
    # retrocompatibilita': se le due superfici se la scrivessero a
    # mano, basterebbe che una se la dimenticasse
    prova("...e la chiamano le due superfici pubbliche", 2,
          src.count("= _sconto_pubblico("))

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
    corpo_mono = src[src.index("async def compra("):
                     src.index("def crea_ordine_pagato(")]
    for chi, corpo in (("_compra_set", corpo_set),
                       ("compra (mono)", corpo_mono)):
        prova(f"{chi}: lo sconto non si legge dal payload", False,
              any(k in corpo for k in ('d.get("sconto', 'd.get("soglia',
                                       'd.get("percento', 'd.get("totale')))
        prova(f"{chi}: la regola arriva dalla riga del VENDITORE", True,
              "_regole_sconto(" in corpo and "WHERE tg_id=?" in corpo)

    # 4) IL MONO SCONTA (ago 2026, decisione di Andrea che ROVESCIA il
    # 6 ago: tre copie della stessa cosa sono tre pezzi). La divisione
    # a ritroso di _righe_ordine RIAGGIUNGE sconto_sats — una copia
    # senza non fa fallire niente: mostra un unitario storto in
    # ordine, notifiche e CSV, in silenzio. Il censimento delle copie
    # sta in prove_divisione_a_ritroso; qui la forma dei due rami.
    prova("compra (mono): lo sconto c'e'", True,
          "_sconto_regole" in corpo_mono and "sconto_sats" in corpo_mono)
    # ...FINISCE IN COLONNA (senza, la ricevuta e la divisione a
    # ritroso leggerebbero uno sconto che non e' mai stato scritto,
    # e l'ordine racconterebbe un prezzo che il conto non spiega)
    prova("compra (mono): l'INSERT scrive sconto_sats e percento", True,
          "protezione_sats,quantita,sconto_sats,sconto_percento,"
          in corpo_mono)
    # ...e `articolo_sats` e' il NETTO su tutti e due i percorsi mono,
    # come nel set: lordo e sconto sono chiavi in piu' che si sommano
    # da sole — lasciato lordo, il client sottrarrebbe lo sconto DUE
    # volte a occhio e il totale non tornerebbe
    for chi, corpo in (("compra (mono)", corpo_mono),
                       ("preventivo_ordine", pezzo("preventivo_ordine"))):
        prova(f"{chi}: articolo_sats e' il netto", True,
              '"articolo_sats": conto["netto"]' in corpo)
    # ...e la regola si legge FUORI dal gate della spedizione: lo
    # sconto vale anche su ritiro e codice online, e una SELECT
    # rimessa dentro quell'if lo spegnerebbe li' in silenzio
    prova("compra (mono): la regola si legge PRIMA del gate spedizione",
          True, corpo_mono.index("_regole_sconto(")
          < corpo_mono.index('if scelta == "spedizione":'))
    codice_righe = "\n".join(
        r for r in pezzo("_righe_ordine").splitlines()
        if not r.strip().startswith("#"))
    prova("_righe_ordine: la divisione a ritroso riaggiunge lo sconto",
          True, "sconto_sats" in codice_righe)
    prova("crea_ordine_pagato (asta) non sconta", False,
          "sconto" in pezzo("crea_ordine_pagato").split('"""')[-1])

    # 5) LA CIFRA DELLA INVOICE E' LA CIFRA DELL'INSERT. E' il buco da
    # cui uscirebbero i sats DI ALTRI ORDINI: se la bolt11 chiedesse il
    # netto e prezzo_sats finisse col lordo, il payout pretenderebbe
    # dalla cassaforte piu' di quanto quell'ordine ha versato — e la
    # cintura di paga_venditore non lo vedrebbe. Su TUTTI E DUE i rami
    # che coniano (il mono sconta anche lui).
    for chi, corpo in (("_compra_set", corpo_set),
                       ("compra (mono)", corpo_mono)):
        i = corpo.index("crea_invoice_escrow(")
        j = corpo.index("INSERT INTO ordini", i)
        prova(f"{chi}: zero await tra invoice e INSERT", False,
              "await " in codice(corpo[i:j]))
        prova(f"{chi}: il totale non si riscrive li' in mezzo", 0,
              corpo[i:j].count("totale ="))
        prova(f"{chi}: la invoice si conia sul TOTALE", True,
              "crea_invoice_escrow(\n        totale," in corpo)

    # 6) Il tetto di rodaggio giudica il LORDO, PRIMA dello sconto: e'
    # un vincolo del listino, non del checkout — altrimenti si
    # pubblicherebbe sopra il tetto rientrandoci con una regola.
    # Sui QUATTRO percorsi, da quando sono quattro.
    for chi, corpo in (("_compra_set", corpo_set),
                       ("_preventivo_set", pezzo("_preventivo_set")),
                       ("compra (mono)", corpo_mono),
                       ("preventivo_ordine", pezzo("preventivo_ordine"))):
        prova(f"{chi}: il tetto giudica PRIMA dello sconto", True,
              corpo.index("TETTO_SATS_ANNUNCIO")
              < corpo.index("_sconto_regole("))

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
          src.count("sconto_pacco_criterio=?"))
    # LE DUE SOGLIE SI CONSERVANO A VICENDA (il COALESCE): senza, un
    # client vecchio — che di `valore` non sa niente — cancellerebbe a
    # ogni salvataggio una soglia che non ha mai visto
    for col in ("sconto_pacco_soglia", "sconto_pacco_valore_eur"):
        prova(f"...e {col} non si azzera per omissione", 1,
              src.count(f"{col}=COALESCE(?, {col})")
              + src.count(f"{col}=COALESCE(?,{col})"))
    # IL CRITERIO NON SI FOTOGRAFA IN `ordini`: non serve alla ricevuta
    # (il «−10%» c'e' gia'), e sarebbe una colonna nella tabella del
    # denaro per un'informazione ornamentale
    prova("nessuna colonna del criterio sugli ordini", False,
          "sconto_criterio INTEGER" in src or "sconto_criterio TEXT" in src)

    # 9) IL CLIENT MOSTRA, NON CALCOLA: nessuna aritmetica della
    # percentuale, e la cifra del conto viene sempre dal server.
    mini = open("miniapp.html", encoding="utf-8").read()
    import re
    prova("il client non moltiplica mai per la percentuale dello sconto",
          0, len(re.findall(r"\(\s*100\s*-\s*[A-Za-z_.]*[Ss]conto", mini)))
    # L'INVITO NON CALCOLA, RICEVE: il totale glielo passa la barra, che
    # quel numero lo mostra gia' due centimetri piu' sotto — cosi' i due
    # non possono divergere, e qui dentro non si moltiplica mai per la
    # percentuale (quanto si risparmia lo dice il conto del server)
    # la funzione INTERA e non una finestra a lunghezza fissa: un
    # numero magico che tronca fa smettere la prova di provare quel che
    # dice, e in silenzio (successo: la funzione e' cresciuta e «s.pct»
    # e' finito oltre il 1500esimo carattere)
    _i0 = mini.index("function aggiornaInvitoSconto")
    _inv = mini[_i0:mini.index("\n}\n", _i0)]
    prova("l'invito del carrello non ricalcola il totale", False,
          "artStima" in _inv)
    prova("...e non applica mai la percentuale", True,
          "s.pct" in _inv and "* s.pct" not in _inv and "/ 100" not in _inv)
    prova("...e riceve il totale per parametro", True,
          "function aggiornaInvitoSconto(tot){" in mini)
    # L'UNICA conversione del client su una promessa, e dal 13 ago
    # 2026 vive nel GIUDICE statoScontoPacco (lo chiamano badge e
    # totale scontato). Guardata da `cambioVivo`, o la riga direbbe
    # una cifra inventata (il patto del ≈). E il floor, come
    # _eur_interi: nel verso prudente.
    _gsc = pezzo_js(mini, "function statoScontoPacco(tot){", "\n}")
    # LA GUARDIA DEL CAMBIO E' PASSATA PER-GAMBA (ago 2026, i due
    # criteri insieme): torna `null` la gamba che non si sa misurare, e
    # gambaInvito la salta invece di farla valere zero — cosi' a
    # CoinGecko muto un negozio con tutte e due continua a invitare sui
    # PEZZI, dove prima la promessa spariva del tutto. Un `return null`
    # secco qui rimetterebbe quel silenzio.
    prova("il confronto converte in euro solo col cambio vivo", True,
          "cambioVivo ? Math.floor((tot || 0) * eurPerSat) : null" in _gsc)
    prova("...col floor, come il giudice del server", True,
          "Math.floor((tot || 0) * eurPerSat)" in _gsc)
    prova("...e la gamba muta esce dal giro, non vale zero", False,
          "!cambioVivo) return null" in _gsc)
    # IL GIUDICE DELLA REGOLA E' UNO ANCHE NEL CLIENT: sono quattro le
    # superfici che la promessa la mostrano, e basta che una guardi la
    # soglia sbagliata perche' dei sats si leggano come pezzi. Dall'ago
    # 2026 e' PLURALE e il nome singolare non deve tornare: un
    # `regolaSconto` accanto a `regoleSconto` sarebbe il posto in cui
    # una superficie mostra meta' promessa senza che nessuno lo veda.
    prova("il client ha UN giudice solo della regola", 1,
          mini.count("function regoleSconto("))
    prova("...e il nome singolare non e' tornato", 0,
          mini.count("function regolaSconto("))
    # la scelta della gamba da mostrare vive in UN posto: due copie
    # direbbero due strade diverse fra la pagina Paga e il carrello
    prova("...e la scelta della gamba pure", 1,
          mini.count("function gambaInvito("))
    # ---- LE DUE GAMBE NEL CLIENT, riga per riga: sono tutte cose che
    # un riordino toglie senza rompere niente di visibile, e la tortura
    # le ha viste sopravvivere alla prima stesura di queste prove.
    _rg = pezzo_js(mini, "function regoleSconto(", "\n}")
    prova("a 'entrambi' il client apre TUTTE E DUE le gambe", True,
          "c === 'entrambi' ? ['pezzi', 'valore']" in _rg)
    prova("...e a criterio singolo resta quella sola", True,
          "(c === 'pezzi' || c === 'valore') ? [c] : []" in _rg)
    _gi = pezzo_js(mini, "function gambaInvito(", "\n}")
    prova("la gamba SCATTATA vince subito", True,
          "if (m >= r.quanto) return {...r, ora: m, scattato: true};" in _gi)
    prova("...e fra le altre vince chi e' piu' AVANTI", True,
          "const p = m / r.quanto;" in _gi and "if (p > progresso)" in _gi)
    prova("...e la gamba che non si sa misurare ESCE dal giro", True,
          "if (m === null || m === undefined" in _gi and "continue;" in _gi)
    prova("...e UNA sola frase pubblica", 1,
          mini.count("function frasePromessaSconto("))
    # era «restano due» finche' il carrello aveva un riepilogo suo col
    # suo caricatore: dall'ago 2026 il conto si chiede in un posto solo
    prova("il lettore del preventivo resta uno", 1,
          mini.count("fetch(`${API_BASE}/orders/preventivo`"))
    prova("il giudice del ≈ resta UNO anche col meno", 1,
          mini.count("function cifraCtrl"))
    prova("...e il meno sta DENTRO di lui", True,
          "const m = meno ? '−' : '';" in mini)

    # 10) LA CAMPAGNA DEL ROVESCIAMENTO (ago 2026): chi aveva lo sconto
    # acceso viene avvisato che ora vale anche sul mono — una tantum
    # GLOBALE col timbro nella tabella `timbri`, mai un globale in RAM
    # (il patto dei timbri: tre deploy in un'ora, tre notifiche).
    campagna = pezzo("avvisa_sconto_su_mono", fine="\n\n\nasync def")
    prova("la campagna esiste e gira nell'orologio", True,
          "await avvisa_sconto_su_mono()" in src)
    prova("il timbro sta nella tabella timbri", True,
          "timbro_letto(TIMBRO_CAMPAGNA_SCONTO_MONO)" in campagna
          and "timbro_scrivi(TIMBRO_CAMPAGNA_SCONTO_MONO" in campagna)
    prova("...e si scrive PRIMA degli invii (il patto delle campagne)",
          True, campagna.index("timbro_scrivi(")
          < campagna.index("await notifica("))
    prova("la campagna lascia la riga nel journal", True,
          "Campagna «il mono sconta»" in campagna)
    prova("...e bussa solo a chi ha la regola accesa", True,
          "sconto_pacco_percento > 0" in campagna)


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

    # I NOMI (ago 2026): i feedback del negozio non sono piu' anonimi
    # — un voto senza un volto non si puo' pesare. Ma i due confini
    # restano, e sono queste due prove: mai l'oggetto comprato, mai un
    # recapito. Si guarda la QUERY, che e' l'unico posto da cui quei
    # campi potrebbero uscire.
    i = _SORGENTE.index("feedback = [] if cursore else [dict(r)")
    query = _SORGENTE[i:_SORGENTE.index("(v[\"tg_id\"],))]", i)]
    prova("il nome di chi ha votato esce", True, "da_nome" in query)
    prova("la faccia rispetta la scelta «nessuna»", True,
          "avatar_scelta='nessuna'" in query)
    prova("il codice del negozio porta alla sua pagina", True,
          "da_negozio" in query)
    # Se un domani qualcuno facesse un JOIN su annunci per «arricchire»
    # la riga, il titolo dell'oggetto finirebbe in pagina: qui cade
    prova("l'OGGETTO comprato non esce mai", False,
          "titolo" in query or "annunci" in query)
    # Lo @username e la npub stanno sulla pagina del negozio, con le
    # loro regole: qui sarebbero una seconda porta da tenere allineata
    prova("nessun recapito nel payload", False,
          "username" in query or "npub" in query)


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
    prova("il 101esimo e' dei primi giorni", "primi_giorni", coorte(101))
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
    prova("non quello di un'altra coorte", False,
          "coorte_primi_giorni" in t)
    # «Fondatore» non e' una coorte e NON si guadagna: senza il config
    # non ce l'ha nessuno, nemmeno il primo iscritto di tutti
    prova("Fondatore non si guadagna col tempo", False, "t_fondatore" in t)
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

    # I FONDATORI (ago 2026): il titolo arriva dal config, non da un
    # criterio — non e' un traguardo, e' un fatto di due persone. Qui
    # si finge il config, che in CI non esiste.
    amb["FONDATORI"] = (1,)
    t = amb["titoli_disponibili"](con, 1)
    prova("il fondatore ha il suo titolo", True, "t_fondatore" in t)
    t5 = amb["titoli_disponibili"](con, 5)
    prova("...e nessun altro, per quanto anziano", False,
          "t_fondatore" in t5)
    con.close()

    # E il CLIENT non mostra piu' i titoli chiusi: con «Fondatore»
    # irraggiungibile per sempre, un elenco che non si puo' completare
    # non e' una molla ma un dispetto (decisione di Andrea).
    html = open("miniapp.html", encoding="utf-8").read()
    prova("il client non disegna i titoli chiusi", False,
          "Ancora da sbloccare" in html)
    prova("...e non filtra piu' gli sbloccati per scartarli", False,
          "filter(t=>!t.sbloccato)" in html)

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
def _finto_coingecko(chiamate, valore=100000.0, muto=False,
                     usd=110000.0):
    """CoinGecko di cartone: REGISTRA le chiamate invece di farle. Con
    `muto` la rete non risponde — che e' il caso vero del cantiere."""
    import types

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"bitcoin": {"eur": valore, "usd": usd}}

    class C:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, params=None):
            chiamate.append(url)
            if muto:
                raise OSError("rete giù")
            return R()

    return types.SimpleNamespace(AsyncClient=C)


def prove_cambio():
    """IL CAMBIO NON MUORE A UN RIAVVIO (ago 2026, caso vero: due deploy
    a quattordici minuti l'uno dall'altro, CoinGecko muta in tutti e
    due, e un compratore davanti alla pagina d'acquisto bloccata).

    La cache era gia' fail-open e teneva l'ultimo valore noto: il buco
    era che NASCEVA VUOTA. Qui si guardano le tre cose che quel buco lo
    chiudono — il valore sopravvive al riavvio, un buco di rete non lo
    cancella, e adesso ha un'eta' oltre la quale smette di valere."""
    print("\n[cambio BTC/EUR]")
    import asyncio
    import sqlite3
    import time as _time

    def gira(coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    # --- 1) IL GIUDICE PURO ----------------------------------------
    amb = {}
    exec(pezzo("_cambio_valido"), amb)
    val = amb["_cambio_valido"]
    ORA = 1_000_000.0
    prova("cambio fresco: si usa", 99000.0, val(99000.0, ORA - 60, ORA, 24))
    prova("mai letto: non disponibile", 0.0, val(0.0, 0.0, ORA, 24))
    prova("di trenta ore fa: non disponibile", 0.0,
          val(99000.0, ORA - 30 * 3600, ORA, 24))
    # Al filo esatto e' ancora buono, come _asta_viva e in_ferie: la
    # scadenza e' un «oltre», non un «da».
    prova("al filo esatto delle 24 ore vale ancora", 99000.0,
          val(99000.0, ORA - 24 * 3600, ORA, 24))
    prova("un secondo dopo il filo, no", 0.0,
          val(99000.0, ORA - 24 * 3600 - 1, ORA, 24))
    prova("leva a 0: non scade mai (il mondo di ieri)", 99000.0,
          val(99000.0, ORA - 1000 * 3600, ORA, 0))

    # --- 2) IL MONDO: un database vero, la rete di cartone ---------
    def mondo(valore=0.0, quando=0.0, muto=False, ore=24, usd=0.0):
        vero = sqlite3.connect(":memory:")
        vero.row_factory = sqlite3.Row
        vero.execute("CREATE TABLE cambio_noto(valuta TEXT PRIMARY KEY, "
                     "valore REAL DEFAULT 0, quando INTEGER DEFAULT 0)")
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

        chiamate = []
        a = {"db": Con, "time": _time,
             "httpx": _finto_coingecko(chiamate, muto=muto),
             "ORE_CAMBIO_VALIDO": ore, "CAMBIO_TTL": 120,
             "CAMBIO_RIPROVA_S": 60, "VALUTE_CAMBIO": ("eur", "usd"),
             "_cambio_cache": {"valori": {"eur": valore, "usd": usd},
                               "quando": quando, "tentato": 0.0}}
        for f in ("_cambio_valido", "_salva_cambio", "cambio_noto_ora",
                  "cambio_per_import", "carica_cambio_salvato"):
            exec(pezzo(f), a)
        for f in ("_rileggi_cambio", "cambio_btc_eur"):
            exec("async " + pezzo(f), a)
        return a, chiamate, vero

    # --- 3) ANDATA E RITORNO DAL DISCO -----------------------------
    a, _, vero = mondo()
    a["_salva_cambio"]({"eur": 99000.0}, 1_700_000_000)
    riga = vero.execute("SELECT * FROM cambio_noto").fetchone()
    prova("il cambio letto finisce sul disco", (99000.0, 1_700_000_000),
          (riga["valore"], riga["quando"]))
    a["_salva_cambio"]({"eur": 98000.0}, 1_700_000_600)
    prova("...e una riga sola, sempre aggiornata", (1, 98000.0),
          (vero.execute("SELECT COUNT(*) c FROM cambio_noto").fetchone()["c"],
           vero.execute("SELECT valore v FROM cambio_noto").fetchone()["v"]))

    a, _, vero = mondo()          # cache VUOTA: e' esattamente un riavvio
    vero.execute("INSERT INTO cambio_noto VALUES('eur', 99000.0, ?)",
                 (int(_time.time()) - 600,))
    vero.commit()
    prova("all'avvio si riprende dal disco", 99000.0,
          a["carica_cambio_salvato"]())
    prova("...e la cache non e' piu' vuota", 99000.0,
          a["_cambio_cache"]["valori"]["eur"])

    a, _, vero = mondo()
    vero.execute("INSERT INTO cambio_noto VALUES('eur', 99000.0, ?)",
                 (int(_time.time()) - 30 * 3600,))
    vero.commit()
    prova("un cambio salvato trenta ore fa non si usa", 0.0,
          a["carica_cambio_salvato"]())

    # --- 4) LA RETE CADE, IL VALORE RESTA --------------------------
    # E' il caso del cantiere: deploy mentre CoinGecko tace.
    a, chiamate, vero = mondo(muto=True)
    vero.execute("INSERT INTO cambio_noto VALUES('eur', 99000.0, ?)",
                 (int(_time.time()) - 3600,))
    vero.commit()
    a["carica_cambio_salvato"]()
    prova("rete muta dopo un riavvio: vale l'ultimo noto", 99000.0,
          gira(a["cambio_btc_eur"]()))
    prova("...e ci ha davvero provato", 1, len(chiamate))
    prova("...ma non ribussa a ogni richiesta", (99000.0, 1),
          (gira(a["cambio_btc_eur"]()), len(chiamate)))
    prova("...e il buco non ha azzerato niente", 99000.0,
          a["_cambio_cache"]["valori"]["eur"])

    a, _, _ = mondo(valore=99000.0, quando=_time.time() - 30 * 3600,
                    muto=True)
    prova("troppo vecchio e rete muta: non disponibile", 0.0,
          gira(a["cambio_btc_eur"]()))

    a, chiamate, _ = mondo(valore=99000.0, quando=_time.time())
    prova("cambio fresco: nessuna chiamata", (99000.0, 0),
          (gira(a["cambio_btc_eur"]()), len(chiamate)))
    # Oltre la soglia il percorso caldo ci prova ancora — e' la rete di
    # sicurezza se il giro di sfondo si ferma. Non e' una lettura
    # FORZATA al momento della fattura: e' il ripiego di sempre, che il
    # raffreddamento tiene a uno al minuto.
    a, chiamate, _ = mondo(valore=99000.0, quando=_time.time() - 200)
    prova("oltre la soglia il caldo ci riprova (rete di sicurezza)",
          (100000.0, 1), (gira(a["cambio_btc_eur"]()), len(chiamate)))

    a, _, vero = mondo()
    prova("lettura riuscita", 100000.0, gira(a["cambio_btc_eur"]()))
    riga = vero.execute("SELECT valore v FROM cambio_noto").fetchone()
    prova("...e si e' salvata sul disco", 100000.0,
          riga["v"] if riga else None)

    # --- 5) LA FORMA, che e' quella che sparisce in un riordino ----
    prova("ogni lettura riuscita si salva", True,
          "_salva_cambio(valori, adesso)" in pezzo("_rileggi_cambio"))
    prova("la tabella del cambio esiste", True,
          "CREATE TABLE IF NOT EXISTS cambio_noto" in _SORGENTE)
    scalda = pezzo("scalda_cambio")
    prova("all'avvio si riprende dal disco, prima di servire", True,
          "carica_cambio_salvato()" in scalda)
    prova("...e la riprova non fa aspettare l'avvio", True,
          "create_task" in scalda)
    # IL RINFRESCO HA UN GIRO SUO (ago 2026): da quando la fonte e' una
    # sola, la cadenza del server E' la freschezza che vede chiunque
    # guardi un prezzo — dentro l'orologio grande da dieci minuti
    # sarebbe un numero vecchio in mano a tutti.
    giro = pezzo("orologio_cambio")
    prova("il cambio si rilegge nel suo giro, alla sua cadenza", True,
          "await _rileggi_cambio()" in giro
          and "await asyncio.sleep(CAMBIO_RINFRESCO_S)" in giro)
    prova("...e non piu' dentro l'orologio da dieci minuti", False,
          "_rileggi_cambio" in pezzo("orologio"))
    prova("il giro parte all'avvio", True,
          "create_task(orologio_cambio())" in pezzo("scalda_cambio"))
    prova("un giro morto non si rialza: c'e' la cintura", True,
          "except Exception as e:" in giro)
    # LA SOGLIA E' DERIVATA dalla cadenza, non un secondo numero da
    # tenere in pari: se fosse piu' STRETTA della cadenza, il percorso
    # caldo tornerebbe a chiamare la rete a ogni giro.
    i = _SORGENTE.index("CAMBIO_TTL = max(")
    riga = _SORGENTE[i:_SORGENTE.index("\n", i)]
    for cadenza, atteso in ((60, 120), (30, 120), (300, 600), (0, 120)):
        a = {"CAMBIO_RINFRESCO_S": cadenza}
        exec(riga, a)
        prova(f"soglia derivata: cadenza {cadenza}s → {atteso}s", atteso,
              a["CAMBIO_TTL"])
        prova(f"...e mai piu' stretta della cadenza ({cadenza}s)", True,
              a["CAMBIO_TTL"] >= cadenza)
    # NESSUNA lettura forzata al momento della fattura: nel percorso
    # caldo la rete si tocca in UN posto solo, e dietro il freno.
    caldo = pezzo("cambio_btc_eur")
    prova("nel percorso caldo la rete si tocca una volta sola", 1,
          caldo.count("_rileggi_cambio"))
    prova("...e sempre dietro il raffreddamento", True,
          caldo.index("CAMBIO_RIPROVA_S") < caldo.index("_rileggi_cambio"))

    # --- 6) L'IMPORT BEVE ALLA STESSA FONTE ------------------------
    # Era la seconda verita' rimasta in piedi, e si e' fatta vedere nel
    # journal: alle 14:52:33 il server legge 56.313, alle 14:52:57
    # l'import dice «Cambio BTC non disponibile». Due letture, due
    # esiti, per convertire gli stessi bitcoin — e quella dell'import
    # viveva DENTRO importa_venditore, che il giro chiama una volta per
    # VENDITORE: una raffica di chiamate a ogni giro.
    a, _, _ = mondo(valore=99000.0, quando=_time.time(), usd=110000.0)
    prova("il cambio per l'import esce nella forma che vuole lui",
          {"EUR": 99000.0, "USD": 110000.0}, a["cambio_per_import"]())
    a, _, _ = mondo(valore=99000.0, quando=_time.time())
    prova("...e porta solo cio' che e' davvero utilizzabile",
          {"EUR": 99000.0}, a["cambio_per_import"]())
    a, _, _ = mondo(valore=99000.0, quando=_time.time() - 30 * 3600,
                    usd=110000.0)
    prova("...troppo vecchio: vuoto, come una lettura fallita",
          {}, a["cambio_per_import"]())
    # LA STESSA ETA' per le due valute: arrivano dalla stessa GET,
    # quindi invecchiano insieme e `quando` e' UNO.
    a, _, vero = mondo()
    gira(a["_rileggi_cambio"]())
    righe = {r["valuta"]: r["quando"]
             for r in vero.execute("SELECT * FROM cambio_noto")}
    prova("euro e dollaro sul disco, con la stessa eta'", 1,
          len(set(righe.values())))
    prova("...e sono le due valute", {"eur", "usd"}, set(righe))
    # L'EURO COMANDA: e' lui che fa le invoice.
    a, _, _ = mondo()
    a["httpx"] = _finto_coingecko([], valore=0.0)
    prova("senza euro la lettura non vale, dollaro o no",
          (False, 0.0), (gira(a["_rileggi_cambio"]()),
                         a["_cambio_cache"]["valori"]["eur"]))

    imp = open("importa_nostr.py", encoding="utf-8").read()
    prova("l'import accetta il cambio dal server", True,
          "vaglio=None, scarica=None,\n                      cambio=None"
          in imp)
    prova("...e lo script a mano resta identico (cambio=None)", True,
          "elif cambio is None:" in imp and "cambio = cambio_btc()" in imp)
    prova("...un cambio VUOTO non passa in silenzio", True,
          "elif not cambio:" in imp and "print(MSG_CAMBIO_MANCANTE)" in imp)
    prova("il messaggio del cambio mancante vive in un posto solo", 1,
          imp.count('MSG_CAMBIO_MANCANTE = ('))
    prova("...e lo dicono tutte e due le strade", 3,   # def + 2 usi
          imp.count("MSG_CAMBIO_MANCANTE"))
    giro_imp = pezzo("importa_nostr_periodico")
    prova("il server legge il cambio UNA volta per giro, fuori dal for",
          1, giro_imp.count("cambio_per_import()"))
    i_letto = giro_imp.index("cambio_import = cambio_per_import()")
    i_for = giro_imp.index("for npub, venditore_id in")
    prova("...e prima del giro dei venditori", True, i_letto < i_for)

    # UNA SOLA FONTE: il client non chiama piu' CoinGecko per conto suo.
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client non chiama piu' CoinGecko da solo", 0,
          mini.count("api.coingecko.com"))
    prova("...lo prende dalla busta della vetrina", 1,
          mini.count("impostaCambio(j.cambio_eur)"))
    prova("...e la vetrina legge la cache, mai la rete", True,
          'risposta["cambio_eur"] = cambio_noto_ora()' in _SORGENTE)
    prova("il cambio assente non diventa un numero inventato", True,
          "if (v <= 0) return;"
          in pezzo_js(mini, "function impostaCambio(", "\n}\n"))

    # --- 5) IL CONTROVALORE DI UN ORDINE E' QUELLO DEL SUO GIORNO
    #        (ago 2026). Un affare di luglio dice quanto valeva a
    #        luglio: il cambio se lo porta l'ordine, e il cambio di
    #        OGGI qui dentro non deve entrare mai.
    resa = pezzo_js(mini, "function _resaCifraOrdine(", "\n}\n")
    # LA PROVA REGINA, e non nomina nessun caso: se in questa funzione
    # comparisse `eurPerSat` — il cambio vivo della vetrina — un affare
    # concluso cambierebbe valore ogni mattina. E' il difetto che tutto
    # il cantiere esiste per togliere, in una riga sola.
    prova("la cifra di un ordine non guarda il cambio di oggi", False,
          "eurPerSat" in resa)
    prova("...guarda quello che l'ordine si porta dietro", True,
          "o.cambioOrdine" in resa)
    # ...e senza, restano i sats: mai un ripiego su oggi
    prova("...e senza cambio non converte", True,
          "!(o.cambioOrdine > 0)" in resa)
    # LA RESA VIVE IN UN POSTO SOLO: la lista e la scheda sono la
    # stessa cifra vista da due posti, e due rese un giorno direbbero
    # due numeri (il patto di `cifraCtrl`).
    prova("la resa e' una sola", 1, mini.count("function _resaCifraOrdine("))
    # i due chiamanti si nominano per esteso e non si CONTANO: la
    # definizione contiene la stessa forma della chiamata, e a contare
    # la prova guardava tre cose credendo di guardarne due
    prova("...e la usa l'involucro", True,
          "${_resaCifraOrdine(o, sats, nuda)}" in mini)
    prova("...e la usa il toggle", True,
          "_resaCifraOrdine(o, +n.dataset.sats" in mini)
    # L'INVOLUCRO AVVOLGE, NON RENDE: una seconda strada per scrivere
    # la cifra qui dentro non la vedrebbe il conto delle rese — e' la
    # mutazione che era rimasta verde, e il modo piu' facile di far
    # divergere lista e scheda e' proprio un ramo in piu' qui.
    prova("l'involucro non scrive cifre per conto suo", False,
          "fmt" in pezzo_js(mini, "function cifraOrdine(", "\n}\n"))
    # IL TOGGLE NON RIAPRE L'ORDINE: riaprirlo butterebbe via il
    # tracciamento a meta' o il codice appena incollato — la ragione
    # per cui esiste aggiornaCifreOrdine invece di un openOrder.
    agg = pezzo_js(mini, "function aggiornaCifreOrdine(", "\n}\n")
    prova("il toggle riscrive in place, non riapre", False, "openOrder" in agg)
    prova("...e setValuta se ne ricorda", True,
          "aggiornaCifreOrdine();" in pezzo_js(mini, "function setValuta(", "\n}\n"))
    # LA CIFRA OPERATIVA RESTA IN SATS: nel pannello d'incasso il
    # numero e' l'importo della invoice da incollare, e la cintura di
    # paga_venditore lo confronta al sat. In euro si incollerebbe
    # l'importo sbagliato.
    prova("il pannello d'incasso non passa dal toggle", False,
          "cifraOrdine(" in pezzo_js(mini, "function payoutPanel(", "\n}\n"))
    # e il dato dev'esserci: senza, ogni ordine sarebbe «senza cambio»
    prova("mapOrder porta il cambio dell'ordine", True,
          "cambioOrdine:o.cambio_ordine" in mini)
    # la riga onesta esiste nel markup (nasce nascosta: la accende il
    # giro delle cifre, che e' anche quello che la rispegne)
    prova("la riga «non abbiamo il cambio» esiste", True,
          'id="ordineSenzaCambio"' in mini)
    # e la cifra non si spezza: «≈», numero e unita' sono un gruppo
    # solo, o il simbolo resta appeso in fondo alla riga di sopra
    prova("la cifra di un ordine non va a capo a meta'", True,
          ".cifra-ord{white-space:nowrap}" in mini)


def prove_recupero_cambi():
    """Lo strumento che recupera il cambio del giorno degli ordini di
    prima (ago 2026). Gira A MANO sul VPS, su `ordini`, cioe' la
    tabella dei soldi: qui si sorveglia il PERIMETRO — cosa tocca e
    cosa no — che e' l'unica cosa che una prova puo' dire di uno
    script che parla con l'esterno."""
    src = open("recupera_cambi_ordini.py", encoding="utf-8").read()
    corpo = src.split('"""', 2)[-1]

    # SCRIVE UNA COLONNA SOLA, e non lo si verifica con un elenco di
    # nomi: si estraggono TUTTE le scritture del corpo e si guarda
    # dove vanno a finire. Cosi' un `UPDATE ordini SET stato=...`
    # infilato qui dentro fra sei mesi non ha bisogno di essere
    # previsto per essere preso (la lezione della prova regina del
    # ritiro offerta).
    scritture = re.findall(r"UPDATE\s+(\w+)\s+SET\s+(\w+)", corpo)
    prova("il recupero scrive in un posto solo", [("ordini", "cambio_ordine")],
          scritture)
    for parola in ("INSERT", "DELETE", "DROP"):
        prova(f"il recupero non {parola.lower()}", False, parola in corpo)

    # ...e solo dove il cambio non c'e': e' cio' che lo rende
    # ripetibile e interrompibile, e che gli impedisce di riscrivere
    # un cambio VERO (quello di un ordine in euro) con lo snapshot
    # del giorno, che e' meno preciso.
    prova("...e solo dove il cambio manca ancora", True,
          "WHERE cambio_ordine = 0" in corpo)

    # L'ANTEPRIMA NON SPENDE CHIAMATE: e' la promessa scritta nella
    # docstring, ed e' verificabile per POSIZIONE — l'unica chiamata a
    # CoinGecko sta dopo l'uscita anticipata di `if not scrivi`.
    # (si cerca la CHIAMATA e non il nome: la definizione della
    # funzione contiene la stessa stringa, e con quella la prova
    # guardava la riga sbagliata — e non poteva che essere rossa)
    chiamata = corpo.find("= cambio_del_giorno(")
    uscita = corpo.find("if not scrivi:")
    prova("la chiamata a CoinGecko e' una sola",
          1, corpo.count("= cambio_del_giorno("))
    prova("...e sta dopo l'uscita dell'anteprima", True,
          0 < uscita < chiamata)

    # LA CINTURA sulla cifra: una risposta malformata non entra nella
    # tabella dei soldi. Zero compreso — `if not eur` sopra — ma qui
    # si guarda la scala.
    prova("una cifra fuori scala non si scrive", True,
          "MIN_PLAUSIBILE <= eur <= MAX_PLAUSIBILE" in corpo)

    # NON IMPORTA server.py, la lezione di ricategorizza: l'import
    # farebbe partire init_db e le migrazioni, magari su un database
    # diverso da quello passato a mano.
    prova("il recupero non importa il server", False, "import server" in corpo)
    # il config si chiede DENTRO main(), o in CI (dove config.py non
    # c'e' per progetto) il modulo non si potrebbe nemmeno leggere
    prova("...e il config non lo chiede all'avvio", True,
          "    from config import DB" in corpo)


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
                 "SCONTO_PACCO_SOGLIE", "SCONTO_PACCO_SCONTI",
                 "SCONTO_PACCO_VALORI_EUR", "SCONTO_PACCO_VALORI_SATS",
                 "SCONTO_PACCO_CRITERI", "VALUTE_SOGLIA",
                 "SPED_GRATIS_SOGLIE_EUR", "SPED_GRATIS_SOGLIE_SATS"):
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
                 "GIORNI_DATA_ANNUNCIO", "ORE_CAMBIO_VALIDO",
                 "CAMBIO_RINFRESCO_S", "TETTO_DIGITALE_NUOVI",
                 "DIGITALE_MIN_VENDITE", "SUGGERIMENTI_DI_SERIE",
                 "SUGGERIMENTI_OGNI_GIORNI", "PROMO_GIORNI_VENDITORE",
                 "POST_LAMPO_CANALE", "RIEPILOGO_SETTIMANALE",
                 "RIEPILOGO_MINIMO"):
        amb[nome] = acceso and 24
    # Il canale non si legge piu' dalla costante: dall'ago 2026 lo
    # decide il bot e il giudice e' `canale_id()`, che va a leggere il
    # database. Qui si stuba — al pannello interessa il FATTO, e
    # trascinare dentro una connessione renderebbe questa prova
    # dipendente da un file su disco, che e' esattamente il tipo di
    # prova che diventa rossa per conto suo.
    amb["canale_id"] = (lambda: "@canale_finto") if acceso else (lambda: "")
    # Il RITMO del canale, per la stessa ragione del canale: dall'ago
    # 2026 lo decide `/vetrina` e i giudici vanno a leggere il
    # database. Il pannello DEVE chiamare loro e non le costanti — la
    # prova «il pannello dice il ritmo EFFETTIVO» piu' sotto vive
    # proprio su questi stub, che dicono numeri che nessuna costante
    # del config finto potrebbe dire.
    amb["ritmo_vetrina"] = ((lambda: (1, 2, 3)) if acceso
                            else (lambda: (0, 0, 0)))
    amb["nome_ritmo"] = (lambda: "giorno") if acceso else (lambda: "")
    amb["SPIEGA_RITMO"] = {"giorno": "uno al giorno per venditore"}
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


def prove_canale_bot():
    """IL CANALE E IL BOT CHE SFOGLIA (ago 2026).

    Quattro famiglie, e la prima e' quella che decide: il freno del
    canale — un post per venditore a settimana, e fra i suoi il piu'
    recente — perche' e' l'unico pezzo di questo cantiere che DECIDE
    qualcosa invece di limitarsi a scrivere del testo."""
    print("\n[il canale e il bot che sfoglia]")
    import html

    # --- 1) UN POST PER VENDITORE A SETTIMANA --------------------
    import time as _time
    amb = {"time": _time}
    exec(pezzo("_un_post_per_venditore"), amb)
    filtro = amb["_un_post_per_venditore"]
    ora = 1_000_000_000

    def ann(i, v, creato, ultimo=0):
        return {"id": i, "venditore_id": v, "creato": creato,
                "promo_canale_il": ultimo}

    uno = filtro([ann(1, 10, 100), ann(2, 10, 200), ann(3, 10, 150)], 7, ora)
    prova("tre annunci dello stesso venditore diventano uno", 1, len(uno))
    prova("e vince il PIU' RECENTE", 2, uno[0]["id"])
    due = filtro([ann(1, 10, 100), ann(2, 20, 100)], 7, ora)
    prova("venditori diversi non si tolgono il posto", 2, len(due))
    # il tie-break: due annunci nello stesso secondo esistono davvero
    pari = filtro([ann(7, 10, 100), ann(9, 10, 100)], 7, ora)
    prova("a pari secondo comanda l'id piu' alto", 9, pari[0]["id"])
    # il timbro: chi ha gia' avuto il turno tace fino alla scadenza
    ieri = ora - 86400
    prova("chi ha postato ieri resta fuori",
          [], filtro([ann(1, 10, 100, ieri)], 7, ora))
    otto = ora - 8 * 86400
    prova("chi ha postato otto giorni fa rientra",
          1, len(filtro([ann(1, 10, 100, otto)], 7, ora)))
    filo = ora - 7 * 86400
    prova("al filo esatto dei sette giorni rientra",
          1, len(filtro([ann(1, 10, 100, filo)], 7, ora)))
    prova("chi non ha mai postato entra sempre",
          1, len(filtro([ann(1, 10, 100, 0)], 7, ora)))
    # l'ordine di arrivo si conserva: la coda e' cronologica
    misto = filtro([ann(1, 10, 100), ann(2, 20, 300), ann(3, 10, 500)], 7, ora)
    prova("l'ordine della coda si conserva", [2, 3],
          [a["id"] for a in misto])
    # IL FRENO A ZERO (la posizione «tutto»): nessun freno, nemmeno
    # quello del «uno per venditore» — si riconosce che e' una
    # posizione della vetrina e non una taratura.
    prova("freno a 0: nessun freno, passa tutto",
          3, len(filtro([ann(1, 10, 100, ora), ann(2, 10, 200),
                         ann(3, 10, 300)], 0, ora)))
    # A UN GIORNO: chi ha postato ieri rientra, chi ha postato adesso no.
    prova("a un giorno chi ha postato ieri rientra",
          1, len(filtro([ann(1, 10, 100, ieri)], 1, ora)))
    prova("...e chi ha postato adesso resta fuori",
          [], filtro([ann(1, 10, 100, ora)], 1, ora))
    # LA FIRMA NON HA DEFAULT, ed e' la lezione di `atteso_sats`: il
    # ritmo lo sceglie il chiamante, e chi se lo dimentica lo sente da
    # Python invece di ereditare in silenzio il freno sbagliato.
    try:
        filtro([ann(1, 10, 100)])
        senza = "passata"
    except TypeError:
        senza = "TypeError"
    prova("chiamarla senza il freno e' un errore", "TypeError", senza)

    # --- 2) LA CAPTION DEL CANALE --------------------------------
    cap = {"html": html, "URL_PUBBLICO": "https://barattolo.store"}
    for f in ("_fmt_sats", "_fmt_eur", "_prezzo_promo", "_slug_categoria",
              "_hashtag_promo", "_firma_venditore", "_caption_canale"):
        exec(pezzo(f), cap)
    a = {"id": 42, "titolo": "Chitarra classica", "prezzo_sats": 80000,
         "valuta": "sats", "zona": "Torino (TO)", "categoria": "Strumenti musicali",
         "venditore": "Alan", "venditore_username": "AlanBimbati",
         "venditore_negozio": "abc12345"}
    t = cap["_caption_canale"](a, 0)
    prova("il titolo c'e' in grassetto", True,
          "<b>Chitarra classica</b>" in t)
    prova("il prezzo c'e'", True, "80.000 sats" in t)
    prova("«Pagabile in Satoshi» c'e'", True, "Pagabile in Satoshi" in t)
    prova("il link e' un'ancora «Apri su Barattolo»", True,
          '<a href="https://barattolo.store/annuncio/42">🫙 Apri su '
          'Barattolo</a>' in t)
    # IL PUNTO DEL CANTIERE: l'URL non si vede in chiaro da nessuna
    # parte. Si contano le occorrenze fuori dagli href — un URL nudo
    # rimasto in coda sarebbe passato dalla prova qui sopra.
    nudi = re.sub(r'href="[^"]*"', "", t)
    prova("nessun URL nudo nel post", False, "https://" in nudi)
    prova("la firma nomina l'@username", True,
          "Annuncio da <b>@AlanBimbati</b>" in t)
    prova("e porta al negozio con un'ancora", True,
          '<a href="https://barattolo.store/negozio/abc12345">vedi il '
          'suo negozio</a>' in t)
    prova("la categoria esce come hashtag", True,
          "#strumentimusicali" in t and "#barattolo" in t)
    prova("il ✅ Venduto si aggiunge in coda", True,
          cap["_caption_canale"](a, 0, venduto=True).endswith("✅ Venduto"))

    # Il venditore SENZA username (i nativi Nostr): niente «@», o
    # nascerebbe una menzione che Telegram non sa risolvere.
    b = dict(a, venditore_username="", venditore="Soddisfatto Cliente")
    t2 = cap["_caption_canale"](b, 0)
    prova("senza username niente chiocciola", False, "@" in t2)
    prova("e si usa il nome", True,
          "Annuncio da <b>Soddisfatto Cliente</b>" in t2)
    # senza codice negozio niente link: porterebbe a un 404
    t3 = cap["_caption_canale"](dict(a, venditore_negozio=""), 0)
    prova("senza codice negozio niente ponte", False, "/negozio/" in t3)

    # L'ESCAPE, che qui non e' pignoleria: il titolo lo scrive
    # l'utente e la caption e' HTML — un «<» spegnerebbe il post in
    # silenzio, ed e' la lezione gia' pagata coi promemoria.
    cattivo = cap["_caption_canale"](
        dict(a, titolo="<b>SVENDO</b> & fuggo",
             venditore_username="", venditore="<i>Tizio</i>"), 0)
    prova("il titolo dell'utente passa da escape", True,
          "&lt;b&gt;SVENDO&lt;/b&gt; &amp; fuggo" in cattivo)
    prova("e cosi' il nome del venditore", True,
          "&lt;i&gt;Tizio&lt;/i&gt;" in cattivo)

    # --- 3) LA GRIGLIA DELLE CATEGORIE ---------------------------
    # L'OTTAVA COPIA del catalogo: le emoji del bot devono dire le
    # stesse cose di quelle della Mini App, o la griglia di Telegram e
    # quella di Sfoglia mostrerebbero due reparti diversi con lo
    # stesso nome. E' la rete di CATEGORIE_SENZA_CONDIZIONE.
    amb2 = {}
    i = _SORGENTE.index("EMOJI_CATEGORIA = {")
    exec(_SORGENTE[i:_SORGENTE.index("}", i) + 1], amb2)
    server_em = amb2["EMOJI_CATEGORIA"]
    mini = open("miniapp.html", encoding="utf-8").read()
    j = mini.index("const EMOJI_CAT = {")
    client_em = dict(re.findall(r"'([^']+)':'([^']+)'",
                                mini[j:mini.index("};", j)]))
    prova("le emoji del bot e quelle della Mini App combaciano",
          client_em, server_em)
    i = _SORGENTE.index("CATEGORIE = (")
    amb2["CATEGORIE"] = None
    exec(_SORGENTE[i:_SORGENTE.index(")", i) + 1], amb2)
    prova("e coprono tutto il catalogo",
          sorted(amb2["CATEGORIE"]), sorted(server_em))

    # La tastiera: due colonne, ordine FISSO del catalogo, e l'INDICE
    # nel callback_data (64 byte scarsi, e il nome ci starebbe stretto).
    amb2["EMOJI_CATEGORIA"] = server_em
    amb2["URL_PUBBLICO"] = "https://barattolo.store"
    exec(pezzo("_riga_webapp"), amb2)
    exec(pezzo("tastiera_categorie"), amb2)
    tast = amb2["tastiera_categorie"]()["inline_keyboard"]
    prova("la Mini App e' la PRIMA riga di tastiera", True,
          tast[0][0]["url"] == "https://barattolo.store")
    griglia = tast[1:]
    prova("due colonne", True, all(len(r) <= 2 for r in griglia))
    prova("c'e' ogni categoria", len(amb2["CATEGORIE"]),
          sum(len(r) for r in griglia))
    prova("nell'ordine del catalogo", amb2["CATEGORIE"][0],
          griglia[0][0]["text"].split(" ", 1)[1])
    dati = [v["callback_data"] for r in griglia for v in r]
    prova("il callback_data sta nei 64 byte", True,
          all(len(d.encode()) <= 64 for d in dati))
    prova("e porta l'INDICE, non il nome", "sfo:0:0", dati[0])

    # --- 4) LA MINI APP VIENE PRIMA ------------------------------
    # La regola di prodotto, e per questo e' una prova e non una
    # buona intenzione: il bottone verso Barattolo e' esattamente la
    # riga che si dimentica nella tastiera aggiunta fra sei mesi.
    exec(pezzo("tastiera_bot"), amb2)
    for nome, t in (("vuota", amb2["tastiera_bot"]()),
                    ("con altre righe", amb2["tastiera_bot"](
                        [[{"text": "x", "callback_data": "y"}]]))):
        prova(f"tastiera {nome}: la Mini App e' in cima", True,
              t["inline_keyboard"][0][0]["url"] == "https://barattolo.store")
    sorgente_bot = pezzo("gestisci_update")
    prova("/start non elenca comandi, invita ad aprire", True,
          "tastiera_bot()" in sorgente_bot and "/canale" not in
          sorgente_bot.split("if testo.startswith(\"/canale\")")[0]
          .split("return await bot_api")[1])
    prova("chi scrive altro riceve comunque i bottoni", True,
          "sfo:menu:0" in sorgente_bot.rsplit("reply_markup", 1)[1]
          or "sfo:menu:0" in sorgente_bot)

    # --- 5) IL CANALE HA UN GIUDICE SOLO -------------------------
    # Se un giorno divergessero, il ✅ Venduto finirebbe in un canale e
    # il post originale in un altro.
    # E' un CENSIMENTO e non un elenco (la lezione del titolo nudo, e
    # qui e' servita subito: dall'ago 2026 le funzioni che scrivono nel
    # canale sono SEI e questa lista ne diceva quattro). Si guarda
    # tutto il file e si chiede che la COSTANTE del config non si
    # nomini in nessuna funzione tranne il giudice, che la usa come
    # valore di partenza, e il pannello, che ne mostra il nome. Chi
    # scrivera' un post nuovo fra sei mesi entra nel conto da solo.
    # I corpi si prendono da pezzo(), che taglia alla riga vuota
    # doppia: affettare «da un def al successivo» si porterebbe dentro
    # i commenti di modulo che stanno in mezzo, e questa prova
    # nominerebbe funzioni che quella parola non l'hanno mai vista.
    def _corpo(n):
        try:                      # l'ultima funzione del file non ha
            return pezzo(n)       # due righe vuote dopo di se'
        except ValueError:
            return _SORGENTE[_SORGENTE.index(f"def {n}("):]

    _corpi = {n: _corpo(n) for n in set(re.findall(
        r"(?m)^(?:async )?def ([a-z_][a-z_0-9]*)\(", _SORGENTE))}
    prova("la costante del canale si nomina solo dove deve",
          {"canale_id", "_leve_stato"},
          {n for n, c in _corpi.items() if "TELEGRAM_CANALE_ID" in c})
    # ...e ogni funzione che POSTA nel canale passa dal giudice.
    for f in ("_posta_promo_singolo", "_posta_promo_aggregato",
              "promo_lampo", "riepilogo_settimana"):
        prova(f"{f} scrive col giudice", True,
              'chat_id": canale_id()' in pezzo(f))
    # L'ELENCO e non il conto: se qualcuno apre una settima bocca sul
    # canale, il diff di questa prova la NOMINA invece di dire «7 != 6»
    # e mandare a cercarla a mano.
    prova("chi parla col canale e' questo e basta",
          {"_posta_promo_singolo",    # l'annuncio nuovo
           "_posta_promo_aggregato",  # la valvola delle raffiche
           "promo_lampo",             # lo sconto a tempo
           "promo_venduto",           # il ✅ sul post gia' fatto
           "promo_rimuovi",           # il post cancellato
           "riepilogo_settimana",     # il lunedi'
           "comando_canale"},         # che il canale lo DICE, non ci posta
          {n for n, c in _corpi.items()
           if "canale_id()" in c and "bot_api(" in c})
    # La caption RICOSTRUITA deve avere la firma: senza il JOIN il
    # post riscritto col ✅ perderebbe il venditore che aveva da nuovo.
    prova("promo_venduto rilegge anche il venditore", True,
          "venditore_username" in pezzo("promo_venduto"))
    prova("e cosi' il drenatore", True,
          "venditore_negozio" in pezzo("_drena_promo"))
    # Il timbro PRIMA dell'invio, il patto delle campagne.
    corpo = pezzo("_posta_promo_singolo")
    prova("il timbro del turno si scrive PRIMA di postare", True,
          corpo.index("promo_canale_il") < corpo.index("bot_api"))

    # --- 6) I COMANDI DI SERVIZIO SONO DEI DUE ADMIN -------------
    amb3 = {}
    exec(pezzo("e_admin"), amb3)
    amb3.update(ADMIN_IDS=[555], MODALITA_COLLAUDO=False)
    exec("ADMIN_BOT_USERNAME = " + repr(("alanbimbati", "aandreaiita")), amb3)
    exec(pezzo("e_admin_bot"), amb3)
    ok = amb3["e_admin_bot"]
    prova("i due username passano", True,
          ok({"id": 1, "username": "AlanBimbati"})
          and ok({"id": 2, "username": "aandreaiita"}))
    prova("maiuscole comprese", True, ok({"id": 1, "username": "ALANBIMBATI"}))
    prova("i moderatori di sempre passano", True, ok({"id": 555}))
    prova("un estraneo no", False, ok({"id": 3, "username": "tizio"}))
    prova("e nemmeno chi non ha username", False, ok({"id": 3}))
    # l'username si prende dal MESSAGGIO e non dalla riga `utenti`:
    # quella potrebbe portarne uno vecchio, magari gia' preso da un
    # altro. La firma dice tutto: riceve il mittente, non un tg_id.
    prova("giudica il mittente, non un id", True,
          "mittente" in pezzo("e_admin_bot").split("\n")[0])
    # la risposta al non-admin non deve MAI dire «non sei
    # autorizzato»: direbbe a un curioso che quel comando esiste. Si
    # guarda il corpo, non la docstring, che la parola la spiega.
    corpo_canale = pezzo("comando_canale").split('"""')[2]
    prova("chi non e' admin non impara che il comando esiste", False,
          "autorizzat" in corpo_canale.lower())
    prova("il canale si prova prima di crederci", True,
          pezzo("comando_canale").index('"chat_id": arg')
          < pezzo("comando_canale").index("imposta_canale(arg)"))
    # IL RECINTO DELLE IMPOSTAZIONI, che e' da NON allargare: mai
    # segreti (finiscono nei backup) e mai leve del DENARO — quelle
    # nascono spente nel codice apposta, perche' accenderle costi un
    # gesto dal VPS.
    # E' un CENSIMENTO e non un conteggio (la lezione del titolo nudo):
    # si estraggono le chiavi VERE dal sorgente e si chiede che siano
    # quelle dichiarate qui. Un `<= 2` diceva quante volte si legge,
    # non COSA — e sarebbe passato liscio davanti a una riga nuova che
    # ne sostituisce una vecchia. Chi ne aggiunge una la scrive qui, e
    # nel farlo si rilegge la regola.
    RECINTO = {"canale_telegram",   # dove parla il bot  (`/canale`)
               "ritmo_vetrina"}     # quanto parla       (`/vetrina`)
    chiavi = set(re.findall(r'\bimpostazione\("([a-z_]+)"', _SORGENTE))
    chiavi |= set(re.findall(r'\bscrivi_impostazione\("([a-z_]+)"',
                             _SORGENTE))
    prova("nel recinto delle impostazioni ci sono solo le chiavi note",
          RECINTO, chiavi)


def prove_vetrina_canale():
    """IL CANALE DIVENTA LA VETRINA (ago 2026, chiesto da Andrea).

    Tre cantieri in uno, e ognuno ha la sua famiglia qui sotto: il
    RITMO che si decide dal bot invece che dal config, lo SCONTO LAMPO
    raccontato nel canale, e il RIEPILOGO del lunedi'.

    La prova che decide e' l'ultima: il riepilogo gira DAVVERO tre
    volte su tre ambienti diversi con lo stesso database sotto — cioe'
    tre deploy — e deve parlare una volta sola. E soprattutto deve
    TIMBRARE ANCHE QUANDO TACE, che e' il contrario del termometro:
    li' il conto e' cumulativo e saltare il turno lo rimanda, qui il
    conto e' di una settimana precisa e ricontrollare martedi' darebbe
    una finestra sfasata."""
    print("\n[il canale diventa la vetrina]")
    import asyncio as _aio
    import html as _html
    import sqlite3
    import time as _time

    # --- 1) I GIUDICI DEL RITMO ----------------------------------
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE impostazioni(chiave TEXT PRIMARY KEY, "
                "valore TEXT DEFAULT '')")
    con.commit()

    class ConFinta:
        def __getattr__(self, n):
            return getattr(con, n)

        def close(self):
            pass                  # su :memory: chiuderebbe il database

    amb = {"db": lambda: ConFinta(), "sqlite3": sqlite3,
           # i valori del CONFIG, riconoscibili: se un giudice li
           # restituisce vuol dire che nessuna posizione e' in vigore
           "PROMO_GIORNI_VENDITORE": 7, "POST_MAX_ORA": 6,
           "SOGLIA_AGGREGA": 3}
    for f in ("impostazione", "scrivi_impostazione", "nome_ritmo",
              "ritmo_vetrina", "imposta_ritmo"):
        exec(pezzo(f), amb)
    # RITMI e' un dizionario di modulo, non una funzione: si prende dal
    # sorgente per testo, come i cataloghi.
    _ritmi_src = _SORGENTE[_SORGENTE.index("RITMI = {"):]
    exec(_ritmi_src[:_ritmi_src.index("\n}") + 2], amb)
    RITMI = amb["RITMI"]

    prova("le posizioni sono tre", {"tutto", "giorno", "settimana"},
          set(RITMI))
    prova("«tutto» non ha freno per venditore", 0, RITMI["tutto"][0])
    prova("«giorno» ne ha uno", 1, RITMI["giorno"][0])
    # SENZA RIGA VALE IL CONFIG, cioe' il mondo di ieri byte per byte:
    # e' la retrocompatibilita' di questo cantiere, ed e' la riga che
    # si rompe per prima se qualcuno mette un default nel giudice.
    prova("nessuna posizione: i numeri del config", (7, 6, 3),
          amb["ritmo_vetrina"]())
    prova("...e il nome e' vuoto, non «settimana»", "", amb["nome_ritmo"]())
    amb["imposta_ritmo"]("tutto")
    prova("scelta «tutto»: i suoi numeri", RITMI["tutto"],
          amb["ritmo_vetrina"]())
    prova("...e il nome lo dice", "tutto", amb["nome_ritmo"]())
    prova("le maiuscole non contano", "giorno", amb["imposta_ritmo"]("GIORNO"))
    # FAIL-SAFE: un nome fuori catalogo — scritto a mano sul VPS, o
    # rimasto da una posizione tolta — non deve poter spegnere il
    # canale: si ricade sul config.
    amb["scrivi_impostazione"]("ritmo_vetrina", "fantasia")
    prova("nome storto: si ricade sul config", (7, 6, 3),
          amb["ritmo_vetrina"]())
    prova("...e il nome torna vuoto", "", amb["nome_ritmo"]())
    prova("imposta_ritmo rifiuta un nome storto", "",
          amb["imposta_ritmo"]("fantasia"))
    prova("«config» annulla la scelta", "", amb["imposta_ritmo"]("config"))
    # UN SOLO LETTORE della riga: nome_ritmo. Se anche ritmo_vetrina
    # andasse a leggerla, i due potrebbero divergere fra una SELECT e
    # l'altra e il pannello direbbe una posizione coi numeri di
    # un'altra.
    prova("la riga la legge solo nome_ritmo", True,
          'impostazione("ritmo_vetrina"' in pezzo("nome_ritmo")
          and 'impostazione("ritmo_vetrina"' not in pezzo("ritmo_vetrina"))

    # --- 2) IL DRENATORE USA IL GIUDICE, NON LE COSTANTI ---------
    dre = codice(pezzo("_drena_promo"))
    prova("il drenatore chiede il ritmo al giudice", True,
          "ritmo_vetrina()" in dre)
    for k in ("PROMO_GIORNI_VENDITORE", "POST_MAX_ORA", "SOGLIA_AGGREGA"):
        prova(f"...e non nomina {k}", False, k in dre)
    # UNA VOLTA SOLA in cima al giro: un `/vetrina` che arriva a meta'
    # drenaggio non deve far uscire mezzo gruppo con una regola e
    # mezzo con un'altra.
    prova("il ritmo si legge una volta sola", 1, dre.count("ritmo_vetrina()"))
    # ...e i tre numeri li USA davvero. Senza queste due righe, un
    # confronto con una costante scritta a mano passerebbe liscio: le
    # tre prove qui sopra guardano che le COSTANTI non si nominino,
    # non che al loro posto ci siano i valori del giudice — l'ha detto
    # la tortura, non la rilettura.
    prova("la soglia dell'aggregato viene dal ritmo", True,
          "len(annunci) <= soglia_aggrega" in dre)
    prova("...e cosi' il tetto orario", True, "<= max_ora" in dre)
    prova("...e il freno per venditore", True,
          "_un_post_per_venditore(annunci, giorni)" in dre)
    # e il timbro del turno lo RICEVE, non se lo rilegge. Si guarda il
    # corpo DOPO la docstring: quella il giudice lo nomina apposta per
    # spiegare da dove arriva, e una sentinella che ci inciampa dentro
    # si fa aggiustare riscrivendo la prosa invece del codice.
    sing = codice(pezzo("_posta_promo_singolo").split('"""')[2])
    prova("chi posta riceve il freno dal chiamante", True,
          "giorni > 0" in sing and "ritmo_vetrina" not in sing)

    # --- 3) LO SCONTO LAMPO NEL CANALE ---------------------------
    pl = {"html": _html, "URL_PUBBLICO": "https://barattolo.store"}
    for f in ("_fmt_sats", "_fmt_eur", "_prezzo_promo", "_prezzo_lampo",
              "_riga_prezzo_lampo"):
        exec(pezzo(f), pl)
    a_sats = {"prezzo_sats": 80000, "prezzo_eur": 0.0, "valuta": "sats"}
    riga = pl["_riga_prezzo_lampo"](a_sats, 20, 0)
    prova("il listino e' barrato", True, "<s>80.000 sats</s>" in riga)
    prova("...e accanto c'e' lo scontato", True, "<b>64.000 sats</b>" in riga)
    # SUL LISTINO IN EURO lo sconto vale anche sull'equivalente in
    # sats: la stessa percentuale sulle due facce, o la riga direbbe
    # due sconti diversi.
    a_eur = {"prezzo_sats": 80000, "prezzo_eur": 40.0, "valuta": "eur"}
    riga_eur = pl["_riga_prezzo_lampo"](a_eur, 25, 0)
    prova("in euro si barra l'euro", True, "<s>40,00 €" in riga_eur)
    prova("...e lo scontato e' l'euro scontato", True, "<b>30,00 €" in riga_eur)
    prova("...e i sats sono scontati con lui", True, "60.000 sats" in riga_eur)
    lam = codice(pezzo("promo_lampo"))
    # SOLO CANALE, NIENTE NOSTR: lo sconto e' locale, e il NIP-99 parla
    # il prezzo pieno per costruzione — e' una regola gia' scritta.
    prova("la lampo non finisce su Nostr", False,
          "_spedisci_ai_relay" in lam or "firma_evento" in lam)
    # LE GUARDIE DI CHI POSTA, tutte e tre: un negozio chiuso o un
    # annuncio importato non si annunciano in piazza.
    for guardia in ("stato", "contatto_nostr", "in_ferie"):
        prova(f"la lampo guarda {guardia}", True, guardia in lam)
    prova("...e che la lampo sia ancora viva", True, "lampo_scadenza" in lam)
    # IL BUDGET ORARIO: senza, il tetto dei post si aggirerebbe
    # lanciando sconti (MAX_LAMPO_SETTIMANA e' 2 *per annuncio*).
    prova("la lampo consuma il budget orario", True,
          "_post_promo_recenti.append" in lam)
    prova("...e a budget pieno salta invece di aggregare", True,
          "ritmo_vetrina()[1]" in lam and "_posta_promo_aggregato" not in lam)
    # IL TITOLO SCAPPATO: le notifiche sono HTML e un «<» spegne il
    # messaggio in silenzio (la lezione dell'avviso di spedizione).
    prova("il titolo della lampo e' scappato", True,
          "html.escape(a['titolo'])" in lam)
    # e il gancio: DOPO il commit e in create_task, il patto di
    # accoda_promo — un post fallito non rompe il lancio di uno sconto
    lan = codice(pezzo("lancia_lampo"))
    prova("il gancio e' un create_task", True,
          "asyncio.create_task(promo_lampo(" in lan)
    prova("...e sta dopo il commit", True,
          lan.index("con.commit()") < lan.index("promo_lampo("))

    # --- 4) IL RIEPILOGO: I CONTI --------------------------------
    con.executescript("""
        CREATE TABLE annunci(id INTEGER PRIMARY KEY, titolo TEXT,
                             creato INTEGER, stato TEXT);
        CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INTEGER,
                            quantita INTEGER, stato TEXT, creato INTEGER);
        CREATE TABLE ordine_righe(ordine_id INTEGER, annuncio_id INTEGER,
                                  titolo TEXT, quantita INTEGER);
        CREATE TABLE timbri(nome TEXT PRIMARY KEY, valore TEXT DEFAULT '',
                            quando INTEGER DEFAULT 0);
    """)
    ora = 1_000_000_000
    da = ora - 7 * 86400
    for i, (tit, quando, stato) in enumerate([
            ("Miele di castagno", ora - 86400, "attivo"),
            ("Cuffie AKG", ora - 2 * 86400, "attivo"),
            ("Jade", ora - 3 * 86400, "venduto"),
            ("Roba tolta", ora - 86400, "rimosso"),
            ("In attesa", ora - 86400, "revisione"),
            ("Vecchio", da - 86400, "attivo")], start=1):
        con.execute("INSERT INTO annunci VALUES(?,?,?,?)",
                    (i, tit, quando, stato))
    # tre ordini mono sul miele (uno pagato x3, uno pagato x1) e uno
    # ancora 'creato', che NON conta: li' i sats non sono in cassaforte
    con.execute("INSERT INTO ordini VALUES(1,1,3,'locked',?)", (ora - 3600,))
    con.execute("INSERT INTO ordini VALUES(2,1,1,'released',?)", (ora - 7200,))
    con.execute("INSERT INTO ordini VALUES(3,2,9,'creato',?)", (ora - 60,))
    con.execute("INSERT INTO ordini VALUES(4,2,9,'annullato',?)", (ora - 60,))
    # un SET: la testata ha annuncio_id=0 e la merce sta nelle righe
    con.execute("INSERT INTO ordini VALUES(5,0,3,'shipped',?)", (ora - 1800,))
    con.execute("INSERT INTO ordine_righe VALUES(5,2,'Cuffie AKG',2)")
    con.execute("INSERT INTO ordine_righe VALUES(5,3,'Jade',1)")
    # un ordine fuori finestra: non deve entrare in nessun conto
    con.execute("INSERT INTO ordini VALUES(6,1,50,'released',?)",
                (da - 3600,))
    con.commit()
    amb2 = {}
    exec(pezzo("_conta_settimana"), amb2)
    nuovi, ordini, top = amb2["_conta_settimana"](con, da)
    # gli stati che sono stati in vetrina DAVVERO: il venduto ci entra
    # (e' stato un annuncio vero, e' solo finito), rimosso e revisione no
    prova("gli annunci nuovi sono gli attivi e i venduti", 3, nuovi)
    # i sats in cassaforte: il complemento di 'creato' e 'annullato'
    prova("gli ordini sono quelli pagati", 3, ordini)
    prova("la classifica ha tre voci", 3, len(top))
    prova("in testa il miele con 4 pezzi",
          ("Miele di castagno", 4), (top[0]["titolo"], top[0]["pezzi"]))
    # IL SET CONTA: la sua merce vive nelle righe, e i mono non hanno
    # righe MAI — guardare solo le righe perderebbe quasi tutto
    prova("le cuffie contano i pezzi del set",
          ("Cuffie AKG", 2), (top[1]["titolo"], top[1]["pezzi"]))
    prova("e la Jade ne ha uno", ("Jade", 1), (top[2]["titolo"], top[2]["pezzi"]))
    # IL PAREGGIO E' STABILE: due articoli con gli stessi pezzi non si
    # scambiano di posto a ogni chiamata.
    prova("il pareggio non balla",
          [t["annuncio_id"] for t in top],
          [t["annuncio_id"] for t in
           amb2["_conta_settimana"](con, da)[2]])
    _cs = codice(pezzo("_conta_settimana"))
    prova("il pareggio si rompe sull'id", True,
          "ORDER BY pezzi DESC, annuncio_id DESC" in _cs)
    prova("_conta_settimana legge e basta", True,
          not any(k in _cs.upper() for k in
                  ("INSERT ", "UPDATE ", "DELETE ")))

    # --- 5) IL RIEPILOGO: TRE DEPLOY, UN POST --------------------
    class TempoFinto:
        """Un lunedi' fisso: il gate del calendario deve restringere il
        giorno, e dentro il giorno a decidere e' il timbro."""

        def __init__(self, wday=0):
            self.wday = wday

        def time(self):
            return ora

        def strftime(self, f, *a):
            return "2026-08-10"

        def localtime(self, *a):
            return type("t", (), {"tm_wday": self.wday})()

    mandati = []

    async def bot_api_finta(metodo, dati):
        mandati.append(dati)
        return {"ok": True, "result": {"message_id": 1}}

    def processo(wday=0, minimo=3):
        """UN DEPLOY: ambiente nuovo, database vecchio."""
        a = {"db": lambda: ConFinta(), "time": TempoFinto(wday),
             "html": _html, "print": lambda *x, **k: None,
             "bot_api": bot_api_finta, "canale_id": lambda: "@vetrina",
             "URL_PUBBLICO": "https://barattolo.store",
             "RIEPILOGO_SETTIMANALE": True, "RIEPILOGO_MINIMO": minimo,
             "TIMBRO_RIEPILOGO": "riepilogo_settimana"}
        for f in ("timbro_letto", "timbro_scrivi", "_conta_settimana"):
            exec(pezzo(f), a)
        # pezzo() taglia dal «def», quindi l'«async » va rimesso a mano
        exec("async " + pezzo("riepilogo_settimana"), a)
        return a

    for _ in range(3):
        _aio.run(processo()["riepilogo_settimana"]())
    prova("tre deploy nello stesso lunedi': UN post solo", 1, len(mandati))
    testo = mandati[0]["text"]
    prova("il post va nel canale", "@vetrina", mandati[0]["chat_id"])
    prova("dice gli annunci nuovi", True, "🫙 3 nuovi annunci" in testo)
    prova("dice gli ordini", True, "🛒 3 ordini" in testo)
    prova("e la classifica col ×N solo dove serve", True,
          "Miele di castagno ×4 · Cuffie AKG ×2 · Jade" in testo)
    prova("niente ×1 su chi ne ha venduto uno", False, "Jade ×1" in testo)
    # NON DI LUNEDI' non si parla, e non si consuma nemmeno il turno
    mandati.clear()
    con.execute("DELETE FROM timbri")
    con.commit()
    _aio.run(processo(wday=2)["riepilogo_settimana"]())
    prova("di mercoledi' non esce niente", 0, len(mandati))
    prova("...e il turno non si consuma", 0,
          con.execute("SELECT COUNT(*) FROM timbri").fetchone()[0])

    # --- 6) LA SETTIMANA MAGRA: TACE, MA TIMBRA ------------------
    # E' il contrario del termometro, ed e' la riga che si sbaglia per
    # prima: li' il conto e' CUMULATIVO e saltare il turno lo rimanda,
    # qui il conto e' di una SETTIMANA e ricontrollare martedi' darebbe
    # una finestra sfasata.
    con.execute("DELETE FROM ordini")
    con.execute("DELETE FROM annunci WHERE id>1")
    con.execute("DELETE FROM timbri")
    con.commit()
    mandati.clear()
    _aio.run(processo(minimo=3)["riepilogo_settimana"]())
    prova("settimana magra: non esce niente", 0, len(mandati))
    prova("...ma il turno SI CONSUMA lo stesso", "2026-08-10",
          con.execute("SELECT valore FROM timbri WHERE nome=?",
                      ("riepilogo_settimana",)).fetchone()[0])
    # e con la soglia abbassata quella stessa settimana parla
    con.execute("DELETE FROM timbri")
    con.commit()
    _aio.run(processo(minimo=1)["riepilogo_settimana"]())
    prova("con la soglia bassa la stessa settimana parla", 1, len(mandati))
    prova("...e senza ordini la riga degli ordini non c'e'", False,
          "🛒" in mandati[0]["text"])
    # IL TITOLO SCAPPATO, che qui sono tre in un colpo solo
    rs = codice(pezzo("riepilogo_settimana"))
    prova("i titoli della classifica sono scappati", True,
          "html.escape(t[" in rs)
    prova("il riepilogo non finisce su Nostr", False,
          "_spedisci_ai_relay" in rs or "firma_evento" in rs)


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
    # IL RITMO DEL CANALE DEV'ESSERE QUELLO EFFETTIVO, non le costanti
    # del config: dall'ago 2026 lo decide `/vetrina` dal bot, e leggere
    # le costanti direbbe lo stato di ieri — la trappola che questa
    # pagina esiste per non far ricadere. I numeri arrivano dallo stub
    # di `ritmo_vetrina` (1, 2, 3) e nessuna costante del config finto
    # puo' dirli: se qualcuno rimette POST_MAX_ORA & co., qui si vede.
    # LA TORTURA L'HA CHIESTA: senza queste righe la mutazione che
    # riportava il pannello alle costanti non faceva rossa una prova.
    prova("il pannello dice i giorni del giudice",
          1, voci_on["PROMO_GIORNI_VENDITORE"]["valore"])
    prova("...e i post all'ora del giudice",
          2, voci_on["POST_MAX_ORA"]["valore"])
    prova("...e la soglia dell'aggregato del giudice",
          3, voci_on["SOGLIA_AGGREGA"]["valore"])
    prova("la posizione del ritmo si dice col suo nome",
          "giorno", voci_on["/vetrina"]["valore"])
    prova("...e senza posizione si dice «config»",
          "config", voci_off["/vetrina"]["valore"])
    prova("il percorso del database non e' una leva",
          False, "DB" in voci_on)

    # --- 2) LA FORMA ---------------------------------------------
    prova("ogni gruppo ha delle voci", True,
          all(g["voci"] for g in gruppi_on) and len(gruppi_on) >= 8)
    prova("ogni voce ha nome, chiave e valore", True,
          all(v.get("nome") and v.get("chiave") and "valore" in v
              for v in voci_on.values()))
    # La chiave e' il NOME della cosa da andare a cambiare, mai il suo
    # valore — un segreto finito li' dentro si vedrebbe da qui. Dalla
    # voce del ritmo (ago 2026) e' ammesso anche un COMANDO del bot,
    # perche' quella la si cambia da li' e mandare qualcuno sul VPS
    # sarebbe un indirizzo sbagliato: `/nome` di sole lettere, cosi'
    # un percorso di file (che comincia anche lui con «/») non passa.
    def chiave_lecita(c):
        return (c.isupper() or c.startswith("_")
                or (c.startswith("/") and c[1:].isalpha()))

    prova("le chiavi sono nomi di config o comandi, non valori", True,
          all(chiave_lecita(c) for c in voci_on))
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


def prove_posizione_vetrina():
    """Tornando indietro la vetrina riparte da dove si era (ago 2026).
    La griglia non si perde MAI — il markup delle pagine caricate resta
    nel DOM per tutto il tempo — quindi qui non c'e' niente da
    ricaricare: si sorveglia solo che la POSIZIONE si salvi e si
    rilegga nei momenti giusti. Sono tutte righe che sparirebbero in un
    riordino senza rompere niente di visibile, ed e' esattamente il
    tipo di riga che va guardata."""
    print("\n[dove si era rimasti in vetrina]")
    mini = open("miniapp.html", encoding="utf-8").read()
    go = pezzo_js(mini, "function go(view){", "\n}\n")

    # --- 1) SI SALVA PRIMA DI SPEGNERE, ed e' LA trappola ---------
    # Un istante dopo il display:none il documento si accorcia e il
    # browser clampa lo scorrimento a zero: chi spostasse questo blocco
    # sotto il remove('active') salverebbe sempre zero, e il ritorno
    # tornerebbe a partire dalla cima senza che nessuna prova si
    # accorga di niente.
    i_salva = go.index("vetrinaPos = {")
    i_spegni = go.index("classList.remove('active')")
    prova("la posizione si salva PRIMA del display:none", True,
          i_salva < i_spegni)
    prova("si salva solo lasciando la VETRINA", True,
          "'view-esplora'" in go[:i_salva])
    # Il conto delle card viaggia con la posizione: e' la cintura che
    # al ritorno dice se la griglia e' ancora quella.
    prova("con la posizione si salva anche il conto delle card", True,
          "el('grid').children.length" in go[i_salva:i_salva + 200])

    # --- 2) IL RIPRISTINO E' UNO SOLO ------------------------------
    # go() aveva uno scrollTo(0,0) nudo in coda: se qualcuno lo
    # rimettesse accanto al giudice, vincerebbe l'ultimo e il ritorno
    # non si vedrebbe piu'.
    prova("in go() nessuno scrollTo nudo", True,
          "scrollTo(0,0)" not in go and "scrollTo(0, 0)" not in go)
    prova("lo scorrimento passa dal giudice unico", 1,
          go.count("posizioneDaRendere("))
    prova("il giudice esiste una volta sola", 1,
          mini.count("function posizioneDaRendere("))

    giudice = pezzo_js(mini, "function posizioneDaRendere(view){", "\n}\n")
    # --- 3) SOLO TORNANDO INDIETRO ---------------------------------
    # `navApplicando` e' la sola cosa che distingue un ritorno da un
    # ingresso nuovo. Senza, il tocco sul tab Esplora mentre si e' gia'
    # in Esplora non riporterebbe piu' in cima, e la tirata di
    # aggiornamento nemmeno.
    prova("si ripristina SOLO ri-applicando una entry", True,
          "navApplicando" in giudice)
    prova("e solo se la griglia e' ancora quella", True,
          "vetrinaPos.n === el('grid').children.length" in giudice)
    prova("solo la vetrina ha una posizione da ritrovare", True,
          "'esplora'" in giudice
          and not any(v in giudice for v in
                      ("'negozio'", "'affari'", "'profilo'", "'miei'")))

    # --- 4) LA CINTURA DEL GIRO NUOVO ------------------------------
    # Il conto delle card da solo non basta: due vetrine diverse
    # possono averne 30 e 30. Chi ricarica la PRIMA pagina — la tirata
    # di aggiornamento, il cambio categoria, i filtri, la ricerca —
    # butta la posizione, e quello e' un giro nuovo, non un ritorno.
    carica = pezzo_js(mini, "async function loadListings(anonimo){", "\n}\n")
    prova("una ricarica di prima pagina butta la posizione", True,
          "vetrinaPos = null" in carica)
    prova("la butta accanto al giro, prima di ogni await", True,
          carica.index("vetrinaPos = null") < carica.index("await fetch"))

    # --- 5) LO SCORRIMENTO LO DECIDIAMO NOI ------------------------
    # Di serie il browser prova a rimetterlo lui a ogni traversata, e
    # con l'URL che non cambia mai le sue entry si somigliano tutte:
    # il suo tentativo arriverebbe dopo il nostro.
    motore = pezzo_js(mini, "function navMotore(){", "\n}\n")
    prova("il ripristino del browser resta spento", True,
          "history.scrollRestoration = 'manual'" in motore)

    # --- 6) NEMMENO IL FOCUS TRASCINA LA PAGINA --------------------
    # Trovato di striscia, ed era li' da sempre: il campo-bottone
    # «Ordina» vive in cima alla vetrina, quindi il focus che torna al
    # campo alla chiusura del picker ce la riportava — stessa
    # frustrazione del cantiere, per un'altra strada. I chiamanti sono
    # DUE (closeSheet e chiudiPicker) e devono restare allineati.
    prova("il focus del picker non scorre, in tutti i suoi chiamanti", 0,
          mini.count("pickerTrigger.focus();"))
    prova("...e sono due, entrambi con preventScroll", 2,
          mini.count("pickerTrigger.focus({preventScroll:true})"))


# ====================================================================
def prove_impersonazione():
    """CHI SI FINGE BARATTOLO (ago 2026, M1 dell'audit). Da quando
    esistono le anteprime dei link, /annuncio/{id} e' una scheda col
    nome Barattolo su un indirizzo di Barattolo, dove titolo,
    descrizione e immagine li sceglie chi pubblica: «Barattolo —
    verifica il tuo pagamento in sospeso» condiviso da li' e' un
    messaggio che sembra ufficiale, e chi lo riceve non ha NESSUN
    segnale per distinguerlo.

    Il verdetto lo da' un modello, quindi qui non si prova che l'AI
    risponda giusto — la chiave Anthropic sta fuori dalla CI apposta,
    e una prova che dipende da un server altrui e' un oroscopo. Si
    prova che LA VOCE ESISTA e che le tre cose che la tengono
    onesta siano ancora scritte: il divieto, il perimetro (titolo E
    descrizione) e la CONTRO-REGOLA — nominare Barattolo e' lecito —
    che e' quella che un riordino toglie per prima perche' sembra un
    ripensamento. Il collaudo col modello vero e' collaudo_
    impersonazione.py, che vuole la chiave."""
    print("\n[chi si finge Barattolo]")
    i = _SORGENTE.index("PROMPT_MODERAZIONE = (")
    # Le stringhe spezzate su piu' righe si RICUCIONO prima di
    # cercare: e' nella piega — «'venduto tramite "» a capo «"Barattolo'»
    # — che una frase si nasconde a chi la cerca, ed e' la lezione
    # gia' pagata dalla sentinella dei sats.
    prompt = re.sub(r'"\s*\n\s*"', "",
                    _SORGENTE[i:_SORGENTE.index("\n\n\n", i)])

    # --- 1) la voce c'e', ed e' un divieto -------------------------
    prova("il prompt nomina l'impersonazione", True,
          "IMPERSONAZIONE" in prompt)
    prova("...e la mette fra i casi netti, non fra i dubbi", True,
          "Ai casi netti si aggiunge l'IMPERSONAZIONE" in prompt)
    prova("...nominando le tre cose per cui ci si puo' spacciare",
          True, all(p in prompt for p in
                    ("la piattaforma", "moderatori", "altro servizio")))

    # --- 2) il perimetro: l'annuncio si giudica INTERO -------------
    # og:title viene dal titolo e og:description dalla descrizione,
    # quindi un divieto scritto sul solo titolo lascerebbe aperta
    # meta' della card. Ma NON si giudicano separatamente, e la
    # differenza e' costata un falso positivo (vedi il punto 3bis):
    # la prima stesura diceva «vale sul TITOLO come sulla
    # DESCRIZIONE», e il modello ha letto la descrizione da sola.
    prova("l'annuncio si giudica intero, non campo per campo", True,
          "Giudica l'annuncio INTERO" in prompt)
    prova("...e l'oggetto puo' stare nel solo titolo", True,
          "l'oggetto puo' stare nel solo TITOLO" in prompt)
    prova("...ma il titolo pulito non salva la descrizione", True,
          "avvelena l'annuncio anche quando il titolo e' pulito"
          in prompt)

    # --- 3) LA CONTRO-REGOLA, che e' la meta' delicata -------------
    # Un divieto sull'impersonazione senza il permesso di NOMINARE la
    # piattaforma e' un filtro sulla parola «Barattolo», cioe' un
    # blocco su annunci legittimi e comunissimi. Deve restare scritto
    # che citare non e' mai di per se' un motivo, e devono restare gli
    # esempi: sono loro a insegnare il confine.
    prova("citare Barattolo resta lecito, a chiare lettere", True,
          "non e' MAI di per" in prompt and "non il citarla" in prompt)
    for legittimo in ("gadget di Barattolo", "venduto tramite Barattolo",
                      "regolamento Barattolo", "negozio Barattolo"):
        prova(f"...con l'esempio «{legittimo}»", True, legittimo in prompt)

    # --- 3bis) IL FALSO POSITIVO CHE ABBIAMO PAGATO PER TROVARE ----
    # Primo giro del collaudo col modello vero, 14/15: «Bicicletta da
    # corsa Bianchi» la cui DESCRIZIONE spiega come funziona l'escrow
    # e' uscita VIETATO col motivo «non descrive l'oggetto in
    # vendita» — ma l'oggetto c'e', e' una bici, sta nel titolo. La
    # causa era mia: avevo scritto «e non descrive nessun oggetto in
    # vendita» dentro la definizione del VIETATO, e il modello l'ha
    # presa per un test sufficiente da applicare alla sola
    # descrizione. Tre righe lo chiudono, e vanno tenute tutte e tre.
    prova("raccontare come funziona Barattolo e' dichiarato LECITO",
          True, "RACCONTARE come funziona Barattolo" in prompt
          and "non e' MAI impersonazione" in prompt)
    prova("...perche' chi spiega l'escrow RASSICURA chi compra", True,
          "RASSICURANDO" in prompt)
    prova("...e il divieto colpisce chi SI RIVOLGE al lettore", True,
          "SI RIVOLGE A CHI LEGGE" in prompt)
    # la regola che il modello aveva scavalcato, adesso dichiarata
    # sovrana e con l'uscita esplicita per l'annuncio prolisso
    prova("la cosa in vendita VINCE sulle altre regole", True,
          "LA REGOLA CHE VINCE SULLE ALTRE" in prompt
          and "una COSA in vendita" in prompt)
    prova("...e un annuncio prolisso e' OK, non impersonazione", True,
          "un annuncio prolisso e' OK" in prompt)
    # ...senza pero' diventare una scappatoia: il caso avvelenato ha
    # anche lui una cosa in vendita, e a distinguerlo e' la seconda
    # meta' della condizione
    prova("...ma solo se al lettore non si chiede NIENTE", True,
          "non si chiede di verificare, sbloccare o confermare NIENTE"
          in prompt.replace("\n", " "))
    # LA COPPIA DI ESEMPI: due descrizioni che nominano tutt'e due
    # Barattolo e finiscono in due esiti opposti. E' il modo in cui un
    # prompt insegna un confine — la regola astratta da sola non era
    # bastata.
    prova("l'esempio della bici (il falso positivo) e' nel prompt",
          True, "Bicicletta da corsa Bianchi" in prompt
          and "finche' non confermi di aver ricevuto la bici' -> OK"
          in prompt)
    prova("...col suo gemello avvelenato che resta VIETATO", True,
          "scrivi a @supporto per sbloccare l'ordine' -> VIETATO"
          in prompt)
    prova("...e la coppia dice che l'oggetto non basta a salvarlo",
          True, "non lo salva il fatto che le cuffie ci siano" in prompt)

    # --- 4) i tre esempi, uno per esito ----------------------------
    # Il prompt insegna per esempi, e questi tre sono le tre risposte
    # possibili sullo STESSO nome: OK chi cita, DUBBIO chi si intesta
    # un ruolo, VIETATO chi finge un messaggio.
    prova("l'esempio che cita il mercatino finisce in OK", True,
          "Adesivi e gadget di Barattolo, lotto da 10' -> OK" in prompt)
    prova("...chi si intesta un ruolo va in DUBBIO", True,
          "supporto agli utenti' -> DUBBIO" in prompt)
    prova("...e il finto messaggio e' VIETATO", True,
          "verifica il tuo pagamento in sospeso' -> VIETATO" in prompt)

    # --- 5) L'IMPORT IN BLOCCO LA EREDITA --------------------------
    # 500 righe di CSV passano da moderazione_ai_lotto, che NON ha un
    # prompt suo: e' lo stesso piu' l'appendice sul formato. Se un
    # domani i due si sdoppiassero, la strada da cui entrano gli
    # annunci a centinaia resterebbe scoperta — e in silenzio.
    lotto = pezzo("moderazione_ai_lotto")
    prova("il lotto non ha un prompt suo: eredita quello del singolo",
          True, "PROMPT_MODERAZIONE + APPENDICE_LOTTO" in lotto)
    prova("...e il singolo pure", True,
          "system=PROMPT_MODERAZIONE," in pezzo("moderazione_ai"))

    # --- 6) il verdetto si legge, e non finisce nel messaggio
    #        sbagliato ---------------------------------------------
    # CHI ESTRAE UNA FUNZIONE NE EREDITA LE DIPENDENZE: da quando il
    # vietato passa dal declassamento, _leggi_verdetto non vive piu'
    # da sola (la lezione di reale() e di _fmt_sats).
    import unicodedata as _u
    amb = {"MODERAZIONE_REVISIONE": True, "re": re, "unicodedata": _u}
    for ancora in ("def normalizza(", "PAROLE_BLOCCANTI = ",
                   "PREFISSI_BLOCCANTI = ", "def _vietato_bloccante("):
        i = _SORGENTE.index(ancora)
        exec(_SORGENTE[i:_SORGENTE.index("\n\n\n", i)], amb)
    exec(pezzo("_leggi_verdetto"), amb)
    # QUESTA PROVA HA CAMBIATO LATO (ago 2026), ed e' l'affermazione
    # piu' forte delle due: chiedeva che «VIETATO: impersonazione»
    # fosse un rifiuto SECCO — cioe' certificava il comportamento che
    # ha fermato un venditore vero. Adesso quel verdetto va in CODA:
    # l'AI segnala, l'umano decide. (Il precedente e' la sentinella
    # del reaper sui 'creato', e quella degli avatar.)
    prova("«VIETATO: impersonazione» va in CODA, non nel rifiuto",
          ("dubbio", "impersonazione della piattaforma"),
          amb["_leggi_verdetto"]("VIETATO: impersonazione della "
                                 "piattaforma"))
    prova("...e il dubbio del ruolo intestato resta un dubbio",
          ("dubbio", "si intesta un ruolo che non ha"),
          amb["_leggi_verdetto"]("DUBBIO: si intesta un ruolo che non ha"))
    # ...mentre un'arma resta un no secco: e' una delle quattro
    # famiglie dove il rifiuto e' giusto anche se il modello sbaglia
    prova("un'arma resta un rifiuto secco",
          ("vietato", "arma da fuoco funzionante"),
          amb["_leggi_verdetto"]("VIETATO: arma da fuoco funzionante"))
    # --- 7) e il rifiuto dice COSA ha sbagliato -------------------
    # Prima l'impersonazione si prendeva la lista delle armi e delle
    # droghe, che non c'entra niente. Adesso ha il suo messaggio, e
    # deve dire anche DOV'E' IL CONFINE: qui e' sottile e non ovvio —
    # nominare il mercatino va benissimo, parlare a nome suo no.
    amb2 = {}
    for costante in ("MSG_RIFIUTO = (", "MSG_RIFIUTO_SERVIZI = (",
                     "MSG_RIFIUTO_IMPERSONAZIONE = (",
                     "PAROLE_IMPERSONAZIONE = ("):
        j = _SORGENTE.index(costante)
        exec(_SORGENTE[j:_SORGENTE.index("\n\n", j)], amb2)
    exec(pezzo("messaggio_rifiuto"), amb2)
    rifiuto = amb2["messaggio_rifiuto"]
    prova("chi si e' spacciato per noi ha il messaggio suo",
          amb2["MSG_RIFIUTO_IMPERSONAZIONE"],
          rifiuto("impersonazione della piattaforma"))
    prova("...che dice il confine, non l'elenco delle armi", True,
          "nominare il mercatino va benissimo" in
          amb2["MSG_RIFIUTO_IMPERSONAZIONE"]
          and "droghe" not in amb2["MSG_RIFIUTO_IMPERSONAZIONE"])
    # l'AI scrive il motivo con parole sue: le varianti ragionevoli
    # devono cadere tutte nello stesso ramo
    # «finto» NON e' una declinazione di «finge» — sono due parole, e
    # a dirlo e' stata questa riga: la prima stesura della lista non
    # lo prendeva, e il caso qui sotto passava dai servizi.
    for variante in ("si finge Barattolo", "fingersi la piattaforma",
                     "fingendosi il supporto", "finto avviso di sicurezza",
                     "impersona un corriere",
                     "si spaccia per un moderatore",
                     "phishing mascherato da annuncio"):
        prova(f"...anche detto «{variante}»",
              amb2["MSG_RIFIUTO_IMPERSONAZIONE"], rifiuto(variante))
    # LA RIGA CHE DECIDE L'ORDINE dei due rami, e senza questa prova
    # sarebbe invisibile: il motivo puo' nominare un servizio proprio
    # perche' quello e' cio' per cui ci si finge. Col ramo dei servizi
    # davanti, a chi ha provato a spacciarsi per noi risponderemmo
    # «i servizi non sono ancora supportati».
    prova("«finto servizio clienti» e' impersonazione, non un servizio",
          amb2["MSG_RIFIUTO_IMPERSONAZIONE"],
          rifiuto("finto servizio clienti di Barattolo"))
    # e le due strade di sempre non si sono mosse
    prova("i servizi veri tengono il loro garbo",
          amb2["MSG_RIFIUTO_SERVIZI"], rifiuto("servizio su commissione"))
    prova("...i servizi sessuali il messaggio severo",
          amb2["MSG_RIFIUTO"], rifiuto("servizi sessuali mascherati"))
    prova("...e le armi la lista di sempre",
          amb2["MSG_RIFIUTO"], rifiuto("arma da fuoco"))


# ====================================================================
def prove_avviso_spedizione():
    """L'AVVISO DI SPEDIZIONE CHE SPARIVA IN SILENZIO (ago 2026, B6
    dell'audit). Le notifiche sono HTML, corriere e tracciamento sono
    testo del VENDITORE: un «<» nel nome del corriere fa fallire il
    parse di Telegram, e il compratore non riceve l'avviso — nessun
    errore, nessuna traccia, semplicemente non arriva.

    ESEGUIBILE e non una sentinella sulla forma: si chiama la funzione
    VERA con un corriere cattivo e si guarda il testo che esce. E si
    guarda anche il ROVESCIO, che e' la meta' che si dimentica: nel
    database e nei confronti coi corrieri-sentinella il corriere deve
    restare quello che il venditore ha scritto, o si escaperebbe a
    monte rompendo 'Ritiro in zona'."""
    print("\n[l'avviso di spedizione]")
    import asyncio
    import html as _html
    import re as _re
    import sqlite3
    import time as _time

    # L'ordine di cartone, coi soli campi che la funzione guarda.
    def ordine(**extra):
        d = {"id": 7, "compratore_id": 111, "venditore_id": 222,
             "stato": "locked", "consegna_scelta": "spedizione",
             "annuncio_id": 3, "via_punto": 0, "punto_ritiro": "",
             "busta_il": 0,
             # l'ordine del mondo di ieri: l'indirizzo non l'ha mai
             # chiesto, quindi il gate di segna_spedito non lo tocca
             "indirizzo_atteso": 0, "indirizzo_il": 0}
        d.update(extra)
        return d

    def gira(corriere, tracking, **extra):
        """Chiama segna_spedito davvero e restituisce (testo della
        notifica, corriere finito nel database)."""
        o = ordine(**extra)
        scritto = {}
        con = sqlite3.connect(":memory:")

        class ConFinta:
            def execute(self, sql, par=()):
                if sql.startswith("SELECT * FROM ordini"):
                    return TrovaOrdine()
                if sql.startswith("UPDATE ordini"):
                    scritto["corriere"], scritto["tracking"] = par[0], par[1]
                    return None
                return con.execute("SELECT 1")     # l'asta: nessuna riga

            def commit(self): pass

            def close(self): pass

        class TrovaOrdine:
            def fetchone(self): return o

        detto = []

        async def notifica_finta(chi, testo, *a, **k):
            detto.append(testo)

        amb = {"html": _html, "time": _time, "db": lambda: ConFinta(),
               "notifica": notifica_finta,
               "MSG_BUSTA_PRONTA": "il pacco ti aspetta",
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "Request": object,
               "verifica_utente": lambda *a: {"id": 222},
               "HTTPException": type("HTTPException", (Exception,), {}),
               "leggi_json": None}

        async def json_finto(req):
            return {"corriere": corriere, "tracking": tracking}
        amb["leggi_json"] = json_finto

        exec("async " + pezzo("segna_spedito"), amb)
        asyncio.run(amb["segna_spedito"](7, None, "", ""))
        return (detto[0] if detto else ""), scritto

    # --- 1) IL CASO CHE HA APERTO IL PUNTO -------------------------
    # «Bartolini <BRT>» e' un nome che uno scrive senza pensarci.
    testo, _ = gira("Bartolini <BRT>", "1234")
    prova("il corriere col minore non entra nudo nel messaggio", False,
          "Bartolini <BRT>" in testo)
    prova("...ci entra scappato", True, "Bartolini &lt;BRT&gt;" in testo)
    # LA PROVA VERA non e' cercare le entita': e' che i tag <b> del
    # messaggio restino pari e richiudibili, che e' cio' che Telegram
    # controlla prima di rifiutare l'invio.
    tag = _re.findall(r"</?b>", testo)
    prova("...e i grassetti restano pari, cioe' il messaggio parte",
          tag.count("<b>"), tag.count("</b>"))

    # --- 2) anche il tracciamento, che nessuno guarda --------------
    testo, _ = gira("Poste Italiane", "AB<script>12")
    prova("il tracciamento cattivo e' scappato pure lui", True,
          "AB&lt;script&gt;12" in testo)
    tag = _re.findall(r"</?b>", testo)
    prova("...e i grassetti reggono anche li'",
          tag.count("<b>"), tag.count("</b>"))

    # --- 3) LO STESSO SULLA STRADA DEL PUNTO DI RITIRO -------------
    # E' il ramo nato col cantiere della busta, quello dove il buco e'
    # stato trovato: qui il messaggio dice «in viaggio verso il punto».
    testo, _ = gira("InPost <lockers>", "999", via_punto=1,
                    punto_ritiro="Bar Centrale, Carmagnola")
    prova("la strada del punto scappa il corriere come l'altra", True,
          "InPost &lt;lockers&gt;" in testo and "<lockers>" not in testo)
    prova("...ed e' proprio il messaggio del punto", True,
          "verso il punto di ritiro" in testo)

    # --- 4) IL ROVESCIO: quel che si scrive resta quel che ha
    #        scritto lui -------------------------------------------
    # Se si escapasse a monte, nel database finirebbe «Bartolini
    # &lt;BRT&gt;» — e il compratore leggerebbe QUELLO nella scheda
    # dell'ordine, dove il client ha gia' il suo esc().
    _, scritto = gira("Bartolini <BRT>", "12<34")
    prova("nel database il corriere resta quello del venditore",
          "Bartolini <BRT>", scritto["corriere"])
    prova("...e il tracciamento pure", "12<34", scritto["tracking"])

    # ...e soprattutto i CORRIERI-SENTINELLA continuano a matchare: e'
    # il confronto per stringa che decide se parte il timer del ritiro
    # invece di quello della spedizione.
    testo, scritto = gira("Ritiro in zona", "")
    prova("«Ritiro in zona» e' ancora riconosciuto", True,
          "consegna a mano" in testo)
    prova("...e arriva intero nel database", "Ritiro in zona",
          scritto["corriere"])

    # --- 5) e il caso normale non e' cambiato ----------------------
    testo, _ = gira("BRT", "0123456789")
    prova("un corriere onesto esce come sempre", True,
          "con <b>BRT</b>, tracciamento <b>0123456789</b>" in testo)

    # --- 6) IL GEMELLO DEL RESO, che aveva lo stesso buco ----------
    # Stessa trappola, altra parte: qui il testo e' del COMPRATORE che
    # rispedisce e ad aspettare e' il venditore. Un «<» e l'avviso che
    # il reso e' partito non arriva — e li' dentro c'e' un rimborso.
    def gira_reso(corriere, tracking):
        o = {"id": 5, "compratore_id": 111, "venditore_id": 222,
             "stato": "return_pending"}
        scritto, detto = {}, []

        class ConFinta:
            def execute(self, sql, par=()):
                if sql.startswith("SELECT * FROM ordini"):
                    return type("R", (), {"fetchone": lambda s: o})()
                scritto["corriere"], scritto["tracking"] = par[0], par[1]

            def commit(self): pass

            def close(self): pass

        async def notifica_finta(chi, testo, *a, **k):
            detto.append((chi, testo))

        async def json_finto(req):
            return {"corriere": corriere, "tracking": tracking}

        amb = {"html": _html, "time": _time, "db": lambda: ConFinta(),
               "notifica": notifica_finta, "leggi_json": json_finto,
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "Request": object,
               "verifica_utente": lambda *a: {"id": 111},
               "HTTPException": type("HTTPException", (Exception,), {})}
        exec("async " + pezzo("reso_spedito"), amb)
        asyncio.run(amb["reso_spedito"](5, None, "", ""))
        return detto[0], scritto

    (chi, testo), scritto = gira_reso("Bartolini <BRT>", "99<88")
    prova("il reso avvisa il VENDITORE, che aspetta l'oggetto", 222, chi)
    prova("...col corriere scappato", True,
          "Bartolini &lt;BRT&gt;" in testo and "<BRT>" not in testo)
    prova("...e il tracciamento pure", True, "99&lt;88" in testo)
    tag = _re.findall(r"</?b>", testo)
    prova("...coi grassetti pari, cioe' l'avviso parte",
          tag.count("<b>"), tag.count("</b>"))
    # e nel database resta il testo vero: il tracciamento di un reso e'
    # anche una prova in disputa, e deve restare quello che e' stato
    # scritto
    prova("nel database il tracciamento del reso resta intero", "99<88",
          scritto["tracking"])
    (_, testo), scritto = gira_reso("Consegna a mano", "")
    prova("«Consegna a mano» e' ancora riconosciuta", True,
          "in consegna a mano" in testo)

    # --- 7) le sentinelle: nessuna delle due variabili nude --------
    # E' la riga che sparisce in un riordino senza rompere niente di
    # visibile — il messaggio si vede uguale finche' nessuno scrive un
    # «<», e il giorno che qualcuno lo scrive non se ne accorge
    # nessuno. I nudi che restano sono quelli che vanno nel DATABASE.
    corpo = pezzo("segna_spedito")
    corpo_avvisi = corpo[corpo.index("corr_e, track_e ="):]
    prova("dopo l'escape nessuna notifica nomina il corriere nudo", 0,
          corpo_avvisi.count("{corriere}"))
    prova("...ne' il tracciamento nudo", 0, corpo_avvisi.count("{tracking}"))
    reso = pezzo("reso_spedito")
    corpo_reso = reso[reso.index("con.close()"):]
    prova("e nel reso lo stesso, dopo l'UPDATE", 0,
          corpo_reso.count("{corriere}") + corpo_reso.count("{tracking}"))


# ====================================================================
def prove_ricevuta_compratore():
    """LA RICEVUTA DEL COMPRATORE (ago 2026). Chi pagava non riceveva
    niente dal server: al venditore «Hai venduto», ai moderatori il
    polso, a lui il solo toast in-app. Ora la notifica parte SEMPRE da
    _incassa_ordine, che e' il punto da cui passano tutte e tre le
    strade dell'accredito (il poll della Mini App, il riacciuffo di
    controlla_annullati, l'ultimo sguardo di controlla_abbandonati) —
    e sulle ultime due lui non e' davanti allo schermo.

    ESEGUIBILE dove conta: si chiama _incassa_ordine VERA su un
    database vero e si guarda il testo che esce. Il resto e' il giudice
    puro della coda, che e' dove vive la bugia possibile — promettere
    un tracciamento a chi ritira a mano, o «i sats partono quando
    confermi» a chi compra un codice."""
    print("\n[la ricevuta del compratore]")
    import asyncio as _aio
    import html as _html
    import sqlite3
    import time as _time
    import types

    _coda = reale("_coda_ricevuta")
    # l'indirizzo di casa (ago 2026) ha allargato la firma di due
    # bool: qui si chiama col MONDO DI IERI (mai chiesto, mai
    # scritto), cosi' le prove storiche restano quelle di sempre e i
    # rami nuovi hanno le loro, sotto.
    coda = lambda c, vp, ps, ia=0, isc=False: _coda(c, vp, ps, ia, isc)

    # --- 1) IL GIUDICE DELLA CODA, strada per strada ---------------
    sped = coda("spedizione", 0, False)
    prova("spedizione a casa: promette il tracciamento", True,
          "tracciamento" in sped)
    prova("...e dice che a chiudere e' la sua conferma", True,
          "confermalo nella Mini App" in sped)

    # I DUE RAMI NUOVI della spedizione a casa: l'indirizzo scritto si
    # NOMINA, quello atteso si CHIEDE — e l'ordine che non l'ha mai
    # chiesto (sopra) resta col testo di sempre, o si manderebbe
    # qualcuno a cercare un campo che sul suo schermo non esiste.
    casa_ok = coda("spedizione", 0, False, 1, True)
    prova("indirizzo scritto: il venditore ci spedisce", True,
          "indirizzo che hai indicato" in casa_ok)
    casa_no = coda("spedizione", 0, False, 1, False)
    prova("indirizzo atteso e non scritto: gli si chiede", True,
          "indica l'indirizzo" in casa_no)
    prova("...e non gli si promette il tracciamento", True,
          "tracciamento" not in casa_no)

    punto = coda("spedizione", 1, True)
    prova("punto di ritiro: niente tracciamento da aspettare", True,
          "tracciamento" not in punto)
    prova("...si aspetta l'avviso che il pacco e' arrivato la'", True,
          "punto di ritiro" in punto and "avvisiamo" in punto)

    # Il residuo del quarto giro: via punto scelta, punto mai scritto
    # (gli ordini nati da un client di ieri). Qui la palla e' SUA, e
    # senza il punto il venditore non puo' nemmeno spedire.
    orfano = coda("spedizione", 1, False)
    prova("via punto senza punto: gli si chiede di indicarlo", True,
          "indica il punto" in orfano)
    prova("...e non gli si promette nessun avviso", True,
          "avvisiamo" not in orfano)

    ritiro = coda("ritiro", 0, False)
    prova("ritiro a mano: nessuna spedizione promessa", True,
          "tracciamento" not in ritiro and "pacco" not in ritiro)
    prova("...ci si accorda col venditore", True,
          "accordo con il venditore" in ritiro)

    # LA RIGA CHE NON SI PUO' AMMORBIDIRE: sul digitale le finestre
    # corte scattano DA SOLE (ORE_CONFERMA_DIGITALE dalla rivelazione,
    # ORE_SILENZIO_DIGITALE dalla consegna mai letta), quindi «i sats
    # partono quando confermi» sarebbe falso — e sarebbe falso proprio
    # verso chi ha comprato la cosa che non torna indietro.
    dig = coda("digitale", 0, False)
    prova("digitale: MAI la promessa della conferma", True,
          "conferm" not in dig)
    prova("...niente spedizione, niente pacco", True,
          "spedi" not in dig and "pacco" not in dig)
    prova("...si dice che il contenuto arriva qui dentro", True,
          "qui dentro" in dig)

    # Gli annunci storici e gli importati da Nostr: consegna ''. Non si
    # inventa una strada che nessuno ha scelto.
    ignota = coda("", 0, False)
    prova("consegna non dichiarata: nessuna strada promessa", True,
          "tracciamento" not in ignota and "conferm" not in ignota)
    prova("...ma qualcosa si dice lo stesso", True, len(ignota) > 20)

    # Nessuna coda e' vuota: una ricevuta che finisce coi due punti e
    # basta e' peggio di nessuna ricevuta.
    for c, nome in ((sped, "casa"), (punto, "punto"), (orfano, "orfano"),
                    (ritiro, "ritiro"), (dig, "digitale"),
                    (ignota, "ignota")):
        prova(f"la coda «{nome}» dice qualcosa e finisce col punto",
              True, bool(c.strip()) and c.rstrip().endswith("."))

    # --- 2) _incassa_ordine VERA, su un database vero --------------
    def gira(titolo="Cuffie AKG", **extra):
        """Chiama _incassa_ordine davvero e restituisce chi e' stato
        avvisato, con che testo."""
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.executescript("""
            CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INT,
              compratore_id INT, venditore_id INT, prezzo_sats INT,
              stato TEXT, quantita INT, consegna_scelta TEXT,
              via_punto INT DEFAULT 0, punto_ritiro TEXT DEFAULT '',
              spedizione_sats INT DEFAULT 0, protezione_sats INT DEFAULT 0,
              sconto_sats INT DEFAULT 0,
              indirizzo_atteso INT DEFAULT 0, indirizzo_il INT DEFAULT 0,
              aggiornato INT DEFAULT 0);
            CREATE TABLE ordine_righe(id INTEGER PRIMARY KEY, ordine_id INT,
              annuncio_id INT, quantita INT, unitario_sats INT, titolo TEXT);
            CREATE TABLE annunci(id INTEGER PRIMARY KEY, titolo TEXT,
              quantita INT, stato TEXT, contatto_nostr TEXT DEFAULT '',
              taglia_pacco TEXT DEFAULT '');
            CREATE TABLE offerte(id INTEGER PRIMARY KEY, annuncio_id INT,
              compratore_id INT, ordine_id INT, stato TEXT,
              aggiornato INT DEFAULT 0);
        """)
        con.execute("INSERT INTO annunci(id,titolo,quantita,stato) "
                    "VALUES(3,?,1,'attivo')", (titolo,))
        riga = {"id": 7, "annuncio_id": 3, "compratore_id": 111,
                "venditore_id": 222, "prezzo_sats": 50000,
                "stato": "creato", "quantita": 1,
                "consegna_scelta": "spedizione", "via_punto": 0,
                "punto_ritiro": ""}
        riga.update(extra)
        con.execute(
            "INSERT INTO ordini(id,annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,stato,quantita,consegna_scelta,via_punto,"
            "punto_ritiro) VALUES(?,?,?,?,?,?,?,?,?,?)",
            tuple(riga[k] for k in
                  ("id", "annuncio_id", "compratore_id", "venditore_id",
                   "prezzo_sats", "stato", "quantita", "consegna_scelta",
                   "via_punto", "punto_ritiro")))
        con.commit()

        class ConFinta:
            """Il close() e' un no-op: su :memory: chiuderebbe il
            database a meta' funzione."""
            def __getattr__(self, n): return getattr(con, n)

            def close(self): pass

        detto = []

        async def notifica_finta(chi, testo, *a, **k):
            detto.append((chi, testo))

        async def polso_finto(*a, **k): pass

        amb = {"html": _html, "time": _time, "db": lambda: ConFinta(),
               "notifica": notifica_finta,
               "polso_ordini_admin": polso_finto,
               "asyncio": types.SimpleNamespace(create_task=lambda c: None),
               "annuncio_su_nostr": lambda *a, **k: None,
               "promo_venduto": lambda *a, **k: None,
               "stima_taglia_set": lambda t: "",
               "_righe_ordine": reale("_righe_ordine"),
               "_titolo_ordine": reale("_titolo_ordine"),
               "_coda_ricevuta": coda, "_fmt_sats": reale("_fmt_sats")}
        exec("async " + pezzo("_incassa_ordine"), amb)
        _aio.run(amb["_incassa_ordine"](7))
        return detto

    detto = gira()
    destinatari = [chi for chi, _ in detto]
    prova("l'incasso avvisa il COMPRATORE", True, 111 in destinatari)
    prova("...e il venditore continua a ricevere il suo", True,
          222 in destinatari)
    ric = [t for chi, t in detto if chi == 111][0]
    prova("la ricevuta e' UNA sola", 1, destinatari.count(111))
    prova("la ricevuta dice che l'ordine e' pagato", True,
          "Ordine pagato" in ric)
    prova("...nomina il deposito di garanzia", True,
          "deposito di garanzia" in ric)
    prova("...dice cosa ha comprato", True, "Cuffie AKG" in ric)
    prova("...e la coda e' quella della sua strada", True,
          "tracciamento" in ric)

    # La coda segue la STRADA, non l'ordine generico: e' tutto il punto
    ric_dig = [t for chi, t in gira(consegna_scelta="digitale")
               if chi == 111][0]
    prova("ordine digitale: la ricevuta non promette un pacco", True,
          "tracciamento" not in ric_dig and "qui dentro" in ric_dig)
    ric_rit = [t for chi, t in gira(consegna_scelta="ritiro")
               if chi == 111][0]
    prova("ordine col ritiro: ci si accorda, non si aspetta un corriere",
          True, "accordo con il venditore" in ric_rit)
    ric_pun = [t for chi, t in gira(via_punto=1,
                                    punto_ritiro="Bar Centrale")
               if chi == 111][0]
    prova("ordine al punto: si aspetta l'avviso d'arrivo", True,
          "punto di ritiro" in ric_pun)
    prova("...e il punto che ha scritto LUI non entra nel messaggio",
          False, "Bar Centrale" in ric_pun)

    # --- 3) IL TITOLO E' TESTO DEL VENDITORE -----------------------
    # Le notifiche sono HTML: un «<» nel titolo fa fallire il parse di
    # Telegram e la ricevuta non arriva — senza errore e senza traccia.
    # E' la lezione dell'avviso di spedizione, sullo stesso tubo.
    ric = [t for chi, t in gira(titolo="Cuffie <b>AKG</b> K371")
           if chi == 111][0]
    prova("il titolo cattivo non entra nudo nella ricevuta", False,
          "<b>AKG</b>" in ric)
    prova("...ci entra scappato", True, "&lt;b&gt;AKG&lt;/b&gt;" in ric)
    import re as _re
    tag = _re.findall(r"</?b>", ric)
    prova("...e i grassetti restano pari, cioe' la ricevuta parte",
          tag.count("<b>"), tag.count("</b>"))

    # --- 4) le sentinelle ------------------------------------------
    inc = pezzo("_incassa_ordine")
    # La ricevuta vive nel FUNNEL e non nei chiamanti: e' cio' che la fa
    # ereditare alle strade dell'orologio senza un ramo apposta. Chi la
    # sposta su verifica_pagamento rimette il silenzio esattamente dove
    # faceva piu' male.
    prova("la ricevuta parte da _incassa_ordine, il funnel", True,
          'notifica(o["compratore_id"]' in inc)
    prova("...e la coda la decide il giudice, mai un if a mano", True,
          "_coda_ricevuta(" in inc)
    prova("il titolo si tronca PRIMA e si escapa DOPO", True,
          'html.escape(_titolo_ordine(righe)[:60])' in inc)
    prova("il giudice della coda ha UN solo chiamante", 1,
          _SORGENTE.count("_coda_ricevuta(o["))
    # Il punto di ritiro e' testo del COMPRATORE e nella coda non ci
    # entra mai: il giudice ne riceve un bool, non la stringa.
    prova("al giudice il punto arriva come bool, mai il testo", True,
          'bool(o["punto_ritiro"])' in inc)
    cod = pezzo("_coda_ricevuta")
    prova("il giudice della coda non tocca ne' database ne' rete", True,
          "con." not in cod and "await" not in cod)

    # Il toast se n'e' andato: durava tre secondi e non lasciava niente
    # da ritrovare. In DEMO resta, che li' non c'e' server che notifichi.
    mini = open("miniapp.html", encoding="utf-8").read()
    i = mini.index("async function verificaOrdine(")
    ver_js = mini[i:mini.index("\n}", i)]
    prova("nel poll non c'e' piu' il toast del pagamento", False,
          "Sats al sicuro" in ver_js)
    prova("...ma in DEMO il toast resta", True,
          "Sats al sicuro" in mini[mini.index("function simulatePaid("):])


# ====================================================================
def prove_titoli_scappati():
    """IL TITOLO NUDO NELLE NOTIFICHE (ago 2026, la famiglia di B6).
    Le notifiche sono HTML e il titolo lo scrive il VENDITORE: un «<»
    fa fallire il parse di Telegram e l'avviso non arriva — senza
    errore e senza traccia. B6 aveva chiuso i due rami della
    spedizione; restavano scoperti il polso degli ordini (che e'
    l'avviso ai MODERATORI), quattro solleciti su sei, e altri otto
    siti che solo il censimento ha tirato fuori.

    LA REGOLA E' UNA SOLA, e la prova che conta e' il CENSIMENTO: chi
    manda un avviso scappa il testo dell'utente ALL'ASSEGNAZIONE, una
    volta, e da li' lo stesso valore serve le notifiche e il polso.
    L'alternativa — l'escape dentro polso_ordini_admin — e' stata
    scritta e poi scartata: i chiamanti che compongono anche messaggi
    loro (_sblocca_sats, _rimborsa_compratore) userebbero la stessa
    variabile in due regimi, e il primo che li confonde scrive
    «&amp;lt;» dentro un avviso.

    Piu' l'ULTIMA RETE in fondo al tubo, che NON sostituisce l'escape
    alla fonte: e' quel che salva il sito scritto l'anno prossimo."""
    print("\n[i titoli scappati nelle notifiche]")
    import asyncio as _aio
    import html as _html
    import re as _re
    import types as _types

    righe = _SORGENTE.split("\n")
    inizi = [(i, m.group(1)) for i, r in enumerate(righe)
             if (m := _re.match(r"(?:async )?def ([a-z_][a-z_0-9]*)\(", r))]

    def corpi():
        for k, (i, nome) in enumerate(inizi):
            fine = inizi[k + 1][0] if k + 1 < len(inizi) else len(righe)
            yield nome, "\n".join(righe[i:fine])

    # --- 1) IL CENSIMENTO, che e' la prova vera --------------------
    # Non un elenco di funzioni scritto a mano — quello invecchia al
    # primo sollecito nuovo: si guarda TUTTO il file e si chiede che
    # ogni «titolo» che finisce in un avviso nasca scappato.
    scoperti, visti = [], []
    for nome, c in corpi():
        if not _re.search(r"\{titolo[\}\[]", c):
            continue
        if not _re.search(r"notifica|polso_ordini_admin|_congela_pagamento", c):
            continue
        visti.append(nome)
        for ass in _re.findall(r"^\s*titolo = (.+)$", c, _re.M):
            if "html.escape" in ass or _re.fullmatch(r'"[^"]*"', ass.strip()):
                continue          # gia' scappato, o un letterale nostro
            scoperti.append((nome, ass.strip()))
    prova("nessuna funzione che notifica interpola un titolo nudo",
          [], scoperti)
    # ...e che il censimento abbia davvero guardato dove serve: se un
    # domani il predicato smettesse di pescarle, il conto a zero
    # sembrerebbe una promozione invece di una cecita'.
    for f in ("sollecita_incassi", "sollecita_ritiri_fermi",
              "sollecita_conferme_ferme", "sollecita_rimborsi_puntate",
              "sollecita_venditori_fermi", "sollecita_buste_ferme",
              "_paga_rimborso", "_sblocca_sats", "_rimborsa_compratore",
              "_incassa_ordine", "_racconta_chiusura", "verifica_rilancio",
              "rispondi_offerta", "scadenze_offerte", "annulla_asta_admin",
              "sollecita_venditore"):
        prova(f"il censimento vede «{f}»", True, f in visti)

    # --- 2) IL ROVESCIO: non si scappa dove non e' HTML ------------
    # In _compra_set il nome del pezzo esaurito va nel detail di un 404,
    # cioe' JSON che il client rende col SUO esc(): un html.escape li'
    # farebbe leggere «Cuffie &lt;b&gt;AKG&lt;/b&gt;» a chi compra. La
    # variabile si chiama apposta in un altro modo, cosi' il censimento
    # non la pesca e chi legge vede subito che e' un'altra cosa.
    cs = pezzo("_compra_set")
    prova("il 404 del set non scappa il nome del pezzo", True,
          'nome_pezzo = a["titolo"][:40]' in cs
          and 'html.escape(a["titolo"][:40]' not in cs)

    # --- 3) IL POLSO riceve un titolo GIA' scappato ----------------
    detto = []

    async def notifica_admin_finta(t):
        detto.append(t)

    class ContaFinta:
        def execute(self, sql, par=()):
            return _types.SimpleNamespace(fetchone=lambda: [4])

        def close(self):
            pass

    amb = {"AVVISI_ORDINI_ADMIN": True,
           "notifica_admin": notifica_admin_finta, "db": lambda: ContaFinta()}
    exec("async " + pezzo("polso_ordini_admin"), amb)
    _aio.run(amb["polso_ordini_admin"](
        "🛒 «Cuffie &lt;b&gt;AKG&lt;/b&gt;» — aperti: {aperti}"))
    prova("il polso non ri-scappa quel che riceve", True,
          "&lt;b&gt;AKG&lt;/b&gt;" in detto[0] and "&amp;" not in detto[0])
    prova("...e il conto degli aperti si riempie come sempre", True,
          detto[0].endswith("aperti: 4"))
    prova("il polso NON ha un escape suo (la regola sta alla fonte)",
          False, "html.escape" in pezzo("polso_ordini_admin"))

    # --- 4) I QUATTRO SOLLECITI, coi loro ripieghi -----------------
    # Tutti e quattro assegnano una volta sola; il ripiego «or ...» e'
    # la cintura del titolo NULL, che stava FUORI dal try — il giorno
    # che diventasse raggiungibile ammazzerebbe il giro per tutti.
    for f, ripiego in (("sollecita_incassi", "il tuo affare"),
                       ("sollecita_ritiri_fermi", "il vostro scambio"),
                       ("sollecita_conferme_ferme", "il tuo acquisto"),
                       ("sollecita_rimborsi_puntate", "un'asta")):
        c = pezzo(f)
        atteso = 'html.escape((r["titolo"] or "' + ripiego + '")[:60])'
        prova(f"{f}: titolo scappato col suo ripiego", True, atteso in c)

    # --- 5) IL PIU' GRAVE: il 🧊 del pagamento incerto -------------
    # E' l'avviso che questo progetto dichiara non debba MAI sparire —
    # un pagamento che puo' essere uscito davvero — e il titolo ci
    # finiva nudo.
    pag = pezzo("_paga_rimborso")
    prova("il 🧊 del pagamento incerto ha il titolo scappato", True,
          "_congela_pagamento" in pag
          and 'html.escape((r["titolo"] or "un' + "'" + 'asta")[:60])' in pag)

    # --- 6) L'ULTIMA RETE in fondo al tubo -------------------------
    mandati = []

    class ClientFinto:
        def __init__(self, esiti):
            self.esiti = list(esiti)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None):
            mandati.append(json)
            return self.esiti.pop(0)

    def risposta(code, testo=""):
        return _types.SimpleNamespace(status_code=code, text=testo)

    def manda(esiti, testo):
        mandati.clear()
        spoglia = {"html": _html, "re": _re}
        exec(pezzo("spoglia_html"), spoglia)
        amb = {"MODALITA_COLLAUDO": False, "BOT_TOKEN": "t",
               "spoglia_html": spoglia["spoglia_html"],
               "httpx": _types.SimpleNamespace(
                   AsyncClient=lambda: ClientFinto(esiti))}
        exec("async " + pezzo("_manda_telegram"), amb)
        _aio.run(amb["_manda_telegram"](12345678, testo))
        return list(mandati)

    # il caso felice non cambia di un byte
    inviati = manda([risposta(200)], "🔒 <b>Venduto</b>")
    prova("messaggio buono: un invio solo", 1, len(inviati))
    prova("...in HTML come sempre", "HTML", inviati[0]["parse_mode"])

    # IL GUASTO: Telegram rifiuta il parse. Prima si perdeva qui, e la
    # risposta non la guardava nessuno.
    rotto = '{"description":"Bad Request: can' + "'" + 't parse entities"}'
    inviati = manda([risposta(400, rotto), risposta(200)],
                    "🔒 <b>Venduto</b> «Cuffie <AKG>»")
    prova("HTML rifiutato: si rimanda invece di perderlo", 2, len(inviati))
    prova("...il secondo invio e' senza parse_mode", True,
          "parse_mode" not in inviati[1])
    prova("...ed e' spoglio e leggibile", "🔒 Venduto «Cuffie »",
          inviati[1]["text"])

    # ogni ALTRO errore resta muto: un secondo invio non lo ripara
    for code, desc in ((403, "bot was blocked by the user"),
                       (400, "chat not found"),
                       (429, "Too Many Requests")):
        inviati = manda([risposta(code, '{"description":"%s"}' % desc)],
                        "🔒 <b>Venduto</b>")
        prova(f"«{desc}»: nessun secondo invio", 1, len(inviati))

    corpo = pezzo("_manda_telegram")
    prova("la risposta di Telegram si GUARDA", True, "status_code" in corpo)
    # ATTENZIONE: qui la prima stesura chiedeva «print( in corpo», e non
    # poteva fallire — il print del collaudo, dieci righe piu' su, la
    # teneva verde anche togliendo quello del ripiego. La tortura l'ha
    # smascherata (0 rosse su una mutazione che doveva farne almeno una).
    # Si guarda DENTRO il ramo, che e' l'unico posto che conta.
    ramo = corpo[corpo.index("if r.status_code"):]
    prova("...e il ripiego STAMPA, mai una riparazione silenziosa",
          True, "print(" in ramo)
    prova("...e non puo' fare catena (un solo invio spoglio)",
          1, corpo.count("spoglia_html("))
# ====================================================================
def prove_timbri_periodici():
    """IL TIMBRO CHE NON TENEVA (ago 2026, caso dal campo: il termometro
    delle sottocategorie arrivato TRE volte in cinquanta minuti — 12:35,
    13:04, 13:25 — agli orari dei tre deploy di quel lunedi').

    LA DIAGNOSI: il timbro era un globale, e un globale muore col
    processo. Il gate del calendario (il lunedi') restringeva il
    GIORNO ma dentro il giorno non contava niente: a distinguere il
    primo battito dal centoquarantesimo c'era solo la RAM. Quindi
    «un riavvio puo' al piu' far suonare due volte», che la docstring
    prometteva, non era garantito da nulla — era una volta PER
    RIAVVIO, senza tetto.

    LA PROVA E' ESEGUIBILE e simula proprio quello: si fa girare la
    funzione VERA tre volte su tre ambienti DIVERSI — che e' cosa
    succede a tre deploy — con lo stesso database sotto. Una
    sentinella sulla forma non basterebbe: qui il difetto non e' una
    riga mancante, e' uno stato che non sopravvive."""
    print("\n[i timbri degli avvisi periodici]")
    import asyncio as _aio
    import sqlite3
    import time as _time

    # Il database vero dei timbri, in memoria: e' il pezzo che deve
    # sopravvivere ai «riavvii».
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE timbri(nome TEXT PRIMARY KEY, "
                "valore TEXT DEFAULT '', quando INTEGER DEFAULT 0)")
    con.commit()

    class ConFinta:
        """close() no-op: su :memory: chiuderebbe il database."""

        def __getattr__(self, n):
            return getattr(con, n)

        def close(self):
            pass

    def ambiente(**extra):
        """UN PROCESSO: ambiente nuovo, database vecchio. E' quel che
        cambia fra un deploy e l'altro."""
        amb = {"db": lambda: ConFinta(), "time": _time,
               "print": lambda *a, **k: None}
        amb.update(extra)
        exec(pezzo("timbro_letto"), amb)
        exec(pezzo("timbro_scrivi"), amb)
        return amb

    # --- 1) i due giudici, andata e ritorno ------------------------
    a = ambiente()
    prova("timbro mai scritto: stringa vuota", "", a["timbro_letto"]("x"))
    a["timbro_scrivi"]("x", "2026-08-10")
    prova("...scritto e riletto", "2026-08-10", a["timbro_letto"]("x"))
    a["timbro_scrivi"]("x", "2026-08-17")
    prova("...si sovrascrive, non si accumula", "2026-08-17",
          a["timbro_letto"]("x"))
    prova("un timbro non parla per un altro", "", a["timbro_letto"]("y"))
    # IL PUNTO DI TUTTO: un ambiente NUOVO (= un deploy) lo rilegge
    prova("e SOPRAVVIVE a un processo nuovo", "2026-08-17",
          ambiente()["timbro_letto"]("x"))

    # --- 2) IL CASO DAL CAMPO, riprodotto --------------------------
    # Tre deploy nello stesso lunedi', vetrina con la coda piena.
    detti = []

    async def notifica_admin_finta(t):
        detti.append(t)

    def deploy(lunedi=True):
        """Un giro d'orologio in un processo APPENA partito."""
        amb = ambiente(
            TERMOMETRO_SOTTOCATEGORIE=True,
            TERMOMETRO_SOTTOCATEGORIE_MINIMO=5,
            TIMBRO_TERMOMETRO="termometro_sotto",
            notifica_admin=notifica_admin_finta,
            _termometro_conta=lambda c: (12, {"Informatica": 7,
                                              "Telefonia": 5}, 3))
        # il calendario si finge: lunedi' o no
        amb["time"] = _types_orologio(_time, lunedi)
        exec("async " + pezzo("termometro_sottocategorie"), amb)
        _aio.run(amb["termometro_sottocategorie"]())

    detti.clear()
    deploy(); deploy(); deploy()
    prova("tre deploy nello stesso lunedi': UNA notifica sola",
          1, len(detti))
    prova("...e dice la coda che ha trovato", True,
          "12" in detti[0] and "Informatica" in detti[0])

    # il lunedi' DOPO si ricomincia (il timbro e' il giorno, non «mai
    # piu'»): si sposta il giorno cancellando la riga, che e' quel che
    # fa il calendario passando a un altro lunedi'
    con.execute("DELETE FROM timbri WHERE nome='termometro_sotto'")
    con.commit()
    detti.clear()
    deploy()
    prova("il lunedi' dopo torna a suonare", 1, len(detti))

    # e in un giorno che non e' lunedi' non suona comunque
    con.execute("DELETE FROM timbri WHERE nome='termometro_sotto'")
    con.commit()
    detti.clear()
    deploy(lunedi=False)
    prova("di martedi' tace, timbro o non timbro", 0, len(detti))

    # --- 3) LA CODA FERMA NON CONSUMA LA SETTIMANA -----------------
    # Sotto il minimo si esce PRIMA di timbrare: se timbrasse, una
    # settimana silenziosa brucerebbe il turno e il lunedi' dopo
    # ricontrollerebbe... mai.
    con.execute("DELETE FROM timbri")
    con.commit()
    detti.clear()
    amb = ambiente(
        TERMOMETRO_SOTTOCATEGORIE=True, TERMOMETRO_SOTTOCATEGORIE_MINIMO=5,
        TIMBRO_TERMOMETRO="termometro_sotto",
        notifica_admin=notifica_admin_finta,
        _termometro_conta=lambda c: (2, {"Informatica": 2}, 0))
    amb["time"] = _types_orologio(_time, True)
    exec("async " + pezzo("termometro_sottocategorie"), amb)
    _aio.run(amb["termometro_sottocategorie"]())
    prova("coda sotto il minimo: non suona", 0, len(detti))
    prova("...e NON timbra, o brucerebbe il turno", "",
          ambiente()["timbro_letto"]("termometro_sotto"))

    # --- 4) FAIL-OPEN NEL VERSO DEL PARLARE ------------------------
    # Un timbro illeggibile non deve poter zittire per sempre un
    # avviso: la lettura che esplode risponde «mai timbrato».
    rotto = {"db": _esplode, "time": _time, "print": lambda *a, **k: None}
    exec(pezzo("timbro_letto"), rotto)
    prova("database muto in lettura: l'avviso PARTE", "",
          rotto["timbro_letto"]("termometro_sotto"))
    # e la scrittura che esplode non ferma il giro dell'orologio
    rotto2 = {"db": _esplode, "time": _time, "print": lambda *a, **k: None}
    exec(pezzo("timbro_scrivi"), rotto2)
    rotto2["timbro_scrivi"]("x", "y")      # non deve sollevare
    prova("database muto in scrittura: non alza, il giro continua",
          True, True)

    # --- 5) IL CENSIMENTO: nessun avviso periodico torna alla RAM ---
    # E' la prova che tiene: chi aggiunge un avviso periodico domani
    # non deve poter reintrodurre il globale che muore al deploy.
    src = _SORGENTE
    for f in ("termometro_sottocategorie", "sollecita_revisioni",
              "controlla_libro_mastro"):
        c = pezzo(f)
        prova(f"{f}: legge il timbro dal database", True,
              "timbro_letto(" in c)
        prova(f"{f}: lo scrive nel database", True, "timbro_scrivi(" in c)
        prova(f"{f}: nessun globale di gate rimasto", False, "global _" in c)
    prova("i vecchi globali non esistono piu'", True,
          "_ultimo_termometro_sotto" not in src
          and "_ultimo_sollecito_revisioni" not in src
          and "_ultimo_libro_mastro" not in src)

    # --- 6) E OGNUNO LASCIA UNA RIGA NEL JOURNAL -------------------
    # Il secondo difetto del caso dal campo: l'invio non si trovava da
    # nessuna parte, quindi un avviso che parte troppo non si poteva
    # nemmeno diagnosticare. La riga si stampa PRIMA della notifica.
    for f in ("termometro_sottocategorie", "sollecita_revisioni",
              "controlla_libro_mastro"):
        c = pezzo(f)
        prova(f"{f}: lascia una riga nel journal quando manda", True,
              "avviso mandato" in c)
        prova(f"{f}: la riga viene PRIMA dell'invio", True,
              c.index("avviso mandato") < c.index("notifica_admin("))


def _esplode():
    raise sqlite3_errore("database bloccato")


def sqlite3_errore(m):
    import sqlite3
    return sqlite3.OperationalError(m)


def _types_orologio(vero, lunedi):
    """Un `time` che mente sul giorno della settimana e basta."""
    import types
    return types.SimpleNamespace(
        strftime=lambda f, *a: "2026-08-10" if f == "%Y-%m-%d"
        else vero.strftime(f, *a),
        localtime=lambda *a: types.SimpleNamespace(tm_wday=0 if lunedi else 1),
        time=vero.time)

# ====================================================================
def _amb_seo():
    """L'ambiente condiviso delle prove sulle anteprime e sul cantiere
    «farsi trovare»: i pezzi VERI di server.py montati senza importarlo
    (che vorrebbe config.py, anthropic e mezzo mondo). I due soli stub
    sono quelli che chiedono il dataset dei comuni e la rete — qui non
    si collauda ne' la geografia ne' CoinGecko."""
    import html as _html
    import json as _json
    import re as _re
    import time as _time
    import unicodedata as _ud

    amb = {"html": _html, "json": _json, "os": os, "re": _re,
           "time": _time, "unicodedata": _ud,
           "URL_PUBBLICO": "https://barattolo.store", "FOTO_DIR": "foto",
           "comune_da_zona": lambda z: "Carmagnola (TO)" if "Carmagnola" in z
           else "",
           "cambio_noto_ora": lambda *a: 0.0}
    for riga in ("IMMAGINE_BRAND = (", "SEGNO_META = ", "SEGNO_TITOLO = ",
                 "SEGNO_CORPO = ", "MAX_SLUG = ", "_ID_PERCORSO = ",
                 "META_NOINDEX = ", "TETTO_CARTELLO = ",
                 "CACHE_SEO_HOME = ", "CAMPI_CARTELLO = ",
                 "TETTO_SITEMAP = ", "CACHE_SITEMAP = "):
        i = _SORGENTE.index(riga)
        exec(_SORGENTE[i:_SORGENTE.index("\n", i)], amb)
    # multi-riga: vogliono il taglio alla riga VUOTA, non al primo \n
    for blocco in ("TLD_RECAPITO = (", "_RECAPITO = re.compile(",
                   "CATEGORIE = (", "CATEGORIE_SENZA_CONDIZIONE = ",
                   "CONDIZIONI = {", "CONDIZIONI_LD = {",
                   "_PAGINA_CACHE = {", "_SEO_HOME_CACHE = {",
                   "_SITEMAP_CACHE = {", "ROBOTS_TXT = (",
                   "TITOLO_HOME = ", "TITOLO_SICUREZZA = "):
        i = _SORGENTE.index(blocco)
        exec(_SORGENTE[i:_SORGENTE.index("\n\n", i)], amb)
    for f in ("normalizza", "slug_categoria", "senza_condizione",
              "condizione_da_mostrare", "in_ferie", "_fmt_sats", "_fmt_eur",
              "_prezzo_promo", "_pare_recapito", "_slug",
              "_id_da_percorso", "_chi_da_percorso",
              "_attr", "_testo", "_ld", "_meta_anteprima", "_taglia_meta",
              "_immagine_anteprima", "_testa_seo", "_url_annuncio",
              "_url_negozio", "_categoria_da_slug", "_schede_cartello",
              "_link_categorie", "_seo_niente", "_prezzo_ld",
              "_disponibilita_ld", "_ld_annuncio", "_seo_annuncio",
              "_seo_negozio", "_seo_categoria", "_seo_home",
              "_seo_o_generici", "_spezza_pagina", "_monta_pagina",
              "_riga_sitemap", "_sitemap"):
        exec(pezzo(f), amb)
    i = _SORGENTE.index("META_GENERICI = _meta_anteprima(")
    exec(_SORGENTE[i:_SORGENTE.index("\n\n", i)], amb)
    i = _SORGENTE.index("META_SICUREZZA = _meta_anteprima(")
    exec(_SORGENTE[i:_SORGENTE.index("\n\n", i)], amb)
    return amb


def _db_finto(con):
    """La connessione di cartone: i costruttori la chiudono nel
    finally, e chiudere davvero un :memory: sarebbe buttare via il
    database fra una prova e l'altra."""
    class ConFinta:
        def execute(self, *a):
            return con.execute(*a)

        def close(self):
            pass
    return lambda: ConFinta()


def _vetrina_finta(con):
    """Le due tabelle che i costruttori SEO leggono, con le colonne che
    servono a loro."""
    import sqlite3
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE annunci (id INTEGER PRIMARY KEY, titolo TEXT, "
                "descrizione TEXT, zona TEXT, valuta TEXT, prezzo_sats INT, "
                "prezzo_eur REAL, foto TEXT, stato TEXT, venditore_id INT, "
                "categoria TEXT DEFAULT '', consegna TEXT DEFAULT '', "
                "condizione TEXT DEFAULT '', quantita INT DEFAULT 1, "
                "creato INT DEFAULT 0, modificato INT DEFAULT 0)")
    con.execute("CREATE TABLE utenti (tg_id INT, nome TEXT, username TEXT, "
                "negozio TEXT, rating REAL, n_feedback INT, "
                "ferie_fino INT DEFAULT 0)")
    return con


def prove_anteprime():
    """LE ANTEPRIME DEI LINK (ago 2026). La famiglia difende tre cose,
    e la prima e' quella che conta: UN ANNUNCIO NON ATTIVO NON RACCONTA
    NIENTE DI SE'. L'anteprima di Telegram resta in cache per giorni e
    viaggia ripubblicata da chi inoltra il messaggio — un titolo finito
    li' dentro e' un annuncio che continua a esistere in giro anche
    dopo che lo scudo anti-resurrezione l'ha spento, cioe' lo stesso
    scudo bucato da un'altra parte. Per questo NON e' una sentinella di
    forma sulla WHERE ma una prova ESEGUIBILE: il rimosso ci passa
    davvero, su un database vero, e il suo titolo si cerca nell'HTML
    che esce."""
    print("\n[le anteprime dei link]")
    import html as _html
    import json as _json
    import re as _re
    import sqlite3
    import tempfile

    amb = _amb_seo()
    GEN = amb["META_GENERICI"]
    # Cio' che non e' pubblico ricade sui generici PIU' il noindex: e'
    # la stessa condizione, letta due volte — l'anteprima tace e il
    # motore non indicizza, e la seconda meta' non e' un secondo «if».
    MUTO = GEN + amb["META_NOINDEX"]

    # --- 1) il taglio: una riga sola, mai a meta' parola ------------
    taglia = amb["_taglia_meta"]
    prova("il taglio schiaccia a-capo e doppi spazi", "ciao mondo",
          taglia("  ciao\n\n   mondo  ", 100))
    prova("...e sotto la misura non mette puntini", "ciao", taglia("ciao", 10))
    prova("...taglia a parola intera", "uno due…",
          taglia("uno due tre quattro", 9))
    prova("...e regge il campo vuoto", "", taglia(None, 20))

    # --- 1bis) UN EURO SI SCRIVE IN UN MODO SOLO -------------------
    # Vive in _fmt_eur, gemello di _fmt_sats, e da li' passano TUTTI i
    # posti dove un euro diventa testo per una persona: i post del
    # canale, le note Nostr, le anteprime dei link e le notifiche
    # delle offerte. Col punto una cifra grande si legge per un
    # fattore mille — e il client lo diceva gia' giusto per conto suo
    # (fmtEur, toLocaleString 'it-IT'): il server era l'unico fuori.
    eur = amb["_fmt_eur"]
    prova("l'euro porta la virgola dei decimali", "284,61", eur(284.61))
    prova("...anche tondo", "5,00", eur(5))
    prova("...e i centesimi non si perdono", "0,07", eur(0.07))
    pp = amb["_prezzo_promo"]
    prova("il listino in euro parla italiano",
          "38,50 € (≈ 70.000 sats)",
          pp({"valuta": "eur", "prezzo_eur": 38.5, "prezzo_sats": 70000}, 0))
    prova("...e il ≈ del listino in sats pure",
          "100.000 sats (≈ 55,00 €)",
          pp({"valuta": "sats", "prezzo_sats": 100000}, 55000.0))
    prova("...senza cambio il ≈ si omette, come sempre",
          "100.000 sats",
          pp({"valuta": "sats", "prezzo_sats": 100000}, 0))
    exec(pezzo("_cifra_offerta"), amb)
    exec(pezzo("testo_prezzo"), amb)
    co, tp = amb["_cifra_offerta"], amb["testo_prezzo"]
    prova("e l'offerta dice la stessa cosa", "15,50 €", co("eur", 0, 15.5))

    # --- 1ter) e UN SATOSHI si scrive in un modo solo --------------
    # Stesso argomento un piano piu' in la' (ago 2026): _fmt_sats
    # esisteva gia' ma meta' dell'app lo scavalcava, e i formati in
    # giro erano QUATTRO — «509000» grezzo, «509.000» dal giudice,
    # «509,000» con la virgola INGLESE di {n:,}, e «509 000» con lo
    # spazio. Adesso ci passa tutto quello che una persona legge.
    prova("i sats portano i puntini, ovunque",
          "80.000 sats", co("sats", 80000, 0.0))
    prova("...anche nel prezzo che leggono i moderatori",
          "509.000 sats", tp("sats", 509000, 0))
    prova("...e nel ≈ accanto a un listino in euro",
          "284,61 EUR (≈ 509.000 sats)", tp("eur", 509000, 284.61))

    # E _fmt_sats NON SOLLEVA MAI, che e' la riga piu' importante di
    # questa famiglia: da qui passano le cifre delle notifiche, e
    # parecchie vivono dentro un try/except che protegge qualcosa di
    # piu' importante — un formattatore che alza le mani li' dentro
    # non fa un errore, fa SPARIRE L'ALLARME in silenzio. Il caso
    # vero, preso da questa prova mentre il cantiere era in corso:
    # importo_invoice torna None sulla bolt11 illeggibile, e con un
    # f"{None:,}" l'avviso «importo storto» ai moderatori — o un
    # wallet rotto, o un tentativo di prelievo — non partiva piu'.
    fs = amb["_fmt_sats"]
    prova("_fmt_sats non solleva sul None di una invoice illeggibile",
          "None", fs(None))
    prova("...ne' su una stringa arrivata per sbaglio", "boh", fs("boh"))
    prova("...e i numeri veri restano quelli", "1.234.567", fs(1234567))

    # LA SENTINELLA che rende il principio verificabile invece che
    # raccomandato: nessuno scrive un euro a mano. Cercare `:.2f} €`
    # e' cercare esattamente il gesto — una cifra formattata al volo
    # col simbolo attaccato — che _fmt_eur esiste per non fare piu'.
    prova("nessun euro col simbolo sfugge a _fmt_eur", 0,
          _SORGENTE.count(":.2f} €"))
    # ...e nemmeno quelli che dicono «EUR» a parole, che sono il modo
    # in cui questa famiglia si nasconde: cercando il solo € il primo
    # censimento ne aveva mancati tre (testo_prezzo dei moderatori e i
    # due avvisi gemelli del drift del cambio), ed e' stata questa
    # sentinella a prenderli.
    # I TRE superstiti non li legge una persona: le due righe di prosa
    # del NIP-99 («Prezzo:» e «spedizione:»), che stanno nello stesso
    # evento dei tag e li ripetono a parole — divergere da loro sarebbe
    # peggio —, e la riga del catalogo che va in pasto ad Haiku, dove
    # il formato compatto e' per la macchina.
    prova("...ne' quelli che scrivono EUR a parole (restano i tre che "
          "una persona non legge)", 3, _SORGENTE.count(":.2f} EUR"))
    # Il censimento completo dei superstiti, che vale come elenco: i
    # tre TAG NIP-99 (price ×2, delivery) e le due righe di prosa che
    # li accompagnano — campi di protocollo che importa_nostr rilegge,
    # dove il punto e' la specifica e non una nostra scelta —, la riga
    # del catalogo che va all'AI (non la legge una persona), _fmt_eur
    # stesso, il CSV (che la virgola ce l'ha gia' per conto suo) e —
    # dall'ago 2026 — il prezzo dei DATI STRUTTURATI in _prezzo_ld, che
    # e' della stessa famiglia dei tag NIP-99: schema.org vuole il
    # punto decimale, e una virgola li' dentro non sarebbe uno stile
    # italiano ma un numero illeggibile per chi lo consuma.
    # Se questo numero cambia: o e' nato un campo di protocollo nuovo,
    # o qualcuno ha ricominciato a scrivere un euro a mano.
    prova("...e i nove superstiti sono tutti censiti", 9,
          _SORGENTE.count(":.2f}"))

    # LA SENTINELLA DEI SATS, gemella. Le stringhe spezzate su piu'
    # righe si RICUCIONO prima di cercare: e' esattamente nella piega
    # — «… {netto} "» a capo «"sats …» — che due siti si erano
    # nascosti al censimento a mano, e una sentinella che non guarda
    # li' dentro certifica una pulizia che non c'e'.
    cucito = _re.sub(r'"\s*\n\s*f?"', "", _SORGENTE)
    grezzi = [m for m in _re.findall(r"\{[^{}]*\} ?sats", cucito)
              if "_fmt_sats" not in m]
    # I QUATTRO superstiti, e nessuno di loro e' testo per una
    # persona: una riga di journal (log diagnostico, un lettore solo),
    # la riga del catalogo che va in pasto ad Haiku, e le due righe di
    # prosa del NIP-99 che ripetono i tag a parole. Se il numero
    # cambia, qualcuno ha ricominciato a scrivere una cifra a mano.
    prova("nessuna cifra in sats sfugge a _fmt_sats (restano i quattro "
          "che una persona non legge)", 4, len(grezzi))
    # e le due convenzioni straniere non devono tornare: la virgola
    # inglese di {n:,} e lo spazio del .replace, che erano il terzo e
    # il quarto formato
    prova("...ne' la virgola inglese di {n:,}", 0,
          len(_re.findall(r"\{[^{}]*:,\} ?sats", cucito)))
    # ...e nemmeno lo spazio fatto a mano, che era il quarto formato.
    # I DUE superstiti non sono sats: sono le righe di journal del
    # cambio €/BTC («55 983 €/BTC»), un'altra cifra e un altro giro —
    # scritto qui perche' la prima stesura di questa sentinella li
    # aveva presi per sats e chiedeva zero.
    prova("...ne' il separatore a spazio fatto a mano (restano i due "
          "del cambio €/BTC, che sats non sono)", 2,
          _SORGENTE.count('.replace(",", " ")'))

    # --- 2) L'ESCAPING: qui il testo dell'utente sta in un ATTRIBUTO -
    # Una virgoletta non escapata non «si vede male»: chiude il
    # content e sputa il resto del titolo come markup.
    cattivo = 'Cuffie "AKG" <b> & l\'amico'
    m = amb["_meta_anteprima"](cattivo, "una descrizione", "https://x/y",
                               ("https://x/a.jpg", 0, 0))
    prova("il titolo cattivo non spezza l'attributo", False,
          f'content="{cattivo}"' in m)
    prova("...la virgoletta diventa entita'", True, "&quot;AKG&quot;" in m)
    prova("...e il minore pure", True, "&lt;b&gt;" in m)
    prova("...e l'apostrofo", True, "&#x27;" in m)
    # la prova vera dell'escaping non e' cercare le entita': e' che il
    # blocco resti fatto di attributi INTERI e rileggibili — se una
    # virgoletta passasse, il regex qui sotto troverebbe pezzi in piu'
    # e la riga si spezzerebbe a meta' del titolo
    contenuti = _re.findall(r'content="([^"]*)"', m)
    prova("restano i dodici attributi di base, interi", 12, len(contenuti))
    prova("...e ognuno si rilegge com'era", True,
          cattivo in [_html.unescape(v) for v in contenuti])

    # --- 3) misure dichiarate solo quando si sanno ------------------
    prova("il brand dichiara le sue misure", True, "og:image:width" in
          amb["_meta_anteprima"]("t", "d", "u"))
    prova("...il francobollo di un annuncio no (il lato dipende dalla "
          "foto, e un numero sbagliato e' peggio di uno assente)", False,
          "og:image:width" in
          amb["_meta_anteprima"]("t", "d", "u", ("https://x/a.jpg", 0, 0)))

    # --- 4) quale immagine finisce nella card -----------------------
    img = amb["_immagine_anteprima"]
    with tempfile.TemporaryDirectory() as d:
        amb["FOTO_DIR"] = d
        pieno = os.path.join(d, "a7_0_9.jpg")
        mini_f = os.path.join(d, "a7_0_9_min.jpg")
        for p in (pieno, mini_f):
            open(p, "w").close()
        prova("la card prende il francobollo, non il pieno",
              "https://barattolo.store/foto/a7_0_9_min.jpg",
              img('["a7_0_9.jpg"]')[0])
        os.remove(mini_f)
        prova("...senza francobollo ripiega sul pieno",
              "https://barattolo.store/foto/a7_0_9.jpg",
              img('["a7_0_9.jpg"]')[0])
        os.remove(pieno)
        # un og:image che non risponde e' peggio di nessun og:image:
        # diversi crawler, non trovandolo, non disegnano la card
        prova("...e su una foto sparita dal disco ripiega sul brand",
              amb["IMMAGINE_BRAND"], img('["a7_0_9.jpg"]'))
        prova("nessuna foto: il brand", amb["IMMAGINE_BRAND"], img("[]"))
        prova("foto illeggibile: il brand", amb["IMMAGINE_BRAND"],
              img("non e' json"))

        # --- 4bis) L'OG:IMAGE E' SOLO ROBA NOSTRA (M2 dell'audit) ---
        # Un URL remoto in colonna e' l'host di chi pubblica su Nostr,
        # e ci resta proprio quando lo scaricamento FALLISCE — cosa
        # che chi pubblica puo' provocare (403, redirect, corpo sopra
        # il tetto). In og:image quell'indirizzo diventa la campana di
        # chiunque veda l'anteprima: il crawler di ogni piattaforma e,
        # nei client che risolvono l'immagine, il telefono di gente
        # che Barattolo non l'ha mai aperto. E resta sostituibile dopo
        # la condivisione, a card gia' in giro.
        prova("l'URL remoto non finisce mai in og:image",
              amb["IMMAGINE_BRAND"],
              img('["https://blossom.example/x.jpg"]'))
        # e non basta scartare la PRIMA: se la remota e' in testa e una
        # nostra viene dopo, la card deve prendere la nostra — saltare
        # e' un `continue`, non un `return`
        for p in (os.path.join(d, "a9_1_3.jpg"),
                  os.path.join(d, "a9_1_3_min.jpg")):
            open(p, "w").close()
        prova("...e una foto nostra piu' in fondo si prende lo stesso",
              "https://barattolo.store/foto/a9_1_3_min.jpg",
              img('["https://blossom.example/x.jpg", "a9_1_3.jpg"]')[0])
        prova("...anche in http nudo", amb["IMMAGINE_BRAND"],
              img('["http://host.example/x.jpg"]'))
    amb["FOTO_DIR"] = "foto"

    # LA VETRINA NON SI TOCCA, ed e' dichiarato: nel client l'URL
    # remoto passa intero (fotoMini lo lascia stare), ed e' un'altra
    # superficie — li' l'immagine la chiede il browser di chi ha
    # aperto una scheda, non quello di chiunque riceva un link.
    mini_js = open("miniapp.html", encoding="utf-8").read()
    prova("in vetrina l'URL remoto passa ancora intero", True,
          "nome.startsWith('http')" in
          pezzo_js(mini_js, "function fotoMini(nome){", "\n}\n"))

    # --- 5) LA PROVA REGINA: solo gli attivi parlano ----------------
    con = _vetrina_finta(sqlite3.connect(":memory:"))
    for aid, stato in ((1, "attivo"), (2, "rimosso"), (3, "revisione"),
                       (4, "venduto")):
        con.execute(
            "INSERT INTO annunci (id, titolo, descrizione, zona, valuta, "
            "prezzo_sats, prezzo_eur, foto, stato, venditore_id, categoria, "
            "condizione) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (aid, f"SEGRETO{aid} cuffie da studio",
             f"RISERVATO{aid} in ottimo stato, poco usate.",
             "Frazione Salsasio, Carmagnola (TO)", "sats",
             80000, 0.0, "[]", stato, 777888999, "Audio e video", "buono"))
    # L'ORFANO: riga utente sparita. Fino a ieri questa query
    # interrogava la sola `annunci` e non poteva fallire per colpa del
    # venditore — con un INNER JOIN la sua anteprima si spegnerebbe, ed
    # e' una regressione silenziosa su cio' che funziona.
    con.execute(
        "INSERT INTO annunci (id, titolo, descrizione, zona, valuta, "
        "prezzo_sats, prezzo_eur, foto, stato, venditore_id, categoria) "
        "VALUES (5,'SEGRETO5 orfano','senza padrone','','sats',9000,0.0,"
        "'[]','attivo',424242,'Altro')")
    con.execute(
        "INSERT INTO utenti (tg_id, nome, username, negozio, rating, "
        "n_feedback) VALUES (777888999, 'Rosa', 'rosina', 'ab12cd34', "
        "4.75, 12)")
    con.commit()

    amb["db"] = _db_finto(con)
    # I costruttori tornano (titolo, testa, corpo): qui si guarda la
    # TESTA, che e' il blocco che i crawler leggono.
    ma = lambda aid: amb["_seo_annuncio"](aid)[1]        # noqa: E731
    mn = lambda chi: amb["_seo_negozio"](chi)[1]         # noqa: E731

    attivo = ma(1)
    prova("l'annuncio attivo racconta il suo titolo", True,
          "SEGRETO1 cuffie da studio" in attivo)
    prova("...col prezzo", True, "80.000 sats" in attivo)
    prova("...il comune, non la zona intera", True,
          "Carmagnola (TO)" in attivo and "Frazione Salsasio" not in attivo)
    prova("...e le prime righe della descrizione", True,
          "RISERVATO1" in attivo)
    prova("...e l'og:url canonico, con lo slug", True,
          'content="https://barattolo.store/annuncio/'
          '1-segreto1-cuffie-da-studio"' in attivo)
    prova("...e non si spaccia per venduto", False, "Venduto" in attivo)
    # L'ORFANO HA COMUNQUE LA SUA CARD: e' la prova che cade con un
    # INNER JOIN al posto del LEFT.
    prova("un annuncio senza venditore ha comunque la sua anteprima",
          True, "SEGRETO5 orfano" in ma(5))

    # IL VENDUTO E' UNO SCAFFALE VUOTO, non un annuncio che non c'e':
    # la scheda esiste ancora (/api/listings/{id} la serve dal cantiere
    # dello stock), quindi il link mandato a un amico non deve morire
    # con le scorte. Ma la card non deve nemmeno MENTIRE — e' il patto
    # di _caption_canale, che al venduto riscrive il post del canale.
    venduto = ma(4)
    prova("il venduto ha la sua anteprima vera", True,
          "SEGRETO4 cuffie da studio" in venduto)
    prova("...e lo DICE, in testa alla descrizione", True,
          'content="✅ Venduto · ' in venduto)
    prova("...senza perdere il link al suo scaffale", True,
          'content="https://barattolo.store/annuncio/'
          '4-segreto4-cuffie-da-studio"' in venduto)
    prova("...e resta indicizzabile: il link non muore con le scorte",
          False, "noindex" in venduto)

    # ECCO IL PUNTO: togliendo lo stato dalla WHERE, queste quattro
    # diventano rosse tutte insieme.
    for aid, stato in ((2, "rimosso"), (3, "revisione")):
        m = ma(aid)
        prova(f"un annuncio {stato} ricade sui generici, col noindex",
              MUTO, m)
        prova(f"...e di lui non trapela una parola ({stato})", True,
              f"SEGRETO{aid}" not in m and f"RISERVATO{aid}" not in m)
        # niente canonical su una pagina deindicizzata: puntando
        # ALTROVE propagherebbe il noindex all'indirizzo canonico
        prova(f"...e nessun canonical se ne va in giro ({stato})", False,
              "canonical" in m)
    prova("un annuncio che non esiste: generici e noindex", MUTO, ma(999))
    prova("...e uno il cui id non e' un id nemmeno lo cerca", MUTO,
          amb["_seo_annuncio"](amb["_id_da_percorso"]("pippo"))[1])

    # e i due elenchi non possono divergere: quello che la scheda
    # serve e' quello di cui l'anteprima puo' parlare, o si manda un
    # link con una bella card che poi atterra su un «non trovato»
    corpo_rotta = _SORGENTE[_SORGENTE.index('@app.get("/api/listings/'
                                            '{annuncio_id}")'):]
    corpo_rotta = corpo_rotta[:corpo_rotta.index("\n\n\n")]
    stati_scheda = _re.findall(r"stato IN \(([^)]+)\)", corpo_rotta)
    stati_meta = _re.findall(r"stato IN \(([^)]+)\)", pezzo("_seo_annuncio"))
    prova("l'anteprima parla degli stessi stati che la scheda serve",
          stati_scheda, stati_meta)

    # --- 6) il negozio: quel che esce e quel che non esce -----------
    neg = mn("rosina")
    prova("il negozio si trova per username", True, "Rosa su Barattolo" in neg)
    prova("...e per codice", neg, mn("ab12cd34"))
    prova("...conta i soli annunci ATTIVI", True,
          "1 oggetto in vetrina" in neg)
    prova("...mostra le stelle all'italiana", True, "4,8 (12)" in neg)
    prova("...porta il CODICE nell'og:url, mai il `chi` dell'URL", True,
          'content="https://barattolo.store/negozio/ab12cd34-rosa"' in neg)
    # il tg_id non esce mai in vetrina: qui serve solo a contare
    prova("...e il tg_id del venditore non esce da nessuna parte", True,
          "777888999" not in neg)
    prova("un negozio che non esiste: generici e noindex", MUTO,
          mn("nessuno"))
    # LO SPACCO SUL PRIMO TRATTINO: username, codice e codice con lo
    # slug appiccicato devono dire tutti la stessa cosa.
    prova("...e le tre strade portano allo stesso canonical", True,
          mn("rosina") == mn("ab12cd34") == mn("ab12cd34-la-bottega-di-rosa"))

    # --- 7) la cintura: un ornamento non manda giu' il mercatino ----
    def esplode(*a):
        raise RuntimeError("database in fiamme")

    prova("un'anteprima che esplode ricade sui generici", ("", GEN, ""),
          amb["_seo_o_generici"](esplode, 1))

    # --- 8) i due file restano allineati ---------------------------
    # Il segno e' il punto in cui i meta si infilano. Se qualcuno
    # ritocca le prime righe di miniapp.html il server non cade (il
    # ripiego serve la pagina senza meta), ma le anteprime si
    # spengono in silenzio: e' questa prova a dirlo.
    mini = open("miniapp.html", "rb").read()
    prova("il segno dove si infilano i meta esiste in miniapp.html", 1,
          mini.count(amb["SEGNO_META"]))
    prova("...ed e' in cima, prima di ogni altro meta", True,
          mini.index(amb["SEGNO_META"]) < mini.index(b'<meta name="viewport"'))
    prova("...e non nomina il fine-riga, che cambia da un disco "
          "all'altro", False,
          b"\n" in amb["SEGNO_META"] or b"\r" in amb["SEGNO_META"])

    # --- 8bis) e il taglio si esercita DAVVERO, sul file vero ------
    # Il punto 2 del cantiere: i meta vanno DOPO il charset (che per
    # specifica deve restare nei primi 1024 byte) e comunque in cima,
    # perche' parecchi crawler smettono di scaricare molto prima della
    # fine di 900 KB. Qui HTMLResponse e' di cartone: serve il corpo,
    # non fastapi.
    amb["HTMLResponse"] = lambda corpo, headers=None: corpo
    amb["HEADER_NO_CACHE"] = {}
    exec(pezzo("_pagina_con_meta"), amb)
    pagina = amb["_pagina_con_meta"]("<!--SEGNAPOSTO-->\n")
    prova("il charset resta il primo tag della pagina", True,
          0 < pagina.index(amb["SEGNO_META"]) < pagina.index(b"<!--SEGNAPOSTO"))
    prova("...e i meta stanno subito dietro, prima del titolo", True,
          pagina.index(b"<!--SEGNAPOSTO") < pagina.index(b"<title>"))
    # LA PAGINA ESCE IDENTICA A COM'E' SUL DISCO, byte per byte: la
    # modalita' testo normalizzerebbe i fine-riga, e sarebbero 15 KB
    # di differenza su cio' che scarica ogni utente — un effetto
    # collaterale di un ornamento.
    prova("...e la pagina esce identica al file, byte per byte", mini,
          pagina.replace(b"\n<!--SEGNAPOSTO-->", b""))

    # --- 8ter) senza il segno la pagina VIVE, muta ------------------
    # Un'anteprima e' un ornamento: se qualcuno ritocca le prime righe
    # di miniapp.html i meta si perdono, ma il mercatino si apre.
    import tempfile as _tmp
    dove_ero = os.getcwd()
    with _tmp.TemporaryDirectory() as d:
        with open(os.path.join(d, "miniapp.html"), "wb") as fh:
            fh.write(b"<!DOCTYPE html>\n<html><head><title>x</title>\n")
        try:
            os.chdir(d)
            amb["_PAGINA_CACHE"].update(timbro=False)
            muta = amb["_pagina_con_meta"]("<!--SEGNAPOSTO-->\n")
        finally:
            os.chdir(dove_ero)
            amb["_PAGINA_CACHE"].update(timbro=False)
    prova("segno sparito: la pagina esce comunque intera", True,
          b"<title>x</title>" in muta)
    prova("...e senza i meta appesi in un posto a caso", False,
          b"SEGNAPOSTO" in muta)

    # --- 9) nessuna rotta condivisibile torna a servire il file nudo -
    # E' la riga che sparisce in un riordino senza rompere niente di
    # visibile: la pagina si aprirebbe uguale, e a mancare sarebbe
    # solo l'anteprima — cioe' proprio la cosa che nessuno guarda.
    ROTTE_PAGINA = ('@app.get("/")', '@app.get("/miniapp.html")',
                    '@app.get("/negozio/{chi}")',
                    '@app.get("/annuncio/{aid}")',
                    '@app.get("/categoria/{slug}")',
                    '@app.get("/sicurezza")',
                    '@app.get("/privacy")')
    for rotta in ROTTE_PAGINA:
        i = _SORGENTE.index(rotta)
        corpo = _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]
        prova(f"{rotta} passa dai meta e non dal file nudo", True,
              "_pagina_con_meta(" in corpo and "FileResponse(" not in corpo)
    # e le tre che portano dati passano dalla cintura
    for rotta, quale in (('@app.get("/negozio/{chi}")', "_seo_negozio"),
                         ('@app.get("/annuncio/{aid}")', "_seo_annuncio"),
                         ('@app.get("/categoria/{slug}")', "_seo_categoria")):
        i = _SORGENTE.index(rotta)
        corpo = _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]
        prova(f"{quale} passa dalla cintura fail-open", True,
              f"_seo_o_generici({quale}" in corpo)
    # E IL BUCO CHE QUESTA LISTA AVEVA: era scritta a mano, quindi una
    # rotta pubblica NUOVA non la sorvegliava nessuno finche' qualcuno
    # non si ricordava di aggiungerla qui. Adesso il conto deve tornare:
    # chi ne aggiunge una senza elencarla trova la CI rossa.
    prova("le rotte che servono la pagina sono tutte in elenco",
          len(ROTTE_PAGINA), _SORGENTE.count("return _pagina_con_meta("))


def prove_seo():
    """FARSI TROVARE (ago 2026): indirizzi parlanti, un titolo per
    pagina, la mappa del sito, il contenuto anche nel corpo.

    La prova che vale di piu' e' quella di COERENZA fra sitemap e
    noindex: niente di cio' che elenchiamo puo' portare noindex — e'
    una contraddizione che Search Console segnala — e le due condizioni
    devono nascere dallo stesso fatto, non da due «if» gemelli che un
    giorno divergono."""
    print("\n[farsi trovare]")
    import html as _html
    import json as _json
    import re as _re
    import sqlite3

    amb = _amb_seo()
    slug = amb["_slug"]

    # --- 1) LO SLUG ------------------------------------------------
    casi = [("Bicicletta da corsa Bianchi", "bicicletta-da-corsa-bianchi"),
            ("Città dei ragazzi", "citta-dei-ragazzi"),
            ("Cuffie \"AKG\" & co.", "cuffie-akg-co"),
            ("L'ombrello di Sant'Angelo", "l-ombrello-di-sant-angelo"),
            ("🔥🔥", ""), ("自転車", ""), ("!!! ???", ""),
            ("", ""), (None, "")]
    for testo, atteso in casi:
        prova(f"slug di {testo!r}", atteso, slug(testo))
    lungo = slug("parola " * 40)
    prova("un titolo lungo si taglia sotto la misura", True,
          len(lungo) <= amb["MAX_SLUG"])
    prova("...a parola intera", True, lungo.endswith("parola"))
    prova("...senza trattino orfano in coda", False, lungo.endswith("-"))
    # NON e' _taglia_meta: il puntino di sospensione in un URL non ci va
    prova("...e senza il puntino di sospensione", False, "…" in lungo)
    prova("una parola unica piu' lunga del tetto si taglia comunque",
          amb["MAX_SLUG"], len(slug("a" * 200)))
    # L'IDEMPOTENZA cattura da sola quasi ogni futuro errore qui dentro
    for testo, _ in casi:
        prova(f"slug idempotente su {testo!r}", slug(testo),
              slug(slug(testo)))
    # LA TOTALITA': e' su questa che poggia il fatto che gli indirizzi
    # costruiti da qui non abbiano bisogno di nessun filtro. Se _slug
    # smettesse di essere totale, ogni URL diventerebbe un punto
    # d'iniezione.
    velenosi = ['"><script>alert(1)</script>', "../../config.py",
                "a?b=1&c=2#frammento", "%2e%2e%2f", "Valle d'Aosta",
                "‮ordine rovesciato", "a\nb\tc"]
    for v in velenosi + [c[0] for c in casi if c[0]]:
        prova(f"lo slug resta [a-z0-9-] su {v!r}", True,
              bool(_re.fullmatch(r"[a-z0-9]*(-[a-z0-9]+)*", slug(v))))

    # --- 1ter) UN NOME PUO' ESSERE UN RECAPITO ---------------------
    # Caso vero dal campo: un venditore si chiama come il proprio
    # Lightning address, `normalizza` lo scioglie docilmente, e il
    # recapito diventa un indirizzo web — per giunta PROPOSTO ai motori
    # dalla sitemap. La guardia sbaglia nel verso giusto: un falso
    # positivo costa l'ornamento, un falso negativo costa il recapito
    # di una persona dentro l'indice.
    pare = amb["_pare_recapito"]
    VERO = "doc557@marshylift40.phoenixwallet.me"
    prova("il caso dal campo e' un recapito", True, pare(VERO))
    prova("...e il suo slug non si fa proprio", "", slug(VERO))
    prova("...quindi resta il solo codice negozio",
          "https://barattolo.store/negozio/57b27cf6",
          amb["_url_negozio"]("57b27cf6", VERO))
    for t in ("satoshi@walletofsatoshi.com", "mario.rossi@gmail.com",
              "phoenixwallet.me", "zbd.gg", "ln.tips", "getalby.com",
              "Pago solo su pippo@wallet.com", "scrivimi@qui.it",
              # LA REGOLA DEI DUE PUNTI non dipende dall'elenco, e va
              # provata con un caso in cui NESSUNA etichetta e' un TLD
              # noto — altrimenti a prenderlo e' l'elenco e la regola
              # si puo' togliere senza che nessuna prova se ne accorga
              # (successo davvero, con «tizio.wallet.qualcosa»: la
              # tortura l'ha smascherato, la rilettura no).
              "tizio.borsellino.chissacosa"):
        prova(f"recapito: {t!r}", True, pare(t))
        prova(f"...e niente slug per {t!r}", "", slug(t))
    # e il rovescio, che e' la meta' che costa: la roba legittima non
    # deve perdere il suo slug. Misurato sugli 888 titoli e sui 24 nomi
    # veri del database di collaudo: zero falsi positivi.
    for t in ("Bicicletta da corsa Bianchi", "Sedia mod. 3 pezzi",
              "Nikon D3.200", "N.B. leggere bene", "Cuffie AKG K371",
              'Cuffie "AKG" & co.', "Art. 15 comma 3", "Vaso in ceramica"):
        prova(f"non e' un recapito: {t!r}", False, pare(t))
    prova("...e il loro slug resta intero", "bicicletta-da-corsa-bianchi",
          slug("Bicicletta da corsa Bianchi"))
    # VALE ANCHE PER GLI ANNUNCI: un titolo puo' contenerne uno, e la
    # guardia sta dentro _slug proprio perche' la ereditino tutti.
    prova("un titolo col recapito perde lo slug, non l'indirizzo",
          "https://barattolo.store/annuncio/13334",
          amb["_url_annuncio"](13334, "Vendo bici, scrivi a mario@rossi.it"))
    # LA GUARDIA GUARDA IL TESTO GREZZO: dopo `normalizza` la
    # chiocciola e i punti sono spazi, e un Lightning address e'
    # indistinguibile da una frase. Spostarla dopo la renderebbe
    # inerte senza rompere niente di visibile.
    corpo_slug = pezzo("_slug")
    prova("sentinella: la guardia gira PRIMA di normalizza", True,
          corpo_slug.index("_pare_recapito(")
          < corpo_slug.index("normalizza("))
    prova("sentinella: e sta dentro _slug, cosi' la ereditano tutti", 1,
          _SORGENTE.count("if _pare_recapito(testo):"))

    # --- 1bis) _slug e slug_categoria sono DUE COSE ----------------
    # La seconda lavora su un catalogo chiuso e il suo prodotto e' un
    # NOME DI FILE su disco: cambiarla spegne 27 illustrazioni. Oggi le
    # due combaciano; il giorno che qualcuno aggiunge «Musica & film»
    # slug_categoria darebbe «musica-&-film» — file rotto E indirizzo
    # rotto — e questa diventa rossa, che e' quando serve saperlo.
    storte = [c for c in amb["CATEGORIE"]
              if slug(c) != amb["slug_categoria"](c)]
    prova("ogni categoria ha lo stesso slug nelle due funzioni", [], storte)

    # --- 2) L'ID DAL PERCORSO --------------------------------------
    idp = amb["_id_da_percorso"]
    for testo, atteso in (("13334", 13334), ("13334-bici", 13334),
                          ("13334-", 13334), ("0", 0),
                          ("pippo", None), ("", None), (None, None),
                          ("-13", None), (" 13", None), ("+13", None),
                          ("1_3", None), ("١٣", None), ("13.0", None),
                          ("9" * 30, None)):
        prova(f"id da {testo!r}", atteso, idp(testo))

    # --- 3) IL NEGOZIO DAL PERCORSO --------------------------------
    chip = amb["_chi_da_percorso"]
    for testo, atteso in (("rosina", "rosina"), ("mario_rossi", "mario_rossi"),
                          ("ab12cd34", "ab12cd34"),
                          ("ab12cd34-la-bottega", "ab12cd34"),
                          ("", ""), (None, "")):
        prova(f"chi da {testo!r}", atteso, chip(testo))

    # --- 4) LE TRE FESSURE, su byte sintetici ----------------------
    spezza, monta = amb["_spezza_pagina"], amb["_monta_pagina"]
    FINTA = (b'<html><head><meta charset="UTF-8">\r\n<title>X</title>\r\n'
             b'</head><body><div id="cartello"></div><div id="app">'
             b"</div></body></html>")
    p = spezza(FINTA)
    prova("le tre fessure si trovano tutte", (True, True, True),
          (p["ha_meta"], p["ha_titolo"], p["ha_corpo"]))
    prova("senza niente da infilare esce il file, byte per byte", FINTA,
          monta(p, "", "", ""))
    pieno = monta(p, "<meta name=x>", "NUOVO", "<h1>ciao</h1>")
    prova("...il titolo si sostituisce, e resta uno solo",
          (1, 1), (pieno.count(b"<title>"), pieno.count(b"</title>")))
    prova("...ed e' quello nuovo", True, b"<title>NUOVO</title>" in pieno)
    prova("...il cartello si riempie", True,
          b'<div id="cartello"><h1>ciao</h1></div>' in pieno)
    prova("...e i fine-riga di Windows sopravvivono", 2, pieno.count(b"\r\n"))
    # ogni fessura si spegne per conto suo, e sempre da VALLE
    senza_c = FINTA.replace(b'<div id="cartello"></div>', b"")
    prova("senza il cartello, le altre due vivono",
          (True, True, False), tuple(spezza(senza_c)[k] for k in
                                     ("ha_meta", "ha_titolo", "ha_corpo")))
    senza_t = FINTA.replace(b"<title>X</title>", b"")
    prova("senza il titolo si spegne anche il cartello, mai il contrario",
          (True, False, False), tuple(spezza(senza_t)[k] for k in
                                      ("ha_meta", "ha_titolo", "ha_corpo")))
    # IL CARTELLO DEVE ESSERE VUOTO: se qualcuno ci mette dentro
    # qualcosa a mano la fessura si chiude e la pagina esce INTATTA,
    # invece di uscire mescolata
    sporco = FINTA.replace(b'<div id="cartello"></div>',
                           b'<div id="cartello">roba</div>')
    p2 = spezza(sporco)
    prova("un cartello non vuoto spegne la sua fessura", False,
          p2["ha_corpo"])
    prova("...e la pagina esce comunque intera", sporco,
          monta(p2, "", "", "<h1>x</h1>"))

    # --- 4bis) e il segno del cartello esiste nel file VERO ---------
    mini = open("miniapp.html", "rb").read()
    apre, chiude = amb["SEGNO_CORPO"]
    prova("il cartello esiste in miniapp.html, una volta sola", 1,
          mini.count(apre))
    prova("...ed e' VUOTO, coi due tag adiacenti", 1,
          mini.count(apre + chiude))
    prova("...e sta dentro #app", True,
          mini.index(b'<div id="app">') < mini.index(apre))

    # --- 5) L'ESCAPING, coi tre regimi in un colpo -----------------
    CATTIVO = ('Cuffie "AKG" <b> & </title></div><script>alert(1)</script>'
               " l'amico")
    con = _vetrina_finta(sqlite3.connect(":memory:"))
    con.execute(
        "INSERT INTO annunci (id, titolo, descrizione, zona, valuta, "
        "prezzo_sats, prezzo_eur, foto, stato, venditore_id, categoria, "
        "condizione, quantita) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (1, CATTIVO, CATTIVO, "", "sats", 80000, 0.0, "[]", "attivo",
         777, "Audio e video", "nuovo", 1))
    con.execute("INSERT INTO utenti (tg_id, nome, username, negozio, "
                "rating, n_feedback) VALUES (777, ?, 'rosina', 'ab12cd34', "
                "0, 0)", (CATTIVO,))
    con.commit()
    amb["db"] = _db_finto(con)
    amb["HTMLResponse"] = lambda corpo, headers=None: corpo
    amb["HEADER_NO_CACHE"] = {}
    exec(pezzo("_pagina_con_meta"), amb)
    amb["_PAGINA_CACHE"].update(timbro=False)
    titolo, testa, corpo = amb["_seo_annuncio"](1)
    pagina = amb["_pagina_con_meta"](testa, titolo, corpo).decode("utf-8")

    prova("il carico non diventa mai markup", False,
          "<script>alert(1)" in pagina)
    prova("...e la pagina ha UN titolo solo",
          (1, 1), (pagina.count("<title>"), pagina.count("</title>")))
    # IL TITOLO E' UN NODO DI TESTO, ed e' il posto in cui questo
    # cantiere aveva gia' sbagliato una volta: usciva crudo, e un
    # «</title>» in un titolo d'annuncio si portava dietro mezza pagina.
    prova("...perche' anche il titolo passa dall'escape", False,
          "<" in titolo)
    prova("...e UN cartello solo", 1, pagina.count('<div id="cartello">'))
    # la prova vera dell'escaping non e' cercare le entita': e' che gli
    # attributi restino INTERI e rileggibili
    for chiave in ("content", "href", "src", "alt"):
        valori = _re.findall(rf'{chiave}="([^"]*)"', pagina)
        rotti = [v for v in valori if "<" in _html.unescape(v)
                 and "</title>" not in _html.unescape(v)]
        prova(f"ogni {chiave}= si rilegge com'era", [], rotti)
    prova("il titolo cattivo si rilegge intero da un attributo", True,
          CATTIVO in [_html.unescape(v)
                      for v in _re.findall(r'content="([^"]*)"', pagina)])
    # IL TERZO REGIME: se qualcuno ci mette un html.escape, il valore
    # riletto contiene «&amp;» e questa diventa rossa. E' l'asserzione
    # che distingue il JSON-LD dagli attributi.
    grezzo = _re.search(r'application/ld\+json">(.*?)</script>',
                        pagina, _re.S)
    prova("il blocco dei dati strutturati c'e'", True, bool(grezzo))
    dati = _json.loads(grezzo.group(1))
    prova("...ed e' JSON valido col titolo VERO, carattere per carattere",
          CATTIVO, dati["name"])
    prova("...senza entita' HTML dentro", False, "&amp;" in grezzo.group(1))
    prova("...e senza poter chiudere il proprio <script>", False,
          "</script>" in grezzo.group(1)[:-1])

    # --- 6) I DATI STRUTTURATI -------------------------------------
    pl = amb["_prezzo_ld"]
    # sats -> BTC e' una conversione ESATTA: la virgola mobile e' il
    # modo di sbagliarla, e 0.0008000000000000001 finirebbe nell'indice
    for sats, atteso in ((1, "0.00000001"), (80_000, "0.00080000"),
                         (100_000_000, "1.00000000"),
                         (2_100_000_000_000_000, "21000000.00000000")):
        prova(f"{sats} sats in BTC", (atteso, "BTC"),
              pl({"valuta": "sats", "prezzo_sats": sats}))
    prova("...e mai col residuo della virgola mobile", False,
          "0.0008000000000000001" == pl({"prezzo_sats": 80_000})[0])
    prova("un listino nato in euro parla euro", ("38.50", "EUR"),
          pl({"valuta": "eur", "prezzo_eur": 38.5, "prezzo_sats": 70000}))

    dl = amb["_disponibilita_ld"]
    prova("un attivo con pezzi e' disponibile", ("InStock", ""),
          dl({"stato": "attivo", "quantita": 3}))
    prova("un venduto e' uno scaffale vuoto", ("SoldOut", ""),
          dl({"stato": "venduto", "quantita": 0}))
    prova("un attivo a zero pezzi non finge", ("OutOfStock", ""),
          dl({"stato": "attivo", "quantita": 0}))
    domani = int(_time_seo() + 86400)
    disp, riparte = dl({"stato": "attivo", "quantita": 1,
                        "venditore_ferie": domani})
    prova("in ferie non si compra, e si dice DA QUANDO si potra'",
          ("OutOfStock", True), (disp, bool(riparte)))
    # al filo esatto il negozio e' APERTO, come _asta_viva
    filo = int(_time_seo())
    prova("...e al secondo esatto del rientro e' gia' aperto", "InStock",
          dl({"stato": "attivo", "quantita": 1, "venditore_ferie": filo})[0])

    LD = amb["CONDIZIONI_LD"]
    prova("le cinque condizioni sono mappate", 5, len(LD))
    prova("«come nuovo» NON e' «ricondizionato»", "UsedCondition",
          LD["come_nuovo"])
    prova("il nuovo e' nuovo", "NewCondition", LD["nuovo"])
    prova("il da sistemare e' danneggiato", "DamagedCondition",
          LD["da_sistemare"])
    # dove la scala non dice niente la proprieta' SI OMETTE, e il
    # giudice e' condizione_da_mostrare: dichiarare UsedCondition per
    # riempimento su un vasetto di marmellata sarebbe falso
    miele = {"titolo": "Miele", "categoria": "Alimenti e bevande",
             "consegna": "", "condizione": "buono", "prezzo_sats": 1000,
             "stato": "attivo", "quantita": 1}
    prova("una categoria esente non dichiara nessuna condizione", False,
          "itemCondition" in amb["_ld_annuncio"](miele, "u", ""))
    prova("...anche col residuo in colonna", "",
          amb["condizione_da_mostrare"](miele))

    # --- 7) MAI il voto del VENDITORE sul prodotto -----------------
    # E' forte la tentazione (u.rating ce l'abbiamo), ma quel voto e'
    # della persona, non dell'oggetto: sul Product sarebbe lo schema
    # delle recensioni auto-attribuite che Google sanziona.
    # Si cerca la CHIAVE fra virgolette, non la parola: il commento qui
    # sopra la nomina apposta, e una sentinella che inciampa nella
    # propria documentazione non sorveglia niente.
    testo_ld = pezzo("_ld_annuncio")
    prova("nessun aggregateRating sul prodotto", True,
          '"aggregateRating"' not in testo_ld and '"review"' not in testo_ld)

    # --- 8) ROBOTS.TXT: indistruttibile e prudente -----------------
    esploso = dict(amb)
    esploso["db"] = lambda: 1 / 0
    prova("robots.txt non tocca il database", True,
          "db(" not in _SORGENTE[_SORGENTE.index("def robots_txt("):
                                 _SORGENTE.index("TETTO_SITEMAP")])
    robots = amb["ROBOTS_TXT"]
    prova("robots.txt dichiara la sitemap", True, "Sitemap: " in robots)
    prova("...e vieta le API", True, "Disallow: /api/" in robots)
    # TRE RIGHE A GUARDIA DELL'ERRORE PIU' COSTOSO DEL CANTIERE: non si
    # blocca in robots.txt cio' che si vuole deindicizzare (il noindex
    # non verrebbe mai letto), e «Disallow: /» si recupera in settimane.
    for quale in ("/annuncio", "/negozio", "/categoria", "/miniapp.html",
                  "/foto"):
        prova(f"...e NON vieta {quale}", False,
              f"Disallow: {quale}" in robots)
    prova("...e non c'e' nessun Disallow secco", False,
          "Disallow: /\n" in robots)

    # --- 9) LA MAPPA E IL NOINDEX NON SI CONTRADDICONO -------------
    con2 = _vetrina_finta(sqlite3.connect(":memory:"))
    for aid, stato, cat, ven in ((1, "attivo", "Biciclette", 10),
                                 (2, "attivo", "Biciclette", 10),
                                 (3, "venduto", "Bitcoin", 10),
                                 (4, "rimosso", "Bitcoin", 10),
                                 (5, "revisione", "Motori", 11),
                                 (6, "attivo", "Motori", 11)):
        con2.execute(
            "INSERT INTO annunci (id, titolo, descrizione, zona, valuta, "
            "prezzo_sats, prezzo_eur, foto, stato, venditore_id, categoria, "
            "quantita, creato) VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?)",
            (aid, f"Oggetto {aid}", "descrizione", "", "sats", 1000, 0.0,
             "[]", stato, ven, cat, 1_700_000_000 + aid))
    con2.execute("INSERT INTO utenti (tg_id, nome, username, negozio, "
                 "rating, n_feedback) VALUES (10,'Rosa','rosina','aaaa1111',"
                 "0,0)")
    # un negozio con SOLO roba non pubblica: pagina sottile, fuori
    con2.execute("INSERT INTO utenti (tg_id, nome, username, negozio, "
                 "rating, n_feedback) VALUES (12,'Vuoto','vuoto','cccc3333',"
                 "0,0)")
    # QUESTO si chiama come il proprio Lightning address, ed e' il caso
    # vero dal campo: deve stare in mappa col codice NUDO.
    con2.execute("INSERT INTO utenti (tg_id, nome, username, negozio, "
                 "rating, n_feedback) VALUES (11,?,'bea','bbbb2222',0,0)",
                 ("doc557@marshylift40.phoenixwallet.me",))
    con2.commit()
    amb["db"] = _db_finto(con2)
    amb["_SITEMAP_CACHE"].update(quando=0.0, xml=b"")
    xml = amb["_sitemap"]().decode("utf-8")
    loc = _re.findall(r"<loc>(.*?)</loc>", xml)
    prova("la sitemap non elenca i rimossi", False,
          any("/annuncio/4-" in x for x in loc))
    prova("...ne' quelli in revisione", False,
          any("/annuncio/5-" in x for x in loc))
    prova("...ne' i venduti (il link vive, ma non lo proponiamo noi)",
          False, any("/annuncio/3-" in x for x in loc))
    prova("...ne' i negozi senza merce", False,
          any("cccc3333" in x for x in loc))
    prova("...ne' i reparti vuoti", False,
          any("/categoria/animali" in x for x in loc))
    # IL RECAPITO NON ENTRA NELLA MAPPA, ed e' la prova che il caso dal
    # campo non puo' tornare: il negozio c'e' (ha merce), ma il suo
    # <loc> e' il codice nudo e del Lightning address non resta traccia
    # in tutto il file.
    prova("un negozio che si chiama come un recapito sta in mappa "
          "col codice nudo", True,
          "https://barattolo.store/negozio/bbbb2222" in loc)
    prova("...e del recapito non resta traccia nella mappa", False,
          "phoenixwallet" in xml or "marshylift" in xml)
    prova("...e gli attivi ci sono tutti e tre", 3,
          sum(1 for x in loc if "/annuncio/" in x))
    prova("...con la home e le due pagine che si mandano a chi chiede",
          True,
          "https://barattolo.store" in loc
          and "https://barattolo.store/sicurezza" in loc
          and "https://barattolo.store/privacy" in loc)
    prova("nessuna data del 1970 nella mappa", False, "1970" in xml)

    # LA PROVA DI COERENZA: si chiama il costruttore di OGNI indirizzo
    # elencato, e nessuno deve dire noindex; e il suo canonical deve
    # essere identico al <loc>, o si consegna a Google un rapporto di
    # contenuti duplicati scritto di proprio pugno.
    contraddizioni = []
    for x in loc:
        if "/annuncio/" in x:
            _, t, _c = amb["_seo_annuncio"](
                amb["_id_da_percorso"](x.rsplit("/", 1)[1]))
        elif "/negozio/" in x:
            _, t, _c = amb["_seo_negozio"](x.rsplit("/", 1)[1])
        elif "/categoria/" in x:
            _, t, _c = amb["_seo_categoria"](x.rsplit("/", 1)[1])
        else:
            continue
        can = _re.search(r'rel="canonical" href="([^"]*)"', t)
        if "noindex" in t or not can or can.group(1) != x:
            contraddizioni.append(x)
    prova("niente di cio' che e' nella mappa porta noindex", [],
          contraddizioni)
    # e il rovescio: cio' che NON e' nella mappa lo dice col noindex
    for chi, atteso in ((amb["_seo_negozio"]("cccc3333"), "negozio vuoto"),
                        (amb["_seo_categoria"]("animali"), "reparto vuoto"),
                        (amb["_seo_categoria"]("inventata"), "reparto finto")):
        prova(f"un {atteso} resta fuori dall'indice", True,
              "noindex" in chi[1])

    # --- 10) IL CARTELLO PORTA I COLLEGAMENTI ----------------------
    _, _, corpo_cat = amb["_seo_categoria"]("biciclette")
    prova("il reparto elenca la sua merce come link veri", 2,
          corpo_cat.count("/annuncio/"))
    prova("...e porta ai 27 reparti", len(amb["CATEGORIE"]),
          corpo_cat.count("/categoria/"))
    _, _, corpo_neg = amb["_seo_negozio"]("rosina")
    prova("il negozio elenca la sua merce", 2, corpo_neg.count("/annuncio/"))
    amb["_SEO_HOME_CACHE"].update(quando=0.0, roba=None)
    _, _, corpo_home = amb["_seo_home"]()
    prova("la home porta agli annunci", 3, corpo_home.count("/annuncio/"))
    prova("...e ai reparti", len(amb["CATEGORIE"]),
          corpo_home.count("/categoria/"))
    # LA CACHE della home: e' cio' che rende accettabile il cambio di
    # natura della rotta piu' colpita di tutte (fino a ieri non toccava
    # il database).
    amb["db"] = lambda: 1 / 0
    prova("la home in cache non ribussa al database", corpo_home,
          amb["_seo_home"]()[2])

    # --- 11) LE SENTINELLE -----------------------------------------
    # Ognuna cerca il CODICE e mai la parola: i commenti qui accanto
    # nominano apposta cio' che vietano, e una sentinella che inciampa
    # nella propria documentazione non sorveglia niente — e' l'errore
    # che ho fatto scrivendole la prima volta.
    testa_seo = pezzo("_testa_seo")
    prova("sentinella: nessun canonical su una pagina deindicizzata",
          True, testa_seo.index("if not indicizza")
          < testa_seo.index('rel="canonical"'))
    prova("sentinella: i meta non portano un <title> (ne uscirebbero due)",
          False, "<title" in pezzo("_meta_anteprima"))
    # IL LISTINO CONTRO LA LAMPO: il modo di garantirlo e' non avere le
    # colonne in mano (si cercano i NOMI di colonna, non la parola)
    prova("sentinella: la query SEO non pesca la lampo", False,
          "lampo_" in pezzo("_seo_annuncio"))
    prova("sentinella: il JSON-LD non passa da html.escape", False,
          "html.escape(" in pezzo("_ld"))
    prova("sentinella: il LEFT JOIN, o l'orfano perde la sua card", True,
          "LEFT JOIN utenti" in pezzo("_seo_annuncio"))
    prova("sentinella: la pagina si monta con join, mai con +=", True,
          'b"".join(' in pezzo("_monta_pagina"))
    prova("sentinella: l'id si legge col giudice, mai con int()", True,
          "_id_da_percorso(" in _SORGENTE[
              _SORGENTE.index('@app.get("/annuncio/{aid}")'):
              _SORGENTE.index('@app.get("/categoria/{slug}")')])
    prova("sentinella: il reparto passa dal catalogo chiuso", True,
          "_categoria_da_slug(" in pezzo("_seo_categoria"))
    # anche l'API del negozio deve spaccare sul trattino, o il negozio
    # non si apre per una persona vera mentre i meta erano perfetti
    corpo_api = _SORGENTE[_SORGENTE.index('@app.get("/api/negozio/{chi}")'):]
    prova("sentinella: anche /api/negozio spacca sul primo trattino", True,
          "_chi_da_percorso(chi)" in corpo_api[:corpo_api.index("\n\n\n")])
    prova("sentinella: offline.html resta fuori dall'indice", True,
          'name="robots" content="noindex' in open(
              "offline.html", encoding="utf-8").read())

    # --- 12) IL CLIENT: la card e' un collegamento vero -------------
    # Si rilegge in modalita' TESTO, come fanno tutte le altre prove sul
    # client, e non si decodifica il `mini` binario di sopra: sul disco
    # di chi scrive i fine-riga sono \r\n, e pezzo_js cerca "\n\n" —
    # decodificando i byte grezzi non troverebbe mai una riga vuota. Le
    # due letture servono due mestieri diversi: quella binaria l'uscita
    # byte per byte, questa il testo.
    testo_mini = open("miniapp.html", encoding="utf-8").read()
    card = pezzo_js(testo_mini, "const cardHTML = l => {")
    i_a, i_fine = card.index('<a class="card-link'), card.index("</a>")
    prova("il contenitore .card non porta piu' un onclick", False,
          "onclick" in card[card.index('<div class="card'):i_a])
    # UN <button> DENTRO UN <a> E' HTML NON VALIDO: i due bottoni
    # stanno fuori, il badge di stato (che e' un <div>) resta dentro —
    # cosi' le sue cinque regole CSS non si toccano.
    prova("il barattolino sta FUORI dall'<a>", True,
          card.index("${jar}") > i_fine)
    prova("...e il bottone del rifornimento pure", True,
          card.index("${rif}") > i_fine)
    prova("il badge di stato invece resta DENTRO", True,
          card.index("${flash}") < i_fine)
    # LA RIGA CHE, SE MANCA, SFREGIA L'APP: senza, i bottoni risalgono
    # fino al blocco iniziale e tutti i barattolini si accatastano in
    # alto a destra. E nel carrello sembrerebbe giusto (.pacco-cella e'
    # gia' relative): e' l'unica prova che vede la differenza.
    prova("la card e' il riferimento dei bottoni sulla foto", True,
          ".card{" in testo_mini.replace(" ", "").replace("\n", "")
          and "position:relative;\n  }" in testo_mini[
              testo_mini.index("  .card{"):
              testo_mini.index("  .card:active")])

    gest = pezzo_js(testo_mini, "function apriCard(", "\n}\n")
    prova("il click normale non naviga davvero", True,
          "preventDefault" in gest)
    # PRIMA si spegne la navigazione, POI si apre: invertirli vuol dire
    # che un'eccezione dentro openDetail ricarica 910 KB per davvero.
    prova("...e si spegne PRIMA di aprire", True,
          gest.index("preventDefault") < gest.index("openDetail"))
    prova("i modificatori restano al browser", True,
          all(k in testo_mini for k in ("ctrlKey", "metaKey", "shiftKey")))
    prova("un giudice solo per card e piastrelle", 1,
          testo_mini.count("const clickNostro"))

    # --- 13) L'ATTERRAGGIO NON E' UNA DISCESA ----------------------
    dc = pezzo_js(testo_mini, "function apriCategoriaDaUrl(", "\n}\n")
    prova("atterrare su un reparto NON alza navSpingi", False,
          "navSpingi" in dc)
    prova("...e la entry si allinea a mano (nessuna classe cambia)", True,
          "navRiflette()" in dc)
    prova("...una volta sola", True, "categoriaAperta" in dc)
    pc = pezzo_js(testo_mini, "function preparaCategoriaDaUrl(", "\n}\n")
    prova("il reparto si sceglie PRIMA della prima pagina", True,
          "activeCat" in pc and "setCat" not in pc)
    # DENTRO avvia(), e prima del PRIMO giro di rete: altrimenti si
    # scarica una vetrina intera per buttarla via, proprio sulla pagina
    # che deve essere veloce per chi arriva da un motore.
    corpo_avvia = pezzo_js(testo_mini, "async function avvia(){", "\n}\n")
    prova("...e la chiamata sta prima del primo giro di rete", True,
          corpo_avvia.index("preparaCategoriaDaUrl();")
          < corpo_avvia.index("await fetch"))
    # LA TRAPPOLA PEGGIORE: dimenticare la chiamata in avviaVetrina()
    # vuol dire che funziona in Telegram e in collaudo e NON funziona
    # esattamente per chi arriva dai motori.
    for f in ("apriNegozioDaUrl", "apriAnnuncioDaUrl", "apriSicurezzaDaUrl",
              "apriPrivacyDaUrl", "apriCategoriaDaUrl"):
        prova(f"{f} si chiama da avvia() E da avviaVetrina()", 2,
              testo_mini.count(f"{f}();"))

    # --- 14) NESSUN GEMELLO CLIENT DI _slug ------------------------
    # E' la sentinella d'ARCHITETTURA: lo slug arriva dal server, e chi
    # lo ricalcolasse in casa creerebbe il secondo posto da tenere
    # allineato per sempre — quello che divergerebbe il giorno che il
    # server cambia la traslitterazione.
    prova("lo slug dell'annuncio arriva dal server", True,
          "l.slug" in pezzo_js(testo_mini, "const linkAnnuncio = l => {",
                               "\n};\n"))
    prova("...e la card lo usa per il suo href", True,
          "linkAnnuncio(l)" in card)
    prova("...e nessuno lo ricalcola dal titolo", None,
          _re.search(r"\.title[^\n]*toLowerCase\(\)[^\n]*replace",
                     testo_mini))

    # --- 15) IL CARTELLO SI TOGLIE, E PRIMA DI TUTTO ---------------
    prova("il cartello si toglie prima che il motore parta", True,
          testo_mini.index("getElementById('cartello')")
          < testo_mini.index("navMotore();"))
    prova("...e senza un ramo d'errore, se il server non ha iniettato",
          True, "?.remove()" in testo_mini)
    # E NON SI DIPINGE MAI (ago 2026): il cartello e' il primo contenuto
    # del corpo, quindi su rete vera e' anche il primo fotogramma —
    # registrato, 5 giri su 6. La rimozione al parse tiene pulito il DOM
    # renderizzato, questa riga tiene pulito lo SCHERMO: servono
    # entrambe, e questa prova ha preso il posto di quella sul
    # `#cartello:empty`, che il display:none copre a maggior ragione.
    prova("il cartello non si dipinge mai", True,
          "#cartello{display:none}" in testo_mini.replace(" ", ""))
    # non deve rubare i nomi di casa: li vedrebbero navPila,
    # l'osservatore del motore, il tour e il conto delle card
    prova("il cartello non si chiama come le cose dell'app", True,
          all(x not in "".join(_re.findall(r'id="cartello"[^>]*', testo_mini))
              for x in ("view", "sheet", "card", "grid")))

    # --- 15bis) E L'AVVIO NON MOSTRA IL SEME DELLA DEMO ------------
    # `avvia()` chiama renderChips PRIMA del primo fetch: senza la
    # guardia la fila delle pillole conta il seme finto e mostra per
    # ~280 ms categorie che in vetrina non esistono.
    conta_cat = pezzo_js(testo_mini, "function contaCategorie(){", "\n}\n")
    prova("dal locale si conta solo se i dati sono veri", True,
          "DEMO || datiVivi" in conta_cat)
    prova("...e senza conteggi si torna a mani vuote, non col seme",
          True, "return conta" in conta_cat)
    # un solo giudice: due copie direbbero due ordini diversi sullo
    # stesso catalogo (le pillole e le piastrelle di Sfoglia)
    prova("la conta delle categorie vive in un posto solo", 1,
          testo_mini.count("function contaCategorie("))
    # esatto e non «almeno due»: chi ne aggiunge un terzo lo sente
    # dalla CI e va a rileggere questa voce, che e' il punto
    prova("...e la chiamano tutti e due i chiamanti", 2,
          testo_mini.count("contaCategorie();"))
    for quale, corpo in (("le pillole non se lo ricontano da sole",
                          pezzo_js(testo_mini, "function renderChips(){",
                                   "\n}\n")),
                         ("Sfoglia non se lo riconta da sola",
                          pezzo_js(testo_mini, "function ordineSfoglia(){",
                                   "\n}\n"))):
        prova(f"...e {quale}", None, _re.search(r"listings\.forEach", corpo))

    # --- 15ter) LA FASCIA PRIMA DELLE CARD, E LE CARD SUBITO -------
    # (ago 2026, registrato coi fotogrammi su barattolo.store: la
    # fascia del rodaggio si infilava sopra la griglia a card gia'
    # dipinte — ~56px di salto, layout-shift v=0.035-0.044 — e la
    # griglia aspettava anche ordini, preferiti, offerte e puntate:
    # quattro giri di rete che alla vetrina non servono a disegnare)
    avvia_js = pezzo_js(testo_mini, "async function avvia(){", "\n}\n")
    prova("la fascia si disegna PRIMA della griglia, nei due avvii", 2,
          testo_mini.count("await fasciaPrima();\n    renderGrid();"))
    prova("...e il banner del rodaggio parte in testa, in parallelo",
          True, avvia_js.index("caricaBannerTest();")
          < avvia_js.index("${API_BASE}/me"))
    prova("le card non aspettano ordini/preferiti/offerte/puntate",
          True, avvia_js.index("await fasciaPrima()")
          < avvia_js.index("await loadOrders()"))
    # esatto, non «almeno»: il demo-path, quello dopo la fascia, e il
    # ridisegno dell'accordo — un quarto (o un ritorno del render in
    # coda) deve farsi vedere qui
    prova("...e i renderGrid di avvia sono tre", 3,
          avvia_js.count("renderGrid()"))
    # l'accordo accettato e' l'unico dato tardivo che cambia una card
    # intera (il verde di scontoQui via artStima legge offerteMie):
    # senza questo ramo sparirebbe dal primo render e nessuno lo
    # ridisegnerebbe mai
    prova("un accordo vivo sulla vetrina ridisegna la griglia", True,
          "o.stato==='accettata'" in avvia_js
          and avvia_js.index("o.stato==='accettata'")
          > avvia_js.index("await loadOfferte()"))
    # la cache del banner-test e' la PROMESSA, non il risultato: col
    # gate booleano il secondo chiamante in corsa prendeva null, e
    # quel giorno niente fascia e niente cartello, in silenzio
    prova("la cache del banner-test e' la promessa", True,
          "if (!bannerTestPromessa)" in pezzo_js(
              testo_mini, "async function caricaBannerTest(){", "\n}\n"))
    prova("...e il vecchio gate sul risultato non esiste piu'", False,
          "bannerTestLetto" in testo_mini)

    # --- 16) LE PIASTRELLE SONO LINK VERI --------------------------
    sf = pezzo_js(testo_mini, "function renderSfoglia(){", "\n}\n")
    prova("le piastrelle sono collegamenti veri", True,
          '<a class="cat-tile"' in sf and 'href="/categoria/' in sf)
    prova("...e l'indirizzo lo fa slugCat, non un elenco", True,
          "slugCat(c)" in sf)
    prova("...senza <button> rimasti in Sfoglia", False, "<button" in sf)
    prova("...e il nome resta in data-cat, mai dentro l'onclick", True,
          "this.dataset.cat" in sf)

    # --- 17) I DUE FILE RESTANO ALLINEATI --------------------------
    # La regex degli annunci NON e' ancorata in coda, ed e' cio' che fa
    # funzionare gli indirizzi parlanti senza toccare il client: chi la
    # «stringe» con un $ li ammazza tutti in silenzio.
    for nome, prova_su, atteso in (
            ("ANNUNCIO_URL", "/annuncio/13334-bici-da-corsa", "13334"),
            ("NEGOZIO_URL", "/negozio/ab12cd34-la-bottega", "ab12cd34"),
            ("NEGOZIO_URL", "/negozio/mario_rossi", "mario_rossi"),
            ("CATEGORIA_URL", "/categoria/casa-e-giardino",
             "casa-e-giardino")):
        m = _re.search(rf"const {nome} = location\.pathname\.match\("
                       r"/(.+?)/\);", testo_mini)
        if not m:
            prova_fallita = f"{nome} non si trova in miniapp.html"
            prova(prova_fallita, True, False)
            continue
        vero = _re.compile(m.group(1)).match(prova_su)
        prova(f"{nome} legge {prova_su}", atteso, vero.group(1) if vero
              else None)


def _time_seo():
    import time
    return time.time()


# ====================================================================
# ====================================================================
def prove_offerta_quantita():
    """I PEZZI DELL'ACCORDO (ago 2026). Prima il venditore accettava un
    prezzo unitario a quantita' INDETERMINATA: articolo = unitario *
    richiesti, e `richiesti` arrivava dal client senza nessun legame
    con l'offerta — poteva quindi vendersi tutto lo stock alla cifra
    scontata e scoprirlo con l'ordine.

    Qui si prova che la quantita' viaggia con l'offerta e COMANDA nei
    quattro percorsi del conto, che la cifra resta l'UNITARIO (o la
    divisione a ritroso di _righe_ordine si romperebbe in silenzio),
    e che le offerte nate prima del cantiere — quantita 0 — restano il
    mondo di ieri byte per byte."""
    print("\n[i pezzi dell'accordo]")
    src = _SORGENTE
    mini = open("miniapp.html", encoding="utf-8").read()

    # --- 1. Il giudice puro: le due facce, e solo quando servono -----
    amb = {}
    for f in ("_fmt_sats", "_fmt_eur", "_cifra_offerta", "_cifra_accordo"):
        exec(pezzo(f), amb)
    cif = amb["_cifra_accordo"]
    # quantita' NON dichiarata (le offerte di ieri): la cifra e basta
    prova("accordo senza quantita': la cifra e basta", "40.000 sats",
          cif("sats", 40_000, 0.0, 0))
    prova("un pezzo solo: nessuna faccia in piu'", "40.000 sats",
          cif("sats", 40_000, 0.0, 1))
    # ...e con piu' pezzi ENTRAMBE, che e' tutto il cantiere
    # IL TOTALE VIENE PRIMO (decisione di Andrea): la forma «X al pezzo
    # × 3 = Y» si leggeva come un calcolo, e la prima cosa che si vuole
    # sapere e' quanto si paga in tutto. L'unitario resta in coda,
    # perche' e' la cifra che si confronta col listino.
    prova("piu' pezzi: prima il TOTALE, poi l'unitario",
          "120.000 sats per 3 pezzi (40.000 sats al pezzo)",
          cif("sats", 40_000, 0.0, 3))
    prova("in euro il totale e' una moltiplicazione esatta",
          "46,50 € per 3 pezzi (15,50 € al pezzo)",
          cif("eur", 0, 15.50, 3))
    # e la vecchia formula non deve tornare da nessuna porta
    prova("...e la forma a calcolo non c'e' piu'", False,
          " = " in cif("sats", 40_000, 0.0, 3))
    # il numero dei pezzi passa dal formattatore di casa: «1.200», mai
    # un muro di cifre (la lezione di MAX_QUANTITA_ANNUNCIO)
    prova("anche i pezzi si scrivono leggibili", True,
          "per 1.200 pezzi" in cif("sats", 10, 0.0, 1200))
    # e a un pezzo la frase NON deve contenere «al pezzo»: e' il
    # rumore che il giudice esiste per non fare
    for q in (0, 1):
        prova(f"q={q}: la frase non dice «al pezzo»", False,
              "al pezzo" in cif("eur", 0, 9.99, q))

    # --- 2. L'aritmetica: l'unitario comanda, e la divisione a
    #        ritroso dell'ordine resta ESATTA ------------------------
    amb2 = {}
    for f in ("_importo_accordo", "_prezzo_lampo", "_unitario_effettivo",
              "_conto_ordine", "_righe_ordine"):
        exec(pezzo(f), amb2)
    ann = {"prezzo_sats": 100_000, "prezzo_eur": 0.0, "valuta": "sats",
           "lampo_percento": 0, "lampo_scadenza": 0}
    off = {"contro_sats": 0, "contro_eur": 0.0,
           "importo_sats": 30_000, "importo_eur": 0.0, "quantita": 3}
    unit = amb2["_unitario_effettivo"](ann, off, 1000, 0.0)
    prova("l'accordo da' l'UNITARIO, non il totale", 30_000, unit)
    conto = amb2["_conto_ordine"](unit * 3, 500, 0, 0)
    prova("articolo = unitario × pezzi", 90_000, conto["articolo"])
    prova("totale = articolo + spedizione", 90_500, conto["totale"])

    class _Fila:
        def __init__(self, d): self.d = d
        def __getitem__(self, k): return self.d[k]

    class _Con:
        def execute(self, q, p):
            self.r = _Fila({"titolo": "Vasetti di miele"})
            return self
        def fetchone(self): return self.r

    o = {"annuncio_id": 7, "quantita": 3, "prezzo_sats": conto["totale"],
         "spedizione_sats": 500, "protezione_sats": 0, "sconto_sats": 0}
    riga = amb2["_righe_ordine"](_Con(), o)[0]
    # E' QUI che un accordo sul TOTALE si romperebbe in silenzio: la
    # divisione a ritroso non tornerebbe piu', e l'unitario sarebbe
    # sbagliato nell'ordine, nelle notifiche e nel CSV.
    prova("ordine dell'accordo: unitario esatto a ritroso", 30_000,
          riga["unitario_sats"])
    prova("...e i pezzi sono quelli dell'accordo", 3, riga["quantita"])

    # --- 3. La quantita' COMANDA nei quattro percorsi del conto ------
    # (il patto di _sped_gratis(misura_eur: quattro chiamanti e
    # quattro soli — i due compratori e i due preventivi)
    prova("la quantita' dell'accordo comanda nei QUATTRO percorsi", 4,
          src.count('off["quantita"] > 0'))
    # il `> 0` e non un `or`: `richiesti = off["quantita"] or 1`
    # forzerebbe UN pezzo sulle offerte di ieri, cioe' riscriverebbe un
    # accordo che nessuno ha mai stretto su un numero
    prova("...col > 0, mai un `or` che confonde lo zero di ieri", False,
          '= off["quantita"] or' in src)
    # e il numero del client non si guarda piu' quando l'accordo parla
    for chi, fine in (("compra", "def crea_ordine_pagato("),
                      ("_compra_set", "async def _preventivo_set(")):
        corpo = src[src.index(f"async def {chi}("):src.index(fine)]
        prova(f"{chi}: la quantita' dell'accordo si IMPONE", True,
              'off["quantita"] > 0' in corpo)

    # --- 4. L'ORDINE DELLE GUARDIE, che e' la riga da non ammorbidire.
    # Portare il blocco dell'offerta SOPRA la ripresa sembra la mossa
    # pulita ed e' una regressione: la guardia `ordine_id` scatterebbe
    # prima che la ripresa faccia il suo lavoro, e il compratore che
    # ritenta con la sua stessa offerta prenderebbe un 400 invece di
    # ritrovarsi la sua fattura.
    i0 = src.index("async def compra(")
    prova("compra: il blocco offerta resta DOPO la ripresa", True,
          src.index("mio = con.execute(", i0)
          < src.index('if d.get("offerta_id"):', i0))
    # ...e DOPO il fail-fast dello stock, che e' cio' che rende
    # necessario il ricontrollo di cortesia quando il numero cambia
    prova("compra: e dopo il fail-fast dello stock", True,
          src.index("disponibile = a[\"quantita\"] - _riservati", i0)
          < src.index('if d.get("offerta_id"):', i0))

    # --- 5. La scrittura: la colonna, e la PRESENZA della chiave -----
    fai = pezzo("fai_offerta", "\n\n\n@app")
    prova("fai_offerta: la colonna si scrive", True,
          "scadenza,quantita," in fai)
    prova("fai_offerta: dichiarare e' la PRESENZA della chiave", True,
          'd.get("quantita") not in (None, "")' in fai)
    prova("fai_offerta: il numero si LIMA allo stock, mai uno scarto",
          True, 'min(pezzi, max(1, a["quantita"]))' in fai)
    # il giudice della quantita' dell'ANNUNCIO qui non c'entra: quello
    # solleva 400 sopra MAX_QUANTITA_ANNUNCIO, e il tetto vero e' lo
    # stock, che e' piu' stretto
    prova("fai_offerta: non CHIAMA quantita_da_payload", False,
          "quantita_da_payload(" in fai)
    # il titolo nasce SCAPPATO (mancava, mentre i tre fratelli ce
    # l'avevano): le notifiche sono HTML
    prova("fai_offerta: il titolo nasce scappato", True,
          "titolo = html.escape(" in fai)
    prova("fai_offerta: la notifica dice le due facce", True,
          "_cifra_accordo(" in fai)
    # la migrazione c'e' (la PRIMA su `offerte`) e NON inventa un
    # passato: nessun DEFAULT 1, nessun backfill
    prova("la migrazione nasce a 0, mai a 1", True,
          "ALTER TABLE offerte ADD COLUMN quantita INTEGER DEFAULT 0"
          in src)
    prova("...e nessun backfill riscrive le offerte di ieri", False,
          "UPDATE offerte SET quantita" in src)

    # --- 6. Il gemello CLIENT: se diverge, meta' dell'app dice una
    #        cosa e meta' un'altra sullo stesso accordo --------------
    prova("il client ha il gemello di _cifra_accordo", True,
          "function cifraPezzi(" in mini)
    prova("...e dice la stessa frase, col totale davanti", True,
          "per ${fmt(q)} pezzi (${unitaria} al pezzo)" in mini)
    prova("cifraAccordo passa i pezzi al gemello", True,
          "cifraPezzi(o.valuta, a.sats, a.eur, o.quantita||0)" in mini)
    # LA QUANTITA' E' UNA SOLA VARIABILE, e non una copia: il foglio ha
    # il suo stepper e scrive in qtaScelta, la stessa del numero
    # accanto ad «Acquista». Due numeri che dicono cose diverse nella
    # stessa schermata sono il difetto che questo cantiere esiste per
    # togliere, e l'unico modo di non averli e' non averne due.
    prova("il foglio manda la quantita' al server", True,
          "quantita: qtaScelta" in mini)
    prova("...e non ne tiene una copia sua", False, "offQta" in mini)
    # lo stepper del foglio e' lo STESSO chip e la STESSA funzione del
    # gemello: da li' vengono gratis il tetto sullo stock e il
    # comportamento al limite, invece di una seconda guardia da tenere
    # in pari (l'anchor sta dentro il render del foglio, non altrove)
    fogjs = mini[mini.index("function aggiornaFoglioOfferta("):
                 mini.index("function offertaScritta(")]
    prova("lo stepper del foglio e' la STESSA funzione del gemello",
          True, "stepperMini(qtaScelta," in fogjs
          and "'setQta(-1)', 'setQta(1)'," in fogjs
          and "qtaScelta >= (l.quantita||1)" in fogjs)
    # DENTRO setQta, non «da qualche parte nel file»: la stessa riga
    # vive anche in setValuta, quindi cercarla nel file intero era una
    # sentinella che non poteva fallire (l'ha detto la tortura).
    setq = mini[mini.index("function setQta("):
                mini.index("function sceltaConsegna(")]
    prova("setQta riscrive il foglio se e' aperto", True,
          "aggiornaFoglioOfferta();" in setq)
    # ...e la riga dice il TOTALE per primo, non un calcolo
    odig = mini[mini.index("function offertaDigitata("):
                mini.index("async function inviaOfferta(")]
    prova("la riga dell'offerta mette il totale davanti", True,
          '<b class="mono">${totale}</b> per ${fmt(qtaScelta)} pezzi' in odig
          and '(${unitaria} al pezzo)' in odig)

    # --- 7. Il foglio rifatto: tre pillole, toggle, ✕ ---------------
    fog = mini[mini.index('id="offertaSheet"'):
               mini.index('id="puntaSheet"')]
    fog2 = mini[mini.index("function offertaChip("):
                mini.index("function offertaDigitata(")]
    prova("il foglio ha la ✕ e non piu' «Annulla»", True,
          'class="pacco-x"' in fog and ">Annulla<" not in fog)
    prova("...e il toggle valuta dei suoi fratelli", True,
          'class="cur-seg inriga"' in fog)
    prova("la ✕ chiude col motore di navigazione", True,
          'class="pacco-x" onclick="navIndietro()"' in fog)
    prova("la terza pillola e' «Personalizzato»", True,
          ">Personalizzato<" in mini)
    # IL CAMPO E' SEMPRE VISIBILE E MODIFICABILE (ago 2026, dal campo):
    # le pillole lo RIEMPIONO, non lo nascondono — chi parte da −10% e
    # poi ritocca dev'essere libero di farlo.
    prova("il campo del prezzo non si nasconde piu'", True,
          'id="offCampo" style="display:flex' in fog)
    prova("...e la pillola percentuale lo lascia dov'e'", True,
          "/* il campo RESTA li', pronto a essere ritoccato */" in fog2)
    # la pillola accesa si DEDUCE dalla cifra: una scelta memorizzata
    # direbbe il falso dopo un ritocco («−10%» su una cifra che non lo
    # e' piu'), e non c'e' piu' nessuna variabile che possa mentire
    prova("nessuna pillola memorizzata: si deduce dal valore", False,
          "offScelta" in mini)
    prova("...e a dedurla e' offertaDigitata", True,
          "b.classList.toggle('attiva', vv > 0 && (p === 'libero'" in mini)
    # IL MINIMO NON E' UN CARTELLO PERMANENTE: compare solo quando la
    # cifra scritta ci finisce sotto. Dirlo prima che serva e' rumore,
    # e affianca un numero che non c'entra con quello che si scrive.
    prova("il minimo nasce nascosto", True,
          'id="offMinimo" style="display:none' in fog)
    prova("...e compare solo sotto soglia", True,
          "const sotto = offertaMinPercento > 0 && v > 0" in mini)
    prova("...e il testo dice che e' troppo bassa", True,
          "Troppo bassa: il minimo" in mini)
    prova("la vecchia riga permanente non c'e' piu'", False,
          "Le offerte partono da" in mini)
    # e il minimo del client arrotonda come il SERVER (per eccesso sui
    # sats), o direbbe «va bene» a una cifra che di la' viene rifiutata
    prova("il minimo si arrotonda come il server", True,
          "Math.ceil(l.price*offertaMinPercento/100)" in mini)
    # LA TASTIERA NON COPRE QUEL CHE SI SCRIVE: i fogli sono ancorati
    # al fondo dello schermo, e il layout viewport non si accorcia —
    # l'unico che lo sa e' visualViewport.
    # sul solo `.open` e col TRANSFORM: alzando il `bottom` si
    # alzerebbero anche i fogli CHIUSI (nascosti con translateY(100%),
    # cioe' la loro altezza sotto l'ancora) e rientrerebbero in vista
    prova("i fogli si alzano con la tastiera", True,
          ".sheet.open{transform:translateY(calc(-1 * "
          "var(--tastiera,0px)))}" in mini)
    prova("...e il foglio CHIUSO resta ancorato al fondo", True,
          "position:fixed;left:0;right:0;bottom:0;" in mini)
    prova("...e si accorciano, che 100dvh su iOS non basta", True,
          "- var(--tastiera,0px))" in mini)
    prova("la misura viene da visualViewport", True,
          "window.innerHeight - vv.height - vv.offsetTop" in mini)
    # divisa per lo zoom: arriva in pixel di VIEWPORT e si spende
    # dentro `html`, che e' zoomato (la ragione dei calc(100vh/...))
    prova("...e si divide per lo zoom di casa", True,
          "coperto / z" in mini)
    # LO SCATTO (ago 2026, dalla PWA): la transizione di 220ms serve
    # alla scivolata d'ingresso, ma il sollevamento passa dalla stessa
    # proprieta' — e visualViewport emette un resize a ogni passo
    # dell'animazione della tastiera. Il foglio finiva a INSEGUIRE un
    # bersaglio che si muove. Mentre la tastiera e' su, niente
    # transizione: il foglio E' dove il viewport dice.
    prova("mentre la tastiera e' su i fogli non inseguono", True,
          "html.con-tastiera .sheet.open{transition:none}" in mini)
    prova("...e la classe la mette chi misura", True,
          "classList.toggle('con-tastiera', su)" in mini)
    # e il fuoco non trascina: uno scroll automatico su un foglio
    # fisso e' l'altro modo in cui nasce uno scatto (lezione picker)
    prova("il fuoco sul campo non trascina niente", True,
          "campo.focus({preventScroll:true})" in mini)
    # IL CAMPO DICE «AL PEZZO» mentre si digita, e solo coi pezzi >1:
    # chi ne vuole tre ragiona sul TOTALE e rischia di scrivere 120
    # intendendo il totale mentre ne sta offrendo 360
    prova("il campo dice «al pezzo» mentre si scrive", True,
          "qtaScelta > 1 ? '<span class=\"off-alpezzo\">al pezzo</span>'"
          in mini)
    prova("...e col pezzo singolo tace", True,
          ".off-alpezzo{display:block" in mini)
    # SOTTO IL MINIMO NIENTE TOTALE: due righe dove ne serve una
    prova("sotto il minimo la riga del totale sparisce", True,
          "if (v<=0 || sotto) { riga.textContent = ''; return; }" in mini)
    # le pillole non portano piu' il controvalore: erano due cifre in
    # concorrenza con quella che conta
    prova("le pillole dicono la sola percentuale", True,
          ">−${p}%</button>" in mini)
    # la riga «se accetta pagheresti» e' morta: diceva un totale senza
    # la spedizione, cioe' una cosa incompleta
    prova("la vecchia stima incompleta non c'e' piu'", False,
          "Se accettata pagheresti" in mini)
    # il toggle governa la LETTURA: ridisegna il foglio, mai la cifra
    prova("setValuta ridisegna il foglio aperto", True,
          "if (el('offertaSheet')?.classList.contains('open')) "
          "aggiornaFoglioOfferta();" in mini)

    # --- 8. Il tasto offerta porta la quantita', e le DUE superfici
    #        non possono divergere (giudice unico) -------------------
    prova("l'etichetta del tasto offerta ha un giudice solo", 1,
          mini.count("function etichettaOfferta("))
    # ...e la usano tutte e due le superfici: la barra su mobile e il
    # gemello in pagina da 768px in su. Sono la stessa cosa vista da
    # due larghezze e non devono poter dire due numeri.
    prova("...e la usano tutte e due le superfici", True,
          "el('bcOfferta').innerHTML = etichettaOfferta(l);" in mini
          and 'tasto-offerta" onclick="apriOfferta()">'
              '${etichettaOfferta(l)}' in mini)
    # tre volte: i due tasti piu' il giro di setQta che li riallinea
    prova("le due superfici portano la stessa classe", 3,
          mini.count("tasto-offerta"))
    prova("setQta riscrive l'etichetta, non solo una cifra", True,
          "q('.tasto-offerta').forEach(b => b.innerHTML = "
          "etichettaOfferta(l));" in mini)
    # con l'accordo la quantita' non si sceglie piu': lo stepper
    # sparisce, o prometterebbe una scelta che il server non accetta
    prova("con l'accordo lo stepper di Acquista sparisce", True,
          "if (off && off.quantita > 0)" in mini)
    # ...e nel carrello la cella si pinna, o la composizione direbbe 5
    # mentre il riepilogo e la invoice dicono 3
    prova("nel carrello la cella si pinna all'accordo", True,
          "const pinnato = qta && acc && acc.quantita > 0;" in mini)

    # --- 9. ACCETTARE NON RISERVA NIENTE, e col numero scritto il
    # venditore si sente piu' impegnato di quanto sia: con 4 pezzi puo'
    # accettare tre offerte da 3 e credersi impegnato per 9. E' il
    # meccanismo di sempre — l'annuncio non si e' mai bloccato — ma va
    # ridetto dove il numero si vede.
    # (ago 2026: non e' piu' un confirm ma il foglio di casa, e la
    # frase vive spezzata su due righe di sorgente — quindi si RICUCE
    # prima di cercarla, o la sentinella direbbe che e' sparita mentre
    # e' li'. La stessa piega del censimento degli euro.)
    cucito = re.sub(r"'\s*\n\s*\+ '", "", mini)
    prova("il foglio del venditore lo dice ancora", True,
          "Accettare non riserva l'oggetto: l'annuncio resta in vetrina"
          .replace("'", "\\'") in cucito)
    prova("...e ora lo dice anche il pannello", True,
          "Accettare non blocca i pezzi" in mini)
    prova("...e la notifica del bot, da cui si accetta di piu'", True,
          "Accettare non blocca l'oggetto" in src)

    # --- 10. IL CAMPO CONVERTE COL TOGGLE (ago 2026, dal campo: si
    # scriveva 40.000 in sats, si passava a euro e il campo diceva
    # ancora 40.000 — la riga sotto convertiva, lui no).
    prova("l'oninput del campo pianta l'ancora", True,
          'oninput="offertaScritta()"' in fog)
    prova("...e il campo segue il toggle", True,
          "campo.value = offTestoCampo(offCifraIn(vc), vc);" in fogjs)
    # la valuta del campo e' quella che si GUARDA, non quella del
    # listino: senza questa riga il campo tornerebbe muto al toggle
    # ed e' precisamente il bug che il cantiere chiude
    prova("...e la valuta del campo e' quella che si guarda", True,
          "const vc = valutaOfferta(l);" in fogjs
          and "return valutaVista==='eur' ? 'eur' : 'sats';" in mini)
    prova("...portando il simbolo della valuta MOSTRATA", True,
          "el('offSuffisso').innerHTML = (vc==='eur' ? '€' : 'sats')"
          in fogjs)
    # L'ANCORA E' QUELLO CHE IMPEDISCE ALLA CIFRA DI DERIVARE: si
    # tiene la cifra com'e' stata scritta e la valuta in cui lo e'
    # stata, e il toggle la RILEGGE convertita. Cosi' dieci toggle di
    # fila costano sempre UNA conversione sull'originale, invece di
    # una catena in cui ognuna parte dal risultato della precedente.
    prova("la conversione parte SEMPRE dall'ancora", True,
          "return offConverti(offCifra, offCifraValuta || valuta, valuta);"
          in mini)
    # ...e a scriverla e' un posto SOLO. Il render non deve toccarla:
    # se la riscrivesse con la propria conversione, l'originale
    # sparirebbe e la cifra deriverebbe a ogni tocco del toggle.
    prova("il render non riscrive l'ancora", False,
          "offCifra =" in fogjs)
    prova("...e nemmeno la riga che la legge", False,
          "offCifra =" in odig)
    # ...che infatti il campo non lo guarda proprio: legge l'ancora,
    # o tornerebbe a dipendere da un numero gia' convertito
    prova("...e non rilegge il campo", False,
          "el('offImporto').value" in odig)
    # tre soli scrittori piu' la dichiarazione: l'apertura che azzera,
    # la pillola, e l'oninput. Chi ne aggiunge un quarto lo dichiari.
    prova("gli scrittori dell'ancora sono tre", 4,
          mini.count("offCifra = "))
    # il campo si riscrive SOLO quando la valuta cambia davvero, o un
    # tocco sullo stepper normalizzerebbe sotto le dita una cifra che
    # si sta ancora scrivendo
    prova("il campo si riscrive solo a valuta cambiata", True,
          "if (vc !== offCampoValuta) {" in fogjs)
    # l'apertura azzera l'ANCORA e non il solo campo: e' lei la cifra
    prova("l'apertura azzera l'ancora, non il campo", True,
          "offCifra = 0; offCifraValuta = ''; offCampoValuta = '';" in mini)
    # senza cambio vivo il campo resta sulla valuta del listino, che e'
    # sempre esatta: mai una conversione fatta col valore di riserva
    prova("senza cambio il campo resta sul listino", True,
          "if (!cambioVivo) return inEur ? 'eur' : 'sats';" in mini)
    # LE PILLOLE si confrontano nella valuta MOSTRATA — e' il numero
    # che si vede — ma piantano l'ancora in quella del LISTINO, cosi'
    # il −10% che parte e' esattamente −10% al sat
    prova("le pillole si confrontano in quel che si vede", True,
          "Math.abs(vv - offertaScontoIn(l, x, vc)) < tol" in odig)
    prova("...e piantano l'ancora nella valuta del listino", True,
          "offCifra = offertaSconto(l, Number(scelta));" in fog2
          and "offCifraValuta = inEur ? 'eur' : 'sats';" in fog2)
    # IL MINIMO: si CONFRONTA nella valuta del listino, che e' quella
    # su cui giudica il server, e si DICE in quella del campo,
    # arrotondato per ECCESSO — chi scrive esattamente la cifra che
    # legge dev'essere ammesso, mai rifiutato per un centesimo.
    prova("il minimo si confronta come il server", True,
          "const v = offCifraIn(inEur ? 'eur' : 'sats');" in odig)
    prova("...e si dice nella valuta del campo", True,
          "offCifraTesto(offMinimoIn(l, min, vc), vc," in odig)
    prova("...arrotondato per eccesso, o rifiuterebbe cio' che mostra",
          True, "Math.ceil(min.sats*eurPerSat*100)/100" in mini
          and "Math.ceil(min.eur/eurPerSat)" in mini)
    # L'INVIO parla la valuta del LISTINO, l'unica in cui l'accordo
    # esiste e l'unica che il server accetta: la conversione avviene
    # li', una volta sola, e sull'ANCORA — mai su quel che il campo
    # mostra adesso, che puo' essere un'altra valuta.
    i_inv = mini.index("async function inviaOfferta(")
    inv = mini[i_inv:mini.index("function apriLampo(", i_inv)]
    prova("l'invio converte verso il listino", True,
          "const cifra = offCifraIn(inEur ? 'eur' : 'sats');" in inv)
    prova("...e non legge piu' il campo", False,
          "el('offImporto').value" in inv)


# ====================================================================
def prove_sat_non_e_barattolo():
    """«SAT» E' LA MONETA, NON UN NOSTRO MARCHIO (ago 2026, falso
    positivo VERO dal campo: «Sat's Oil 🫒 GENESIS EDITION» bloccato
    per impersonazione, col motivo «il nome appare progettato per
    confondere con Barattolo (associando "sat")»).

    Due difetti distinti, e qui si difendono tutti e due: la voce del
    prompt che ora dice a chiare lettere che nominare i satoshi non e'
    mai impersonazione, e la regola che senza testo non si conclude
    niente — il motivo diceva anche «il titolo e la descrizione
    mancano», cioe' il modello aveva DEDOTTO l'impersonazione da cio'
    che il testo non diceva. Piu' il buco della lista delle parole,
    che era vero e separato: «confondere» non matchava, e a un
    venditore onesto e' arrivata la lista delle armi e delle droghe.

    La FORMA si difende qui; che il modello abbia capito lo dice solo
    collaudo_impersonazione.py, che vuole la chiave."""
    print("\n[«sat» non e' Barattolo]")
    src = _SORGENTE
    i = src.index("PROMPT_MODERAZIONE = (")
    amb = {}
    exec(src[i:src.index("\n\n\n", i)], amb)
    p = amb["PROMPT_MODERAZIONE"]

    # 1. la contro-regola sui satoshi: la TERZA, accanto a «nominare
    #    Barattolo e' lecito» e «raccontare come funziona e' lecito»
    prova("il prompt dice che i satoshi sono la MONETA", True,
          "sono la MONETA di questo mercatino" in p)
    prova("...e che nominarli non e' MAI impersonazione", True,
          "NOMINARE I SATOSHI non e' MAI impersonazione" in p)
    # la somiglianza di NOME non basta: a decidere resta il GESTO —
    # senza questa riga il divieto torna a essere un filtro sul nome
    prova("una somiglianza di nome non e' mai un motivo", True,
          "Una somiglianza di NOME non e' mai un motivo" in p)
    prova("il caso vero e' un esempio del prompt", True,
          "Sat's Oil GENESIS EDITION\" -> OK" in p)

    # 2. senza testo non si conclude niente. E' la riga che disinnesca
    #    la confabulazione osservata: se il modello CREDE che il testo
    #    manchi, adesso quella premessa porta a OK invece che a VIETATO
    prova("il prompt dice cosa fare col testo mancante", True,
          "SE IL TESTO NON C'E', NON SI CONCLUDE NIENTE" in p)
    prova("...e vieta di dedurre dal non detto", True,
          "Non dedurre MAI l'impersonazione da cio' che il testo non "
          "dice" in p)

    # 3. le due contro-regole di ieri non sono state travolte da quella
    #    nuova: sono la meta' che un riordino toglie per prima
    prova("...e le due contro-regole di ieri restano", True,
          "NOMINARE Barattolo non e' MAI di per se' un motivo" in p
          and "RACCONTARE come funziona Barattolo e' invece LECITO" in p)

    # 4. il buco della lista: il messaggio giusto a chi si e' visto
    #    dire «confondere». Si prova sulla funzione VERA, coi motivi
    #    scritti come li scrive l'AI.
    amb2 = {}
    for n in ("MSG_RIFIUTO", "MSG_RIFIUTO_SERVIZI",
              "MSG_RIFIUTO_IMPERSONAZIONE", "PAROLE_IMPERSONAZIONE"):
        j = src.index(f"{n} = ")
        exec(src[j:src.index("\n\n\n", j)], amb2)
    exec(pezzo("messaggio_rifiuto"), amb2)
    msg = amb2["messaggio_rifiuto"]
    imperson = amb2["MSG_RIFIUTO_IMPERSONAZIONE"]
    prova("«confondere»: il messaggio dell'impersonazione, non le armi",
          imperson,
          msg('il nome appare progettato per confondere con Barattolo'))
    # e le vecchie non si sono mosse
    for motivo in ("si finge il supporto Barattolo",
                   "impersona la piattaforma",
                   "phishing: chiede le credenziali"):
        prova(f"...e resta vero per «{motivo[:28]}»", imperson,
              msg(motivo))
    prova("un servizio resta un servizio", amb2["MSG_RIFIUTO_SERVIZI"],
          msg("servizio di riparazione su commissione"))
    prova("e le armi la lista di sempre", amb2["MSG_RIFIUTO"],
          msg("arma da fuoco funzionante"))

    # 5. il collaudo col MODELLO tiene il caso come REGRESSIONE
    #    PERMANENTE, con la gemella scritta con altre parole: se
    #    cadesse solo la gemella, la cura avrebbe insegnato il NOME
    #    invece della regola
    col = open("collaudo_impersonazione.py", encoding="utf-8").read()
    prova("il caso vero e' nel collaudo", True, "Sat's Oil" in col)
    prova("...con la sua gemella", True, "SatShop" in col)
    prova("...e col caso a descrizione VUOTA", True,
          "Satoshi Coffee" in col)
    # tutti e tre attesi OK: sono annunci legittimi
    for nome in ("Sat's Oil", "SatShop", "Satoshi Coffee"):
        k = col.index(nome)
        prova(f"«{nome}» e' atteso OK", True,
              '"OK"' in col[k:k + 400])

    # L'ATTESO SEGUE IL PROMPT, NON IL MODELLO (ago 2026, decisione di
    # Andrea). «Assistenza Barattolo» e' il caso che l'ha insegnato:
    # per tre giorni il modello ha risposto VIETATO dove il prompt
    # insegna DUBBIO, e l'atteso fu ALZATO per inseguirlo; poi il
    # modello si e' ri-allineato e l'atteso e' tornato dov'era.
    # UN ATTESO CHE CAMBIA DUE VOLTE NON E' PIU' UN ATTESO: se un
    # domani oscillasse ancora si dichiara INSTABILE, non lo si
    # rincorre una terza volta — e questa sentinella e' li' perche'
    # una terza riscrittura silenziosa non possa succedere.
    k = col.index("Assistenza Barattolo")
    prova("«Assistenza Barattolo» e' atteso DUBBIO, come il prompt",
          True, '"DUBBIO"' in col[k:k + 500])
    prova("...e il prompt insegna ancora DUBBIO su quella riga", True,
          "'Assistenza Barattolo - supporto agli utenti' -> DUBBIO"
          in p)


# ====================================================================
def prove_ai_segnala():
    """L'AI SEGNALA, NON DECIDE (ago 2026, decisione di Andrea dopo il
    falso positivo che ha fermato un venditore vero). Un VIETATO
    dell'AI non basta piu' a bloccare: ferma solo se il MOTIVO nomina
    una delle quattro famiglie dove il no e' la risposta giusta anche
    quando il modello ha sbagliato — armi, droghe, sesso a pagamento e
    sfruttamento, documenti e credenziali. Tutto il resto va in
    REVISIONE, dove non e' pubblico e decide un umano.

    Il declassamento vive nel GIUDICE UNICO e non nel prompt: il
    modello e' gia' stato visto disobbedire alla lettera del prompt,
    quindi la garanzia deve stare dove il modello non arriva."""
    print("\n[l'AI segnala, non decide]")
    src = _SORGENTE
    import unicodedata as _u
    amb = {"re": re, "unicodedata": _u}
    for ancora in ("def normalizza(", "PAROLE_BLOCCANTI = ",
                   "PREFISSI_BLOCCANTI = ", "def _vietato_bloccante("):
        i = src.index(ancora)
        exec(src[i:src.index("\n\n\n", i)], amb)
    blocca = amb["_vietato_bloccante"]

    # --- le quattro famiglie che fermano davvero -------------------
    for motivo in ("arma da fuoco funzionante", "munizioni da caccia",
                   "droga", "vendita di stupefacenti",
                   "cocaina", "servizi sessuali mascherati",
                   "sfruttamento della prostituzione",
                   "materiale pedopornografico", "coinvolge minori",
                   "carte clonate", "credenziali di accesso rubate"):
        prova(f"blocca: «{motivo[:34]}»", True, blocca(motivo))

    # --- e quelle che NON fermano: hanno tutte una lettura innocente
    # che il modello puo' aver frainteso, e un no le fermerebbe da
    # gente onesta senza che nessuno lo sappia ----------------------
    for motivo in ("il nome appare progettato per confondere con Barattolo",
                   "finto servizio clienti di Barattolo",
                   "impersonazione della piattaforma",
                   "possibile refurtiva",
                   "borsa probabilmente contraffatta",
                   "farmaco con obbligo di ricetta",
                   "animale protetto",
                   "servizio su commissione",
                   "contenuto vietato"):
        prova(f"in coda: «{motivo[:34]}»", False, blocca(motivo))

    # --- LE TRAPPOLE DELLA SOTTOSTRINGA, che sono la ragione per cui
    # le parole corte stanno in un insieme di ESATTE e non fra i
    # prefissi: «arma» sta dentro «armadio» --------------------------
    for motivo in ("vendita di un armadio antico", "armadietto da bagno",
                   "cornice dorata", "minorenne"):
        prova(f"non e' una parola: «{motivo[:30]}»", False, blocca(motivo))

    # --- il declassamento sta nel GIUDICE, e la leva resta sovrana --
    lv = pezzo("_leggi_verdetto")
    prova("il vietato passa da _vietato_bloccante", True,
          "if _vietato_bloccante(motivo):" in lv)
    prova("...e chi non lo e' diventa un dubbio", True,
          '("dubbio" if MODERAZIONE_REVISIONE else "vietato"), motivo'
          in lv)
    # a leva SPENTA si torna al binario di ieri, rifiuto secco: il
    # freno d'emergenza deve continuare a fare quello che promette
    prova("la leva spenta rimette il rifiuto secco", 2,
          lv.count('if MODERAZIONE_REVISIONE else "vietato"'))
    # il PROMPT non e' stato toccato: i suoi verdetti li collauda uno
    # script che vuole la chiave, e cambiarlo alla cieca sarebbe un
    # ritocco non verificato
    prova("il prompt insegna ancora VIETATO sui casi netti", True,
          "Riserva VIETATO a questi casi netti" in src)

    # --- fail-SAFE verso la coda: un motivo vuoto o incomprensibile
    # non blocca. Sbagliare qui costa un tocco a un moderatore;
    # sbagliare nell'altro verso costa un venditore, in silenzio.
    for motivo in ("", "   ", "boh", None):
        prova(f"motivo {motivo!r}: nel dubbio, la coda", False,
              blocca(motivo or ""))

    # --- lo strumento che dice quanto si allunga la coda esiste e
    # LEGGE E BASTA: e' il conto su cui si decide, e un conto che
    # scrive non lo si lancia a server acceso ------------------------
    stima = open("stima_coda_moderazione.py", encoding="utf-8").read()
    corpo = stima.split('"""', 2)[-1]
    for parola in ("INSERT", "UPDATE", "DELETE", "commit"):
        prova(f"lo strumento della stima non {parola.lower()}", False,
              parola in corpo)


def prove_ritiro_offerta():
    """Il compratore ritira la sua offerta (ago 2026, da un caso vero:
    un'offerta mandata per sbaglio non si poteva togliere, e la guardia
    `attive` impediva perfino di rifarla giusta). Qui si prova che il
    gesto e' suo e di nessun altro, che non manda mai una notifica
    doppia, e soprattutto CHE L'ESCROW NON C'ENTRA MAI."""
    print("\n[il ritiro dell'offerta]")
    import asyncio
    import re
    import sqlite3

    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    # I giudici VERI, non stub: la lezione di _fmt_sats — uno stub
    # scritto a mano finisce per imitare anche i bug dell'originale.
    puro = {}
    for f in ("_fmt_sats", "_fmt_eur", "_cifra_offerta", "_cifra_accordo",
              "_importo_accordo"):
        exec(pezzo(f), puro)

    def mondo():
        vero = sqlite3.connect(":memory:")
        vero.row_factory = sqlite3.Row
        vero.execute(
            "CREATE TABLE offerte(id INTEGER PRIMARY KEY, annuncio_id INT, "
            "compratore_id INT, venditore_id INT, valuta TEXT, "
            "importo_sats INT, importo_eur REAL, contro_sats INT, "
            "contro_eur REAL, stato TEXT, scadenza INT, ordine_id INT, "
            "quantita INT, creato INT, aggiornato INT)")
        vero.execute("CREATE TABLE annunci(id INTEGER PRIMARY KEY, "
                     "titolo TEXT)")
        vero.execute("CREATE TABLE ordini(id INTEGER PRIMARY KEY, "
                     "compratore_id INT, stato TEXT, prezzo_sats INT, "
                     "payment_hash TEXT)")
        vero.execute("INSERT INTO annunci VALUES(7,'Miele di castagno')")
        vero.executemany("INSERT INTO ordini VALUES(?,?,?,?,?)", [
            (50, 111, "creato", 210000, "hash50"),      # invoice viva
            (51, 111, "annullato", 210000, "hash51")])  # lapide, fossile
        futuro = 9_000_000_000
        righe = [
            # id, ann, compr, vend, val, imp_s, imp_e, ctr_s, ctr_e,
            #     stato, scadenza, ordine_id, quantita
            (1, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "proposta", futuro, 0, 3),
            (2, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "accettata", futuro, 0, 3),
            (3, 7, 111, 222, "sats", 70000, 0, 80000, 0,
             "controproposta", futuro, 0, 1),
            (4, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "rifiutata", 0, 0, 1),
            (5, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "conclusa", 0, 0, 1),
            (6, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "proposta", 1, 0, 1),                      # scaduta di fatto
            (7, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "accettata", futuro, 50, 3),               # ordine VIVO
            (8, 7, 111, 222, "sats", 70000, 0, 0, 0,
             "accettata", futuro, 51, 3),               # ordine fossile
            (9, 7, 333, 222, "sats", 70000, 0, 0, 0,
             "proposta", futuro, 0, 1),                 # di un ALTRO
        ]
        vero.executemany(
            "INSERT INTO offerte VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,0,0)",
            righe)
        vero.commit()
        return vero

    def ritira(vero, offerta_id, chi):
        """L'ambiente e' POVERO APPOSTA: non contiene NESSUNO dei nomi
        che muovono sats. Se un domani il ritiro impara a toccarli, la
        prova non diventa rossa — ESPLODE con NameError, che e' molto
        piu' difficile da ignorare."""
        detti = []

        class Con:
            def execute(self, *a):
                return vero.execute(*a)

            def commit(self):
                vero.commit()

            def close(self):
                pass

        async def _notifica(tg_id, testo):
            detti.append((tg_id, testo))

        amb = {"db": Con, "HTTPException": _H, "notifica": _notifica,
               "html": __import__("html"), "time": __import__("time"),
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi},
               "URL_PUBBLICO": "https://barattolo.store",
               "STATI_OFFERTA_VIVI": ("proposta", "controproposta",
                                      "accettata"),
               "_cifra_accordo": puro["_cifra_accordo"],
               "_importo_accordo": puro["_importo_accordo"]}
        exec("async " + pezzo("ritira_offerta"), amb)
        try:
            esito = asyncio.new_event_loop().run_until_complete(
                amb["ritira_offerta"](offerta_id))
            return esito, detti
        except _H as e:
            return f"{e.code} {e.detail}", detti

    def stato_di(vero, i):
        r = vero.execute("SELECT stato, scadenza FROM offerte WHERE id=?",
                         (i,)).fetchone()
        return (r["stato"], r["scadenza"]) if r else None

    # --- 1) il gesto suo, dai due stati che lo ammettono -------------
    v = mondo()
    esito, detti = ritira(v, 1, 111)
    prova("il compratore ritira la sua proposta",
          ({"ok": True, "stato": "ritirata"}, ("ritirata", 0)),
          (esito, stato_di(v, 1)))
    prova("...e il venditore lo viene a sapere", 1, len(detti))

    esito, detti = ritira(v, 2, 111)
    prova("il compratore ritira un accordo accettato",
          ({"ok": True, "stato": "ritirata"}, ("ritirata", 0)),
          (esito, stato_di(v, 2)))
    prova("...con la riga che dice che nessun sat si era mosso", True,
          len(detti) == 1 and "Nessun sat si era mosso" in detti[0][1])
    prova("...e la cifra dell'accordo con le due facce", True,
          "210.000 sats per 3 pezzi" in detti[0][1])

    # --- 2) di chi NON e' -------------------------------------------
    prova("il venditore non ritira l'offerta che ha ricevuto",
          "400 Operazione non permessa", ritira(v, 9, 222)[0])
    prova("un estraneo non ritira l'offerta altrui",
          "400 Operazione non permessa", ritira(v, 9, 444)[0])
    # L'ORACOLO: chi enumera gli id non deve imparare niente.
    prova("offerta altrui e offerta inesistente rispondono UGUALE",
          True, ritira(v, 9, 111)[0] == ritira(v, 99999, 111)[0])

    # --- 3) gli stati che non si ritirano ---------------------------
    esito, detti = ritira(v, 3, 111)
    prova("dalla controproposta no: li' la strada e' «Rifiuta»", True,
          esito.startswith("400") and "Rifiuta" in esito)
    prova("...e la riga non si tocca", ("controproposta", 9_000_000_000),
          stato_di(v, 3))
    for i, nome in ((4, "rifiutata"), (5, "conclusa")):
        prova(f"da {nome}: 400 «già chiusa»",
              "400 Questa offerta è già chiusa", ritira(v, i, 111)[0])
    prova("una ritirata non si ritira due volte",
          "400 Questa offerta è già chiusa", ritira(v, 1, 111)[0])

    # --- 4) la scadenza: si timbra 'scaduta', MAI 'ritirata' ---------
    esito, detti = ritira(v, 6, 111)
    prova("l'offerta scaduta di fatto: 400 onesto",
          "400 Questa offerta è scaduta", esito)
    prova("...timbrata 'scaduta' e non 'ritirata'", "scaduta",
          stato_di(v, 6)[0])
    prova("...e nessuno riceve un messaggio contraddittorio", 0,
          len(detti))

    # --- 5) l'ordine: blocca solo se e' VIVO -------------------------
    esito, detti = ritira(v, 7, 111)
    prova("con una fattura in corso non si ritira", True,
          esito.startswith("400") and "annullala dagli Ordini" in esito)
    prova("...e l'offerta resta accettata", "accettata", stato_di(v, 7)[0])
    prova("...e il venditore non riceve niente", 0, len(detti))
    # LA PROVA ANTI-VICOLO-CIECO: con la guardia secca
    # `if off["ordine_id"]` questa diventa rossa, e il compratore
    # resterebbe incastrato per sempre (annulla_ordine su un ordine non
    # 'creato' risponde «Operazione non permessa»).
    prova("con la lapide di un ordine annullato si ritira eccome",
          {"ok": True, "stato": "ritirata"}, ritira(v, 8, 111)[0])

    # --- 6) il doppio tap: una notifica sola ------------------------
    v2 = mondo()
    _, primi = ritira(v2, 1, 111)
    esito, secondi = ritira(v2, 1, 111)
    prova("il secondo tocco non manda una seconda notifica",
          (1, 0), (len(primi), len(secondi)))

    # --- 7) il tetto conta, la strada si riapre ---------------------
    # Le due query VERE di fai_offerta, girate sullo stesso database:
    # un mondo dove il compratore ha UNA sola offerta, appena ritirata.
    v4 = sqlite3.connect(":memory:")
    v4.row_factory = sqlite3.Row
    v4.execute("CREATE TABLE offerte(id INTEGER PRIMARY KEY, "
               "annuncio_id INT, compratore_id INT, stato TEXT)")
    v4.execute("INSERT INTO offerte VALUES(1,7,111,'ritirata')")
    attive = v4.execute(
        "SELECT COUNT(*) AS n FROM offerte WHERE annuncio_id=? AND "
        "compratore_id=? AND stato IN ('proposta','controproposta',"
        "'accettata')", (7, 111)).fetchone()["n"]
    totali = v4.execute(
        "SELECT COUNT(*) AS n FROM offerte WHERE annuncio_id=? AND "
        "compratore_id=?", (7, 111)).fetchone()["n"]
    v4.close()
    prova("dopo il ritiro non c'e' piu' un'offerta «attiva»: "
          "si riprova SUBITO", 0, attive)
    prova("...ma il tentativo resta CONTATO nel tetto", 1, totali)

    # --- 8) L'ESCROW NON C'ENTRA MAI, tre livelli -------------------
    v3 = mondo()
    prima = [tuple(r) for r in v3.execute("SELECT * FROM ordini "
                                          "ORDER BY id")]
    ritira(v3, 2, 111)
    ritira(v3, 8, 111)
    dopo = [tuple(r) for r in v3.execute("SELECT * FROM ordini "
                                         "ORDER BY id")]
    prova("nessun ordine si muove di una virgola", prima, dopo)
    v.close()
    v2.close()
    v3.close()

    rit = pezzo("ritira_offerta")
    # Le sentinelle guardano il CODICE, non la prosa: senza togliere
    # docstring e commenti, un «risponde 404» scritto in italiano
    # basterebbe a far sembrare presente un ramo che non c'e' (o
    # assente uno che c'e'). E si RICUCIONO le stringhe spezzate a
    # capo, o «AND stato=?» a cavallo di due righe si nasconde alla
    # ricerca — e' la piega in cui gia' due siti si erano nascosti al
    # censimento degli euro.
    corpo = rit.split('"""', 2)[-1]
    codice = "\n".join(r for r in corpo.split("\n")
                       if not r.strip().startswith("#"))
    codice = re.sub(r'"\s*\n\s*"', "", codice)
    for nome in ("invoice_pagata", "crea_invoice_escrow", "paga_venditore",
                 "_paga_rimborso", "_rimborsa_compratore", "_sblocca_sats",
                 "_incassa_ordine", "payment_hash", "rimborsi_asta",
                 "importo_invoice", "lnbits"):
        prova(f"il ritiro non nomina mai {nome}", False, nome in codice)
    # Il livello STRUTTURALE, il piu' forte: non deve indovinare i nomi
    # di domani. Ogni scrittura del corpo colpisce `offerte` e basta —
    # cattura anche un «UPDATE ordini SET stato='annullato'», che
    # nessuna lista di nomi vedrebbe.
    scritture = re.findall(r"(?:UPDATE|INSERT INTO|DELETE FROM)\s+(\w+)",
                           codice)
    prova("ogni scrittura del ritiro colpisce solo `offerte`",
          {"offerte"}, set(scritture))
    prova("...e almeno una scrittura c'e' (il predicato VEDE)", True,
          len(scritture) >= 1)

    # --- 9) le sentinelle di forma ----------------------------------
    prova("la guardia di proprieta' e' nella WHERE", True,
          "o.compratore_id=?" in codice)
    prova("...e non c'e' nessun 404 che faccia da oracolo", False,
          "HTTPException(404" in codice)
    prova("il CAS sullo stato letto, col 409", True,
          "AND stato=?" in codice and "rowcount == 0" in codice
          and "HTTPException(409" in codice)
    prova("la lapide, mai un DELETE", True,
          "stato='ritirata'" in codice
          and "DELETE FROM offerte" not in codice)
    prova("la scadenza si azzera (mai un «~-3h» in pagina)", True,
          "scadenza=0" in codice)
    prova("il titolo nasce scappato", True, "html.escape(" in codice)
    prova("la notifica parte DOPO il commit", True,
          codice.rindex("con.close()") < codice.index("await notifica("))
    # il patto anti-doppione: nessun await nella sezione critica
    prova("nessun await prima dell'ultimo close", True,
          "await" not in codice[:codice.rindex("con.close()")])
    # Il gate di ruolo del gemello non deve aver imparato niente: il
    # ritiro e' una rotta sua.
    prova("rispondi_offerta non ha imparato un'azione «ritira»", False,
          "ritira" in pezzo("rispondi_offerta"))
    # «ritirata» vive in un posto solo: se qualcuno la infila in
    # _incassa_ordine, in scadenze_offerte o in un elenco di stati, si
    # sente da qui.
    prova("«ritirata» quotata vive in UN posto solo", 1,
          _SORGENTE.count("'ritirata'"))

    # --- 10) le eredita' VOLUTE non si perdono ----------------------
    # Ritirando, il compratore LIBERA il venditore: puo' lanciare la
    # lampo e andare in ferie. Non e' solo un'uscita, e' anche una
    # restituzione.
    prova("il freno della lampo guarda ancora le sole accettate vive",
          True, "stato='accettata' AND scadenza>?" in _SORGENTE)
    orolo = pezzo("scadenze_offerte")
    prova("l'orologio non ripesca le ritirate", True,
          "'proposta','controproposta','accettata'" in orolo)

    # --- 11) il client -----------------------------------------------
    mini = open("miniapp.html", encoding="utf-8").read()
    prova("il client ha la sua ritiraOfferta", True,
          "function ritiraOfferta(" in mini)
    rend = pezzo_js(mini, "function renderOfferte()", "\nfunction toggleContro")
    prova("il bottone Ritira compare in DUE rami (proposta e accettata)",
          2, rend.count("ritiraOfferta("))
    prova("la ritirata non entra fra le vive", False,
          "'ritirata'" in rend)
    # Le due meta' del gesto: chi APRE la domanda e chi ESEGUE. Le
    # ancore sono esplicite perche' fra le due funzioni non c'e' una
    # riga vuota, e pezzo_js taglia proprio li'.
    apre = mini[mini.index("function ritiraOfferta("):
                mini.index("async function inviaRitiro(")]
    esegue = mini[mini.index("async function inviaRitiro("):
                  mini.index("/* «Paga ora»: si riapre il dettaglio")]
    prova("il tetto non si hardcoda: viene dalla busta", True,
          "max_offerte" in apre)
    prova("il client chiama la rotta giusta", True,
          "/ritira`" in esegue)
    # IL PUNTO DEL CANTIERE: la domanda si fa col foglio di casa, mai
    # col dialogo del sistema operativo. (Le prove sul foglio in se'
    # — che esista, che sia in closeSheet, che nessuno lo scavalchi —
    # stanno in prove_fogli_di_casa: qui si guarda che il RITIRO ci
    # passi.)
    prova("nessun confirm() di sistema nel ritiro", False,
          "confirm(" in apre or "confirm(" in esegue)
    prova("...e nemmeno un alert()", False,
          "alert(" in apre or "alert(" in esegue)
    prova("il ritiro passa dal foglio di casa", True,
          "chiediConferma({" in apre)
    prova("...e gli passa la sua azione", True, "poi: () =>" in apre)
    # Il titolo dell'annuncio e' testo del VENDITORE dentro innerHTML,
    # e ora la testata la fabbrica un posto solo.
    prova("il titolo passa da esc()", True,
          "esc(o.titolo)" in pezzo_js(mini, "function testataOfferta("))


def prove_fogli_di_casa():
    """I dialoghi del sistema operativo che sono diventati fogli
    nostri (ago 2026). Il prompt() era il piu' stridente dei due —
    un'app che ha sostituito ogni tendina nativa non puo' chiedere
    una durata a un campo di sistema — e la riscossione era il caso
    peggiore: dentro ci si incolla una bolt11 di duecento caratteri, e
    all'errore il prompt buttava via tutto."""
    print("\n[i fogli di casa al posto dei dialoghi]")
    mini = open("miniapp.html", encoding="utf-8").read()

    # --- LA PROVA CHE VALE PIU' DI TUTTE: nessun prompt() di sistema
    # in tutto il client. Il predicato: `prompt(` non preceduto da un
    # punto (esclude `ev.prompt()`, che e' l'API d'installazione PWA e
    # ci deve restare) e non seguito subito da `)` — le chiamate vere
    # hanno sempre un argomento, mentre i COMMENTI che raccontano la
    # storia scrivono «prompt()» a parentesi vuota.
    veri = re.findall(r"(?<!\.)\bprompt\((?!\))", mini)
    prova("nessun prompt() di sistema nel client", 0, len(veri))
    # e il predicato VEDE: su un finto prompt scritto apposta deve
    # contare (o certificherebbe una pulizia che non ha guardato)
    prova("...e il predicato sa riconoscerne uno", 1,
          len(re.findall(r"(?<!\.)\bprompt\((?!\))",
                         "const g = prompt('quanti giorni?');")))
    prova("l'API d'installazione PWA non e' un dialogo di sistema",
          True, "ev.prompt()" in mini)

    def solo_codice(js):
        """Via i commenti di blocco e le righe di commento: senza,
        una sentinella che cerca «prompt(» pesca la PROSA che
        racconta il cantiere invece del programma — ed e' successo
        subito, qui e nel ritiro. La stessa lezione della sentinella
        che ricuce le stringhe spezzate."""
        js = re.sub(r"/\*[\s\S]*?\*/", "", js)
        return "\n".join(r for r in js.split("\n")
                         if not r.strip().startswith("//"))

    def fetta(firma, fine):
        return solo_codice(mini[mini.index(firma):mini.index(fine)])

    chiudi = pezzo_js(mini, "function closeSheet()")

    # --- 1) il rilancio dell'asta: era un PICKER TRAVESTITO ---------
    prova("il foglio del rilancio esiste", True,
          'id="rilancioSheet"' in mini)
    prova("...ed e' registrato in closeSheet", True,
          "rilancioSheet" in chiudi)
    ril = fetta("function rilanciaAsta(", "function renderRilancioDurate(")
    # la fine e' convertiAsta e non il foglio dopo: fra le due c'e' un
    # confirm() ancora vivo (uno dei gesti sui sats, non di questo
    # cantiere) e la fetta larga se lo pescava — l'ha detto la prova
    inv = fetta("async function inviaRilancio(", "async function convertiAsta(")
    prova("il rilancio non chiede piu' niente al sistema", False,
          "prompt(" in ril or "confirm(" in ril
          or "prompt(" in inv or "confirm(" in inv)
    prova("le durate vengono dalle leve, mai da un elenco a mano",
          True, "astaLeve && astaLeve.durate_giorni" in
          fetta("function renderRilancioDurate(",
                "function setRilancioGiorni("))
    prova("le pillole sono quelle di casa", True,
          "consegna-pill" in fetta("function renderRilancioDurate(",
                                   "function setRilancioGiorni("))
    # LA RIGA DELICATA: il rilancio ha una variabile SUA. Con
    # `sellAstaGiorni` un rilancio riscriverebbe la durata che il
    # venditore ha impostato nel form Vendi per il prossimo annuncio.
    # Si guarda TUTTA l'area del rilancio, dalla DICHIARAZIONE in giu':
    # con le sole tre funzioni la sentinella era cieca proprio sulla
    # riga dove il difetto e' piu' facile da scrivere — un
    # `let rilancioGiorni = sellAstaGiorni` non la faceva fiatare, e
    # l'ha detto la tortura, non la rilettura.
    area = fetta("let rilancioId = 0", "async function convertiAsta(")
    prova("il rilancio non tocca la durata del form Vendi", False,
          "sellAstaGiorni" in area)
    prova("...e l'area sorvegliata comprende la dichiarazione", True,
          "rilancioGiorni = 0;" in area)

    # --- 2) la riscossione: il foglio RESTA APERTO sull'errore ------
    prova("il foglio della riscossione esiste", True,
          'id="riscuotiSheet"' in mini)
    prova("...ed e' registrato in closeSheet", True,
          "riscuotiSheet" in chiudi)
    apre = fetta("function riscuotiRimborso(", "function riscuotiDigitata(")
    esegue = fetta("async function inviaRiscossione(",
                   "\n/* La sezione in testa alla scheda Ordini")
    prova("la riscossione non chiede piu' niente al sistema", False,
          "prompt(" in apre or "confirm(" in apre
          or "prompt(" in esegue or "confirm(" in esegue)
    # IL GUADAGNO VERO sul prompt(): sull'errore non si chiude e non si
    # perde la bolt11 appena incollata. La prova e' che nel ramo
    # dell'errore ci sia il `return` PRIMA di qualunque chiusura.
    ramo = esegue[esegue.index("if (!r.ok)"):]
    ramo = ramo[:ramo.index("return;")]
    prova("sull'errore il foglio NON si chiude", False,
          "classList.remove('open')" in ramo)
    prova("...e il motivo si scrive dentro", True,
          "nota.textContent" in ramo)
    prova("il campo non si svuota sull'errore", False,
          "riscuotiInv').value = ''" in esegue)
    prova("una bolt11 non sta su una riga: e' una textarea", True,
          'id="riscuotiInv"' in mini
          and "<textarea id=\"riscuotiInv\"" in mini)
    prova("il fuoco non trascina la pagina", True,
          "preventScroll" in apre)

    # --- 3) LA DOMANDA, una volta sola -----------------------------
    # Tre gesti quasi identici volevano tre fogli: il generico e' cio'
    # che rende i prossimi una CHIAMATA invece di un foglio.
    prova("il foglio della domanda esiste", True,
          'id="confermaSheet"' in mini)
    prova("...ed e' registrato in closeSheet", True,
          "confermaSheet" in chiudi)
    chiedi = fetta("function chiediConferma(", "function testataOfferta(")
    esegui = fetta("async function eseguiConferma(",
                   "/* Il ritiro del PROPONENTE")
    prova("l'azione e' anche la GUARDIA del bottone: senza, un doppio "
          "tocco la manda due volte", True,
          "confermaAzione = null;" in esegui
          and "const poi = confermaAzione; if (!poi) return;" in esegui)
    prova("il corpo si scrive con textContent (testo NUDO, niente "
          "HTML da scappare)", True, "confCorpo').textContent" in chiedi)
    prova("la testata e' facoltativa e sparisce se non c'e'", True,
          "testata.style.display" in chiedi)
    prova("chiusura MIRATA, mai closeSheet", True,
          "confermaSheet').classList.remove('open')" in esegui
          and "closeSheet()" not in esegui)
    # I CINQUE CHIAMANTI di oggi (i tre delle offerte, l'annullo della
    # modifica, e dall'ago 2026 l'AVVISO del barattolino sul proprio
    # annuncio — che e' la conferma degenere: un bottone solo e niente
    # da confermare). Il conto e' la prova che il generico e' davvero
    # condiviso: se qualcuno si scrive un foglio suo, CALA — ed e'
    # quello il verso da sorvegliare. Cresce a mano quando un gesto
    # nuovo lo adotta, come il censimento delle leve-lista.
    prova("i gesti che passano dalla domanda unica sono cinque", 5,
          solo_codice(mini).count("chiediConferma({"))
    for chi, dove in (("il ritiro", "function ritiraOfferta("),
                      ("accetta e rifiuta", "function rispondiOfferta(")):
        f = fetta(dove, "async function invia")
        prova(f"{chi}: niente dialoghi di sistema", False,
              "confirm(" in f or "prompt(" in f or "alert(" in f)
    # La controproposta NON chiede: si sta gia' scrivendo una cifra in
    # un campo, e una domanda in piu' sarebbe un ostacolo.
    risp = fetta("function rispondiOfferta(", "async function inviaRisposta(")
    # il commento qui NON si puo' cercare: `fetta` toglie i commenti
    # apposta. Si guarda il CODICE — i due rami che chiedono escono
    # con un return, e la coda della funzione manda dritto.
    prova("la controproposta non passa dalla domanda", True,
          risp.count("chiediConferma({") == 2
          and risp.rstrip().rstrip("}").rstrip().endswith(
              "inviaRisposta(id, azione, importo);"))


# ====================================================================
def prove_sollecito_a_comando():
    """IL PROMEMORIA A COMANDO (ago 2026): chi ha pagato puo' bussare
    al venditore fermo PRIMA che scatti l'automatico. La funzione non
    e' nuova — sollecita_venditori_fermi la fa gia' —, quindi le prove
    guardano quel che il bottone AGGIUNGE e soprattutto quel che NON
    deve toccare: i sats (mai), i contatori dell'automatico (mai, o
    chi bussa spesso allontanerebbe il 🧊 ai moderatori) e `aggiornato`
    (l'ancora e' `creato`, la trappola gia' pagata dalla gemella)."""
    print("\n[il promemoria a comando al venditore]")
    import asyncio
    import re
    import sqlite3

    class _H(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    ORA = 1_700_000_000
    LEVE = {"SOLLECITO_MANUALE_ORE": 48,
            "SOLLECITO_MANUALE_DIGITALE_ORE": 24,
            "SOLLECITO_MANUALE_PAUSA_ORE": 24,
            "SOLLECITO_MANUALE_MAX": 3}

    def mondo():
        vero = sqlite3.connect(":memory:")
        vero.row_factory = sqlite3.Row
        vero.execute(
            "CREATE TABLE ordini(id INTEGER PRIMARY KEY, compratore_id INT, "
            "venditore_id INT, annuncio_id INT, stato TEXT, "
            "consegna_scelta TEXT, creato INT, aggiornato INT, "
            "sollecito_manuale_il INT DEFAULT 0, "
            "solleciti_manuali INT DEFAULT 0, "
            "sollecito_venditore_il INT DEFAULT 0, "
            "solleciti_venditore INT DEFAULT 0, "
            # il timbro del bottone GEMELLO, quello del venditore
            "sollecito_il INT DEFAULT 0)")
        vero.execute("CREATE TABLE annunci(id INTEGER PRIMARY KEY, "
                     "titolo TEXT, asta_base_sats INT DEFAULT 0)")
        vero.execute("CREATE TABLE ordine_righe(id INTEGER PRIMARY KEY, "
                     "ordine_id INT, annuncio_id INT, quantita INT, "
                     "unitario_sats INT, titolo TEXT)")
        vero.execute("INSERT INTO annunci VALUES(7,'Miele di castagno',0)")
        vero.execute("INSERT INTO annunci VALUES(8,'Cuffie <b>AKG</b>',0)")
        # un annuncio ALL'ASTA: il vincitore deve ancora scegliere
        vero.execute("INSERT INTO annunci VALUES(9,'Jade all''asta',50000)")
        vero.executemany(
            "INSERT INTO ordine_righe(ordine_id, annuncio_id, quantita, "
            "unitario_sats, titolo) VALUES(?,?,?,?,?)",
            [(60, 7, 1, 1000, "Miele di castagno"),
             (60, 8, 2, 2000, "Cuffie AKG")])
        g = 3600
        righe = [
            # id, compr, vend, ann, stato, strada, creato, aggiornato,
            #     sollecito_manuale_il, solleciti_manuali,
            #     sollecito_venditore_il, solleciti_venditore
            (1, 111, 222, 7, "locked", "spedizione", ORA - 49 * g,
             ORA - g, 0, 0, ORA - 5 * g, 2),          # pronto da bussare
            (2, 111, 222, 7, "locked", "spedizione", ORA - g,
             ORA - g, 0, 0, 0, 0),                    # troppo presto
            (3, 111, 222, 7, "locked", "digitale", ORA - 25 * g,
             ORA - g, 0, 0, 0, 0),                    # codice: 24h bastano
            (4, 111, 222, 7, "locked", "spedizione", ORA - 25 * g,
             ORA - g, 0, 0, 0, 0),                    # pacco: 24h no
            (5, 111, 222, 7, "locked", "ritiro", ORA - 99 * g,
             ORA - g, 0, 0, 0, 0),                    # il ritiro sta fuori
            (6, 111, 222, 7, "locked", "", ORA - 99 * g,
             ORA - g, 0, 0, 0, 0),                    # strada non dichiarata
            (7, 111, 222, 7, "shipped", "spedizione", ORA - 99 * g,
             ORA - g, 0, 0, 0, 0),                    # gia' partito
            (8, 111, 222, 7, "locked", "spedizione", ORA - 99 * g,
             ORA - g, ORA - 99 * g, 3, 0, 0),         # al tetto
            (9, 111, 222, 7, "locked", "spedizione", ORA - 99 * g,
             ORA - g, ORA - 2 * g, 1, 0, 0),          # pausa non passata
            (10, 111, 222, 8, "locked", "spedizione", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),                    # titolo cattivo
            (60, 111, 222, 0, "locked", "spedizione", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),                    # un SET
            # stesso compratore, un ALTRO venditore: il caso che ha
            # aperto la voce — sollecitarne uno non deve zittire
            # l'altro
            (11, 111, 333, 7, "locked", "spedizione", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),
            # la via NON DICHIARATA su un annuncio normale: storici e
            # importati da Nostr si spediscono eccome
            (12, 111, 222, 7, "locked", "", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),
            # ...e su un'ASTA il cui vincitore non ha ancora scelto
            (13, 111, 222, 9, "locked", "", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),
            # e il gemello del venditore: due compratori diversi
            (30, 111, 222, 7, "shipped", "spedizione", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),
            (31, 444, 222, 7, "shipped", "spedizione", ORA - 49 * g,
             ORA - g, 0, 0, 0, 0),
        ]
        vero.executemany(
            "INSERT INTO ordini VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0)", righe)
        vero.commit()
        return vero

    def bussa(vero, ordine_id, chi=111, **leve):
        """L'ambiente e' POVERO APPOSTA: non contiene NESSUNO dei nomi
        che muovono sats. Se un domani questo bottone imparasse a
        toccarli la prova non diventa rossa — ESPLODE con NameError,
        che e' molto piu' difficile da ignorare."""
        detti = []

        class Con:
            def execute(self, *a):
                return vero.execute(*a)

            def commit(self):
                vero.commit()

            def close(self):
                pass

        async def _notifica(tg_id, testo):
            detti.append((tg_id, testo))

        amb = {"db": Con, "HTTPException": _H, "notifica": _notifica,
               "html": __import__("html"),
               "time": type("t", (), {"time": staticmethod(lambda: ORA)}),
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi},
               "_titolo_ordine": reale("_titolo_ordine")}
        amb.update(LEVE)
        amb.update(leve)
        exec("async " + pezzo("sollecita_venditore"), amb)
        try:
            esito = asyncio.new_event_loop().run_until_complete(
                amb["sollecita_venditore"](ordine_id))
            return esito, detti, None
        except _H as e:
            return None, detti, e

    def riga(vero, i):
        return vero.execute("SELECT * FROM ordini WHERE id=?", (i,)).fetchone()

    # --- 1) il giro che funziona ----------------------------------
    v = mondo()
    prima = dict(riga(v, 1))
    esito, detti, err = bussa(v, 1)
    dopo = riga(v, 1)
    prova("il promemoria parte", {"ok": True}, esito)
    prova("...e arriva al VENDITORE", [222], [t for t, _ in detti])
    prova("...una volta sola", 1, len(detti))
    prova("...il contatore sale", 1, dopo["solleciti_manuali"])
    prova("...e il timbro e' adesso", ORA, dopo["sollecito_manuale_il"])
    # LA PROVA DELLA CONVIVENZA: l'automatico non si sposta di un
    # minuto — se no chi bussa spesso allontanerebbe il momento in cui
    # un moderatore guarda il caso.
    prova("i contatori dell'automatico non si toccano",
          (prima["sollecito_venditore_il"], prima["solleciti_venditore"]),
          (dopo["sollecito_venditore_il"], dopo["solleciti_venditore"]))
    # ...e nemmeno l'ancora: `creato` e `aggiornato` restano dov'erano
    prova("l'ordine non si muove (creato, aggiornato, stato)",
          (prima["creato"], prima["aggiornato"], prima["stato"]),
          (dopo["creato"], dopo["aggiornato"], dopo["stato"]))
    prova("il testo non e' un rimprovero", True,
          "giornata storta" in detti[0][1]
          and "promemoria gentile" in detti[0][1])

    # --- 2) subito dopo: la pausa ---------------------------------
    esito, detti2, err = bussa(v, 1)
    prova("il secondo tocco non passa", 400, err and err.code)
    prova("...e dice la pausa", True, "24 ore" in (err.detail or ""))
    prova("...senza mandare niente", [], detti2)
    prova("...e senza toccare il contatore", 1,
          riga(v, 1)["solleciti_manuali"])

    # --- 3) le due finestre ---------------------------------------
    for oid, ok, che in ((2, False, "un'ora dal pagamento"),
                         (3, True, "il codice a 25 ore"),
                         (4, False, "il pacco a 25 ore")):
        v2 = mondo()
        esito, detti3, err = bussa(v2, oid)
        prova(f"finestra: {che}", ok, esito is not None)
        if not ok:
            prova(f"...e il 400 dice di aspettare ({che})", True,
                  "presto" in (err.detail or ""))

    # --- 4) chi resta fuori ---------------------------------------
    for oid, che in ((5, "il ritiro in zona"),
                     (7, "l'ordine gia' spedito")):
        v2 = mondo()
        esito, detti4, err = bussa(v2, oid)
        prova(f"fuori: {che}", (400, "Operazione non permessa"),
              (err and err.code, err and err.detail))
        prova(f"...e nessuno riceve niente ({che})", [], detti4)

    # --- 4-bis) LA VIA NON DICHIARATA (ago 2026, dal campo) -------
    # Il bottone non compariva su ordini pagati da settimane: la via
    # vuota — storici e annunci importati da Nostr — era esclusa
    # insieme al ritiro. Ma li' il venditore PUO' spedire: il rifiuto
    # di segna_spedito scatta solo sull'ASTA che aspetta la scelta del
    # vincitore, ed e' quella la domanda da fare.
    v2 = mondo()
    esito, dv, err = bussa(v2, 12)
    prova("la via non dichiarata adesso passa", {"ok": True}, esito)
    prova("...e il promemoria parte davvero", [222], [t for t, _ in dv])
    v2 = mondo()
    esito, dv2, err = bussa(v2, 13)
    prova("...ma l'asta che aspetta la scelta resta fuori", 400,
          err and err.code)
    prova("...e il 400 dice a chi legge cosa deve fare", True,
          "scegli come vuoi riceverlo" in (err.detail or ""))
    prova("...senza mandare niente a nessuno", [], dv2)
    prova("il ritiro in zona invece resta fuori davvero", 400,
          bussa(mondo(), 5)[2].code)
    # LE DUE STRADE FANNO LA STESSA DOMANDA, o una promette quel che
    # l'altra nega: entrambe leggono `asta_base_sats` sul ramo vuoto.
    for f in ("sollecita_venditore", "segna_spedito"):
        c4 = pezzo(f)
        prova(f"{f} chiede dell'asta sulla via vuota", True,
              'if not o["consegna_scelta"]:' in c4
              and "SELECT asta_base_sats FROM annunci" in c4)

    # --- 5) il tetto ----------------------------------------------
    v2 = mondo()
    esito, detti5, err = bussa(v2, 8)
    prova("al tetto non si bussa piu'", 400, err and err.code)
    prova("...e la strada che resta e' la disputa", True,
          "disputa" in (err.detail or ""))
    esito, _, err = bussa(mondo(), 9)
    prova("la pausa vale anche sotto il tetto", 400, err and err.code)

    # --- 6) di chi e' il gesto ------------------------------------
    # ANTI-ORACOLO: il venditore, un estraneo e un ordine che non
    # esiste devono ricevere la STESSA risposta, o in fila si impara
    # quali ordini esistono.
    risposte = []
    for chi, oid in ((222, 1), (333, 1), (111, 999)):
        v2 = mondo()
        esito, detti6, err = bussa(v2, oid, chi=chi)
        risposte.append((err and err.code, err and err.detail))
        prova(f"niente notifiche (chi={chi}, ordine={oid})", [], detti6)
    prova("venditore, estraneo e ordine inesistente: stessa risposta",
          1, len(set(risposte)))
    prova("...ed e' il 400 dei fratelli",
          (400, "Operazione non permessa"), risposte[0])

    # --- 7) il titolo, scappato all'assegnazione ------------------
    v2 = mondo()
    esito, detti7, err = bussa(v2, 10)
    testo = detti7[0][1]
    prova("il titolo cattivo esce scappato", True, "&lt;b&gt;" in testo)
    prova("...e i grassetti restano PARI", testo.count("<b>"),
          testo.count("</b>"))

    # --- 8) il SET ha il suo titolo -------------------------------
    v2 = mondo()
    esito, detti8, err = bussa(v2, 60)
    prova("il set porta il titolo sintetizzato", True,
          "Miele di castagno + 1 altri" in detti8[0][1])

    # --- 9) le leve spente ----------------------------------------
    esito, _, err = bussa(mondo(), 1, SOLLECITO_MANUALE_MAX=0)
    prova("MAX a 0 spegne il gesto", 400, err and err.code)
    esito, _, err = bussa(mondo(), 1, SOLLECITO_MANUALE_ORE=0)
    prova("finestra a 0 spegne la sua popolazione", 400, err and err.code)
    esito, _, err = bussa(mondo(), 3, SOLLECITO_MANUALE_DIGITALE_ORE=0)
    prova("...e vale per il digitale separatamente", 400, err and err.code)

    # --- 10) le sentinelle sulla forma ---------------------------
    c = pezzo("sollecita_venditore")
    # il CORPO, senza la docstring: li' dentro `aggiornato` compare
    # apposta, a raccontare la trappola che si sta evitando
    corpo = c.split('"""')[2]
    prova("l'ancora e' `creato`, mai `aggiornato`", True,
          'o["creato"] + finestra' in corpo and "aggiornato" not in corpo)
    prova("la guardia di proprieta' sta dentro la WHERE", True,
          "o.compratore_id=?" in c and "o.stato='locked'" in c)
    prova("il titolo nasce scappato", True,
          "titolo = html.escape(" in c)
    prova("la notifica parte DOPO il commit", True,
          c.index("con.commit()") < c.index("await notifica("))
    # il gemello del venditore resta quello che era: questo cantiere
    # non lo tocca (le due colonne sono diverse apposta)
    prova("il bottone del venditore non ha cambiato colonna", True,
          "sollecito_il=?" in pezzo("sollecita_acquirente"))

    # --- 10-bis) DUE ORDINI NON SI BLOCCANO A VICENDA ------------
    # Il caso dal campo: sollecitato un venditore, il bottone su un
    # ALTRO ordine rispondeva «aspetta 24 ore». La pausa e il tetto
    # sono di ogni ORDINE, mai della persona — qui si prova sul pezzo
    # vero, due righe di fila, e non su una rilettura del codice.
    v = mondo()
    e1, d1, x1 = bussa(v, 1)              # ordine 1, venditore 222
    e2, d2, x2 = bussa(v, 11)             # ordine 11, venditore 333
    prova("il primo ordine passa", ({"ok": True}, None), (e1, x1))
    prova("...e il secondo pure, subito dopo", ({"ok": True}, None),
          (e2, x2))
    prova("...con due destinatari diversi", [222, 333],
          [t for t, _ in d1 + d2])
    conti = {r["id"]: (r["solleciti_manuali"], r["sollecito_manuale_il"])
             for r in v.execute("SELECT * FROM ordini WHERE id IN (1,11,60)")}
    prova("...e ogni riga ha il SUO conto, a uno per uno",
          {1: (1, ORA), 11: (1, ORA), 60: (0, 0)}, conti)
    # il terzo tocco sullo stesso ordine invece si ferma: e' li' che
    # la pausa deve mordere
    e3, d3, x3 = bussa(v, 1)
    prova("...mentre sullo STESSO ordine la pausa morde", 400,
          x3 and x3.code)

    # --- 10-ter) e lo stesso vale per il bottone del VENDITORE ----
    def sollecita_come_venditore(vero, ordine_id, chi=222):
        detti = []

        class Con:
            def execute(self, *a):
                return vero.execute(*a)

            def commit(self):
                vero.commit()

            def close(self):
                pass

        async def _notifica(tg_id, testo):
            detti.append((tg_id, testo))

        amb = {"db": Con, "HTTPException": _H, "notifica": _notifica,
               "time": type("t", (), {"time": staticmethod(lambda: ORA)}),
               "Header": lambda d="": d, "Cookie": lambda d="": d,
               "verifica_utente": lambda h, s: {"id": chi}}
        exec("async " + pezzo("sollecita_acquirente"), amb)
        try:
            esito = asyncio.new_event_loop().run_until_complete(
                amb["sollecita_acquirente"](ordine_id))
            return esito, detti, None
        except _H as e:
            return None, detti, e

    v2 = mondo()
    g1, n1, y1 = sollecita_come_venditore(v2, 30)
    g2, n2, y2 = sollecita_come_venditore(v2, 31)
    prova("il gemello: il primo ordine passa", ({"ok": True}, None),
          (g1, y1))
    prova("...e il secondo pure, con un altro compratore",
          ({"ok": True}, None), (g2, y2))
    prova("...e sono arrivati a due persone diverse", [111, 444],
          [t for t, _ in n1 + n2])
    g3, n3, y3 = sollecita_come_venditore(v2, 30)
    prova("...mentre sullo STESSO ordine la pausa morde", 400,
          y3 and y3.code)

    # --- 10-quater) il conto sta sulla RIGA, non sulla persona ----
    for nome, c2 in (("il promemoria a comando", corpo),
                     ("il gemello del venditore",
                      pezzo("sollecita_acquirente"))):
        agg = c2[c2.index("UPDATE ordini"):]
        agg = agg[:agg.index(")")]
        prova(f"{nome}: l'UPDATE timbra UNA riga", True,
              "WHERE id=?" in agg
              and "compratore_id" not in agg and "venditore_id" not in agg)

    # --- 11) il giudice del client -------------------------------
    mini = open("miniapp.html", encoding="utf-8").read()
    g = mini[mini.index("function statoSollecito("):]
    g = g[:g.index("\n}")]
    prova("il client guarda `creato` e non `aggiornato`", True,
          "o.creato" in g and "aggiornato" not in g)
    prova("...e tiene fuori il ritiro in zona", True,
          "o.consegnaScelta==='ritiro'" in g)
    prova("...e l'asta che aspetta la scelta del vincitore", True,
          "!o.consegnaScelta && o.asta" in g)
    prova("...ma non la sola via non dichiarata", False,
          "['spedizione','digitale'].includes(o.consegnaScelta)" in g)
    prova("...e il tetto non e' scritto a mano", True,
          "SOLLECITO.max" in g and not re.search(r">=\s*3\b", g))

    # --- 12) IL BOTTONE SPENTO DICE PERCHE' ----------------------
    # Sparire non e' gratis: dal campo, un bottone che c'era e un
    # attimo dopo non c'e' piu' si legge come un guasto. Tre stati,
    # non due — e quello che NON deve esserci resta il «e' presto»,
    # o l'attesa normale diventa un conto alla rovescia.
    b = pezzo_js(mini, "function bottoneSollecito(o){")
    prova("il giudice ha tre esiti, non due", True,
          "return 'tetto'" in g and "return 'pausa'" in g
          and "return 'ok'" in g)
    prova("...e «è presto» resta il NIENTE", True,
          "return '';   // è ancora presto" in g)
    prova("la pausa lo lascia in pagina, spento e col perché", True,
          "Già ricordato oggi — riprova domani" in b)
    prova("...e il tetto pure, col numero della leva", True,
          "Hai già ricordato ${SOLLECITO.max} volte" in b)
    prova("da spento NON c'e' nessun onclick", 1, b.count("onclick="))
    prova("...ed e' quello dello stato 'ok'", True,
          "st === 'ok'" in b
          and b.index("st === 'ok'") < b.index("onclick="))
    # la DEMO non ha `creato`: la somma fa NaN, e il NOT della forma
    # positiva la fa cadere sul ramo «non c'e'» invece che su 'ok'
    prova("la finestra e' scritta a prova di NaN", True,
          "if (!(o.creato + ore*3600 <= adesso))" in g)
    prova("...e cosi' la pausa", True,
          "if (!(o.sollecitoManualeIl + SOLLECITO.pausa*3600 <= adesso))"
          in g)
    prova("il dettaglio chiama la fabbrica del bottone", True,
          "${bottoneSollecito(o)}" in mini)
    # IL DOPPIO TOCCO: finche' la risposta e' per strada il bottone
    # dev'essere spento, o il secondo tocco si becca il 400 della
    # pausa e si legge come un tetto sbagliato.
    for f, chi in (("sollecitaVenditore", "il compratore"),
                   ("sollecita", "il venditore")):
        c3 = mini[mini.index(f"async function {f}(btn){{"):]
        c3 = c3[:c3.index("\n}")]
        prova(f"il bottone di {chi} si spegne durante l'invio", True,
              "btn.disabled = true" in c3
              and c3.index("btn.disabled = true") < c3.index("await fetch"))
    prova("il bottone della disputa ha la forma di casa", True,
          'class="btn allarme" onclick="openDispute()"' in mini
          and 'class="btn danger-ghost" onclick="openDispute()"' not in mini)

    # --- 13) LO SPAZIO E' DELLA COPPIA, NON DEL BOTTONE ----------
    # La regola di ieri (`#orderContent .btn + .btn`) non aveva una
    # sentinella, e nel frattempo tre margini scritti a mano la
    # scavalcavano ancora — misurati dal vivo: il gesto principale a
    # 0px dalla didascalia di @trackbot. Qui si sorveglia che quei
    # margini non tornino: sono righe che un riordino rimette senza
    # rompere niente di visibile a chi legge il codice.
    # UN SELETTORE PER LE DUE COLONNE (ago 2026): il dettaglio
    # dell'annuncio aveva lo stesso difetto e la stessa causa, e due
    # regole gemelle sarebbero due numeri da tenere in pari.
    FRATELLI = "#orderContent .btn + .btn,#detailContent .btn + .btn"
    USCITA = "#orderContent .btn.allarme,#detailContent .btn.allarme"
    prova("lo spazio fra bottoni e' detto fra FRATELLI", True,
          FRATELLI + "{margin-top:10px}" in mini)
    prova("...e vale nelle DUE colonne, con un selettore solo", 1,
          mini.count("#detailContent .btn + .btn"))
    prova("...e l'uscita resta staccata, DOPO di lui", True,
          USCITA + "{margin-top:18px}" in mini and FRATELLI in mini
          and mini.index(FRATELLI) < mini.index(USCITA))
    for f, chi in (("bottoneNotifichePacco(o, s){", "le notifiche del pacco"),
                   ("o.role==='seller' && s==='shipped' ?",
                    "il sollecito del venditore")):
        b2 = mini[mini.index(f):]
        b2 = b2[:b2.index("</button>")]
        # il solo TAG, o il commento che racconta la storia (e nomina
        # il margine tolto) terrebbe rossa una prova gia' verde
        b2 = b2[b2.rindex("<button"):]
        prova(f"{chi}: nessun margine suo sul bottone", False,
              "margin-top:0" in b2)
    # la didascalia si infila FRA due bottoni: senza il margine sotto,
    # quel che viene dopo le si incolla (e' il difetto misurato)
    d2 = pezzo_js(mini, "function bottoneNotifichePacco(o, s){")
    prova("la didascalia porta lo spazio della coppia sotto", True,
          'style="margin:2px 0 10px;text-align:center"' in d2)

    # --- 14) LA COLONNA DEL PROPRIETARIO -------------------------
    # Stesso difetto dell'ordine, stessa causa: nel dettaglio di un
    # annuncio proprio lampo e Modifica si toccavano (0px), tenuti li'
    # da tre `margin-top:0` scritti prima che una regola esistesse.
    # Qui si guarda che NESSUNO torni: la regola dei fratelli sopra
    # non serve a niente se un inline la scavalca.
    det = mini[mini.index("function openDetail(id){"):]
    det = det[:det.index("aggiornaCurToggle();")]
    prova("nel dettaglio nessun bottone si ricompra un margine suo",
          0, det.count("margin-top:0"))
    prova("...nemmeno il Rifornisci dell'esaurito", False,
          'margin-top:0" onclick="apriRifornisci' in mini)
    # IL BOTTONE CHE ELIMINA: il testuale sottolineato spariva fra due
    # ghost — il gesto piu' consequenziale della colonna era anche il
    # meno visibile. Stessa ricetta della disputa: velato, mai pieno.
    prova("eliminare ha la forma di casa, col rosso velato", 2,
          det.count('class="btn allarme" onclick="deleteListing('))
    prova("...e non e' piu' un testuale sottolineato", False,
          'danger-ghost" onclick="deleteListing(' in mini)
    # il gemello del moderatore fa la STESSA cosa su un annuncio
    # altrui: due bottoni cosi' non possono avere due vestiti, anche
    # se non si vedono mai insieme
    prova("anche il Rimuovi del moderatore porta lo stesso vestito",
          True, 'class="btn allarme" onclick="rimuoviModerazione('
          in det)
    prova("...e nella colonna non resta un solo rosso testuale",
          False, "danger-ghost" in det)
    prova("...e il testo dice solo cosa fa", True,
          "🗑 Elimina l'annuncio</button>" in det
          and "Questo è un tuo annuncio — eliminalo" not in mini)


# ====================================================================
def prove_ordini_fermi():
    """LA CODA DEGLI ORDINI FERMI (ago 2026) e la riga che resta.

    Ogni sollecito bussa N volte, manda UN 🧊 e poi tace per sempre: da
    li' in poi un ordine coi sats in cassaforte non compariva in
    nessuna lista e si raggiungeva solo sapendone il numero.
    Si prova DAVVERO — l'endpoint girato su un database gemello in
    memoria, ermetico — perche' una query di coda sbagliata non
    fallisce, TACE, che e' il peggior modo di fallire per un allarme:
    la stessa ragione per cui esiste prove_libro_mastro."""
    print("\n[la coda degli ordini fermi]")
    import re
    import sqlite3
    import time as _t

    corpo = pezzo("coda_fermi")
    c = codice(corpo)
    i = _SORGENTE.index("_SQL_FERMI = (")
    sql_src = _SORGENTE[i:_SORGENTE.index("\n\n\n", i)]
    amb_sql = {}
    exec(sql_src, amb_sql)
    SQL = amb_sql["_SQL_FERMI"]

    # --- 1) LEGGE E BASTA -------------------------------------------
    # E' il vincolo del cantiere, e sparirebbe in silenzio il giorno
    # che qualcuno «ripara» al volo una riga ferma.
    for vietato in ("INSERT", "UPDATE", "DELETE", "DROP", "REPLACE"):
        prova(f"la coda non fa {vietato}", False, vietato in c.upper())
    for nome in ("_sblocca_sats", "_rimborsa_compratore", "_paga_rimborso",
                 "paga_venditore", "notifica"):
        prova(f"...e non chiama {nome}", False, nome in c)
    # `def` e non `async def`: non c'e' niente da aspettare, e l'async
    # e' il primo passo per infilarci dentro un await notifica(...)
    prova("e' sincrona", True, "async def coda_fermi" not in _SORGENTE)
    prova("la guardia e' quella delle sorelle", True,
          'if not e_admin(user["id"])' in c
          and 'HTTPException(403, "Riservato ai moderatori")' in c)
    # non e' un giro periodico: nell'orologio non ci deve entrare
    orologio = pezzo("orologio")
    prova("non e' agganciata all'orologio", True,
          "coda_fermi" not in orologio and "_SQL_FERMI" not in orologio)

    # --- 2) LE ANCORE -----------------------------------------------
    # Uno zero deve far comparire la riga in CIMA, mai sparire: in
    # SQLite «NULL < x» vale NULL, quindi una guardia sull'ancora
    # nasconderebbe l'ordine dalla coda degli ordini spariti. E' il
    # difetto che i due solleciti di 'shipped' hanno davvero, col loro
    # «AND spedito_il > 0».
    prova("nessuna guardia di confronto sulle ancore", None,
          re.search(r"o\.(creato|spedito_il|consegnato|aggiornato)\s*[><]",
                    SQL))
    # ogni ramo dell'ancora DEVE cominciare con un COALESCE: e' quello
    # che trasforma un NULL in uno zero, cioe' in una riga che compare
    # in cima invece di sparire
    case = SQL[SQL.index("CASE o.stato"):SQL.index("END AS fermo_da")]
    prova("ogni ramo dell'ancora e' un COALESCE", 4,
          len(re.findall(r"(?:WHEN '\w+' THEN|ELSE)\s*COALESCE\(", case)))
    prova("l'ancora di 'locked' e' `creato`, mai `aggiornato`", True,
          "WHEN 'locked' THEN COALESCE(o.creato, 0)" in SQL)
    # i terminali stanno fuori, e 'creato' con loro: li' i sats non
    # sono ancora in cassaforte, e se ne occupa controlla_abbandonati
    prova("la porta e' il complemento dei terminali", True,
          "NOT IN ('creato','released','refunded','annullato')" in SQL)
    prova("dal piu' fermo, con l'id a pareggiare", True,
          "ORDER BY fermo_da ASC, id ASC" in SQL)
    prova("nessun LIMIT: la coda non nasconde le righe piu' vecchie",
          False, "LIMIT" in SQL.upper())
    prova("i JOIN sono LEFT (i set, e la riga utenti che manca)", 3,
          SQL.count("LEFT JOIN"))

    # --- 3) L'INVARIANTE DELLA SOGLIA -------------------------------
    # «Se il 🧊 e' partito, la riga c'e'»: la coda non puo' mai essere
    # piu' povera delle notifiche gia' mandate. Dipende dalle leve,
    # quindi si RIFA' IL CONTO invece di ricordarselo — chi stringe un
    # passo trova questa riga rossa.
    def leva(nome):
        m = re.search(rf"^    {nome} = (\d+)", _SORGENTE, re.M)
        return int(m.group(1))

    passo, tetto = leva("PROMEMORIA_CONFERMA_GIORNI"), leva(
        "PROMEMORIA_CONFERMA_MAX")
    inc_passo, inc_tetto = leva("SOLLECITO_INCASSO_GIORNI"), leva(
        "SOLLECITO_INCASSO_MAX")
    ghiacci = {
        "merce mai partita": leva("PROMEMORIA_SPEDIZIONE_GIORNI") + tetto * passo,
        "codice mai consegnato": leva("PROMEMORIA_DIGITALE_ORE") // 24
                                 + tetto * passo,
        "busta mai depositata": leva("PROMEMORIA_BUSTA_GIORNI") + tetto * passo,
        "ritiro fermo": inc_passo * (inc_tetto + 1),
        "incasso fermo": inc_passo * (inc_tetto + 1)}
    soglia = leva("CODA_FERMI_GIORNI")
    for nome, giorno in ghiacci.items():
        prova(f"la coda apre PRIMA del 🧊 «{nome}» (g.{giorno})", True,
              0 < soglia < giorno)
    # ORE_CONFERMA e GIORNI_AUTO_SBLOCCO vivono solo nel config, quindi
    # le due famiglie di 'shipped'/'delivered' restano fuori dal conto:
    # dichiarato, non dimenticato.
    prova("le due leve senza default restano fuori dal conto", True,
          not re.search(r"^    (ORE_CONFERMA|GIORNI_AUTO_SBLOCCO) = ",
                        _SORGENTE, re.M))
    prova("la leva e' anche nel config d'esempio", True,
          "CODA_FERMI_GIORNI" in open("config_esempio.py",
                                      encoding="utf-8").read())
    prova("...e censita nel pannello delle leve", True,
          '"CODA_FERMI_GIORNI", CODA_FERMI_GIORNI' in _SORGENTE)

    # --- 4) L'ENDPOINT, GIRATO DAVVERO ------------------------------
    ORA, G = 1_800_000_000, 86400

    class _Errore(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    class _SenzaClose:
        """close() non chiude: un :memory: chiuso sparisce, e qui la
        connessione la riusano tutte le chiamate del giro."""
        def __init__(self, con): self._c = con
        def __getattr__(self, n): return getattr(self._c, n)
        def close(self): pass

    def apparecchia():
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.executescript("""
        CREATE TABLE ordini(id INTEGER PRIMARY KEY, annuncio_id INT,
          compratore_id INT, venditore_id INT, stato TEXT,
          prezzo_sats INT, creato INT, aggiornato INT,
          spedito_il INT DEFAULT 0, consegnato INT DEFAULT 0,
          consegna_scelta TEXT DEFAULT '', via_punto INT DEFAULT 0,
          disputata INT DEFAULT 0,
          solleciti_venditore INT DEFAULT 0,
          sollecito_venditore_il INT DEFAULT 0,
          solleciti_ritiro INT DEFAULT 0, sollecito_ritiro_il INT DEFAULT 0,
          solleciti_conferma INT DEFAULT 0,
          sollecito_conferma_il INT DEFAULT 0,
          solleciti_incasso INT DEFAULT 0, sollecito_incasso_il INT DEFAULT 0,
          solleciti_busta INT DEFAULT 0, sollecito_busta_il INT DEFAULT 0,
          indirizzo_atteso INT DEFAULT 0, indirizzo_il INT DEFAULT 0);
        CREATE TABLE annunci(id INTEGER PRIMARY KEY, titolo TEXT);
        CREATE TABLE ordine_righe(id INTEGER PRIMARY KEY, ordine_id INT,
          titolo TEXT, quantita INT);
        CREATE TABLE utenti(tg_id INTEGER PRIMARY KEY,
          npub_accesso TEXT DEFAULT '', npub_verificata INT DEFAULT 0);
        INSERT INTO annunci VALUES(7,'Bici da corsa');
        INSERT INTO utenti VALUES(111,'',0),(222,'',0),(-9,'',0);
        """)
        return con

    def metti(con, id, stato, **kw):
        d = dict(annuncio_id=7, compratore_id=111, venditore_id=222,
                 prezzo_sats=50000, creato=ORA - 30 * G,
                 aggiornato=ORA - 30 * G, consegna_scelta='spedizione')
        d.update(kw)
        con.execute("INSERT INTO ordini(id,stato," + ",".join(d) +
                    ") VALUES(?,?," + ",".join("?" * len(d)) + ")",
                    [id, stato] + list(d.values()))

    def gira(con, admin=True, giorni=None, ora=ORA):
        amb = {"Header": lambda d: d, "Cookie": lambda d: d,
               "HTTPException": _Errore, "db": lambda: _SenzaClose(con),
               "e_admin": lambda i: admin,
               "verifica_utente": lambda *a: {"id": 999},
               "_titolo_ordine": reale("_titolo_ordine"),
               "time": type("t", (), {"time": staticmethod(lambda: ora)}),
               "CODA_FERMI_GIORNI": soglia if giorni is None else giorni,
               "_SQL_FERMI": SQL,
               "app": type("a", (), {"get": lambda *a, **k: (lambda f: f)})()}
        exec(corpo, amb)
        return amb["coda_fermi"]("", "")

    con = apparecchia()
    metti(con, 1, 'locked', consegna_scelta='')          # nessuno lo chiama
    metti(con, 2, 'locked', aggiornato=ORA - G)          # ancora immobile
    metti(con, 3, 'locked', creato=ORA - 3 * G, aggiornato=ORA - 3 * G)
    metti(con, 4, 'shipped', spedito_il=0)               # ancora vuota
    metti(con, 5, 'delivered', consegnato=0, spedito_il=ORA - 40 * G)
    metti(con, 6, 'locked', creato=None)                 # creato NULL
    metti(con, 7, 'locked', annuncio_id=0)               # un set
    metti(con, 8, 'confirmed', disputata=1)
    metti(con, 9, 'refund')
    metti(con, 10, 'released')
    metti(con, 11, 'refunded')
    metti(con, 12, 'annullato')
    metti(con, 13, 'creato')
    metti(con, 14, 'dispute')
    metti(con, 15, 'locked', venditore_id=-9, solleciti_venditore=4,
          sollecito_venditore_il=ORA - 2 * G)
    metti(con, 16, 'locked', consegna_scelta='ritiro', solleciti_ritiro=5)
    con.execute("INSERT INTO ordine_righe VALUES(1,7,'Miele',2),(2,7,'Cera',1)")
    con.commit()

    prima = con.execute("SELECT * FROM ordini ORDER BY id").fetchall()
    righe = gira(con)
    visti = [r["id"] for r in righe]

    prova("l'ordine che nessun sollecito copre c'e'", True, 1 in visti)
    prova("...e quello che il venditore ha ri-toccato ieri pure", True,
          2 in visti)
    prova("lo 'shipped' senza `spedito_il` non sparisce", True, 4 in visti)
    prova("...ne' il 'delivered' senza `consegnato`", True, 5 in visti)
    prova("...ne' la riga con `creato` NULL", True, 6 in visti)
    prova("il set c'e', col titolo sintetizzato", "Miele + 1 altri",
          next(r["titolo"] for r in righe if r["id"] == 7))
    prova("il 'refund', che nessuno sollecita mai, c'e'", True, 9 in visti)
    prova("...e la disputa dimenticata da un mese", True, 14 in visti)
    prova("l'ordine fresco resta fuori", False, 3 in visti)
    for id, stato in ((10, 'released'), (11, 'refunded'),
                      (12, 'annullato'), (13, 'creato')):
        prova(f"'{stato}' resta fuori", False, id in visti)
    prova("l'ancora vuota sta in CIMA, non sparisce", 6, visti[0])
    prova("...e il resto e' dal piu' fermo", True,
          [r["fermo_da"] for r in righe] ==
          sorted(r["fermo_da"] for r in righe))
    r15 = next(r for r in righe if r["id"] == 15)
    prova("il nativo Nostr senza chiave e' irraggiungibile", 0,
          r15["venditore_ok"])
    prova("...ma il compratore Telegram no", 1, r15["compratore_ok"])
    prova("il contatore dice quante volte ha bussato la macchina", 4,
          r15["promemoria"])
    prova("...e a zero dice che non l'ha chiamato nessuno", 0,
          next(r["promemoria"] for r in righe if r["id"] == 1))
    prova("il ritiro fermo entra come tutti", True, 16 in visti)
    prova("la disputa gia' decisa porta il suo flag", 1,
          next(r["disputata"] for r in righe if r["id"] == 8))

    # LEGGE E BASTA, provato e non sperato
    prova("il database non si e' mosso di un byte",
          [tuple(r) for r in prima],
          [tuple(r) for r in
           con.execute("SELECT * FROM ordini ORDER BY id")])

    # due righe ferme dallo stesso secondo non devono ballare: a
    # sorvegliare l'ORDER BY c'e' la sentinella sul testo, qui si
    # guarda la proprieta' che si vede da fuori
    pari = [r["id"] for r in righe
            if r["fermo_da"] == righe[-1]["fermo_da"]]
    prova("a parita' di attesa gli id sono crescenti", sorted(pari), pari)

    # la leva spenta spegne, e il database non si tocca NEMMENO
    def _mai():
        raise AssertionError("a leva spenta il database non si tocca")
    amb = {"Header": lambda d: d, "Cookie": lambda d: d,
           "HTTPException": _Errore, "db": _mai, "e_admin": lambda i: True,
           "verifica_utente": lambda *a: {"id": 999},
           "_titolo_ordine": reale("_titolo_ordine"), "time": _t,
           "CODA_FERMI_GIORNI": 0, "_SQL_FERMI": SQL,
           "app": type("a", (), {"get": lambda *a, **k: (lambda f: f)})()}
    exec(corpo, amb)
    prova("a leva spenta la coda e' vuota", [], amb["coda_fermi"]("", ""))

    # e chi non modera non entra
    try:
        gira(con, admin=False)
        prova("chi non modera prende il 403", True, False)
    except _Errore as e:
        prova("chi non modera prende il 403", 403, e.code)

    # un mercatino tutto fresco non deve pescare niente
    con2 = apparecchia()
    metti(con2, 1, 'locked', creato=ORA - G, aggiornato=ORA - G)
    metti(con2, 2, 'shipped', spedito_il=ORA - 2 * G)
    con2.commit()
    prova("col mercatino in movimento la coda tace", [], gira(con2))

    # --- 5) IL CLIENT -----------------------------------------------
    mini = open("miniapp.html", encoding="utf-8").read()
    g = pezzo_js(mini, "function notaFermo(o){", "\n}")
    prova("la riga e' del compratore, su 'locked'", True,
          "o.role!=='buyer' || o.state!=='locked'" in g)
    prova("...fuori il ritiro, che ha gia' la sua nota", True,
          "o.consegnaScelta==='ritiro'" in g)
    prova("...e l'asta in cui la palla e' del compratore", True,
          "!o.consegnaScelta && o.asta" in g)
    # la riga NON e' il bottone: il tetto e la leva a zero non la
    # devono spegnere, o si toglierebbero le parole insieme allo squillo
    prova("il tetto dei promemoria non la spegne", False,
          "sollecitiManuali" in g)
    prova("...ne' la leva a zero", False, "SOLLECITO.max" in g)
    prova("condivide pero' la finestra del bottone", True,
          "SOLLECITO.daDig" in g and "SOLLECITO.da" in g)
    # in DEMO `creato` non c'e': la somma fa NaN e il NOT della forma
    # positiva la fa cadere sul ramo «non c'e'»
    prova("la finestra e' scritta a prova di NaN", True,
          "if (!(o.creato + ore*3600 <= Date.now()/1000)) return '';" in g)
    # deve restare vera anche al giorno 40, quando i promemoria hanno
    # smesso: niente promesse su cosa sta facendo la macchina
    prova("non promette che qualcuno stia sollecitando", True,
          "stiamo ricordando" not in g and "solleciter" not in g)
    prova("...e dice che nessun timer li muove", True,
          "nessun timer li muove" in g)
    prova("il dettaglio la disegna sopra i due bottoni", True,
          mini.index("${notaFermo(o)}")
          < mini.index("${bottoneSollecito(o)}")
          < mini.index('onclick="openDispute()"'))

    prova("il pannello non impara a fare fetch di nascosto", 1,
          mini.count("/admin/fermi"))
    # «⏳ In revisione» vive anche nel badge dei PROPRI annunci,
    # molto piu' su nel file: l'ancora e' quella del pannello
    prova("la coda sta fra i pagamenti e la revisione", True,
          mini.index("🧊 Pagamenti da verificare (${incerti.length})")
          < mini.index("${boxFermi()}")
          < mini.index("⏳ In revisione (${rev.length})"))
    # il pallino resta com'era: una coda che puo' restare piena per
    # settimane accenderebbe un cartello sempre acceso, e un cartello
    # sempre acceso non lo guarda nessuno
    chiamate = [r for r in mini.split("\n") if "aggiornaAdmDot(" in r
                and "function aggiornaAdmDot" not in r]
    prova("il pallino ha ancora due soli chiamanti", 2, len(chiamate))
    prova("...e nessuno dei due ha imparato la coda dei fermi", True,
          all("fermi" not in r for r in chiamate))
    riga = pezzo_js(mini, "const rigaFermo = o => {", "\n};")
    prova("il titolo dal database passa da esc()", True,
          "esc(o.titolo)" in riga)
    prova("negli onclick viaggia solo il numero", True,
          "apriOrdinePerId(${o.id})" in riga
          and "scriviAParte(${o.venditore_id})" in riga)
    prova("chi non e' raggiungibile non ha il bottone «scrivi»", 2,
          riga.count("🔇"))
    prova("«mostra i piu' vecchi» ridisegna e non rifa' le fetch", True,
          "apriTuttiFermi();return false" in mini
          and "loadAdminStats" not in pezzo_js(
              mini, "function apriTuttiFermi(){", "\n}"))

    # --- 6) IL CASO INCAGLIATO --------------------------------------
    # risolvi_disputa accetta confirmed/refund con disputata=1, ma i
    # bottoni comparivano solo su 'dispute': la coda ci portava davanti
    # a un caso decidibile senza dare il modo di deciderlo.
    prova("il server accetta ancora il caso incagliato", True,
          "disputata=1 AND stato IN ('confirmed','refund')"
          in _SORGENTE.replace("\n", " ").replace("  ", " ")
          or "(disputata=1 AND stato IN ('confirmed','refund'))" in _SORGENTE)
    prova("...e ora il client offre i bottoni", True,
          "isAdmin && (s==='dispute' ||" in mini
          and "(o.disputata && ['confirmed','refund'].includes(s)))" in mini)
    prova("...con `disputata` che arriva fino al client", True,
          "disputata:o.disputata||0," in mini)


# ====================================================================
def prove_numero_ordine():
    """IL NUMERO DELL'ORDINE SI VEDE (ago 2026, caso dal campo: un
    utente segnala un problema e per ritrovare il suo ordine bisognava
    chiedergli il nome dell'oggetto e cercarlo nel database).
    Le due cose da sorvegliare non sono la resa — quella si guarda a
    schermo — ma: che il numero sia UNO SOLO, cioe' `ordini.id`, lo
    stesso che il moderatore batte in «Apri un ordine per numero»; e
    che il gesto della copia non possa diventare silenzioso."""
    print("\n[il numero dell'ordine]")
    mini = open("miniapp.html", encoding="utf-8").read()

    def solo_codice(js):
        """Via i commenti, o una sentinella pesca la prosa che
        racconta il cantiere invece del programma."""
        js = re.sub(r"/\*[\s\S]*?\*/", "", js)
        return "\n".join(r for r in js.split("\n")
                         if not r.strip().startswith("//"))

    # --- 1) UN'IDENTITA' SOLA ---------------------------------------
    # E' il cuore della richiesta di Andrea: se il numero mostrato non
    # fosse `o.id`, chi lo legge e chi lo cerca parlerebbero di due
    # cose diverse — che e' peggio di non mostrarlo affatto.
    prova("il numero mostrato e' `o.id`, e la fabbrica e' una sola", 1,
          mini.count("function numeroOrdine("))
    # ATTENZIONE all'estrazione: `pezzo_js` di serie si ferma alla
    # prima riga VUOTA, e queste due funzioni non ne hanno — cosi' il
    # pezzo arrivava fino dentro renderOrders e le sentinelle qui
    # sotto trovavano il `#${o.id}` della RIGA anche quando quello del
    # dettaglio non c'era piu' (una sentinella che non puo' fallire:
    # l'ha detto la tortura, non la rilettura). Ci si ferma alla
    # graffa di chiusura.
    num = solo_codice(pezzo_js(mini, "function numeroOrdine(o){", "\n}\n"))
    prova("...e non inventa nessuna numerazione sua", True,
          "#${o.id}" in num
          and not re.search(r"o\.(numero|codice|riferimento)", num))
    # Lo stesso numero comanda le due strade del moderatore: il campo
    # lo passa cosi' com'e' a loadOrders/openOrder, e il server filtra
    # la colonna `id`. Chi cambiasse una delle due farebbe divergere
    # cio' che si legge da cio' che si cerca.
    apri = solo_codice(pezzo_js(
        mini, "async function apriOrdinePerId(numero){", "\n}\n"))
    prova("il campo admin apre proprio quel numero", True,
          "await loadOrders(id)" in apri and "openOrder(id)" in apri)
    prova("...e il server lo cerca nella colonna id", True,
          'q += " OR o.id=?"' in pezzo("miei_ordini"))

    # --- 2) LA COPIA NON PUO' DIVENTARE MUTA ------------------------
    # Negli appunti va il NUDO «#88» e non la frase: chi copia lo
    # incolla dentro un messaggio che sta gia' scrivendo. E se la
    # copia non riesce — contesti non sicuri, permessi negati — il
    # numero deve finire nel TOAST: far credere che sia negli appunti
    # quando non c'e' e' il modo in cui questo gesto fallisce in
    # silenzio (la regola del codice di @trackbot).
    cop = solo_codice(pezzo_js(
        mini, "async function copiaNumeroOrdine(id){", "\n}\n"))
    prova("negli appunti va il numero nudo, mai la frase", True,
          "writeText(`#${id}`)" in cop and "Ordine #" not in cop)
    prova("...e se la copia non riesce il numero lo dice il toast", True,
          "catch" in cop and "${id}" in cop.split("catch")[1])

    # --- 3) IL BERSAGLIO, E LA LEZIONE DEL FIGLIO FLEX --------------
    # Il numero e' alto 18px: senza lo pseudo-elemento il bersaglio
    # sarebbe quello, e lo pseudo non occupa layout — toglierlo non
    # sposta un pixel, quindi non lo vedrebbe nessuno.
    prova("il bersaglio del tocco e' allargato", True,
          ".ordine-num::after{content:'';position:absolute;inset:-10px}"
          in mini)
    # (Il `min-width:0` della colonna — la lezione del figlio flex —
    # lo guarda la sentinella storica in prove_dettaglio_ordine, che
    # si e' TRASLOCATA sull'elemento nuovo: una riga, una guardia.)
    prova("il dettaglio lo chiede alla fabbrica, una volta sola", 1,
          mini.count("${numeroOrdine(o)}"))

    # --- 4) NELLA LISTA SI LEGGE, NON SI TOCCA ----------------------
    # La riga ha gia' il suo tocco (apri l'ordine) e la sua ✕: un
    # terzo bersaglio su una card alta 60px si sbaglia e basta — cio'
    # che AGISCE vive dentro l'ordine, dove c'e' il contesto.
    ro = solo_codice(pezzo_js(mini, "function renderOrders(){"))
    riga_sub = ro[ro.index('<div class="sub">'):]
    riga_sub = riga_sub[:riga_sub.index("</div>")]
    prova("nella riga il numero c'e'...", True,
          '<span class="mono">#${o.id}</span>' in riga_sub)
    prova("...e non si tocca", True,
          "onclick" not in riga_sub and "ordine-num" not in riga_sub)


def prove_promesse_badge():
    """LE PROMESSE DEL NEGOZIO DIVENTANO BADGE (ago 2026, decisione di
    Andrea). Le due righe di prosa grigia — lo sconto carrello e la
    spedizione gratis sopra soglia — passano a pillole su tre
    superfici: la scheda annuncio (dove la promessa entra DENTRO il
    badge della spedizione), «Altri oggetti» (sotto il bottone) e il
    carrello, dove il badge porta il CONTO VIVO e diventa verde quando
    la soglia scatta.
    Qui si guardano le righe che un riordino toglie per prime: l'ordine
    dei rami del badge (che e' la specifica), le guardie travasate, il
    verde che non deve uscire dal carrello, e le due scatole che
    tengono separate due promesse con unita' indipendenti."""
    print("\n[le promesse come badge]")
    mini = open("miniapp.html", encoding="utf-8").read()

    # ---- 1. IL BADGE DELLA SCHEDA: DUE STATI, E LA SOGLIA NON SI
    # NOMINA (ago 2026, decisione di Andrea che ROVESCIA il giro del
    # giorno prima). Tre prove hanno CAMBIATO LATO qui — chiedevano che
    # il badge portasse la promessa SCRITTA, cioe' certificavano
    # l'equivoco che questo giro toglie: «da 200 €» accanto al prezzo
    # dell'articolo si legge come una proprieta' di quell'articolo.
    # Si taglia sul `\n}` e non sulla riga vuota: le tre funzioni del
    # badge stanno attaccate senza righe bianche, quindi la finestra di
    # default le avrebbe prese tutte e le prove avrebbero guardato il
    # pezzo sbagliato senza dirlo.
    _sb = pezzo_js(mini, "function spedBadge(l){", "\n}")
    _tsb = pezzo_js(mini, "function testoSpedBadge(l){", "\n}")
    _sq = pezzo_js(mini, "function spedGratisQui(l, qta){", "\n}")
    prova("la riga di prosa del dettaglio non esiste piu'", False,
          "rigaSpedGratis" in mini)
    # LA PROVA REGINA DEL GIRO: nel badge non entra nessuna CIFRA. Non
    # basta togliere l'etichetta — a rimetterci un numero si fa in
    # fretta, ed e' precisamente il difetto.
    prova("nel badge non si nomina nessuna soglia", True,
          not any(x in _tsb for x in
                  ("cifraSoglia", "etichettaSpedGratis", "regolaSpedGratis",
                   "r.quanto", "fmt(")))
    # DUE STATI SOLI, e quello «sopra soglia» RIUSA lo stato che c'era
    # gia' (i negozi che spediscono gratis senza condizioni): uno stato
    # nuovo direbbe la stessa cosa con parole diverse.
    prova("...e gli stati sono due", 2, _tsb.count("🚚"))
    prova("...col riuso di «gratuita», non uno stato nuovo", True,
          "🚚 Spedizione <b>gratuita</b>" in _tsb
          and "🚚 Spedizione disponibile" in _tsb)
    prova("un solo «Spedizione disponibile» in tutto il file", 1,
          mini.count("🚚 Spedizione disponibile"))
    # A decidere sono DUE soli giudici: la gratuita' piena (proprieta'
    # dell'annuncio) e il verdetto sulla soglia. Un terzo «if» qui
    # dentro e' una regola che non passa da nessuno dei due.
    # ...e dall'ago 2026 la coppia vive in `spedGratisOra`, perche' la
    # vogliono in TRE (il testo, il colore del guscio, e il
    # riallineamento a ogni ± dello stepper): tre copie della stessa
    # domanda direbbero prima o poi tre cose diverse sullo stesso
    # annuncio.
    prova("i giudici della gratuita' sono due e non tre", True,
          "spedGratis(l) || spedGratisQui(l, qtaScelta)"
          in pezzo_js(mini, "const spedGratisOra =", ";\n"))
    prova("...e la coppia si scrive una volta sola", 1,
          mini.count("const spedGratisOra ="))
    prova("...e il testo del badge passa da li'", True,
          "spedGratisOra(l)" in _tsb)

    # ---- 1-bis. IL GIUDICE DEL VERDETTO, e le tre decisioni di Andrea
    prova("il verdetto ha un giudice solo", 1,
          mini.count("function spedGratisQui("))
    # 1) la cifra e' quella del SERVER: artStima (MIN fra lampo e
    # accordo) per i pezzi scelti. Col listino pieno il badge direbbe
    # «gratuita» dove il conto fa pagare la spedizione.
    prova("la cifra e' quella del server, per i pezzi scelti", True,
          "artStima(l) * Math.max(1, qta || 1)" in _sq)
    # 2) a cambio muto si tace, ed e' la risposta VERA: senza cambio il
    # server la promessa non la applica affatto (promesse_sospese)
    prova("serve il cambio a meno che siano tutti e due in sats", True,
          "r.valuta !== 'sats' || l.valuta === 'eur'" in _sq)
    prova("...e senza cambio il verdetto non si da'", True,
          "if (serveCambio && !cambioVivo) return false;" in _sq)
    # AL FILO ESATTO E' GRATIS, come il giudice del server
    # (`_sped_gratis`, e come _asta_viva e in_ferie): col «>» un
    # carrello esattamente a 200 € pagherebbe qui e non di la'
    prova("al filo esatto la spedizione e' gratis", True,
          "return ora >= r.quanto;" in _sq)
    # 3) in ferie nessun verdetto: li' non si compra, e non c'e' nessun
    # conto con cui essere d'accordo
    # e nemmeno in ASTA (ago 2026): li' il prezzo e' una puntata in
    # corso e la spedizione e' inclusa per costruzione — trovato dal
    # vivo col filtro nuovo, che pescava un'asta sopra soglia
    prova("in ferie e in asta non si da' nessun verdetto", True,
          "if (!spedisce(l) || inFerie(l) || astaE(l)) return false;"
          in _sq)
    # ...ma la gratuita' PIENA resta visibile anche in ferie: e' una
    # proprieta' dell'annuncio, non un verdetto su un acquisto
    prova("...mentre la gratuita' piena non guarda le ferie", False,
          "inFerie" in pezzo_js(mini, "const spedGratis =", ";\n"))
    # LA QUANTITA' SPOSTA L'ESITO, quindi il badge si riscrive a ogni ±
    # insieme alle cifre di Acquista — e si riscrive il CONTENUTO, o il
    # nodo sparirebbe da sotto i piedi al giro dopo
    _sq2 = pezzo_js(mini, "function setQta(d){", "\n}")
    prova("il badge si riscrive a ogni ± dello stepper", True,
          "b.innerHTML = testoSpedBadge(l);" in _sq2)
    # E COL CONTENUTO IL COLORE (ago 2026): la classe sta sul GUSCIO,
    # che non si riscrive — senza questa riga il verde resterebbe
    # acceso su un ± che riporta l'articolo sotto soglia, e non si
    # accenderebbe su un + che la scavalca. E' la trappola di questo
    # cantiere, e si vede solo muovendo lo stepper.
    prova("...e col contenuto si commuta il COLORE", True,
          "b.classList.toggle('pill-trust', spedGratisOra(l));" in _sq2)
    prova("...dallo stesso giudice del testo, mai da una copia", 2,
          _sq2.count("spedGratisOra(l)") + _tsb.count("spedGratisOra(l)"))
    prova("...e il guscio porta l'aggancio", True,
          'data-sped>' in _sb)

    # ---- 2. LE DUE ETICHETTE CORTE: un registro diverso dalla prosa,
    # ma un giudice solo per la CIFRA (cifraSoglia, provato nel blocco
    # della valuta). L'etichetta della spedizione ha DUE superfici
    # neutre — scheda e «Altri oggetti» — e quel testo dev'essere
    # letteralmente lo stesso.
    prova("l'etichetta corta della spedizione e' UNA", 1,
          mini.count("function etichettaSpedGratis("))
    # UNA superficie sola dall'ago 2026 (era due): la scheda ha smesso
    # di nominare la soglia, e la promessa COL NUMERO vive solo dove
    # parla del NEGOZIO — accanto al bottone del carrello.
    prova("...e la usa la sola «Altri oggetti»", 2,
          mini.count("etichettaSpedGratis("))
    prova("l'etichetta corta dello sconto e' UNA", 1,
          mini.count("function etichettaSconto("))
    # «NEL CARRELLO» E' MORTO in tutte e due (ago 2026, il mono
    # sconta): la parola che restringeva e' diventata la parola che
    # mente — chi compra tre copie dalla scheda sconta, e chi compra
    # UNA cosa cara sopra la soglia a valore pure. Le due etichette
    # parlano uguale, ed e' la verita' e non piu' una bugia: il
    # perimetro delle due promesse ora e' lo stesso.
    # le fette si chiudono alla graffa della funzione: fino alla riga
    # vuota inghiottirebbero i commenti-dottrina dei vicini, che
    # nominano apposta le parole vietate (la lezione della prosa lunga)
    _es = pezzo_js(mini, "function etichettaSconto(regole){", fine="\n}")
    _esg = pezzo_js(mini, "function etichettaSpedGratis(r){", fine="\n}")
    prova("lo sconto NON dice piu' «nel carrello»", 0,
          _es.count("nel carrello"))
    prova("...e nemmeno la spedizione", False, "nel carrello" in _esg)
    # «DI ARTICOLI» E' USCITO DALLE ETICHETTE (12 ago 2026, decisione
    # di Andrea): vivono solo in «Altri oggetti», che parla del
    # NEGOZIO — li' l'equivoco col prezzo dell'oggetto non esiste e
    # basta la cifra. La parola resta nelle PROSE e nella pagina Paga,
    # dove distingue la merce dal totale con la spedizione dentro.
    prova("...e nei badge del negozio basta la cifra", False,
          "di articoli" in _es or "di articoli" in _esg)

    # ---- 3. LA PROSA LUNGA sopravvive solo dove non e' diventata
    # badge: testata negozio e hint del form Vendi (piu' la
    # definizione). Se il conto sale, qualcuno ha rimesso una riga di
    # prosa sotto le pillole.
    prova("la prosa lunga della spedizione resta in due superfici", 3,
          mini.count("frasePromessaSpedGratis("))
    prova("...e quella dello sconto pure", 3,
          mini.count("frasePromessaSconto("))
    # ...e il TESTO della prosa lunga ha finalmente una sentinella (il
    # buco trovato col rovesciamento: si poteva riscrivere la frase
    # senza che nulla diventasse rosso). Dice il perimetro nuovo:
    # niente carrello, le stesse parole della gemella. La fetta si
    # chiude alla graffa della funzione — fino alla riga vuota
    # inghiottirebbe 18mila caratteri di vicini, «carrello» compreso.
    _fps = pezzo_js(mini, "function frasePromessaSconto(regole){",
                    fine="\n}")
    prova("la prosa lunga dello sconto non nomina il carrello", False,
          "carrello" in _fps)
    # ...E CON DUE GAMBE LE NOMINA TUTTE E DUE (ago 2026): qui la
    # promessa e' una REGOLA del negozio, non un verdetto su un
    # carrello — e' il posto giusto per dirle entrambe, mentre l'invito
    # e la barra mostrano la sola strada piu' vicina. La percentuale
    # una volta sola, in testa: ripeterla farebbe leggere due sconti.
    prova("la prosa lunga unisce le gambe con una «o»", True,
          "rs.map(meta).join(' o da ')" in _fps)
    prova("...e la percentuale la dice una volta sola", 1,
          _fps.count("rs[0].pct"))
    prova("...e l'etichetta corta fa lo stesso", True,
          "rs.map(meta).join(' o ')" in _es)
    prova("...e dice «da N pezzi in su» / «di articoli»", True,
          "pezzi in su" in _fps and "di articoli" in _fps)

    # ---- 4. «ALTRI OGGETTI»: TITOLO → BOTTONE → BADGE, col blocco
    # bottone+badge APPICCICATO (13 ago 2026, TERZA rigirata chiesta
    # da Andrea — il verbale la vietava «senza un meccanismo nuovo»,
    # e il meccanismo e' la fila a RIGHE PIENE: il difetto delle prime
    # due nasceva dai chip affiancati — mangiati uno alla volta sotto
    # il bottone, o gonfiati a 178px dentro il blocco. In colonna e
    # DENTRO il blocco la coppia non si spezza per costruzione, e
    # l'altezza rimisurata sta nel commento del template).
    # SI MISURA IL MARKUP e non il nome della classe: scritta col nome
    # nudo, questa sentinella non poteva fallire — il commento della
    # funzione nomina `.altri-azione` PRIMA del template, quindi
    # l'indice cadeva sul commento (l'ha detto la tortura, non la
    # rilettura).
    _ao = pezzo_js(mini, "async function sezioneAltriOggetti(l){")
    prova("il bottone viene PRIMA dei badge (terza rigirata)", True,
          _ao.index('🛒 Aggiungi al carrello</button>')
          < _ao.index('<div class="pills altri-promo fila-promesse">'))
    prova("...e i badge stanno DENTRO il blocco appiccicato", True,
          '</button>${badge ? `<div class="pills altri-promo'
          ' fila-promesse">' in _ao)
    prova("...che precede la griglia", True,
          _ao.index('<div class="altri-azione">')
          < _ao.index('<div class="grid altri-griglia">')
          and 'fila-promesse">${badge}</div>`' in _ao)
    # IL TITOLO STA SU UNA RIGA (13 ago 2026, dal campo: col gradino
    # a 13px andava a capo). MISURATO prima di scegliere, ed e' il
    # numero che ha deciso: a 320 il titolo andava a capo ANCHE agli
    # 11px di serie (250px di testo contro 246 di budget) — il
    # difetto era PREESISTENTE e il gradino l'ha solo reso evidente,
    # quindi «tornare al corpo di prima» non era una cura. La cura ha
    # due gambe: il padding laterale DOPPIO tolto (32px restituiti, e
    # il titolo si allinea a bottone e card) e la formula piu' corta
    # («questo» via). Il testo INTERO a 13px non ci sta a 320 in
    # nessun modo che non mangi il letter-spacing del maiuscoletto.
    prova("...e il titolo della sezione ha il suo gradino", True,
          'class="section-label altri-tit"' in _ao
          and ".altri-tit{font-size:13px;" in mini)
    prova("...senza il padding laterale doppio (che lo mandava a capo"
          " e lo disallineava)", True,
          ".altri-tit{font-size:13px;padding-left:0;padding-right:0}"
          in mini)
    prova("...e con la formula corta, quella che ci sta a 320", True,
          ">Altri oggetti del venditore</div>" in _ao
          and "Altri oggetti di questo venditore" not in _ao)
    # Il chip azzurro della spedizione e' morto con lo sfollamento
    # colori: la regola CSS restava orfana a far credere che vivesse.
    # Si guardano la REGOLA e l'USO e non il nome nudo, che vive ancora
    # nella lapide a commento — spiega perche' i token --ship-soft
    # restano definiti, e vale piu' della comodita' di un `in mini`.
    prova("la regola del chip .sped-badge non c'e' piu'", False,
          ".sped-badge{" in mini)
    prova("...e nessuno emette piu' quella classe", None,
          re.search(r'class="[^"]*sped-badge', mini))
    # il predicato del bottone era ripetuto a mano accanto a quello dei
    # badge: adesso che sono attaccati, due copie si sfasano al primo
    # ritocco
    prova("bottone e badge hanno UN giudice solo", 1,
          _ao.count("tuttoDigitale || inFerie(l)"))
    prova("...e nessuna fila vuota se il negozio non promette niente",
          True,
          "badge ? `<div class=\"pills altri-promo fila-promesse\">"
          in _ao)

    # ---- 4bis. L'INVITO DELLO SCONTO NELLA PAGINA PAGA (12 ago 2026,
    # chiesto da Andrea col mono che sconta): la stessa forma del
    # carrello — la pillola «Ancora N → −X%» e il verde «nel conto» —
    # ma coi numeri del SERVER (mancano_*), quindi senza la fascia
    # stretta del cambio; e a cambio muto la promessa non si applica e
    # la riga lo DICE invece di sparire.
    _ra = pezzo_js(mini, "function renderAcquisto(){", "\n}")
    _blocco_sc = _ra[_ra.index("L'INVITO DELLO SCONTO"):
                     _ra.index("L'INVITO DELLA SPEDIZIONE GRATIS")]
    prova("la pagina Paga invita allo sconto coi numeri del server",
          True, "p.mancano_pezzi" in _blocco_sc
          and "p.mancano_sats" in _blocco_sc
          and "p.mancano_eur" in _blocco_sc)
    prova("...col verde di conferma quando scatta", True,
          'pill pill-trust" data-barra="sc">✅ Sconto' in _blocco_sc)
    prova("...e a cambio muto lo dice, non sparisce", True,
          "lo sconto non si applica" in _blocco_sc)
    prova("...senza mai convertire in proprio", False,
          "eurPerSat" in _blocco_sc or "artStima" in _blocco_sc)
    prova("...e la cifra del quanto manca passa dal giudice unico",
          True, "cifraSoglia(scManca, scVal)" in _blocco_sc)
    # ...e la SPEDIZIONE parla la stessa lingua (12 ago 2026, il
    # secondo tempo): pillola «Ancora N → spedizione gratis» sotto
    # soglia, verde NUDO quando scatta — nella STESSA fila dello
    # sconto, ognuna col suo stato (sono indipendenti: una verde e
    # una no e' uno stato normale, come nel carrello).
    _blocco_sg = _ra[_ra.index("L'INVITO DELLA SPEDIZIONE GRATIS"):]
    prova("la spedizione in pagina Paga parla la lingua dello sconto",
          True, "→ <b>spedizione gratis</b>" in _blocco_sg
          and "✅ Spedizione <b>gratis</b></span>" in _blocco_sg)
    # LE PILLOLE SCATTATE SONO NUDE, OVUNQUE (13 ago 2026, deciso da
    # Andrea in due tempi: prima Paga con l'unitario scontato in
    # pagina, poi il CARRELLO col totale che mostra lo scontato): la
    # coda «nel conto» diceva di aspettare il conto perche' il totale
    # del carrello restava al lordo — adesso scende da solo, col
    # lordo barrato, e la coda direbbe di cercare altrove una cosa
    # gia' in vista. Di code non ne resta NESSUNA in tutto il client.
    prova("le pillole scattate di Paga sono nude", True,
          '>✅ Sconto <b>−${scPct}%</b></span>' in mini
          and '>✅ Spedizione <b>gratis</b></span>' in mini)
    prova("...e la coda «nel conto» e' morta anche al carrello", 0,
          mini.count("nel conto</span>"))
    prova("...nella stessa fila, righe piene", 1,
          _ra.count('`<div class="pills fila-promesse">${pillole}</div>`'))
    # L'ORDINE DELLA FILA E' UNO SOLO (12 ago 2026, decisione di
    # Andrea): 🚚 prima della 🎁, ovunque le due promesse compaiano
    # insieme — pagina Paga, «Altri oggetti», carrello, testata del
    # negozio. L'occhio impara UNA fila: una superficie che la
    # rovescia gliene fa trovare un'altra. In Paga i BLOCCHI sorgente
    # restano sconto-poi-spedizione (le prove qui sopra li affettano
    # coi marcatori): l'ordine reso lo decide la sola composizione.
    prova("la fila di Paga dice PRIMA la spedizione", True,
          "pillaSg + pillaSc" in _ra)
    # fra la fila e le vie si e' infilato il bottone che riporta al
    # carrello (ago 2026): e' la RISPOSTA all'invito, e sta sotto di
    # lui — «il badge dice la cosa, il bottone da' la strada»
    prova("...e sta SOPRA la riga della consegna", True,
          "${fila}${tornaCarrello}${vie}" in _ra)
    prova("in «Altri oggetti» la spedizione viene prima", True,
          _ao.index("sgOk ? `<span") < _ao.index("scOk.length ? `<span"))
    prova("nel carrello la scatola della spedizione sta sopra", True,
          mini.index('id="paccoSpedGratis"') < mini.index('id="paccoSconto"'))
    prova("e la testata del negozio dice lo stesso ordine", True,
          "${spedGratisNegozioRiga(v)}${scontoNegozioRiga(v)}" in mini)
    # le SOSPESE restano prosa e ognuna guarda la SUA valuta:
    # promesse_sospese e' un flag combinato, e senza il filtro una
    # spedizione in SATS si direbbe sospesa per colpa di uno sconto
    # in euro (il bug tolto con questo riordino)
    prova("le sospese sono gated sulla LORO valuta", True,
          "p.promesse_sospese && scCrit === 'valore'" in _ra
          and "p.promesse_sospese && sgVal === 'eur'" in _ra)
    # IL GATE DEL 🚚 SULLA VIA SCELTA (ago 2026, ROVESCIA il 12 ago —
    # ed e' legato al DEFAULT: allora il ritiro era il
    # preselezionato-di-fatto e la pillola serviva a far cambiare
    # idea; ora che il default e' il punto, chi sta su ritiro o
    # codice online ci e' arrivato toccando, e li' un cartello sulla
    # spedizione e' rumore. Se il default cambia ancora, questo gate
    # va riguardato). La 🎁 dello sconto invece vale su ogni via: il
    # gate NON deve comparire nel suo blocco.
    prova("la 🚚 di Paga tace sulla via che non spedisce", True,
          "&& d.via !== 'ritiro' && d.via !== 'digitale'" in _blocco_sg)
    prova("...e la 🎁 dello sconto non guarda MAI la via", False,
          "d.via" in _blocco_sc)

    # ---- 4quater. LO STEPPER DELLA PAGINA PAGA (12 ago 2026): il ±
    # rifa' il conto sul server — quella pagina E' il conto — e
    # l'anti-raffica NON e' un debounce (scartato nel carrello:
    # litiga con chi sale in fretta) ma la RIASSEGNAZIONE di acqDati:
    # l'oggetto nuovo e' il token, le risposte dei tocchi precedenti
    # muoiono sulla guardia `acqDati !== d0` che caricaPreventivo ha
    # gia'. La mutazione in place farebbe vincere l'ultima risposta
    # ad ARRIVARE invece dell'ultima CHIESTA.
    _ap2 = pezzo_js(mini, "function acqPasso(delta){", "\n}")
    prova("il ± della pagina Paga riassegna acqDati (il token)", True,
          "acqDati = {...d0, qta: n}" in _ap2)
    prova("...e non muta mai la quantita' in place", False,
          "acqDati.qta =" in _ap2)
    prova("...col clamp allo stock, come la scheda", True,
          "Math.min(stock, Math.max(1, d0.qta + delta))" in _ap2)
    prova("...e con l'accordo lo stepper non parte (quantita' pinnata)",
          True, "d0.offertaId" in _ap2)
    prova("...sincronizzando qtaScelta (un solo stato con la scheda)",
          True, "qtaScelta = n;" in _ap2)
    # setQta(0) e' il SINCRONIZZATORE della scheda (trovato dal vivo:
    # l'indietro ri-mostra la vista senza ri-renderizzarla, e lo
    # stepper di la' restava al numero vecchio): a delta ZERO riusa la
    # regia in-place di setQta senza duplicarne i selettori — ma il
    # conteggio del ± resta di acqPasso, mai di setQta(±1)
    prova("...e la scheda si sincronizza con setQta(0), mai col ±",
          True, "setQta(0);" in _ap2
          and "setQta(1)" not in _ap2 and "setQta(-1)" not in _ap2)
    prova("lo stepper in pagina passa da stepperMini con chiamate sue",
          True, "stepperMini(d.qta, 'acqPasso(-1)', 'acqPasso(1)'" in _ra)
    # IL VELO D'ATTESA E' RITARDATO: secco lampeggerebbe a ogni tocco
    # su rete viva; cosi' compare solo quando l'attesa si sente — mai
    # numeri vecchi spacciati per freschi, mai un lampeggio sul caso
    # normale. E muore a ogni render, che E' la risposta.
    prova("il velo d'attesa e' ritardato (niente lampeggi)", True,
          "setTimeout(" in _ap2 and "acq-attesa" in _ap2)
    prova("...e muore a ogni render", True,
          "clearTimeout(acqAttesaTimer);" in pezzo_js(
              mini, "function renderAcquisto(){", "\n}"))
    # L'ERRORE SU UN ± NON BUTTA LA PAGINA: si ripiega sull'ultimo
    # conto buono — la quantita' TORNA a quella del preventivo vero,
    # mai numeri nuovi su un conto vecchio — e il ramo distruttivo
    # («← Torna») resta al solo primo carico.
    _rip = pezzo_js(mini, "function acqRipiega(d0, msg){", "\n}")
    prova("l'errore su un ± ripiega sull'ultimo conto buono", True,
          "d0.preventivo.quantita" in _rip and "renderAcquisto();" in _rip)
    _cp = pezzo_js(mini, "async function caricaPreventivo(){", "\n}")
    prova("...da TUTTI E DUE i rami d'errore", 2,
          _cp.count("acqRipiega(d0,"))
    prova("un ± non azzera la via gia' scelta", True,
          "vive.some(s => s.via === d0.via)" in _cp)

    # ---- 4ter. LA PAGINA DEL CARRELLO (12 ago 2026): testata e badge
    # APPICCICATI in cima — i numeri dei badge cambiano a ogni
    # «Aggiungi» e chi scorre non deve perderseli. UN blocco solo,
    # quindi la coppia e' atomica per costruzione (la lezione di
    # «Altri oggetti»); il costo e' misurato nel commento CSS. E il
    # sottotitolo dice il PERIMETRO («articoli dello stesso
    # venditore»), non piu' il modello.
    prova("la testata del carrello e' appiccicata", True,
          ".pacco-appiccicato{position:sticky" in mini)
    # l'ancora di coda era id="view-controllapacco", la vista che dal
    # cantiere della cassa non esiste piu': adesso e' la cassa, che nel
    # file segue subito il carrello. E' una fetta, quindi se l'ancora
    # sparisce questa non diventa rossa: ESPLODE.
    _vp = mini[mini.index('id="view-pacco"'):mini.index('id="view-acquisto"')]
    prova("...e testata e badge stanno DENTRO il blocco", True,
          _vp.index('class="pacco-appiccicato"')
          < _vp.index('class="pacco-testa"')
          < _vp.index('id="paccoPromesse"')
          < _vp.index("/.pacco-appiccicato"))
    prova("...con la griglia FUORI (le card devono passarci sotto)",
          True, _vp.index("/.pacco-appiccicato")
          < _vp.index('id="paccoGrid"'))
    prova("il sottotitolo dice il perimetro, non il modello", True,
          "'articoli dello stesso venditore'" in mini)
    prova("...e la riga vecchia non e' piu' il sottotitolo", False,
          "'un venditore alla volta, spedizione unica'" in mini)

    # ---- 5. IL CARRELLO: due promesse, due scatole. Con un
    # contenitore solo la prima che tace cancellerebbe la sorella
    # (tutte e due si spengono con box.innerHTML='').
    prova("due scatole nella vista", True,
          'id="paccoSconto"' in mini and 'id="paccoSpedGratis"' in mini)
    prova("...e ognuna e' scritta da una funzione sola", (1, 1),
          (mini.count("el('paccoSconto')"),
           mini.count("el('paccoSpedGratis')")))
    _sg = pezzo_js(mini, "function aggiornaInvitoSpedGratis(tot){")
    prova("il gemello riceve il totale, non lo ricalcola", True,
          "function aggiornaInvitoSpedGratis(tot){" in mini
          and "artStima" not in _sg)
    # UN CARRELLO DI SOLI RITIRI non ha una spedizione da rendere
    # gratis: la promessa sarebbe vera e inutile insieme
    prova("...e tace su un carrello che non spedisce", True,
          "stradeSet().includes('spedizione')" in _sg)
    # ...e la guardia sta DOPO `!pezzi`: a carrello vuoto stradeSet()
    # parte da ['spedizione','ritiro'] e non filtra niente, quindi
    # messa sopra sarebbe vacuamente vera
    prova("...con la guardia delle strade DOPO quella del vuoto", True,
          _sg.index("!r || !pezzi") < _sg.index("stradeSet()"))
    # la fascia del cambio, come nel gemello: in euro senza cambio si
    # tace (il patto del ≈), in sats il confronto e' esatto
    prova("in euro senza cambio vivo tace", True,
          "!cambioVivo) { box.innerHTML = ''; return; }" in _sg)
    prova("...e in sats non chiede il cambio", True,
          "r.valuta === 'sats' ? (tot || 0)" in _sg)
    prova("...col floor, come il giudice del server", True,
          "Math.floor((tot || 0) * eurPerSat)" in _sg)
    # LE DUE PROMESSE SONO INDIPENDENTI, ed e' il motivo per cui sono
    # due funzioni: una puo' essere scattata mentre l'altra no, e una
    # soglia in euro col cambio muto non deve spegnere una promessa
    # dichiarata in sats
    _bp = pezzo_js(mini, "function aggiornaBarraPacco(){")
    prova("la barra chiama tutti e due gli inviti", True,
          "aggiornaInvitoSconto(tot);" in _bp
          and "aggiornaInvitoSpedGratis(tot);" in _bp)

    # ---- 6. IL VERDE, E DOVE VIVE (ago 2026, decisione di Andrea che
    # ROVESCIA A META' la riga di prima — «il verde vive solo nel
    # carrello»).
    # NELLA SCHEDA ADESSO C'E', ed e' un cambio di significato prima
    # che di colore: li' il verde non dice «promessa scattata» ma
    # «questa spedizione non si paga» — piu' debole e piu' utile — e
    # allinea la scheda alla pagina Paga, che quel verde ce l'ha da
    # quando il suo badge nasce dal fatto. La promessa non e' piu' una
    # REGOLA da raccontare: e' un esito su QUESTO acquisto, e la
    # quantita' lo sposta.
    # IN CARD RESTA FUORI, e la ragione e' misurata: li' il verde e'
    # gia' dello SCONTO (`--sconto`, il badge sulla foto), e due verdi
    # che dicono due cose diverse nello stesso riquadro sono peggio
    # della divergenza che si chiude — di sera sono la STESSA tinta
    # (1,17 di contrasto fra loro). Chi vorra' distinguerli parta
    # dalla palette, non da un ritocco qui.
    prova("il verde entra nella scheda, e dal giudice unico", True,
          "pill-trust" in _sb and "spedGratisOra(l)" in _sb)
    prova("...ma NON in card, dove il verde e' dello sconto", False,
          "pill-trust" in pezzo_js(mini, "function iconeCard(l){", "\n}"))
    prova("...ne' in «Altri oggetti»", False, "pill-trust" in _ao)
    _in = pezzo_js(mini, "function aggiornaInvitoSconto(tot){")
    prova("...e nel carrello lo portano tutti e due i badge scattati",
          (True, True),
          ("pill-trust" in _in, "pill-trust" in _sg))
    # ...e non e' un colore nuovo: e' l'acceso della barra (--barra-a,
    # famiglia della fiducia), lo stesso traguardo di Paga — dal 13
    # ago 2026 la scattata e' piena e accesa anche qui, vedi la
    # sentinella della base .pill.pill-trust nella suite di Paga.
    _css = mini[mini.index(".pill.pill-trust{"):]
    _css = _css[:_css.index("}")]
    prova("il verde della scattata e' l'acceso della barra", True,
          "var(--barra-a)" in _css and "var(--ink)" in _css)
    # LA CODA «NEL CONTO» E' MORTA QUI (13 ago 2026, ROVESCIA la
    # clausola d'onesta' di ieri): il totale della barra ora mostra lo
    # scontato col lordo barrato, quindi il badge scattato e' NUDO —
    # ripetere «nel conto» direbbe di cercare altrove una cosa gia'
    # in vista due dita sotto.
    # (si guarda la stringa EMESSA e non un «"nel conto" not in», che
    # inciamperebbe nel commento che racconta la morte della coda: se
    # la coda tornasse, il </span> subito dopo il % sparirebbe e
    # questa riga diventerebbe rossa da sola — piu' il conteggio
    # globale a zero, qui sopra.)
    prova("il badge scattato del carrello e' nudo", True,
          '>✅ Sconto <b>−${s.pct}%</b></span>' in _in)
    # E IL CARRELLO PARLA LA LINGUA DELLA CASSA (ago 2026, decisione di
    # Andrea col cantiere della cassa): la spedizione scattata portava
    # il 🚚 dove la gemella dello sconto porta il ✅ — due emoji per lo
    # stesso grado di fatto, nella stessa fila — e l'invito spezzava il
    # grassetto («→ spedizione <b>gratis</b>» contro il
    # «→ <b>spedizione gratis</b>» di Paga). Le due superfici divergono
    # nella forma, mai nella lingua.
    _sg2 = pezzo_js(mini, "function aggiornaInvitoSpedGratis(tot){", "\n}")
    prova("la spedizione scattata del carrello dice ✅ come lo sconto",
          True, '>✅ Spedizione <b>gratis</b></span>' in _sg2)
    prova("...e il vecchio 🚚 della scattata non c'e' piu'", False,
          '>🚚 Spedizione <b>gratis</b></span>' in _sg2)
    prova("...e l'invito porta il grassetto intero, come in Paga", True,
          "→ <b>spedizione gratis</b></span>" in _sg2)
    # ---- 6bis. LA BARRA E IL TOTALE SCONTATO DEL CARRELLO (13 ago
    # 2026, decisione di Andrea: il carrello parla la lingua di Paga
    # per intero). Il giudice dello scatto e' UNO (statoScontoPacco):
    # lo interrogano il badge e il totale, e due copie del confronto
    # divergerebbero al primo ritocco.
    # (il conteggio comprende la definizione: 2 chiamanti + 1)
    prova("il giudice dello scatto e' uno, e lo chiamano in due", 3,
          mini.count("statoScontoPacco(tot)"))
    prova("...i badge del carrello corrono la barra dei ferri comuni",
          (True, True),
          ("pill-barra" in _in and "barreCorri" in _in,
           "pill-barra" in _sg and "barreCorri" in _sg))
    # IL TOTALE DICE IL NETTO col lordo barrato, con la formula del
    # server (_sconto_pacco: floor sul netto, il sat di dubbio a chi
    # paga); il barrato compare SOLO a sconto scattato.
    prova("il totale scontato usa la formula del server (floor)", True,
          "Math.floor(tot * (100 - st.pct) / 100)" in _bp)
    prova("...col lordo barrato solo a sconto scattato", True,
          "el('paccoPieno').textContent = (st && st.scattato)"
          " ? resa(tot) : ''" in _bp)
    # E IL TAG «−X%» ACCANTO AL NETTO (secondo giro del 13 ago 2026,
    # visto da Andrea: in Paga c'era e nel carrello no — due superfici
    # che mostrano lo stesso scontato lo dicono con la stessa forma).
    # Stessa classe di Paga, mai una copia: la regola CSS resta UNA.
    prova("il tag −X% della barra compare solo a sconto scattato",
          True, "el('paccoTag').textContent = (st && st.scattato)"
          " ? `−${st.pct}%` : ''" in _bp)
    # dall'ago 2026 le superfici sono QUATTRO: l'unitario della cassa,
    # la barra del carrello, la RIGA DEL CONTO e quella del paySheet —
    # le ultime due si sono riprese la percentuale quando l'etichetta
    # e' passata a «Sconto» secco. Sempre con la stessa classe, mai un
    # verde nuovo da spiegare.
    prova("...con la classe di Paga, nelle quattro sole superfici", 4,
          mini.count('class="sconto-tag"'))
    prova("...e la regola CSS del tag resta una", 1,
          mini.count(".sconto-tag{"))
    prova("...e il barrato ha la sua riga nel markup e nel CSS",
          (True, True), ('<s class="mono" id="paccoPieno"></s>' in mini,
                         "#paccoPieno:empty{display:none}" in mini))
    # LA MISURA RESTA AL LORDO, ed e' la meta' da non rovesciare: la
    # soglia guarda gli articoli PRIMA dello sconto (la regola del
    # server), o lo sconto si spegnerebbe da solo facendo scendere il
    # totale sotto la soglia che l'ha acceso. Ai due inviti e al
    # giudice va `tot` cosi' com'e' — mai il netto.
    prova("la misura resta al LORDO: il netto non entra mai", False,
          "aggiornaInvitoSconto(netto" in mini
          or "aggiornaInvitoSpedGratis(netto" in mini
          or "statoScontoPacco(netto" in mini)


def prove_promesse_raggiungibili():
    """L'INVITO CHE NON SI PUO' ACCETTARE, E IL VERDE IN VETRINA (ago
    2026, decisione di Andrea). Due difetti opposti sulla stessa
    famiglia di badge.
    Nella pagina PAGA l'invito «Ancora 2 pezzi → −10%» compariva anche
    su un annuncio che ne ha uno solo: chiedeva una cosa che non si
    puo' fare. Adesso la pillola SOTTO soglia sparisce quando nessuna
    quantita' acquistabile arriva alla soglia — e quella SCATTATA non
    si tocca, perche' un fatto non e' un invito.
    In VETRINA il contrario: un articolo che da solo fa scattare lo
    sconto carrello non lo diceva da nessuna parte. Adesso il prezzo
    parla verde col contorno, la resa di lampo e asta.
    E «🚚 gratis» in card dice il FATTO in tutti e due i casi —
    gratuita' dichiarata o soglia raggiunta — e resta NERA: chi
    sfoglia vuole sapere se paga la spedizione, non perche'."""
    print("\n[le promesse raggiungibili, e il verde in vetrina]")
    src = open("server.py", encoding="utf-8").read()
    mini = open("miniapp.html", encoding="utf-8").read()

    # ---- 1. IL SERVER CONTA LA RAGGIUNGIBILITA' (il patto di
    # `mancano_*`: il client riceve, non calcola — e' lo stesso posto
    # dove vivrebbe un off-by-one).
    prova("le due chiavi escono dal preventivo", (1, 1),
          (src.count('"sconto_raggiungibile":'),
           src.count('"sped_gratis_raggiungibile":')))
    # ZERO GIUDICI NUOVI: la domanda «esiste una quantita' che la fa
    # scattare?» si risponde chiamando i due giudici DEL DENARO al
    # massimo acquistabile. Sono monotoni nella quantita', quindi «il
    # massimo scatta» ⟺ «qualcosa scatta» — e un terzo giudice sarebbe
    # il posto da cui un giorno la pagina direbbe una cosa e la invoice
    # un'altra.
    # (la fetta parte dal FILTRO delle gambe raggiungibili, che dall'ago
    # 2026 e' il posto dove il giudice del denaro viene interrogato —
    # una volta per gamba, al massimo acquistabile)
    _rag = src[src.index("_sc_ragg = [r for r in regole_sc"):
               src.index('"promesse_sospese":')]
    prova("...chiamando i giudici del denaro, non un terzo", (True, True),
          ("_sconto_pacco(_art_max, _eur_max," in _rag,
           "_sped_gratis(_art_max, _eur_max, sog_gratis, val_sg)" in _rag))
    # con due gambe basta che ne sia raggiungibile UNA, e la chiave lo
    # dice leggendo la lista gia' filtrata invece di rifare il conto
    prova("...e basta che ne sia raggiungibile UNA", True,
          '"sconto_raggiungibile": bool(_sc_ragg)' in src)
    # IL FILTRO VIENE PRIMA DELLA SCELTA: con due gambe, invitare verso
    # quella col progresso maggiore quando e' proprio lei a non essere
    # percorribile lascerebbe muta l'altra, piu' lontana ma possibile.
    prova("...e il filtro precede la scelta della gamba", True,
          src.index("_sc_ragg = [r for r in regole_sc")
          < src.index("_g_sc = _gamba_invito(_sc_ragg,"))
    # IL TETTO E' LO STOCK, o l'ACCORDO quando c'e': la quantita' di
    # un'offerta accettata e' ESATTA e non un tetto (la regola di
    # stepperAcquista), quindi li' il massimo e' quella.
    prova("il tetto e' lo stock", True,
          'else max(richiesti, a["quantita"])' in src)
    prova("...e l'accordo, quando c'e', lo abbassa", True,
          "_max_pezzi = (_pinnata if _pinnata > 0" in src)
    # E il massimo si misura sull'unitario EFFETTIVO (lampo e accordo
    # gia' dentro), o si prometterebbe una soglia sul listino pieno
    prova("...misurato sull'unitario effettivo", True,
          "_art_max = unitario * _max_pezzi" in src)
    prova("...e in euro con la conversione di casa", True,
          "_eur_max = _eur_interi(_art_max, cambio)" in src)
    # NEL SET NON ESCONO, ed e' dichiarato: la' la composizione puo'
    # sempre crescere di un altro articolo del negozio, quindi «non
    # raggiungibile» non si puo' affermare. Si guarda il corpo del
    # preventivo del set, non il file intero.
    _pset = src[src.index("async def _preventivo_set("):]
    _pset = _pset[:_pset.index("\ndef ") if "\ndef " in _pset else len(_pset)]
    prova("nel SET la raggiungibilita' non si afferma", False,
          "raggiungibile" in _pset)

    # ---- 2. IL CLIENT LE LEGGE FAIL-OPEN. `!== false` e non `&&`:
    # chiave assente = invito come oggi (il set, la DEMO, i server di
    # ieri). Col `&&` secco l'invito sparirebbe proprio dove non si
    # puo' concludere niente.
    _ra = pezzo_js(mini, "function renderAcquisto(){", "\n}")
    prova("l'invito dello sconto guarda la raggiungibilita'", True,
          "scManca > 0 && p.sconto_raggiungibile !== false" in _ra)
    # la 🚚 la porta SPEZZATA su due righe: si ricuce prima di cercare,
    # o questa riga diventa rossa per un a-capo invece che per una
    # guardia caduta (la lezione della sentinella dei sats, che si
    # nascondevano nella piega di una stringa)
    prova("...e quello della spedizione pure", True,
          "sgManca > 0 && p.sped_gratis_raggiungibile !== false"
          in re.sub(r"\s+", " ", _ra))
    prova("...tutti e due FAIL-OPEN, mai un && secco", (False, False),
          ("&& p.sconto_raggiungibile)" in mini,
           "&& p.sped_gratis_raggiungibile)" in mini))
    # LA PILLOLA SCATTATA NON SI TOCCA: e' un fatto, non un invito, e
    # con stock 1 sopra soglia il verde deve restare.
    # E' UN CENSIMENTO E NON UN ELENCO, e la ragione e' che la prima
    # stesura di questa riga NON POTEVA FALLIRE: guardava la riga della
    # PILLOLA, mentre una guardia di troppo si aggiunge alla riga della
    # CONDIZIONE, un rigo sopra — la tortura l'ha smascherata (0 rosse
    # su una mutazione che doveva farne una). Contare le occorrenze
    # prende tutti e due i rami del verde insieme, e prendera' da sola
    # anche la terza promessa di domani.
    # (si conta la FORMA della guardia e non la parola nuda: quella
    # vive anche nei commenti qui accanto, e una sentinella che li
    # conta certifica la prosa invece del codice)
    prova("la guardia si scrive DUE volte: i due inviti, mai i due"
          " verdi", 2, _ra.count("raggiungibile !== false"))

    # ---- 2b. E CHE COSA DICE IL RAMO CHE LA GUARDIA LASCIA PASSARE.
    # La riga qui sopra guarda DOVE sta la guardia, ed era vera anche
    # col difetto: per la 🎁 il verde e' agganciato al FATTO
    # (`sconto_sats > 0`) e sta PRIMA dell'invito, per la 🚚 arrivava da
    # un `else` NUDO che raccoglieva due casi diversi — «soglia
    # raggiunta» e «soglia non raggiungibile con questo stock» — e al
    # secondo prometteva «Spedizione gratis» dove il conto addebitava.
    # Difetto vero dal campo (ago 2026), e su OGNI annuncio del negozio
    # che da solo non arrivava alla soglia: non un caso limite, la
    # regola per quel listino.
    # LA LEZIONE, ed e' la QUINTA volta che questa classe di sentinella
    # certifica meta' disegno: una prova sulla POSIZIONE di una guardia
    # dice che la guardia c'e', mai che il ramo accanto sia onesto —
    # e un disegno vero per una promessa puo' essere falso per la sua
    # gemella. Da qui in poi va SEMPRE in coppia con una sul CONTENUTO.
    def _solo_codice(js):
        js = re.sub(r"/\*[\s\S]*?\*/", "", js)
        return "\n".join(r for r in js.split("\n")
                         if not r.strip().startswith("//"))

    _rac = _solo_codice(_ra)
    # IL VERDE DELLA 🚚 NASCE DAL FATTO, e il fatto e' un numero del
    # SERVER: la tariffa della via SCELTA. Zero vuol dire «su questo
    # acquisto non si paga», che sia per la tariffa dichiarata dal
    # venditore o perche' la soglia e' scattata — la ragione non cambia
    # il fatto (regola di Andrea, ago 2026, su tutte e tre le
    # superfici). Il ramo e' anche il PRIMO: prima si dice cos'e' vero,
    # poi eventualmente cosa manca.
    prova("il verde della 🚚 nasce dal fatto, ed e' il primo ramo", True,
          "if (sgGratisOra)" in _rac
          and _rac.index("if (sgGratisOra)")
          < _rac.index("sgManca > 0"))
    # `cambio_assente` NON E' GRATIS: su una strada spenta dal cambio
    # muto la chiave della tariffa non c'e' affatto, e un `||0` la
    # leggerebbe come uno zero — cioe' prometterebbe gratis proprio
    # dove non sappiamo quanto costa. E' la riga che si sbaglia per
    # prima, e la mutazione che la toglie e' la piu' silenziosa del
    # cantiere.
    prova("...e il fatto esclude la strada spenta dal cambio muto", True,
          "!stradaSel.cambio_assente" in re.sub(r"\s+", " ", _rac))
    prova("...e si legge sulla via SCELTA, non su una qualsiasi", True,
          "(stradaSel.spedizione_sats||0) === 0" in _rac)
    # LA SOGLIA GATEA SOLO CHI LA USA (prosa e invito), MAI IL FATTO:
    # col gate sul blocco intero un negozio che spedisce gratis senza
    # condizioni in pagina non lo diceva — buco vissuto dalla nascita
    # del blocco, e piu' largo di quello che l'ha fatto trovare.
    prova("la soglia non gatea piu' il blocco intero", False,
          "if (sgSoglia > 0 && spedisceQui" in _rac)
    prova("...e quello della 🎁 resta agganciato al fatto", True,
          "else if ((p.sconto_sats||0) > 0)" in _rac)
    # CENSIMENTO e non elenco (la lezione del titolo nudo): ogni verde
    # di renderAcquisto — anche la terza promessa che qualcuno
    # aggiungera' fra sei mesi — deve nascere da una condizione SUA. Un
    # `else` nudo davanti a una pillola `pill-trust` e' esattamente la
    # forma del difetto, e da qui la CI la vede da sola.
    _nudi = []
    for _p in re.finditer(r"pill pill-trust", _rac):
        _testa = _rac[:_p.start()]
        _i = _testa.rfind("else")
        _ramo = _testa[_i:].strip() if _i >= 0 else ""
        if _ramo.startswith("else") and not _ramo.startswith("else if"):
            _nudi.append(_rac[_p.start():_p.start() + 40])
    prova("nessun verde nasce per esclusione: mai un `else` nudo", [],
          _nudi)
    # e il censimento vede DAVVERO i due verdi: a zero pillole trovate
    # la riga qui sopra sarebbe una promozione invece di una cecita'
    # (la lezione del censimento dei titoli scappati)
    prova("...e i verdi censiti sono i due che ci sono", 2,
          _rac.count("pill pill-trust"))

    # ---- 2c. E ADESSO LA PROVA CHE RISPONDE, non che rilegge: il
    # blocco si RITAGLIA da miniapp.html e si fa GIRARE con node sui
    # casi che contano. Le sentinelle qui sopra dicono COM'E' SCRITTO
    # il ramo, mai COSA RISPONDE — e la regola di Andrea e' sul cosa
    # risponde: dove la spedizione non si paga il badge lo dice (per la
    # tariffa dichiarata come per la soglia raggiunta), dove si paga
    # davvero il badge non c'e'. Le due famiglie non si devono poter
    # confondere, e questa prova le tiene distinte anche il giorno che
    # qualcuno riscrive il blocco da capo — che e' precisamente quel
    # che una sentinella sulla forma non puo' promettere.
    import json as _json, shutil as _sh2, subprocess as _sp2
    _node = _sh2.which("node")
    if not _node:
        salta("il badge della 🚚 risponde giusto sui due casi",
              "node non installato")
    else:
        _blocco = mini[mini.index(
            "  const spedisceQui = (p.strade||[]).some("):]
        _blocco = _blocco[:_blocco.index("  /* LA FILA:")]

        def _badge(strada, soglia=0, manca=0, ragg=True, sospese=False):
            """Il blocco vero su un preventivo finto. Gli unici pezzi di
            cartone sono i due ornamenti del testo (la cifra e la
            barra), che non decidono MAI quale ramo si accende."""
            p = {"strade": [strada], "sped_gratis_eur": soglia,
                 "sped_gratis_soglia": 0, "sped_gratis_valuta": "eur",
                 "mancano_sped_eur": manca, "mancano_sped_sats": 0,
                 "sped_gratis_raggiungibile": ragg,
                 "promesse_sospese": sospese}
            js = ("const cifraSoglia=(n,v)=>`${n}`;"
                  "const barraPromessa=()=>'';let note='';"
                  "const p=" + _json.dumps(p) + ";const d={via:'casa'};"
                  "const stradaSel=(p.strade||[]).find(s=>s.via===d.via)"
                  "||null;" + _blocco +
                  "console.log(pillaSg.includes('pill-trust')?'VERDE'"
                  ":pillaSg.includes('pill-barra')?'invito'"
                  ":note?'prosa':'niente');")
            r = _sp2.run([_node, "-e", js], capture_output=True,
                         text=True, encoding="utf-8")
            return (r.stdout or r.stderr).strip()

        def _via(sats):
            return {"via": "casa", "spedizione_sats": sats,
                    "totale_sats": 30_000 + sats}

        # NON SI PAGA → il badge lo dice, per tutte e due le RAGIONI.
        # I primi due sono i buchi chiusi da questo cantiere; il terzo
        # e' la promessa che scatta, cioe' il caso di sempre.
        prova("non si paga (tariffa a zero, nessuna soglia): il badge"
              " c'e'", "VERDE", _badge(_via(0)))
        prova("non si paga (tariffa a zero, soglia lontana): il badge"
              " c'e'", "VERDE", _badge(_via(0), 50, 20, False))
        # E QUI L'INVITO SAREBBE ASSURDO: «Ancora 20 € → spedizione
        # gratis» a chi la spedizione ce l'ha gia' gratis. E' il caso
        # che tiene il FATTO davanti alla soglia — con i rami in
        # ordine inverso questa riga e' l'unica che diventa rossa.
        prova("...anche quando quella soglia sarebbe raggiungibile",
              "VERDE", _badge(_via(0), 50, 20, True))
        prova("non si paga (soglia raggiunta, il server ha azzerato)",
              "VERDE", _badge(_via(0), 50, 0))
        # SI PAGA → il badge non c'e'. E' il difetto vero dal campo, e
        # questa e' la riga che lo tiene chiuso: la prima delle tre e'
        # esattamente il caso «L'individuo sovrano».
        prova("si paga (soglia lontana, stock che non ci arriva):"
              " niente", "niente", _badge(_via(5_000), 50, 20, False))
        prova("si paga (soglia raggiungibile): l'invito, mai il verde",
              "invito", _badge(_via(5_000), 50, 20, True))
        prova("si paga (nessuna soglia): niente", "niente",
              _badge(_via(5_000)))
        # NON SI SA → mai una promessa: la strada spenta dal cambio
        # muto non porta affatto la chiave della tariffa
        prova("non si sa (strada spenta dal cambio muto): mai il verde",
              "prosa", _badge({"via": "casa", "cambio_assente": True},
                              50, 20, True, True))

    # ---- 2d. LE TRE SUPERFICI DICONO LA STESSA COSA. La regola vale
    # in card, nel dettaglio e in pagina Paga: card e dettaglio il
    # fatto lo chiedono al giudice di casa (`spedGratis`, la tariffa
    # dichiarata) piu' `spedGratisQui` per la soglia; la pagina Paga
    # ce l'ha gia' contato dal server. Tre strade per la stessa
    # domanda, e la prova qui e' che nessuna delle due di vetrina
    # perda il pezzo della TARIFFA DICHIARATA — che e' il pezzo che in
    # pagina Paga mancava.
    _ic = pezzo_js(mini, "function iconeCard(l){", "\n}")
    _tb = pezzo_js(mini, "function testoSpedBadge(l){", "\n}")
    prova("in card il fatto comprende la tariffa dichiarata", True,
          "spedGratis(l) || spedGratisQui(l, 1)" in _ic)
    prova("...e nel dettaglio pure, dal giudice che le tiene insieme",
          True, "spedGratisOra(l)" in _tb)

    # ---- 3. IL GIUDICE DEL VERDE IN CARD: il gemello di spedGratisQui,
    # e ne eredita le decisioni parola per parola.
    _sc = pezzo_js(mini, "function scontoQui(l, qta){", "\n}")
    prova("il verdetto dello sconto ha un giudice solo", 1,
          mini.count("function scontoQui("))
    # NIENTE `spedisce(l)`, ed e' la sola differenza che conta: lo
    # sconto vale su OGNI via — e' sugli articoli, non sulla strada —
    # ed e' la regola del server (il gate della via lo prende la 🚚).
    prova("...e non guarda la strada: lo sconto vale su ogni via",
          False, "spedisce(" in _sc)
    # in ferie e sull'esaurito nessun verdetto: li' non si compra
    prova("in ferie, sull'esaurito e in asta nessun verdetto", True,
          "if (inFerie(l) || esaurito(l) || astaE(l)) return false;"
          in _sc)
    # la regola arriva dal giudice unico, mai letta a mano dai campi —
    # e dall'ago 2026 le gambe possono essere due: basta che ne scatti
    # UNA, che a un pezzo puo' essere solo quella a valore
    prova("...e la regola la legge regoleSconto", True,
          "regoleSconto(l.scontoCriterio" in _sc)
    prova("...e basta che ne scatti una", True, ".some(r =>" in _sc)
    # IL CUORE DEL VERDETTO E' TRASLOCATO (ago 2026, la riga viva del
    # form Vendi): la cifra e' quella del server, a cambio muto si
    # tace, al filo esatto scatta — le stesse tre righe di sempre, in
    # una funzione sola che ora hanno in comune la vetrina (che ha un
    # annuncio in mano) e il form (che ha solo un numero che si sta
    # digitando). Due copie direbbero, prima o poi, due cose diverse
    # sullo stesso prezzo.
    _ss = pezzo_js(mini, "function scontoScatta(", "\n}")
    prova("il cuore del verdetto e' uno", 1,
          mini.count("function scontoScatta("))
    prova("...e lo chiamano la vetrina e il form", 3,
          mini.count("scontoScatta("))   # la definizione piu' i due
    prova("la cifra e' quella del server, per i pezzi scelti", True,
          "scontoScatta(r, artStima(l), l.valuta, qta)" in _sc
          and "const art = artSats * n;" in _ss)
    prova("...senza cambio il verdetto non si da'", True,
          "if (serveCambio && !cambioVivo) return false;" in _ss)
    prova("...e al filo esatto la promessa scatta", True,
          "return ora >= r.quanto;" in _ss)

    # ---- 4. IL SEGNO IN CARD: il calco di lampo e asta, e la
    # PRECEDENZA — il prezzo porta UN colore solo, e questo e' l'ultimo
    # della catena (con la lampo non convive: quel prezzo e' gia' rosso
    # e artStima applica la lampo, che puo' far SCENDERE sotto soglia).
    _ch = pezzo_js(mini, "const cardHTML = l => {", "\n};")
    prova("la card sa quando lo sconto scatta da solo", True,
          "const sconto = !esa && !ferie && !asta && !lampo"
          " && scontoQui(l, 1);" in _ch)
    prova("...e il colore e' l'ultimo della catena", True,
          "lampo?' in-lampo':sconto?' in-sconto':''" in _ch)
    # «Ne resta 1» CONVIVE: e' un badge sulla foto, questo e' il colore
    # del prezzo — due slot diversi, e `ultimo` non lo guarda.
    prova("...mentre «Ne resta 1» non si spegne per lo sconto", False,
          "!sconto && ultimoPezzo" in _ch or "sconto && ultimoPezzo" in _ch)
    # IL BADGE C'E' (ago 2026, decisione di Andrea): la forma della
    # lampo SENZA il fulmine — il fulmine vuol dire «a tempo», e
    # questo non scade. Questa prova ha CAMBIATO LATO: chiedeva che
    # il badge non esistesse, cioe' certificava la vetrina di ieri.
    prova("lo sconto ha il suo badge, e senza fulmine", (True, False),
          ('<div class="card-sconto">−${l.scontoPct}%</div>' in _ch,
           'card-sconto">⚡' in mini))
    # nello stesso angolo della lampo, che e' anche il motivo per cui
    # i due non convivono mai
    prova("...nell'angolo della lampo, con la sua forma", True,
          ".card-sconto{position:absolute;top:8px;left:8px;" in mini)
    # le due regole CSS, gemelle di quelle della lampo
    prova("la cornice e il prezzo hanno le loro due regole", (1, 1),
          (mini.count(".card.in-sconto{outline:1.5px solid"
                      " var(--trust-text);outline-offset:-1.5px}"),
           mini.count(".card.in-sconto .tag-price"
                      " .price{color:var(--sconto)}")))
    # IL TOKEN E' FISSO, come i suoi due gemelli: vive sul cartellino,
    # che e' di carta chiara nei DUE temi — uno che si schiarisce di
    # notte li' sparirebbe. Quindi si dichiara UNA volta sola e il
    # blocco scuro non lo tocca.
    prova("il token del verde e' dichiarato una volta sola", 1,
          mini.count("--sconto:"))
    _scuro = mini[mini.index('html[data-tema="scuro"]'):]
    prova("...e il tema scuro non lo tocca", False,
          "--sconto:" in _scuro[:_scuro.index("}")])
    # e nessun'altra regola colora quel prezzo. Sono QUATTRO per CINQUE
    # stati: lampo, sconto, asta, e la quarta che ferie ed esaurito si
    # dividono («e' qui, non si compra» detto per due ragioni: una
    # frase, un posto solo da tarare). Il numero e' il censimento — chi
    # ne aggiunge una lo sente, e il posto giusto per un colore nuovo
    # e' questa lista, non una regola sparsa altrove nel foglio.
    prova("i colori del prezzo in card restano quattro", 4,
          len(re.findall(r"\.tag-price[^{]*\.price\{color:", mini)))

    # ---- 5. «🚚 GRATIS» DICE IL FATTO, NON IL PERCHE' (decisione di
    # Andrea): la parola compare in tutti e due i casi — gratuita'
    # dichiarata o soglia raggiunta da un pezzo solo — e resta NERA.
    # Da qui il GIUDICE UNICO al posto del test a mano, che `spedGratis`
    # dichiara di essere da sempre «anche dell'icona in card».
    # ⚠️ E' anche una CORREZIONE: il test di prima non guardava il
    # SUPPLEMENTO per pezzo, quindi «base 0 + supplemento pieno»
    # scriveva «gratis» mentendo — su due pezzi si paga.
    _ic = pezzo_js(mini, "function iconeCard(l){", "\n}")
    prova("la parola passa dal giudice unico", True,
          "(spedGratis(l) || spedGratisQui(l, 1))" in _ic)
    prova("...e non dal test a mano che scavalcava il supplemento",
          False, "!(l.sped > 0) && !(l.spedEur > 0)" in _ic)
    # NERA: il colore resta l'inchiostro di sempre, e il verde non
    # entra qui — o le due promesse direbbero la stessa cosa due volte
    prova("...restando nera: nessun verde sulla parola", False,
          "trust" in _ic or "sconto-prezzo" in _ic)


def prove_verde_e_filtri():
    """IL PREZZO SCONTATO IN VETRINA E I DUE FILTRI (ago 2026,
    decisioni di Andrea). La card in sconto mostra il prezzo SCONTATO
    col listino barrato e un badge verde in alto a sinistra — lo stesso
    meccanismo della lampo, senza il fulmine — e lo stesso vale nella
    scheda. Nei filtri nascono «Spedizione gratis» e «In sconto», e
    «In offerta» diventa «Offerta a tempo»: con due sconti in elenco la
    parola da sola non distingueva piu' niente.
    LA REGOLA IN UNA FRASE, ed e' quella da tenere: e' il CRITERIO a
    dire dove vale lo sconto — a VALORE conta la cifra, quindi vale
    anche su un articolo solo; a PEZZI conta il numero, quindi serve
    arrivare a piu' pezzi. Nessuna eccezione da ricordare."""
    print("\n[il prezzo scontato in vetrina, e i due filtri]")
    src = open("server.py", encoding="utf-8").read()
    mini = open("miniapp.html", encoding="utf-8").read()

    # ---- 1. IL PREZZO MOSTRATO HA UN GIUDICE SOLO: lo chiamano la
    # card, la scheda e il riscrittore del toggle valuta, e tre copie
    # della precedenza divergerebbero al primo ritocco.
    _pm = pezzo_js(mini, "function prezzoMostrato(l){", "\n}")
    prova("il prezzo mostrato ha un giudice solo", 1,
          mini.count("function prezzoMostrato("))
    # 5 = la definizione piu' i QUATTRO chiamanti (card, i due del
    # prezzo nella scheda, il riscrittore del toggle valuta)
    prova("...e lo chiamano card, scheda e toggle valuta", 5,
          mini.count("prezzoMostrato(l)"))
    # LA LAMPO VINCE, ed e' la regola del conto: artStima applica la
    # lampo e lo sconto misura QUEL prezzo.
    prova("la lampo vince sullo sconto", True,
          "if (lampoAttiva(l)) return conLampo(l);" in _pm)
    prova("...e lo sconto viene dopo, a quantita' 1", True,
          "return scontoQui(l, 1) ? conSconto(l) : l;" in _pm)
    # la ricetta e' quella del server (_sconto_pacco: netto col FLOOR,
    # mai sotto 1 sat) ed e' identica a conLampo.
    # LA SENTINELLA HA CAMBIATO LATO (ago 2026, la riga viva del form
    # Vendi): cercava la STESSA riga di aritmetica nei due corpi —
    # cioe' certificava che due copie fossero in pari. Adesso la copia
    # e' UNA (scontaSats/scontaEur, che serve anche il form, dove
    # sarebbe stata la terza) e la sentinella chiede l'opposto: che
    # nei due corpi l'aritmetica non ci sia PIU'. Il verso e' piu'
    # forte — quella di prima passava anche con due copie sbagliate
    # nello stesso modo.
    _cs = pezzo_js(mini, "function conSconto(l){", "\n}")
    _cl = pezzo_js(mini, "function conLampo(l){", "\n}")
    prova("il netto scontato ha un posto solo, per unita'", (1, 1),
          (mini.count("function scontaSats("),
           mini.count("function scontaEur(")))
    for _n, _c in (("conSconto", _cs), ("conLampo", _cl)):
        prova(f"...e {_n} non se lo calcola per conto suo", (True, False),
              ("scontaSats(" in _c, "Math.floor(" in _c))
    # i due arrotondamenti restano DIVERSI: i sats interi col floor e
    # mai sotto 1, l'euro coi centesimi. Scambiarli e' il modo silenzioso
    # di sbagliare, e i nomi dicono l'unita' apposta (la lezione di
    # `nome_pezzo`).
    _sa = pezzo_js(mini, "function scontaSats(", "\n}")
    _se = pezzo_js(mini, "function scontaEur(", "\n}")
    prova("i sats: interi col floor, mai sotto 1", True,
          "Math.max(1, Math.floor(" in _sa)
    prova("l'euro: centesimi, mai sotto un centesimo", True,
          "Math.max(0.01, Math.round(" in _se)
    # la percentuale la legge il GIUDICE, mai il campo nudo: un pct
    # senza soglia non e' una regola. Con due gambe basta la PRIMA:
    # la percentuale e' una sola per negozio, e sommarle o sceglierne
    # una piu' grande vorrebbe dire due sconti dove ce n'e' uno.
    prova("...e la regola la legge regoleSconto", True,
          "regoleSconto(l.scontoCriterio" in _cs)
    prova("...e sconta con la percentuale della prima gamba", True,
          "rs[0].pct" in _cs)

    # ---- 2. IL SEGNO IN CARD: badge nell'angolo della lampo e listino
    # barrato. I due badge non convivono MAI — stesso angolo.
    _ch = pezzo_js(mini, "const cardHTML = l => {", "\n};")
    prova("il barrato compare per la lampo E per lo sconto", True,
          "${(lampo||sconto)?" in _ch)
    prova("il prezzo della card viene dal giudice", True,
          ": prezzoMostrato(l));" in _ch)
    # «Ne resta 1» si spegne anche per lo sconto: da quando il verde ha
    # un badge, i due vorrebbero lo stesso angolo
    prova("«Ne resta 1» si spegne per lo sconto", True,
          "const ultimo = !esa && !ferie && !asta && !lampo && !sconto"
          in _ch)
    # ...e lo sconto si spegne per la lampo, non il contrario
    prova("...e lo sconto si spegne per la lampo", True,
          "const sconto = !esa && !ferie && !asta && !lampo"
          " && scontoQui(l, 1);" in _ch)

    # ---- 3. LA SCHEDA dice la stessa cosa: prezzo dal giudice, chip
    # verde e NIENTE countdown (questo non scade).
    prova("la scheda colora il numero grande", True,
          "lampoAttiva(l)?' lampo':scontoQui(l,1)?' sconto':''" in mini)
    prova("...con l'inchiostro dei due temi, non col token fisso", True,
          ".detail-price.sconto{color:var(--trust-text)}" in mini)
    # solo il MARKUP, non la regola CSS che porta gli stessi due nomi
    _riga = [r for r in mini.split("\n") if "sconto-badge" in r
             and '<div class="lampo-was">' in r]
    prova("la riga «prezzo di prima» esiste anche per lo sconto",
          1, len(_riga))
    prova("...senza countdown: questo non scade", False,
          "lampo-resta" in (_riga[0] if _riga else "lampo-resta"))
    prova("...e il chip riusa la forma, cambiando il solo fondo", True,
          ".lampo-was .lampo-badge.sconto-badge{background:var(--sconto)}"
          in mini)

    # ---- 4. I DUE FILTRI, SERVER. L'aritmetica sta in UN posto solo:
    # chi la copia fa mentire il filtro (la invoice non passa di qui).
    prova("l'aritmetica dei filtri e' in un posto solo", (1, 1),
          (src.count("def _sql_articolo_sats("),
           src.count("def _sql_soglia_negozio(")))
    # SUBQUERY e non JOIN: la query del TOTALE di /api/listings non ha
    # il JOIN su `utenti`, e un `u.` la farebbe esplodere
    _sq = pezzo("_sql_soglia_negozio")
    prova("la soglia si chiede in una EXISTS, mai con un JOIN", True,
          "EXISTS (SELECT 1 FROM utenti us" in _sq)
    prova("...e in ferie nessun verdetto, come nel client", True,
          "us.ferie_fino<=?" in _sq)
    # a cambio muto il ramo in euro non si scrive proprio
    prova("a cambio muto la soglia in euro non scatta", True,
          "if cambio > 0:" in _sq)
    _wo0, _wsg0 = pezzo("_where_occasioni"), pezzo("_where_sped_gratis")
    _lista = src[src.index("async def lista_annunci("):
                 src.index("async def pubblica(")]
    # NIENTE LAMPO VIVA nei due filtri: il suo badge occupa lo stesso
    # angolo, quindi quel segno la card non ce l'ha
    # si guarda il CONTENUTO e non il nome: contare `_no_lampo`
    # sopravvive a un `_no_lampo = ""`, cioe' proprio alla mutazione
    # che questa riga esiste per prendere (l'ha detto la tortura).
    prova("il ramo dello sconto salta le lampo vive", (True, 1),
          ("NOT (a.lampo_percento>0" in _wo0
           and 'AND a.lampo_scadenza>?) AND' in _wo0,
           _wo0.count("NOT (a.lampo_percento>0")))
    # NIENTE ASTE nei rami che misurano una SOGLIA: li' il prezzo e'
    # una puntata in corso. Due volte — lo sconto e il ramo soglia
    # della spedizione — mentre la gratuita' DICHIARATA resta vera
    # anche su un'asta (trovato dal vivo col filtro nuovo).
    prova("i rami della soglia saltano le aste", (1, 1),
          (_wo0.count("a.asta_base_sats=0"),
           _wsg0.count("a.asta_base_sats=0")))
    # LE LEVE: a sconto spento nessun annuncio ha il badge, quindi il
    # filtro non deve dare niente — mai una vetrina senza il segno che
    # la spunta prometteva. La spedizione gratis DICHIARATA invece non
    # dipende da nessuna promessa e resta.
    prova("a leva spenta il filtro sconto non da' niente", True,
          'rami.append("0")' in _wo0)
    prova("...mentre la gratuita' dichiarata resta anche a leva spenta",
          True, "a.spedizione_extra_eur=0)" in _wsg0)

    # ---- 5. LA PROVA CHE CONTA: il predicato SQL e il giudice Python
    # devono dire la STESSA cosa. Il predicato gira su un database
    # gemello, il giudice sugli stessi numeri: se un giorno divergono,
    # questa riga lo dice — ed e' l'unico modo di accorgersene, perche'
    # un filtro che sbaglia non fallisce: mostra la card sbagliata.
    import sqlite3
    amb = {}
    exec(pezzo("_eur_interi"), amb)
    exec(pezzo("_sped_gratis"), amb)
    exec(pezzo("_sql_articolo_sats"), amb)
    exec(pezzo("_sql_soglia_negozio"), amb)
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE annunci(id INTEGER PRIMARY KEY, "
                "venditore_id INT, prezzo_sats INT, prezzo_eur REAL, "
                "valuta TEXT, lampo_percento INT DEFAULT 0, "
                "lampo_scadenza INT DEFAULT 0)")
    con.execute("CREATE TABLE utenti(tg_id INT, ferie_fino INT, "
                "sped_gratis_soglia INT, sped_gratis_soglia_eur INT, "
                "sped_gratis_valuta TEXT)")
    CAMBIO = 55_000.0
    NEG = {1: (0, 40_000, 0, "sats"), 2: (0, 0, 25, "eur"),
           3: (9_999_999_999, 40_000, 0, "sats")}   # il terzo e' in ferie
    con.executemany("INSERT INTO utenti VALUES(?,?,?,?,?)",
                    [(k,) + v for k, v in NEG.items()])
    righe = [(10, 1, 39_999, 0.0, "sats"), (11, 1, 40_000, 0.0, "sats"),
             (12, 1, 90_000, 0.0, "sats"), (13, 2, 40_000, 0.0, "sats"),
             (14, 2, 50_000, 0.0, "sats"),
             (15, 2, 0, 25.0, "eur"), (16, 2, 0, 24.99, "eur"),
             (17, 3, 90_000, 0.0, "sats")]
    con.executemany("INSERT INTO annunci(id,venditore_id,prezzo_sats,"
                    "prezzo_eur,valuta) VALUES(?,?,?,?,?)", righe)
    sql, par = amb["_sql_soglia_negozio"](
        "sped_gratis_soglia", "sped_gratis_soglia_eur",
        "sped_gratis_valuta", CAMBIO, 1_000_000)
    da_sql = {r["id"] for r in con.execute(
        "SELECT a.id FROM annunci a WHERE" + sql, par)}
    # ...e adesso la stessa domanda in Python, coi giudici veri
    da_py = set()
    for (aid, vend, psats, peur, val) in righe:
        u = NEG[vend]
        if u[0] > 0:            # in ferie: nessun verdetto
            continue
        art = (round(peur * 100_000_000 / CAMBIO)
               if val == "eur" and peur > 0 else psats)
        sog = u[1] if u[3] == "sats" else u[2]
        if amb["_sped_gratis"](art, amb["_eur_interi"](art, CAMBIO),
                               sog, u[3]):
            da_py.add(aid)
    prova("il filtro SQL e il giudice Python dicono la stessa cosa",
          da_py, da_sql)
    prova("...e non e' una tautologia: qualcosa scatta e qualcosa no",
          True, 0 < len(da_sql) < len(righe))
    # al filo esatto scatta, come _sped_gratis e in_ferie
    prova("al filo esatto la soglia e' raggiunta", (True, False),
          (11 in da_sql, 10 in da_sql))
    prova("...e il negozio in ferie non da' nessun verdetto", False,
          17 in da_sql)
    con.close()

    # ---- 6. I DUE FILTRI, CLIENT: params, stato, azzera e DEMO.
    prova("i due filtri viaggiano al server", (True, True),
          ("p.set('solo_sped_gratis', '1')" in mini,
           "p.set('solo_sconto', '1')" in mini))
    for _n, _v in (("SpedGratis", "filtroSpedGratis"),
                   ("Sconto", "filtroSconto")):
        prova("il filtro " + _n + " si accende e si azzera",
              (True, True),
              (_v + " = !!el('filtro" + _n + "Inp').checked;" in mini,
               "el('filtro" + _n + "Inp').checked = false;" in mini))
    prova("...e i due entrano in filtriVivi", True,
          "|| filtroDig || filtroLampo || filtroAsta || filtroSpedGratis"
          in mini)
    # in DEMO rispondono coi GIUDICI del client, gli stessi che
    # disegnano la parola e il badge: demo e vetrina non divergono
    _rg = pezzo_js(mini, "function renderGrid(", "\n}")
    # in DEMO le occasioni si uniscono come sul server, e la
    # spedizione gratis resta un filtro a se'
    prova("in DEMO filtrano coi giudici che disegnano", (True, True),
          ("data.filter(l => spedGratis(l) || spedGratisQui(l, 1))" in _rg,
           "(filtroSconto && scontoQui(l, 1))" in _rg))
    prova("...e in DEMO le occasioni si uniscono come sul server", True,
          "if (filtroLampo || filtroAsta || filtroSconto)" in _rg)

    # ---- 8. LE COMBINAZIONI, TUTTE (ago 2026, bug dal campo: due
    # spunte insieme e la vetrina restava vuota). UN FILTRO SOLO CHE
    # FUNZIONA NON GARANTISCE CHE DUE INSIEME FUNZIONINO, ed e'
    # letteralmente quello che era successo: le prove di ieri
    # guardavano un filtro alla volta e passavano tutte.
    # La causa non era aritmetica ma STRUTTURALE — lampo, asta e sconto
    # sono stati MUTUAMENTE ESCLUSIVI (la precedenza dei badge), quindi
    # in AND l'intersezione e' vuota PER DEFINIZIONE. Qui si girano le
    # 16 combinazioni dei quattro filtri sul database gemello, con le
    # funzioni VERE che compongono la WHERE.
    amb2 = {}
    exec(pezzo("_eur_interi"), amb2)
    exec(pezzo("_sql_articolo_sats"), amb2)
    exec(pezzo("_sql_soglia_negozio"), amb2)
    amb2["SCONTO_PACCO_ATTIVO"] = True
    amb2["SPED_GRATIS_ATTIVO"] = True
    exec(pezzo("_where_occasioni"), amb2)
    exec(pezzo("_where_sped_gratis"), amb2)
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE annunci(id INTEGER PRIMARY KEY, "
                "venditore_id INT, prezzo_sats INT, prezzo_eur REAL, "
                "valuta TEXT, consegna TEXT, spedizione_sats INT, "
                "spedizione_eur REAL, spedizione_extra_sats INT, "
                "spedizione_extra_eur REAL, lampo_percento INT, "
                "lampo_scadenza INT, asta_base_sats INT, asta_scadenza INT)")
    con.execute("CREATE TABLE utenti(tg_id INT, ferie_fino INT, "
                "sped_gratis_soglia INT, sped_gratis_soglia_eur INT, "
                "sped_gratis_valuta TEXT, sconto_pacco_percento INT, "
                "sconto_pacco_criterio TEXT, sconto_pacco_valore INT, "
                "sconto_pacco_valore_eur INT, "
                "sconto_pacco_valore_valuta TEXT)")
    ORA = 1_000_000
    con.execute("INSERT INTO utenti VALUES(1,0,45000,0,'sats',"
                "15,'valore',45000,0,'sats')")
    # (id, prezzo, sped, lampo%, asta_base) e cosa DEVE avere ognuno:
    # e' l'atteso scritto a mano, non una seconda copia della regola
    CASI = [
        # id, prezzo, sped, lampo, asta,  lampo? asta? sconto? gratis?
        (1, 10_000, 1500, 0, 0,           False, False, False, False),
        (2, 60_000, 1500, 0, 0,           False, False, True,  True),
        (3,  8_000,    0, 0, 0,           False, False, False, True),
        # la lampo lo porta a 80.000: sopra soglia spedizione, ma il
        # badge verde non ce l'ha (il rosso vince) — e' il caso del
        # SECONDO difetto, quello che il filtro saltava
        (4, 100_000, 1500, 20, 0,         True,  False, False, True),
        # lampo che scende SOTTO tutte e due le soglie
        (5, 50_000, 1500, 20, 0,          True,  False, False, False),
        # un'asta: niente sconto e niente soglia spedizione, mai
        (6, 90_000, 1500, 0, 90_000,      False, True,  False, False),
    ]
    for (i, p, sp, lp, ab, *_r) in CASI:
        con.execute("INSERT INTO annunci VALUES(?,1,?,0,'sats',"
                    "'spedizione',?,0,0,0,?,?,?,?)",
                    (i, p, sp, lp, ORA + 999 if lp else 0, ab,
                     ORA + 999 if ab else 0))
    ATT = {c[0]: {"lampo": c[5], "asta": c[6], "sconto": c[7],
                  "gratis": c[8]} for c in CASI}

    def _chiedi(fl, fa, fs, fg):
        sql, par = amb2["_where_occasioni"](fl, fa, fs, 55_000.0, ORA)
        dove, p = "1=1" + sql, list(par)
        if fg:
            s2, p2 = amb2["_where_sped_gratis"](55_000.0, ORA)
            dove += s2
            p += p2
        return {r["id"] for r in con.execute(
            "SELECT a.id FROM annunci a WHERE " + dove, p)}

    guai = []
    for fl in (0, 1):
        for fa in (0, 1):
            for fs in (0, 1):
                for fg in (0, 1):
                    occ = [n for n, v in (("lampo", fl), ("asta", fa),
                                          ("sconto", fs)) if v]
                    att = {i for i, d in ATT.items()
                           if (not occ or any(d[n] for n in occ))
                           and (not fg or d["gratis"])}
                    avuto = _chiedi(fl, fa, fs, fg)
                    if avuto != att:
                        guai.append((fl, fa, fs, fg, sorted(att),
                                     sorted(avuto)))
    prova("le 16 combinazioni dei filtri dicono tutte il vero", [], guai)
    # LA PROVA REGINA DEL GIRO: le coppie che davano il VUOTO. Se
    # qualcuno rimette l'AND fra le occasioni, queste tre righe cadono
    # insieme — ed e' l'unico modo di accorgersene, perche' una vetrina
    # vuota non e' un errore: e' una vetrina vuota.
    prova("lampo + sconto non e' piu' il vuoto", {2, 4, 5},
          _chiedi(1, 0, 1, 0))
    prova("asta + sconto non e' piu' il vuoto", {2, 6}, _chiedi(0, 1, 1, 0))
    prova("lampo + asta non e' piu' il vuoto", {4, 5, 6},
          _chiedi(1, 1, 0, 0))
    # ...e la spedizione gratis resta un'INTERSEZIONE, non si unisce:
    # e' un asse ortogonale, e chi la spunta vuole l'incrocio
    prova("la spedizione gratis incrocia, non unisce", {2},
          _chiedi(0, 0, 1, 1))
    # IL SECONDO DIFETTO, che si vedeva solo riproducendo: una lampo il
    # cui prezzo SCONTATO supera la soglia ha la parola «gratis» sulla
    # card, e il filtro la saltava perche' escludeva le lampo.
    prova("la lampo sopra soglia e' spedizione gratis", True,
          4 in _chiedi(0, 0, 0, 1))
    prova("...e quella che scende sotto, no", False,
          5 in _chiedi(0, 0, 0, 1))
    # ...E UN NEGOZIO CON TUTTI E DUE I CRITERI (ago 2026): la gamba a
    # valore ce l'ha, quindi sulle sue card il badge verde c'e' e il
    # filtro DEVE pescarle. Dimenticare 'entrambi' nella WHERE vorrebbe
    # dire una spunta che nasconde annunci su cui il segno e' acceso —
    # il difetto piu' brutto di un filtro, perche' non fallisce: mostra
    # la vetrina sbagliata. (Si semina in fondo, o cambierebbe gli
    # insiemi attesi delle prove qui sopra.)
    con.execute("INSERT INTO utenti VALUES(2,0,0,0,'eur',"
                "15,'entrambi',45000,0,'sats')")
    con.execute("INSERT INTO annunci VALUES(7,2,60000,0,'sats',"
                "'spedizione',1500,0,0,0,0,0,0,0)")
    prova("il filtro pesca anche chi ha TUTTI E DUE i criteri", True,
          7 in _chiedi(0, 0, 1, 0))
    con.close()
    # LA STRUTTURA, perche' il giorno che qualcuno rimette l'AND lo
    # dica anche una sentinella e non solo i numeri qui sopra
    _wo = pezzo("_where_occasioni")
    prova("le occasioni si uniscono in OR", True,
          ' OR ".join(rami)' in _wo)
    prova("...e la spedizione gratis non e' fra loro", False,
          "sped_gratis" in _wo)
    # e l'ORDINAMENTO resta un vincolo DURO: il keyset pagina su quella
    # colonna, e un annuncio senza scadenza in mezzo romperebbe la
    # paginazione, non solo la vista
    prova("l'ordinamento resta in AND, fuori dall'unione", True,
          'if ordina in ("lampo", "asta"):' in _lista)

    # ---- 9. L'ORDINA TORNA A TRE VOCI (ago 2026, decisione di Andrea).
    # «Offerta a tempo» e «All'asta» erano ordinamenti VERI — per
    # scadenza crescente, chi finisce prima in testa — ma implicavano
    # il filtro, che c'e' gia' fra le spunte: la stessa cosa si faceva
    # in due posti. Il criterio pero' NON si perde, e non doveva:
    # spuntata UNA SOLA occasione, la vetrina lo eredita.
    _voci = re.findall(r'<option value="([^"]*)">([^<]*)</option>',
                       mini[mini.index('id="ordinaSel"'):
                            mini.index("</select>",
                                       mini.index('id="ordinaSel"'))])
    prova("l'Ordina della vetrina ha TRE voci", 3, len(_voci))
    prova("...e sono queste", ["", "prezzo_su", "prezzo_giu"],
          [v for v, _ in _voci])
    # IL GIUDICE UNICO dell'ordine effettivo: lo chiedono il parametro
    # al server, il campo-bottone e il ramo DEMO — tre copie della
    # regola divergerebbero al primo ritocco.
    _oe = pezzo_js(mini, "function ordinaEffettivo(){", "\n}")
    prova("l'ordine effettivo ha un giudice solo", 1,
          mini.count("function ordinaEffettivo("))
    # 4 = la definizione piu' i TRE chiamanti (parametro al server,
    # campo-bottone, ramo DEMO)
    prova("...e lo chiedono in tre", 4, mini.count("ordinaEffettivo()"))
    # LA SCELTA ESPLICITA VINCE: l'eredita' vale solo sul default
    prova("la scelta esplicita vince sull'eredita'", True,
          "if (ordinaVista) return ordinaVista;" in _oe)
    # UNA SOLA occasione eredita: con due spunte non esiste una
    # scadenza sola da guardare, e l'ordine di sempre e' l'unica
    # risposta onesta
    prova("eredita solo con UNA occasione spuntata", (True, True),
          ("if (filtroLampo && !filtroAsta) return 'lampo';" in _oe,
           "if (filtroAsta && !filtroLampo) return 'asta';" in _oe))
    # IL CAMPO NON MENTE: mostra l'ordine EFFETTIVO e non il valore del
    # select — che con un'occasione spuntata direbbe «Piu' recenti» su
    # una vetrina in scadenza (la regola del pannello Filtri, dove la
    # regione resta in elenco anche a zero annunci)
    _cmp = mini[mini.index("  ordinaSel: {titolo:"):
                mini.index("poi: v => setOrdina(v)}")]
    prova("il campo dice l'ordine effettivo", True,
          "const e = ordinaEffettivo();" in _cmp)
    prova("...con le etichette dell'ordine ereditato", True,
          "ETICHETTE_ORDINE[e]" in _cmp)
    prova("...che non sono voci del menu", 0,
          sum(1 for v, _ in _voci if v in ("lampo", "asta")))
    # LA RADICE ASTE tiene l'ordine per scadenza (decisione di Andrea:
    # e' una gara, e li' il tempo E' il criterio) ma non lo imposta
    # piu' a mano: lo eredita dalla sua spunta, e cosi' il campo dice
    # la verita' senza un ramo apposta.
    _va = pezzo_js(mini, "function vaiAste(){", "\n}")
    prova("la radice Aste accende la spunta", True,
          "filtroAsta = true;" in _va)
    prova("...e NON imposta piu' l'ordinamento a mano", False,
          "ordinaVista = 'asta'" in mini)
    # e uscendo non c'e' piu' niente da spegnere: l'ordine era
    # ereditato dalla spunta, che vaiEsplora toglie
    # 2 = la DICHIARAZIONE piu' la radice Aste, che azzera la scelta
    # esplicita per poter EREDITARE l'ordine per scadenza (nel
    # giudice la scelta vince sempre, e una rimasta in memoria
    # terrebbe la pagina delle aste fuori dal suo ordine).
    # vaiEsplora invece non spegne piu' niente: l'ordine era
    # ereditato dalla spunta, che lui toglie.
    prova("...e l'unico che lo azzera e' la radice Aste",
          (2, True), (mini.count("ordinaVista = '';"),
                      "ordinaVista = '';" in _va))
    # il DEMO ordina con lo STESSO giudice, o demo e vetrina vera
    # ordinerebbero diverso
    prova("in DEMO l'ordine viene dallo stesso giudice", True,
          "const ord = ordinaEffettivo();" in _rg)
    prova("...e il DEMO non guarda piu' ordinaVista a mano", False,
          "ordinaVista === 'lampo'" in mini)
    # IL SERVER NON CAMBIA: gli ordinamenti restano cinque, e i due per
    # scadenza sono ancora raggiungibili — adesso li chiede il client
    # quando eredita, e un client vecchio in cache continua a mandarli
    # come sempre. Toglierli avrebbe rotto lui, non noi.
    prova("il server tiene i cinque ordinamenti", (True, True),
          ('"lampo":      ("lampo_scadenza", "ASC", ">")' in src,
           '"asta":       ("asta_scadenza", "ASC", ">")' in src))

    # ---- 7. LE ETICHETTE: «In offerta» non basta piu' a distinguere.
    # La voce di Ordina non esiste piu' (ago 2026, decisione di
    # Andrea): quelli erano ordinamenti VERI — per scadenza — ma la
    # stessa cosa si faceva coi filtri, e due strade per una cosa
    # sola sono un bivio. Resta UNA sola «Offerta a tempo», la
    # spunta; l'urgenza la eredita il filtro (ordinaEffettivo).
    prova("«Offerta a tempo» e' rimasta la sola spunta", (1, False),
          (mini.count("⚡ Offerta a tempo"), "⚡ In offerta" in mini))
    prova("...e accanto ci sono le due nuove", (True, True),
          ("🚚 Spedizione gratis" in mini, "🎁 In sconto" in mini))
    # E «Spedizione gratis» sta ATTACCATA a «Spedizione» (ago 2026,
    # decisione di Andrea): sono la stessa famiglia, e un filtro
    # della spedizione in fondo all'elenco fra le occasioni si
    # cerca dove non e'. L'ordine del pannello e' contenuto, non
    # forma: se nessuno lo guarda, il prossimo riordino lo sposta.
    _pan = mini[mini.index('id="filtroSpedInp"'):
                mini.index('id="filtroAstaInp"')]
    _spunte = re.findall(r'id="filtro(\w+?)Inp"', _pan)
    prova("«Spedizione gratis» sta accanto a «Spedizione»",
          ["Sped", "SpedGratis", "Ritiro", "Dig", "Lampo", "Sconto"],
          _spunte)


def prove_guardia_is_bot():
    """LA GUARDIA is_bot DEL CAMPANELLO (ago 2026). Dal bot-to-bot
    (Bot API 10.0, maggio 2026) un altro bot puo' DAVVERO scriverci:
    la vecchia certezza «i bot non si vedono fra loro» non e' piu' del
    protocollo — e' solo questa riga di gestisci_update. Oggi la
    modalita' e' spenta su BotFather (trackbot ha detto no, scelta di
    posizionamento), ma se un domani qualcuno la riaccende — o
    Telegram cambia ancora i default, com'e' appena successo — la
    guardia torna a essere l'unica difesa attiva contro i loop e le
    righe fantasma in anagrafe.
    TRE MODI di perderla, ognuno col codice apparentemente sano: la
    guardia sparisce dalla condizione; resta ma il return trasloca tre
    righe piu' giu'; scivola sotto upsert_utente, che intanto la riga
    fantasma l'ha gia' scritta. UNA PROVA PER MODO, e le altre due
    restano verdi apposta (vacuamente, sulle liste vuote): cosi'
    quella che parla dice QUALE dei tre e' successo.
    Si guarda l'ALBERO (ast) e non il testo: una regex qui si
    romperebbe al primo riordino della condizione — la lezione delle
    sentinelle che non potevano fallire."""
    print("\n[la guardia is_bot del campanello]")
    # pezzo() cerca `def gestisci_update(` e lo trova DENTRO
    # `async def`: il testo estratto parte da «def», e senza il
    # rattoppo gli await del corpo sarebbero un SyntaxError.
    fn = ast.parse("async " + pezzo("gestisci_update")).body[0]
    guardie = [n for n in ast.walk(fn) if isinstance(n, ast.If)
               and "'is_bot'" in ast.dump(n.test)]
    # 1) LA GUARDIA C'E' — e una sola: due copie sarebbero due posti
    #    da tenere in pari, e quella dimenticata e' quella che mente.
    prova("la guardia is_bot esiste, una volta sola", 1, len(guardie))
    # 2) ...E DAL SUO if SI ESCE: il return dev'essere figlio DIRETTO
    #    della guardia, non un flag raccolto e speso tre righe piu'
    #    giu' — che lascia il codice apparentemente sano e il bot
    #    dentro.
    prova("...e il return sta nello stesso if", True,
          all(any(isinstance(s, ast.Return) for s in g.body)
              for g in guardie))
    # 3) ...E STA PRIMA DELL'ANAGRAFE: sotto upsert_utente la riga
    #    fantasma del bot si crea comunque, guardia o no.
    anagrafe = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == "upsert_utente"]
    prova("l'anagrafe del campanello e' una", 1, len(anagrafe))
    prova("...e la guardia sta prima di lei", True,
          bool(anagrafe) and all(g.lineno < anagrafe[0].lineno
                                 for g in guardie))


def prove_script_nel_workflow():
    """OGNI SCRIPT DEL REPO PASSA DAL compileall (ago 2026).

    L'elenco del workflow e' scritto A MANO, e CLAUDE.md lo dichiara
    da mesi come il punto in cui uno script nuovo si fa dimenticare —
    «ai tre nati il 3 ago 2026 e' successo». Un file fuori da
    quell'elenco non e' meno rotto: e' solo un file che nessuno
    guarda, e se ne accorge chi lo lancia mesi dopo.

    Questa riga chiude il buco: non tiene un secondo elenco (sarebbe
    lo stesso problema spostato) ma GUARDA la cartella, e chiede che
    ogni .py alla radice compaia nel comando. Chi ne aggiunge uno lo
    sente dalla CI il giorno stesso, non fra sei mesi.

    `config.py` resta fuori per costruzione: non e' tracciato, e in
    CI non esiste (la regola ferrea 1)."""
    print("\n[gli script del repo, e il compileall]")
    wf = open(".github/workflows/prove.yml", encoding="utf-8").read()
    riga = wf[wf.index("python -m compileall"):]
    riga = riga[:riga.index("\n      -")]
    nostri = sorted(f for f in os.listdir(".")
                    if f.endswith(".py") and f != "config.py")
    prova("il repo ha degli script da compilare", True, len(nostri) > 10)
    fuori = [f for f in nostri if f not in riga]
    prova("...e sono TUTTI nel compileall del workflow", [], fuori)


def prove_altri_scorrimento():
    """«ALTRI OGGETTI DEL VENDITORE» A SCORRIMENTO CONTINUO (ago 2026):
    in fondo al dettaglio si vede TUTTO il negozio, una pagina alla
    volta, invece delle sei o sette card di ieri — il vecchio
    `slice(0,8)` non ha mai morso, perche' il tetto vero era il
    `limit=7` della fetch, e la promessa delle «quattro righe piene»
    scritta nel commento non e' mai arrivata.
    QUI SI DIFENDE LA FORMA. Che scorrendo si veda tutto il negozio UNA
    VOLTA SOLA e nell'ordine giusto lo prova `collaudo_altri_oggetti.py`
    sulla rotta vera: queste prove non hanno un database e non hanno un
    endpoint, e un difetto di paginazione non fallisce da solo — non
    alza eccezioni, fa sparire delle card.
    Le righe sorvegliate, ognuna torturata rompendo il codice:
    1) la sentinella sta FUORI da #detailContent — dentro morirebbe a
       ogni apertura, che openDetail ne riscrive l'innerHTML, e si
       porterebbe via il suo osservatore;
    2) il GIRO si alza PRIMA della guardia `mio` e si controlla PRIMA
       di scrivere lo stato: e' quel che impedisce a una pagina 2 del
       venditore di ieri di appiccicarsi alla griglia di quello nuovo,
       e il controllo d'identita' sull'annuncio non basta (lo stesso
       annuncio si puo' riaprire);
    3) `caricando` si spegne solo a giro invariato, o sul ramo catch si
       scriverebbe sull'oggetto NUOVO sbloccandogli una pagina che non
       ha chiesto;
    4) catalogo si', griglia della vetrina MAI (il patto di inCatalogo);
    5) col cursore il server tace le due liste, senza togliere le
       chiavi."""
    print("\n[«Altri oggetti» a scorrimento continuo]")
    mini = open("miniapp.html", encoding="utf-8").read()

    # 1) LA SENTINELLA, e soprattutto DOVE sta
    prova("la sentinella esiste", True, 'id="altriSentinella"' in mini)
    prova("...e sta DOPO #detailContent, mai dentro", True,
          mini.index('<div id="altriSentinella"')
          > mini.index('<div id="detailContent"></div>'))
    prova("...ed e' armata dall'osservatore di casa", True,
          "osservaSentinella('altriSentinella', caricaAltriOggetti);" in mini)
    # censimento e non elenco: la quinta di domani entra nel conto da
    # sola, e chi ne toglie una lo sente
    prova("le sentinelle dello scroll infinito sono quattro", 4,
          mini.count("\nosservaSentinella('"))

    # 2) IL GIRO
    sez = pezzo_js(mini, "async function sezioneAltriOggetti(l){")
    prova("il giro si alza PRIMA della guardia `mio`", True,
          sez.index("++altriGiro") < sez.index("const mio ="))
    prova("...e lo stato di pagina riparte con lui", True,
          "altriPag = {id:l.id" in sez)
    prova("il giro si controlla PRIMA di scrivere lo stato", True,
          sez.index("if (giro !== altriGiro) return;")
          < sez.index("altriPag.cursore ="))
    prova("la prima pagina non e' piu' sette card", True,
          "?limit=${ALTRI_PAGINA}" in sez and "?limit=7" not in mini)
    prova("il tetto che non mordeva se n'e' andato", False,
          "altri.slice(0,8)" in mini)

    # 3-4) LA PAGINA DOPO
    car = pezzo_js(mini, "async function caricaAltriOggetti(){")
    prova("le tre guardie di famiglia", True,
          "if (DEMO || !altriPag.cursore || altriPag.caricando) return;"
          in car)
    prova("la guardia di giro dopo l'await", True,
          "if (giro !== altriGiro) return;" in car)
    prova("`caricando` si spegne solo a giro invariato", True,
          "if (giro === altriGiro) altriPag.caricando = false;" in car)
    prova("catalogo si'...", True, "inCatalogo(nuovi)" in car)
    prova("...griglia della vetrina MAI", [],
          [s for s in ("vetrina.push", "vetrina =", "vetrina.length",
                       "renderGrid(") if s in car])
    prova("le card si appendono, non si riscrivono", True,
          "insertAdjacentHTML('beforeend'" in car)

    # 5) IL SERVER TACE LE DUE LISTE, SENZA TOGLIERE LE CHIAVI
    neg = pezzo("negozio")
    prova("server: col cursore gli esauriti tacciono", True,
          "esauriti = [] if cursore else" in neg)
    prova("server: ...e i feedback pure", True,
          "feedback = [] if cursore else" in neg)
    prova("server: le chiavi restano comunque nella risposta", True,
          '"esauriti": esauriti' in neg and '"feedback": feedback' in neg)


def prove_sintassi_client():
    """IL PARSE DEL CLIENT (13 ago 2026, nata da un guasto VERO
    arrivato fino a main: un `*/` doppio in un commento di
    sezioneAltriOggetti ha trasformato in codice la coda del commento
    e ha ucciso l'INTERO script al parse — niente card, niente barra
    collaudo, un'app morta — mentre la CI era VERDE, perche' queste
    prove leggono miniapp.html come TESTO e non l'hanno mai fatto
    leggere a un motore JS. Duemilanovecento sentinelle sulla forma e
    nessuna sulla sintassi: questa e' quella che mancava.
    Ogni <script> inline passa da `node --check`; sw.js pure. Node
    sta sui runner di GitHub di serie e il check e' un parse puro,
    zero esecuzione — niente rete, niente DOM. Senza node in locale
    si SALTA contando (il patto di salta): in CI, con PROVE_SEVERE,
    una saltata vale una fallita, che e' giusto cosi' — questa prova
    esiste proprio per non essere sussurrata."""
    print("\n[la sintassi del client]")
    import re as _re, shutil as _sh, subprocess as _sp, tempfile as _tf
    node = _sh.which("node")
    if not node:
        salta("il client passa dal parser JS", "node non installato")
        return
    mini = open("miniapp.html", encoding="utf-8").read()
    blocchi = _re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
                          mini, _re.S)
    prova("gli <script> inline del client sono almeno due "
          "(anti-flash + app)", True, len(blocchi) >= 2)
    rotti = []
    for i, b in enumerate(blocchi):
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False,
                                    encoding="utf-8") as f:
            f.write(b); percorso = f.name
        r = _sp.run([node, "--check", percorso],
                    capture_output=True, text=True)
        if r.returncode != 0:
            rotti.append(f"blocco {i}: {(r.stderr or '').splitlines()[:2]}")
        os.unlink(percorso)
    prova("ogni <script> del client passa il parse di node", [], rotti)
    r = _sp.run([node, "--check", "sw.js"], capture_output=True, text=True)
    prova("...e sw.js pure", 0, r.returncode)
    prove_avvio_client(mini, node)
    prove_commenti_css(mini)
    prove_chiavi_doppie(mini)


def prove_avvio_client(mini=None, node=None):
    """L'AVVIO del client, non il suo parse (ago 2026, da un guasto
    VERO fatto scrivendo l'indirizzo di casa: `scriviTempi()` gira a
    top-level e chiamava una funzione che legge una `let` dichiarata
    PIU' IN BASSO — ReferenceError da temporal dead zone, lo script si
    interrompe li' e l'app resta muta: niente card, niente barra
    collaudo. Le 3400 sentinelle erano verdi e node --check pure,
    perche' LA SINTASSI ERA PERFETTA: e' l'esecuzione che moriva.

    Qui lo script si fa GIRARE per davvero, con un DOM di cartone: se
    qualcosa alza prima dell'ultima riga, la prova e' rossa. Non
    verifica che l'app funzioni — per quello ci vuole un browser — ma
    che ARRIVI IN FONDO, che e' la differenza fra un'app viva e una
    pagina bianca. `avvia()` in coda e' async: le sue promesse cadono
    nel vuoto e non fermano niente, ed e' giusto cosi' — quel che si
    prova qui e' il corpo sincrono."""
    import shutil as _sh, subprocess as _sp, tempfile as _tf, re as _re
    if mini is None:
        mini = open("miniapp.html", encoding="utf-8").read()
    if node is None:
        node = _sh.which("node")
    if not node:
        salta("il client arriva in fondo allo script", "node non installato")
        return
    blocchi = _re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
                          mini, _re.S)
    # il DOM di cartone: solo quel che il client tocca prima di
    # respirare. Non deve far FUNZIONARE niente — deve solo non
    # mentire su un'assenza (mai `undefined` dove il client si aspetta
    # un oggetto), o si fallirebbe per colpa dello stub.
    stub = """
    const noop = () => {};
    const elFinto = () => new Proxy({
      style:{setProperty:noop, removeProperty:noop,
             getPropertyValue:()=>''},
      classList:{add:noop, remove:noop, toggle:noop,
                 contains:()=>false},
      dataset:{}, children:[], value:'', textContent:'', innerHTML:'',
      appendChild:noop, removeChild:noop, remove:noop, focus:noop,
      addEventListener:noop, removeEventListener:noop, setAttribute:noop,
      getAttribute:()=>null, querySelector:()=>elFinto(),
      querySelectorAll:()=>[elFinto()],
      closest:()=>null, insertAdjacentHTML:noop, scrollIntoView:noop,
      getBoundingClientRect:()=>({top:0,left:0,width:0,height:0}),
      play:noop, click:noop, submit:noop, reset:noop, checked:false,
      files:[], options:[], selectedIndex:0, disabled:false,
    }, {get:(t,k)=> k in t ? t[k] : undefined, set:()=>true});
    globalThis.document = {
      documentElement: elFinto(), body: elFinto(), head: elFinto(),
      getElementById: () => elFinto(), querySelector: () => elFinto(),
      // UN elemento e non zero, ed e' la riga che rende la prova
      // capace di fallire: con la lista vuota ogni forEach gira a
      // vuoto e il corpo — dove vivono i ReferenceError — non viene
      // eseguito mai. La prima stesura passava anche col guasto
      // dentro, e l'ha detto la tortura.
      querySelectorAll: () => [elFinto()], createElement: () => elFinto(),
      addEventListener: noop, removeEventListener: noop,
      cookie:'', title:'', readyState:'complete', visibilityState:'visible',
      scripts:[], forms:[], activeElement:null, hidden:false,
      createTextNode: () => elFinto(), execCommand: noop,
    };
    globalThis.window = globalThis;
    globalThis.self = globalThis;
    globalThis.addEventListener = noop;
    globalThis.removeEventListener = noop;
    globalThis.dispatchEvent = noop;
    globalThis.localStorage = {getItem:()=>null, setItem:noop,
                               removeItem:noop, clear:noop, key:()=>null,
                               length:0};
    globalThis.sessionStorage = globalThis.localStorage;
    globalThis.navigator = {userAgent:'prove', language:'it-IT',
      clipboard:{writeText:()=>Promise.resolve()}, share:undefined,
      serviceWorker:{register:()=>Promise.resolve(), ready:new Promise(noop)},
      vibrate:noop, onLine:true, maxTouchPoints:0};
    globalThis.location = {href:'http://localhost/', pathname:'/',
      search:'', hash:'', origin:'http://localhost', hostname:'localhost',
      protocol:'http:', reload:noop, replace:noop, assign:noop};
    globalThis.history = {pushState:noop, replaceState:noop, back:noop,
      go:noop, state:null, length:1, scrollRestoration:'auto'};
    globalThis.matchMedia = () => ({matches:false, addEventListener:noop,
      removeEventListener:noop, addListener:noop, removeListener:noop});
    globalThis.fetch = () => new Promise(noop);   // mai risolta: zero rete
    globalThis.requestAnimationFrame = () => 0;
    globalThis.cancelAnimationFrame = noop;
    globalThis.setInterval = () => 0;             // niente timer vivi
    globalThis.clearInterval = noop;
    globalThis.setTimeout = () => 0;
    globalThis.clearTimeout = noop;
    globalThis.IntersectionObserver = class { observe(){} unobserve(){}
      disconnect(){} };
    globalThis.MutationObserver = class { observe(){} disconnect(){}
      takeRecords(){ return [] } };
    globalThis.ResizeObserver = globalThis.MutationObserver;
    globalThis.alert = noop; globalThis.confirm = () => false;
    globalThis.prompt = () => null;
    globalThis.getComputedStyle = () => new Proxy(
      {getPropertyValue:()=>'', setProperty:noop, removeProperty:noop},
      {get:(t,k)=> k in t ? t[k] : '', has:()=>true});
    globalThis.Notification = {permission:'default', requestPermission:noop};
    globalThis.scrollTo = noop; globalThis.scrollBy = noop;
    globalThis.innerWidth = 390; globalThis.innerHeight = 844;
    globalThis.visualViewport = {height:844, offsetTop:0,
      addEventListener:noop};
    globalThis.crypto = globalThis.crypto || {getRandomValues:(a)=>a,
      randomUUID:()=>'x'};
    process.on('unhandledRejection', noop);   // avvia() e' async
    """
    rotti = []
    for i, b in enumerate(blocchi):
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False,
                                    encoding="utf-8") as f:
            f.write(stub + "\n" + b + "\n;globalThis.__fine = true;")
            percorso = f.name
        r = _sp.run([node, percorso], capture_output=True, text=True,
                    timeout=90)
        if r.returncode != 0:
            prima = [x for x in (r.stderr or "").splitlines()
                     if "Error" in x or "error" in x][:2]
            rotti.append(f"blocco {i}: {prima or (r.stderr or '')[:160]}")
        os.unlink(percorso)
    prova("ogni <script> del client arriva in fondo (niente "
          "ReferenceError da temporal dead zone)", [], rotti)


def prove_commenti_css(mini=None):
    """IL GEMELLO CSS DEL PARSE (ago 2026, da un guasto vero fatto
    scrivendo il conteggio dei barattoli): un commento aperto con
    «\\*» invece di «/*» non apre niente, e il parser si mangia IN
    SILENZIO la regola che segue — quella volta si e' portato via
    anche `.nota-punto`, che esisteva da prima e non c'entrava niente.
    Nessuna prova sulla forma se ne accorge: il selettore c'e', il
    valore e' giusto, semplicemente non lo applica nessuno. Lo si vede
    solo a schermo, o da qui.
    Si contano le aperture e le chiusure: un `*/` che non chiude
    niente e' la firma esatta di quell'errore."""
    if mini is None:
        mini = open("miniapp.html", encoding="utf-8").read()
    import re as _re
    blocchi = _re.findall(r"<style[^>]*>(.*?)</style>", mini, _re.S)
    prova("il client ha il suo blocco di stile", True, len(blocchi) >= 1)
    orfani, aperti = [], 0
    for css in blocchi:
        i, dentro = 0, False
        while i < len(css) - 1:
            if not dentro and css[i:i + 2] == "/*":
                dentro = True; i += 2; continue
            if css[i:i + 2] == "*/":
                if not dentro:
                    orfani.append(css[max(0, i - 60):i + 2].splitlines()[-1])
                dentro = False; i += 2; continue
            i += 1
        if dentro:
            aperti += 1
    prova("nessun «*/» che non chiude niente (il commento aperto male "
          "si mangia la regola dopo)", [], orfani)
    prova("...e nessun commento resta aperto in fondo al foglio", 0, aperti)


def _chiavi_literal(src, apertura):
    """Le chiavi di PRIMO livello di un object literal, letto a mano
    dalla graffa che segue `apertura`. Salta stringhe (le tre specie),
    commenti e tutto cio' che sta annidato: senza, un `{a:{a:1}}` o un
    `${x?'a:':''}` dentro un template darebbero chiavi fantasma.
    Torna None se il literal non si chiude (meglio niente che una
    lista sbagliata: a dire che il file e' rotto c'e' node)."""
    i = src.find(apertura)
    if i < 0:
        return None
    i = src.find("{", i)
    if i < 0:
        return None
    chiavi, prof, j, n = [], 0, i, len(src)
    while j < n:
        c = src[j]
        if c in "\"'`":
            fine, j = c, j + 1
            while j < n and src[j] != fine:
                j += 2 if src[j] == "\\" else 1
            j += 1
            continue
        if src[j:j + 2] == "/*":
            j = src.find("*/", j) + 2 or n
            continue
        if src[j:j + 2] == "//":
            j = src.find("\n", j) + 1 or n
            continue
        if c in "{[(":
            prof += 1
            j += 1
            continue
        if c in "}])":
            prof -= 1
            if prof == 0:
                return chiavi
            j += 1
            continue
        if prof == 1:
            m = re.match(r"([A-Za-z_$][\w$]*)\s*:", src[j:])
            # solo a inizio voce: dopo `{` o dopo una virgola
            if m:
                k = j - 1
                while k >= 0 and src[k] in " \t\r\n":
                    k -= 1
                if k >= 0 and src[k] in "{,":
                    chiavi.append(m.group(1))
                    j += m.end()
                    continue
        j += 1
    return None


def prove_chiavi_doppie(mini=None):
    """DUE SIGNIFICATI, UN NOME (ago 2026, da un guasto VERO in
    produzione). `acqDati` nasceva con `tipo` scritto DUE volte:
    `tipo:'mono'` — quale acquisto e' — e, aggiunto dal cantiere del
    locker, `tipo:''` per il tipo di punto. In un object literal
    l'ULTIMA chiave vince, quindi `tipo` valeva '' e da li' lo stepper
    della pagina Paga moriva sulla sua prima guardia (`d0.tipo !==
    'mono'`) e il carrello non arrivava nemmeno alla cassa
    (`caricaPreventivo` mandava il body mono con annuncio 0).

    PERCHE' NESSUNA DELLE 3670 PROVE L'HA VISTO, ed e' la ragione per
    cui questa sta qui e non altrove: le chiavi doppie sono JS
    PERFETTAMENTE LECITO — `node --check` non fiata, e prove_avvio_client
    vede lo script arrivare in fondo, perche' arriva davvero. Non e' un
    difetto di sintassi ne' di esecuzione: e' un difetto di
    SIGNIFICATO, e a quel livello nessuno stava guardando.

    IL PERIMETRO E' DICHIARATO: si guardano i literal assegnati ad
    `acqDati`, che e' l'oggetto piu' affollato del client (sedici
    campi) e quello su cui scrivono cantieri diversi a settimane di
    distanza — cioe' il posto dove due nomi si incontrano senza
    vedersi. Un censimento di TUTTI gli object literal del file
    vorrebbe un AST vero; se un domani servira', il lettore qui sopra
    e' gia' quello giusto e cambia solo chi gli si da' in pasto."""
    if mini is None:
        mini = open("miniapp.html", encoding="utf-8").read()
    literali = [("apriAcquisto", "acqDati = {tipo:'mono'"),
                ("apriAcquistoSet", "acqDati = {tipo:'set'")]
    for nome, apertura in literali:
        chiavi = _chiavi_literal(mini, apertura)
        prova(f"il literal di acqDati in {nome} si legge",
              True, bool(chiavi) and len(chiavi) >= 10)
        doppie = sorted({k for k in (chiavi or []) if (chiavi or []).count(k) > 1})
        prova(f"...e nessuna sua chiave e' scritta due volte ({nome})",
              [], doppie)
    # il nome del tipo di punto e' quello dell'ordine (o.tipoPunto), e
    # `tipo` resta di mono/set: se tornassero a chiamarsi uguale, il
    # difetto tornerebbe identico
    for nome, apertura in literali:
        chiavi = _chiavi_literal(mini, apertura) or []
        prova(f"il tipo di punto si chiama tipoPunto, non tipo ({nome})",
              True, "tipoPunto" in chiavi and chiavi.count("tipo") == 1)
    # E `tipo` NON SI RISCRIVE MAI dopo la nascita, che e' la meta' che
    # il literal da solo non copre: `acqDati.tipo = 'locker'` a runtime
    # rimetterebbe la collisione IDENTICA — stepper morto e carrello
    # fuori strada — al primo tocco su una pillola, e nessun literal
    # sarebbe sporco. Trovato con la tortura: la mutazione che fa
    # divergere lo scrittore dal lettore passava liscia davanti a
    # tutte le altre prove.
    scritture = re.findall(r"(?:acqDati|d|d0)\.tipo\s*=(?!=)", mini)
    prova("...e `tipo` non si riscrive MAI dopo la nascita "
          "(dice quale acquisto e', non uno stato che cambia)",
          [], scritture)


def prove_pagina_dati():
    """La pagina «I tuoi dati» (ago 2026), sorella di «Il pagamento
    protetto».

    LE PROVE CHE CONTANO sono quelle sulle TRE AFFERMAZIONI SCOMODE.
    Una pagina sulla privacy si guasta in un modo solo: qualcuno
    riscrive una frase in meglio di com'e' la realta', e nessuno se ne
    accorge — non alza eccezioni, non fa cadere niente, e chi la legge
    non ha modo di sapere che e' stata addolcita. Quelle tre frasi
    dicono, nell'ordine: che se un ordine non si chiude mai l'indirizzo
    resta; che «cifrato» non protegge da noi; e che sul contenuto
    digitale il moderatore invece legge."""
    mini = open("miniapp.html", encoding="utf-8").read()
    i = mini.index('<div class="view" id="view-privacy">')
    vista = mini[i:mini.index("VISTA: VENDI", i)]

    # --- 1) le tre affermazioni scomode, per intero
    prova("dati: l'indirizzo resta se l'ordine non si chiude mai", True,
          "se l'ordine non si chiude mai, il tuo indirizzo resta lì"
          in vista)
    prova("...e la strada per farlo sparire si dice", True,
          "la strada è chiudere l'affare" in vista)
    prova("dati: «cifrato» non protegge da noi, e lo dice", True,
          "al riparo da un database rubato, non da noi" in vista
          and "il server lo può leggere" in vista)
    prova("...e dice perche' la garanzia vera e' la durata", True,
          "L'unica garanzia vera è che il dato duri poco" in vista)
    prova("dati: sul contenuto digitale il moderatore LEGGE", True,
          "codice digitale invece sì" in vista)
    prova("...e sull'indirizzo no, con la sua asimmetria intera", True,
          "Il tuo indirizzo non lo legge" in vista)

    # --- 2) nessuna durata battuta a mano: solo segnaposto
    prova("dati: i giorni dell'indirizzo vengono dal server", 2,
          vista.count("data-giorni-ind"))
    prova("dati: le tre durate nuove vengono dal server", 3,
          vista.count("data-durata="))
    prova("dati: la vita della invoice viene da TEMPI", True,
          'data-tempo="invoice"' in vista)
    # le chiavi della vista devono essere quelle che il server manda:
    # una chiave sbagliata lascia il segnaposto VUOTO, e un buco al
    # posto di un numero non lo vede nessuno finche' non apre la pagina
    chiavi = set(re.findall(r'data-durata="([a-z]+)"', vista))
    prova("dati: le chiavi combaciano con quelle della busta",
          {"sessione", "initdata", "avvisi"}, chiavi)
    for k in ("sessione", "initdata", "avvisi"):
        prova(f'dati: il server manda «{k}»', True,
              f'"{k}": ' in _SORGENTE)

    # --- 3) l'impianto della vista, sul calco della sorella
    prova("dati: la vista non e' una radice (l'indietro torna indietro)",
          True, "'privacy'" in mini and "RADICI = " in mini
          and "'privacy'" not in mini[mini.index("RADICI = "):
                                      mini.index("RADICI = ") + 200])
    prova("dati: la nav accende Esplora", True,
          "'sicurezza','privacy'" in mini.replace(" ", ""))
    prova("dati: niente pull-to-refresh (non c'e' nulla da rileggere)",
          True, "privacy" not in mini[mini.index("VISTE_PTR = "):
                                      mini.index("VISTE_PTR = ") + 120])
    prova("dati: si condivide, e non in DEMO", True,
          "condividiPrivacy" in mini and "privShare" in mini
          and "DEMO ? 'none' : ''" in mini)

    # --- 4) la porta dal cassetto dell'indirizzo: e' il momento in cui
    #        nasce il dubbio, ed e' la ragione per cui la pagina esiste
    prova("dati: dal cassetto dell'indirizzo si arriva alla voce giusta",
          True, "apriPrivacy('priv-indirizzo')" in mini)
    prova("...legata all'ultima parola, mai sola a capo", True,
          '<span class="fine-frase">l\'oggetto. <button type="button" '
          'class="scopri-link" onclick="apriPrivacy(' in mini)
    prova("dati: e le due sorelle si rimandano", True,
          'onclick="apriPrivacy()">🔐 E i tuoi dati?' in mini)

    # --- 5) il cantiere dichiarato: le tre cose che mancano
    #
    # ⚠️ IL TESTO SI RICUCE PRIMA DI CERCARLO. renderPrivacy lo compone
    # concatenando letterali, quindi «non si » e «può ancora» stanno in
    # due stringhe diverse e una ricerca ingenua non trova la frase —
    # ci si e' inciampati scrivendo questa prova, ed e' la stessa
    # trappola gia' pagata col censimento dei sats. Si tolgono le
    # cuciture (' + ') e le barre di escape, poi si cerca.
    j = mini.index("function renderPrivacy")
    corpo = mini[j:mini.index("\n}", j)]
    cucito = re.sub(r"'\s*\+\s*'", "", corpo).replace("\\'", "'")
    prova("dati: il documento dichiara di essere in costruzione", True,
          "Questo documento è in costruzione" in cucito)
    prova("...il titolare e il recapito mancano, e si dice", True,
          "titolare del trattamento" in cucito
          and "recapito formale" in cucito)
    prova("...e che l'account non si cancella con un bottone", True,
          "cancellare l'account non si può ancora fare con un bottone"
          in cucito)
    # il contatto e' quello che ESISTE GIA' (il canale del rodaggio):
    # senza canale nel config resta la RIGA, che dice comunque la cosa
    # vera, mai un bottone che non porta da nessuna parte
    prova("dati: il contatto ripiega sulla riga senza canale", True,
          "bannerTest?.link" in corpo
          and "scrivi ai moderatori" in cucito)


def prove_font():
    """I font serviti da casa (ago 2026). Il cantiere ha tolto l'ultima
    terza parte dal foglio: finche' la pagina li chiedeva a
    fonts.googleapis.com, l'IP e lo user-agent di OGNI visitatore
    arrivavano a Google a ogni apertura — e la pagina «I tuoi dati»
    avrebbe dovuto dichiararlo.

    LA PROVA CHE CONTA e' quella dei PESI. La resa non doveva cambiare
    di un pixel, e a garantirlo e' che i pesi dichiarati siano ESATTI:
    ne' uno di piu' ne' uno di meno. Sono font VARIABILI, quindi un peso
    aggiunto non e' innocuo — cambia le regole che oggi ricadono su un
    altro (`.sicu p{font-weight:500}` rende 400 solo perche' il 500 non
    e' dichiarato)."""
    mini = open("miniapp.html", encoding="utf-8").read()
    swjs = open("sw.js", encoding="utf-8").read()

    # 1) i sei file ci sono, e sono woff2 veri (la firma, non il nome)
    FILE = ("baloo2-latin", "baloo2-latin-ext", "nunito-latin",
            "nunito-latin-ext", "jetbrains-mono-latin",
            "jetbrains-mono-latin-ext")
    for nome in FILE:
        p = os.path.join("vendor", "font", nome + ".woff2")
        prova(f"font: {nome}.woff2 c'e' ed e' un woff2 vero", True,
              os.path.exists(p) and open(p, "rb").read(4) == b"wOF2")
    # l'OFL vuole che la licenza viaggi coi file, o non possiamo
    # ridistribuirli
    prova("font: la licenza OFL viaggia coi file", True,
          os.path.exists("vendor/font/OFL.txt")
          and os.path.exists("vendor/font/LICENZE.md"))

    # 2) Google non compare piu' da nessuna parte: e' il cantiere
    prova("font: Google non compare piu' nella pagina", True,
          "fonts.googleapis" not in mini and "fonts.gstatic" not in mini)
    prova("font: Google non compare piu' nel service worker", True,
          "fonts.googleapis" not in swjs and "fonts.gstatic" not in swjs)

    # 3) la rotta: esplicita e con whitelist, mai una directory montata
    prova("font: la rotta e' esplicita e passa da una whitelist", True,
          '@app.get("/vendor/font/{nome}")' in _SORGENTE
          and "if nome not in FILE_FONT:" in _SORGENTE)
    prova("font: i sei nomi sono nella whitelist del server", 6,
          sum(1 for n in FILE if f'"{n}.woff2"' in _SORGENTE))

    # 4) in dispensa i tre del latino, e nient'altro
    for n in ("baloo2-latin", "nunito-latin", "jetbrains-mono-latin"):
        prova(f"font: {n} e' in dispensa PWA", True,
              f"'/vendor/font/{n}.woff2'," in swjs)
    prova("font: i latin-ext NON gonfiano l'addAll atomico", True,
          "latin-ext.woff2'," not in swjs)
    prova("font: la VERSIONE del SW e' salita", True,
          "barattolo-v5" in swjs)
    prova("font: il ramo cache-first di Google e' codice morto tolto",
          True, "fontDallaDispensa" not in swjs and "CACHE_FONT" not in swjs)

    # 5) I PESI SONO QUELLI DI IERI, uno per uno
    blocchi = re.findall(
        r"@font-face\{font-family:'([^']+)';font-style:normal;"
        r"font-weight:(\d+);", mini)
    pesi = {}
    for fam, w in blocchi:
        pesi.setdefault(fam, set()).add(int(w))
    prova("font: i pesi di Baloo 2 sono quelli di ieri", {700, 800},
          pesi.get("Baloo 2"))
    prova("font: i pesi di Nunito sono quelli di ieri",
          {400, 600, 700, 800}, pesi.get("Nunito"))
    prova("font: i pesi di JetBrains Mono sono quelli di ieri",
          {500, 700}, pesi.get("JetBrains Mono"))
    # Un peso dichiarato a INTERVALLO farebbe istanziare al browser il
    # peso esatto richiesto: e' la riga che cambierebbe la resa senza
    # che nessuno se ne accorga.
    # Si guarda DENTRO i @font-face e non in tutto il file, o la
    # sentinella prende il commento che la spiega — ci si e' inciampati
    # scrivendola, ed e' la stessa trappola gia' pagata altrove.
    prova("font: nessun peso dichiarato a intervallo", 0,
          sum(1 for b in re.findall(r"@font-face\{[^}]*\}", mini)
              if re.search(r"font-weight:\d+ \d+", b)))
    prova("font: otto pesi per due sottoinsiemi", 16, len(blocchi))


def prove_nwc_cifratura():
    """La cifratura NWC si DICHIARA (ago 2026, dal campo: «Primal non
    si collega»). NIP-47 dice che il client mette un tag `encryption`
    nella richiesta e che «l'assenza del tag indica nip04»: noi il tag
    non lo scrivevamo MAI, quindi il ripiego su nip44 spediva un
    contenuto nip44 dentro un evento che si dichiarava nip04 — un
    wallet che segue la specifica non lo decifra e tace, e per
    l'utente diventa «Barattolo non riconosce il mio wallet».

    E il rovescio era peggio del rifiuto: un wallet che RISPONDE
    `UNSUPPORTED_ENCRYPTION` finiva nel ramo «connessione viva» e lo
    SALVAVAMO — collegato in una cifratura che non parla, cioe' un
    wallet che poi non paga mai.

    Qui non si guarda la forma: si fa GIRARE `infoNwc` vera contro un
    wallet di cartone nip44-only, e si chiede che si colleghi (e che
    si colleghi in nip44). Una sentinella sulla forma direbbe che il
    tag c'e', mai che la stretta di mano riesce."""
    print("\n[NWC: la cifratura si dichiara]")
    import json as _json
    import shutil as _sh
    import subprocess as _sp
    import tempfile as _tf
    import os as _os
    node = _sh.which("node")
    if not node:
        salta("il wallet nip44-only si collega", "node non installato")
        return
    mini = open("miniapp.html", encoding="utf-8").read()
    pezzi = "\n\n".join(pezzo_js(mini, f) for f in (
        "function chiaveNwc(con){",
        "async function leggiEventoInfo(NT, relays, walletPub){",
        "async function infoNwc(stringa){",
        "async function clientNwc(dati){"))

    # Il wallet di cartone: risponde SOLO alla cifratura che parla, e
    # a quella sbagliata risponde `UNSUPPORTED_ENCRYPTION` come
    # prescrive la specifica — cioe' PARLA, che e' esattamente il caso
    # in cui prima lo salvavamo storto.
    banco = """
// le chiavi finte si COSTRUISCONO, mai scritte per esteso: lo
// scanner dei segreti rifiuta 64 esadecimali di fila fuori da
// vendor/, e quella regola e' larga apposta — un fixture non vale
// un'eccezione (basta che siano esadecimali e lunghe giuste).
const PK = 'b8'.repeat(32);
const SEC = '71'.repeat(32);
let PARLA = 'nip44';
let ultimo = null, n = 0;
function caricaNostrTools(){ return Promise.resolve(); }
const eco = t => t;
const relay = {
  subscribe(filtri, h){
    if ((filtri[0].kinds || []).includes(13194)) setTimeout(()=>h.oneose(), 0);
    else relay.onev = h.onevent;
  },
  publish(ev){
    ultimo = ev;
    const tag44 = (ev.tags || []).some(t => t[0] === 'encryption' && /nip44/.test(t[1] || ''));
    const giusta = (PARLA === 'nip44') === tag44;
    const msg = giusta ? {result: {methods: ['pay_invoice']}}
                       : {error: {code: 'UNSUPPORTED_ENCRYPTION', message: 'no'}};
    setTimeout(()=>relay.onev({tags: [['e', ev.id]], content: JSON.stringify(msg)}), 0);
    return Promise.resolve();
  },
  close(){},
};
const NT = {
  nip47: {parseConnectionString: () => ({pubkey: PK, relays: ['wss://finto'], secret: SEC})},
  utils: {hexToBytes: h => h},
  getPublicKey: () => 'cli',
  nip44: {getConversationKey: () => 'k', encrypt: eco, decrypt: eco},
  nip04: {encrypt: (a, b, t) => t, decrypt: (a, b, t) => t},
  finalizeEvent: (e) => Object.assign({}, e, {id: 'ev' + (++n)}),
  Relay: {connect: () => Promise.resolve(relay)},
};
const window = {NostrTools: NT};
const console2 = console; console = {log(){}};   // il client chiacchiera

function chiavi(){
  const casi = {};
  for (const [nome, pk] of [['esadecimale', PK], ['maiuscola', PK.toUpperCase()],
                            ['barra finale', '/'], ['npub', 'npub1hyfl7kc5fmvs0']]) {
    try { casi[nome] = chiaveNwc({pubkey: pk}); }
    catch(e){ casi[nome] = 'NO: ' + e.message; }
  }
  return casi;
}

(async () => {
  const out = {chiavi: chiavi()};
  for (const modo of ['nip44', 'nip04']) {
    PARLA = modo; ultimo = null;
    try {
      const r = await infoNwc('nostr+walletconnect://' + PK + '?relay=wss://finto&secret=' + SEC);
      out['esito_' + modo] = r.cifratura;
    } catch(e){ out['esito_' + modo] = 'ESPLODE: ' + e.message; }
    out['tag_' + modo] = (ultimo.tags || []).some(t => t[0] === 'encryption' && t[1] === 'nip44_v2');
  }
  console2.log(JSON.stringify(out));
  process.exit(0);
})();
"""
    f = _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    f.write(pezzi + "\n" + banco)
    f.close()
    try:
        r = _sp.run([node, f.name], capture_output=True, text=True, timeout=60)
    finally:
        _os.unlink(f.name)
    if r.returncode != 0:
        prova("il banco NWC gira", "", r.stderr.strip()[:300])
        return
    o = _json.loads(r.stdout.strip().splitlines()[-1])

    # 1) il tag encryption, come prescrive NIP-47
    prova("verso un wallet nip44 la richiesta DICHIARA nip44_v2",
          True, o["tag_nip44"])
    prova("verso un wallet nip04 il tag NON si mette (l'assenza vale nip04)",
          False, o["tag_nip04"])

    # 2) UNSUPPORTED_ENCRYPTION non e' una connessione viva
    prova("il wallet nip44-only si collega, e si collega in nip44",
          "nip44", o["esito_nip44"])
    prova("il wallet nip04 resta identico a ieri",
          "nip04", o["esito_nip04"])

    # 3) le due guardie sulla chiave
    prova("la chiave esadecimale passa", "b8" * 32,
          o["chiavi"]["esadecimale"])
    prova("la chiave MAIUSCOLA si abbassa", "b8" * 32,
          o["chiavi"]["maiuscola"])
    prova("la barra finale non diventa una chiave", True,
          o["chiavi"]["barra finale"].startswith("NO: "))
    prova("l'npub lo dice, invece di far esplodere nip04", True,
          "npub" in o["chiavi"]["npub"])

    # la forma, per quel che l'eseguibile non puo' vedere: il ramo che
    # SALVA non deve tornare raggiungibile per un codice qualunque.
    corpo = pezzo_js(mini, "async function infoNwc(stringa){")
    prova("il ramo del codice guarda UNSUPPORTED_ENCRYPTION prima di salvare",
          True, corpo.index("UNSUPPORTED_ENCRYPTION") < corpo.index("connessione viva"))
    prova("la preferenza dell'evento info ORDINA, non esclude",
          True, "['nip44', 'nip04']" in corpo and "['nip04', 'nip44']" in corpo)

    # e il giudice dev'essere COLLEGATO, non solo esistere: la tortura
    # ha visto sopravvivere la mutazione che rimette `con.pubkey` nei
    # due chiamanti — la guardia c'era e non la chiamava nessuno, e
    # tutte le prove restavano verdi. Quindi un CENSIMENTO invece di
    # un elenco: fuori da chiaveNwc la chiave del wallet non si legge
    # a mano da nessuna parte, nemmeno dalla funzione che qualcuno
    # aggiungera' qui fra sei mesi.
    i = mini.index("const NWC_CHIAVE")
    sezione = mini[i:mini.index("async function collegaWallet(")]
    fuori = sezione.replace(pezzo_js(mini, "function chiaveNwc(con){"), "")
    # il verdetto del relay si stampa: senza, un evento rifiutato e un
    # wallet muto si raccontano identici (un timeout), ed e' l'ambiguita'
    # che ha reso difficile la diagnosi di Primal.
    cn = pezzo_js(mini, "async function clientNwc(dati){")
    prova("il rifiuto del relay non si ingoia in silenzio",
          False, "catch(()=>{})" in cn.replace(" ", ""))
    prova("...e si dice a chi guarda la console",
          True, "il relay ha rifiutato" in cn)

    prova("fuori dal giudice nessuno si legge la pubkey a mano",
          0, fuori.count("con.pubkey"))
    prova("e il giudice lo chiamano tutti e due i chiamanti",
          2, fuori.count("chiaveNwc(con)"))


def main():
    print("=" * 58)
    print("  LE PROVE DI BARATTOLO")
    print("=" * 58)
    for f in (prove_filtro_italiano, prove_testo_evento,
              prove_tag_commercio, prove_anello, prove_categorie,
              prove_nome_nostr,
              prove_senza_condizione, prove_sottocategorie,
              prove_ricategorizza, prove_asta, prove_proxy_asta,
              prove_annullo, prove_abbandonati,
              prove_ritiro, prove_disarmo, prove_importo_uscita,
              prove_initdata, prove_foto, prove_foto_scarti, prove_avatar,
              prove_pagamento_incerto, prove_disputa_incagliata,
              prove_idor_verifica, prove_contenuti_cifrati,
              prove_busta_ritiro, prove_indirizzo_casa,
              prove_nascondi_ordine,
              prove_lista_ordini, prove_dettaglio_ordine,
              prove_ssrf_redirect, prove_quota_ricerca,
              prove_tracking_corretto, prove_barattolo,
              prove_savers_proprietario, prove_barattolo_in_testata,
              prove_messaggio_admin, prove_avviso_contatto,
              prove_forma_tracking, prove_bip353, prove_firme_nostr, prove_conta_feedback,
              prove_ferie, prove_stock_raccontato,
              prove_xp, prove_coorti_titoli, prove_conto_acquisto,
              prove_supplemento_spedizione,
              prove_sconto_pacco, prove_forma_sconto_pacco,
              prove_divisione_a_ritroso,
              prove_sped_gratis, prove_valuta_soglia, prove_suggerimenti,
              prove_libro_mastro, prove_leve, prove_canale_bot,
              prove_vetrina_canale,
              prove_cambio, prove_recupero_cambi,
              prove_consegna_payload_punto, prove_reti_corriere,
              prove_pagina_acquisto,
              prove_posizione_vetrina, prove_anteprime, prove_seo,
              prove_impersonazione, prove_avviso_spedizione,
              prove_ricevuta_compratore, prove_titoli_scappati,
              prove_timbri_periodici, prove_offerta_quantita,
              prove_ritiro_offerta, prove_fogli_di_casa,
              prove_sollecito_a_comando,
              prove_sat_non_e_barattolo, prove_ai_segnala,
              prove_ordini_fermi, prove_numero_ordine,
              prove_promesse_badge, prove_promesse_raggiungibili,
              prove_verde_e_filtri,
              prove_guardia_is_bot,
              prove_altri_scorrimento,
              prove_script_nel_workflow,
              prove_nwc_cifratura,
              prove_pagina_dati,
              prove_font,
              prove_sintassi_client):
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
