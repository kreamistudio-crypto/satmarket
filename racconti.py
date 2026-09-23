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
To The Mooon resta dov'e': lo accende lo spazio sponsorizzato, e
traslocarlo vorrebbe dire rifare la card di «Da scoprire» con le sue
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

LO STATO (bozza o pubblicata) NON STA QUI: vive in `impostazioni`, e
lo cambia il gesto del moderatore dal pannello. Questo file dice COSA
c'e' scritto, mai SE si vede.
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
        # LE FOTO NON SONO ANCORA ARRIVATE, e questa e' la riga del
        # cantiere di una riga: quando ci sono, i file vanno in
        # assets/racconti/ coi nomi qui sotto (WebP, larghe 1360 come
        # quelle di To The Mooon) e `foto` passa a True. Nient'altro:
        # la rotta li serve gia' (FORMA_RACCONTO + questo catalogo) e il
        # renderer sa gia' dove metterli.
        # Finche' e' False l'anteprima (dei moderatori e del venditore)
        # mostra un segnaposto con l'etichetta, e chi arriva sulla pagina
        # pubblicata non vede nessun riquadro: la storia esce senza
        # immagini invece che con dei buchi.
        #   una-garlanda-cop.webp  la copertina, 21:9 come l'hero di To The Mooon
        #   una-garlanda-1.webp    le varietà
        #   una-garlanda-2.webp    l'ecosistema
        #   una-garlanda-3.webp    la pileria
        #   una-garlanda-4.webp    il QR di EcoOasi (piccola)
        #   una-garlanda-5.webp    le persone
        #   una-garlanda-6.webp    il logo (piccola)
        "foto": False,
        # IL LOGO DELLA CARD «CONSIGLIATI» NON C'E' ANCORA: quando c'e',
        #   python prepara_logo_consigliato.py <il PNG> una-garlanda
        # e qui True. Puo' essere lo stesso disegno della foto 6 (il logo
        # dentro la storia), ma e' un altro file: quella e' una foto del
        # racconto, questo gira nella card sul bruno delle categorie e
        # vuole la trasparenza.
        "logo": False,
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
            # il QR subito sotto la voce che lo nomina
            {"t": "foto", "n": 4, "etichetta": "QR EcoOasi", "piccola": True,
             "alt": "Il QR di EcoOasi"},
            {"t": "foto", "n": 5, "etichetta": "persone",
             "alt": "La Famiglia Stocchi"},
            {"t": "firma", "h": "Custodi di Natura e Biodiversità",
             "p": "Famiglia Stocchi, Rovasenda (VC)"},
            {"t": "foto", "n": 6, "etichetta": "logo", "piccola": True,
             "alt": "Il logo di Una Garlanda"},
        ],
    },
}
