"""Il catalogo di un e-commerce diventa annunci di Barattolo.

IL GEMELLO DI `importa_nostr.py`, e la parentela e' voluta: e' lo
stesso mestiere — leggere un catalogo che vive FUORI e tenerlo in pari
qui — con le stesse tre idee portanti (il match su una chiave stabile,
lo scudo anti-resurrezione, «cio' che la fonte non dichiara non si
inventa»). Cambia da dove arrivano i dati e chi li firma.

MA QUESTO FILE NON GIRA DA SOLO, ed e' la differenza da capire prima
di toccarlo: `importa_nostr.py` ha un `main()` perche' la npub sta nel
config ed e' PUBBLICA — chiunque puo' rileggere quegli eventi. Qui le
credenziali sono token di un sistema altrui, vivono cifrate nel
database e non devono passare da nessun config in chiaro. Quindi niente
`main()`, e le colonne nuove si danno per esistenti (le crea `init_db`
del server, che e' l'unico a chiamarci).

IL PATTO DELLE FUNZIONI INIETTATE, lo stesso del `vaglio` di Nostr:
qui dentro non c'e' NESSUNA chiamata di rete e nessuna scrittura di
file. Il trasporto HTTP (`chiama`), lo scaricatore delle foto
(`salva_foto`) e il cambio arrivano dal server, che ha le guardie —
anti-SSRF, tetti, timeout, la filiera della compressione unica. Cosi'
i traduttori e la riconciliazione restano PURI, cioe' collaudabili in
`prove.py` con un catalogo di cartone.
"""
import base64
import json
import re
import sqlite3
import time

# La versione dell'API Shopify vive in una COSTANTE e non dentro gli
# URL: quelle date hanno un ciclo di deprecazione (Shopify ne ritira
# una ogni anno), e il giorno che va alzata dev'esserci UN posto da
# toccare, non sei stringhe sparse.
VERSIONE_API_SHOPIFY = "2024-07"

# Il gemello di Woo. WooCommerce vive dentro WordPress, quindi la
# versione sta nel PERCORSO (`/wp-json/wc/v3/`) e non in una data:
# la v3 e' ferma dal 2018 e non ha un ciclo di ritiro annunciato.
VERSIONE_API_WOO = "wc/v3"

# Quanto si legge in un colpo. 250 e' il massimo che Shopify concede
# per pagina; il tetto vero al giro lo mette il server
# (MAX_PRODOTTI_CONNETTORE), che sa quanto puo' tenere occupato
# l'orologio.
PER_PAGINA = 250

# WordPress ne concede 100 e non 250, ed e' un tetto SUO: chiederne di
# piu' non fa una pagina piu' grande, fa un 400.
PER_PAGINA_WOO = 100

# I tagli del testo, IDENTICI alle colonne del database. Non sono un
# gusto: sono la ragione per cui `testo_negozio` esiste (vedi sotto).
MAX_TITOLO = 120
MAX_DESCRIZIONE = 1500

# Quante foto si tengono per annuncio: la stessa misura del form e
# dell'import CSV.
MAX_FOTO = 5

# Quel che si dice al venditore quando il catalogo non ci sta nel
# tetto di lettura, e la seconda meta' e' quella che prima MANCAVA: la
# frase di ieri prometteva «il resto arriva ai giri successivi», ed
# era falsa — nessuno dei due lettori tiene un cursore fra un giro e
# l'altro, quindi ogni ora si rilegge da pagina 1 e si taglia allo
# stesso punto. Il resto non arrivava mai: veniva letto, tagliato e
# (prima della cura) spento.
# UN POSTO SOLO per i due lettori: due frasi che dicono la stessa cosa
# sono due frasi che un giorno dicono cose diverse.
MSG_TRONCATO_CODA = (
    ": gli altri non entrano, e finche' e' cosi' non spegniamo qui i "
    "prodotti che togli dal negozio — non sapremmo distinguerli da "
    "quelli che non abbiamo letto"
)


def _msg_troncato(tetto: int, totale: int = 0) -> str:
    """La testa cambia, la coda no. Il conto VERO si dice quando c'e'
    (Woo lo mette in `X-WP-Total`), perche' «ne hai 250 e ne leggiamo
    200» si capisce e «ne hai piu' di 200» si subisce; ma la parte che
    NON puo' mancare in nessuno dei due casi e' la seconda."""
    testa = (f"il tuo negozio ha {totale} prodotti e ne leggiamo "
             f"{tetto} per volta" if totale else
             f"il tuo catalogo ha piu' di {tetto} prodotti")
    return testa + MSG_TRONCATO_CODA


# --- IL TESTO CANONICO ------------------------------------------------

def _spoglia_html(testo: str) -> str:
    """La descrizione di un prodotto arriva in HTML (`body_html` su
    Shopify, `description` su Woo). Qui diventa testo piano UNA volta
    sola, e il punto e' proprio «una volta»: se a spogliarlo fosse chi
    scrive nel database e non anche chi lo GIUDICA, la moderazione
    leggerebbe un testo e la vetrina un altro — cioe' l'impronta non
    combacerebbe mai e ogni giro ripagherebbe l'AI per dire la stessa
    cosa.
    Niente parser: si tolgono i tag, si rendono i «a capo» dei
    paragrafi e si sciolgono le poche entita' che contano. Un
    e-commerce scrive HTML semplice, e una libreria in piu' per
    guadagnare le virgolette tipografiche non vale la dipendenza."""
    if not testo:
        return ""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", testo)
    # i tag che vanno a capo davvero: il resto sparisce senza lasciare
    # traccia, o le parole si incollerebbero fra loro
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", t)
    t = re.sub(r"(?i)<li[^>]*>", "· ", t)
    # i tag INLINE spariscono senza lasciare spazio, o un
    # «<b>a mano</b>.» diventerebbe «a mano .» — il grassetto sta in
    # mezzo a una frase, non fra due frasi
    t = re.sub(r"(?i)</?(b|strong|i|em|u|s|span|a|small|code|sup|sub)"
               r"(\s[^>]*)?>", "", t)
    t = re.sub(r"<[^>]+>", " ", t)
    for entita, segno in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                          ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"),
                          ("&apos;", "'"), ("&euro;", "€")):
        t = t.replace(entita, segno)
    # gli spazi si collassano, i capoversi restano (al massimo uno)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    # e lo spazio davanti alla punteggiatura, che i tag lasciano dietro
    t = re.sub(r" +([.,;:!?])", r"\1", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()


def testo_negozio(prodotto: dict, fonte: str) -> tuple[str, str]:
    """Titolo e descrizione come finiranno nel database, troncati.

    IL CUORE CONDIVISO fra chi scrive e chi giudica — il gemello di
    `testo_evento`, e vale la stessa lezione: se i due divergessero,
    un prodotto fermo sembrerebbe cambiato a ogni giro (e si
    ripagherebbe la moderazione per sempre), oppure — peggio — uno
    cambiato sembrerebbe fermo e il testo nuovo entrerebbe in vetrina
    senza che nessuno l'abbia guardato."""
    if fonte == "woo":
        titolo = prodotto.get("name") or ""
        grezza = prodotto.get("description") or prodotto.get(
            "short_description") or ""
    else:
        titolo = prodotto.get("title") or ""
        grezza = prodotto.get("body_html") or ""
    desc = _spoglia_html(grezza)
    # il trattino e' il ripiego di casa per la descrizione vuota
    return titolo.strip()[:MAX_TITOLO], (desc or "—")[:MAX_DESCRIZIONE]


# --- I TRADUTTORI -----------------------------------------------------
# Ognuno prende un prodotto COME L'API LO DA' e restituisce la RIGA
# NORMALIZZATA che la riconciliazione sa scrivere. Sono l'unico posto
# che conosce la forma di Shopify o di Woo: aggiungere una terza
# piattaforma vuol dire scrivere un traduttore e nient'altro.
#
# Una riga saltata NON e' un errore: torna col suo `saltato_perche`, e
# il report lo dice al venditore. Un catalogo dove tre prodotti su
# quaranta non passano dev'essere un catalogo con trentasette annunci
# e tre righe di spiegazione, mai un giro fallito.

def _sats_da_eur(eur: float, cambio: dict) -> int | None:
    """L'equivalente in sats di un prezzo in euro, con la RICETTA DEL
    SERVER (`prezzo_da_payload`): stesso arrotondamento e stesso
    pavimento a 1 sat. Se le due divergessero, la vetrina direbbe una
    cifra e la fattura un'altra.
    `None` quando il cambio non c'e': il chiamante salta la riga
    invece di inventare un numero — e' la regola dell'avviso EUR
    («meglio un match perso che uno sbagliato»)."""
    tasso = (cambio or {}).get("EUR") or 0
    if tasso <= 0 or eur <= 0:
        return None
    return max(1, round(eur / tasso * 1e8))


def _numero(v) -> float:
    """I prezzi arrivano come stringhe ('7.50'), a volte con la
    virgola, a volte vuoti o nulli."""
    if v is None:
        return 0.0
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return 0.0


def traduci_shopify(p: dict, cambio: dict) -> dict:
    """Un prodotto Shopify diventa una riga normalizzata."""
    riga = {"origine_chiave": str(p.get("id") or ""),
            "saltato_perche": "", "titolo": "", "descrizione": "",
            "prezzo_eur": 0.0, "prezzo_sats": 0, "quantita": None,
            "foto": [], "categoria_grezza": "", "attivo": True}
    titolo, descrizione = testo_negozio(p, "shopify")
    riga["titolo"], riga["descrizione"] = titolo, descrizione
    if not riga["origine_chiave"] or not titolo:
        riga["saltato_perche"] = "senza id o senza titolo"
        return riga
    varianti = p.get("variants") or []
    # ATTENZIONE, la trappola di Shopify: un prodotto ha SEMPRE almeno
    # una variante, anche quando nel pannello non se ne vede nessuna —
    # quella e' la variante «di default». Quindi il salto guarda `> 1`,
    # e un prodotto normale non ci cade mai.
    if len(varianti) > 1:
        riga["saltato_perche"] = f"ha {len(varianti)} varianti"
        return riga
    if not varianti:
        riga["saltato_perche"] = "senza prezzo"
        return riga
    v = varianti[0]
    riga["prezzo_eur"] = round(_numero(v.get("price")), 2)
    sats = _sats_da_eur(riga["prezzo_eur"], cambio)
    if not sats:
        riga["saltato_perche"] = ("senza prezzo" if riga["prezzo_eur"] <= 0
                                  else "cambio non disponibile")
        return riga
    riga["prezzo_sats"] = sats
    # LO STOCK NON TRACCIATO NON E' ZERO, ed e' la riga da non
    # ammorbidire: chi non fa gestire il magazzino a Shopify vende
    # senza contare i pezzi, e scriverci 0 spegnerebbe il suo catalogo
    # intero al primo giro. `None` = «non lo sappiamo», e la
    # riconciliazione lascia stare la colonna.
    if v.get("inventory_management"):
        riga["quantita"] = int(v.get("inventory_quantity") or 0)
    # la coordinata che servira' al decremento (fase 2). Si LEGGE gia'
    # adesso perche' costa zero e sta nella stessa risposta, ma non si
    # scrive da nessuna parte finche' quella fase non esiste.
    riga["scorta"] = str(v.get("inventory_item_id") or "")
    riga["foto"] = [i.get("src") for i in (p.get("images") or [])
                    if i.get("src")][:MAX_FOTO]
    riga["categoria_grezza"] = (p.get("product_type") or "").strip() or \
        (p.get("tags") or "").split(",")[0].strip()
    # draft e archived non sono in vetrina sul suo negozio: non devono
    # esserlo nemmeno qui
    riga["attivo"] = (p.get("status") or "active") == "active"
    return riga


# I TIPI DI PRODOTTO WOO CHE NON SAPPIAMO TRATTARE, e ognuno col suo
# perche' scritto: un annuncio di Barattolo e' UNA cosa con UN prezzo
# e UNA giacenza, e questi tre non lo sono.
# · `variable` e' il gemello del multi-variante di Shopify (taglie,
#   colori: `annunci` e' piatto, e le varianti sono un cantiere loro);
# · `grouped` e' un contenitore che rimanda ad altri prodotti e un
#   prezzo suo non ce l'ha;
# · `external` e' il prodotto in affiliazione: il bottone porta su un
#   ALTRO sito, quindi comprarlo qui non vorrebbe dire niente — ed e'
#   quello che si dimentica, perche' un prezzo ce l'ha.
SALTI_WOO = {"variable": "ha piu' varianti",
             "grouped": "e' un gruppo di prodotti",
             "external": "si compra su un altro sito"}


def traduci_woo(p: dict, cambio: dict) -> dict:
    """Un prodotto WooCommerce diventa una riga normalizzata.

    IL PREZZO SI LEGGE COM'E', ed e' la riga che regge su una
    promessa fatta a monte: `leggi_catalogo_woo` ha gia' chiesto al
    negozio se i suoi prezzi sono quelli che si pagano (vedi
    `prezzi_finiti_woo`) e ha ALZATO se non lo erano. Qui non si
    corregge nessuna IVA e non si indovina nessuna aliquota — se un
    domani qualcuno togliesse quel controllo, questa funzione
    comincerebbe a scrivere in vetrina un prezzo che non e' il prezzo
    di nessuno, in silenzio."""
    riga = {"origine_chiave": str(p.get("id") or ""),
            "saltato_perche": "", "titolo": "", "descrizione": "",
            "prezzo_eur": 0.0, "prezzo_sats": 0, "quantita": None,
            "foto": [], "categoria_grezza": "", "attivo": True}
    titolo, descrizione = testo_negozio(p, "woo")
    riga["titolo"], riga["descrizione"] = titolo, descrizione
    if not riga["origine_chiave"] or not titolo:
        riga["saltato_perche"] = "senza id o senza titolo"
        return riga
    tipo = str(p.get("type") or "simple").lower()
    if tipo in SALTI_WOO:
        riga["saltato_perche"] = SALTI_WOO[tipo]
        return riga
    # `price` e' gia' il prezzo EFFICACE (lo sconto, se c'e'); il
    # `regular_price` e' il ripiego per i temi che lasciano `price`
    # vuoto sui prodotti mai visitati.
    riga["prezzo_eur"] = round(
        _numero(p.get("price") or p.get("regular_price")), 2)
    sats = _sats_da_eur(riga["prezzo_eur"], cambio)
    if not sats:
        riga["saltato_perche"] = ("senza prezzo" if riga["prezzo_eur"] <= 0
                                  else "cambio non disponibile")
        return riga
    riga["prezzo_sats"] = sats
    # --- LA GIACENZA, e qui c'e' la trappola gemella della variante di
    # default di Shopify: `manage_stock` non e' un booleano, puo'
    # essere la STRINGA 'parent' — le varianti che ereditano il
    # magazzino dal prodotto padre — e in Python quella stringa e'
    # VERA. Il confronto e' quindi col VALORE e non con la verita':
    # scritto `if p.get("manage_stock"):` si scriverebbe qui la
    # giacenza di un ALTRO prodotto (quella del padre), oppure, col
    # numero assente, si alzerebbe su `int(None)` — una riga persa nel
    # report invece di un annuncio.
    gestito = p.get("manage_stock")
    scorte = p.get("stock_quantity")
    if gestito in (True, 1) and scorte is not None:
        riga["quantita"] = int(scorte)
    elif str(p.get("stock_status") or "") == "outofstock":
        # NON gestisce il magazzino ma dichiara «esaurito»: quello e'
        # un fatto, non un'assenza, e vale zero. Il rovescio —
        # 'onbackorder' — resta IGNOTO apposta: sul suo negozio quel
        # prodotto si compra, e scriverci zero lo spegnerebbe qui.
        riga["quantita"] = 0
    riga["foto"] = [i.get("src") for i in (p.get("images") or [])
                    if isinstance(i, dict) and i.get("src")][:MAX_FOTO]
    categorie = [c.get("name") for c in (p.get("categories") or [])
                 if isinstance(c, dict) and c.get("name")]
    riga["categoria_grezza"] = (categorie[0] if categorie else "").strip()
    # DUE DOMANDE E NON UNA: `status` dice se e' pubblicato (draft,
    # pending e private non sono in vetrina da lui), `catalog_
    # visibility` se si vede nel negozio — un prodotto 'publish' ma
    # 'hidden' e' roba che tiene fuori dallo scaffale apposta.
    riga["attivo"] = (str(p.get("status") or "publish") == "publish" and
                      str(p.get("catalog_visibility") or "visible")
                      != "hidden")
    # la coordinata del decremento (fase 2): su Woo si scrive sul
    # prodotto stesso, non su una riga di magazzino a parte. Si legge
    # gia' adesso perche' costa zero, e non si scrive da nessuna parte
    # finche' quella fase non esiste.
    riga["scorta"] = str(p.get("id") or "")
    return riga


TRADUTTORI = {"shopify": traduci_shopify, "woo": traduci_woo}


def traduci(prodotti: list, fonte: str, cambio: dict) -> list:
    """Il dispatch: una lista di prodotti diventa una lista di righe
    normalizzate. Chi aggiunge una piattaforma aggiunge una voce a
    TRADUTTORI e non tocca nient'altro."""
    tr = TRADUTTORI.get(fonte)
    if not tr:
        return []
    return [tr(p, cambio) for p in prodotti if isinstance(p, dict)]


# --- LA LETTURA DEL CATALOGO ------------------------------------------
# `chiama(metodo, url, intestazioni)` la passa il server: torna
# `(stato, corpo_json, intestazioni_risposta)` oppure alza. Qui dentro
# c'e' solo la PAGINAZIONE, che e' la parte che cambia da una
# piattaforma all'altra ed e' anche quella che si sbaglia.

_HOST_HTTPS = re.compile(r"https://([A-Za-z0-9.-]+)(?:[:/?#]|$)")


def _host_di(url: str) -> str:
    """L'host di un indirizzo https, minuscolo, o '' se non lo e'.
    Con una regex e non con `urllib.parse`, che qui dentro non entra
    (il patto del modulo puro: nessun import che sappia di rete)."""
    m = _HOST_HTTPS.match(str(url or "").strip())
    return m.group(1).lower() if m else ""


def _prossima_pagina_shopify(intestazioni: dict) -> str:
    """Shopify pagina col header `Link`, non con un numero:
    `<https://...page_info=abc>; rel="next"`. Va letto cosi' e non
    ricostruito a mano — il `page_info` e' opaco e la sua vita e'
    breve."""
    link = ""
    for k, v in (intestazioni or {}).items():
        if k.lower() == "link":
            link = v or ""
            break
    for pezzo in link.split(","):
        if 'rel="next"' in pezzo:
            m = re.search(r"<([^>]+)>", pezzo)
            if m:
                return m.group(1)
    return ""


def leggi_catalogo_shopify(dominio: str, credenziali: dict, chiama,
                           tetto: int = 200) -> tuple[list, str]:
    """Il catalogo, pagina per pagina. Torna `(prodotti, avviso)`:
    l'avviso non e' un errore ma una cosa da dire al venditore — oggi
    solo «il catalogo e' piu' grande del tetto, il resto al prossimo
    giro».

    ALZA se la chiamata fallisce, e non torna una lista vuota: le due
    cose sono diverse e confonderle sarebbe il guasto peggiore di
    questo file — un catalogo che non si e' potuto LEGGERE, preso per
    un catalogo VUOTO, spegnerebbe tutti gli annunci del venditore
    (vedi `riconcilia_connettore`, che sulle sparizioni si fida).

    IL SECONDO ARGOMENTO E' LA BUSTA INTERA delle credenziali e non il
    token, ed e' il cambio della tappa 3: Shopify ne ha una sola, Woo
    ne ha due (chiave e segreto), e ogni lettore si prende quel che
    gli serve. Con `token` nella firma il server avrebbe dovuto sapere
    che forma hanno le credenziali di ogni piattaforma — cioe' la
    stessa cosa che i traduttori esistono per non far sapere a
    nessuno."""
    prodotti = []
    atteso = str(dominio or "").strip().lower()
    url = (f"https://{dominio}/admin/api/{VERSIONE_API_SHOPIFY}"
           f"/products.json?limit={PER_PAGINA}")
    intestazioni = {"X-Shopify-Access-Token":
                    (credenziali or {}).get("token", "")}
    while url and len(prodotti) < tetto:
        stato, corpo, risposta = chiama("GET", url, intestazioni)
        if stato != 200:
            raise RuntimeError(f"Shopify ha risposto {stato}")
        prodotti.extend((corpo or {}).get("products") or [])
        # L'INDIRIZZO DELLA PAGINA DOPO LO SCRIVE IL NEGOZIO, e qui il
        # cursore e' opaco: non si puo' comporre, si puo' solo seguire
        # — quindi si lega all'HOST DEL COLLEGAMENTO. E' la stessa
        # regola scritta per Woo, dove viene gratis perche' li' le
        # pagine si numerano. Senza, chi risponde su quel dominio puo'
        # far bussare il server a un host qualunque con in mano il
        # token di quel negozio: il guardiano del trasporto ferma gli
        # indirizzi privati, non gli estranei pubblici.
        # E ALZA, non si ferma: fermarsi vorrebbe dire consegnare alla
        # riconciliazione un catalogo LETTO A META', che sulle
        # sparizioni si fida — cioe' spegnere gli annunci non visti.
        prossima = _prossima_pagina_shopify(risposta)
        if prossima and _host_di(prossima) != atteso:
            raise RuntimeError(
                "la pagina successiva punta a un altro indirizzo")
        url = prossima
    # NIENTE TETTI IN SILENZIO: il gemello Woo lo pagava per davvero, e
    # qui la stessa forma era LATENTE — regge solo perche' la pagina e'
    # da 250 e il tetto 200, quindi il confronto scatta; alzando
    # MAX_PRODOTTI_CONNETTORE a 250 si atterrerebbe esatti sul tetto e
    # il catalogo si troncherebbe senza dirlo. Qui il conto esatto non
    # serve: se dopo il ciclo un `url` c'e' ancora, c'e' ANCORA UNA
    # PAGINA — lo dice Shopify stesso nel suo header.
    # E IL TRONCAMENTO SI DICHIARA COME FATTO, non come prosa: e' il
    # terzo valore della tupla, e senza di lui questa funzione mentiva
    # al suo unico lettore. Il commento delle sparizioni dice «il
    # chiamante non deve mai arrivare qui con una lettura parziale», e
    # la difesa costruita era che una lettura fallita ALZA — ma il
    # tetto NON alza: torna una lista corta, cioe' produce esattamente
    # la lettura parziale che quel commento teme, e i prodotti oltre
    # il tetto venivano spenti per sempre.
    completo = not url and len(prodotti) <= tetto
    avviso = "" if completo else _msg_troncato(tetto)
    return prodotti[:tetto], avviso, completo


# --- WOOCOMMERCE ------------------------------------------------------
# La differenza che decide tutto il resto: il negozio Shopify vive su
# `nome.myshopify.com` — un dominio di un'azienda sola, normalizzato al
# collegamento — mentre L'INDIRIZZO DI UN WOO LO SCRIVE L'UTENTE e puo'
# essere qualunque cosa. Da li' le tre righe da non ammorbidire:
#
#  1. LA GUARDIA STA NEL TRASPORTO, cioe' in `url_api_ammesso` dentro
#     `chiama_api_negozio`, e gira su OGNI chiamata — non solo sulla
#     prima. E' il server ad averla, non questo modulo (qui non c'e'
#     rete, e' il patto del `vaglio`): quindi ogni lettore futuro la
#     eredita senza doversene ricordare.
#  2. QUI DENTRO GLI URL SI COSTRUISCONO, MAI SI SEGUONO. Shopify
#     pagina con un cursore opaco e l'indirizzo della pagina dopo lo
#     scrive LUI nell'header `Link`; Woo pagina con un numero, quindi
#     l'indirizzo lo componiamo noi dal `url_negozio` del collegamento
#     e non c'e' NESSUN modo che il negozio ci mandi altrove — cioe'
#     che si faccia consegnare le chiavi di un altro a un host che non
#     abbiamo mai giudicato.
#  3. `_base_woo` e' la cintura di forma: rifiuta tutto quello che non
#     e' `https://host[/percorso]`. Non sostituisce la guardia del
#     server — non risolve nessun nome e non sa niente di indirizzi
#     privati — ma impedisce che da qui esca un URL con dentro una
#     porta, una query o delle credenziali (`https://ck:cs@vero.it`,
#     l'inganno visivo di `link_banner_ammesso`).

_FORMA_BASE_WOO = re.compile(r"https://[A-Za-z0-9.-]+(/[A-Za-z0-9._~-]+)*")


def _base_woo(url_negozio: str) -> str:
    """L'indirizzo del negozio, ripulito, o alza.

    Il percorso e' ammesso apposta: parecchi Woo vivono in una
    sottocartella (`https://sito.it/shop`), e pretendere la radice
    taglierebbe fuori negozi veri."""
    base = str(url_negozio or "").strip().rstrip("/")
    if not _FORMA_BASE_WOO.fullmatch(base):
        raise RuntimeError(
            "l'indirizzo del negozio non e' un https:// che sappiamo "
            "chiamare")
    return base


def _intestazioni_woo(credenziali: dict) -> dict:
    """Le chiavi di WooCommerce viaggiano in BASIC AUTH e mai in
    query string, che e' l'altra strada che la sua documentazione
    concede: un segreto in un URL finisce nei log di ogni proxy che
    sta in mezzo, e per giunta nei nostri se un domani qualcuno
    stampasse l'indirizzo di una chiamata fallita."""
    ck = str((credenziali or {}).get("consumer_key") or "")
    cs = str((credenziali or {}).get("consumer_secret") or "")
    if not ck or not cs:
        raise RuntimeError("mancano le chiavi del negozio")
    coppia = base64.b64encode(f"{ck}:{cs}".encode()).decode()
    return {"Authorization": f"Basic {coppia}"}


def _valore_impostazione(corpo, chiave: str):
    """Il valore di una impostazione dentro la risposta di
    `/settings/{gruppo}`, che e' una LISTA di voci `{id, value, ...}`.

    Torna `None` quando non si trova, e la differenza con la stringa
    vuota e' tutto il punto: chi chiama tratta il `None` come «non lo
    sappiamo» e si ferma, invece di prendere un'assenza per una
    risposta.
    ATTENZIONE alla forma che arriva: il trasporto del server incarta
    le liste in `{"lista": [...]}` (`_json_o_niente`), quindi qui si
    accettano tutt'e due — e anche la voce singola, che e' quel che
    risponde `/settings/{gruppo}/{id}`."""
    voci = corpo
    if isinstance(corpo, dict):
        voci = corpo.get("lista")
        if voci is None:
            voci = [corpo] if corpo.get("id") else []
    for v in voci or []:
        if isinstance(v, dict) and v.get("id") == chiave:
            valore = v.get("value")
            return "" if valore is None else str(valore)
    return None


MSG_IVA_ESCLUSA = (
    "i prezzi del tuo negozio sono scritti al NETTO dell'IVA: "
    "cosi' non sappiamo quanto si paga davvero. Su WooCommerce, "
    "Impostazioni → Tasse → «Prezzi inseriti con le tasse»")
MSG_IVA_IGNOTA = (
    "non riusciamo a sapere come sono scritti i prezzi del tuo "
    "negozio (le impostazioni non rispondono): il catalogo aspetta")


def prezzi_finiti_woo(base: str, intestazioni: dict, chiama) -> None:
    """Il prezzo di un prodotto Woo E' quello che si paga? Se non lo
    e', o non lo sappiamo, si ALZA e il catalogo non si legge.

    E' LA DOMANDA PIU' IMPORTANTE DI QUESTA TAPPA, e la ragione e'
    che WooCommerce non la risponde nel prodotto: `price` e' la cifra
    COM'E' STATA SCRITTA nel pannello, e se il negozio e' configurato
    «prezzi inseriti SENZA le tasse» quella cifra e' il netto — cioe'
    su un'aliquota al 22% importeremmo in vetrina un prezzo piu' basso
    del 18% di quello che sul suo sito il cliente paga davvero. Il
    venditore lo scoprirebbe incassando, che e' il modo peggiore.
    L'ALIQUOTA NON SI INDOVINA: dipende dalla classe di tassazione del
    prodotto e dal paese di chi compra (`/taxes` ne restituisce una
    tabella, non un numero), quindi correggere a mano vorrebbe dire
    scrivere un prezzo che non e' il suo — ed e' esattamente quel che
    questo progetto non fa mai col denaro.

    PERCHE' ALZA INVECE DI SALTARE LE RIGHE, ed e' la riga da capire
    prima di toccarla: una riga saltata NON entra in `viste`, quindi
    la riconciliazione la tratterebbe come sparita dal negozio e la
    SPEGNEREBBE. Saltare tutto il catalogo vorrebbe dire spegnere la
    vetrina di quel venditore in un colpo. Un catalogo di cui non
    sappiamo leggere i prezzi e' un catalogo che NON SI E' POTUTO
    LEGGERE — la stessa cosa di una rete caduta — e il giro lo tratta
    cosi': si conta l'errore, la vetrina resta com'era, e il motivo
    vero finisce in `ultimo_errore`, dove il venditore lo legge.

    FAIL-CLOSED su cio' che non si sa, come `importo_invoice`: fra un
    connettore che non parte (visibile, diagnosticabile, zero danno) e
    dei prezzi forse sbagliati del 22% su cose che si comprano, si
    sceglie il primo.

    LA PORTA CHE MANCA, dichiarata: chi vende al netto apposta (i
    negozi B2B) oggi resta fuori. La leva sarebbe un'aliquota
    dichiarata dal venditore nel cassetto del collegamento — una
    colonna e un campo, cioe' roba della tappa 5 — e finche' non c'e'
    non si aggiunge una colonna per una cosa che non esiste."""
    stato, corpo, _ = chiama(
        "GET", f"{base}/wp-json/{VERSIONE_API_WOO}/settings/general",
        intestazioni)
    if stato != 200:
        raise RuntimeError(MSG_IVA_IGNOTA)
    tasse = _valore_impostazione(corpo, "woocommerce_calc_taxes")
    if tasse is None:
        raise RuntimeError(MSG_IVA_IGNOTA)
    if tasse != "yes":
        return          # le tasse sono spente: il prezzo e' quel che e'
    stato, corpo, _ = chiama(
        "GET", f"{base}/wp-json/{VERSIONE_API_WOO}/settings/tax",
        intestazioni)
    if stato != 200:
        raise RuntimeError(MSG_IVA_IGNOTA)
    incluse = _valore_impostazione(corpo, "woocommerce_prices_include_tax")
    if incluse is None:
        raise RuntimeError(MSG_IVA_IGNOTA)
    if incluse != "yes":
        raise RuntimeError(MSG_IVA_ESCLUSA)


def _quanti_in_tutto(intestazioni) -> int:
    """Quanti prodotti ha il negozio, secondo lui: WordPress lo dice
    in `X-WP-Total` su ogni pagina. 0 = non l'ha detto.
    Le chiavi si confrontano in minuscolo perche' un header non ha un
    maiuscolo canonico (la lezione di `_prossima_pagina_shopify`)."""
    for k, v in (intestazioni or {}).items():
        if str(k).lower() == "x-wp-total":
            try:
                return int(str(v).strip())
            except ValueError:
                return 0
    return 0


def _prodotti_dalla_risposta(corpo) -> list:
    """WooCommerce risponde con una lista nuda; il trasporto del
    server la incarta in `{"lista": [...]}`. Si accettano tutt'e due,
    e si tiene solo cio' che e' un prodotto."""
    voci = corpo
    if isinstance(corpo, dict):
        voci = corpo.get("lista") or []
    return [p for p in (voci or []) if isinstance(p, dict)]


def leggi_catalogo_woo(url_negozio: str, credenziali: dict, chiama,
                       tetto: int = 200) -> tuple[list, str]:
    """Il catalogo di un WooCommerce, pagina per pagina.

    ALZA come il gemello Shopify, e per la stessa ragione: le
    sparizioni si giudicano solo su un catalogo COMPLETO, quindi una
    lettura a meta' non deve MAI tornare come una lista corta.

    L'ORDINE E' PER ID CRESCENTE e non e' un vezzo: il default di
    WooCommerce e' la data di pubblicazione, e con quello basta che il
    venditore ritocchi un prodotto mentre stiamo paginando perche' una
    riga scivoli fra due pagine e non la si veda — cioe' un prodotto
    dichiarato sparito e spento per sbaglio. L'id non si muove."""
    base = _base_woo(url_negozio)
    intestazioni = _intestazioni_woo(credenziali)
    prezzi_finiti_woo(base, intestazioni, chiama)
    prodotti, pagina, restano = [], 1, False
    totale = 0
    while True:
        url = (f"{base}/wp-json/{VERSIONE_API_WOO}/products"
               f"?per_page={PER_PAGINA_WOO}&page={pagina}"
               f"&orderby=id&order=asc")
        stato, corpo, risposta = chiama("GET", url, intestazioni)
        if stato != 200:
            raise RuntimeError(f"WooCommerce ha risposto {stato}")
        totale = totale or _quanti_in_tutto(risposta)
        fetta = _prodotti_dalla_risposta(corpo)
        prodotti.extend(fetta)
        # la pagina corta e' la fine: WordPress non ha un cursore, e
        # chiedere la pagina dopo l'ultima risponde 400
        if len(fetta) < PER_PAGINA_WOO:
            break
        if len(prodotti) >= tetto:
            # ci si ferma perche' il tetto e' arrivato, non perche' il
            # catalogo e' finito: l'ultima pagina era PIENA
            restano = True
            break
        pagina += 1
    # NIENTE TETTI IN SILENZIO, ed e' un difetto vero preso provando e
    # non leggendo: con cento prodotti per pagina e un tetto di
    # duecento si atterra ESATTAMENTE sul tetto, quindi il confronto
    # «ne ho letti piu' del tetto?» non scatta mai e il catalogo si
    # troncherebbe senza dirlo — il venditore andrebbe a cercare i
    # prodotti mancanti da tutt'altra parte. Il conto vero lo dice
    # WordPress in `X-WP-Total`; senza quell'header vale il fatto che
    # l'ultima pagina era piena.
    # E IL CONTO VERO COMANDA DA SOLO: quando `X-WP-Total` c'e' dice
    # anche che NON ne restano — senza questa precedenza un negozio
    # con esattamente duecento prodotti (due pagine piene) si
    # sentirebbe dire «ce n'e' ancora» a ogni giro, per sempre.
    if totale:
        completo = totale <= tetto
    else:
        completo = not restano and len(prodotti) <= tetto
    avviso = "" if completo else _msg_troncato(tetto, totale)
    return prodotti[:tetto], avviso, completo


LETTORI = {"shopify": leggi_catalogo_shopify, "woo": leggi_catalogo_woo}


# --- LO STOCK ---------------------------------------------------------

def quantita_corretta(esterno: int, saldo: int) -> int:
    """La giacenza da scrivere QUI, visti i movimenti che il negozio
    di la' non sa ancora.

    E' LA FUNZIONE CHE TIENE IN PIEDI LA FASE 1. Il sync ricopre
    `quantita` dalla lettura esterna a ogni giro: senza questa
    correzione, una vendita fatta su Barattolo verrebbe RIALZATA
    entro l'ora — e sul pezzo unico il 'venduto' risorgerebbe, perche'
    la regola dice che uno stock esterno tornato sopra zero riaccende
    l'annuncio (serve al ricarico legittimo del miele).
    Quindi: o il venditore ha gia' riallineato il suo magazzino, e
    allora `esterno` e' gia' giusto e le pendenti sono state spente al
    giro in cui il movimento si e' visto; o non l'ha fatto, e lo
    correggiamo noi. Mai sotto zero.

    IL SALDO HA UN SEGNO, e dalla tappa 4 non e' piu' un conteggio:
    NEGATIVO sono i pezzi venduti qui che il negozio non ha ancora
    scalato, POSITIVO quelli rimborsati qui che non ha ancora
    rimesso. E' la convenzione che lo schema di `connettori_uscite`
    dichiara dal primo giorno («negativo = venduto qui; positivo =
    rimborso»), e il `- abs(...)` di ieri — nato quando nel registro
    c'erano le sole vendite — sul rimborso avrebbe SOTTRATTO invece di
    aggiungere, cioe' nascosto due volte dei pezzi che ci sono."""
    return max(0, int(esterno) + int(saldo or 0))


def rifletti_pendenti(con, annuncio_id: int, visto_prima: int,
                      adesso_esterno: int) -> int:
    """Il venditore ha riallineato il suo magazzino? Allora i
    movimenti che gli avevamo segnalato sono ARRIVATI, e smettono di
    correggere.

    SENZA QUESTA FUNZIONE LA CORREZIONE SI MANGIA LO STOCK: vendo un
    pezzo qui (esterno 10, locale 9, una pendente da 1), il venditore
    scala il suo magazzino a 9, e al giro dopo `quantita_corretta(9, 1)`
    direbbe 8 — la stessa vendita contata due volte, e cosi' a ogni
    riallineamento, fino a zero. E' il difetto che la fase 1
    introdurrebbe curando il suo: peggiore dell'originale, perche'
    silenzioso.

    IL MOVIMENTO SI ATTRIBUISCE ALLE PENDENTI PIU' VECCHIE, fino a
    concorrenza: si spegne solo quel che copre per intero — una riga
    da 3 pezzi contro un calo di 2 resta pendente, che spezzarla
    vorrebbe dire inventare mezza vendita.
    E SI GUARDA IL VERSO (tappa 4): un calo del negozio spegne le
    VENDITE in attesa, una risalita spegne i RIMBORSI — righe di
    segno opposto al movimento non si toccano. Senza, il venditore
    che rimette a magazzino i pezzi di un reso spegnerebbe con quella
    risalita una vendita pendente che non c'entra niente, e da li' in
    poi il conto sarebbe storto per sempre.
    IMPERFEZIONE DICHIARATA, e va nei due versi: un calo dovuto a una
    vendita sul LORO sito puo' spegnere una pendente nostra (e allora
    il locale resta un filo piu' alto del vero: e' la finestra della
    collisione rara, quella che l'escrow copre); un venditore che non
    riallinea MAI tiene il locale piu' basso del suo negozio, che e'
    il verso prudente e glielo dice ogni notifica di vendita. La fase
    2 — il decremento scritto da noi — toglie l'euristica di mezzo."""
    movimento = int(adesso_esterno) - int(visto_prima)
    if visto_prima < 0 or movimento == 0:
        return 0
    try:
        righe = con.execute(
            "SELECT id, delta FROM connettori_uscite "
            "WHERE annuncio_id=? AND stato='pendente' ORDER BY id",
            (annuncio_id,)).fetchall()
    except sqlite3.OperationalError:
        return 0
    spente, resto = 0, abs(movimento)
    for r in righe:
        delta = int(r[1] or 0)
        if delta == 0 or (delta > 0) != (movimento > 0):
            continue          # verso opposto: questo movimento non e' suo
        if abs(delta) > resto:
            break
        con.execute("UPDATE connettori_uscite SET stato='riflessa', "
                    "aggiornato=? WHERE id=?", (int(time.time()), r[0]))
        resto -= abs(delta)
        spente += 1
    return spente


def _saldo_pendente(con, annuncio_id: int) -> int:
    """Il SALDO col segno dei movimenti che il negozio non sa ancora:
    negativo se qui si e' venduto piu' di quanto si sia rimborsato.

    IL NOME DICE IL SEGNO, e il vecchio `_pendenti` non c'e' piu'
    apposta: quello contava dei PEZZI e chi lo leggeva li sottraeva:
    col registro che dalla tappa 4 contiene anche i rimborsi, un
    conteggio senza segno avrebbe nascosto due volte dei pezzi che
    ci sono. Fail-open sul database che non ha ancora la tabella:
    senza registro il saldo e' zero, cioe' il comportamento di chi
    non ha mai venduto niente."""
    try:
        r = con.execute(
            "SELECT COALESCE(SUM(delta), 0) FROM connettori_uscite "
            "WHERE annuncio_id=? AND stato='pendente'",
            (annuncio_id,)).fetchone()
        return int(r[0] or 0)
    except sqlite3.OperationalError:
        return 0


# --- LA RICONCILIAZIONE -----------------------------------------------

def spegni_annuncio(con, annuncio_id: int, stato: str = "rimosso"):
    """Spegne una riga e annulla gli ordini mai pagati.

    E' lo SPECCHIO di `importa_nostr.spegni_annuncio`, ricopiato e non
    importato: dieci righe contro il trascinarsi dietro
    websocket-client, che quel file esige in cima. I sats in escrow non
    c'entrano mai — un annuncio con un affare in corso non e' piu'
    'attivo', e i chiamanti filtrano su quello."""
    adesso = int(time.time())
    con.execute("UPDATE annunci SET stato=? WHERE id=?",
                (stato, annuncio_id))
    con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                "WHERE annuncio_id=? AND stato='creato'",
                (adesso, annuncio_id))
    con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                "WHERE stato='creato' AND id IN (SELECT ordine_id "
                "FROM ordine_righe WHERE annuncio_id=?)",
                (adesso, annuncio_id))


def _riga_locale(con, connettore_id: int, chiave: str):
    """Il match, e ne basta UNO: la chiave del prodotto sul negozio.

    NIENTE ADOZIONE PER TITOLO, ed e' una decisione con una storia:
    l'import Nostr ce l'ha per ragioni sue (gli eventi di ieri non
    avevano una coordinata) e l'ha pagata col caso delle «due teste» —
    una riga NATIVA adottata da fuori perde Modifica e rifornimento, e
    il venditore non capisce perche'. Qui la chiave c'e' sempre,
    quindi il caso non deve nemmeno potersi presentare: se esiste gia'
    un annuncio omonimo nato qui, ne nasce uno NUOVO e il report lo
    dice — «se e' lo stesso oggetto, ritira quello vecchio»."""
    return con.execute(
        "SELECT id, stato, foto, origine_foto, quantita, "
        "origine_stock_visto FROM annunci "
        "WHERE connettore_id=? AND origine_chiave=?",
        (connettore_id, chiave)).fetchone()


def _foto_locali(con, annuncio_id: int, urls: list, salva_foto) -> str:
    """Scarica le foto e torna il JSON dei nomi locali. Un download
    fallito lascia l'URL com'era: meglio una foto che arriva dal
    negozio del venditore che nessuna foto (e' la regola di
    `localizza_foto`)."""
    nomi = []
    for i, u in enumerate(urls or []):
        nome = None
        try:
            nome = salva_foto(annuncio_id, i, u)
        except Exception as e:
            print(f"    ⚠️ foto non salvata ({str(u)[:60]}): {e}")
        nomi.append(nome or u)
    return json.dumps(nomi) if nomi else ""


def riconcilia_connettore(con, connettore: dict, righe: list,
                          salva_foto, revisioni=None, *,
                          completo: bool, max_nuovi: int = 0) -> dict:
    """Porta il catalogo tradotto dentro `annunci`, e torna il report.

    L'ORDINE DELLE DOMANDE e' quello di `importa_venditore`, che e' il
    fratello maggiore di questa funzione: si ritrova la riga per
    chiave; se non c'e' ma esiste SPENTA, non si risuscita; altrimenti
    si aggiorna o si crea.

    QUELLO CHE NON SI RICOPRE MAI: la categoria e la sottocategoria
    gia' scelte (una scelta fatta a mano qui non si cancella ogni ora
    col silenzio di un e-commerce), e la consegna, che viene dal
    CASSETTO del collegamento e non dal negozio.

    `revisioni` e' il marchio della moderazione: `{chiave: motivo}`.
    Una riga marchiata nasce — o torna — in `stato='revisione'`, cioe'
    invisibile al pubblico finche' un moderatore non dice la sua.

    `completo` E' OBBLIGATORIO E SENZA DEFAULT, ed e' la lezione di
    `atteso_sats`: dice se `righe` e' il catalogo INTERO. Su una
    lettura parziale le sparizioni non si possono giudicare — quel che
    non e' stato letto e quel che il venditore ha tolto si somigliano
    troppo — e prima di questa riga il tetto di lettura produceva
    esattamente quella parzialita' in silenzio, spegnendo per sempre
    i prodotti oltre il duecentesimo (e 'rimosso' non risorge).
    Senza default apposta: ogni strada futura eredita la domanda, e
    chi la dimentica lo sente da Python invece che da un venditore.

    `max_nuovi` e' quante righe NUOVE nascono in questo giro (0 =
    nessun tetto). Non e' un fratello del tetto di lettura, e' il suo
    opposto: quello TRONCAVA la vista e mutilava il catalogo, questo
    legge tutto — quindi le sparizioni restano vere — e distribuisce
    solo l'INGRESSO in vetrina. E' anche l'unica riga che rende vera
    la promessa «il resto arriva ai giri successivi»: al giro dopo le
    righe gia' create si ritrovano per chiave e il tetto tocca alle
    prossime.
    """
    revisioni = revisioni or {}
    adesso = int(time.time())
    cid = connettore["id"]
    fonte = connettore["fonte"]
    esito = {"nuovi": 0, "aggiornati": 0, "invariati": 0, "spenti": 0,
             "riaccesi": 0, "in_revisione": 0, "rimandati": 0,
             "parziale": not completo, "saltati": [], "falliti": []}
    viste = set()

    for r in righe:
        # `viste` SI RIEMPIE SEMPRE, ed e' la riga da non spostare piu'
        # in basso: dice «questa chiave c'e' ANCORA sul negozio», che
        # e' l'unica domanda a cui le sparizioni rispondono. Non dice
        # «l'abbiamo scritta»: una riga rimandata dal tetto, saltata
        # dal traduttore (un multi-variante) o non ammessa dalla
        # moderazione e' una riga che sul negozio esiste eccome —
        # spegnerla come «tolta dal venditore» e' una bugia, e per
        # giunta irreversibile ('rimosso' non risorge).
        # Prima stava DOPO il `continue` delle saltate, e bastava che
        # un prodotto gia' in vetrina diventasse multi-variante — o che
        # l'AI avesse un singhiozzo sul suo testo cambiato — perche'
        # sparisse per sempre.
        viste.add(r["origine_chiave"])
        if r.get("saltato_perche"):
            esito["saltati"].append({"titolo": r.get("titolo", "")[:60],
                                     "perche": r["saltato_perche"]})
            continue
        chiave = r["origine_chiave"]
        try:
            _una_riga(con, connettore, r, salva_foto, revisioni, esito,
                      adesso,
                      max_nuovi <= 0 or esito["nuovi"] < max_nuovi)
        except Exception as e:
            # Una riga che esplode e' una voce del report, mai il giro
            # morto: e' il patto di `_crea_riga_con_guardia`
            # dell'import CSV.
            esito["falliti"].append({"titolo": r.get("titolo", "")[:60],
                                     "perche": str(e)[:120]})
            print(f"    ⚠️ riga saltata ({r.get('titolo', '')[:40]}): {e}")

    # --- LE SPARIZIONI ------------------------------------------------
    # Un prodotto che non c'e' piu' nel catalogo COMPLETO si spegne. Il
    # chiamante non deve mai arrivare qui con una lettura parziale: un
    # errore di rete a meta' paginazione svuoterebbe la vetrina di quel
    # venditore, ed e' il motivo per cui `leggi_catalogo_*` ALZA invece
    # di tornare una lista corta.
    # MA IL TETTO DI LETTURA NON ALZAVA, e passava di qui indisturbato:
    # per due tappe questo `for` ha avuto il potere di spegnere tutto
    # cio' che stava oltre il duecentesimo prodotto, in silenzio e per
    # sempre. Adesso la domanda si fa, e la risposta arriva da chi ha
    # letto — non si deduce qui, che da questa parte un catalogo corto
    # e un catalogo piccolo sono indistinguibili.
    # SI SBAGLIA NEL VERSO GIUSTO: sospendere le sparizioni lascia in
    # vetrina un annuncio che il venditore ha tolto (lo toglie lui, o
    # il giro dopo se il catalogo ci sta), spegnerle a torto toglie
    # merce vera a chi vende senza che nessuno lo sappia.
    if completo:
        for riga in con.execute(
                "SELECT id, titolo, origine_chiave FROM annunci "
                "WHERE connettore_id=? AND stato IN ('attivo','revisione')",
                (cid,)).fetchall():
            if riga["origine_chiave"] in viste:
                continue
            spegni_annuncio(con, riga["id"], "rimosso")
            esito["spenti"] += 1
            print(f"    🗑 tolto dal negozio: {riga['titolo'][:50]}")
    else:
        print(f"    ⏸ lettura parziale: le sparizioni non si giudicano")

    con.commit()
    print(f"  🏪 {fonte} #{cid}: {esito['nuovi']} nuovi, "
          f"{esito['aggiornati']} aggiornati, {esito['invariati']} invariati, "
          f"{esito['spenti']} spenti, {esito['rimandati']} rimandati, "
          f"{len(esito['saltati'])} saltati")
    return esito


def _una_riga(con, connettore: dict, r: dict, salva_foto, revisioni,
              esito: dict, adesso: int, puo_creare: bool = True):
    """Il corpo del ciclo, per riga. Sta fuori dal `for` perche' ogni
    riga ha il suo `try`: cosi' il fallimento di una non si porta
    dietro le altre.

    `puo_creare` a False rimanda la sola NASCITA: chi c'e' gia' si
    aggiorna come sempre. E' il tetto di `max_nuovi` visto da qui, e
    tocca l'ingresso in vetrina, mai la tenuta in pari del prezzo o
    della giacenza di quel che si vende gia'."""
    cid = connettore["id"]
    chiave = r["origine_chiave"]
    gia = _riga_locale(con, cid, chiave)
    marchio = revisioni.get(chiave)

    # --- lo scudo anti-resurrezione -----------------------------------
    # La differenza con Nostr e' DICHIARATA e va tenuta:
    # · 'rimosso' non risorge MAI. E' la lapide dei connettori: l'ha
    #   tolto il venditore da qui, un moderatore, o e' sparito dal
    #   negozio. Per tornare serve un prodotto nuovo (chiave nuova).
    # · 'venduto' RISORGE se la giacenza esterna torna sopra zero, e
    #   qui e' il contrario di Nostr apposta: per un negozio il
    #   ricarico del miele e' routine, non una resurrezione — tenerlo
    #   spento sarebbe il difetto, non la guardia.
    if gia and gia["stato"] == "rimosso":
        esito["saltati"].append({"titolo": r["titolo"][:60],
                                 "perche": "gia' rimosso qui: "
                                           "non si ricrea da solo"})
        return

    quantita = r.get("quantita")
    if quantita is not None and gia:
        # PRIMA si spengono le pendenti che il calo esterno copre, POI
        # si sottrae quel che resta: nell'ordine opposto la vendita
        # appena riconosciuta si sottrarrebbe un'ultima volta, e il
        # numero scenderebbe di uno a ogni riallineamento.
        rifletti_pendenti(con, gia["id"], gia["origine_stock_visto"],
                          quantita)
        quantita = quantita_corretta(quantita,
                                     _saldo_pendente(con, gia["id"]))

    if gia:
        _aggiorna(con, gia, r, connettore, salva_foto, marchio, quantita,
                  esito, adesso)
        return

    # --- la riga nuova ------------------------------------------------
    # IL TETTO STA QUI E NON PIU' IN ALTO, ed e' la differenza fra
    # distribuire e mutilare: la riga e' stata LETTA (quindi e' in
    # `viste` e non passa per sparita), semplicemente non nasce oggi.
    # Il giro dopo si ritrova per chiave — o nasce, se il tetto la
    # lascia passare.
    if not puo_creare:
        esito["rimandati"] += 1
        return
    stato = "revisione" if marchio else ("attivo" if r["attivo"]
                                         else "rimosso")
    # L'INVARIANTE DI CASA VALE ANCHE ALLA NASCITA, e non solo agli
    # aggiornamenti: venduto <=> quantita = 0. Senza questa riga un
    # prodotto che arriva GIA' esaurito nascerebbe 'attivo' con zero
    # pezzi — in vetrina un annuncio comprabile all'occhio che alla
    # cassa risponde di no, e nessuna scopa lo raddrizza (quella
    # d'avvio va nell'altro verso: mette a zero i venduti).
    # E' un caso raro su Shopify e QUOTIDIANO su Woo, dove
    # `stock_status: outofstock` e' il modo normale di dire «finito»
    # senza far gestire il magazzino a WooCommerce.
    if stato == "attivo" and quantita == 0:
        stato = "venduto"
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,foto,valuta,prezzo_eur,quantita,quantita_max,"
        "consegna,spedizione_eur,spedizione_punto_eur,"
        "spedizione_punto_dichiarata,spedizione_extra_eur,"
        "fonte,connettore_id,origine_chiave,origine_foto,"
        "origine_stock_visto,creato,modificato,stato) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (connettore["tg_id"], r["titolo"], r["descrizione"],
         r.get("categoria") or "Altro", r["prezzo_sats"],
         connettore["zona"], "", "eur", r["prezzo_eur"],
         1 if quantita is None else quantita,
         1 if quantita is None else quantita,
         connettore["consegna"], connettore["spedizione_eur"],
         connettore["spedizione_punto_eur"],
         connettore["spedizione_punto_dichiarata"],
         connettore["spedizione_extra_eur"],
         connettore["fonte"], cid, chiave,
         json.dumps(r["foto"]) if r["foto"] else "",
         -1 if r.get("quantita") is None else r["quantita"],
         adesso, adesso, stato))
    nuovo = cur.lastrowid
    # le foto DOPO l'insert: il nome del file vuole l'id
    foto = _foto_locali(con, nuovo, r["foto"], salva_foto)
    if foto:
        con.execute("UPDATE annunci SET foto=? WHERE id=?", (foto, nuovo))
    con.commit()          # commit per riga: un crash a meta' giro
    #                       lascia solo annunci completi
    esito["nuovi"] += 1
    if marchio:
        esito["in_revisione"] += 1
    print(f"    🏪 {r['titolo'][:50]} — {r['prezzo_eur']:.2f} € "
          f"[{r.get('categoria') or 'Altro'}]")


def _aggiorna(con, gia, r: dict, connettore: dict, salva_foto, marchio,
              quantita, esito: dict, adesso: int):
    """La riga c'e' gia': si ricopre il contenuto (la fonte comanda) e
    si lascia stare tutto il resto."""
    foto_url = json.dumps(r["foto"]) if r["foto"] else ""
    if foto_url and foto_url == (gia["origine_foto"] or ""):
        foto = gia["foto"]          # stesse foto: niente ri-download
    else:
        foto = _foto_locali(con, gia["id"], r["foto"], salva_foto)
    con.execute(
        "UPDATE annunci SET titolo=?, descrizione=?, prezzo_sats=?, "
        "valuta='eur', prezzo_eur=?, foto=?, origine_foto=?, "
        "origine_stock_visto=?, modificato=? WHERE id=?",
        (r["titolo"], r["descrizione"], r["prezzo_sats"], r["prezzo_eur"],
         foto, foto_url,
         -1 if r.get("quantita") is None else r["quantita"],
         adesso, gia["id"]))
    if quantita is not None:
        con.execute("UPDATE annunci SET quantita=?, "
                    "quantita_max=MAX(quantita_max,?) WHERE id=?",
                    (quantita, quantita, gia["id"]))
    # --- lo stato -----------------------------------------------------
    if marchio:
        # il testo e' cambiato e la moderazione non sa piu' approvarlo:
        # torna in attesa, come una modifica fatta dal form
        con.execute("UPDATE annunci SET stato='revisione' "
                    "WHERE id=? AND stato='attivo'", (gia["id"],))
        esito["in_revisione"] += 1
    elif not r["attivo"]:
        if gia["stato"] != "rimosso":
            spegni_annuncio(con, gia["id"], "rimosso")
            esito["spenti"] += 1
    elif gia["stato"] == "venduto" and (quantita or 0) > 0:
        con.execute("UPDATE annunci SET stato='attivo' WHERE id=?",
                    (gia["id"],))
        esito["riaccesi"] += 1
        print(f"    ↑ tornato in vetrina: {r['titolo'][:50]}")
    elif gia["stato"] == "attivo" and quantita == 0:
        # l'invariante di casa: venduto <=> quantita = 0
        con.execute("UPDATE annunci SET stato='venduto' WHERE id=?",
                    (gia["id"],))
    con.commit()
    esito["aggiornati"] += 1
