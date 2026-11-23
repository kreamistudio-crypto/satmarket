# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE FOTO IN ORDINE, DELLE LORO DESCRIZIONI E DELLE
VARIANTI (23 nov 2026, cantiere foto-varianti, chieste da Zzap).

Le rotte VERE di pubblicazione, modifica e revisione:

  · la descrizione di ogni foto si salva allineata alla foto, e segue la
    foto entrata quando un'altra viene scartata;
  · in modifica le foto che restano si nominano, le nuove arrivano come
    data:, l'ordine e' quello della lista e quel che manca se ne va
    (anche dal disco); un client di ieri (solo foto nuove) sostituisce
    in blocco come sempre;
  · descrizioni e varianti passano dalla moderazione;
  · le varianti semplici si scrivono nella colonna `scelte` (la stessa
    dei negozi collegati), e la cassa le esige;
  · le varianti col loro prezzo fanno una famiglia: un annuncio per
    voce, prezzo e pezzi suoi, foto copiate e non condivise; nata in
    revisione, si decide tutta insieme.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server e FOTO_DIR punta a una cartella usa-e-getta.

USO:  python collaudo_foto_varianti.py
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
LETTI = []

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
    tmp = tempfile.mkdtemp(prefix="barattolo-foto-varianti-")
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
    server.avvisa_revisione = zitto
    # LA MODERAZIONE SI ASCOLTA: ogni testo che le arriva si annota, e
    # una parola spia la fa rispondere come vuole la prova
    async def ai(titolo, testo):
        LETTI.append(testo)
        if "SPIA_VIETATO" in testo:
            return ("vietato", "spia")
        if "SPIA_DUBBIO" in testo:
            return ("dubbio", "spia")
        return None
    server.moderazione_ai = ai
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


BASE = {"titolo": "Maglietta di cotone", "prezzo_sats": 30000,
        "categoria": "Abbigliamento", "zona": "Torino (TO)",
        "descrizione": "Cotone pesante", "consegna": "spedizione",
        "spedizione_sats": 2000, "quantita": 3, "condizione": "nuovo"}


def main():
    tmp = avvio()
    nera = uri(jpeg_nero())
    f1, f2, f3, f4 = (uri(jpeg_vero(s)) for s in (1, 2, 3, 4))

    print("\n[le descrizioni delle foto, pubblicando]")
    LETTI.clear()
    codice, r = pubblica({**BASE, "foto": [f1, nera, f2],
                          "didascalie": ["Davanti", "la nera", "  Dietro  "]})
    aid = r.get("id")
    prova("si pubblica con le due buone", (200, 2),
          (codice, r.get("foto_salvate")))
    prova("...e ogni descrizione resta con la SUA foto (la nera si porta "
          "via la sua)", ["Davanti", "Dietro"],
          json.loads(riga(aid)["didascalie"]))
    prova("la moderazione le ha lette con la descrizione", True,
          bool(LETTI) and "Davanti" in LETTI[-1] and "Dietro" in LETTI[-1]
          and "Cotone pesante" in LETTI[-1])
    codice, detto = pubblica({**BASE, "titolo": "Troppo lunga",
                              "foto": [f1], "didascalie": ["x" * 81]})
    prova("oltre 80 caratteri: 400 che dice quale foto", (400, True),
          (codice, "foto 1" in str(detto)))
    codice, _ = pubblica({**BASE, "titolo": "Spia nella foto",
                          "foto": [f1], "didascalie": ["SPIA_VIETATO"]})
    prova("una descrizione vietata ferma la pubblicazione", 400, codice)
    codice, r0 = pubblica({**BASE, "titolo": "Senza descrizioni",
                           "foto": [f1]})
    prova("senza descrizioni la colonna resta vuota", (200, ""),
          (codice, riga(r0["id"])["didascalie"]))

    print("\n[la modifica: restano, si spostano, se ne aggiungono]")
    prima = foto_di(aid)
    file_prima = file_di(aid)
    codice, r = modifica(aid, {**BASE, "foto": [prima[1], f3, prima[0]],
                               "didascalie": ["Dietro, ora prima",
                                              "Nuova", ""]})
    dopo = foto_di(aid)
    prova("si salva, e la nuova entra", (200, 1),
          (codice, r.get("foto_salvate")))
    prova("l'ordine e' quello chiesto, le vecchie col loro nome",
          (prima[1], prima[0]), (dopo[0], dopo[2]) if len(dopo) == 3
          else None)
    prova("...la nuova in mezzo, con un nome nuovo", True,
          len(dopo) == 3 and dopo[1] not in prima)
    prova("le descrizioni seguono l'ordine nuovo",
          ["Dietro, ora prima", "Nuova", ""],
          json.loads(riga(aid)["didascalie"]))
    prova("le vecchie che restano sono ancora sul disco", True,
          all(n in file_di(aid) for n in prima))
    codice, r = modifica(aid, {**BASE, "foto": [dopo[2]],
                               "didascalie": ["Sola"]})
    prova("togliendone due con la ✕: si salva", 200, codice)
    prova("...resta quella sola, con la sua descrizione",
          ([dopo[2]], ["Sola"]),
          (foto_di(aid), json.loads(riga(aid)["didascalie"])))
    prova("...e le tolte se ne vanno dal disco (con le miniature)",
          sorted([dopo[2], dopo[2][:-4] + "_min.jpg"]), file_di(aid))
    codice, detto = modifica(aid, {**BASE, "foto": [dopo[2], dopo[2]]})
    prova("la stessa foto due volte: 400", 400, codice)
    codice, _ = modifica(aid, {**BASE, "foto": [dopo[2]] + [f1] * 5})
    prova("piu' di cinque: 400", 400, codice)
    codice, _ = modifica(aid, {**BASE, "foto": [dopo[2]],
                               "didascalie": ["SPIA_VIETATO"]})
    prova("una descrizione vietata ferma anche la modifica", 400, codice)
    prova("...e la descrizione di prima e' intatta", ["Sola"],
          json.loads(riga(aid)["didascalie"]))
    codice, _ = modifica(aid, {**BASE, "titolo": "Solo il titolo"})
    prova("senza la chiave «foto» le foto e le descrizioni restano",
          (200, [dopo[2]], ["Sola"]),
          (codice, foto_di(aid), json.loads(riga(aid)["didascalie"])))
    codice, r = modifica(aid, {**BASE, "foto": [f4]})
    prova("il client di ieri (solo foto nuove) sostituisce in blocco",
          (200, 1, True),
          (codice, len(foto_di(aid)), foto_di(aid)[0] != dopo[2]))
    prova("...e le descrizioni vecchie non restano appese", "",
          riga(aid)["didascalie"])

    print("\n[le varianti semplici]")
    LETTI.clear()
    codice, r = pubblica({**BASE, "titolo": "Felpa", "foto": [f1],
                          "scelte": [[" Colore ", ["rosso", " blu", "blu",
                                                   ""]]]})
    sid = r.get("id")
    prova("si pubblica, una riga sola", 200, codice)
    prova("la colonna `scelte` e' quella dei negozi, ripulita",
          [["Colore", ["rosso", "blu"]]], json.loads(riga(sid)["scelte"]))
    prova("la moderazione le ha lette", True,
          bool(LETTI) and "Colore: rosso, blu" in LETTI[-1])
    sc = SRV.scelte_lette(riga(sid)["scelte"])
    prova("la cassa le esige e accetta una voce dell'elenco",
          "Colore: blu", SRV.scelte_da_payload(sc, {"Colore": "blu"}))
    try:
        SRV.scelte_da_payload(sc, {"Colore": "verde"})
        fuori = None
    except SRV.HTTPException as e:
        fuori = e.status_code
    prova("...e rifiuta una voce che non c'e'", 400, fuori)
    codice, detto = pubblica({**BASE, "titolo": "Felpa senza nome",
                              "foto": [f1], "scelte": [["", ["rosso"]]]})
    prova("senza nome: 400", 400, codice)
    codice, _ = modifica(sid, {**BASE, "titolo": "Felpa",
                               "scelte": [["Taglia", ["S", "M"]]]})
    prova("in modifica si cambiano", (200, [["Taglia", ["S", "M"]]]),
          (codice, json.loads(riga(sid)["scelte"])))
    codice, _ = modifica(sid, {**BASE, "titolo": "Felpa ritoccata"})
    prova("...senza la chiave restano", [["Taglia", ["S", "M"]]],
          json.loads(riga(sid)["scelte"]))
    codice, _ = modifica(sid, {**BASE, "titolo": "Felpa", "scelte": []})
    prova("...e con la lista vuota si tolgono", (200, ""),
          (codice, riga(sid)["scelte"]))

    print("\n[le varianti col loro prezzo e i loro pezzi]")
    codice, r = pubblica({**BASE, "titolo": "Cappello", "foto": [f1, f2],
                          "didascalie": ["Fronte", ""],
                          "varianti": {"nome": "Colore", "voci": [
                              {"voce": "rosso", "prezzo": "", "quantita": ""},
                              {"voce": "blu", "prezzo": 45000,
                               "quantita": 7},
                              {"voce": "verde", "prezzo": "",
                               "quantita": 1}]}})
    capo = r.get("id")
    prova("si pubblica", 200, codice)
    con = SRV.db()
    fam = [dict(x) for x in con.execute(
        "SELECT * FROM annunci WHERE famiglia=? ORDER BY id",
        (f"u:{capo}",))]
    con.close()
    prova("tre annunci, una famiglia, la prima e' quello pubblicato",
          (3, capo), (len(fam), fam[0]["id"] if fam else None))
    prova("titoli col nome della voce",
          ["Cappello – rosso", "Cappello – blu", "Cappello – verde"],
          [x["titolo"] for x in fam])
    prova("il titolo della card e' quello scritto", {"Cappello"},
          {x["famiglia_titolo"] for x in fam})
    prova("prezzi: vuoto = quello dell'annuncio", [30000, 45000, 30000],
          [x["prezzo_sats"] for x in fam])
    prova("pezzi: vuoto = quelli dell'annuncio", [3, 7, 1],
          [x["quantita"] for x in fam])
    prova("le opzioni dicono la voce",
          [[["Colore", "rosso"]], [["Colore", "blu"]], [["Colore", "verde"]]],
          [json.loads(x["opzioni"]) for x in fam])
    prova("tutte in vetrina", {"attivo"}, {x["stato"] for x in fam})
    nomi_fam = [json.loads(x["foto"]) for x in fam]
    prova("ognuna ha le sue due foto, mai gli stessi file", (True, 6),
          (all(len(n) == 2 for n in nomi_fam),
           len({f for n in nomi_fam for f in n})))
    prova("...e le descrizioni viaggiano con le foto", {'["Fronte", ""]'},
          {x["didascalie"] for x in fam})
    con = SRV.db()   # la card vuole il venditore fra gli utenti
    con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome) "
                "VALUES(222, 'Vende')")
    con.commit()
    con.close()
    righe = SRV.arricchisci_righe_vetrina([dict(SRV.db().execute(
        f"SELECT {SRV.CAMPI_VETRINA} FROM annunci a JOIN utenti u ON "
        "u.tg_id=a.venditore_id WHERE a.id=?", (capo,)).fetchone())])
    prova("la card sa che sono tre e che i prezzi cambiano", (3, True),
          (righe[0].get("famiglia_n"), righe[0].get("famiglia_varia")))
    codice, _ = modifica(fam[1]["id"], {**BASE, "titolo": "Cappello – blu",
                                        "prezzo_sats": 46000, "quantita": 7,
                                        "foto": [nomi_fam[1][0]]})
    prova("una variante si ritocca da sola", (200, 46000, 2),
          (codice, riga(fam[1]["id"])["prezzo_sats"],
           len(foto_di(fam[0]["id"]))))
    prova("...e le foto delle sorelle restano sul disco", True,
          all(n in os.listdir(FOTO) for n in nomi_fam[0] + nomi_fam[2]))
    codice, detto = pubblica({**BASE, "titolo": "Una sola voce",
                              "foto": [f1], "varianti": {
                                  "nome": "Colore",
                                  "voci": [{"voce": "rosso"}]}})
    prova("con una voce sola: 400", 400, codice)
    codice, _ = pubblica({**BASE, "titolo": "Voci doppie", "foto": [f1],
                          "varianti": {"nome": "Colore", "voci": [
                              {"voce": "Rosso"}, {"voce": "rosso"}]}})
    prova("con due voci uguali: 400", 400, codice)
    codice, _ = pubblica({**BASE, "titolo": "Prezzo storto", "foto": [f1],
                          "varianti": {"nome": "Colore", "voci": [
                              {"voce": "a"}, {"voce": "b",
                                              "prezzo": -5}]}})
    prova("con un prezzo storto: 400", 400, codice)

    print("\n[la famiglia nata in revisione]")
    codice, r = pubblica({**BASE, "titolo": "Borsa",
                          "descrizione": "SPIA_DUBBIO", "foto": [f1],
                          "varianti": {"nome": "Colore", "voci": [
                              {"voce": "nera"}, {"voce": "beige"}]}})
    capo2 = r.get("id")
    prova("nasce in revisione", (200, True), (codice, r.get("revisione")))
    con = SRV.db()
    stati = lambda: [x["stato"] for x in con.execute(
        "SELECT stato FROM annunci WHERE famiglia=? ORDER BY id",
        (f"u:{capo2}",))]
    prova("...tutte e due", ["revisione", "revisione"], stati())
    ok, _ = asyncio.run(SRV.decidi_revisione(capo2, "pubblica", 999))
    prova("approvata la prima, si approva la famiglia",
          (True, ["attivo", "attivo"]), (ok, stati()))
    con.close()

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database e foto usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
