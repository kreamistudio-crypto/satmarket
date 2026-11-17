# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «SPEDISCI ENTRO IL…» (17 nov 2026, cantiere spedisci-entro).

Lo spunto viene dalle card di vendita di un altro mercatino: «articolo
venduto», «spedisci entro il…» col link alla guida, «ordine spedito».
Da noi il giudice della data e' `spedire_entro`, e la data e' il
GIORNO DEL PRIMO PROMEMORIA: questo script cammina il giro col server
vero e guarda che le tre cose dicano lo stesso giorno.

  1. il pagamento timbra `pagato_il` (una volta sola) e lascia stare
     `creato`;
  2. «Hai venduto» dice «Spedisci entro <giorno>», nomina la guida e
     porta il tasto che apre l'ordine — una notifica sola;
  3. `/api/orders` da' la stessa data a chi vende e a chi compra;
  4. il promemoria al venditore cade QUEL giorno, anche quando la
     fattura e' nata giorni prima del pagamento (on-chain, riacciuffo):
     prima della data tace, dopo suona;
  5. gli ordini senza timbro tornano a `creato`, come ieri;
  6. il ritiro in zona non promette niente e il testo resta quello di
     ieri; dopo la spedizione la data sparisce; con la leva a 0 tace
     tutto e «Hai venduto» torna parola per parola quello di prima.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. LNbits non viene mai chiamato.

USO:  python collaudo_spedisci_entro.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
DETTO = []          # (destinatario, testo, bottone) di ogni notifica


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  [ok] {nome}")
    else:
        FALLITE += 1
        print(f"  [NO] {nome}\n       atteso: {atteso!r}\n       avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server (la liturgia di
    collaudo_email_corriere). Le leve restano quelle di serie: il tempo
    si fa passare RETRODATANDO l'ordine."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("[!] server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-entro-"),
                      "usa-e-getta.db")
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
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        return {"payment_hash": f"hash{int(time.time()*1000000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    async def notifica_finta(chi, testo, bottone=None, *a, **k):
        DETTO.append((chi, testo, bottone))

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.notifica_admin = zitto
    server.polso_ordini_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": admin}


def chiama(fn, *args, corpo=None):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def riga(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return dict(o)


def tocca(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET "
                + ", ".join(f"{k}=?" for k in campi)
                + " WHERE id=?", tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address,spedizionieri,spedizioniere) "
                "VALUES(222,'Vende','neg22222',1,'','|InPost|','InPost')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,"
                "'compra@wallet.tld')")
    ids = []
    for n in range(8):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(222,?,'una cosa vera',50000,'Altro',"
            "'Pavia (PV)','attivo',1,?,9,'sats','nuovo',1000)",
            (f"Cosa {n}", "ritiro" if n == 7 else "spedizione"))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_a_casa(annuncio_id):
    """L'ordine NASCE e resta 'creato': il pagamento lo fa
    `_incassa_ordine`, che e' la porta che timbra."""
    come(111)
    c = chiama(SRV.compra, None, corpo={
        "annuncio_id": annuncio_id, "consegna": "spedizione",
        "spedizione_via": "casa",
        "indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                      "cap": "27100", "citta": "Pavia",
                      "provincia": "PV"}})
    return c["ordine_id"]


def paga(oid):
    DETTO.clear()
    asyncio.run(SRV._incassa_ordine(oid))
    return [(t, b) for chi, t, b in DETTO if chi == 222]


def vista(oid, chi):
    come(chi)
    for r in SRV.miei_ordini(0, "", ""):
        if r["id"] == oid:
            return r
    return None


def main():
    G = 86400
    tmp = avvio()
    print(f"\n  database usa-e-getta: {tmp}\n")
    ann = semina()
    giorni = SRV.PROMEMORIA_SPEDIZIONE_GIORNI
    prova("la leva di serie e' quella del promemoria (5 giorni)", 5, giorni)

    # ============================================================
    print("\n[1] IL PAGAMENTO TIMBRA, E LA FATTURA RESTA DOV'ERA")
    # ============================================================
    # La fattura nata tre giorni prima del pagamento: il caso on-chain
    # e il saldo riacciuffato, dove `creato` non dice quando sono
    # arrivati i sats.
    o1 = ordine_a_casa(ann[0])
    nato = int(time.time()) - 3 * G
    tocca(o1, creato=nato)
    prima = int(time.time())
    detti = paga(o1)
    r1 = riga(o1)
    prova("l'ordine e' pagato", "locked", r1["stato"])
    prova("...col timbro del pagamento di adesso", True,
          prima <= r1["pagato_il"] <= int(time.time()))
    prova("...e `creato` non si muove", nato, r1["creato"])
    entro = r1["pagato_il"] + giorni * G
    # il secondo giro dell'incasso non ritimbra (il CAS lo ferma)
    timbro = r1["pagato_il"]
    tocca(o1, pagato_il=timbro - 7)
    asyncio.run(SRV._incassa_ordine(o1))
    prova("...e un secondo incasso non lo riscrive", timbro - 7,
          riga(o1)["pagato_il"])
    tocca(o1, pagato_il=timbro)

    # ============================================================
    print("\n[2] «HAI VENDUTO» DICE IL GIORNO, LA GUIDA E IL TASTO")
    # ============================================================
    prova("al venditore parte UNA notifica", 1, len(detti))
    testo, bottone = detti[0] if detti else ("", None)
    giorno = SRV.giorno_entro(entro)
    prova("...che dice «Spedisci entro <giorno>»", True,
          f"Spedisci entro {giorno}" in testo)
    prova("...dove il giorno e' quello del primo promemoria", True,
          SRV.spedire_entro("locked", "spedizione", timbro, nato) == entro)
    prova("...nomina la guida nell'ordine", True,
          "«Come si spedisce?»" in testo)
    prova("...e porta il tasto che apre l'ordine",
          (SRV.BOTTONE_ORDINE_VENDUTO, f"{SRV.URL_PUBBLICO}/?ordine={o1}"),
          bottone)
    prova("...il giorno si legge da persona («domenica 22 novembre»)",
          "domenica 22 novembre",
          SRV.giorno_entro(int(time.mktime((2026, 11, 22, 12, 0, 0, 0, 0, -1)))))

    # ============================================================
    print("\n[3] LA STESSA DATA A CHI VENDE E A CHI COMPRA")
    # ============================================================
    v, c = vista(o1, 222), vista(o1, 111)
    prova("chi vende la legge nell'ordine", entro,
          v and v.get("spedire_entro"))
    prova("...e chi compra la stessa", entro, c and c.get("spedire_entro"))
    prova("...col timbro del pagamento accanto", timbro,
          c and c.get("pagato_il"))

    # ============================================================
    print("\n[4] IL PROMEMORIA CADE QUEL GIORNO")
    # ============================================================
    # Si porta indietro il pagamento: un minuto PRIMA della data il
    # promemoria tace — con l'ancora di ieri (`creato`, otto giorni fa)
    # avrebbe gia' suonato —, un minuto DOPO suona.
    adesso = int(time.time())
    tocca(o1, pagato_il=adesso - giorni * G + 60, creato=adesso - 8 * G)
    DETTO.clear()
    asyncio.run(SRV.sollecita_venditori_fermi())
    prova("un minuto prima della data il promemoria tace", [],
          [t for chi, t, b in DETTO if chi == 222])
    prova("...e la data che legge chi vende non e' ancora passata", True,
          vista(o1, 222)["spedire_entro"] > int(time.time()))
    tocca(o1, pagato_il=adesso - giorni * G - 60)
    DETTO.clear()
    asyncio.run(SRV.sollecita_venditori_fermi())
    prova("un minuto dopo suona", True,
          any("aspetta te" in t for chi, t, b in DETTO if chi == 222))
    prova("...e la data era davvero passata", True,
          vista(o1, 222)["spedire_entro"] < int(time.time()))

    # ============================================================
    print("\n[5] GLI ORDINI SENZA TIMBRO TORNANO A `creato`")
    # ============================================================
    o2 = ordine_a_casa(ann[1])
    paga(o2)
    tocca(o2, pagato_il=0, creato=adesso - 2 * G)
    prova("senza timbro la data e' `creato` piu' i giorni",
          adesso - 2 * G + giorni * G, vista(o2, 222)["spedire_entro"])
    tocca(o2, creato=adesso - giorni * G - 60, sollecito_venditore_il=0,
          solleciti_venditore=0)
    DETTO.clear()
    asyncio.run(SRV.sollecita_venditori_fermi())
    prova("...e il promemoria suona come ieri", True,
          any("aspetta te" in t for chi, t, b in DETTO if chi == 222))

    # ============================================================
    print("\n[6] DOVE LA DATA NON C'E'")
    # ============================================================
    come(111)
    o3 = chiama(SRV.compra, None, corpo={
        "annuncio_id": ann[7], "consegna": "ritiro"})["ordine_id"]
    detti = paga(o3)
    t3, b3 = detti[0] if detti else ("", "?")
    prova("il ritiro in zona non promette nessun giorno", (False, None),
          ("Spedisci entro" in t3, b3))
    prova("...il testo resta quello di ieri", True,
          "Spedisci l'oggetto e segna l'ordine come spedito" in t3)
    prova("...e nell'ordine nessuna data", 0, vista(o3, 222)["spedire_entro"])

    o4 = ordine_a_casa(ann[2])
    paga(o4)
    come(222)
    chiama(SRV.segna_spedito, o4, None,
           corpo={"corriere": "InPost", "tracking": "616555400308780213"})
    prova("dopo la spedizione la data sparisce", ("shipped", 0),
          (riga(o4)["stato"], vista(o4, 222)["spedire_entro"]))

    SRV.PROMEMORIA_SPEDIZIONE_GIORNI = 0
    o5 = ordine_a_casa(ann[3])
    detti = paga(o5)
    t5, b5 = detti[0] if detti else ("", "?")
    prova("con la leva a 0 la data tace", (False, None, 0),
          ("Spedisci entro" in t5, b5, vista(o5, 222)["spedire_entro"]))
    prova("...e «Hai venduto» torna quello di prima", True,
          "Spedisci l'oggetto e segna l'ordine come spedito nella "
          "Mini App. 📦" in t5)
    prova("...ma il pagamento si timbra lo stesso", True,
          riga(o5)["pagato_il"] > 0)
    SRV.PROMEMORIA_SPEDIZIONE_GIORNI = giorni

    print("\n" + "=" * 60)
    print(f"  {PASSATE} verdi, {FALLITE} rosse")
    print("=" * 60)
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
