# -*- coding: utf-8 -*-
"""
LE PAGINE DEI NEGOZI CONSIGLIATI CHE NASCONO IN BOZZA (set 2026).

Il racconto in cima a un negozio — pastiglia, titolo, storia, schede,
foto — con la STESSA FORMA del catalogo `RACCONTI` di miniapp.html,
quello di To The Mooon, e disegnato dallo STESSO renderer
(`raccontoNegozio`). Cambia una cosa sola, ed e' quella che decide
dove vive: queste pagine nascono in BOZZA, e una bozza la vedono i
moderatori e il venditore della pagina — nessun altro.

PERCHE' QUI E NON ACCANTO A TO THE MOOON. Il catalogo del client
viaggia DENTRO la pagina, a chiunque la apra: una bozza scritta li'
sarebbe leggibile nel sorgente da tutti — invisibile solo a chi non
guarda, che non e' «invisibile». Questo file invece non lo serve
nessuna rotta, e il testo ne esce da tre porte sole:
  - `/api/negozio/{chi}`, e SOLO a pagina pubblicata;
  - `/api/admin/racconti`, che risponde 403 a chi non e' moderatore;
  - `/api/me/racconti`, che al venditore da' le pagine del SUO negozio
    e a chiunque altro una lista vuota.
To The Mooon resta dov'e': la sua card in «Da scoprire» la accende lo
spazio sponsorizzato, e traslocarlo vorrebbe dire rifarla con le sue
prove — un altro cantiere (vedi Cantieri, «Una Garlanda in bozza»).

SONO DATI E NON MARKUP, il patto del catalogo gemello: testi nudi,
che il client passa da esc() come quelli di chiunque altro. Qui NON
ci va la parola della pastiglia: la scrive il renderer, perche' la
dichiarazione non deve poter dipendere dal catalogo (c'e' la prova).
Il catalogo porta solo l'EMOJI che le sta davanti.

LE CHIAVI SONO QUELLE DEL CLIENT, apposta: `t` il tipo del blocco,
`h` il titoletto, `p` la prosa, `voci` gli elementi, `e` l'emoji di
una scheda, `n` il numero della foto. In piu', per queste pagine:
  - `etichetta`: che foto va li' — la dice il SEGNAPOSTO che
    l'anteprima (dei moderatori e del venditore) mostra finche' le foto
    non arrivano;
  - `piccola`: logo e QR non vanno a colonna piena;
  - il blocco `firma`: la chiusura, `h` in grassetto e `p` sotto;
  - `logo` (set 2026): il marchio che gira nella card «Consigliati»
    della home, in `assets/consigliati/<slug>.webp` — lo prepara
    `prepara_logo_consigliato.py`. E' la SECONDA condizione per entrare
    fra i Consigliati, accanto alla pubblicazione: finche' e' False la
    pagina, anche pubblicata, si apre dal suo negozio e basta. Non esce
    verso il client (non e' fra i CAMPI_RACCONTO): lo legge il solo
    `consigliati_pubblici`.
  - `logo_giu` (set 2026): quanto scende quel logo nel quadrato della
    card, in pixel della card del telefono (84px; sul computer scala
    con lei), negativo per salire, da -12 a 12. Serve ai marchi col
    peso tutto in alto o in basso, che centrati a riquadro sembrano
    fuori centro. Esce nella busta dei Consigliati accanto al logo.
  - `banner` (set 2026): l'immagine della card del negozio nella
    pagina «Consigliati», in `assets/scoprire/<slug>.webp` — le misure
    del banner di To The Mooon (1040x498), col nome dentro il disegno.
    Senza, la card della pagina e' la riserva col logo e il nome sul
    bruno. Come il logo conta SOLO a pagina pubblicata: la busta lo
    porta come vero/falso, e la rotta di «Da scoprire» serve il file di
    una pagina del server solo quando e' pubblicata col suo `banner`
    vero. E' ANCHE LA CARD DELLO SPAZIO SPONSORIZZATO di «Da scoprire»
    (24 set 2026): una pagina col suo `banner` si accende dal bot come
    quelle del catalogo di casa (`/sponsor <slug> 30`), e la sua card
    compare solo a pagina PUBBLICATA — in bozza lo spazio puo' essere
    acceso, e la scadenza corre, ma non si vede. Uno slug non puo' stare
    in tutt'e due i cataloghi: ogni spazio ha una leva sola.

LO STATO (bozza o pubblicata) NON STA QUI: vive in `impostazioni`, e
lo cambia il gesto del moderatore dal pannello. Questo file dice COSA
c'e' scritto, mai SE si vede. Quindi anche TOGLIERE UNA PAGINA DAI
CONSIGLIATI non si fa da qui: si fa col «📝 Rimetti in bozza» del
pannello, che la toglie dalla card, dalla pagina e dal negozio
insieme — mentre per le voci del catalogo di casa la leva e'
`consigliato: false` nel client, che dal server non si puo' spegnere.
"""

RACCONTI_NEGOZI = {
    "una-garlanda": {
        # IL LEGAME PAGINA → VENDITORE ha due forme, e la PRIMA VINCE:
        #  - `negozio`: il CODICE del suo negozio (otto caratteri, es.
        #    "1b9a53e6") — pubblico e stabile per costruzione, la forma
        #    di casa (il patto di SLUG_SPONSOR e dei punti di ritiro:
        #    «nessun tg_id entra nel repo»);
        #  - `venditore_tg`: il tg_id del suo account, che il server
        #    risolve nel codice da solo.
        # ⚠️ QUI C'E' LA SECONDA, ED E' UN'ECCEZIONE DICHIARATA (23 set
        # 2026, decisione di Andrea): il codice di Manuele (@Manumussa,
        # «Manuele M.») si legge solo dal database del VPS, che da qui
        # non si tocca, e Andrea ha scelto il tg_id per chiudere il
        # cantiere invece di fermarlo. Il tg_id NON ESCE DAL SERVER: non
        # e' fra i CAMPI_RACCONTO e nessuna risposta lo porta (c'e' la
        # prova). LA STRADA DEL RITORNO e' una riga: letto il codice
        # (il cassetto del pannello lo mostra accanto al nome), lo si
        # scrive in `negozio` e si toglie `venditore_tg`.
        # Senza nessuna delle due la pagina esiste solo nell'anteprima
        # dei moderatori e NON si puo' pubblicare (fail-closed).
        "negozio": "",
        "venditore_tg": 525073888,
        "emoji": "🌾",
        "titolo": "Una Garlanda",
        "sottotitolo": "Riso biodiverso. Custodito, non prodotto.",
        "intro": ("Non è semplice riso biologico. Una Garlanda è l'azienda "
                  "agricola della Famiglia Stocchi a Rovasenda, nel cuore "
                  "della Baraggia vercellese, una delle terre storiche del "
                  "riso italiano. Qui si custodiscono e si coltivano "
                  "varietà antiche e tradizionali, alcune molto rare, "
                  "riproducendo i semi anno dopo anno."),
        # LE FOTO DI MANUELE (30 set 2026), con la ricetta di «Un tempo
        # per te»: WebP q82 senza metadati, sotto i 250 KB, mai
        # ingrandite. IL QR DI ECOOASI E' STATO TOLTO (decisione di
        # Andrea): non e' ancora attivo e non si sa quando lo sara'. Il
        # giorno che c'e', torna come foto 4, piccola, subito sotto
        # l'elenco che nomina EcoOasi.
        #   una-garlanda-cop.webp  il labirinto nella risaia, 21:9
        #   una-garlanda-1.webp    le varietà: i sacchetti e i chicchi
        #   una-garlanda-2.webp    l'ecosistema: risaie, alberi e stagni
        #   una-garlanda-3.webp    la pileria: le macine
        #   una-garlanda-5.webp    le persone: la famiglia
        #   una-garlanda-6.webp    il logo, il fiore del riso (piccola)
        "foto": True,
        # il logo della card «Consigliati», da logo.png: lo stesso
        # disegno della foto 6, ma un altro file (sul bruno delle
        # categorie, con la trasparenza). Entra nella card solo a pagina
        # pubblicata. ALL'86% DEL RIQUADRO (30 set 2026, dal telefono di
        # Andrea):
        #   python prepara_logo_consigliato.py logo.png una-garlanda 0.86
        "logo": True,
        # E CENTRATO NEL QUADRATO (1 ott 2026, dal telefono di Andrea:
        # a +2 stava troppo in basso). Era -6, il centro del PESO (al 59%
        # dell'altezza, la spiga in basso): ma il disegno riempiva tutto
        # il riquadro, e 6px in su lo portavano 1,7px oltre il bordo del
        # quadrato — la cima tagliata. Poi +2, scelto sulla simulazione,
        # e sul telefono pareva sceso. All'86% e 0 ha ~9,5px d'aria sopra
        # e sotto nel quadrato da 84: non tocca mai i bordi.
        "logo_giu": 0,
        # il banner della card nella pagina «Consigliati», 1040x498
        "banner": True,
        "blocchi": [
            {"t": "testo", "h": "COS'È",
             "p": ("Riso di varietà storiche, coltivato senza nessun "
                   "trattamento, nemmeno quelli ammessi nel biologico, "
                   "dentro il primo ecosistema europeo di agroforestazione "
                   "in risicoltura. Ogni confezione contiene una varietà, "
                   "una storia, un territorio e un pezzo di biodiversità "
                   "agricola che continua a esistere perché qualcuno la "
                   "custodisce.")},
            {"t": "foto", "n": 1, "etichetta": "varietà",
             "alt": "Le varietà storiche di riso di Una Garlanda"},
            {"t": "punti", "h": "IL VALORE DELLE ORIGINI", "voci": [
                {"e": "🌱", "h": "Semi antichi custoditi nel tempo",
                 "p": ("Dellarole, Rosa Marchetti, Chinese Originario, "
                       "Bertone 1819, Rosso Angelo Aromatico: varietà "
                       "storiche di cui si preservano i semi e la "
                       "biodiversità.")},
                {"e": "🌳", "h": "Cresce in un ecosistema, non in una coltivazione",
                 "p": ("Le risaie convivono con alberi, siepi, fasce "
                       "naturali e altri habitat: agricoltura e "
                       "biodiversità crescono insieme. È il primo "
                       "ecosistema europeo di agroforestazione in "
                       "risicoltura.")},
                {"e": "🚫", "h": "Nessun trattamento, neppure quelli del biologico",
                 "p": ("Oltre il disciplinare: nessun prodotto chimico, "
                       "nemmeno quelli consentiti in agricoltura "
                       "biologica.")},
            ]},
            {"t": "foto", "n": 2, "etichetta": "ecosistema",
             "alt": ("Le risaie fra alberi e siepi: l'agroforestazione "
                     "in risicoltura")},
            # Le tappe vanno a capo sotto il loro titolo, quindi la
            # prosa comincia con la maiuscola (nel testo consegnato
            # stava dopo una lineetta, sulla stessa riga).
            {"t": "tappe", "h": "COME SI COLTIVA", "voci": [
                {"h": "Il suolo vivo",
                 "p": ("Rotazioni, colture di copertura, minima lavorazione "
                       "del terreno e agroforestazione, per creare habitat "
                       "a insetti, uccelli, anfibi e a tutte le specie "
                       "dell'ecosistema della risaia.")},
                {"h": "Dal seme al piatto",
                 "p": ("La famiglia segue direttamente tutto il percorso, "
                       "dalla conservazione e riproduzione del seme alla "
                       "coltivazione, dalla raccolta alla lavorazione e al "
                       "confezionamento.")},
                {"h": "Lavorato a pietra",
                 "p": ("Dopo la raccolta il riso passa nella pileria "
                       "aziendale dedicata, con lavorazioni delicate "
                       "pensate per rispettare le caratteristiche di ogni "
                       "varietà.")},
                {"h": "Oggi",
                 "p": ("Il riso della Famiglia Stocchi è la conseguenza di "
                       "un ecosistema, non di una produzione.")},
            ]},
            {"t": "foto", "n": 3, "etichetta": "pileria",
             "alt": "La pileria aziendale, dove il riso si lavora a pietra"},
            {"t": "elenco", "h": "COM'È FATTO", "voci": [
                ("Varietà storiche: Dellarole, Rosa Marchetti, Chinese "
                 "Originario, Bertone 1819, Rosso Angelo Aromatico"),
                "Semi riprodotti in azienda, anno dopo anno",
                "Zero trattamenti, oltre il disciplinare biologico",
                "Filiera certificata dal seme al piatto",
                "Lavorazione a pietra nella pileria aziendale",
                "EcoOasi: custodi di natura e biodiversità",
            ]},
            {"t": "foto", "n": 5, "etichetta": "persone",
             "alt": "La Famiglia Stocchi"},
            {"t": "firma", "h": "Custodi di Natura e Biodiversità",
             "p": "Famiglia Stocchi, Rovasenda (VC)"},
            {"t": "foto", "n": 6, "etichetta": "logo", "piccola": True,
             "alt": "Il logo di Una Garlanda"},
        ],
    },
    "un-tempo-per-te": {
        # IL LEGAME COL VENDITORE E' IL TG_ID, la stessa eccezione
        # dichiarata di Una Garlanda (24 set 2026, decisione di Andrea):
        # Luca, @lucabortolameotti, negozio «Un tempo per te». La strada
        # del ritorno e' la stessa: letto il codice nel cassetto del
        # pannello, lo si scrive in `negozio` e si toglie `venditore_tg`.
        "negozio": "",
        "venditore_tg": 613784705,
        "emoji": "🌱",
        "titolo": "Un tempo per te",
        # il titolo della pagina e' l'h3 della testa, che il renderer
        # prende da qui: la riga intera come l'hanno scritta loro
        "sottotitolo": "Un tempo per te. Il cibo, per noi, è cura.",
        "intro": ("Siamo Luca e Katia. Amiamo la natura, gli animali, lo "
                  "sport e il vivere in modo semplice e sano. Per anni "
                  "abbiamo cercato un luogo dove tutto questo potesse "
                  "incontrarsi, e lo abbiamo trovato nel centro storico di "
                  "Dro, in Trentino, a pochi chilometri dal Lago di Garda. "
                  "Lì il nostro sogno è diventato casa: prima un B&B, poi "
                  "una cucina aperta a chi vuole imparare, e oggi anche i "
                  "nostri prodotti."),
        # LE FOTO CI SONO (WebP senza metadati, al massimo 1360 di lato
        # come quelle di To The Mooon, mai ingrandite). LE VERTICALI SONO
        # QUADRATE (24 set 2026, ritocco di Andrea: in piedi si prendevano
        # troppo spazio): ritaglio 1:1 centrato dagli originali, che sul
        # soggetto non tagliava niente — le orizzontali restano com'erano.
        #   un-tempo-per-te-cop.webp  la copertina (1-copertina), 21:9
        #   un-tempo-per-te-1.webp    i prodotti, 1:1
        #   un-tempo-per-te-2.webp    la cucina
        #   un-tempo-per-te-3.webp    la colazione, 1:1
        #   un-tempo-per-te-4.webp    Katia e Luca
        #   un-tempo-per-te-5.webp    il dettaglio, 1:1
        "foto": True,
        # il logo della card «Consigliati», da logo.pdf: entra nella card
        # solo a pagina pubblicata. ALL'86% DEL RIQUADRO (30 set 2026,
        # come Una Garlanda): pieno, col suo -4 arrivava a 0,3px dal
        # bordo alto del quadrato.
        #   python prepara_logo_consigliato.py logo.png un-tempo-per-te 0.86
        "logo": True,
        # il peso del disegno sta al 56% dell'altezza (il riquadro scuro
        # col nome in basso, il camino sottile in cima): era -4 a logo
        # pieno; all'86% la stessa correzione e' ~-3, e -2 tiene il
        # camino a ~7,5px dal bordo del quadrato da 84
        "logo_giu": -2,
        # il banner della card nella pagina «Consigliati», 1040x498
        "banner": True,
        "blocchi": [
            {"t": "testo", "h": "COS'È",
             "p": ("Una realtà di autoproduzione alimentare 100% vegetale. "
                   "Creme spalmabili, prodotti da forno, fermentati, "
                   "conserve e alternative vegetali ai formaggi, preparati "
                   "a mano e in piccole quantità, con attenzione alle "
                   "materie prime, alla qualità nutrizionale e alla "
                   "sostenibilità. Sono le stesse ricette che nascono ogni "
                   "mattina nella nostra cucina, per i nostri ospiti.")},
            {"t": "foto", "n": 1, "etichetta": "prodotti",
             "alt": "I prodotti di Un tempo per te"},
            {"t": "punti", "h": "UN TEMPO PER TE, PER INTERO", "voci": [
                {"e": "🏡", "h": "Il B&B ecologico",
                 "p": ("Da qui è partito tutto. Tre camere e un "
                       "appartamento, luminosi ed essenziali, con i nomi "
                       "delle posizioni dello yoga; una cucina comune dove "
                       "ci si incontra al mattino, un angolo lettura con la "
                       "nostra Biblioteca del Benessere, e un giardino dove "
                       "fare colazione quando il sole lo permette. Qui non "
                       "troverete lusso, ma accoglienza vera.")},
                {"e": "🥣", "h": "Il Vegan Home Lab",
                 "p": ("Non un ristorante, ma uno spazio dove condividiamo "
                       "quello che abbiamo imparato: corsi di cucina "
                       "vegetale, laboratori sulle fermentazioni naturali e "
                       "sulle autoproduzioni casalinghe, anche in versione "
                       "crudista e senza glutine, e percorsi di formazione "
                       "per cuochi. Si impara facendo, e si finisce sempre "
                       "a tavola, insieme, ad assaggiare quello che abbiamo "
                       "preparato.")},
                {"e": "🧘", "h": "La sala olistica",
                 "p": ("Yoga e ritiri dedicati all'Ayurveda, per un "
                       "benessere che parte dal corpo e arriva a tutto il "
                       "resto.")},
            ]},
            {"t": "foto", "n": 2, "etichetta": "cucina",
             "alt": "Luca e Katia al lavoro nella loro cucina"},
            {"t": "testo", "h": "IL CIBO È CURA",
             "p": ("Ogni colazione e ogni brunch è preparato in casa, 100% "
                   "vegetale, biologico e naturale, con la stessa "
                   "attenzione che mettiamo nell'accogliere chi arriva. È "
                   "da questa cura quotidiana che sono nati i prodotti che "
                   "trovate qui: non una linea pensata a tavolino, ma "
                   "quello che serviamo davvero, in barattolo.")},
            {"t": "foto", "n": 3, "etichetta": "colazione",
             "alt": "Una colazione preparata in casa"},
            # le tappe vanno a capo sotto il loro titolo, come in Una
            # Garlanda: la prosa comincia con la maiuscola
            {"t": "tappe", "h": "COM'È NATO", "voci": [
                {"h": "Il sogno",
                 "p": ("Un luogo dove natura, sport, cibo sano e "
                       "accoglienza potessero stare insieme, cercato per "
                       "anni.")},
                {"h": "La casa",
                 "p": ("Un piccolo B&B ecologico nel centro di Dro, per chi "
                       "ha voglia di fermarsi, respirare e ricominciare con "
                       "più energia.")},
                # «il Home Lab» nel testo consegnato: il nome intero, come
                # nella scheda qui sopra, rimette a posto l'articolo
                {"h": "La cucina",
                 "p": ("Dalle colazioni per gli ospiti sono nati il Vegan "
                       "Home Lab, i corsi e i laboratori.")},
                {"h": "Oggi",
                 "p": ("Le stesse preparazioni, ora anche per chi non passa "
                       "da Dro.")},
            ]},
            {"t": "foto", "n": 4, "etichetta": "Katia e Luca",
             "alt": "Katia e Luca fra gli scaffali dei loro barattoli"},
            {"t": "elenco", "h": "COM'È FATTO", "voci": [
                "100% vegetale, biologico e naturale",
                "Piccole quantità, preparate a mano",
                ("Creme spalmabili, prodotti da forno, fermentati, conserve, "
                 "formaggi vegetali"),
                "Filiera corta, etica e relazione diretta",
                "Opzioni crudiste e senza glutine nei laboratori",
                ("B&B ecologico, Vegan Home Lab e sala olistica a Dro (TN)"),
            ]},
            {"t": "foto", "n": 5, "etichetta": "dettaglio",
             "alt": "Un piatto preparato da Un tempo per te"},
            {"t": "firma",
             "h": ("Un tempo per rallentare, per nutrirsi bene, per tornare "
                   "a casa un po' più leggeri."),
             "p": "Katia e Luca, Dro (TN)"},
        ],
    },
}
