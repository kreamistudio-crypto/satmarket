# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CONFERMA DELL'INDIRIZZO (13 ott 2026, cantiere
«indirizzo-giusto», primo push).

IL CASO: chi compra sbaglia l'indirizzo, il pacco torna indietro, e le
spese di spedizione restavano sempre a chi vende. Il primo passo e'
far dire a chi compra, prima di pagare, «Ho controllato l'indirizzo:
se è sbagliato, le spese di spedizione restano a mio carico» — e
conservare QUANDO l'ha detto, cosi' il moderatore lo legge in disputa.
Insieme, il nome: la via non e' piu' «a casa» ma «a un indirizzo».

`prove.py` difende la forma e fa girare i giudici della pagina. Questo
script fa girare la cosa VERA — database, rotte, fatture contate — e
risponde alle domande su cui il push si regge:

  · la conferma si SALVA con l'ordine (mono e carrello), come data;
  · NESSUNA VENDITA SI BLOCCA: una pagina rimasta aperta, che la
    casella non ce l'ha, compra lo stesso — e l'ordine dice «nessuna
    conferma», che e' la verita';
  · la conferma SEGUE L'INDIRIZZO: riscritto senza rispuntare torna a
    zero, dalla cassa (la ripresa) come dal campo dentro l'ordine;
  · solo `True` e solo CON un indirizzo: ne' una stringa, ne' la via
    punto, ne' il ritiro;
  · in disputa il moderatore riceve il FATTO e la data, nella nota e
    nella sua lista — e MAI l'indirizzo;
  · a ordine chiuso l'indirizzo si cancella e la conferma RESTA (e' un
    fatto, non un dato personale);
  · gli avvisi e i rifiuti dicono «a un indirizzo», mai «a casa».

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, LNbits non viene mai chiamato (le fatture si
contano), le notifiche si registrano invece di partire. Gira senza
rete, ed e' cosi' che gira nella gabbia della CI.

USO:  python collaudo_indirizzo_confermato.py
"""

import asyncio
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []
DETTI = []      # (a chi, testo): le notifiche alle persone
ADMIN = []      # (testo, argomento): quel che arriva ai moderatori

CAMBIO = 100_000.0
UTENTE = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}

CASA = {"nome": "Mario Rossi", "via": "Via Garibaldi 17", "cap": "27100",
        "citta": "Pavia", "provincia": "PV", "telefono": "3330000000"}
ALTRA = dict(CASA, via="Corso Cavour 3")


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alza(nome, fn, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        codice = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if codice == 400 and (not dentro or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso 400 con {dentro!r}"
              f"\n      avuto:  {codice} {testo!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-indirizzo-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME e lascia passare solo INCOLLA_QUI
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    cfg.PROTEZIONE_PERCENTO = 0
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return CAMBIO

    async def zitta(*a, **k):
        return None

    async def mai_pagata(_hash, _cassaforte=""):
        return False

    async def detta(chi, testo, *a, **k):
        DETTI.append((chi, testo))

    async def ai_moderatori(testo, *a, **k):
        ADMIN.append((testo, k.get("argomento", "")))

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = detta
    server.notifica_admin = ai_moderatori
    server.premia_distintivi = zitta
    server.premia_xp = zitta
    server.polso_ordini_admin = zitta
    server.verifica_utente = lambda *a, **k: UTENTE
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": admin}


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def esegui(fn, *args, corpo=None):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def semina():
    """Un venditore con InPost (cosi' la via punto c'e', e si prova che
    la conferma li' non entra) e tre annunci che si spediscono."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "spedizionieri,spedizioniere) "
                "VALUES(222,'Vende','neg22222',1,'|InPost|','InPost')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    ids = []
    for titolo, consegna in (("Cosa", "spedizione"), ("Altra", "spedizione"),
                             ("Terza", "entrambe")):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(222,?,'desc',30000,'Altro',"
            "'Torino (TO)','attivo',1,?,9,'sats','buono',4000)",
            (titolo, consegna))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    come(111)
    return ids


def a_indirizzo(aid, indirizzo=CASA, **extra):
    """L'acquisto verso un indirizzo. La conferma si passa esplicita:
    `indirizzo_confermato=True` e' la casella spuntata."""
    come(111)
    corpo = {"annuncio_id": aid, "quantita": 1, "consegna": "spedizione",
             "spedizione_via": "casa", "indirizzo": dict(indirizzo)}
    corpo.update(extra)
    return chiama(SRV.compra, corpo)


def riga(oid):
    con = SRV.db()
    r = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return r


def tocca(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET " + ", ".join(f"{k}=?" for k in campi)
                + " WHERE id=?", tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def recente(ts):
    return bool(ts) and abs(int(time.time()) - int(ts)) < 120


# ---------------------------------------------------------------
def prove_cassa():
    print("\n── ALLA CASSA: la casella spuntata si salva con l'ordine ──")
    a1, a2, a3 = semina()
    r = a_indirizzo(a1, indirizzo_confermato=True)
    o = riga(r["ordine_id"])
    prova("l'ordine nasce, verso un indirizzo", ("spedizione", 0, True),
          (o["consegna_scelta"], o["via_punto"], bool(o["indirizzo"])))
    prova("...e porta la DATA della conferma", True,
          recente(o["indirizzo_confermato_il"]))

    # NESSUNA VENDITA SI BLOCCA: la pagina rimasta aperta da prima
    prima = len(INVOICES)
    r = a_indirizzo(a2)
    o = riga(r["ordine_id"])
    prova("senza la casella (una pagina di prima) si compra lo stesso",
          True, bool(r.get("ordine_id")) and len(INVOICES) == prima + 1)
    prova("...e l'ordine dice la verita': nessuna conferma", 0,
          o["indirizzo_confermato_il"])

    # solo True, solo il gesto
    semina()
    con = SRV.db()
    aid = con.execute("SELECT id FROM annunci ORDER BY id").fetchone()[0]
    con.close()
    for finto in ("true", 1, "si", {"ok": True}):
        r = a_indirizzo(aid, indirizzo_confermato=finto)
        prova(f"{finto!r} non e' una casella spuntata", 0,
              riga(r["ordine_id"])["indirizzo_confermato_il"])
        tocca(r["ordine_id"], stato="annullato")


def prove_carrello_e_altre_vie():
    print("\n── IL CARRELLO, E LE VIE DOVE LA CONFERMA NON ENTRA ──")
    a1, a2, a3 = semina()
    come(111)
    r = chiama(SRV.compra, {
        "righe": [{"annuncio_id": a1, "quantita": 1},
                  {"annuncio_id": a2, "quantita": 1}],
        "consegna": "spedizione", "spedizione_via": "casa",
        "indirizzo": dict(CASA), "indirizzo_confermato": True})
    prova("dal carrello la conferma si salva uguale", True,
          recente(riga(r["ordine_id"])["indirizzo_confermato_il"]))
    r = chiama(SRV.compra, {
        "righe": [{"annuncio_id": a1, "quantita": 1},
                  {"annuncio_id": a2, "quantita": 1}],
        "consegna": "spedizione", "spedizione_via": "casa",
        "indirizzo": dict(ALTRA)})
    prova("...e senza casella il carrello nasce lo stesso, a zero", 0,
          riga(r["ordine_id"])["indirizzo_confermato_il"])
    # la via PUNTO non ha un indirizzo da confermare
    r = chiama(SRV.compra, {
        "annuncio_id": a1, "quantita": 1, "consegna": "spedizione",
        "spedizione_via": "punto", "tipo_punto": "locker",
        "punto_ritiro": "Locker InPost Via Verdi 3",
        "indirizzo_confermato": True})
    o = riga(r["ordine_id"])
    prova("verso un punto di ritiro la conferma non entra", (1, 0),
          (o["via_punto"], o["indirizzo_confermato_il"]))
    # e nemmeno il ritiro in zona
    r = chiama(SRV.compra, {"annuncio_id": a3, "quantita": 1,
                            "consegna": "ritiro",
                            "indirizzo_confermato": True})
    prova("...e sul ritiro in zona nemmeno", 0,
          riga(r["ordine_id"])["indirizzo_confermato_il"])


def prove_ripresa():
    print("\n── LA RIPRESA: la conferma segue l'indirizzo che si riscrive ──")
    a1, _, _ = semina()
    prima = len(INVOICES)
    r1 = a_indirizzo(a1)                       # primo tocco, senza casella
    r2 = a_indirizzo(a1, indirizzo_confermato=True)   # poi la spunta
    prova("il secondo tocco su «Paga» riprende lo STESSO ordine",
          (r1["ordine_id"], 1), (r2["ordine_id"], len(INVOICES) - prima))
    prova("...e la spunta arrivata dopo si salva", True,
          recente(riga(r1["ordine_id"])["indirizzo_confermato_il"]))
    r3 = a_indirizzo(a1, indirizzo=ALTRA)      # corregge, non rispunta
    prova("corretto l'indirizzo senza rispuntare: la conferma torna a "
          "zero (parlava di un altro indirizzo)",
          (r1["ordine_id"], 0),
          (r3["ordine_id"],
           riga(r1["ordine_id"])["indirizzo_confermato_il"]))


def prove_dall_ordine():
    print("\n── DAL CAMPO DENTRO L'ORDINE: la conferma si rinnova ──")
    a1, _, _ = semina()
    oid = a_indirizzo(a1, indirizzo_confermato=True)["ordine_id"]
    tocca(oid, stato="locked", indirizzo_confermato_il=1000)
    come(111)
    DETTI.clear()
    r = esegui(SRV.indica_indirizzo, oid, None, "", "",
               corpo={"indirizzo": dict(ALTRA),
                      "indirizzo_confermato": True})
    o = riga(oid)
    prova("corretto dall'ordine con la casella: la data e' quella di "
          "ADESSO, non quella della cassa", True,
          recente(o["indirizzo_confermato_il"]))
    prova("...e la risposta lo dice alla pagina", o["indirizzo_confermato_il"],
          r.get("indirizzo_confermato_il"))
    prova("...e la correzione si conta, come sempre", 1,
          o["indirizzo_correzioni"])
    prova("al venditore si dice «indirizzo di spedizione», mai «di casa»",
          (True, False),
          (len(DETTI) == 1 and DETTI[0][0] == 222
           and "aggiornato l'indirizzo di spedizione" in DETTI[0][1],
           "casa" in (DETTI[0][1] if DETTI else "")))
    prova("...e l'indirizzo nel messaggio NON c'e'", False,
          "Cavour" in (DETTI[0][1] if DETTI else ""))
    # una pagina di prima corregge senza la casella
    esegui(SRV.indica_indirizzo, oid, None, "", "",
           corpo={"indirizzo": dict(CASA)})
    prova("corretto da una pagina di prima (niente casella): torna a zero",
          0, riga(oid)["indirizzo_confermato_il"])
    # i rifiuti parlano col nome nuovo
    alza("un campo che manca si chiede col nome nuovo",
         lambda: esegui(SRV.indica_indirizzo, oid, None, "", "",
                        corpo={"indirizzo": dict(CASA, cap="")}),
         "Per la spedizione a un indirizzo serve anche")
    oid_p = chiama(SRV.compra, {
        "annuncio_id": a1, "quantita": 1, "consegna": "spedizione",
        "spedizione_via": "punto", "tipo_punto": "locker",
        "punto_ritiro": "Locker InPost Via Verdi 3"})["ordine_id"]
    tocca(oid_p, stato="locked")
    alza("...e su un ordine verso un punto il rifiuto pure",
         lambda: esegui(SRV.indica_indirizzo, oid_p, None, "", "",
                        corpo={"indirizzo": dict(CASA)}),
         "non è una spedizione a un indirizzo")


def nota_disputa(oid):
    """Apre la disputa e rende la nota che arriva ai moderatori."""
    ADMIN.clear()
    come(111)
    esegui(SRV.apri_disputa, oid, "", "")
    return " || ".join(t for t, arg in ADMIN if arg == "dispute")


def prove_disputa():
    print("\n── IN DISPUTA: cosa legge il moderatore ──")
    a1, a2, _ = semina()
    oid = a_indirizzo(a1, indirizzo_confermato=True)["ordine_id"]
    tocca(oid, stato="shipped", corriere="BRT", tracking="123")
    nota = nota_disputa(oid)
    prova("la nota arriva ai moderatori", True, bool(nota))
    prova("...col nome nuovo della via", (True, False),
          ("Spedizione a un INDIRIZZO" in nota, "a CASA" in nota))
    prova("...e il FATTO della conferma, con la data", True,
          "L'acquirente lo ha CONFERMATO il " in nota)
    prova("...e le parole che ha sottoscritto", True,
          "le spese di spedizione restano a mio carico" in nota)
    prova("...ma MAI l'indirizzo", (False, False),
          ("Garibaldi" in nota, "27100" in nota))

    oid2 = a_indirizzo(a2)["ordine_id"]          # senza casella
    tocca(oid2, stato="shipped", corriere="BRT", tracking="456")
    nota2 = nota_disputa(oid2)
    prova("senza conferma la nota lo dice, e dice perche' puo' mancare",
          (True, True),
          ("NESSUNA conferma dell'acquirente" in nota2,
           "non la chiedevano" in nota2))
    prova("...e non la inventa", False, "CONFERMATO" in nota2)

    come(999, admin=True)
    mio = {r["id"]: r for r in SRV.miei_ordini(0, "", "")}
    prova("nella sua lista l'admin trova la data della conferma", True,
          recente(mio.get(oid, {}).get("indirizzo_confermato_il")))
    prova("...e lo zero dell'ordine senza conferma", 0,
          mio.get(oid2, {}).get("indirizzo_confermato_il"))
    prova("...ma l'indirizzo non c'e', per nessuno dei due",
          (False, False),
          ("indirizzo" in mio.get(oid, {}), "indirizzo" in mio.get(oid2, {})))
    come(111)
    c = {r["id"]: r for r in SRV.miei_ordini(0, "", "")}
    prova("chi ha comprato riceve la sua data (la pagina la sa)", True,
          recente(c.get(oid, {}).get("indirizzo_confermato_il")))


def prove_scopa():
    print("\n── A ORDINE CHIUSO: l'indirizzo si cancella, la conferma no ──")
    a1, _, _ = semina()
    oid = a_indirizzo(a1, indirizzo_confermato=True)["ordine_id"]
    conf = riga(oid)["indirizzo_confermato_il"]
    # chiuso da tempo: la scopa lo deve prendere
    vecchio = int(time.time()) - 400 * 86400
    tocca(oid, stato="released", aggiornato=vecchio)
    SRV.pulisci_indirizzi()
    o = riga(oid)
    prova("la scopa ha cancellato l'indirizzo", ("", True),
          (o["indirizzo"], o["indirizzo_purgato_il"] > 0))
    prova("...e la conferma e' rimasta: e' un fatto, non un dato "
          "personale", conf, o["indirizzo_confermato_il"])


def prove_avvisi():
    print("\n── GLI AVVISI AL VENDITORE: «a un indirizzo», mai «a casa» ──")
    a1, _, _ = semina()
    oid = a_indirizzo(a1, indirizzo_confermato=True)["ordine_id"]
    DETTI.clear()
    asyncio.run(SRV._incassa_ordine(oid))
    al_venditore = " || ".join(t for chi, t in DETTI if chi == 222)
    prova("il «Hai venduto!» dice la via col nome nuovo", (True, False),
          ("spedizione a un indirizzo" in al_venditore,
           "spedizione a casa" in al_venditore
           or "a\ncasa" in al_venditore))
    prova("...e l'indirizzo nel messaggio non c'e'", False,
          "Garibaldi" in al_venditore)
    prova("l'ordine e' pagato e la conferma e' ancora li'", ("locked", True),
          (riga(oid)["stato"],
           recente(riga(oid)["indirizzo_confermato_il"])))


def main():
    db = avvio()
    print("=" * 66)
    print("COLLAUDO DELLA CONFERMA DELL'INDIRIZZO — db usa-e-getta")
    print("=" * 66)
    prove_cassa()
    prove_carrello_e_altre_vie()
    prove_ripresa()
    prove_dall_ordine()
    prove_disputa()
    prove_scopa()
    prove_avvisi()
    print("\n" + "=" * 66)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 66)
    try:
        os.remove(db)
    except OSError:
        pass
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
