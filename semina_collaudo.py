# -*- coding: utf-8 -*-
"""
🌱 LA SEMINA DEL COLLAUDO (20 ott 2026, cantiere collaudo-ritocco,
richiesta di Andrea; procedura: docs/COLLAUDO.md). Il database dell'istanza
di prova (la vm-2050) riceve un mercatino FINTO abbastanza pieno da provare
davvero le liste, il carrello, la chat e «I miei ordini»: quattro venditori
di prova, quattordici annunci in dodici categorie con le loro foto finte, e
due ordini comprati dal primo id della lista del collaudo — uno in corso e
uno concluso. Tutto dice di essere finto: nomi, titoli, testi e foto.

E' LA GEMELLA DI `semina_demo.py`, che resta com'e' (il negozio della demo
di Torino, chiusa senza MODALITA_COLLAUDO). Questa la lancia `sudo collaudo
azzera` sulla VM, dopo che il server ha creato il database.

FAIL-CLOSED, TRE VOLTE (`giudizio_semina`, la regola di Andrea: «oltre a
PROVA_SOLO_IDS piena, rifiuta se URL_PUBBLICO e' barattolo.store o il
database e' quello di produzione»):
  1) ci vuole un'istanza di prova: `PROVA_SOLO_IDS` piena (o, in locale,
     MODALITA_COLLAUDO = True);
  2) `URL_PUBBLICO` dichiarato e NON barattolo.store (ne' www.): non
     dichiarato vale barattolo.store, cioe' no;
  3) il database non sta sotto /srv/barattolo/, la cartella della
     produzione (letto anche attraverso i collegamenti).
Niente `import server`, niente rete: un file sqlite che il SERVER ha gia'
creato (lo schema lo controlla `controlla_schema` della gemella) e la
cartella foto/ accanto, come fa il server.

USO (sulla VM, dalla cartella del codice, come utente collaudo):
  python semina_collaudo.py            # semina (rilanciabile: niente doppioni)
  python semina_collaudo.py stato      # cosa c'e', senza scrivere
Opzioni: --db PERCORSO (default: `DB` del config).
Per prove e collaudi: SEMINA_CARTELLA_FOTO sposta la cartella delle foto.
"""

import json
import os
import sqlite3
import sys
import time
from urllib.parse import urlparse

from semina_demo import SeminaFerma, controlla_schema, _codice_libero

QUI = os.path.dirname(os.path.abspath(__file__))
CARTELLA_PRODUZIONE = "/srv/barattolo/"
HOST_PRODUZIONE = ("barattolo.store", "www.barattolo.store")

# --- I VENDITORI DI PROVA (id piccoli: nessuno di loro entra mai) -------
VENDITORI = (
    (9001, "Anna di prova", "Pavia (PV)"),
    (9002, "Bottega di prova di Bruno", "Torino (TO)"),
    (9003, "Carla (prova)", "Bologna (BO)"),
    (9004, "Mercatino di prova di Dario", "Napoli (NA)"),
)
# --- GLI ANNUNCI: (venditore, titolo, categoria, condizione, sats, consegna)
ANNUNCI = (
    (9001, "Cuffie bluetooth di prova", "Audio e video", "come_nuovo", 18_000, "spedizione"),
    (9001, "Romanzo giallo di prova", "Libri e media", "buono", 6_000, "entrambe"),
    (9001, "Lampada da scrivania di prova", "Casa e giardino", "nuovo", 22_000, "ritiro"),
    (9002, "Tastiera meccanica di prova", "Informatica", "come_nuovo", 45_000, "spedizione"),
    (9002, "Bicicletta da città di prova", "Biciclette", "buono", 150_000, "ritiro"),
    (9002, "Set di cacciaviti di prova", "Fai da te e utensili", "nuovo", 12_000, "entrambe"),
    (9003, "Maglione di lana di prova", "Abbigliamento", "come_nuovo", 15_000, "spedizione"),
    (9003, "Barattolo di miele di prova", "Alimenti e bevande", "nuovo", 5_000, "entrambe"),
    (9003, "Gioco in scatola di prova", "Bambini", "buono", 9_000, "spedizione"),
    (9004, "Chitarra classica di prova", "Strumenti musicali", "accettabile", 60_000, "ritiro"),
    (9004, "Moneta da collezione di prova", "Collezionismo", "come_nuovo", 30_000, "spedizione"),
    (9004, "Pallone da calcio di prova", "Sport e hobby", "buono", 8_000, "entrambe"),
    # i due degli ordini (venduti, un pezzo solo)
    (9002, "Mouse senza fili di prova (venduto)", "Elettronica", "come_nuovo", 7_000, "ritiro"),
    (9003, "Tazza dipinta di prova (venduta)", "Arte e artigianato", "nuovo", 11_000, "ritiro"),
)
DESCRIZIONE = ("Annuncio DI PROVA del collaudo di Barattolo: l'oggetto non "
               "esiste e niente viene spedito. Serve a provare le liste, il "
               "carrello, la chat e gli ordini.")
# gli ordini: (titolo dell'annuncio, stato) — uno in corso, uno concluso
ORDINI = (
    ("Mouse senza fili di prova (venduto)", "locked"),
    ("Tazza dipinta di prova (venduta)", "released"),
)
FOTO_LATO, FOTO_MIN, FOTO_QUALITA = 800, 480, 82


# ======================= IL GIUDICE (lo prova prove.py) ===================

def giudizio_semina(cfg: dict, percorso_db: str) -> str:
    """PURA (a parte `realpath`): '' se su questo config e questo database
    la semina puo' scrivere, altrimenti il perche'. `cfg` e' un dizionario
    con quel che il config dichiara (le chiavi assenti NON ci sono)."""
    lista = cfg.get("PROVA_SOLO_IDS", [])
    prova = (isinstance(lista, (list, tuple, set)) and len(lista) > 0)
    if not prova and cfg.get("MODALITA_COLLAUDO") is not True:
        return ("non e' un'istanza di prova: PROVA_SOLO_IDS e' vuota (e "
                "MODALITA_COLLAUDO non e' True)")
    url = cfg.get("URL_PUBBLICO")
    if not isinstance(url, str) or not url.strip():
        return ("URL_PUBBLICO non e' dichiarato, cioe' vale barattolo.store: "
                "sulla produzione non si semina")
    host = (urlparse(url.strip()).hostname or "").lower()
    if not host or host in HOST_PRODUZIONE:
        return f"URL_PUBBLICO e' {url}: e' la produzione, non si semina"
    vero = os.path.realpath(percorso_db).replace("\\", "/")
    if (percorso_db.replace("\\", "/").startswith(CARTELLA_PRODUZIONE)
            or vero.startswith(CARTELLA_PRODUZIONE)):
        return f"il database {percorso_db} sta nella cartella della produzione"
    return ""


def ids_compratori(cfg: dict) -> list:
    """Gli id Telegram (positivi) della lista, nell'ordine scritto: il primo
    compra i due ordini seminati."""
    fuori = []
    for v in cfg.get("PROVA_SOLO_IDS", []) or []:
        try:
            n = int(v)
        except (TypeError, ValueError):
            continue
        if n > 0 and n not in fuori:
            fuori.append(n)
    return fuori


# ========================= IL DATABASE ====================================

def _foto_finta(cartella_foto: str, nome_base: str, categoria: str) -> list:
    """La foto finta di un annuncio: l'illustrazione della sua categoria
    (assets/categorie/) su un fondo chiaro, con una fascia «FOTO DI PROVA»,
    nella forma della whitelist `NOME_FOTO` (`a<id>_0.jpg` e il francobollo
    `_min`). [] se Pillow o il disegno mancano: l'annuncio nasce lo stesso."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return []
    slug = (categoria.lower().replace(" ", "-").replace("'", "-"))
    sorgente = os.path.join(QUI, "assets", "categorie", f"{slug}.webp")
    try:
        quadro = Image.new("RGB", (FOTO_LATO, FOTO_LATO), (246, 240, 228))
        if os.path.exists(sorgente):
            disegno = Image.open(sorgente).convert("RGBA")
            disegno.thumbnail((FOTO_LATO - 160, FOTO_LATO - 160))
            quadro.paste(disegno, ((FOTO_LATO - disegno.width) // 2,
                                   (FOTO_LATO - disegno.height) // 2 - 40), disegno)
        tela = ImageDraw.Draw(quadro)
        tela.rectangle((0, FOTO_LATO - 150, FOTO_LATO, FOTO_LATO - 50), fill=(247, 143, 25))
        try:
            font = ImageFont.load_default(size=56)
        except TypeError:
            font = ImageFont.load_default()
        tela.text((FOTO_LATO // 2, FOTO_LATO - 100), "FOTO DI PROVA",
                  fill=(255, 255, 255), font=font, anchor="mm")
        os.makedirs(cartella_foto, exist_ok=True)
        quadro.save(os.path.join(cartella_foto, f"{nome_base}.jpg"), "JPEG",
                    quality=FOTO_QUALITA)
        quadro.resize((FOTO_MIN, FOTO_MIN), Image.Resampling.LANCZOS).save(
            os.path.join(cartella_foto, f"{nome_base}_min.jpg"), "JPEG",
            quality=FOTO_QUALITA)
    except Exception:
        return []
    return [f"{nome_base}.jpg"]


def semina_venditori(con, adesso: int) -> int:
    nuovi = 0
    for tg_id, nome, _zona in VENDITORI:
        if con.execute("SELECT 1 FROM utenti WHERE tg_id=?", (tg_id,)).fetchone():
            continue
        con.execute("INSERT INTO utenti(tg_id, nome, username, registrato, negozio) "
                    "VALUES(?,?,?,?,?)",
                    (tg_id, nome, "", adesso, _codice_libero(con)))
        nuovi += 1
    return nuovi


def semina_annunci(con, cartella_foto: str, adesso: int) -> dict:
    """Ogni annuncio si cerca per venditore e titolo: c'e' = si lascia."""
    zone = {v[0]: v[2] for v in VENDITORI}
    ids, nuovi = {}, 0
    for i, (vend, titolo, categoria, condizione, sats, consegna) in enumerate(ANNUNCI):
        r = con.execute("SELECT id FROM annunci WHERE venditore_id=? AND titolo=?",
                        (vend, titolo)).fetchone()
        if r:
            ids[titolo] = r[0]
            continue
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
            "sottocategoria,prezzo_sats,zona,valuta,prezzo_eur,consegna,"
            "paese_domestico,condizione,quantita,quantita_max,stato,creato) "
            "VALUES(?,?,?,?,'',?,?,'sats',0,?,'IT',?,1,1,'attivo',?)",
            (vend, titolo, DESCRIZIONE, categoria, sats, zone[vend], consegna,
             condizione, adesso - 3600 * (len(ANNUNCI) - i)))
        aid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        foto = _foto_finta(cartella_foto, f"a{aid}_0", categoria)
        if foto:
            con.execute("UPDATE annunci SET foto=? WHERE id=?", (json.dumps(foto), aid))
        ids[titolo] = aid
        nuovi += 1
    return {"ids": ids, "nuovi": nuovi}


def semina_ordini(con, ids: dict, compratore: int, adesso: int) -> int:
    """Gli ordini del primo id della lista: si cercano per compratore e
    annuncio. L'annuncio di un ordine e' venduto (un pezzo solo).
    payment_hash e invoice VUOTI: nessuna fattura vera, e il mietitore non
    guarda gli ordini senza payment_hash."""
    nuovi = 0
    for titolo, stato in ORDINI:
        aid = ids[titolo]
        if con.execute("SELECT 1 FROM ordini WHERE annuncio_id=? AND compratore_id=?",
                       (aid, compratore)).fetchone():
            continue
        vend, prezzo = con.execute("SELECT venditore_id, prezzo_sats FROM annunci "
                                   "WHERE id=?", (aid,)).fetchone()
        quando = adesso - (86400 * 3 if stato == "released" else 86400)
        con.execute(
            "INSERT INTO ordini(cassaforte,annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,stato,payment_hash,invoice,creato,aggiornato,cambio_ordine,"
            "consegna_scelta,quantita,spedizione_sats,protezione_sats) "
            "VALUES('saas',?,?,?,?,?,'','',?,?,0,'ritiro',1,0,0)",
            (aid, compratore, vend, prezzo, stato, quando, quando + 3600))
        con.execute("UPDATE annunci SET quantita=0, stato='venduto' WHERE id=?", (aid,))
        nuovi += 1
    return nuovi


def stato(con) -> dict:
    vend = [v[0] for v in VENDITORI]
    segni = ",".join("?" * len(vend))
    return {
        "venditori": con.execute(f"SELECT COUNT(*) FROM utenti WHERE tg_id IN ({segni})",
                                 vend).fetchone()[0],
        "annunci": con.execute(f"SELECT stato, COUNT(*) FROM annunci WHERE venditore_id "
                               f"IN ({segni}) GROUP BY stato", vend).fetchall(),
        "ordini": con.execute(f"SELECT id, stato, compratore_id FROM ordini WHERE "
                              f"venditore_id IN ({segni}) ORDER BY id", vend).fetchall(),
    }


# ============================ IL COMANDO ==================================

def _config_dichiarato() -> dict:
    """Quel che config.py DICHIARA, e nient'altro (una chiave assente non
    prende il valore di serie del server: per URL_PUBBLICO quel valore e'
    la produzione)."""
    try:
        import config
    except ImportError:
        raise SeminaFerma("manca config.py: la semina del collaudo legge "
                          "PROVA_SOLO_IDS, URL_PUBBLICO e DB da li'")
    return {k: getattr(config, k) for k in ("PROVA_SOLO_IDS", "MODALITA_COLLAUDO",
                                            "URL_PUBBLICO", "DB")
            if hasattr(config, k)}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    db_a_mano = ""
    while "--db" in argv:
        i = argv.index("--db")
        try:
            db_a_mano = argv[i + 1]
        except IndexError:
            print("--db vuole un percorso")
            return 2
        del argv[i:i + 2]
    comando = argv[0] if argv else "semina"
    if comando not in ("semina", "stato") or len(argv) > 1:
        print(__doc__.split("USO")[1])
        return 2
    try:
        cfg = _config_dichiarato()
        percorso = db_a_mano or cfg.get("DB", "satmarket.db")
        if not os.path.isabs(percorso):
            percorso = os.path.join(QUI, percorso)
        no = giudizio_semina(cfg, percorso)
        if no:
            raise SeminaFerma(no)
        if not os.path.exists(percorso):
            raise SeminaFerma(f"il database {percorso} non esiste: avvia "
                              "Barattolo una volta (lo crea lui) e rilancia")
        con = sqlite3.connect(percorso, timeout=15)
        try:
            controlla_schema(con)
            if comando == "stato":
                s = stato(con)
                print(f"🔎 {percorso}: {s['venditori']} venditori di prova, annunci "
                      f"{dict(s['annunci'])}, ordini {[(o[0], o[1]) for o in s['ordini']]}")
                return 0
            compratori = ids_compratori(cfg)
            adesso = int(time.time())
            # la cartella delle foto e' quella del server (FOTO_DIR, accanto
            # al codice); prove e collaudi la spostano con SEMINA_CARTELLA_FOTO
            cartella_foto = (os.environ.get("SEMINA_CARTELLA_FOTO")
                             or os.path.join(QUI, "foto"))
            v = semina_venditori(con, adesso)
            a = semina_annunci(con, cartella_foto, adesso)
            o = semina_ordini(con, a["ids"], compratori[0], adesso) if compratori else 0
            con.commit()
            print(f"🌱 Semina del collaudo su {percorso}: {v} venditori nuovi "
                  f"(su {len(VENDITORI)}), {a['nuovi']} annunci nuovi (su "
                  f"{len(ANNUNCI)}), {o} ordini nuovi"
                  + (f" per l'id {compratori[0]}" if compratori else
                     " (nessun id Telegram in lista: niente ordini)")
                  + f"; le foto in {cartella_foto}. Rilanciabile: niente doppioni.")
            return 0
        finally:
            con.close()
    except SeminaFerma as e:
        print(f"⛔ Semina ferma: {e}")
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
