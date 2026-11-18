# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL DUPLICATO (ago 2026).

`prove.py` difende la FORMA — che la guardia di proprieta' stia nella
WHERE, che si copi solo senza foto nuove, che la copia non ricomprima —
e fa girare `copia_foto` su una cartella di cartone. Quello che non
puo' fare e' chiamare la ROTTA: `pubblica` con `copia_foto_da` dentro.

Le domande a cui risponde questo script sono quelle su cui il cantiere
si regge:

  · il duplicato NASCE (un annuncio NUOVO, non una modifica) e
    l'originale non si muove di un byte — e' la cosa che si puo'
    capire male, ed e' anche la sola che farebbe un danno vero;
  · le FOTO si ereditano davvero passando dalla rotta, e i byte del
    pieno sono IDENTICI: nessuna seconda compressione;
  · le foto NUOVE vincono sull'eredita' — sceglierne una sostituisce
    il set per intero, come in modifica;
  · la GUARDIA DI PROPRIETA' morde: le foto di un altro non si
    copiano, e l'annuncio nasce lo stesso (senza foto), che rifiutare
    una pubblicazione per un id storto sarebbe la cura peggiore del
    male;
  · il MONDO DI IERI e' intatto: una pubblicazione senza
    `copia_foto_da` fa esattamente quel che ha sempre fatto.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (o si aprirebbe il database di casa) e FOTO_DIR
punta a una cartella usa-e-getta — senza quella riga il collaudo
scriverebbe nelle foto vere.

USO:  python collaudo_duplicato.py
"""

import asyncio
import base64
import io
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
FOTO = None            # la cartella usa-e-getta delle foto

VENDITORE = {"id": 222, "nome": "Vende", "first_name": "Vende",
             "username": "vende", "admin": False}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    global SRV, FOTO
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-duplicato-")
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
    sys.modules["config"] = cfg
    # QUI NON SI CHIAMA NESSUN MODELLO (la chiave e' il segnaposto e la
    # moderazione e' fail-open), quindi il client Anthropic si sostituisce
    # con un guscio: su una macchina con `anthropic` vecchio e `httpx`
    # nuovo il suo costruttore alza all'import di server — un guasto
    # d'AMBIENTE che non ha niente a che vedere col collaudo, e che
    # senza questa riga lo fermerebbe prima di cominciare.
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    # LE FOTO IN UNA CARTELLA USA-E-GETTA: senza questa riga il
    # collaudo scriverebbe dentro foto/, cioe' fra le foto vere.
    FOTO = os.path.join(tmp, "foto")
    os.makedirs(FOTO, exist_ok=True)
    server.FOTO_DIR = FOTO

    async def zitto(*a, **k):
        return None

    server.verifica_utente = lambda *a, **k: VENDITORE
    server.notifica_admin = zitto
    server.notifica = zitto
    server.annuncio_su_nostr = zitto
    server.premia_distintivi = zitto
    server.avvisa_contatto_mancante = zitto
    server.accoda_promo = lambda *a, **k: None
    server.accoda_match = lambda *a, **k: None
    return tmp


def pubblica(corpo):
    """La rotta VERA, col suo giro di ganci."""
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi

    async def giro():
        r = await SRV.pubblica(None)
        await asyncio.sleep(0.05)      # i create_task in coda
        return r
    return asyncio.run(giro())


def riga(aid):
    con = SRV.db()
    r = con.execute("SELECT * FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return dict(r) if r else None


def foto_di(aid):
    import json
    r = riga(aid)
    return json.loads(r["foto"]) if r and r["foto"] else []


def uri(raw):
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def jpeg_vero(seme=0):
    """Una foto che non e' una tinta unita: quella la rifiuta
    _foto_vuota, che e' il suo mestiere."""
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


BASE = {"titolo": "Miele di acacia 500g", "prezzo_sats": 30000,
        "categoria": "Alimenti e bevande", "zona": "Torino (TO)",
        "descrizione": "Del nostro apiario", "consegna": "spedizione",
        "spedizione_sats": 2000, "quantita": 6,
        # (18 nov 2026) negli alimenti la tabella nutrizionale e'
        # obbligatoria: il motivo d'esenzione la sostituisce
        "etichetta": {"esente": "artigiano"}}


def main():
    tmp = avvio()
    print("\n[l'annuncio di partenza]")
    pieno = jpeg_vero()
    r = pubblica({**BASE, "foto": [uri(pieno), uri(jpeg_vero(9))]})
    orig = r["id"]
    prova("nasce con le sue due foto", 2, r["foto_salvate"])
    prima = riga(orig)

    print("\n[il duplicato eredita le foto]")
    r2 = pubblica({**BASE, "titolo": "Miele di castagno 500g",
                   "prezzo_sats": 35000, "foto": [],
                   "copia_foto_da": orig})
    dup = r2["id"]
    prova("e' un annuncio NUOVO", True, dup != orig)
    prova("con le due foto ereditate", 2, r2["foto_salvate"])
    prova("...e nessuno scarto", [], r2["foto_scarti"])
    prova("i nomi sono i suoi", [f"a{dup}_0.jpg", f"a{dup}_1.jpg"],
          foto_di(dup))
    # LA PROVA REGINA: i byte del pieno non sono stati toccati. Una
    # seconda compressione non alza e non fallisce — sgrana la foto.
    with open(os.path.join(FOTO, f"a{dup}_0.jpg"), "rb") as f:
        prova("i byte del pieno sono IDENTICI", pieno, f.read())
    prova("e la gemella _min c'e'", True,
          os.path.exists(os.path.join(FOTO, f"a{dup}_0_min.jpg")))
    # L'ORIGINALE NON SI MUOVE: e' la cosa che si puo' capire male
    prova("l'annuncio di partenza e' intatto", prima, riga(orig))

    print("\n[le foto nuove vincono sull'eredita']")
    nuova = jpeg_vero(77)
    r3 = pubblica({**BASE, "titolo": "Miele di tiglio 500g",
                   "foto": [uri(nuova)], "copia_foto_da": orig})
    prova("ne entra una sola", 1, r3["foto_salvate"])
    with open(os.path.join(FOTO, f"a{r3['id']}_0.jpg"), "rb") as f:
        prova("...ed e' quella scelta", nuova, f.read())

    print("\n[la guardia di proprieta']")
    con = SRV.db()
    con.execute("INSERT INTO annunci(venditore_id,titolo,prezzo_sats,"
                "categoria,stato,creato,foto) VALUES(333,'Roba d''altri',"
                "1,'Altro','attivo',1,'[\"a1_0.jpg\"]')")
    con.commit()
    altrui = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    con.close()
    # DALL'11 OTT 2026 (cantiere foto-obbligatorie) IL PATTO DEL CURSORE
    # STORTO E' CAMBIATO: prima un id altrui o storto non copiava niente
    # e l'annuncio nasceva lo stesso, senza foto. Adesso senza foto non
    # nasce niente — quindi chi non ne sceglie e non ne ha da ereditare
    # riceve il no della regola, e la guardia di proprieta' si vede dal
    # fatto che le foto di un altro NON contano come «da ereditare».
    def rifiuto(corpo):
        try:
            pubblica(corpo)
        except SRV.HTTPException as e:
            return e.status_code, e.detail
        return 200, ""

    def nate(titolo):
        con = SRV.db()
        n = con.execute("SELECT COUNT(*) FROM annunci WHERE titolo=?",
                        (titolo,)).fetchone()[0]
        con.close()
        return n

    r4 = rifiuto({**BASE, "titolo": "Copio le foto di un altro",
                  "foto": [], "copia_foto_da": altrui})
    prova("le foto di un altro non si copiano: senza foto sue, e' un no",
          (400, SRV.MSG_SERVE_UNA_FOTO), r4)
    prova("...e non nasce nessuna riga", 0,
          nate("Copio le foto di un altro"))
    for storto in (None, "", "pippo", 999999):
        r5 = rifiuto({**BASE, "titolo": f"Storto {storto!r}",
                      "foto": [], "copia_foto_da": storto})
        prova(f"id storto ({storto!r}): niente da ereditare, e' un no",
              (400, 0), (r5[0], nate(f"Storto {storto!r}")))
    r4b = pubblica({**BASE, "titolo": "Le foto di un altro, ma con la mia",
                    "foto": [uri(jpeg_vero(4))], "copia_foto_da": altrui})
    prova("...con una foto propria si pubblica, e di quella altrui niente",
          1, r4b["foto_salvate"])

    print("\n[senza duplicato]")
    r6 = rifiuto({**BASE, "titolo": "Senza duplicato", "foto": []})
    prova("pubblicare senza foto non e' piu' pubblicare",
          (400, SRV.MSG_SERVE_UNA_FOTO), r6)
    r7 = pubblica({**BASE, "titolo": "Con la sua foto",
                   "foto": [uri(jpeg_vero(3))]})
    prova("...con una foto si'", 1, r7["foto_salvate"])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database e foto usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
