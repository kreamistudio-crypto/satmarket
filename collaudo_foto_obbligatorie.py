# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE FOTO OBBLIGATORIE (11 ott 2026, cantiere
foto-obbligatorie, decisione di Andrea).

La regola: sul mercatino, per pubblicare un annuncio serve almeno una
foto. Vale per tutti i tipi — oggetti, contenuti digitali, servizi — e
chi c'e' gia' resta: nessun annuncio si spegne, ma chi ritocca un
annuncio nato senza foto per salvare deve dargliene una.

`prove.py` guarda il testo dei pezzi; qui si chiamano le ROTTE VERE e i
due importatori veri, su un database usa-e-getta, per le domande che
solo il giro intero puo' chiudere:

  · pubblica(): senza foto e' un 400 che si capisce, per OGNI strada di
    consegna, detto prima dell'AI e prima dell'INSERT (nessuna riga);
    con una foto si pubblica come sempre;
  · il duplicato: eredita le foto dell'originale, e se l'originale non
    ne ha e' lo stesso no;
  · modifica_annuncio(): l'annuncio nato senza foto resta online, non
    si salva senza una foto, si salva con; chi le ha gia' non se ne
    accorge; e i no di proprieta' e di stato vengono PRIMA di questo;
  · l'import da file: la riga senza foto e' uno scarto col motivo, il
    modello cosi' com'e' non si fa scartare per le foto, e la riga le
    cui foto non entrano non lascia un annuncio in vetrina;
  · il negozio collegato: un prodotto mai visto senza immagini non
    nasce, non va all'AI, si conta e si dice al venditore; entra al
    giro in cui ne ha una; chi e' gia' dentro resta;
  · Nostr: un evento mai visto senza foto non nasce e non va all'AI;
    entra quando ne porta una; chi e' gia' dentro resta.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, FOTO_DIR punta a una cartella usa-e-getta, i
negozi e i relay sono di cartone e nessuna foto si scarica davvero.

USO:  python collaudo_foto_obbligatorie.py
"""

import asyncio
import base64
import io
import json
import os
import re
import sys
import tempfile
import time
import types
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = IMP = None
FOTO = None

VENDITORE = {"id": 222, "nome": "Vende", "first_name": "Vende",
             "username": "vende", "admin": False}
ALTRO = {"id": 333, "nome": "Altro", "first_name": "Altro",
         "username": "altro", "admin": False}
CHI = [VENDITORE]
CHIAMATE_AI = []              # ogni titolo che arriva alla moderazione
NOTIFICHE = []                # (tg_id, testo)
NEGOZIO = {"catalogo": []}    # il WooCommerce di cartone
EVENTI = []                   # quel che risponde il relay di cartone
CHIAVE = "bb" * 32            # la chiave Nostr del venditore, in hex
NPUB = ""


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def jpeg_vero(seme=0):
    """Una foto che non e' una tinta unita (il server scarta le vuote)."""
    from PIL import Image
    img = Image.new("RGB", (240, 180))
    px = img.load()
    for y in range(180):
        for x in range(240):
            px[x, y] = ((x * 7 + seme) % 256, (y * 5) % 256,
                        (x + y + seme) % 256)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=90)
    return out.getvalue()


def uri(raw):
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def api_finta(metodo, url, intestazioni):
    """Il WooCommerce di cartone: un catalogo di prodotti semplici."""
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes",
                                "value": "yes"}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax",
                                "value": "yes"}]}, {}
    if re.search(r"/products/\d+/variations", url):
        return 200, {"lista": []}, {}
    per_pagina = int(re.search(r"per_page=(\d+)", url).group(1))
    pagina = int(re.search(r"[?&]page=(\d+)", url).group(1))
    fetta = NEGOZIO["catalogo"][(pagina - 1) * per_pagina:
                                pagina * per_pagina]
    return 200, {"lista": fetta}, {"X-WP-Total": str(len(NEGOZIO["catalogo"]))}


def prodotto_woo(pid, nome, foto=True):
    return {"id": pid, "name": nome, "description": f"<p>Vasetto {pid}</p>",
            "type": "simple", "status": "publish",
            "catalog_visibility": "visible", "price": "7.50",
            "regular_price": "7.50", "manage_stock": True,
            "stock_quantity": 12, "stock_status": "instock",
            "images": ([{"src": f"https://negozio.test/{pid}.jpg"}]
                       if foto else []),
            "categories": [{"id": 1, "name": "Casa"}]}


def evento(d, titolo, foto=True, eid=None):
    """Un NIP-99 del venditore, con o senza il tag `image`."""
    tags = [["d", d], ["title", titolo], ["price", "50000", "SAT"],
            ["location", "Pavia (PV)"]]
    if foto:
        tags.append(["image", f"https://foto.test/{d}.jpg"])
    return {"id": eid or (f"{abs(hash(d)) % 10**8:08d}" * 8),
            "pubkey": CHIAVE, "kind": 30402,
            "created_at": int(time.time()), "content": "Descrizione.",
            "tags": tags}


def avvio():
    global SRV, IMP, FOTO, NPUB
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-foto-obbligatorie-")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = os.path.join(tmp, "usa-e-getta.db")
    cfg.CONNETTORI_NEGOZIO_APERTI = True
    cfg.SERVIZI_ATTIVI = True          # la strada «servizio» vive dietro la leva
    # la leva anti-frode dei digitali spenta: qui si prova la FOTO, e
    # quel no arriverebbe prima a un venditore senza vendite
    cfg.DIGITALE_MIN_VENDITE = 0
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    import importa_nostr
    SRV, IMP = server, importa_nostr
    server.init_db()
    server.DIGITALE_MIN_VENDITE = 0
    # LE FOTO IN UNA CARTELLA USA-E-GETTA: senza questa riga il
    # collaudo scriverebbe dentro foto/, cioe' fra le foto vere.
    FOTO = os.path.join(tmp, "foto")
    os.makedirs(FOTO, exist_ok=True)
    server.FOTO_DIR = FOTO
    NPUB = server.hex_to_npub(CHIAVE)
    IMP.RELAYS = ["wss://finto"]
    IMP.DB = cfg.DB
    IMP.interroga = lambda relay, hexkey: list(EVENTI)

    async def zitto(*a, **k):
        return None

    async def ai_finta(titolo, descrizione=""):
        CHIAMATE_AI.append(titolo)
        return None

    async def lotto_finto(voci):
        CHIAMATE_AI.extend(t for _, t, _ in voci)
        return {}

    async def notifica_finta(tg_id, testo, *a, **k):
        NOTIFICHE.append((tg_id, testo))

    async def cambio_finto():
        return 100_000.0

    # il cambio di cartone: le righe in euro del modello CSV lo
    # chiederebbero a CoinGecko (lo ha detto la gabbia di collaudi_ci)
    server.cambio_btc_eur = cambio_finto
    server.verifica_utente = lambda *a, **k: CHI[0]
    server.moderazione_ai = ai_finta
    server.moderazione_ai_lotto = lotto_finto
    server.notifica = notifica_finta
    for nome in ("notifica_admin", "annuncio_su_nostr", "premia_distintivi",
                 "avvisa_contatto_mancante", "polso_ordini_admin",
                 "promo_venduto"):
        setattr(server, nome, zitto)
    server.accoda_promo = lambda *a, **k: None
    server.accoda_match = lambda *a, **k: None
    # i negozi e le foto di fuori: di cartone, mai rete
    server.chiama_api_negozio = api_finta
    server._salva_foto_connettore = lambda annuncio_id, indice, url: None
    server.cambio_per_import = lambda: {"EUR": 60_000.0, "USD": 65_000.0}
    server.url_foto_ammesso = lambda u: u.startswith(
        ("https://foto.test/", "https://esempio.it/"))
    buona = jpeg_vero(21)
    server.scarica_foto_import = lambda u: (None if "morta" in u else buona)
    con = server.db()
    for u in (VENDITORE, ALTRO):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)",
                    (u["id"], u["nome"], f"neg{u['id']}"))
    con.commit()
    con.close()
    return tmp


def chiama(rotta, corpo, *argomenti):
    """La rotta VERA: torna (200, risposta) o (codice, detail)."""
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi

    async def giro():
        try:
            r = await rotta(*argomenti)
            await asyncio.sleep(0.05)      # i create_task in coda
            return 200, r
        except SRV.HTTPException as e:
            return e.status_code, e.detail
    return asyncio.run(giro())


def pubblica(corpo):
    return chiama(SRV.pubblica, corpo, None)


def modifica(aid, corpo):
    return chiama(SRV.modifica_annuncio, corpo, aid, None)


def riga(aid):
    con = SRV.db()
    r = con.execute("SELECT * FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return dict(r) if r else None


def righe_con(titolo):
    con = SRV.db()
    r = [dict(x) for x in con.execute(
        "SELECT * FROM annunci WHERE titolo=? ORDER BY id", (titolo,))]
    con.close()
    return r


def semina(titolo, stato="attivo", venditore=222, foto=""):
    """Un annuncio scritto dritto nel database: lo STORICO, nato quando
    la regola non c'era (o un importato)."""
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats,foto) VALUES(?,?,'Di ieri',30000,'Altro',"
        "'Torino (TO)',?,1,'spedizione',1,'sats','buono',2000,?)",
        (venditore, titolo, stato, foto))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


BASE = {"titolo": "Tastiera meccanica", "prezzo_sats": 30000,
        "categoria": "Altro", "zona": "Torino (TO)",
        "descrizione": "Come nuova", "consegna": "spedizione",
        "spedizione_sats": 2000, "quantita": 1, "condizione": "buono"}
STRADE = {
    "spedizione": {},
    "ritiro": {"consegna": "ritiro"},
    "entrambe": {"consegna": "entrambe"},
    "digitale": {"consegna": "digitale", "categoria": "Buoni ed esperienze",
                 "zona": "", "condizione": ""},
    "servizio": {"consegna": "servizio", "categoria": "Lezioni e corsi",
                 "zona": "", "condizione": "", "durata_min": 60},
}


def collaudo_giudice():
    print("\n[il giudice: «qui c'e' almeno una foto?»]")
    casi = [("", False), (None, False), ("[]", False), ('[""]', False),
            ("storto", False), ('{"a": 1}', False), (0, False),
            ('["a1_0.jpg"]', True), ('["https://x.test/a.jpg"]', True),
            ([], False), ([""], False), (["a1_0.jpg"], True)]
    prova("stringa vuota, JSON vuoto o storto = no; un nome o un URL = si'",
          [c[1] for c in casi], [SRV.ha_foto(c[0]) for c in casi])
    prova("le tre frasi dicono «foto» e non parlano tecnico", True,
          all("foto" in t and "400" not in t and "JSON" not in t
              for t in (SRV.MSG_SERVE_UNA_FOTO,
                        SRV.MSG_SERVE_UNA_FOTO_MODIFICA,
                        SRV.MOTIVO_RIGA_SENZA_FOTO)))
    prova("...e chi pubblica legge «almeno una foto», come nel form", True,
          "almeno una foto" in SRV.MSG_SERVE_UNA_FOTO)


def collaudo_pubblica():
    print("\n[pubblicare senza foto: un no che si capisce, per ogni strada]")
    for nome, extra in STRADE.items():
        CHIAMATE_AI.clear()
        titolo = f"Senza foto ({nome})"
        esiti = [pubblica({**BASE, **extra, "titolo": titolo, **foto})
                 for foto in ({}, {"foto": []}, {"foto": None},
                              {"foto": "non-una-lista"})]
        prova(f"{nome}: senza chiave, lista vuota, None, stringa — 400 "
              f"con la frase", [(400, SRV.MSG_SERVE_UNA_FOTO)] * 4, esiti)
        prova(f"{nome}: ...prima dell'AI e senza lasciare una riga",
              (0, 0), (len(CHIAMATE_AI), len(righe_con(titolo))))

    print("\n[pubblicare con una foto: come sempre, per ogni strada]")
    for i, (nome, extra) in enumerate(STRADE.items()):
        codice, r = pubblica({**BASE, **extra,
                              "titolo": f"Con la foto ({nome})",
                              "foto": [uri(jpeg_vero(i))]})
        nata = riga(r["id"]) if codice == 200 else {}
        prova(f"{nome}: si pubblica, in vetrina, con la sua foto",
              (200, "attivo", True),
              (codice, nata.get("stato"), SRV.ha_foto(nata.get("foto"))))

    print("\n[il duplicato]")
    codice, r = pubblica({**BASE, "titolo": "Originale con foto",
                          "foto": [uri(jpeg_vero(40))]})
    orig = r["id"]
    codice, r = pubblica({**BASE, "titolo": "Duplicato che eredita",
                          "foto": [], "copia_foto_da": orig})
    prova("da un annuncio CON foto: nasce e le eredita", (200, 1),
          (codice, r.get("foto_salvate") if codice == 200 else r))
    storico = semina("Storico da duplicare")
    codice, detto = pubblica({**BASE, "titolo": "Duplicato di uno senza",
                              "foto": [], "copia_foto_da": storico})
    prova("da un annuncio SENZA foto: lo stesso no",
          (400, SRV.MSG_SERVE_UNA_FOTO, 0),
          (codice, detto, len(righe_con("Duplicato di uno senza"))))
    codice, r = pubblica({**BASE, "titolo": "Duplicato di uno senza",
                          "foto": [uri(jpeg_vero(41))],
                          "copia_foto_da": storico})
    prova("...e scegliendone una si pubblica", 200, codice)


def collaudo_modifica():
    print("\n[gli annunci gia' online senza foto restano online]")
    storico = semina("Storico senza foto")
    SRV.init_db()                     # un riavvio: nessuna scopa li tocca
    prova("dopo un riavvio lo storico e' ancora attivo, e ancora senza",
          ("attivo", ""), (riga(storico)["stato"], riga(storico)["foto"]))

    print("\n[...ma per salvare una modifica serve una foto]")
    nuovo = {**BASE, "titolo": "Storico ritoccato"}
    CHIAMATE_AI.clear()
    esiti = [modifica(storico, {**nuovo, **foto})
             for foto in ({}, {"foto": []}, {"foto": None})]
    prova("senza foto la modifica non si salva: 400 con la sua frase",
          [(400, SRV.MSG_SERVE_UNA_FOTO_MODIFICA)] * 3, esiti)
    prova("...prima dell'AI, e l'annuncio e' com'era, ancora online",
          (0, "Storico senza foto", "attivo"),
          (len(CHIAMATE_AI), riga(storico)["titolo"],
           riga(storico)["stato"]))
    codice, r = modifica(storico, {**nuovo, "foto": [uri(jpeg_vero(50))]})
    prova("con una foto si salva, e la foto c'e'",
          (200, "Storico ritoccato", True),
          (codice, riga(storico)["titolo"],
           SRV.ha_foto(riga(storico)["foto"])))
    codice, r = modifica(storico, {**nuovo, "titolo": "Ritocco dopo"})
    prova("da li' in poi e' un annuncio come gli altri: si ritocca senza "
          "mandare foto", (200, "Ritocco dopo"),
          (codice, riga(storico)["titolo"]))

    print("\n[i no di proprieta' e di stato vengono prima]")
    in_rev = semina("Storico in revisione", stato="revisione")
    codice, detto = modifica(in_rev, {**nuovo})
    prova("in revisione: si sente dire quello, non «manca la foto»",
          (400, True, False),
          (codice, "revisione" in str(detto), "foto" in str(detto)))
    altrui = semina("Storico di un altro", venditore=333)
    codice, detto = modifica(altrui, {**nuovo})
    prova("di un altro: «Operazione non permessa»",
          (400, "Operazione non permessa"), (codice, detto))


CSV_TESTA = ("titolo;descrizione;prezzo;valuta;categoria;zona;foto;"
             "consegna;spedizione;taglia;condizione;quantita\n")


def prepara(testo, zip_token=""):
    return chiama(SRV.import_prepara, {"csv": testo, "zip": zip_token}, None)


def collaudo_import_file():
    print("\n[l'import da file: la riga senza foto e' uno scarto]")
    testo = (CSV_TESTA
             + "Con indirizzo;Buona;1000;sats;Altro;;"
               "https://foto.test/buona.jpg;spedizione;100;piccolo;buono;1\n"
             + "Senza foto;Buona;1000;sats;Altro;;;spedizione;100;piccolo;"
               "buono;1\n"
             + "Nome senza ZIP;Buona;1000;sats;Altro;;trapano.jpg;spedizione;"
               "100;piccolo;buono;1\n"
             + "Indirizzo morto;Buona;1000;sats;Altro;;"
               "https://foto.test/morta.jpg;spedizione;100;piccolo;buono;1\n")
    codice, r = prepara(testo)
    prova("due righe valide su quattro", (200, 2, 4),
          (codice, r.get("valide"), r.get("totale")))
    prova("le due senza una foto raggiungibile sono scarti, col motivo",
          [(3, SRV.MOTIVO_RIGA_SENZA_FOTO), (4, SRV.MOTIVO_RIGA_SENZA_FOTO)],
          [(s["riga"], s["motivo"]) for s in r.get("scarti", [])])
    prova("...e il nome senza ZIP ha anche il suo avviso, che dice perche'",
          True, any(a["riga"] == 4 and "nessuno ZIP" in a["motivo"]
                    for a in r.get("avvisi", [])))

    print("\n[...e quella le cui foto non entrano non resta in vetrina]")
    lavoro = SRV.IMPORT_LAVORI[r["biglietto"]]
    for una in lavoro["righe"]:
        asyncio.run(SRV._crea_riga_con_guardia(lavoro, una))
    buona, morta = righe_con("Con indirizzo"), righe_con("Indirizzo morto")
    prova("la riga con la foto buona e' in vetrina con la sua foto",
          [("attivo", True)],
          [(x["stato"], SRV.ha_foto(x["foto"])) for x in buona])
    prova("la riga con l'indirizzo morto e' ritirata, senza foto",
          [("rimosso", "")], [(x["stato"], x["foto"]) for x in morta])
    prova("...fra i non riusciti, col motivo; fra i riusciti c'e' solo "
          "l'altra", (True, [buona[0]["id"]] if buona else None),
          (any(f["titolo"] == "Indirizzo morto"
               and "nessuna foto" in f["motivo"]
               for f in lavoro["falliti"]), lavoro["ok"]))

    print("\n[il modello che si scarica non insegna a farsi scartare]")
    righe_modello = [x for x in SRV.MODELLO_IMPORT.strip().splitlines()[1:]]
    prova("ogni riga del modello ha la cella foto piena", [],
          [x.split(";")[0] for x in righe_modello if not x.split(";")[6]])
    token = "zip-di-collaudo"
    SRV.IMPORT_ZIP[token] = (VENDITORE["id"], time.time() + 600)
    nomi = sorted({n for x in righe_modello for n in x.split(";")[6].split("|")
                   if not n.startswith("http")})
    os.makedirs(os.path.dirname(SRV._percorso_zip(token)), exist_ok=True)
    with zipfile.ZipFile(SRV._percorso_zip(token), "w") as z:
        for n in nomi:
            z.writestr("foto/" + n, jpeg_vero(len(n)))
    SRV.IMPORT_LAVORI.clear()
    codice, r = prepara(SRV.MODELLO_IMPORT, token)
    prova("il modello con lo ZIP delle sue foto: nessuno scarto per le "
          "foto", (200, []),
          (codice, [s for s in r.get("scarti", []) if "foto" in s["motivo"]]))
    SRV.IMPORT_LAVORI.clear()
    codice, r = prepara(SRV.MODELLO_IMPORT)
    prova("...senza ZIP entra solo la riga con gli indirizzi web, le altre "
          "dicono «manca la foto»", (len(righe_modello) - 1, True),
          (len([s for s in r.get("scarti", [])
                if s["motivo"] == SRV.MOTIVO_RIGA_SENZA_FOTO]),
           all(s["motivo"] == SRV.MOTIVO_RIGA_SENZA_FOTO
               or "foto" not in s["motivo"] for s in r.get("scarti", []))))
    try:
        os.remove(SRV._percorso_zip(token))
    except OSError:
        pass


def giro_negozio():
    SRV._prossimo_giro_connettori = 0.0
    asyncio.run(SRV.sincronizza_connettori())
    con = SRV.db()
    c = dict(con.execute("SELECT * FROM connettori ORDER BY id DESC "
                         "LIMIT 1").fetchone())
    righe = {r["titolo"]: dict(r) for r in con.execute(
        "SELECT * FROM annunci WHERE connettore_id=?", (c["id"],))}
    con.close()
    return json.loads(c["ultimo_esito"] or "{}"), righe


def collaudo_negozio():
    print("\n[il negozio collegato: senza immagini un prodotto non nasce]")
    con = SRV.db()
    con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,zona,stato,creato) VALUES(?,?,?,?,?,?,?,?,?)",
        (VENDITORE["id"], "woo", "https://negozio.test",
         SRV._cifra_contenuto(json.dumps(
             {"consumer_key": "ck_finta", "consumer_secret": "cs_finta"})),
         "spedizione", 5.0, "Carmagnola (TO)", "attivo", int(time.time())))
    con.commit()
    con.close()
    NEGOZIO["catalogo"] = [prodotto_woo(1, "Miele con la foto"),
                           prodotto_woo(2, "Miele senza foto", foto=False),
                           prodotto_woo(3, "Marmellata senza foto",
                                        foto=False)]
    CHIAMATE_AI.clear()
    NOTIFICHE.clear()
    esito, righe = giro_negozio()
    prova("nasce solo quello con la foto; gli altri due nessuna riga",
          ["Miele con la foto"], sorted(righe))
    prova("...si contano, e non sono ne' nuovi ne' saltati ne' rimandati",
          (1, 2, 0, 0),
          (esito.get("nuovi"), esito.get("senza_foto"),
           len(esito.get("saltati") or []), esito.get("rimandati")))
    prova("...l'AI ha guardato solo quello che entra",
          ["Miele con la foto"], CHIAMATE_AI)
    testo = " ".join(t for _, t in NOTIFICHE)
    prova("...e il venditore lo legge nel rapporto, col rimedio", True,
          "2 senza foto (entrano appena sul negozio ne hanno una)" in testo)

    print("\n[...entra al giro in cui il negozio gli da' una foto]")
    NEGOZIO["catalogo"][1] = prodotto_woo(2, "Miele senza foto")
    CHIAMATE_AI.clear()
    NOTIFICHE.clear()
    esito, righe = giro_negozio()
    prova("il prodotto che ha preso la foto nasce, attivo",
          ("attivo", 1, 1),
          ((righe.get("Miele senza foto") or {}).get("stato"),
           esito.get("nuovi"), esito.get("senza_foto")))
    prova("...giudicato adesso, e solo lui", ["Miele senza foto"],
          CHIAMATE_AI)
    prova("...e il rapporto dice «1 senza foto (entra appena…)»", True,
          "1 senza foto (entra appena sul negozio ne ha una)"
          in " ".join(t for _, t in NOTIFICHE))

    print("\n[...e chi e' gia' dentro resta, anche se la perde]")
    NEGOZIO["catalogo"][0] = prodotto_woo(1, "Miele con la foto", foto=False)
    esito, righe = giro_negozio()
    prova("il prodotto gia' in vetrina che sul negozio perde la foto "
          "resta attivo", "attivo",
          (righe.get("Miele con la foto") or {}).get("stato"))
    prova("...e non finisce nel conto dei senza foto (quello e' di chi "
          "non e' mai entrato)", 1, esito.get("senza_foto"))


def collaudo_nostr():
    print("\n[Nostr: un evento mai visto senza foto non nasce]")

    def importa():
        return IMP.importa_venditore(
            NPUB, VENDITORE["id"], db=SRV.DB,
            cambio={"EUR": 60_000.0, "USD": 65_000.0},
            scarica=lambda url: None)

    def nostr_righe():
        con = SRV.db()
        r = {x["titolo"]: dict(x) for x in con.execute(
            "SELECT * FROM annunci WHERE contatto_nostr=?", (NPUB,))}
        con.close()
        return r

    EVENTI[:] = [evento("con-foto", "Licenza con la foto", eid="1a" * 32),
                 evento("senza-foto", "Licenza senza foto", foto=False,
                        eid="2b" * 32)]
    nuovi, noti = SRV._da_giudicare(list(EVENTI), NPUB, VENDITORE["id"])
    prova("all'AI va solo quello che puo' entrare",
          (["Licenza con la foto"], ["Licenza senza foto"]),
          ([IMP.testo_evento(e)[0] for e in nuovi],
           [IMP.testo_evento(e)[0] for e in noti]))
    importati, aggiornati, saltati = importa()
    prova("entra solo quello con la foto; l'altro e' saltato, senza riga",
          (1, 0, 1, ["Licenza con la foto"]),
          (importati, aggiornati, saltati, sorted(nostr_righe())))

    print("\n[...entra quando l'evento porta una foto]")
    EVENTI[1] = evento("senza-foto", "Licenza senza foto", eid="3c" * 32)
    nuovi, _ = SRV._da_giudicare(list(EVENTI), NPUB, VENDITORE["id"])
    prova("adesso e' un mai visto come gli altri: si giudica",
          ["Licenza senza foto"], [IMP.testo_evento(e)[0] for e in nuovi])
    importati, aggiornati, saltati = importa()
    prova("...e nasce", (1, 1, 0, "attivo"),
          (importati, aggiornati, saltati,
           (nostr_righe().get("Licenza senza foto") or {}).get("stato")))

    print("\n[...e chi e' gia' dentro resta, anche se la perde]")
    EVENTI[0] = evento("con-foto", "Licenza con la foto", foto=False,
                       eid="4d" * 32)
    importati, aggiornati, saltati = importa()
    prova("l'evento gia' importato che perde la foto si aggiorna e resta "
          "attivo", (0, 2, 0, "attivo"),
          (importati, aggiornati, saltati,
           (nostr_righe().get("Licenza con la foto") or {}).get("stato")))

    print("\n[il NIP-15, che le foto le porta nel content]")
    prova("`images` nel JSON del prodotto: lette; senza, o storto: nessuna",
          (["https://foto.test/a.jpg"], [], [], []),
          (IMP.foto_evento({"kind": 30018, "content": json.dumps(
              {"name": "x", "images": ["https://foto.test/a.jpg", 7]})}),
           IMP.foto_evento({"kind": 30018,
                            "content": json.dumps({"name": "x"})}),
           IMP.foto_evento({"kind": 30018, "content": "{storto"}),
           IMP.foto_evento({"kind": 30018, "content": "[1, 2]"})))


def main():
    tmp = avvio()
    collaudo_giudice()
    collaudo_pubblica()
    collaudo_modifica()
    collaudo_import_file()
    collaudo_negozio()
    collaudo_nostr()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database e foto usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
