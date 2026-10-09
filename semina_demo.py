# -*- coding: utf-8 -*-
"""
🌱 LA SEMINA DELLA DEMO (9 ott 2026, hackathon di Torino, richiesta di
Andrea): il database di COLLAUDO riceve quel che la schermata 3 di
`docs/HACKATHON-SETUP.md` §11.2 da' per scontato e che un database
nato da solo non ha — il negozio To The Mooon, un suo annuncio, il
cliente 111 — e un comando crea l'ordine «creato, non pagato» della
mattina della demo.

IL BUCO CHE L'HA FATTO NASCERE (9 ott, prove della demo sul PC di
Andrea): Barattolo in collaudo parte e l'utente 111 e' loggato, ma la
ricerca «Mooon» non trova niente, `/negozio/1b9a53e6` apre il
mercatino generale e la card «Consigliati» della home — che il client
costruisce dal SUO catalogo (`RACCONTI` di miniapp.html), negozio
`1b9a53e6` compreso — porta a un negozio che in quel database non
esiste: «Negozio non trovato». La card non si puo' spegnere per il solo
collaudo senza toccare il client, e non serve: basta che il negozio
ESISTA col codice che la card gia' porta. E' il legame dichiarato dal
catalogo stesso («IL CODICE NEGOZIO E' IL LEGAME»), letto da
miniapp.html e mai scritto a memoria qui: se un giorno il codice la'
cambia, la semina lo segue.

COSA SEMINA, e perche' cosi':
  - IL NEGOZIO: l'utente finto 444 «To The Mooon» (111, 222 e 999 sono
    le tre identita' di collaudo di sempre, e il negozio della demo non
    deve essere nessuna delle tre: il cliente compra da un ALTRO), col
    codice del catalogo del client, il link a scelta `/negozio/
    tothemooon` (lo stesso nome del NIP-05, `tothemooon@barattolo.store`,
    che e' il nome con cui la demo lo chiama) e la npub PUBBLICA
    dell'identita' di prova `tothemooon` di §11 (il badge Nostr
    auto-dichiarato: regola ferrea 2, la npub e' pubblica, la nsec non
    esiste qui). L'avatar e' il logo gia' in `assets/consigliati/`,
    posato su un quadrato bianco (e' largo, e il cerchio dell'avatar lo
    taglierebbe) nella forma che la whitelist `NOME_FOTO` ammette.
    L'INSEGNA (banner_foto, richiesta di Andrea del 9 ott) e' il banner
    gia' in `assets/scoprire/`, ritagliato 3:1 come fa `_salva_banner`,
    con lo stato 'attivo' che il moderatore darebbe. Il client la mostra
    SOLO con un link https (e' l'uscita verso il sito del venditore,
    col «Esci da Barattolo?») e con `BANNER_NEGOZIO_ATTIVO = True` nel
    config: il sito del negozio vero non sta in nessun documento, e qui
    non si inventa — si passa con `--insegna-link https://…`, e senza
    la semina lo dice.
  - L'ANNUNCIO: il gioco, un pezzo, ritiro a mano a Torino (niente
    spedizione ne' protezione: cosi' il conto dell'ordine E' il prezzo,
    e la riga «oppure 4,80 USDB» dello studio C torna senza resti), col
    PREZZO IN SATS CHE OGGI VALE 4,80 $: lo studio C fissa la cifra in
    dollari (4,80 USDB = 480 unita', «1 USDB = 1 $ al cambio di oggi») e
    non in sats, e il cambio lo sa il server — `cambio_noto`, la riga
    'usd' che CoinGecko gli ha dettato all'ultimo giro. Rilanciare la
    semina la mattina della demo RITARA il prezzo al cambio fresco:
    e' il modo in cui «4,80» resta 4,80 anche se bitcoin si e' mosso.
    Senza un cambio nel database la semina si FERMA e lo dice: un
    prezzo a memoria sarebbe un numero inventato (`--cambio-usd` lo
    passa a mano, dichiarato).
  - IL CLIENTE 111: scritto come lo scrive `_upsert_da_telegram` al
    primo ingresso, cosi' «Ordini» e il Profilo lo trovano anche se
    Andrea non ha ancora aperto l'app su quel database.
  - L'ORDINE (`ordine`): stato 'creato', `payment_hash` VUOTO e nessuna
    fattura, ed e' deliberato in tutt'e due le direzioni. Il mietitore
    (`controlla_abbandonati`) guarda SOLO gli ordini con un payment_hash
    (e' la sua domanda a LNbits), quindi questo resta 'creato' tutto il
    giorno senza che nessuno lo annulli alle sue spalle; e una fattura
    di cartone sarebbe una bugia su un ordine che la demo paga in USDB
    (il foglio di sabato) e non in sats. Non si passa da `/api/orders`
    perche' quella strada conia la invoice su LNbits, che sul portatile
    della demo non c'e'.

IDEMPOTENTE: ogni pezzo si cerca prima di scriverlo — il negozio per
tg_id e codice, l'annuncio per venditore e titolo, il cliente per
tg_id, l'ordine per cliente+annuncio+stato — e rilanciare non duplica
niente. L'unico gesto ripetibile apposta e' `ordine --nuovo`, per il
secondo ordine della domenica (§11.3: quello delle 13:30 e quello del
vivo).

FAIL-CLOSED, DUE VOLTE: senza `MODALITA_COLLAUDO = True` nel config
non scrive un byte (il config del VPS dice False, e questo file non
deve poter seminare un mercatino vero nemmeno per sbaglio); e vuole un
database che il SERVER ha gia' creato — la semina non conosce lo
schema, lo controlla (`controlla_schema`) e si ferma se manca una
tabella o una colonna, invece di crearne una versione sua. Niente
`import server` (la lezione degli script che lo facevano: parte
init_db e il giro intero), niente rete, niente VPS: un file sqlite
locale e la cartella `foto/` accanto, come fa il server.

USO (da PowerShell, dalla cartella del repo, col server acceso o no):
  py -3 semina_demo.py            # negozio + annuncio + cliente
  py -3 semina_demo.py ordine     # l'ordine «creato» della mattina
  py -3 semina_demo.py stato      # cosa c'e', senza scrivere
Opzioni: --db PERCORSO (default: `DB` del config), --cambio-usd N
(il cambio $/BTC a mano, se il server non ne ha ancora letto uno),
--insegna-link https://… (il sito del venditore sotto l'insegna).
Per prove e collaudi: SEMINA_CARTELLA_FOTO sposta la cartella delle foto.
"""
import json
import os
import re
import secrets
import sqlite3
import sys
import time
from decimal import Decimal

QUI = os.path.dirname(os.path.abspath(__file__))

# --- IL NEGOZIO ---------------------------------------------------------
# La chiave della voce nel catalogo del client e nelle cartelle di
# assets/ (consigliati/, racconti/, scoprire/): e' la grafia di casa,
# «to-the-moon», diversa dal nome stilizzato con tre «o».
SLUG_CATALOGO = "to-the-moon"
TG_NEGOZIO = 444
NOME_NEGOZIO = "To The Mooon"
# Il link a scelta e il nome NIP-05 sono la stessa parola, apposta: e'
# il nome con cui la demo chiama il negozio («tothemooon@barattolo.store»).
SLUG_NEGOZIO = "tothemooon"
NIP05_NOME = "tothemooon"
# La chiave PUBBLICA dell'identita' di prova `tothemooon` (§11 di
# HACKATHON-SETUP, creata l'8 ott): in npub e non in hex perche' 64
# esadecimali di fila farebbero scattare lo scanner dei segreti della CI.
NPUB_NEGOZIO = "npub12xql9gw8ru2qv63x8nvhtc2vcqcl06rce5d30sw6vcza4zsjgpns0nr6n4"
LOGO = os.path.join("assets", "consigliati", f"{SLUG_CATALOGO}.webp")
AVATAR_LATO = 128          # come AVATAR_LATO del server
AVATAR_QUALITA = 85        # come AVATAR_QUALITA del server
# l'insegna: il banner di «Da scoprire» (1040x498), ritagliato 3:1 al
# centro coi numeri di `_salva_banner` del server
INSEGNA = os.path.join("assets", "scoprire", f"{SLUG_CATALOGO}.webp")
BANNER_LARGO, BANNER_ALTO, BANNER_QUALITA = 1200, 400, 88

# --- L'ANNUNCIO ---------------------------------------------------------
PREZZO_USD = Decimal("4.80")    # lo studio C: «oppure 4,80 USDB», 480 unita'
TITOLO_ANNUNCIO = "To The Mooon! — il gioco da tavolo che spiega Bitcoin"
DESCRIZIONE_ANNUNCIO = (
    "Un gioco da tavolo che ti porta sulla Luna e ti spiega Bitcoin per "
    "la strada: proof of work, gli imprevisti di chi lascia i fondi su un "
    "exchange, il senso di scriversi una seed. Le regole si imparano in "
    "cinque minuti. Nella scatola c'è anche il libro.\n\n"
    "Copia di prova per la demo dell'hackathon «Agentic Dollars on "
    "Bitcoin» (Torino, 17-18 ott 2026): si paga in USDB di prova, e il "
    "negozio ti regala i suoi punti MOON, un punto per euro."
)
CATEGORIA = "Sport e hobby"
SOTTOCATEGORIA = "giochi-tavolo"
ZONA, LAT, LON, REGIONE = "Torino (TO)", 45.0703, 7.6869, "Piemonte"
# le foto del racconto gia' in assets/: la scatola, poi la copertina
FOTO_ANNUNCIO = (f"{SLUG_CATALOGO}-2.webp", f"{SLUG_CATALOGO}-1.webp")

# --- IL CLIENTE ---------------------------------------------------------
TG_CLIENTE, NOME_CLIENTE = 111, "Compratore"

# --- LO SCHEMA CHE LA SEMINA PRETENDE (lo crea il server, non lei) -------
COLONNE_RICHIESTE = {
    "utenti": ("tg_id", "nome", "username", "registrato", "negozio",
               "negozio_slug", "npub", "avatar", "banner_foto", "banner_link",
               "banner_stato", "banner_deciso_il", "banner_sbloccato_il"),
    "annunci": ("id", "venditore_id", "titolo", "descrizione", "categoria",
                "sottocategoria", "prezzo_sats", "zona", "valuta",
                "prezzo_eur", "lat", "lon", "regione", "consegna",
                "paese_domestico", "condizione", "quantita", "quantita_max",
                "foto", "stato", "creato"),
    "ordini": ("id", "cassaforte", "annuncio_id", "compratore_id",
               "venditore_id", "prezzo_sats", "stato", "payment_hash",
               "invoice", "creato", "aggiornato", "cambio_ordine",
               "consegna_scelta", "quantita", "spedizione_sats",
               "protezione_sats"),
    "cambio_noto": ("valuta", "valore", "quando"),
}

CHARSET_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


class SeminaFerma(Exception):
    """La semina si ferma e dice perche': niente scritto a meta'."""


# ======================= I PEZZI PURI (li prova prove.py) ================

def codice_negozio_del_client(sorgente_miniapp: str) -> str:
    """IL CODICE NEGOZIO LO DICE IL CLIENT, non questo file: la voce
    `'to-the-moon'` di `RACCONTI` in miniapp.html porta `negozio:
    '<8 hex>'`, ed e' quello che la card «Consigliati» apre. Si legge
    SOLO quella voce (il catalogo ne ha altre), e senza non si semina
    niente: meglio fermarsi che inventare un codice a cui la card non
    porterebbe mai."""
    m = re.search(r"'" + re.escape(SLUG_CATALOGO) + r"':\s*\{\s*negozio:\s*'([0-9a-f]{8})'",
                  sorgente_miniapp)
    if not m:
        raise SeminaFerma(f"in miniapp.html non trovo `negozio: '<codice>'` "
                          f"nella voce '{SLUG_CATALOGO}' di RACCONTI")
    return m.group(1)


def npub_in_hex(npub: str) -> str:
    """La npub (bech32) nella chiave esadecimale, come `npub_to_hex`
    del server — ricopiata e non importata, perche' il server qui non
    si importa. Serve a dire se la npub seminata e' la stessa che il
    config di collaudo mette in `NIP05_NOMI`."""
    if not npub.startswith("npub1"):
        raise ValueError("npub non valida: non comincia con npub1")
    dati = [CHARSET_BECH32.find(c) for c in npub[5:]]
    if -1 in dati:
        raise ValueError("npub non valida: carattere sconosciuto")
    dati = dati[:-6]
    bits, val, out = 0, 0, []
    for d in dati:
        val = (val << 5) | d
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((val >> bits) & 0xFF)
    hexkey = bytes(out).hex()
    if len(hexkey) != 64:
        raise ValueError("npub non valida: lunghezza sbagliata")
    return hexkey


def sats_da_usd(usd: Decimal, cambio_usd: float) -> int:
    """Quanti sats valgono `usd` dollari a `cambio_usd` $/BTC, al sat
    piu' vicino (mai zero: un annuncio a 0 sats non si pubblica)."""
    if cambio_usd <= 0:
        raise ValueError("cambio $/BTC non positivo")
    return max(1, int((usd / Decimal(str(cambio_usd)) * 100_000_000)
                      .to_integral_value()))


def fmt_sats(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def fmt_usd(d: Decimal) -> str:
    return f"{d:.2f}".replace(".", ",")


# ========================= IL DATABASE ====================================

def controlla_schema(con) -> None:
    """Le tabelle e le colonne che la semina scrive devono ESISTERE
    gia': le crea il server all'avvio (init_db e le sue migrazioni), e
    questo file non ne tiene una copia. Manca qualcosa = ci si ferma
    dicendo cosa, e la cura e' una sola: avviare Barattolo una volta su
    quel database."""
    mancano = []
    for tabella, colonne in COLONNE_RICHIESTE.items():
        presenti = {r[1] for r in con.execute(f"PRAGMA table_info({tabella})")}
        if not presenti:
            mancano.append(f"la tabella `{tabella}`")
            continue
        for c in colonne:
            if c not in presenti:
                mancano.append(f"`{tabella}.{c}`")
    if mancano:
        raise SeminaFerma("il database non ha lo schema del server: manca "
                          + ", ".join(mancano)
                          + ". Avvia Barattolo una volta su questo database "
                          "(py -3 -m uvicorn server:app --port 8080) e rilancia.")


def cambio_noto(con, valuta: str):
    """L'ultimo cambio che il server ha letto da CoinGecko, (valore,
    quando) o (0, 0) se non c'e'. Non e' un dato di denaro: e' il
    promemoria del server, e qui serve a tradurre 4,80 $ in sats."""
    r = con.execute("SELECT valore, quando FROM cambio_noto WHERE valuta=?",
                    (valuta,)).fetchone()
    if not r or not r[0]:
        return 0.0, 0
    return float(r[0]), int(r[1] or 0)


def _codice_libero(con) -> str:
    """Il codice negozio di un utente NUOVO, come `nuovo_codice_negozio`
    del server: 8 hex casuali, unici."""
    while True:
        codice = secrets.token_hex(4)
        if not con.execute("SELECT 1 FROM utenti WHERE negozio=?",
                           (codice,)).fetchone():
            return codice


def _avatar_dal_logo(radice: str, cartella_foto: str, codice: str) -> str:
    """Il logo di assets/consigliati/ come avatar del negozio: posato
    al centro di un quadrato bianco (il logo e' largo e basso, e il
    cerchio dell'avatar ne mangerebbe i bordi), AVATAR_LATO per lato,
    JPEG come i francobolli del server, col nome nella forma della
    whitelist `NOME_FOTO` (`av_<codice>_<n>.jpg`). Il numero e' fisso
    — 1 — cosi' rilanciare riscrive lo stesso file invece di
    seminarne uno a ogni giro. '' se Pillow non c'e' o il logo manca:
    il negozio nasce lo stesso, senza faccia."""
    try:
        from PIL import Image
    except ImportError:
        return ""
    sorgente = os.path.join(radice, LOGO)
    if not os.path.exists(sorgente):
        return ""
    nome = f"av_{codice}_1.jpg"
    try:
        logo = Image.open(sorgente).convert("RGBA")
        lato = max(logo.size)
        quadro = Image.new("RGBA", (lato, lato), (255, 255, 255, 255))
        quadro.alpha_composite(logo, ((lato - logo.width) // 2,
                                      (lato - logo.height) // 2))
        quadro = quadro.convert("RGB").resize((AVATAR_LATO, AVATAR_LATO),
                                              Image.Resampling.LANCZOS)
        os.makedirs(cartella_foto, exist_ok=True)
        quadro.save(os.path.join(cartella_foto, nome), "JPEG",
                    quality=AVATAR_QUALITA)
    except Exception:
        return ""
    return nome


def _insegna_dal_banner(radice: str, cartella_foto: str, codice: str) -> str:
    """L'insegna del negozio dal banner di `assets/scoprire/`: ritaglio
    3:1 al centro, 1200x400 JPEG, come `_salva_banner` del server, col
    nome nella forma della whitelist (`ban_<codice>_<n>.jpg`), numero
    fisso come l'avatar. '' se Pillow o il file mancano."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return ""
    sorgente = os.path.join(radice, INSEGNA)
    if not os.path.exists(sorgente):
        return ""
    nome = f"ban_{codice}_1.jpg"
    try:
        img = Image.open(sorgente).convert("RGB")
        # il ritaglio parte dalla CIMA (centering 0.0, non il centro 0.5
        # del server): in questo banner la scritta sta sul bordo alto, e
        # il taglio centrato le mangiava la testa — visto dal vivo il 9 ott
        img = ImageOps.fit(img, (BANNER_LARGO, BANNER_ALTO),
                           Image.Resampling.LANCZOS, centering=(0.5, 0.0))
        os.makedirs(cartella_foto, exist_ok=True)
        img.save(os.path.join(cartella_foto, nome), "JPEG",
                 quality=BANNER_QUALITA)
    except Exception:
        return ""
    return nome


def link_insegna_valido(url: str) -> bool:
    """Il link sotto l'insegna: solo https, con un host, senza
    credenziali — le prime tre regole di `link_banner_ammesso` del
    server, che qui bastano perche' il link lo scrive Andrea a mano."""
    return bool(re.fullmatch(r"https://[a-z0-9.-]+\.[a-z]{2,}(/[^\s@]*)?",
                             (url or "").strip(), re.I))


def semina_negozio(con, codice: str, radice: str, cartella_foto: str,
                   adesso: int, link_insegna: str = "") -> dict:
    """L'utente 444 col codice del catalogo del client, il link a
    scelta, la npub e l'avatar. Idempotente: la riga si cerca per
    tg_id; il codice si pretende LIBERO o gia' suo — se un altro utente
    del database lo porta (succede solo a mano, o per una collisione da
    1 su 4 miliardi) ci si ferma, perche' rubarglielo spegnerebbe il
    SUO negozio."""
    altro = con.execute("SELECT tg_id FROM utenti WHERE negozio=? AND tg_id!=?",
                        (codice, TG_NEGOZIO)).fetchone()
    if altro:
        raise SeminaFerma(f"il codice negozio {codice} e' gia' dell'utente "
                          f"{altro[0]}: non lo tolgo a nessuno")
    for colonna in ("negozio_slug", "username"):
        preso = con.execute(
            f"SELECT tg_id FROM utenti WHERE {colonna}=? COLLATE NOCASE "
            f"AND tg_id!=?", (SLUG_NEGOZIO, TG_NEGOZIO)).fetchone()
        if preso:
            raise SeminaFerma(f"il link /negozio/{SLUG_NEGOZIO} e' gia' preso "
                              f"({colonna} dell'utente {preso[0]})")
    c_era = con.execute("SELECT 1 FROM utenti WHERE tg_id=?",
                        (TG_NEGOZIO,)).fetchone() is not None
    if not c_era:
        con.execute("INSERT INTO utenti(tg_id, nome, username, registrato, "
                    "negozio) VALUES(?,?,?,?,?)",
                    (TG_NEGOZIO, NOME_NEGOZIO, "", adesso, codice))
    avatar = _avatar_dal_logo(radice, cartella_foto, codice)
    con.execute("UPDATE utenti SET nome=?, negozio=?, negozio_slug=?, npub=?"
                + (", avatar=?" if avatar else "") + " WHERE tg_id=?",
                (NOME_NEGOZIO, codice, SLUG_NEGOZIO, NPUB_NEGOZIO)
                + ((avatar,) if avatar else ()) + (TG_NEGOZIO,))
    insegna, link = _insegna_dal_banner(radice, cartella_foto, codice), ""
    if insegna:
        # il link e' quello passato, o quello gia' in colonna: una
        # semina di ieri con --insegna-link non si spegne rilanciando
        # senza. Lo stato e' quello che darebbe il moderatore.
        gia = con.execute("SELECT banner_link FROM utenti WHERE tg_id=?",
                          (TG_NEGOZIO,)).fetchone()[0] or ""
        link = (link_insegna or gia).strip()
        con.execute("UPDATE utenti SET banner_foto=?, banner_link=?, "
                    "banner_stato='attivo', banner_deciso_il=?, "
                    "banner_sbloccato_il=CASE WHEN banner_sbloccato_il>0 "
                    "THEN banner_sbloccato_il ELSE ? END WHERE tg_id=?",
                    (insegna, link, adesso, adesso, TG_NEGOZIO))
    return {"nuovo": not c_era, "codice": codice, "avatar": avatar,
            "insegna": insegna, "link_insegna": link}


def _copia_foto(radice: str, cartella_foto: str, annuncio_id: int) -> list:
    """Le foto del racconto (assets/racconti/) accanto alle foto degli
    annunci, coi nomi che la whitelist `NOME_FOTO` ammette
    (`a<id>_<n>.webp`). Il client le chiede a `/foto/<nome>`, e la
    rotta serve solo quel che sta in `foto/` con un nome in forma: una
    copia e' il solo modo. Idempotente: stesso nome, stesso file."""
    nomi = []
    for n, f in enumerate(FOTO_ANNUNCIO):
        sorgente = os.path.join(radice, "assets", "racconti", f)
        if not os.path.exists(sorgente):
            continue
        nome = f"a{annuncio_id}_{n}.webp"
        os.makedirs(cartella_foto, exist_ok=True)
        with open(sorgente, "rb") as da, \
                open(os.path.join(cartella_foto, nome), "wb") as a:
            a.write(da.read())
        nomi.append(nome)
    return nomi


def semina_annuncio(con, prezzo_sats: int, radice: str, cartella_foto: str,
                    adesso: int) -> dict:
    """L'annuncio del gioco, un pezzo, ritiro a mano, al prezzo in sats
    che oggi vale 4,80 $. Si cerca per venditore e titolo: se c'e' si
    RITARA (prezzo al cambio di oggi, di nuovo 'attivo' e con un pezzo
    se la demo l'ha gia' venduto una volta), se no nasce con le colonne
    che `/api/listings` scrive per un annuncio come questo. `ricerca_v`
    resta a 0: l'indice della ricerca lo rifa' il server alla prossima
    ricerca (`riallinea_ricerca`), senza aspettare nessun orologio."""
    r = con.execute("SELECT id, prezzo_sats, stato, quantita, quantita_max, foto "
                    "FROM annunci WHERE venditore_id=? AND titolo=? "
                    "ORDER BY id LIMIT 1", (TG_NEGOZIO, TITOLO_ANNUNCIO)).fetchone()
    if r:
        con.execute("UPDATE annunci SET prezzo_sats=?, stato='attivo', "
                    "quantita=1, quantita_max=MAX(quantita_max, 1) WHERE id=?",
                    (prezzo_sats, r[0]))
        esito = {"nuovo": False, "id": r[0], "prezzo_prima": r[1],
                 "stato_prima": r[2], "pezzi_prima": r[3]}
        if not (r[5] or "").strip() or r[5] == "[]":
            foto = _copia_foto(radice, cartella_foto, r[0])
            if foto:
                con.execute("UPDATE annunci SET foto=? WHERE id=?",
                            (json.dumps(foto), r[0]))
        return esito
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
        "sottocategoria,prezzo_sats,zona,valuta,prezzo_eur,lat,lon,regione,"
        "consegna,paese_domestico,condizione,quantita,quantita_max,stato,"
        "creato) VALUES(?,?,?,?,?,?,?,'sats',0,?,?,?,'ritiro','IT','nuovo',"
        "1,1,'attivo',?)",
        (TG_NEGOZIO, TITOLO_ANNUNCIO, DESCRIZIONE_ANNUNCIO, CATEGORIA,
         SOTTOCATEGORIA, prezzo_sats, ZONA, LAT, LON, REGIONE, adesso))
    aid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    foto = _copia_foto(radice, cartella_foto, aid)
    if foto:
        con.execute("UPDATE annunci SET foto=? WHERE id=?",
                    (json.dumps(foto), aid))
    return {"nuovo": True, "id": aid, "foto": foto}


def semina_cliente(con, adesso: int) -> dict:
    """Il cliente 111 come lo scrive il server al primo ingresso
    (`_upsert_da_telegram`): nome, username, data, codice negozio suo.
    Se c'e' gia' non si tocca: il nome che Andrea gli ha dato dall'hash
    (`collaudo:111:<Nome>`) resta il suo."""
    if con.execute("SELECT 1 FROM utenti WHERE tg_id=?", (TG_CLIENTE,)).fetchone():
        return {"nuovo": False}
    con.execute("INSERT INTO utenti(tg_id, nome, username, registrato, negozio) "
                "VALUES(?,?,?,?,?)",
                (TG_CLIENTE, NOME_CLIENTE, NOME_CLIENTE.lower(), adesso,
                 _codice_libero(con)))
    return {"nuovo": True}


def annuncio_seminato(con):
    return con.execute("SELECT id, prezzo_sats, stato FROM annunci WHERE "
                       "venditore_id=? AND titolo=? ORDER BY id LIMIT 1",
                       (TG_NEGOZIO, TITOLO_ANNUNCIO)).fetchone()


def crea_ordine(con, adesso: int, cambio_eur: float, nuovo: bool = False) -> dict:
    """L'ordine «creato, non pagato» della demo: il cliente 111 compra
    l'annuncio seminato, ritiro a mano, un pezzo, al prezzo
    dell'annuncio (niente spedizione ne' protezione: il conto E' il
    prezzo). `payment_hash` e `invoice` VUOTI, deliberato (vedi in
    testa): nessuna fattura in sats su un ordine che si paga in USDB, e
    il mietitore non guarda gli ordini senza payment_hash. La cassaforte
    e' quella del SaaS, un nome che `_chiavi_cassaforte` conosce.
    Idempotente: se c'e' gia' un 'creato' di 111 su quell'annuncio lo
    si restituisce invece di farne un altro — a meno di `nuovo`, per il
    secondo ordine della domenica."""
    a = annuncio_seminato(con)
    if not a:
        raise SeminaFerma("l'annuncio della demo non c'e': prima "
                          "`py -3 semina_demo.py`")
    if not con.execute("SELECT 1 FROM utenti WHERE tg_id=?", (TG_CLIENTE,)).fetchone():
        raise SeminaFerma("il cliente 111 non c'e': prima `py -3 semina_demo.py`")
    gia = con.execute("SELECT id, creato FROM ordini WHERE annuncio_id=? AND "
                      "compratore_id=? AND stato='creato' ORDER BY id DESC "
                      "LIMIT 1", (a[0], TG_CLIENTE)).fetchone()
    if gia and not nuovo:
        return {"nuovo": False, "id": gia[0], "creato": gia[1],
                "annuncio_id": a[0], "prezzo_sats": a[1]}
    con.execute(
        "INSERT INTO ordini(cassaforte,annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,stato,payment_hash,invoice,creato,aggiornato,cambio_ordine,"
        "consegna_scelta,quantita,spedizione_sats,protezione_sats) "
        "VALUES('saas',?,?,?,?,'creato','','',?,?,?,'ritiro',1,0,0)",
        (a[0], TG_CLIENTE, TG_NEGOZIO, a[1], adesso, adesso, cambio_eur))
    oid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {"nuovo": True, "id": oid, "creato": adesso, "annuncio_id": a[0],
            "prezzo_sats": a[1]}


def stato(con) -> dict:
    """Cosa c'e' nel database della demo, senza scrivere niente."""
    neg = con.execute("SELECT negozio, negozio_slug, npub, avatar, nome, "
                      "banner_foto, banner_link FROM utenti "
                      "WHERE tg_id=?", (TG_NEGOZIO,)).fetchone()
    cli = con.execute("SELECT nome FROM utenti WHERE tg_id=?", (TG_CLIENTE,)).fetchone()
    a = annuncio_seminato(con)
    ordini = con.execute("SELECT id, stato, prezzo_sats, creato FROM ordini WHERE "
                         "compratore_id=? AND venditore_id=? ORDER BY id",
                         (TG_CLIENTE, TG_NEGOZIO)).fetchall() if a else []
    return {"negozio": dict(zip(("codice", "slug", "npub", "avatar", "nome",
                                 "insegna", "link_insegna"), neg))
            if neg else None,
            "cliente": cli[0] if cli else None,
            "annuncio": dict(zip(("id", "prezzo_sats", "stato"), a)) if a else None,
            "ordini": [dict(zip(("id", "stato", "prezzo_sats", "creato"), o))
                       for o in ordini]}


# ============================ IL COMANDO ==================================

def _ora(t: int) -> str:
    return time.strftime("%H:%M del %d/%m", time.localtime(t)) if t else "?"


def _config():
    """Il config locale, come lo legge il server. SOLO in collaudo:
    il resto non e' un database su cui questo file abbia il diritto di
    scrivere."""
    try:
        import config
    except ImportError:
        raise SeminaFerma("manca config.py: la semina legge MODALITA_COLLAUDO "
                          "e DB da li' (copia config_esempio.py e metti "
                          "MODALITA_COLLAUDO = True)")
    if getattr(config, "MODALITA_COLLAUDO", False) is not True:
        raise SeminaFerma("MODALITA_COLLAUDO non e' True nel config: la "
                          "semina scrive SOLO su un database di collaudo")
    return config


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cambio_a_mano, db_a_mano = 0.0, ""
    while "--cambio-usd" in argv:
        i = argv.index("--cambio-usd")
        try:
            cambio_a_mano = float(argv[i + 1])
        except (IndexError, ValueError):
            print("--cambio-usd vuole un numero ($/BTC)")
            return 2
        del argv[i:i + 2]
    while "--db" in argv:
        i = argv.index("--db")
        try:
            db_a_mano = argv[i + 1]
        except IndexError:
            print("--db vuole un percorso")
            return 2
        del argv[i:i + 2]
    link_insegna = ""
    while "--insegna-link" in argv:
        i = argv.index("--insegna-link")
        try:
            link_insegna = argv[i + 1]
        except IndexError:
            print("--insegna-link vuole un indirizzo https://…")
            return 2
        if not link_insegna_valido(link_insegna):
            print("--insegna-link vuole un indirizzo https://dominio/… senza credenziali")
            return 2
        del argv[i:i + 2]
    nuovo = "--nuovo" in argv
    argv = [a for a in argv if a != "--nuovo"]
    comando = argv[0] if argv else "semina"
    if comando not in ("semina", "ordine", "stato") or len(argv) > 1:
        print(__doc__.split("USO")[1].replace("(", "USO (", 1))
        return 2
    try:
        cfg = _config()
        percorso = db_a_mano or getattr(cfg, "DB", "satmarket.db")
        if not os.path.isabs(percorso):
            percorso = os.path.join(QUI, percorso)
        if not os.path.exists(percorso):
            raise SeminaFerma(f"il database {percorso} non esiste: avvia "
                              "Barattolo una volta (lo crea lui) e rilancia")
        con = sqlite3.connect(percorso, timeout=15)
        try:
            controlla_schema(con)
            adesso = int(time.time())
            # la cartella delle foto e' quella del server, accanto al
            # codice; prove e collaudi la spostano con SEMINA_CARTELLA_FOTO
            # per non scrivere nella foto/ del repo
            cartella_foto = (os.environ.get("SEMINA_CARTELLA_FOTO")
                             or os.path.join(QUI, "foto"))
            if comando == "stato":
                return _stampa_stato(stato(con), percorso)
            if comando == "ordine":
                eur, _ = cambio_noto(con, "eur")
                o = crea_ordine(con, adesso, eur, nuovo=nuovo)
                con.commit()
                verbo = "creato" if o["nuovo"] else "c'è già"
                print(f"🧾 Ordine #{o['id']} {verbo} (cliente 111 → annuncio "
                      f"#{o['annuncio_id']}, {fmt_sats(o['prezzo_sats'])} sats, "
                      f"ritiro a mano): stato «creato», non pagato, nessuna "
                      f"fattura in sats — payment_hash vuoto, il mietitore non "
                      f"lo tocca. Nato alle {_ora(o['creato'])}."
                      + ("" if o["nuovo"] else
                         " Per un secondo ordine: `ordine --nuovo`."))
                return 0
            # --- semina ---
            with open(os.path.join(QUI, "miniapp.html"), encoding="utf-8") as f:
                codice = codice_negozio_del_client(f.read())
            usd, quando = (cambio_a_mano, adesso) if cambio_a_mano \
                else cambio_noto(con, "usd")
            if not usd:
                raise SeminaFerma("il server non ha ancora letto un cambio $/BTC "
                                  "(tabella cambio_noto vuota): lascialo acceso "
                                  "un minuto con la rete, o passa "
                                  "`--cambio-usd <dollari per bitcoin>`")
            prezzo = sats_da_usd(PREZZO_USD, usd)
            print(f"🌱 Semina della demo sul database di collaudo: {percorso}")
            n = semina_negozio(con, codice, QUI, cartella_foto, adesso,
                               link_insegna)
            print(f"   ✓ negozio {NOME_NEGOZIO} ({'nuovo' if n['nuovo'] else 'c’era'}): "
                  f"utente {TG_NEGOZIO}, codice {codice} (dal catalogo del client), "
                  f"/negozio/{SLUG_NEGOZIO}, npub {NPUB_NEGOZIO[:12]}…"
                  + (f", avatar {n['avatar']}" if n["avatar"] else
                     ", senza avatar (Pillow o il logo mancano)"))
            if not n["insegna"]:
                print("   · senza insegna (Pillow o il banner di assets/scoprire/ mancano)")
            else:
                leva = getattr(cfg, "BANNER_NEGOZIO_ATTIVO", False) is True
                print(f"   {'✓' if n['link_insegna'] and leva else '⚠️'} insegna "
                      f"{n['insegna']} (stato attivo)"
                      + (f", link {n['link_insegna']}" if n["link_insegna"] else
                         " — SENZA LINK il client non la mostra: "
                         "`--insegna-link https://<sito del negozio>`")
                      + ("" if leva else
                         "; e BANNER_NEGOZIO_ATTIVO non è True nel config: "
                         "resta nascosta"))
            nomi = getattr(cfg, "NIP05_NOMI", None) or {}
            hex_attesa = npub_in_hex(NPUB_NEGOZIO)
            if isinstance(nomi, dict) and nomi.get(NIP05_NOME):
                combacia = str(nomi[NIP05_NOME]).lower() == hex_attesa
                print(f"   {'✓' if combacia else '⚠️'} NIP05_NOMI['{NIP05_NOME}'] nel "
                      f"config {'combacia con' if combacia else 'NON combacia con'} "
                      f"la npub seminata")
            else:
                print(f"   · NIP05_NOMI['{NIP05_NOME}'] non e' nel config: "
                      f"/.well-known/nostr.json non lo risponde (le hex le da' "
                      f"`node identita.mjs pubblica tothemooon`)")
            a = semina_annuncio(con, prezzo, QUI, cartella_foto, adesso)
            cambio_riga = (f"{fmt_usd(PREZZO_USD)} $ al cambio di "
                           f"{fmt_sats(int(usd))} $/BTC"
                           + (" (a mano)" if cambio_a_mano else
                              f" letto dal server alle {_ora(quando)}"))
            if a["nuovo"]:
                print(f"   ✓ annuncio #{a['id']} «{TITOLO_ANNUNCIO}» nuovo: "
                      f"{fmt_sats(prezzo)} sats = {cambio_riga}, ritiro a mano a "
                      f"{ZONA}, {len(a['foto'])} foto")
            else:
                ritocchi = []
                if a["prezzo_prima"] != prezzo:
                    ritocchi.append(f"prezzo {fmt_sats(a['prezzo_prima'])} → "
                                    f"{fmt_sats(prezzo)} sats")
                if a["stato_prima"] != "attivo":
                    ritocchi.append(f"stato {a['stato_prima']} → attivo")
                if a["pezzi_prima"] != 1:
                    ritocchi.append(f"pezzi {a['pezzi_prima']} → 1")
                print(f"   ✓ annuncio #{a['id']} «{TITOLO_ANNUNCIO}» c’era: "
                      f"{fmt_sats(prezzo)} sats = {cambio_riga}"
                      + (" — ritoccato: " + ", ".join(ritocchi) if ritocchi
                         else " — niente da ritoccare"))
            c = semina_cliente(con, adesso)
            print(f"   ✓ cliente {TG_CLIENTE} {'nuovo' if c['nuovo'] else 'c’era'}: "
                  f"pronto a comprare (identita' dall'hash: "
                  f"tgWebAppData=collaudo:{TG_CLIENTE}:{NOME_CLIENTE})")
            con.commit()
            print("   Rilanciabile: niente doppioni. L'ordine della mattina: "
                  "`py -3 semina_demo.py ordine`.")
            return 0
        finally:
            con.close()
    except SeminaFerma as e:
        print(f"⛔ Semina ferma: {e}")
        return 1


def _stampa_stato(s: dict, percorso: str) -> int:
    print(f"🔎 Database {percorso}")
    if s["negozio"]:
        n = s["negozio"]
        print(f"   negozio {n['nome']}: codice {n['codice']}, /negozio/{n['slug']}, "
              f"npub {n['npub'][:12]}…, avatar {n['avatar'] or '—'}, "
              f"insegna {n['insegna'] or '—'}"
              + (f" → {n['link_insegna']}" if n["link_insegna"] else " (senza link)"))
    else:
        print("   negozio: non seminato")
    print(f"   cliente 111: {s['cliente'] or 'non c’è'}")
    if s["annuncio"]:
        a = s["annuncio"]
        print(f"   annuncio #{a['id']}: {fmt_sats(a['prezzo_sats'])} sats, {a['stato']}")
    else:
        print("   annuncio: non seminato")
    for o in s["ordini"]:
        print(f"   ordine #{o['id']}: {o['stato']}, {fmt_sats(o['prezzo_sats'])} sats, "
              f"nato alle {_ora(o['creato'])}")
    if not s["ordini"]:
        print("   ordini: nessuno")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
