# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE FOTO SCARTATE (28 set 2026, cantiere modifica-foto).

Dal campo: l'annuncio #461 e' nato senza foto. Il telefono (Android,
Mini App dentro Telegram) disegnava le foto NERE nella tela, il server
le scartava giustamente come «immagine vuota» — e l'annuncio si
pubblicava lo stesso, vuoto. La cura del client sta in miniapp.html (e
la provano i banchi di prove.py); qui si chiamano le ROTTE VERE per le
domande che solo il server puo' chiudere:

  · se TUTTE le foto scelte vengono scartate, l'annuncio NON si
    pubblica: 400 col motivo di ognuna, la riga ritirata (cancellazione
    morbida, 'rimosso'), niente in vetrina, e il secondo tentativo con
    una foto buona passa (lo scudo anti-doppione non lo scambia per un
    retry);
  · se ne entra ALMENO una, si pubblica e lo scarto si dice, con la
    posizione della foto;
  · chi non sceglie nessuna foto NON pubblica (dall'11 ott 2026, cantiere
    foto-obbligatorie): 400 prima dell'INSERT, nessuna riga;
  · una MODIFICA le cui foto nuove vengono scartate tutte non si salva
    affatto: campi di prima, foto di prima, file di prima sul disco;
  · una modifica con la lista VUOTA non tocca le foto;
  · una modifica con foto nuove buone sostituisce il set, e le vecchie
    se ne vanno dal disco solo DOPO.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server e FOTO_DIR punta a una cartella usa-e-getta.

USO:  python collaudo_foto_scartate.py
"""

import asyncio
import base64
import io
import json
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
FOTO = None

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
    tmp = tempfile.mkdtemp(prefix="barattolo-foto-scartate-")
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
    # come in collaudo_duplicato: nessun modello si chiama davvero, e un
    # `anthropic` vecchio non deve fermare il collaudo all'import
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


def foto_di(aid):
    r = riga(aid)
    return json.loads(r["foto"]) if r and r["foto"] else []


def file_di(aid):
    return sorted(f for f in os.listdir(FOTO) if f.startswith(f"a{aid}_"))


def uri(raw):
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def jpeg_vero(seme=0):
    """Una foto che non e' una tinta unita."""
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


def jpeg_nero():
    """IL CASO VERO: quello che la tela del telefono consegnava — un
    JPEG sano, 1200x900, tutto nero."""
    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", (1200, 900), (0, 0, 0)).save(out, "JPEG", quality=90)
    return out.getvalue()


PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"
BASE = {"titolo": "Lotto demo PlayStation", "prezzo_sats": 30000,
        "categoria": "Altro", "zona": "Torino (TO)",
        "descrizione": "Nove dischi funzionanti", "consegna": "spedizione",
        "spedizione_sats": 2000, "quantita": 1, "condizione": "buono"}


def main():
    tmp = avvio()
    nera = uri(jpeg_nero())

    print("\n[la pubblicazione con tutte le foto scartate]")
    codice, detto = pubblica({**BASE, "foto": [nera, nera]})
    prova("non si pubblica: 400", 400, codice)
    prova("...lo dice, e dice che i dati scritti restano", True,
          str(detto).startswith("Annuncio non pubblicato")
          and "quel che hai scritto è ancora qui" in str(detto))
    prova("...foto per foto, con la posizione", (True, True),
          ("la foto 1 non è stata accettata" in str(detto),
           "la foto 2 non è stata accettata" in str(detto)))
    prova("...e il motivo del server", True, "immagine vuota" in str(detto))
    con = SRV.db()
    ritirate = con.execute(
        "SELECT id, stato, foto FROM annunci WHERE titolo=?",
        (BASE["titolo"],)).fetchall()
    con.close()
    prova("la riga c'e' ma e' ritirata (cancellazione morbida)",
          [("rimosso", "")], [(r["stato"], r["foto"]) for r in ritirate])
    prova("...e sul disco non c'e' niente di suo", [],
          file_di(ritirate[0]["id"]) if ritirate else ["?"])
    codice, _ = pubblica({**BASE, "foto": [uri(PDF)]})
    prova("un PDF vestito da foto, da solo: nemmeno", 400, codice)

    print("\n[il secondo tentativo, con una foto buona]")
    codice, r = pubblica({**BASE, "foto": [uri(jpeg_vero())]})
    prova("passa: lo scudo anti-doppione non lo prende per un retry",
          (200, True), (codice, r.get("id") not in
                        [x["id"] for x in ritirate]))
    prova("...ed e' in vetrina con la sua foto", ("attivo", 1),
          (riga(r["id"])["stato"], len(foto_di(r["id"]))))

    print("\n[una buona e una scartata]")
    codice, r = pubblica({**BASE, "titolo": "Una buona e una nera",
                          "foto": [uri(jpeg_vero(3)), nera]})
    prova("si pubblica con quella buona", (200, 1),
          (codice, r.get("foto_salvate")))
    prova("...e lo scarto dice QUALE foto", True,
          len(r.get("foto_scarti", [])) == 1 and r["foto_scarti"][0]
          .startswith("la foto 2 non è stata accettata: immagine vuota"))

    # IL MONDO DI IERI E' FINITO L'11 OTT 2026 (cantiere
    # foto-obbligatorie): fino a quel giorno chi non sceglieva foto
    # pubblicava come sempre, e questa prova lo diceva. Adesso e' un
    # no, detto PRIMA dell'INSERT: nessuna riga da ritirare. Il resto
    # della regola nuova lo gira collaudo_foto_obbligatorie.py.
    print("\n[senza nessuna foto]")
    codice, detto = pubblica({**BASE, "titolo": "Senza foto, apposta",
                              "foto": []})
    prova("chi non sceglie foto non pubblica piu': 400 che si capisce",
          (400, SRV.MSG_SERVE_UNA_FOTO), (codice, detto))
    con = SRV.db()
    nate = con.execute("SELECT COUNT(*) FROM annunci WHERE titolo=?",
                       ("Senza foto, apposta",)).fetchone()[0]
    con.close()
    prova("...e non lascia nessuna riga, nemmeno ritirata", 0, nate)

    print("\n[la modifica con tutte le foto nuove scartate]")
    codice, r = pubblica({**BASE, "titolo": "Annuncio con due foto",
                          "foto": [uri(jpeg_vero(5)), uri(jpeg_vero(6))]})
    aid = r["id"]
    prima_foto, prima_file = foto_di(aid), file_di(aid)
    prova("parte con due foto e quattro file (pieni e miniature)",
          (2, 4), (len(prima_foto), len(prima_file)))
    codice, detto = modifica(aid, {**BASE, "titolo": "Titolo NUOVO",
                                   "foto": [nera]})
    prova("la modifica non si salva: 400", 400, codice)
    prova("...e dice che l'annuncio e' com'era, foto comprese", True,
          str(detto).startswith("Modifica non salvata")
          and "L'annuncio è com'era, foto comprese" in str(detto))
    prova("...la foto nuova con la sua posizione", True,
          "la foto 1 non è stata accettata: immagine vuota" in str(detto))
    prova("il titolo NON e' cambiato", "Annuncio con due foto",
          riga(aid)["titolo"])
    prova("le foto nel database sono quelle di prima", prima_foto,
          foto_di(aid))
    prova("...e i file sul disco pure", prima_file, file_di(aid))

    print("\n[la modifica con la lista vuota]")
    codice, r = modifica(aid, {**BASE, "titolo": "Ritocco il titolo",
                               "foto": []})
    prova("si salva", 200, codice)
    prova("...il titolo cambia", "Ritocco il titolo", riga(aid)["titolo"])
    prova("...e le foto NON si toccano", (prima_foto, prima_file),
          (foto_di(aid), file_di(aid)))
    codice, _ = modifica(aid, {**BASE, "titolo": "Senza la chiave foto"})
    prova("senza la chiave «foto»: idem", (200, prima_foto, prima_file),
          (codice, foto_di(aid), file_di(aid)))

    print("\n[la modifica con una foto nuova buona e una nera]")
    codice, r = modifica(aid, {**BASE, "titolo": "Foto nuove",
                               "foto": [uri(jpeg_vero(8)), nera]})
    prova("si salva con quella buona", (200, 1),
          (codice, r.get("foto_salvate")))
    prova("...e lo scarto dice QUALE foto", True,
          (r.get("foto_scarti") or [""])[0]
          .startswith("la foto 2 non è stata accettata"))
    nuove = foto_di(aid)
    prova("il set e' quello nuovo", True,
          len(nuove) == 1 and nuove[0] not in prima_foto)
    prova("le vecchie se ne sono andate dal disco, la nuova c'e'",
          sorted([nuove[0], nuove[0][:-4] + "_min.jpg"]), file_di(aid))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database e foto usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
