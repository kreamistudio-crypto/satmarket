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
import hashlib
import html
import json
import re
import sqlite3
import time
import unicodedata
from collections import Counter

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
# I TETTI ALLE PAGINE (1 ott 2026, cura 8): un negozio che risponde
# sempre una pagina piena — o Shopify con un `Link: next` su una pagina
# vuota — faceva girare il lettore per sempre, con la memoria che
# cresce. Oltre il tetto si ALZA, come su una risposta storta: un giro
# che fallisce si conta e si riprova fra un'ora, una lista a meta' no.
MAX_PAGINE_VARIAZIONI_WOO = 10     # mille varianti per prodotto: oltre non e' un prodotto
MAX_PAGINE_CATALOGO = 50           # cinquemila prodotti letti: il tetto e' molto prima

# LA PAUSA FRA LE PAGINE DI SHOPIFY (1 ott 2026, «negozi grandi»): col
# tetto di lettura a mille il catalogo di Shopify si pagina davvero
# (250 prodotti a pagina), e il suo limite torna a contare — due
# richieste al secondo per negozio, un secchio da quaranta che si
# svuota a quel ritmo. Mezzo secondo fra una pagina e l'altra E' quel
# ritmo: il secchio non si riempie mai, qualunque sia il catalogo, e
# mille prodotti costano un secondo e mezzo di attesa in tutto.
# ⚠️ E STAVOLTA SI PRENDE. Una costante con questo nome era sparita ad
# agosto perche' nessun ciclo la usava — la promessa di una pausa che
# non c'era. Adesso sta DENTRO il ciclo del lettore, prima di ogni
# pagina dopo la prima, e il dormire arriva iniettato come il
# trasporto (`ritmo["dormi"]`): le prove lo contano invece di
# aspettarlo.
PAUSA_PAGINE_SHOPIFY = 0.5

# I tagli del testo, IDENTICI alle colonne del database. Non sono un
# gusto: sono la ragione per cui `testo_negozio` esiste (vedi sotto).
MAX_TITOLO = 120
MAX_DESCRIZIONE = 1500

# Quante foto si tengono per annuncio: la stessa misura del form e
# dell'import CSV.
MAX_FOTO = 5

# Quanti titoli ENTRATI porta il report di un giro (set 2026): il
# venditore legge cosa e' comparso, il conto vero resta `nuovi`. Il
# report vive in una colonna JSON riletta a ogni apertura del
# cassetto, e duecento titoli a giro la gonfierebbero per niente.
MAX_ENTRATI_REPORT = 30

# IL LOTTO DELLE SPARIZIONI (1 ott 2026, «database is locked»): quanti
# annunci si spengono fra un commit e l'altro nel ciclo delle
# sparizioni. Il database e' UNO per tutto il mercatino e sqlite ha un
# solo scrittore alla volta: una transazione che spegne trecento righe
# in un colpo tiene fuori le rotte per tutto il tempo. Il lotto e'
# piccolo apposta — il commit costa un fsync, non ha senso farne uno a
# riga — e un crash a meta' lascia un lotto spento e il resto da
# spegnere al giro dopo, che per le sparizioni e' esattamente quel che
# succederebbe comunque.
LOTTO_SPEGNIMENTI = 25

# IL RESPIRO DEL GIRO (1 ott 2026, «negozi grandi», trovato dal collaudo
# col traffico vero). Le transazioni del giro sono brevi — un commit per
# riga, la cura di «database is locked» — ma vengono UNA DIETRO L'ALTRA,
# senza un attimo fra l'una e l'altra: e sqlite non fa la fila. Chi
# aspetta il lucchetto riprova a intervalli (1, 2, 5, 10... ms), e ogni
# volta che riprova trova il giro gia' dentro la transazione dopo. Misurato
# su mille prodotti: una scrittura della app morta dopo 0,6 s con le rotte
# impazienti, e in produzione — dove ogni richiesta autenticata scrive, e
# l'attesa avviene nel ciclo principale — il server intero fermo finche'
# non trova un buco, per tutta la fase di scrittura del giro.
# La cura: dopo ogni riga che ha scritto, il giro lascia il database
# libero per TANTO TEMPO QUANTO L'HA TENUTO (meta' del tempo suo, meta'
# di tutti: chi aspetta entra al primo o secondo tentativo, qualunque
# sia il disco), al piu' RESPIRO_MAX_S. Il giro gira in un thread, quindi
# rallentarlo non costa niente a nessuno; il conto lo paga lui.
RESPIRO_MAX_S = 0.1


def _respira(secondi: float):
    """La pausa del giro fra una riga scritta e la successiva. Una
    funzione e non un `time.sleep` in linea: le prove la contano invece
    di aspettarla."""
    if secondi > 0:
        time.sleep(secondi)

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


# IL NEGOZIO LENTO (1 ott 2026, «negozi grandi»): un negozio che
# risponde piano NON e' un negozio rotto, e il venditore lo legge nel
# report come legge il tetto — con la meta' che conta, cioe' cosa
# succede intanto ai suoi prodotti. Due frasi, una per dove la lettura
# a tempo si e' fermata (vedi `leggi_catalogo_woo`).
def _msg_lento(letti: int, totale: int = 0) -> str:
    """Fermi fra le pagine del catalogo: la lettura e' parziale, e la
    coda e' quella del tetto, parola per parola."""
    return (f"il tuo negozio risponde piano: in questo giro abbiamo letto "
            f"{letti} prodotti" + (f" su {totale}" if totale else "")
            + MSG_TRONCATO_CODA)


def _msg_varianti_al_prossimo(lette: int, tutte: int) -> str:
    """Fermi fra le variazioni: il catalogo e' intero, i dettagli di
    qualche prodotto arrivano al giro dopo."""
    return (f"il tuo negozio risponde piano: in questo giro abbiamo letto "
            f"le varianti di {lette} prodotti su {tutte}, le altre al "
            f"prossimo giro — intanto quelle gia' in vetrina restano come "
            f"sono")


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


def spoglia_titolo(titolo) -> str:
    """Il TITOLO come testo piano, su una riga sola (8 ott 2026).
    Il caso vero: «Pinuts <h6>Cookies al cacao e arachidi…» in vetrina.
    Il nome di un prodotto su Woo (il `post_title`) o su Shopify puo'
    portare HTML, e la pagina lo stampa escapato — cioe' col tag in
    bella vista. Fin qui la descrizione passava da `_spoglia_html` e il
    titolo da uno `strip()` e basta.
    Stessa scuola della gemella: i tag inline spariscono senza lasciare
    spazio (un «Pinu<b>ts</b>» resta «Pinuts»), gli altri diventano uno
    spazio (un <h6> fra due parole le tiene separate); poi le ENTITA'
    si sciolgono TUTTE con `html.unescape` — anche &#8211; e &rsquo;,
    che la lista corta della descrizione non conosce —, gli spazi si
    comprimono (a capo compresi: un titolo sta su una riga) e si taglia
    agli estremi.
    E' A PUNTO FISSO: si ripete finche' non cambia piu' niente, cosi'
    spoglia_titolo(spoglia_titolo(x)) == spoglia_titolo(x) SEMPRE, anche
    su un «&amp;lt;b&amp;gt;» che al secondo giro scioglie in un tag.
    Serve alla passata all'avvio (`ripulisci_titoli_importati` in
    server.py): un titolo gia' pulito deve restare IDENTICO, o il giro
    di sync lo vedrebbe «cambiato» a ogni riavvio e ripagherebbe la
    moderazione per niente. Termina sempre: ogni giro accorcia o lascia
    uguale, mai allunga.
    Un «<» da solo (taglia < 40, un «<3») non e' un tag e resta."""
    t = str(titolo or "")
    while True:
        prima = t
        t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
        t = re.sub(r"(?i)</?(b|strong|i|em|u|s|span|a|small|code|sup|sub)"
                   r"(\s[^>]*)?>", "", t)
        t = re.sub(r"<[^>]+>", " ", t)
        t = html.unescape(t)
        t = re.sub(r"\s+", " ", t).strip()
        if t == prima:
            return t


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
    # il trattino e' il ripiego di casa per la descrizione vuota; il
    # titolo si spoglia PRIMA di troncare, o un tag lungo mangerebbe
    # le parole vere
    return (spoglia_titolo(titolo)[:MAX_TITOLO],
            (desc or "—")[:MAX_DESCRIZIONE])


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
    """Un prodotto Shopify diventa una riga normalizzata.

    UN PRODOTTO, UNA RIGA: il multi-variante non arriva piu' qui
    intero — `esplodi_shopify` lo ha gia' spezzato in un figlio per
    variante (set 2026), ognuno con la SUA sola variante dentro.
    Il salto sul `> 1` resta come cintura: se un giorno qualcuno
    chiamasse il traduttore senza passare da `traduci`, il prodotto
    si salta dicendolo invece di leggere il prezzo della prima
    variante come fosse quello di tutte."""
    riga = {"origine_chiave": str(p.get("id") or ""),
            "saltato_perche": "", "titolo": "", "descrizione": "",
            "prezzo_eur": 0.0, "prezzo_sats": 0, "quantita": None,
            "foto": [], "categoria_grezza": "", "categorie_grezze": [],
            "attivo": True, "digitale": False}
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
    # NIENTE DA SPEDIRE (set 2026): Shopify lo dice per variante, con
    # `requires_shipping`. E' il negozio a dichiararlo, non noi a
    # dedurlo dal titolo — e vale il FALSO esplicito: la chiave che
    # manca e' un prodotto fisico, come lo era ieri.
    riga["digitale"] = (varianti[0].get("requires_shipping") is False
                        if isinstance(varianti[0], dict) else False)
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
    # TUTTI i nomi con cui il negozio classifica il prodotto (16 nov
    # 2026, cantiere categoria-connettori), nell'ordine in cui contano:
    # il «tipo di prodotto» prima, poi i tag. Li legge il server
    # (`categoria_dal_negozio`), che tiene solo il primo che combacia
    # PER INTERO con una nostra categoria: un tag a caso non sposta
    # niente, e chi non combacia resta in «Altro» come ieri.
    tag = p.get("tags") or ""
    if isinstance(tag, list):
        tag = ",".join(str(t) for t in tag)
    riga["categorie_grezze"] = [n for n in
                                [(p.get("product_type") or "").strip()]
                                + [t.strip() for t in str(tag).split(",")]
                                if n]
    # draft e archived non sono in vetrina sul suo negozio: non devono
    # esserlo nemmeno qui
    riga["attivo"] = (p.get("status") or "active") == "active"
    return riga


# I TIPI DI PRODOTTO WOO CHE NON SAPPIAMO TRATTARE, e ognuno col suo
# perche' scritto: un annuncio di Barattolo e' UNA cosa con UN prezzo
# e UNA giacenza, e questi due non lo sono.
# · `grouped` e' un contenitore che rimanda ad altri prodotti e un
#   prezzo suo non ce l'ha;
# · `external` e' il prodotto in affiliazione: il bottone porta su un
#   ALTRO sito, quindi comprarlo qui non vorrebbe dire niente — ed e'
#   quello che si dimentica, perche' un prezzo ce l'ha.
# · `variable` NON e' piu' un salto (set 2026): il lettore gli aggancia
#   le variazioni (`_variazioni`) e `esplodi_woo` ne fa un figlio per
#   ciascuna. Arriva qui intero solo se le variazioni non ci sono —
#   mai lette (un chiamante che non passa dal lettore) o zero in
#   vendita — e allora si salta DICENDO quale dei due casi e'.
SALTI_WOO = {"variable": "ha piu' varianti e non le ho potute leggere",
             "grouped": "e' un gruppo di prodotti",
             "external": "si compra su un altro sito"}
MSG_VARIANTI_VUOTE = "nessuna delle sue varianti e' in vendita"
# (1 ott 2026) il terzo caso del `variable` intero: le variazioni non
# sono MANCATE, non le abbiamo ancora chieste — la lettura a tempo si
# e' fermata prima (vedi `leggi_catalogo_woo`)
MSG_VARIANTI_AL_PROSSIMO = "le sue varianti le leggiamo al prossimo giro"


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
            "foto": [], "categoria_grezza": "", "categorie_grezze": [],
            "attivo": True, "digitale": False}
    titolo, descrizione = testo_negozio(p, "woo")
    riga["titolo"], riga["descrizione"] = titolo, descrizione
    if not riga["origine_chiave"] or not titolo:
        riga["saltato_perche"] = "senza id o senza titolo"
        return riga
    tipo = str(p.get("type") or "simple").lower()
    if tipo in SALTI_WOO:
        riga["saltato_perche"] = (MSG_VARIANTI_VUOTE
                                  if tipo == "variable"
                                  and p.get("_variazioni") == []
                                  else SALTI_WOO[tipo])
        if tipo == "variable" and p.get("_variazioni_al_prossimo"):
            # LE FIGLIE RESTANO COME SONO (1 ott 2026): il prodotto c'e',
            # le sue variazioni non le abbiamo lette in questo giro. Il
            # segno dice alla riconciliazione di non prendere le sue
            # righe `pid:vid` per sparite — sono sul negozio, aspettano
            # solo il loro turno.
            riga["saltato_perche"] = MSG_VARIANTI_AL_PROSSIMO
            riga["_figlie_intatte"] = True
        return riga
    # NIENTE DA SPEDIRE (set 2026): WooCommerce lo dice con due
    # spunte, «Virtuale» e «Scaricabile», e basta una delle due — un
    # corso online e' virtuale e non scaricabile, un PDF e' tutt'e
    # due. Sulle variazioni le spunte sono loro (`esplodi_woo` le
    # porta qui gia' fuse con quelle del padre).
    riga["digitale"] = bool(p.get("virtual")) or bool(p.get("downloadable"))
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
    # tutte, e non solo la prima (16 nov 2026): un prodotto Woo sta
    # spesso in «Senza categoria» E in quella vera, o nella madre e
    # nella figlia — il server tiene la prima che combacia
    riga["categorie_grezze"] = [str(c).strip() for c in categorie
                                if str(c).strip()]
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


# --- LE VARIANTI (set 2026) -------------------------------------------
# `annunci` e' piatto: un annuncio ha UN prezzo e UNA giacenza. Un
# prodotto con piu' varianti (il libro in PDF o cartaceo, la maglia in
# tre taglie) non ci sta dentro, e fino a ieri si saltava dicendolo.
# La forma che ci sta e' UN ANNUNCIO PER VARIANTE — «Titolo — pdf»,
# «Titolo — cartaceo» — col prezzo e la giacenza della variante, e le
# esaurite fuori vetrina come ogni esaurito.
#
# L'ESPLOSIONE STA PRIMA DEL TRADUTTORE E NON DENTRO, ed e' la scelta
# che tiene tutto il resto com'era: ogni figlio e' un prodotto FINTO
# nella forma della sua piattaforma — una sola variante dentro, il
# titolo gia' composto, le foto della variante davanti — e il
# traduttore lo legge come un prodotto normale, senza sapere che era
# un pezzo di qualcosa. Cosi' il prezzo, la giacenza, l'IVA, lo
# stato e il testo canonico passano dalle STESSE righe di sempre, e
# una regola aggiunta domani a un traduttore vale da sola anche per
# le varianti.
#
# LA CHIAVE DEL FIGLIO E' `padre:variante`, e non il solo id della
# variante: si legge nel database (`origine_chiave` dice subito di
# chi e' figlia), e non puo' MAI combaciare con l'id di un prodotto
# semplice. Il prodotto con UNA sola variante tiene la chiave di ieri
# (l'id del padre), quindi nessuna riga gia' in vetrina cambia nome.
# ⚠️ IL CAMBIO DI FORMA E' UNA SPARIZIONE, dichiarata: un prodotto
# semplice che sul negozio diventa variabile perde la chiave `pid` e
# ne guadagna N `pid:vid` — la riga vecchia si spegne come «tolta dal
# negozio» (e 'rimosso' non risorge) e ne nascono N nuove, che la
# moderazione guarda una volta. E' lo stesso patto scritto per lo
# scudo anti-resurrezione: «per tornare serve una chiave nuova».

def _titolo_variante(base: str, opzione: str) -> str:
    """«Titolo — pdf». Se il titolo del padre e' lungo si accorcia
    LUI e non l'opzione: e' l'opzione che distingue due annunci che
    per il resto sono identici, e troncata dal fondo sparirebbe
    proprio lei."""
    base = str(base or "").strip()
    opzione = str(opzione or "").strip()
    if not opzione:
        return base
    spazio = MAX_TITOLO - len(opzione) - 3
    if len(base) > spazio > 0:
        base = base[:spazio].rstrip()
    return f"{base} — {opzione}"


def esplodi_shopify(p: dict) -> list:
    """Un prodotto Shopify con piu' varianti diventa un figlio per
    variante; con una sola (quella «di default», che c'e' sempre)
    torna com'e' — cioe' la chiave e il titolo di ieri."""
    varianti = [v for v in (p.get("variants") or []) if isinstance(v, dict)]
    if len(varianti) <= 1:
        return [p]
    pid = p.get("id")
    foto = [i for i in (p.get("images") or []) if isinstance(i, dict)]
    # i NOMI delle opzioni stanno sul padre («Taglia», «Colore»), i
    # valori sulla variante (option1..option3), nello stesso ordine
    nomi = [str(o.get("name") or "").strip()
            for o in (p.get("options") or []) if isinstance(o, dict)]
    figli = []
    for n, v in enumerate(varianti, 1):
        vid = v.get("id")
        opzioni = [[nomi[i] if i < len(nomi) and nomi[i] else "Variante",
                    str(v.get(f"option{i + 1}")).strip()]
                   for i in range(3) if v.get(f"option{i + 1}")]
        # la foto DELLA variante davanti alle altre: il cartaceo ha la
        # sua copertina, e in vetrina e' la prima che si vede
        sue = [i for i in foto if v.get("image_id")
               and i.get("id") == v.get("image_id")]
        figlio = dict(p)
        figlio["id"] = f"{pid}:{vid}" if pid and vid else ""
        figlio["title"] = _titolo_variante(
            p.get("title"), v.get("title") or f"variante {n}")
        figlio["variants"] = [v]
        figlio["images"] = sue + [i for i in foto if i not in sue]
        figlio["_opzioni"] = opzioni or [["Variante", str(
            v.get("title") or f"variante {n}").strip()]]
        figli.append(figlio)
    return figli


def esplodi_woo(p: dict) -> list:
    """Un prodotto WooCommerce `variable` diventa un figlio per
    variazione, nella forma di un prodotto `simple`.

    LE VARIAZIONI LE AGGANCIA IL LETTORE (`_variazioni`), perche' su
    Woo vivono a un altro indirizzo e questo modulo non fa rete. Se
    non ci sono — mai lette, o lista vuota — il padre torna com'e' e
    il traduttore lo salta col motivo giusto.
    COSA VIENE DAL PADRE E COSA DALLA VARIAZIONE, e non e' una scelta
    di gusto: prezzo, giacenza, stato, spunte digitali e foto sono
    della variazione (e' li' che il negoziante li scrive); testo,
    categorie, visibilita' a scaffale sono del padre (la variazione
    non li ha). La giacenza «parent» — la variazione che eredita il
    magazzino del padre — prende i numeri del padre, cosi' la
    trappola di `manage_stock: 'parent'` si scioglie QUI, una volta,
    e al traduttore arriva un booleano."""
    if str(p.get("type") or "simple").lower() != "variable":
        return [p]
    variazioni = p.get("_variazioni")
    if not isinstance(variazioni, list) or not variazioni:
        return [p]
    pid = p.get("id")
    figli = []
    # LE SCELTE «QUALSIASI» (19 nov 2026, il negozio Uhmami): vedi
    # `scelte_aperte_woo` — chi ne lascia aperte, con le stesse fisse di
    # una sorella gia' vista, e' un doppione e non nasce
    viste = set()
    for n, v in enumerate(variazioni, 1):
        if not isinstance(v, dict):
            continue
        vid = v.get("id")
        attributi = [a for a in (v.get("attributes") or [])
                     if isinstance(a, dict) and a.get("option")]
        scelte = scelte_aperte_woo(p, attributi)
        if scelte:
            fisse = tuple(_chiave_attributo(a) + (_testo_attributo(
                a.get("option")).casefold(),) for a in attributi)
            if fisse in viste:
                continue
            viste.add(fisse)
        opzioni = ", ".join(_testo_attributo(a.get("option"))
                            for a in attributi)
        # il codice articolo come nome solo se non c'e' altro da dire: con
        # le scelte aperte la variante si distingue da quelle (le tendine)
        nome = opzioni or ("" if scelte else
                           str(v.get("sku") or "").strip() or f"variante {n}")
        gestito, scorte = v.get("manage_stock"), v.get("stock_quantity")
        if gestito == "parent" or gestito is None:
            gestito, scorte = p.get("manage_stock"), p.get("stock_quantity")
        foto = []
        if isinstance(v.get("image"), dict) and v["image"].get("src"):
            foto.append(v["image"])
        foto += [i for i in (p.get("images") or []) if isinstance(i, dict)]
        # una variazione «privata» non e' in vendita sul negozio: per
        # il traduttore e' un prodotto non pubblicato
        stato = (p.get("status") if str(v.get("status") or "publish")
                 == "publish" else "private")
        figli.append({
            "id": f"{pid}:{vid}" if pid and vid else "",
            "name": _titolo_variante(p.get("name"), nome),
            "description": p.get("description") or "",
            "short_description": p.get("short_description") or "",
            "type": "simple", "status": stato,
            "catalog_visibility": p.get("catalog_visibility"),
            "price": v.get("price"), "regular_price": v.get("regular_price"),
            "manage_stock": gestito, "stock_quantity": scorte,
            "stock_status": v.get("stock_status") or p.get("stock_status"),
            "images": foto, "categories": p.get("categories") or [],
            "virtual": bool(v.get("virtual")) or bool(p.get("virtual")),
            "downloadable": (bool(v.get("downloadable"))
                             or bool(p.get("downloadable"))),
            "_opzioni": [[_testo_attributo(a.get("name")) or "Variante",
                          _testo_attributo(a.get("option"))]
                         for a in attributi]
                        or ([["Variante", nome]] if nome else []),
            "_scelte": scelte,
        })
    return figli or [p]


# --- LE SCELTE «QUALSIASI» (19 nov 2026) --------------------------------
# Il difetto dal campo: il negozio Uhmami vende una box con due tendine
# (il gusto della pallina, la composta), e su WooCommerce le sue sei
# variazioni sono TUTTE «Qualsiasi pallina / Qualsiasi composta», stesso
# prezzo, stessa giacenza, stesso codice articolo «025». Woo, per un
# attributo lasciato su «Qualsiasi», non lo scrive nella variazione: il
# cliente lo sceglie con la tendina e il negozio lo legge nell'ordine.
# Qui arrivavano sei variazioni senza attributi, cioe' sei annunci
# «Box — 025», uguali, col codice articolo come nome.
# LA FORMA GIUSTA: le tendine stanno sul PADRE (`attributes`, quelli con
# `variation: true`, coi loro `options`); quelle che la variazione NON
# fissa sono una SCELTA del compratore, non un annuncio a parte — prezzo
# e giacenza non cambiano, e moltiplicare gli annunci moltiplicherebbe
# anche le scorte (dieci box, ma dieci per ogni combinazione in vetrina).
# Le variazioni con le stesse fisse e scelte aperte sono DOPPIONI: Woo
# vende sempre la prima che combacia, e noi teniamo quella (la lettura e'
# in ordine di id). La scelta del compratore viaggia con l'ordine, nella
# nota al venditore (`scelte_da_payload` in server.py).

MAX_SCELTE = 3            # le tendine di una riga (Woo non ha un tetto)
MAX_VALORI_SCELTA = 40    # le voci di una tendina
MAX_TESTO_SCELTA = 60     # il nome di una tendina, o una sua voce


def _testo_attributo(t) -> str:
    """Il nome di una tendina, o una sua voce, come testo piano su una
    riga (19 nov 2026, il negozio Uhmami): l'API di WooCommerce manda i
    nomi degli attributi con le ENTITA' HTML — «Spalmabile Uhmami N&#039;
    1» — e la pagina, che giustamente escapa, mostrava «N&#039;» al
    posto dell'apice. Si sciolgono qui, alla fonte, una volta: dalla
    colonna alla tendina, fino alla nota del venditore e al controllo
    del server sulla voce scelta, viaggia lo stesso testo. A punto
    fisso, come `spoglia_titolo`: un «&amp;#039;» doppio si scioglie
    tutto, e un testo gia' pulito resta IDENTICO (il giro dell'ora non
    lo vede cambiato)."""
    t = str(t or "")
    while True:
        prima = t
        t = " ".join(html.unescape(t).split())
        if t == prima:
            return t


def _chiave_attributo(a: dict) -> tuple:
    """Come si riconosce lo stesso attributo sul padre e sulla
    variazione: l'id per quelli globali (Prodotti → Attributi), il nome
    per quelli scritti nel prodotto (id 0)."""
    try:
        aid = int(a.get("id") or 0)
    except (TypeError, ValueError):
        aid = 0
    return ("id", aid) if aid else (
        "nome", _testo_attributo(a.get("name")).casefold())


def scelte_aperte_woo(padre: dict, fissi: list) -> list:
    """[[nome, [voci...]], ...]: gli attributi da variazione del padre
    che la variazione lascia su «Qualsiasi». Lista vuota = niente da
    scegliere, il mondo di ieri. Pura."""
    prese = {_chiave_attributo(a) for a in fissi}
    scelte = []
    for a in padre.get("attributes") or []:
        if not isinstance(a, dict) or not a.get("variation"):
            continue
        if _chiave_attributo(a) in prese:
            continue
        nome = _testo_attributo(a.get("name"))[:MAX_TESTO_SCELTA]
        voci = []
        for o in a.get("options") or []:
            o = _testo_attributo(o)[:MAX_TESTO_SCELTA]
            if o and o not in voci:
                voci.append(o)
        if nome and voci:
            scelte.append([nome, voci[:MAX_VALORI_SCELTA]])
    return scelte[:MAX_SCELTE]


ESPLOSIONI = {"shopify": esplodi_shopify, "woo": esplodi_woo}


def traduci(prodotti: list, fonte: str, cambio: dict) -> list:
    """Il dispatch: una lista di prodotti diventa una lista di righe
    normalizzate — prima l'esplosione delle varianti, poi il
    traduttore su ogni figlio. Chi aggiunge una piattaforma aggiunge
    una voce a TRADUTTORI (e una a ESPLOSIONI) e non tocca
    nient'altro."""
    tr = TRADUTTORI.get(fonte)
    if not tr:
        return []
    esplodi = ESPLOSIONI.get(fonte) or (lambda p: [p])
    righe = []
    for p in prodotti:
        if not isinstance(p, dict):
            continue
        # il titolo del PADRE, letto con la stessa ricetta dei figli:
        # e' quello su cui si riconosce un'edizione numerata
        titolo_padre = testo_negozio(p, fonte)[0]
        for figlio in esplodi(p):
            riga = tr(figlio, cambio)
            riga["_padre"] = str(p.get("id") or "")
            riga["_titolo_padre"] = titolo_padre
            riga["_opzioni"] = figlio.get("_opzioni") or []
            riga["scelte"] = figlio.get("_scelte") or []
            righe.append(riga)
    assegna_famiglie(righe)
    return righe


# --- LE FAMIGLIE (set 2026) --------------------------------------------
# Il difetto dal campo: il negozio AGORA ha fatto entrare 150 righe
# quasi identiche — «COWBOY Limited Edition #N/21 — Golden Yellow,
# TAGLIA» — e la home si e' riempita di magliette gialle uguali.
# L'ESPLOSIONE RESTA (un annuncio per variante, col suo prezzo e la sua
# giacenza: e' quel che il motore dei soldi sa comprare, spedire e
# rimborsare), e SOPRA ci si scrive la FAMIGLIA: quali righe sono lo
# stesso prodotto, e con quali opzioni si distinguono. La vetrina ne
# mostra una card sola, la scheda i bottoncini per scegliere.
# DUE REGOLE, e la seconda e' stretta apposta:
# · le varianti dello stesso prodotto padre sono una famiglia;
# · prodotti DIVERSI dello stesso negozio il cui titolo differisce
#   SOLO per un numero d'edizione col cancelletto («#7», «#07/21») sono
#   una famiglia sola, col «Numero» come opzione in piu'. Solo col
#   cancelletto: «Scarpe 42/43» o «Set 3 pezzi» non si toccano mai.
#   Il confronto ignora maiuscole, spazi, emoji e segni (il #09 di
#   AGORA porta «💛 » davanti al titolo, ed e' lo stesso prodotto).
# Un prodotto con una variante sola e senza edizione resta com'era:
# nessuna famiglia, nessuna differenza.

_EDIZIONE = re.compile(r"#\s*(\d{1,4})(?:\s*/\s*(\d{1,4}))?")


def _radice_titolo(titolo: str) -> str:
    """La forma di confronto: solo lettere e cifre, in minuscolo."""
    t = unicodedata.normalize("NFKC", str(titolo or "")).casefold()
    return "".join(c for c in t if c.isalnum())


def _pulisci_titolo(titolo: str) -> str:
    """Il titolo senza il numero d'edizione, per la card di famiglia."""
    t = _EDIZIONE.sub(" ", str(titolo or ""))
    t = re.sub(r"\s{2,}", " ", t).strip(" \t-–—,·|")
    return t or str(titolo or "").strip()


def edizione_titolo(titolo: str):
    """(radice, numero) se il titolo porta UN numero d'edizione col
    cancelletto, altrimenti None. Due numeri nello stesso titolo non si
    sa quale sia l'edizione: niente famiglia, meglio che indovinare."""
    trovati = _EDIZIONE.findall(str(titolo or ""))
    if len(trovati) != 1:
        return None
    radice = _radice_titolo(_EDIZIONE.sub(" ", titolo))
    if not radice:
        return None
    num, di = trovati[0]
    return radice, f"{num}/{di}" if di else num


def assegna_famiglie(righe: list) -> None:
    """Scrive su ogni riga `famiglia` (la chiave dentro il negozio, ''
    = nessuna), `famiglia_titolo` e `opzioni` ([[nome, valore], ...]).
    PURA: lavora sul catalogo letto in questo giro, e la chiave del
    collegamento la aggiunge chi scrive (`_scrivi_famiglia`), cosi' due
    negozi con lo stesso id di prodotto non si mescolano mai."""
    vive = [r for r in righe if not r.get("saltato_perche")]
    for r in righe:
        r["famiglia"], r["famiglia_titolo"], r["opzioni"] = "", "", []
    padri = {}
    for r in vive:
        padri.setdefault(r.get("_padre") or r["origine_chiave"], []).append(r)
    # le edizioni: padri diversi con la stessa radice e un numero
    edizioni = {}
    for padre, figli in padri.items():
        ed = edizione_titolo(figli[0].get("_titolo_padre") or "")
        if ed:
            edizioni.setdefault(ed[0], []).append((padre, ed[1]))
    in_edizione = {}
    for radice, membri in edizioni.items():
        if len(membri) < 2:
            continue
        chiave = "e:" + hashlib.sha1(radice.encode()).hexdigest()[:12]
        titoli = Counter(_pulisci_titolo(padri[p][0].get("_titolo_padre"))
                         for p, _ in membri)
        titolo = titoli.most_common(1)[0][0]
        for padre, numero in membri:
            in_edizione[padre] = (chiave, titolo, numero)
    for padre, figli in padri.items():
        if padre in in_edizione:
            chiave, titolo, numero = in_edizione[padre]
            for r in figli:
                r["famiglia"], r["famiglia_titolo"] = chiave, titolo
                r["opzioni"] = [["Numero", numero]] + list(
                    r.get("_opzioni") or [])
        elif len(figli) > 1:
            titolo = figli[0].get("_titolo_padre") or ""
            for r in figli:
                r["famiglia"], r["famiglia_titolo"] = f"p:{padre}", titolo
                r["opzioni"] = list(r.get("_opzioni") or [])


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
                           tetto: int = 200, ritmo: dict = None) -> tuple[list, str]:
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
    nessuno.

    `ritmo` (1 ott 2026) e' la stessa idea per il TEMPO: un dizionario
    da cui ogni lettore pesca quel che gli serve. Qui solo `dormi`, chi
    fa la pausa fra due pagine (di serie `time.sleep`); il gemello Woo
    ci pesca la scadenza e il segno della rotazione."""
    prodotti = []
    dormi = (ritmo or {}).get("dormi") or time.sleep
    atteso = str(dominio or "").strip().lower()
    url = (f"https://{dominio}/admin/api/{VERSIONE_API_SHOPIFY}"
           f"/products.json?limit={PER_PAGINA}")
    intestazioni = {"X-Shopify-Access-Token":
                    (credenziali or {}).get("token", "")}
    pagine = 0
    while url and len(prodotti) < tetto:
        pagine += 1
        if pagine > MAX_PAGINE_CATALOGO:
            raise RuntimeError("il catalogo non finisce mai: oltre "
                               f"{MAX_PAGINE_CATALOGO} pagine")
        if pagine > 1:
            # la pausa VERA, fra una pagina e l'altra e mai prima della
            # prima: il negozio da duecento prodotti non aspetta niente
            dormi(PAUSA_PAGINE_SHOPIFY)
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


def radice_woo(url_negozio: str) -> str:
    """L'indirizzo principale del sito, senza il percorso:
    `https://sito.it/negozio/` → `https://sito.it`. E' dove sta l'API
    di WooCommerce quando WordPress vive alla radice — il caso normale
    — e chi collega il negozio scrive spesso la pagina dello shop. Se
    la forma non e' quella di `_base_woo` torna l'indirizzo com'e':
    a rifiutarlo pensa lei."""
    base = str(url_negozio or "").strip().rstrip("/")
    m = re.match(r"(https://[A-Za-z0-9.-]+)(/|$)", base)
    return m.group(1) if m else base


def _codice_wp(corpo) -> str:
    """Il codice d'errore che WordPress e WooCommerce mettono nel corpo
    (`{"code": "rest_no_route", "message": ..., "data": {...}}`), o ''
    quando la risposta NON viene da loro: la pagina 404 di un tema, il
    muro HTML di un firewall, una risposta vuota. E' la differenza fra
    «WordPress mi ha risposto di no» e «non sono nemmeno arrivato»."""
    if isinstance(corpo, dict) and isinstance(corpo.get("code"), str):
        return corpo["code"]
    return ""


def _dove_rimanda(intestazioni) -> str:
    """Il `Location` di un redirect, senza query (che potrebbe portare
    un token di sessione): serve a dire al venditore QUALE indirizzo
    scrivere, non a seguirlo — quello il trasporto non lo fa mai."""
    for k, v in (intestazioni or {}).items():
        if str(k).lower() == "location":
            return str(v).split("?", 1)[0].split("#", 1)[0].strip()[:160]
    return ""


def spiega_risposta_woo(stato: int, corpo, intestazioni, base: str) -> str:
    """Una risposta non-200 dell'API di WooCommerce, detta a chi collega
    il negozio con quel che puo' FARE (set 2026): prima diceva «le
    impostazioni non rispondono» per qualunque stato, e un venditore con
    l'indirizzo della pagina del negozio non aveva modo di capire che
    il guasto era l'indirizzo.

    Si distingue, quando si puo': l'INDIRIZZO sbagliato (un 404 senza
    codice WordPress = li' non risponde nessun WordPress; con codice =
    WordPress c'e' ma WooCommerce no), le CHIAVI (401 con codice = il
    negozio non le riconosce; 403 con codice = le riconosce ma non
    hanno il permesso di leggere, o l'utente non gestisce il negozio),
    il SITO CHE BLOCCA (401/403 SENZA codice, cioe' una risposta che
    non e' di WordPress: un firewall, una protezione del server), il
    REDIRECT (si dice dove, non si segue: e' il patto del trasporto), e
    l'errore del server. Il 200 senza le voci attese resta quel che
    era, MSG_IVA_IGNOTA — li' davvero non si sa."""
    codice = _codice_wp(corpo)
    radice = radice_woo(base)
    if 300 <= stato < 400:
        dove = _dove_rimanda(intestazioni)
        return ("il sito rimanda a un altro indirizzo"
                + (f" ({dove})" if dove else "")
                + ": scrivi quello, come lo apre il browser (con o senza "
                  "«www», con https)")
    if stato == 401:
        if codice:
            return ("il negozio non riconosce le chiavi: ricontrolla "
                    "Consumer key e Consumer secret (WooCommerce → "
                    "Impostazioni → Avanzate → API REST), o generane una "
                    "coppia nuova. Se sono giuste, il server potrebbe "
                    "scartare l'intestazione Authorization: chiedi a chi "
                    "lo gestisce")
        return ("il sito chiede una password prima ancora di arrivare a "
                "WooCommerce (una protezione del server): chiedi a chi lo "
                "gestisce di lasciar passare le chiamate a /wp-json/")
    if stato == 403:
        if codice:
            return ("le chiavi sono giuste ma non possono leggere: la "
                    "chiave API deve avere il permesso «Lettura» ed essere "
                    "di un utente che gestisce il negozio (Shop manager o "
                    "Amministratore)")
        return ("il sito blocca le richieste (un firewall, o un servizio "
                "come Cloudflare): chiedi a chi lo gestisce di lasciar "
                "passare le chiamate a /wp-json/wc/v3/ con User-Agent "
                "«Barattolo/1.0»")
    if stato == 404:
        if codice:
            return (f"a {base} risponde un WordPress, ma non WooCommerce "
                    f"(o la sua API REST è spenta): controlla che "
                    f"WooCommerce sia attivo")
        if radice != base:
            return (f"a {base} non risponde nessun WordPress: usa "
                    f"l'indirizzo principale del sito, per esempio "
                    f"{radice}")
        return f"a {base} non risponde nessun WordPress: controlla l'indirizzo"
    if stato >= 500:
        return (f"il sito ha risposto con un errore suo ({stato}): riprova "
                f"fra un po', o chiedi a chi lo gestisce")
    return (f"il sito ha rifiutato la richiesta ({stato}), probabilmente un "
            f"firewall: chiedi a chi lo gestisce di lasciar passare le "
            f"chiamate a /wp-json/wc/v3/")


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
    stato, corpo, risposta = chiama(
        "GET", f"{base}/wp-json/{VERSIONE_API_WOO}/settings/general",
        intestazioni)
    if stato != 200:
        # e' la PRIMA chiamata al negozio, quindi e' qui che un
        # indirizzo sbagliato o una chiave senza permesso si scoprono:
        # si dice quale dei due, non «le impostazioni non rispondono»
        raise RuntimeError(spiega_risposta_woo(stato, corpo, risposta, base))
    tasse = _valore_impostazione(corpo, "woocommerce_calc_taxes")
    if tasse is None:
        raise RuntimeError(MSG_IVA_IGNOTA)
    if tasse != "yes":
        return          # le tasse sono spente: il prezzo e' quel che e'
    stato, corpo, risposta = chiama(
        "GET", f"{base}/wp-json/{VERSIONE_API_WOO}/settings/tax",
        intestazioni)
    if stato != 200:
        raise RuntimeError(spiega_risposta_woo(stato, corpo, risposta, base))
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
                       tetto: int = 200, ritmo: dict = None) -> tuple[list, str]:
    """Il catalogo di un WooCommerce, pagina per pagina.

    ALZA come il gemello Shopify, e per la stessa ragione: le
    sparizioni si giudicano solo su un catalogo COMPLETO, quindi una
    lettura a meta' non deve MAI tornare come una lista corta.

    L'ORDINE E' PER ID CRESCENTE e non e' un vezzo: il default di
    WooCommerce e' la data di pubblicazione, e con quello basta che il
    venditore ritocchi un prodotto mentre stiamo paginando perche' una
    riga scivoli fra due pagine e non la si veda — cioe' un prodotto
    dichiarato sparito e spento per sbaglio. L'id non si muove.

    LA LETTURA A TEMPO (1 ott 2026, «negozi grandi»). Col tetto a mille
    un Woo lento non ci stava piu' nel giro: una chiamata per ogni
    prodotto variabile, e mille variabili a un secondo l'una sono
    diciassette minuti — oltre la scadenza, cioe' un errore contato a
    ogni giro, e al quinto il collegamento dichiarato ROTTO, col
    messaggio al venditore, per un negozio che rispondeva benissimo.
    `ritmo["entro"]` e' l'ora (dell'orologio `ritmo["orologio"]`, di
    serie quello monotono) oltre la quale non si bussa piu': il lettore
    si ferma DA SOLO, prima della scadenza, e quel che ha letto e' un
    giro buono, non un errore.
      · fra le VARIAZIONI, che e' il caso vero: i prodotti a cui non si
        arriva tornano marcati `_variazioni_al_prossimo`, e il catalogo
        resta COMPLETO — la lista dei prodotti e' intera, mancano solo
        i dettagli di alcuni. La riconciliazione non spegne le loro
        figlie (vedi `_figlie_intatte`) e le aggiorna al giro in cui
        tocca a loro;
      · fra le PAGINE del catalogo, che e' il caso estremo (un negozio
        che non serve dieci pagine in otto minuti): ci si ferma e la
        lettura e' PARZIALE, come al tetto — le sparizioni aspettano.
    LA ROTAZIONE: `ritmo["segno"]` e' un dizionario che il server tiene
    da un giro all'altro, e `dopo` e' l'id dell'ultimo prodotto
    variabile letto. Il giro seguente riparte da li', in cerchio: senza,
    si rileggerebbero ogni ora gli stessi primi prodotti e la coda non
    arriverebbe mai. Senza `ritmo` (la prova del collegamento, le prove
    di ieri) si legge tutto, come prima."""
    base = _base_woo(url_negozio)
    intestazioni = _intestazioni_woo(credenziali)
    ritmo = ritmo or {}
    orologio = ritmo.get("orologio") or time.monotonic
    entro = ritmo.get("entro")
    segno = ritmo.get("segno")

    def c_e_tempo() -> bool:
        return entro is None or orologio() < entro

    prezzi_finiti_woo(base, intestazioni, chiama)
    prodotti, pagina, restano, fermato = [], 1, False, False
    totale = 0
    while True:
        url = (f"{base}/wp-json/{VERSIONE_API_WOO}/products"
               f"?per_page={PER_PAGINA_WOO}&page={pagina}"
               f"&orderby=id&order=asc")
        stato, corpo, risposta = chiama("GET", url, intestazioni)
        if stato != 200:
            raise RuntimeError(spiega_risposta_woo(stato, corpo, risposta,
                                                   base))
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
        if pagina > MAX_PAGINE_CATALOGO:
            raise RuntimeError("il catalogo non finisce mai: oltre "
                               f"{MAX_PAGINE_CATALOGO} pagine")
        if not c_e_tempo():
            # il tempo e' finito fra due pagine: si consegna quel che si
            # e' letto, e qui sotto la lettura si dichiara PARZIALE
            fermato = True
            break
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
    if fermato:
        # IL TEMPO BATTE IL CONTO VERO: `X-WP-Total` direbbe «ci stanno
        # tutti» (mille contro un tetto di mille), ma le pagine dopo non
        # le abbiamo lette — e un catalogo letto a meta' preso per
        # intero spegnerebbe tutto cio' che sta oltre, per sempre
        completo = False
        avviso = _msg_lento(len(prodotti), totale)
    prodotti = prodotti[:tetto]
    # LE VARIAZIONI (set 2026), e DOPO il taglio al tetto: su Woo
    # vivono a un indirizzo loro, una chiamata per prodotto variabile,
    # quindi si chiedono solo per i prodotti che entrano davvero — la
    # prova del collegamento legge con tetto 1 e non deve bussare
    # cento volte. L'indirizzo lo componiamo NOI dall'id (un intero),
    # come ogni URL di questo lettore: niente da seguire.
    variabili = []
    for p in prodotti:
        if str(p.get("type") or "").lower() != "variable":
            continue
        try:
            pid = int(p.get("id"))
        except (TypeError, ValueError):
            continue          # senza un id da comporre resta intero: si salta
        variabili.append((pid, p))
    # LA ROTAZIONE (1 ott 2026): prima chi viene DOPO l'ultimo letto al
    # giro scorso, poi da capo — in cerchio, per id
    dopo = int((segno or {}).get("dopo") or 0)
    variabili.sort(key=lambda v: (v[0] <= dopo, v[0]))
    lette, ultimo, finito = 0, 0, False
    for pid, p in variabili:
        finito = finito or not c_e_tempo()
        if finito:
            # niente variazioni lette: il prodotto resta intero e lo dice,
            # e le sue figlie gia' in vetrina aspettano il loro giro
            p["_variazioni_al_prossimo"] = True
            continue
        p["_variazioni"] = _variazioni_woo(base, pid, intestazioni, chiama)
        lette, ultimo = lette + 1, pid
    rimaste = len(variabili) - lette
    if segno is not None:
        # il segno torna a zero quando il giro le ha lette tutte (il
        # prossimo riparte dal primo, che e' lo stesso cerchio), avanza
        # se ne ha lette alcune, e RESTA DOV'ERA se il tempo e' finito
        # prima della prima: tornare a zero rimanderebbe in fondo alla
        # fila proprio chi stava aspettando il suo turno
        segno.update(dopo=ultimo if lette and rimaste else
                     (dopo if rimaste else 0), lette=lette, rimaste=rimaste)
    if rimaste and not fermato:
        # (fermi gia' fra le pagine, l'avviso del negozio lento c'e' gia':
        # una volta basta)
        avviso = "; ".join(a for a in (
            avviso, _msg_varianti_al_prossimo(lette, len(variabili))) if a)
    return prodotti, avviso, completo


def _variazioni_woo(base: str, pid: int, intestazioni: dict, chiama) -> list:
    """Le variazioni di un prodotto variabile, tutte le pagine.

    ALZA su una risposta storta, e non torna una lista corta — per la
    ragione di tutto il lettore: le chiavi delle figlie sono
    `pid:vid`, e una lista a meta' farebbe passare le variazioni non
    lette per SPARITE dal negozio, cioe' spente per sempre. Un giro
    che fallisce si conta e si riprova fra un'ora; una sparizione
    falsa no."""
    variazioni, pagina = [], 1
    while True:
        url = (f"{base}/wp-json/{VERSIONE_API_WOO}/products/{pid}/variations"
               f"?per_page={PER_PAGINA_WOO}&page={pagina}"
               f"&orderby=id&order=asc")
        stato, corpo, _ = chiama("GET", url, intestazioni)
        if stato != 200:
            raise RuntimeError(f"WooCommerce ha risposto {stato} sulle "
                               f"varianti del prodotto {pid}")
        fetta = _prodotti_dalla_risposta(corpo)
        variazioni.extend(fetta)
        if len(fetta) < PER_PAGINA_WOO:
            return variazioni
        pagina += 1
        if pagina > MAX_PAGINE_VARIAZIONI_WOO:
            raise RuntimeError(f"il prodotto {pid} ha piu' di "
                               f"{MAX_PAGINE_VARIAZIONI_WOO * PER_PAGINA_WOO} "
                               "variazioni: non e' un catalogo che si possa leggere")


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
    dice — «se e' lo stesso oggetto, ritira quello vecchio».
    (1 ott 2026) Porta anche i valori che `_aggiorna` confronta per non
    riscrivere una riga identica."""
    return con.execute(
        "SELECT id, stato, foto, origine_foto, quantita, quantita_max, "
        "origine_stock_visto, consegna, titolo, descrizione, prezzo_eur, "
        "valuta, famiglia, famiglia_titolo, opzioni, scelte, categoria "
        "FROM annunci "
        "WHERE connettore_id=? AND origine_chiave=?",
        (connettore_id, chiave)).fetchone()


def _valori_famiglia(connettore_id: int, r: dict) -> tuple:
    """(famiglia, famiglia_titolo, opzioni) come si scrivono nella riga:
    UN posto solo, per chi scrive e per chi confronta (`_aggiorna`)."""
    fam = r.get("famiglia") or ""
    return (f"c{connettore_id}:{fam}" if fam else "",
            (r.get("famiglia_titolo") or "")[:MAX_TITOLO] if fam else "",
            json.dumps(r.get("opzioni") or [], ensure_ascii=False)
            if fam else "")


def _valore_scelte(r: dict) -> str:
    """Le scelte «Qualsiasi» della riga come si scrivono in colonna
    (19 nov 2026): '' = nessuna tendina. Un posto solo per chi scrive e
    per chi confronta, come `_valori_famiglia`."""
    return json.dumps(r["scelte"], ensure_ascii=False) \
        if r.get("scelte") else ""


def _scrivi_famiglia(con, annuncio_id: int, connettore_id: int, r: dict):
    """La famiglia della riga, a OGNI giro e su ogni stato (anche in
    revisione e venduto): la decide il catalogo letto oggi, e una
    famiglia che si scioglie torna vuota qui. La chiave porta il
    collegamento davanti, cosi' due negozi non si mescolano mai.
    Niente `modificato`: non e' un cambio del testo dell'annuncio.
    (19 nov 2026) Con la famiglia viaggiano le SCELTE «Qualsiasi»: sono
    della stessa natura (le dice il catalogo, a ogni giro)."""
    con.execute(
        "UPDATE annunci SET famiglia=?, famiglia_titolo=?, opzioni=?, "
        "scelte=? WHERE id=?", (*_valori_famiglia(connettore_id, r),
                                _valore_scelte(r), annuncio_id))


def consegna_riga(connettore: dict, digitale: bool) -> dict:
    """La consegna e i costi da scrivere su UNA riga: quelli del
    cassetto per la merce che viaggia, «digitale» e tutto a zero per
    cio' che il negozio dichiara virtuale o scaricabile (set 2026).

    E' L'UNICO POSTO che decide, e lo leggono la nascita e
    l'aggiornamento: se i due divergessero, un corso online nascerebbe
    digitale e al giro dopo tornerebbe con «🚚 Spedizione».
    ⚠️ ROVESCIA UNA DECISIONE DI AGOSTO, e va detto: la consegna
    digitale sui negozi collegati era «MAI», perche' la consegna si
    dichiara nel CASSETTO per tutto il catalogo e un negozio non puo'
    promettere «codice online» per ogni prodotto. Qui a dichiararlo e'
    il NEGOZIO, prodotto per prodotto, e il venditore del
    collegamento e' una persona su Barattolo che il bottone «consegna
    il contenuto» ce l'ha: incolla il link o il codice nell'ordine,
    come farebbe per un buono nato qui. Il cassetto continua a non
    poterlo dichiarare (`CONSEGNE_NEGOZIO` resta fisico)."""
    if digitale:
        return {"consegna": "digitale", "spedizione_eur": 0.0,
                "spedizione_sats": 0, "spedizione_punto_eur": 0.0,
                "spedizione_punto_sats": 0,
                "spedizione_punto_dichiarata": 0,
                "spedizione_extra_eur": 0.0, "spedizione_extra_sats": 0}
    # le tariffe del collegamento nella valuta che ha scelto: euro
    # ancorato o sats FISSI, con zeri nell'altra (la forma di `annunci`,
    # dove fisso batte ancorato); il `.get` sui sats e' per i banchi di
    # cartone e le righe di ieri
    return {"consegna": connettore["consegna"],
            "spedizione_eur": connettore["spedizione_eur"],
            "spedizione_sats": connettore.get("spedizione_sats") or 0,
            "spedizione_punto_eur": connettore["spedizione_punto_eur"],
            "spedizione_punto_sats":
                connettore.get("spedizione_punto_sats") or 0,
            "spedizione_punto_dichiarata":
                connettore["spedizione_punto_dichiarata"],
            "spedizione_extra_eur": connettore["spedizione_extra_eur"],
            "spedizione_extra_sats":
                connettore.get("spedizione_extra_sats") or 0}


def _foto_locali(con, annuncio_id: int, urls: list, salva_foto) -> str:
    """Scarica le foto e torna il JSON dei nomi locali. Un download
    fallito lascia l'URL com'era: meglio una foto che arriva dal
    negozio del venditore che nessuna foto (e' la regola di
    `localizza_foto`).

    SI CHIAMA FUORI DA OGNI TRANSAZIONE, ed e' la regola del 1 ott 2026
    («database is locked»): ogni download vale fino a dieci secondi, piu'
    Pillow, e sqlite ha UNO scrittore alla volta — una transazione aperta
    qui attorno teneva il mercatino intero fuori dal database per tutta
    la durata delle foto, e le rotte morivano col loro timeout. Il
    chiamante scarica PRIMA di scrivere (l'aggiornamento) o fra due
    commit brevi (la nascita). `prove_db_contesa_negozi` lo gira con una
    seconda connessione che scrive durante ogni download."""
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
                          completo: bool, max_nuovi: int | None = None) -> dict:
    """Porta il catalogo tradotto dentro `annunci`, e torna il report.

    L'ORDINE DELLE DOMANDE e' quello di `importa_venditore`, che e' il
    fratello maggiore di questa funzione: si ritrova la riga per
    chiave; se non c'e' ma esiste SPENTA, non si risuscita; altrimenti
    si aggiorna o si crea.

    QUELLO CHE NON SI RICOPRE MAI: la categoria e la sottocategoria
    gia' scelte (una scelta fatta a mano qui non si cancella ogni ora
    col silenzio di un e-commerce), e la consegna, che viene dal
    CASSETTO del collegamento e non dal negozio.
    «ALTRO» NON E' UNA SCELTA (16 nov 2026): e' la casella vuota. Una
    riga ferma li' prende la categoria che il server le ha dato
    (`r["categoria"]`: quella dichiarata nel cassetto, o quella del
    negozio quando combacia), e chi sta gia' in un'altra non si muove.

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

    `max_nuovi` e' quante righe NUOVE nascono in questo giro (None =
    nessun tetto). Non e' un fratello del tetto di lettura, e' il suo
    opposto: quello TRONCAVA la vista e mutilava il catalogo, questo
    legge tutto — quindi le sparizioni restano vere — e distribuisce
    solo l'INGRESSO in vetrina. E' anche l'unica riga che rende vera
    la promessa «il resto arriva ai giri successivi»: al giro dopo le
    righe gia' create si ritrovano per chiave e il tetto tocca alle
    prossime.
    ZERO VUOL DIRE ZERO (1 ott 2026, «negozi grandi», seconda parte):
    fino a ieri lo zero era «nessun tetto», e un giro non poteva dire
    «quest'ora i posti sono finiti» — da quando il rodaggio si conta
    all'ora (`_nuovi_per_giro` nel server) lo deve poter dire. Il
    «nessun tetto» e' None; la leva del config resta com'era (0 = nessun
    tetto), e a tradurla e' il server.
    """
    revisioni = revisioni or {}
    adesso = int(time.time())
    cid = connettore["id"]
    fonte = connettore["fonte"]
    esito = {"nuovi": 0, "aggiornati": 0, "invariati": 0, "spenti": 0,
             "riaccesi": 0, "in_revisione": 0, "rimandati": 0,
             "parziale": not completo, "saltati": [], "falliti": [],
             # (set 2026) i titoli NATI in questo giro, e quante righe
             # hanno cambiato consegna: il venditore legge COSA e'
             # entrato, non solo quanti
             "entrati": [], "consegna_corretta": 0,
             # (1 ott 2026) i prodotti di cui la lettura a tempo non ha
             # chiesto le varianti: un conto, non una voce per uno —
             # cinquecento righe «al prossimo giro» fra i saltati
             # sarebbero un report da cinquanta KB e un allarme falso
             "varianti_al_prossimo": 0,
             # (1 ott 2026, seconda parte) i prodotti in bozza o nascosti
             # sul negozio che non sono mai entrati: un conto, non una
             # riga — e non nascono, vedi `_una_riga`
             "non_pubblicati": 0,
             # (11 ott 2026, cantiere foto-obbligatorie) i prodotti mai
             # entrati che sul negozio non hanno nemmeno un'immagine:
             # un conto anche loro, e non nascono finche' non ne hanno
             "senza_foto": 0}
    viste = set()
    # i padri le cui figlie questo giro non le ha VISTE ne' le ha
    # cercate: sul negozio ci sono, e non si spengono (vedi sotto)
    intatte = set()
    # il tempo passato a SCARICARE si conta a parte: il respiro misura
    # quello passato dentro il database, non l'attesa di un negozio lento
    in_foto = [0.0]

    def scarica(*a):
        dal = time.monotonic()
        try:
            return salva_foto(*a)
        finally:
            in_foto[0] += time.monotonic() - dal

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
        if r.get("_figlie_intatte"):
            intatte.add(r["origine_chiave"])
            esito["varianti_al_prossimo"] += 1
            continue
        if r.get("saltato_perche"):
            esito["saltati"].append({"titolo": r.get("titolo", "")[:60],
                                     "perche": r["saltato_perche"]})
            continue
        chiave = r["origine_chiave"]
        scritte, dal, foto_prima = con.total_changes, time.monotonic(), in_foto[0]
        try:
            _una_riga(con, connettore, r, scarica, revisioni, esito,
                      adesso,
                      max_nuovi is None or esito["nuovi"] < max_nuovi)
        except Exception as e:
            # Una riga che esplode e' una voce del report, mai il giro
            # morto: e' il patto di `_crea_riga_con_guardia`
            # dell'import CSV.
            esito["falliti"].append({"titolo": r.get("titolo", "")[:60],
                                     "perche": str(e)[:120]})
            print(f"    ⚠️ riga saltata ({r.get('titolo', '')[:40]}): {e}")
        # IL RESPIRO (vedi RESPIRO_MAX_S): solo dopo una riga che ha
        # scritto, e mai a transazione aperta — li' il lucchetto e' gia'
        # preso, e una pausa lo terrebbe di piu' invece di lasciarlo
        if con.total_changes != scritte and not con.in_transaction:
            _respira(min(time.monotonic() - dal - (in_foto[0] - foto_prima),
                         RESPIRO_MAX_S))

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
        # A LOTTI, con un commit ogni LOTTO_SPEGNIMENTI (1 ott 2026):
        # una vetrina intera spenta in una transazione sola e' una
        # scrittura lunga, e le scritture lunghe sono vietate in questo
        # giro — il database e' di tutti, non del connettore. La lista
        # si legge tutta PRIMA (`fetchall`) per non tenere un cursore
        # aperto sull'annunci mentre si scrive sopra. E fra un lotto e
        # l'altro il respiro, come fra le righe qui sopra.
        lotto_dal = time.monotonic()
        for riga in con.execute(
                "SELECT id, titolo, origine_chiave FROM annunci "
                "WHERE connettore_id=? AND stato IN ('attivo','revisione')",
                (cid,)).fetchall():
            if riga["origine_chiave"] in viste:
                continue
            # LE FIGLIE DI CHI ASPETTA IL SUO TURNO (1 ott 2026, la
            # lettura a tempo): le righe `pid:vid` del prodotto di cui
            # questo giro non ha chiesto le variazioni non sono in
            # `viste` perche' NESSUNO le ha cercate, non perche' siano
            # sparite. (La riga `pid` di quando era un prodotto semplice
            # sta gia' in `viste`, col padre: si spegnera' al giro che
            # legge le figlie, come ogni cambio di forma.)
            if str(riga["origine_chiave"] or "").split(":")[0] in intatte:
                continue
            spegni_annuncio(con, riga["id"], "rimosso")
            esito["spenti"] += 1
            print(f"    🗑 tolto dal negozio: {riga['titolo'][:50]}")
            if esito["spenti"] % LOTTO_SPEGNIMENTI == 0:
                con.commit()
                _respira(min(time.monotonic() - lotto_dal, RESPIRO_MAX_S))
                lotto_dal = time.monotonic()
    else:
        print(f"    ⏸ lettura parziale: le sparizioni non si giudicano")

    con.commit()
    print(f"  🏪 {fonte} #{cid}: {esito['nuovi']} nuovi, "
          f"{esito['aggiornati']} aggiornati, {esito['invariati']} invariati, "
          f"{esito['spenti']} spenti, {esito['rimandati']} rimandati, "
          f"{len(esito['saltati'])} saltati"
          + (f", {esito['senza_foto']} senza foto (non entrano)"
             if esito["senza_foto"] else "")
          + (f", {esito['varianti_al_prossimo']} con le varianti al "
             f"prossimo giro" if esito["varianti_al_prossimo"] else ""))
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

    # --- LE FOTO PRIMA DI OGNI SCRITTURA (1 ott 2026) -----------------
    # Sulla riga che c'e' gia' i download stanno QUI, prima di
    # `rifletti_pendenti`: quella e' la prima scrittura della riga, e
    # da li' in poi la connessione ha una transazione aperta — cioe'
    # il lucchetto di scrittura dell'intero database — finche' non si
    # fa commit. Scaricare dentro quel tratto, com'era prima, teneva il
    # mercatino fermo per tutta la durata delle foto. Niente foto
    # nuove = niente download, come sempre.
    foto = None
    if gia:
        foto_url = json.dumps(r["foto"]) if r["foto"] else ""
        if foto_url and foto_url == (gia["origine_foto"] or ""):
            foto = gia["foto"]          # stesse foto: niente ri-download
        else:
            foto = _foto_locali(con, gia["id"], r["foto"], salva_foto)

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
        _aggiorna(con, gia, r, connettore, foto, marchio, quantita,
                  esito, adesso)
        return

    # --- la riga nuova ------------------------------------------------
    # IL TETTO STA QUI E NON PIU' IN ALTO, ed e' la differenza fra
    # distribuire e mutilare: la riga e' stata LETTA (quindi e' in
    # `viste` e non passa per sparita), semplicemente non nasce oggi.
    # Il giro dopo si ritrova per chiave — o nasce, se il tetto la
    # lascia passare.
    # E LA RIGA `rimandata` (1 ott 2026, «negozi grandi») e' lo stesso
    # tetto visto da prima: il server non l'ha fatta guardare all'AI
    # perche' stava oltre i posti di questo giro (`_righe_da_giudicare`),
    # e una riga che nessuno ha guardato NON NASCE — nemmeno quando il
    # conto dei nuovi lascerebbe un posto libero (una riga giudicata che
    # esplode lo libera, e non tocca a lei prenderlo).
    # LA BOZZA NON NASCE (1 ott 2026, decisione di Andrea). Un prodotto
    # che il negozio non mostra — bozza, privato, nascosto dallo scaffale
    # — e che qui non e' mai entrato nasceva 'rimosso' dalla tappa 2, e
    # 'rimosso' e' la lapide: il giorno che il negoziante lo pubblicava,
    # lo scudo qui sopra lo teneva fuori per sempre (l'imperfezione
    # dichiarata in ARCHITETTURA). Adesso non nasce niente: al giro in
    # cui il negozio lo pubblica e' una riga mai vista come le altre, e
    # nasce attiva. Prima del tetto, apposta: una bozza non aspetta un
    # posto (non lo prende nemmeno: `_righe_da_giudicare` la lascia fuori
    # dall'AI e dai posti).
    if not r["attivo"]:
        esito["non_pubblicati"] += 1
        return
    # IL PRODOTTO SENZA FOTO NON NASCE (11 ott 2026, cantiere
    # foto-obbligatorie, decisione di Andrea): la regola del foglio
    # «Pubblica» — almeno una foto per entrare in vetrina — vale anche
    # per il catalogo di un negozio collegato. Come la bozza qui sopra
    # non lascia nessuna riga (niente lapide: al giro in cui il negozio
    # gli da' un'immagine e' una riga mai vista come le altre, e nasce)
    # e non prende un posto ne' una chiamata all'AI
    # (`_righe_da_giudicare` lo lascia fra le note). Si CONTA, e il
    # conto arriva al venditore: un prodotto che non entra senza un
    # perche' si legge come un import rotto.
    # SOLO LA NASCITA: chi e' gia' in vetrina e perde le foto sul
    # negozio resta com'e' (il ramo di sopra, che non passa di qui) —
    # gli annunci gia' online non si spengono per questa regola.
    if not r["foto"]:
        esito["senza_foto"] += 1
        return
    if not puo_creare or r.get("rimandata"):
        esito["rimandati"] += 1
        return
    stato = "revisione" if marchio else "attivo"
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
    # la consegna: del cassetto, o «digitale» se il negozio lo dichiara
    # (set 2026) — un giudice solo, lo stesso dell'aggiornamento
    cons = consegna_riga(connettore, bool(r.get("digitale")))
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,foto,valuta,prezzo_eur,quantita,quantita_max,"
        "consegna,spedizione_eur,spedizione_sats,spedizione_punto_eur,"
        "spedizione_punto_sats,spedizione_punto_dichiarata,"
        "spedizione_extra_eur,spedizione_extra_sats,"
        "fonte,connettore_id,origine_chiave,origine_foto,"
        "origine_stock_visto,creato,modificato,stato) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (connettore["tg_id"], r["titolo"], r["descrizione"],
         r.get("categoria") or "Altro", r["prezzo_sats"],
         # le foto: gli URL del negozio, finche' il secondo commit (sotto)
         # non ci mette i nomi locali
         connettore["zona"], json.dumps(r["foto"]) if r["foto"] else "",
         "eur", r["prezzo_eur"],
         1 if quantita is None else quantita,
         1 if quantita is None else quantita,
         # LE TARIFFE nella valuta del collegamento (euro ancorato o sats
         # FISSI) o tutto a zero sul digitale: le decide `consegna_riga`,
         # lo stesso giudice dell'aggiornamento
         cons["consegna"], cons["spedizione_eur"], cons["spedizione_sats"],
         cons["spedizione_punto_eur"], cons["spedizione_punto_sats"],
         cons["spedizione_punto_dichiarata"],
         cons["spedizione_extra_eur"], cons["spedizione_extra_sats"],
         connettore["fonte"], cid, chiave,
         json.dumps(r["foto"]) if r["foto"] else "",
         -1 if r.get("quantita") is None else r["quantita"],
         adesso, adesso, stato))
    nuovo = cur.lastrowid
    _scrivi_famiglia(con, nuovo, cid, r)
    # LA NASCITA E' IN DUE COMMIT BREVI (1 ott 2026), e le foto stanno
    # IN MEZZO, fuori da tutt'e due: il nome del file vuole l'id, quindi
    # non si possono scaricare prima dell'insert — e scaricarle dentro
    # la transazione, com'era, teneva il lucchetto di scrittura del
    # database per dieci secondi a foto (le rotte morivano «database
    # is locked», 1 ott 2026, il giro di STACKER NEWS). La riga nasce
    # COMPLETA al primo commit, con gli URL del negozio al posto delle
    # foto (lo stato di un download fallito, che la vetrina sa gia'
    # mostrare); il secondo commit ci mette i nomi locali. Un crash fra
    # i due lascia esattamente quel che lascerebbe un download fallito.
    con.commit()          # commit per riga: un crash a meta' giro
    #                       lascia solo annunci completi
    foto = _foto_locali(con, nuovo, r["foto"], salva_foto)
    if foto:
        con.execute("UPDATE annunci SET foto=? WHERE id=?", (foto, nuovo))
        con.commit()
    esito["nuovi"] += 1
    if marchio:
        esito["in_revisione"] += 1
    # il titolo nel report, con la sua strada: e' quel che il
    # venditore legge per sapere COSA e' entrato (i primi, per non
    # gonfiare il JSON: il conto vero e' `nuovi`)
    if len(esito["entrati"]) < MAX_ENTRATI_REPORT:
        esito["entrati"].append({"titolo": r["titolo"][:60],
                                 "digitale": bool(r.get("digitale")),
                                 "stato": stato})
    print(f"    🏪 {r['titolo'][:50]} — {r['prezzo_eur']:.2f} € "
          f"[{r.get('categoria') or 'Altro'}]"
          f"{' · digitale' if r.get('digitale') else ''}")


def _aggiorna(con, gia, r: dict, connettore: dict, foto: str, marchio,
              quantita, esito: dict, adesso: int):
    """La riga c'e' gia': si ricopre il contenuto (la fonte comanda) e
    si lascia stare tutto il resto.

    `foto` ARRIVA GIA' PRONTA (il JSON dei nomi locali, o quello di
    ieri se gli URL non sono cambiati): la scarica `_una_riga` prima
    di qualunque scrittura, perche' qui dentro la transazione e' gia'
    aperta e un download la terrebbe aperta per tutto il mercatino
    (1 ott 2026, «database is locked»).

    SI SCRIVE SOLO CIO' CHE E' CAMBIATO (1 ott 2026, decisione di
    Andrea). Fino a ieri ogni giro riscriveva OGNI riga gia' in vetrina,
    identica o no: duemiladuecento commit all'ora per un negozio grande,
    e `modificato` spostato a ogni ora — la sitemap diceva ai motori che
    tutto il catalogo era cambiato, e la scheda «aggiornato un'ora fa» a
    chi guardava. Adesso ogni colonna si scrive solo se e' diversa, e
    `modificato` si muove solo quando cambia quel che il compratore
    legge — titolo, descrizione, prezzo in euro, foto — come per un
    annuncio fatto a mano (la giacenza, la famiglia e lo stato si
    scrivono senza toccarla, la regola gia' scritta in
    `_scrivi_famiglia`). Il cambio BTC che si muove NON e' un cambio:
    il prezzo vero di una riga in euro e' `prezzo_eur` al cambio vivo, e
    `prezzo_sats` e' il ripiego della pubblicazione, come per gli
    annunci nativi. Una riga identica non scrive niente, non chiude
    nessuna transazione e non respira: e' un «invariato» nel report."""
    foto_url = json.dumps(r["foto"]) if r["foto"] else ""
    visto = -1 if r.get("quantita") is None else r["quantita"]
    prima = con.total_changes
    if ((r["titolo"], r["descrizione"], round(float(r["prezzo_eur"] or 0), 2),
         foto or "", foto_url, "eur")
            != (gia["titolo"], gia["descrizione"],
                round(float(gia["prezzo_eur"] or 0), 2), gia["foto"] or "",
                gia["origine_foto"] or "", gia["valuta"])):
        con.execute(
            "UPDATE annunci SET titolo=?, descrizione=?, prezzo_sats=?, "
            "valuta='eur', prezzo_eur=?, foto=?, origine_foto=?, "
            "modificato=? WHERE id=?",
            (r["titolo"], r["descrizione"], r["prezzo_sats"], r["prezzo_eur"],
             foto, foto_url, adesso, gia["id"]))
    # la giacenza letta di la' (la usa `rifletti_pendenti` al giro dopo)
    if visto != gia["origine_stock_visto"]:
        con.execute("UPDATE annunci SET origine_stock_visto=? WHERE id=?",
                    (visto, gia["id"]))
    if quantita is not None and (quantita != gia["quantita"]
                                 or quantita > (gia["quantita_max"] or 0)):
        con.execute("UPDATE annunci SET quantita=?, "
                    "quantita_max=MAX(quantita_max,?) WHERE id=?",
                    (quantita, quantita, gia["id"]))
    if (*_valori_famiglia(connettore["id"], r), _valore_scelte(r)) != (
            gia["famiglia"] or "", gia["famiglia_titolo"] or "",
            gia["opzioni"] or "", gia["scelte"] or ""):
        _scrivi_famiglia(con, gia["id"], connettore["id"], r)
    # --- la categoria (16 nov 2026) -----------------------------------
    # SI RIEMPIE SOLO LA CASELLA VUOTA: una riga in «Altro» (cioe' nata
    # quando nessuno sapeva dove metterla) prende quella che il server
    # ha deciso per lei; una riga che sta gia' altrove — spostata da un
    # moderatore, o dal cassetto — resta dov'e'. Senza `modificato`:
    # il compratore non legge niente di nuovo nella scheda.
    cat = r.get("categoria") or ""
    if (gia["categoria"] or "Altro") == "Altro" and cat and cat != "Altro":
        # (la sottocategoria di «Altro» e' gia' vuota: non c'e' niente
        # da azzerare, e un nuovo reparto la trova vuota come alla
        # nascita)
        con.execute("UPDATE annunci SET categoria=? WHERE id=?",
                    (cat, gia["id"]))
    # --- la consegna (set 2026) ---------------------------------------
    # LA RIGA CHE CORREGGE IL PREGRESSO: un corso online importato
    # ieri con «🚚 Spedizione» e «🤝 Ritiro» torna digitale al primo
    # giro dopo il deploy, e un prodotto che il negozio smette di
    # dichiarare virtuale riprende la consegna del cassetto. Si tocca
    # SOLO quando la strada cambia: la consegna fisica la scrive il
    # cassetto (`_applica_dichiarazione`), e ricoprirla ogni ora da qui
    # sarebbe un secondo scrittore sulla stessa colonna.
    digitale = bool(r.get("digitale"))
    if digitale != (gia["consegna"] == "digitale"):
        cons = consegna_riga(connettore, digitale)
        con.execute(
            "UPDATE annunci SET consegna=?, spedizione_eur=?, "
            "spedizione_sats=?, spedizione_punto_eur=?, "
            "spedizione_punto_sats=?, spedizione_punto_dichiarata=?, "
            "spedizione_extra_eur=?, spedizione_extra_sats=?, "
            "taglia_pacco='' WHERE id=?",
            (cons["consegna"], cons["spedizione_eur"],
             cons["spedizione_sats"], cons["spedizione_punto_eur"],
             cons["spedizione_punto_sats"],
             cons["spedizione_punto_dichiarata"],
             cons["spedizione_extra_eur"], cons["spedizione_extra_sats"],
             gia["id"]))
        esito["consegna_corretta"] += 1
        print(f"    ↔ consegna corretta ({cons['consegna'] or 'cassetto'}): "
              f"{r['titolo'][:50]}")
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
    elif gia["stato"] == "venduto" and digitale and r.get("quantita") is None:
        # IL DIGITALE SENZA MAGAZZINO NON SI ESAURISCE (set 2026): un
        # PDF che il negozio non conta nasce «pezzo unico» come ogni
        # stock ignoto, e dopo la prima vendita resterebbe «venduto»
        # per sempre — il negozio non lo rifornisce, perche' per lui
        # non e' mai finito (`instock` senza numero). Qui torna in
        # vetrina al giro dopo, con un pezzo: quel che il negozio
        # dice («c'e'») e non piu' di quello. Fra la vendita e il giro
        # e' fuori per un'ora al massimo, ed e' il prezzo dichiarato
        # di non inventare un numero di copie.
        con.execute("UPDATE annunci SET stato='attivo', quantita=1 "
                    "WHERE id=?", (gia["id"],))
        esito["riaccesi"] += 1
        print(f"    ↑ digitale di nuovo in vetrina: {r['titolo'][:50]}")
    elif gia["stato"] == "attivo" and quantita == 0:
        # l'invariante di casa: venduto <=> quantita = 0
        con.execute("UPDATE annunci SET stato='venduto' WHERE id=?",
                    (gia["id"],))
    # IL COMMIT SOLO SE QUALCOSA SI E' MOSSO — anche prima di qui:
    # `rifletti_pendenti` in `_una_riga` puo' aver aperto la transazione
    if con.total_changes != prima or con.in_transaction:
        con.commit()
        esito["aggiornati"] += 1
    else:
        esito["invariati"] += 1
