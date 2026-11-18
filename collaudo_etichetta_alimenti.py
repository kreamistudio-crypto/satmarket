# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ETICHETTA DEGLI ALIMENTI (17 nov 2026, cantiere
etichetta-alimenti).

Da Luca, via Andrea: per l'art. 14 del Regolamento UE 1169/2011 chi
compra online deve poter leggere ingredienti, allergeni, peso netto e
valori nutrizionali PRIMA di pagare. Facoltativa per chi vende
(decisione di Andrea, 17 nov).

`prove.py` difende la forma e il giudice puro. Qui gira il SERVER VERO
su un database usa-e-getta — pubblica, modifica e la scheda del singolo
annuncio — e si chiedono le cose che solo la filiera intera puo' dire:
  · un alimento pubblicato con l'etichetta la ritrova nella scheda,
    coi numeri puliti e l'energia completata dal conto;
  · LA TABELLA E' OBBLIGATORIA (18 nov 2026): un alimento senza tabella
    e senza motivo d'esenzione e' un 400 che non lascia righe, anche dal
    client di ieri che non manda la chiave; col motivo passa, e la scheda
    lo dice; spenta la leva ETICHETTA_OBBLIGATORIA, torna facoltativa;
  · in modifica gli annunci di prima restano in pace finche' il form
    non li ritocca (chiave assente = conserva);
  · una tabella a meta' o storta e' un 400 che non lascia righe;
  · fuori da «Alimenti e bevande» la chiave si butta, e la scheda non
    mostra un'etichetta rimasta in colonna;
  · in modifica la chiave assente conserva, quella vuota cancella, e
    cambiare categoria se la porta via;
  · a leva spenta il server non scrive e la scheda non manda — e quel
    che c'era torna con la leva.

NON TOCCA NIENTE DI VERO: config sostituito PRIMA dell'import di
server, AI e notifiche di cartone, foto in una cartella usa-e-getta.

USO:  python collaudo_etichetta_alimenti.py
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
VENDITORE = {"id": 222, "nome": "Vende", "first_name": "Vende",
             "username": "vende", "admin": False}
CHI = [VENDITORE]

ETICHETTA = {"ingredienti": "Miele  millefiori\n  italiano",
             "allergeni": ["latte", "inventato", "glutine"],
             "peso": "500", "unita": "g", "base": "100g",
             "valori": {"kcal": "304", "grassi": "0", "saturi": "0",
                        "carboidrati": "82,4", "zuccheri": "82,1",
                        "proteine": "0,3", "sale": "0,01"}}


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
    return "data:image/jpeg;base64," + base64.b64encode(
        out.getvalue()).decode()


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-etichetta-")
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
    # NIENTE ETICHETTA_ALIMENTI nel config: la leva deve nascere accesa
    # da sola (le leve nuove sono accese di serie)
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    server.init_db()
    foto = os.path.join(tmp, "foto")
    os.makedirs(foto, exist_ok=True)
    server.FOTO_DIR = foto

    async def zitto(*a, **k):
        return None

    async def ai_finta(titolo, descrizione=""):
        return None

    async def cambio_finto():
        return 100_000.0

    server.cambio_btc_eur = cambio_finto
    server.verifica_utente = lambda *a, **k: CHI[0]
    server.utente_se_autenticato = lambda *a, **k: None
    server.moderazione_ai = ai_finta
    server.notifica = zitto
    for nome in ("notifica_admin", "annuncio_su_nostr", "premia_distintivi",
                 "avvisa_contatto_mancante", "polso_ordini_admin",
                 "promo_venduto"):
        setattr(server, nome, zitto)
    server.accoda_promo = lambda *a, **k: None
    server.accoda_match = lambda *a, **k: None
    con = server.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(?,?,?,1)", (222, "Vende", "neg222"))
    con.commit()
    con.close()


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


BASE = {"prezzo_sats": 12000, "categoria": "Alimenti e bevande",
        "zona": "Cuneo (CN)", "descrizione": "Raccolto quest'estate",
        "consegna": "ritiro", "quantita": 3}


def pubblica(titolo, **extra):
    return chiama(SRV.pubblica, {**BASE, "titolo": titolo,
                                 "foto": [jpeg_vero(len(titolo))],
                                 **extra}, None)


def modifica(aid, **extra):
    corpo = {**BASE, "titolo": colonna(aid, "titolo"), **extra}
    return chiama(SRV.modifica_annuncio, corpo, aid, None)


def colonna(aid, nome):
    con = SRV.db()
    r = con.execute(f"SELECT {nome} FROM annunci WHERE id=?",
                    (aid,)).fetchone()
    con.close()
    return r[0] if r else None


def scheda(aid):
    return SRV.un_annuncio(aid, "", "")


def conta(titolo):
    con = SRV.db()
    n = con.execute("SELECT COUNT(*) FROM annunci WHERE titolo=?",
                    (titolo,)).fetchone()[0]
    con.close()
    return n


def main():
    print("=" * 58)
    print("  L'ETICHETTA DEGLI ALIMENTI — il giro vero")
    print("=" * 58)
    avvio()

    # ---------------------------------------------------------------
    print("\n[un alimento con l'etichetta]")
    prova("la leva nasce accesa senza riga nel config", True,
          SRV.ETICHETTA_ALIMENTI)
    codice, r = pubblica("Miele millefiori", etichetta=ETICHETTA)
    prova("si pubblica", 200, codice)
    aid = r["id"] if codice == 200 else 0
    e = scheda(aid).get("etichetta")
    prova("la scheda la porta: ingredienti a righe, spazi puliti",
          "Miele millefiori\nitaliano", (e or {}).get("ingredienti"))
    prova("...gli allergeni ignoti si buttano, l'ordine e' quello della "
          "legge", ["glutine", "latte"], (e or {}).get("allergeni"))
    prova("...il peso netto e la sua unita'", (500.0, "g"),
          ((e or {}).get("peso"), (e or {}).get("unita")))
    prova("...i numeri con la virgola italiana diventano numeri, e i kJ "
          "li fa il conto", {"kj": 1272, "kcal": 304.0, "grassi": 0.0,
                             "saturi": 0.0, "carboidrati": 82.4,
                             "zuccheri": 82.1, "proteine": 0.3,
                             "sale": 0.01},
          (e or {}).get("valori"))
    prova("...per 100 g", "100g", (e or {}).get("base"))

    # ---------------------------------------------------------------
    print("\n[obbligatoria: senza tabella non si pubblica (18 nov 2026)]")
    prova("la leva nasce accesa senza riga nel config", True,
          SRV.ETICHETTA_OBBLIGATORIA)
    codice, detail = pubblica("Marmellata di fichi")
    prova("il client di ieri (niente chiave): 400 che dice di aggiornare, "
          "nessuna riga", (400, True, 0),
          (codice, "aggiorna l'app" in str(detail),
           conta("Marmellata di fichi")))
    codice, detail = pubblica("Olio nuovo", etichetta={"valori": {}})
    prova("un'etichetta tutta vuota: 400 che nomina la tabella e "
          "l'esenzione, nessuna riga", (400, True, True, 0),
          (codice, "obbligatoria" in str(detail),
           "Non dovuta per legge" in str(detail), conta("Olio nuovo")))
    codice, detail = pubblica("Olio novello", etichetta={
        "ingredienti": "Olive", "peso": "750", "unita": "ml"})
    prova("...anche con ingredienti e peso ma senza tabella", (400, 0),
          (codice, conta("Olio novello")))
    codice, detail = pubblica("Olio di frantoio", etichetta={
        "esente": "inventato", "valori": {}})
    prova("...e un motivo che non esiste non vale", (400, 0),
          (codice, conta("Olio di frantoio")))
    codice, r2 = pubblica("Marmellata della nonna", etichetta={
        "esente": "artigiano", "ingredienti": "Fichi, zucchero"})
    prova("col motivo d'esenzione si pubblica", 200, codice)
    a2 = r2["id"] if codice == 200 else 0
    e2 = scheda(a2).get("etichetta") or {}
    prova("...e la scheda porta il motivo e gli ingredienti, senza tabella",
          ("artigiano", "Fichi, zucchero", False),
          (e2.get("esente"), e2.get("ingredienti"), "valori" in e2))
    codice, r3 = pubblica("Miele con tabella", etichetta={
        **ETICHETTA, "esente": "artigiano"})
    prova("con la tabella il motivo non si scrive: la tabella vince",
          (200, False, True),
          (codice, "esente" in (scheda(r3["id"]).get("etichetta") or {}),
           "valori" in (scheda(r3["id"]).get("etichetta") or {}))
          if codice == 200 else (codice,))
    for motivo in SRV.ESENZIONI_ETICHETTA:
        codice, r = pubblica(f"Esente {motivo}",
                             etichetta={"esente": motivo})
        prova(f"il motivo «{motivo}» passa e si rilegge", (200, motivo),
              (codice, (scheda(r["id"]).get("etichetta") or {})
               .get("esente") if codice == 200 else None))
    codice, _ = pubblica("Sedia senza etichetta", categoria="Casa e giardino",
                         condizione="buono")
    prova("fuori dagli alimenti l'obbligo non c'e'", 200, codice)
    SRV.ETICHETTA_OBBLIGATORIA = False
    try:
        codice, r7 = pubblica("Confettura facoltativa")
        prova("leva spenta: si pubblica senza la chiave, come il 17 nov",
              (200, ""), (codice, colonna(r7["id"], "etichetta")
                          if codice == 200 else None))
        codice, r8 = pubblica("Confettura vuota", etichetta={"valori": {}})
        prova("...e un'etichetta vuota vale «nessuna»", (200, ""),
              (codice, colonna(r8["id"], "etichetta")
               if codice == 200 else None))
        codice, r9 = pubblica("Confettura esente",
                              etichetta={"esente": "artigiano"})
        prova("...il motivo, se c'e', si scrive lo stesso",
              (200, "artigiano"),
              (codice, (scheda(r9["id"]).get("etichetta") or {})
               .get("esente") if codice == 200 else None))
    finally:
        SRV.ETICHETTA_OBBLIGATORIA = True

    # ---------------------------------------------------------------
    print("\n[i campi facoltativi del 18 nov: origine, conservazione, "
          "lotto, scadenza]")
    codice, rc = pubblica("Miele di sulla", etichetta={
        **ETICHETTA, "origine": "  Italia,   Calabria ",
        "conservazione": "In luogo fresco\ne asciutto", "lotto": "L2411",
        "scadenza": "2027-12-31"})
    ec = scheda(rc["id"]).get("etichetta") or {} if codice == 200 else {}
    prova("si rileggono puliti, su una riga", (200, "Italia, Calabria",
          "In luogo fresco e asciutto", "L2411", "2027-12-31"),
          (codice, ec.get("origine"), ec.get("conservazione"),
           ec.get("lotto"), ec.get("scadenza")))
    codice, rc = pubblica("Miele di tiglio", etichetta={
        **ETICHETTA, "scadenza": "2020-01-31"})
    prova("una scadenza passata non si rifiuta (il «preferibilmente "
          "entro» si vende)", 200, codice)
    codice, rc = pubblica("Miele senza extra", etichetta=ETICHETTA)
    prova("...e senza i campi nuovi le chiavi non ci sono",
          [False] * 4, [k in (scheda(rc["id"]).get("etichetta") or {})
                        for k in ("origine", "conservazione", "lotto",
                                  "scadenza")] if codice == 200 else None)
    for nome, extra, frase in (
            ("origine troppo lunga", {"origine": "x" * 121}, "troppo lungo"),
            ("un contatto nella conservazione",
             {"conservazione": "scrivimi @venditore"}, "link"),
            ("una scadenza storta", {"scadenza": "31/12/2027"}, "non è una data"),
            ("una data che non esiste", {"scadenza": "2027-02-30"},
             "non è una data")):
        titolo = f"Extra {nome}"
        codice, detail = pubblica(titolo, etichetta={**ETICHETTA, **extra})
        prova(f"{nome}: 400 che lo dice, nessuna riga", (400, True, 0),
              (codice, frase in str(detail), conta(titolo)))

    # ---------------------------------------------------------------
    print("\n[le tabelle storte si dicono, e non lasciano righe]")
    casi = [
        ("tabella a meta'", {"valori": {"kcal": "300", "grassi": "2"}},
         "Completa la tabella"),
        ("saturi oltre i grassi", {"valori": {**ETICHETTA["valori"],
                                              "grassi": "1",
                                              "saturi": "3"}},
         "saturi"),
        ("zuccheri oltre i carboidrati",
         {"valori": {**ETICHETTA["valori"], "zuccheri": "90"}},
         "zuccheri"),
        ("piu' di 100 g su 100 g",
         {"valori": {**ETICHETTA["valori"], "proteine": "40"}},
         "100 g su 100 g"),
        ("un numero che non e' un numero",
         {"valori": {**ETICHETTA["valori"], "sale": "poco"}}, "sale"),
        ("un valore negativo", {"peso": "-3"}, "peso netto"),
        ("un link negli ingredienti",
         {"ingredienti": "miele, vedi https://esempio.it"}, "link"),
        ("ingredienti troppo lunghi", {"ingredienti": "x" * 1501},
         "troppo lunghi"),
        ("un'etichetta che non e' un oggetto", "miele", "non si legge"),
    ]
    for nome, et, frase in casi:
        titolo = f"Storto {nome}"
        codice, detail = pubblica(titolo, etichetta=et)
        prova(f"{nome}: 400 che lo dice, nessuna riga",
              (400, True, 0),
              (codice, frase.lower() in str(detail).lower(), conta(titolo)))
    codice, r4 = pubblica("Sciroppo d'acero",
                          etichetta={"base": "100ml", "valori": {
                              "kj": "1400", "grassi": "0", "saturi": "0",
                              "carboidrati": "112", "zuccheri": "110",
                              "proteine": "0", "sale": "0"}})
    prova("per 100 ml i grammi possono passare i 100 (lo sciroppo pesa)",
          (200, 335), (codice, (scheda(r4["id"]).get("etichetta") or {})
                       .get("valori", {}).get("kcal")
                       if codice == 200 else None))

    # ---------------------------------------------------------------
    print("\n[fuori dagli alimenti non c'e']")
    codice, r5 = pubblica("Tastiera", categoria="Elettronica",
                          condizione="buono", etichetta=ETICHETTA)
    prova("un trapano con l'etichetta: si pubblica e la chiave si butta",
          (200, ""), (codice, colonna(r5["id"], "etichetta")
                      if codice == 200 else None))
    con = SRV.db()
    con.execute("UPDATE annunci SET categoria='Collezionismo' WHERE id=?",
                (a2,))
    con.execute("UPDATE annunci SET etichetta=? WHERE id=?",
                (colonna(aid, "etichetta"), a2))
    con.commit()
    con.close()
    prova("un moderatore lo sposta di categoria: la scheda non la "
          "mostra piu'", False, "etichetta" in scheda(a2))
    con = SRV.db()
    con.execute("UPDATE annunci SET categoria='Alimenti e bevande', "
                "etichetta='{storto' WHERE id=?", (a2,))
    con.commit()
    con.close()
    prova("una colonna rovinata e' «nessuna», mai un 500", False,
          "etichetta" in scheda(a2))

    # ---------------------------------------------------------------
    print("\n[la modifica]")
    prima = colonna(aid, "etichetta")
    codice, _ = modifica(aid, descrizione="Ancora qualche vasetto")
    prova("chiave assente (il client di ieri): resta quella di prima",
          (200, prima), (codice, colonna(aid, "etichetta")))
    codice, _ = modifica(aid, etichetta={**ETICHETTA,
                                         "allergeni": ["sesamo"]})
    prova("chiave piena: si riscrive", (200, ["sesamo"]),
          (codice, (scheda(aid).get("etichetta") or {}).get("allergeni")))
    codice, detail = modifica(aid, etichetta={"valori": {"kcal": "1"}})
    prova("una tabella a meta' in modifica e' un 400 che non tocca "
          "niente", (400, ["sesamo"]),
          (codice, json.loads(colonna(aid, "etichetta")).get("allergeni")))
    codice, _ = modifica(aid, etichetta={})
    prova("chiave vuota: con la tabella obbligatoria e' un 400 che non "
          "tocca niente", (400, ["sesamo"]),
          (codice, json.loads(colonna(aid, "etichetta")).get("allergeni")))
    codice, _ = modifica(aid, etichetta={"esente": "fresco"})
    prova("...col motivo si sostituisce la tabella", (200, "fresco", False),
          (codice, (scheda(aid).get("etichetta") or {}).get("esente"),
           "valori" in (scheda(aid).get("etichetta") or {})))
    SRV.ETICHETTA_OBBLIGATORIA = False
    try:
        codice, _ = modifica(aid, etichetta={})
        prova("...e a leva spenta la chiave vuota cancella, come il 17 nov",
              (200, ""), (codice, colonna(aid, "etichetta")))
    finally:
        SRV.ETICHETTA_OBBLIGATORIA = True
    codice, _ = modifica(aid, descrizione="Un annuncio di prima")
    prova("un annuncio di prima SENZA etichetta si ritocca dal client di "
          "ieri (chiave assente = conserva)", (200, ""),
          (codice, colonna(aid, "etichetta")))
    modifica(aid, etichetta=ETICHETTA)
    codice, _ = modifica(aid, categoria="Casa e giardino",
                         condizione="buono", etichetta=ETICHETTA)
    prova("cambiare categoria se la porta via", (200, ""),
          (codice, colonna(aid, "etichetta")))

    # ---------------------------------------------------------------
    print("\n[la leva spenta]")
    modifica(aid, etichetta=ETICHETTA)
    salvata = colonna(aid, "etichetta")
    SRV.ETICHETTA_ALIMENTI = False
    try:
        prova("spenta: la scheda non la manda", False,
              "etichetta" in scheda(aid))
        codice, _ = modifica(aid, etichetta={})
        prova("...il server non la scrive (nemmeno per cancellarla)",
              (200, salvata), (codice, colonna(aid, "etichetta")))
        codice, r6 = pubblica("Miele di castagno", etichetta=ETICHETTA)
        prova("...e un annuncio nuovo nasce senza", (200, ""),
              (codice, colonna(r6["id"], "etichetta")
               if codice == 200 else None))
    finally:
        SRV.ETICHETTA_ALIMENTI = True
    prova("riaccesa: quella di prima torna nella scheda", ["glutine",
                                                           "latte"],
          (scheda(aid).get("etichetta") or {}).get("allergeni"))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
