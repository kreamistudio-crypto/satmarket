# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI CONNETTORI: il giro vero su un negozio di cartone.

`prove.py` difende la FORMA — che il giudice sia uno, che le guardie
non si allentino, che una colonna nasca additiva. Quello che non puo'
fare e' far GIRARE il sync: le sue prove non hanno un database, non
hanno un catalogo e non scrivono un annuncio.

Questo script chiude quel buco. Fa partire il SERVER VERO su un
database usa-e-getta, con due negozi finti al posto dell'API — uno
Shopify e uno WooCommerce — e chiede le cose che solo l'esecuzione
puo' dire.

LA PROVA REGINA DELLA FASE 1 e' una sola: **una vendita fatta qui non
viene rialzata dal giro dopo**. Il sync ricopre la giacenza dalla
lettura esterna, quindi senza il registro delle uscite ogni acquisto
su Barattolo verrebbe annullato entro l'ora — e sul pezzo unico il
'venduto' risorgerebbe, rimettendo in vendita una cosa gia' venduta.
Non fallisce da solo: nessuna eccezione, nessun log, solo un numero
che torna su.

Le altre domande che si fanno insieme a quella:
  · un catalogo che non si e' potuto LEGGERE non e' un catalogo
    vuoto — un errore di rete non deve spegnere la vetrina;
  · un prodotto tolto dal negozio sparisce anche qui, e i suoi ordini
    mai pagati si annullano;
  · uno gia' rimosso QUI non risorge, mentre un esaurito che viene
    rifornito sul negozio torna in vetrina (la differenza dichiarata
    con Nostr);
  · la moderazione si paga UNA volta: al secondo giro, a testo
    invariato, all'AI non si chiede niente;
  · quel che il negozio non dichiara non si inventa (lo stock non
    tracciato) e quel che non sappiamo trattare si salta DICENDOLO
    (i multi-variante).

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. L'API del
negozio non viene mai chiamata — c'e' un catalogo in memoria — quindi
lo script gira senza rete e senza chiavi.

COSA NON PUO' DIRE, ed e' dichiarato: come si comporta l'API vera (il
rate limit di Shopify, il suo header `Link` contro un negozio in
carne e ossa, i permessi veri di un token, i certificati di un Woo
self-hosted) e la moderazione vera. Per quelle serve il rodaggio con
uno store di sviluppo, prima di accendere la leva.

USO:  python collaudo_connettori.py
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
CHIAMATE_AI = []        # quante volte la moderazione e' stata chiamata
NOTIFICHE = []          # (tg_id, testo)

CAMBIO = 100_000.0      # 1 BTC = 100.000 €, cioe' 1000 sats = 1 €
VENDITORE = 222


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# --- IL NEGOZIO DI CARTONE -------------------------------------------
# Un catalogo in memoria che si comporta come l'API di Shopify: stessa
# forma della risposta, stesso header di paginazione. Si cambia da
# fuori (CATALOGO[:] = [...]) per raccontare cosa succede sul negozio
# fra un giro e l'altro.
CATALOGO = []
ERRORE_API = [None]     # se pieno, l'API alza: la rete che cade
LETTURE = []            # gli URL chiesti, per contare le pagine

# --- IL WOOCOMMERCE DI CARTONE ---------------------------------------
# Un secondo negozio, con l'altro dialetto e con la cosa che Shopify
# non ha: le due impostazioni da cui dipende il significato di
# `price`. `IVA_WOO` a 'no' vuol dire «prezzi scritti al NETTO», cioe'
# il caso in cui il catalogo NON si deve leggere.
CATALOGO_WOO = []
TASSE_WOO = ["yes"]     # woocommerce_calc_taxes
IVA_WOO = ["yes"]       # woocommerce_prices_include_tax


def prodotto(pid, titolo, prezzo="7.50", stock=12, stato="active",
             varianti=1, gestito=True, foto=("https://cdn.esempio/a.jpg",),
             tipo="Alimenti e bevande", desc="<p>Buono</p>"):
    v = [{"id": pid * 10 + k, "price": prezzo,
          "inventory_quantity": stock,
          "inventory_management": "shopify" if gestito else None,
          "inventory_item_id": pid * 100 + k}
         for k in range(varianti)]
    return {"id": pid, "title": titolo, "body_html": desc, "status": stato,
            "product_type": tipo, "variants": v,
            "images": [{"src": u} for u in foto]}


def prodotto_woo(pid, nome, prezzo="7.50", stock=12, gestito=True,
                 tipo="simple", stato="publish", visibile="visible",
                 disponibile="instock", desc="<p>Buono</p>",
                 foto=("https://cdn.esempio/w.jpg",), categoria="Casa"):
    return {"id": pid, "name": nome, "description": desc, "type": tipo,
            "status": stato, "catalog_visibility": visibile,
            "price": prezzo, "regular_price": prezzo,
            "manage_stock": gestito,
            "stock_quantity": stock if gestito else None,
            "stock_status": disponibile,
            "images": [{"src": u} for u in foto],
            "categories": [{"id": 1, "name": categoria}]}


def api_finta(metodo, url, intestazioni):
    """Al posto di `chiama_api_negozio`. Non guarda le credenziali:
    qui non si prova l'autenticazione, si prova il giro — a smistare
    e' l'indirizzo, che i due dialetti costruiscono diverso."""
    LETTURE.append(url)
    if ERRORE_API[0]:
        raise RuntimeError(ERRORE_API[0])
    if "/wp-json/" not in url:
        return 200, {"products": list(CATALOGO)}, {}
    # --- WooCommerce ---
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes",
                                "value": TASSE_WOO[0]}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax",
                                "value": IVA_WOO[0]}]}, {}
    return (200, {"lista": list(CATALOGO_WOO)},
            {"X-WP-Total": str(len(CATALOGO_WOO))})


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-connettori-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME e lascia passare solo INCOLLA_QUI
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    # LA LEVA ACCESA, che e' l'unica differenza col mondo di oggi: in
    # produzione nasce False apposta, qui si prova il giro
    cfg.CONNETTORI_NEGOZIO_APERTI = True
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    server.init_db()

    # il trasporto: il negozio di cartone al posto della rete
    server.chiama_api_negozio = api_finta

    # le foto: non si scarica niente, si annota il nome che avrebbe
    def foto_finta(annuncio_id, indice, url):
        return f"a{annuncio_id}_{indice}.jpg"
    server._salva_foto_connettore = foto_finta

    # il cambio, senza CoinGecko
    server.cambio_per_import = lambda: {"EUR": CAMBIO, "USD": CAMBIO}

    # la moderazione: si CONTA e si passa. Il verdetto vero lo prova
    # collaudo_impersonazione.py, che vuole la chiave; qui interessa
    # QUANTE volte la si chiama — cioe' che si paghi una volta sola.
    async def lotto_finto(voci):
        CHIAMATE_AI.append(len(voci))
        return {}
    server.moderazione_ai_lotto = lotto_finto

    async def niente(*a, **k):
        return None
    server.notifica_admin = niente

    async def annota(tg_id, testo, *a, **k):
        NOTIFICHE.append((tg_id, testo))
    server.notifica = annota
    return db


def collega(fonte="shopify", url="mio.myshopify.com", consegna="spedizione",
            zona="Carmagnola (TO)"):
    """Scrive il collegamento a mano: l'endpoint arriva alla tappa 5,
    e quel che si prova qui e' il GIRO."""
    # ogni piattaforma ha la sua busta: Shopify un token, Woo una
    # chiave e un segreto — ed e' il LETTORE a sapere che forma hanno
    chiavi = ({"consumer_key": "ck_finta",
               "consumer_secret": "cs_segretissima"} if fonte == "woo"
              else {"token": "shpat_finto"})
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,zona,creato) VALUES(?,?,?,?,?,?,?,?)",
        (VENDITORE, fonte, url,
         SRV._cifra_contenuto(json.dumps(chiavi)),
         consegna, 5.0, zona, int(time.time())))
    con.commit()
    cid = cur.lastrowid
    con.close()
    return cid


def giro():
    """Un giro di sync, come lo farebbe l'orologio."""
    SRV._prossimo_giro_connettori = 0.0
    asyncio.run(SRV.sincronizza_connettori())


def annunci(cid=None):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    q = ("SELECT * FROM annunci WHERE connettore_id=? ORDER BY id"
         if cid else "SELECT * FROM annunci ORDER BY id")
    righe = [dict(r) for r in con.execute(q, (cid,) if cid else ())]
    con.close()
    return righe


def uno(cid, chiave):
    for a in annunci(cid):
        if a["origine_chiave"] == str(chiave):
            return a
    return None


def main():
    print("=" * 62)
    print("  IL COLLAUDO DEI CONNETTORI")
    print("=" * 62)
    avvio()
    con = SRV.db()
    con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio) "
                "VALUES(?,?,?)", (VENDITORE, "Il Negozio", "abc123"))
    con.commit()
    con.close()
    cid = collega()

    # ---- 1. il primo giro -------------------------------------------
    print("\n[il primo giro: il catalogo diventa vetrina]")
    CATALOGO[:] = [
        prodotto(1, "Miele di castagno", "7.50", stock=12),
        prodotto(2, "Olio EVO 500ml", "12.00", stock=3),
        prodotto(3, "Maglietta", "20.00", varianti=3),      # multi-variante
        prodotto(4, "Birra artigianale", "4.00", gestito=False),
        prodotto(5, "Bozza mai pubblicata", "9.00", stato="draft"),
    ]
    giro()
    righe = annunci(cid)
    prova("entrano i prodotti trattabili (il multi-variante no)",
          {"Miele di castagno", "Olio EVO 500ml", "Birra artigianale"},
          {a["titolo"] for a in righe if a["stato"] == "attivo"})
    miele = uno(cid, 1)
    prova("il prezzo e' il listino in EURO", (7.5, "eur"),
          (miele["prezzo_eur"], miele["valuta"]))
    prova("...e i sats sono l'equivalente al cambio del giro", 7_500,
          miele["prezzo_sats"])
    prova("la giacenza arriva dal negozio", 12, miele["quantita"])
    prova("l'origine e' scritta", ("shopify", cid, "1"),
          (miele["fonte"], miele["connettore_id"], miele["origine_chiave"]))
    prova("la consegna viene dal CASSETTO, non dal negozio",
          ("spedizione", 5.0, "Carmagnola (TO)"),
          (miele["consegna"], miele["spedizione_eur"], miele["zona"]))
    prova("la categoria nasce «Altro» (la sceglie la coda, non il "
          "product_type)", "Altro", miele["categoria"])
    prova("la descrizione e' spogliata dell'HTML", "Buono",
          miele["descrizione"])
    birra = uno(cid, 4)
    prova("lo stock NON tracciato non si inventa: resta 1", 1,
          birra["quantita"])
    prova("...e si annota che non lo sappiamo", -1,
          birra["origine_stock_visto"])
    prova("la bozza non entra in vetrina", "rimosso",
          uno(cid, 5)["stato"])
    prova("il multi-variante non diventa un annuncio", None, uno(cid, 3))
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (cid,)
    ).fetchone()[0])
    con.close()
    prova("...ma il report lo dice, col motivo",
          ["ha 3 varianti"],
          [s["perche"] for s in esito["saltati"]
           if s["titolo"].startswith("Maglietta")])
    prova("il venditore riceve UN riepilogo", 1, len(NOTIFICHE))

    # ---- 2. il secondo giro, a catalogo fermo ------------------------
    print("\n[il secondo giro: la moderazione si paga una volta sola]")
    prima = len(CHIAMATE_AI)
    giro()
    prova("a testo invariato all'AI non si chiede niente", prima,
          len(CHIAMATE_AI))
    prova("...e non nasce nessun doppione", 4, len(annunci(cid)))
    prova("...ne' un secondo riepilogo (niente e' successo)", 1,
          len(NOTIFICHE))

    # ---- 3. il prezzo cambia sul negozio -----------------------------
    print("\n[il negozio si muove: prezzo e giacenza]")
    CATALOGO[0] = prodotto(1, "Miele di castagno", "9.00", stock=10)
    giro()
    miele = uno(cid, 1)
    prova("il prezzo nuovo arriva qui", (9.0, 9_000),
          (miele["prezzo_eur"], miele["prezzo_sats"]))
    prova("...e cosi' la giacenza", 10, miele["quantita"])

    # ---- 4. LA PROVA REGINA ------------------------------------------
    print("\n[la prova regina: una vendita qui non si rialza]")
    # si vende UN pezzo su Barattolo: lo stock locale scala e resta la
    # pendente, che e' quel che la fase 2 drenera' verso il negozio
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=quantita-1 WHERE id=?",
                (miele["id"],))
    con.execute("INSERT INTO connettori_uscite(connettore_id,annuncio_id,"
                "ordine_id,delta,tipo,stato,creato) "
                "VALUES(?,?,?,?,'vendita','pendente',?)",
                (cid, miele["id"], 4242, -1, int(time.time())))
    con.commit()
    con.close()
    prova("dopo la vendita qui la giacenza e' scesa", 9,
          uno(cid, 1)["quantita"])
    # il negozio non sa ancora niente: la sua lettura dice ancora 10
    giro()
    prova("il sync NON la rialza (la pendente si sottrae)", 9,
          uno(cid, 1)["quantita"])
    # il venditore riallinea il suo magazzino: adesso di la' sono 9
    CATALOGO[0] = prodotto(1, "Miele di castagno", "9.00", stock=9)
    giro()
    prova("quando il venditore riallinea, il conto resta giusto", 9,
          uno(cid, 1)["quantita"])

    # ---- 5. il pezzo unico venduto qui -------------------------------
    print("\n[il pezzo unico venduto qui non risorge]")
    olio = uno(cid, 2)
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=0, stato='venduto' WHERE id=?",
                (olio["id"],))
    con.execute("INSERT INTO connettori_uscite(connettore_id,annuncio_id,"
                "ordine_id,delta,tipo,stato,creato) "
                "VALUES(?,?,?,?,'vendita','pendente',?)",
                (cid, olio["id"], 4243, -3, int(time.time())))
    con.commit()
    con.close()
    giro()   # sul negozio sono ancora 3
    olio = uno(cid, 2)
    prova("resta venduto, e la giacenza resta a zero",
          ("venduto", 0), (olio["stato"], olio["quantita"]))

    # ---- 6. il rifornimento vero -------------------------------------
    print("\n[il rifornimento sul negozio riaccende l'annuncio]")
    con = SRV.db()
    con.execute("UPDATE connettori_uscite SET stato='riflessa' "
                "WHERE annuncio_id=?", (olio["id"],))
    con.commit()
    con.close()
    CATALOGO[1] = prodotto(2, "Olio EVO 500ml", "12.00", stock=6)
    giro()
    olio = uno(cid, 2)
    prova("torna in vetrina con la giacenza vera", ("attivo", 6),
          (olio["stato"], olio["quantita"]))

    # ---- 7. la sparizione --------------------------------------------
    print("\n[il prodotto tolto dal negozio sparisce anche qui]")
    con = SRV.db()
    con.execute("INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
                "prezzo_sats,stato,creato,aggiornato) "
                "VALUES(?,?,?,?,'creato',?,?)",
                (uno(cid, 4)["id"], 111, VENDITORE, 4000,
                 int(time.time()), int(time.time())))
    con.commit()
    con.close()
    CATALOGO[:] = [c for c in CATALOGO if c["id"] != 4]
    giro()
    prova("l'annuncio si spegne", "rimosso", uno(cid, 4)["stato"])
    con = SRV.db()
    stato_ordine = con.execute(
        "SELECT stato FROM ordini WHERE annuncio_id=?",
        (uno(cid, 4)["id"],)).fetchone()[0]
    con.close()
    prova("...e l'ordine mai pagato si annulla", "annullato", stato_ordine)

    # ---- 8. lo scudo anti-resurrezione -------------------------------
    print("\n[quel che e' stato tolto qui non torna da solo]")
    # il prodotto torna sul negozio, e per giunta col titolo cambiato
    CATALOGO.append(prodotto(4, "Birra artigianale IPA", "4.00",
                             gestito=False))
    giro()
    prova("il prodotto rimesso sul negozio NON risorge", "rimosso",
          uno(cid, 4)["stato"])
    # ...e NON si continua a lavorarci sopra: senza lo scudo la riga
    # verrebbe aggiornata lo stesso — titolo riscritto, foto
    # riscaricate — restando invisibile. Il titolo vecchio e' la prova
    # che la riga e' stata SALTATA e non solo lasciata spenta.
    prova("...e non si aggiorna nemmeno", "Birra artigianale",
          uno(cid, 4)["titolo"])
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (cid,)
    ).fetchone()[0])
    con.close()
    prova("...e il report dice perche'",
          ["gia' rimosso qui: non si ricrea da solo"],
          [s["perche"] for s in esito["saltati"]
           if s["titolo"].startswith("Birra")])

    # ---- 9. la rete che cade -----------------------------------------
    print("\n[un catalogo che non si legge non e' un catalogo vuoto]")
    vivi = [a["id"] for a in annunci(cid) if a["stato"] == "attivo"]
    ERRORE_API[0] = "connessione rifiutata"
    giro()
    ERRORE_API[0] = None
    prova("nessun annuncio si spegne", vivi,
          [a["id"] for a in annunci(cid) if a["stato"] == "attivo"])
    con = SRV.db()
    c = con.execute("SELECT errori_di_fila, stato, ultimo_errore "
                    "FROM connettori WHERE id=?", (cid,)).fetchone()
    con.close()
    prova("...ma l'errore si conta e si scrive", (1, "attivo"),
          (c[0], c[1]))
    prova("...senza mai il token nel messaggio", False,
          "shpat_finto" in (c[2] or ""))

    # ---- 10. il collegamento rotto -----------------------------------
    print("\n[cinque giri a vuoto: il collegamento si dichiara rotto]")
    ERRORE_API[0] = "connessione rifiutata"
    for _ in range(4):
        giro()
    ERRORE_API[0] = None
    con = SRV.db()
    stato = con.execute("SELECT stato FROM connettori WHERE id=?",
                        (cid,)).fetchone()[0]
    con.close()
    prova("il collegamento passa in errore", "errore", stato)
    prova("...e il venditore lo viene a sapere UNA volta", 1,
          len([n for n in NOTIFICHE if "non risponde" in n[1]]))
    giro()
    prova("...e da li' il giro lo salta", "errore", stato)

    # ---- 11. il secondo dialetto -------------------------------------
    # Da qui in avanti il connettore Shopify e' in 'errore', quindi il
    # giro guarda solo il Woo: e' quel che serve per leggere le due
    # sezioni che seguono senza confondere i due negozi.
    print("\n[WooCommerce: l'altro dialetto]")
    wid = collega(fonte="woo", url="https://ilmionegozio.it")
    CATALOGO_WOO[:] = [
        prodotto_woo(11, "Tazza in ceramica", "14.00", stock=8),
        prodotto_woo(12, "Maglietta", "20.00", tipo="variable"),
        prodotto_woo(13, "Corso di cucina", "80.00", tipo="external"),
        prodotto_woo(14, "Set di posate", "35.00", tipo="grouped"),
        prodotto_woo(15, "Sapone all'olio", "6.00", gestito=False,
                     disponibile="outofstock"),
        prodotto_woo(16, "Vaso di scorta", "9.00", visibile="hidden"),
        prodotto_woo(17, "Tovaglia su ordinazione", "22.00",
                     gestito=False, disponibile="onbackorder"),
    ]
    giro()
    prova("entra quel che sappiamo trattare",
          {"Tazza in ceramica", "Tovaglia su ordinazione"},
          {a["titolo"] for a in annunci(wid) if a["stato"] == "attivo"})
    tazza = uno(wid, 11)
    prova("il prezzo e' il listino in EURO, coi sats al cambio del giro",
          (14.0, "eur", 14_000),
          (tazza["prezzo_eur"], tazza["valuta"], tazza["prezzo_sats"]))
    prova("l'origine dice WooCommerce", ("woo", wid, "11"),
          (tazza["fonte"], tazza["connettore_id"], tazza["origine_chiave"]))
    prova("la giacenza arriva dal negozio", 8, tazza["quantita"])
    con = SRV.db()
    esito = json.loads(con.execute(
        "SELECT ultimo_esito FROM connettori WHERE id=?", (wid,)
    ).fetchone()[0])
    con.close()
    # I TRE TIPI CHE NON SAPPIAMO TRATTARE, e `external` e' quello che
    # si dimentica: un prezzo ce l'ha e sembra un prodotto normale, ma
    # il suo bottone porta su un ALTRO sito.
    prova("i tre tipi che non sappiamo trattare si saltano, col motivo",
          {"Maglietta": "ha piu' varianti",
           "Set di posate": "e' un gruppo di prodotti",
           "Corso di cucina": "si compra su un altro sito"},
          {s["titolo"]: s["perche"] for s in esito["saltati"]
           if s["titolo"] in ("Maglietta", "Set di posate",
                              "Corso di cucina")})
    # L'INVARIANTE DI CASA VALE ANCHE ALLA NASCITA: un prodotto che
    # arriva GIA' esaurito non deve nascere 'attivo' con zero pezzi —
    # sarebbe un annuncio comprabile all'occhio che alla cassa dice di
    # no, e nessuna scopa lo raddrizza. Su Woo e' il caso quotidiano.
    sapone = uno(wid, 15)
    prova("chi arriva gia' esaurito nasce «venduto», non «attivo»",
          ("venduto", 0), (sapone["stato"], sapone["quantita"]))
    prova("il prodotto nascosto nello scaffale non entra in vetrina",
          "rimosso", uno(wid, 16)["stato"])
    # ...e il rovescio: «su ordinazione» sul suo sito si compra ancora,
    # quindi la giacenza resta IGNOTA e non diventa zero
    prova("«su ordinazione» resta comprabile", ("attivo", 1),
          (uno(wid, 17)["stato"], uno(wid, 17)["quantita"]))
    prova("...e si annota che la giacenza non la sappiamo", -1,
          uno(wid, 17)["origine_stock_visto"])
    prova("la consegna viene dal CASSETTO anche qui",
          ("spedizione", 5.0), (tazza["consegna"], tazza["spedizione_eur"]))

    # ---- 12. L'IVA -----------------------------------------------------
    # LA PROVA CHE CONTA DELLA TAPPA 3. WooCommerce non dice nel
    # prodotto se `price` include le tasse: dipende da un'impostazione
    # del negozio. Con i prezzi scritti al NETTO, importarli com'e'
    # vorrebbe dire mettere in vetrina una cifra piu' bassa di quella
    # che sul suo sito si paga — e il venditore lo scoprirebbe
    # incassando.
    print("\n[l'IVA: un prezzo che non e' il prezzo non si importa]")
    vivi = [(a["id"], a["stato"]) for a in annunci(wid)]
    quante = len(NOTIFICHE)
    IVA_WOO[0] = "no"          # «prezzi inseriti SENZA le tasse»
    giro()
    prova("col netto il catalogo non si legge: nessun prezzo cambia",
          vivi, [(a["id"], a["stato"]) for a in annunci(wid)])
    # ...ed e' QUESTA la ragione per cui `prezzi_finiti_woo` ALZA invece
    # di marchiare le righe una per una: una riga saltata non entra in
    # `viste`, quindi la riconciliazione la tratterebbe come sparita
    # dal negozio e la spegnerebbe — saltare tutto il catalogo
    # vorrebbe dire spegnere la vetrina di quel venditore in un colpo.
    prova("...e SOPRATTUTTO nessun annuncio si spegne",
          {"Tazza in ceramica", "Tovaglia su ordinazione"},
          {a["titolo"] for a in annunci(wid) if a["stato"] == "attivo"})
    con = SRV.db()
    c = con.execute("SELECT errori_di_fila, ultimo_errore FROM connettori "
                    "WHERE id=?", (wid,)).fetchone()
    con.close()
    prova("l'errore si conta, come una rete caduta", 1, c[0])
    prova("...e il motivo VERO resta scritto, per il venditore", True,
          "NETTO" in (c[1] or ""))
    prova("...senza mai le chiavi nel messaggio", False,
          "cs_segretissima" in (c[1] or ""))
    prova("nessuno viene svegliato per un giro solo", quante,
          len(NOTIFICHE))
    # e il rientro: rimessa l'impostazione, il giro riprende da solo
    IVA_WOO[0] = "yes"
    CATALOGO_WOO[0] = prodotto_woo(11, "Tazza in ceramica", "16.00",
                                   stock=5)
    giro()
    tazza = uno(wid, 11)
    prova("sistemata l'impostazione, il catalogo torna a scorrere",
          (16.0, 16_000, 5),
          (tazza["prezzo_eur"], tazza["prezzo_sats"], tazza["quantita"]))
    con = SRV.db()
    prova("...e il conto degli errori si azzera", 0,
          con.execute("SELECT errori_di_fila FROM connettori WHERE id=?",
                      (wid,)).fetchone()[0])
    con.close()
    # LE TASSE SPENTE sono l'altro caso lecito: il prezzo e' quel che e'
    TASSE_WOO[0], IVA_WOO[0] = "no", "no"
    CATALOGO_WOO[0] = prodotto_woo(11, "Tazza in ceramica", "18.00",
                                   stock=5)
    giro()
    prova("col negozio senza tasse il prezzo si legge com'e'", 18.0,
          uno(wid, 11)["prezzo_eur"])

    print("\n" + "=" * 62)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 62)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
