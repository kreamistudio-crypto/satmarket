# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA PORTA DEL TIMER (ago 2026).

`prove.py` difende la FORMA — che il timbro si scriva, che la clausola
sia nella WHERE, che i giudici del client rispondano giusto. Quello che
non puo' fare e' far girare il GIRO INTERO: un ordine digitale vero che
un timer chiude, un moderatore che lo riapre, e i sats che tornano
indietro.

Questo script chiude quel buco. Fa partire il SERVER VERO su un
database usa-e-getta, con LNbits finto, e cammina la storia dall'inizio
alla fine:

  1. ordine digitale, il venditore consegna il codice, il compratore lo
     rivela;
  2. si retrodata la rivelazione di 25 ore e si fa girare l'orologio:
     l'ordine si chiude da solo in 'confirmed' — il venditore non ha un
     metodo d'incasso — la colonna porta il timbro, e il compratore
     riceve la sua unica notifica, quella con dentro la maniglia;
  3. il compratore prova ad aprire una disputa: 400. La porta non e'
     sua, e non lo diventa;
  4. il moderatore decide 'rimborso': l'ordine chiude a 'refunded' e il
     bilancio si rilegge dal database.

E LA REGRESSIONE CHE CONTA, che e' l'altra meta' della decisione: un
ordine identico CONFERMATO A MANO resta 'confirmed' col timbro a zero,
e per il moderatore non e' decidibile — chi ha confermato di persona
resta chiuso, e nessuno puo' riaprire da solo un affare concluso.

Piu' la ronda del libro mastro, che su tutto questo deve TACERE.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato, quindi lo script gira senza rete e senza chiavi.

USO:  python collaudo_porta_timer.py
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
DETTO = []          # (destinatario, testo) di ogni notifica


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
    """Il config finto PRIMA di importare server. ORE_CONFERMA_DIGITALE
    resta 24 come in produzione: il tempo lo si fa passare retrodatando
    l'ordine, non accorciando la leva — cosi' si prova il numero vero."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-porta-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME con un valore non vuoto
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    # le due leve dei rami FISICI: qui non c'entrano (il digitale ha le
    # sue finestre, e restano armate col disarmo) ma l'import di server
    # le pretende
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None):
        return {"payment_hash": f"hash{int(time.time()*1000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    async def paga_finto(bolt11, atteso_sats):
        return SRV.PAGATO

    async def invoice_da_address(addr, sats):
        return f"lnbc{sats}rimborso"

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.paga_venditore = paga_finto
    server.invoice_da_ln_address = invoice_da_address
    # awaitable: nel server queste si aspettano, e uno stub che torna
    # None fa esplodere il ramo invece di tacere
    async def zitto(*a, **k):
        return None

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


def semina():
    """Un venditore SENZA metodo d'incasso — e' il caso del buco — e un
    compratore che invece ce l'ha, cosi' il rimborso puo' arrivare in
    fondo."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(222,'Vende','neg22222',1,'')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,"
                "'compra@wallet.tld')")
    ids = []
    for n in range(2):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'un codice',50000,'Altro','','attivo',1,"
            "'digitale',5,'sats','nuovo')", (f"Codice {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_digitale(annuncio_id):
    """Compra, incassa e porta l'ordine fino alla RIVELAZIONE, coi
    percorsi veri: il pagamento e' l'unico pezzo simulato (LNbits non
    si chiama), e si scrive lo stesso stato che scriverebbe
    _incassa_ordine."""
    come(111)
    c = chiama(SRV.compra, None, corpo={"annuncio_id": annuncio_id,
                                        "consegna": "digitale"})
    oid = c["ordine_id"]
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (oid,))
    con.commit()
    con.close()

    come(222)                                   # il venditore consegna
    chiama(SRV.consegna_digitale, oid, None,
           corpo={"contenuto": "ABCD-1234-EFGH"})
    come(111)                                   # e il compratore rivela
    chiama(SRV.leggi_contenuto_digitale, oid)
    return oid


def main():
    print("=" * 58)
    print("  LA PORTA DEL TIMER — il giro vero")
    print("=" * 58)
    avvio()
    a1, a2 = semina()

    # ---- 1) l'ordine chiuso dal timer ----------------------------
    print("\n[il timer chiude l'affare]")
    oid = ordine_digitale(a1)
    o = riga(oid)
    prova("il codice rivelato porta a 'delivered'", "delivered", o["stato"])
    prova("...e la rivelazione e' registrata", True, o["consegnato"] > 0)

    # 25 ore fa: la finestra vera e' ORE_CONFERMA_DIGITALE (24), e non
    # si accorcia la leva — si fa passare il tempo
    con = SRV.db()
    con.execute("UPDATE ordini SET consegnato=? WHERE id=?",
                (int(time.time()) - 25 * 3600, oid))
    con.commit()
    con.close()

    DETTO.clear()
    asyncio.run(SRV.controlla_scadenze())
    o = riga(oid)
    prova("il timer chiude l'ordine in 'confirmed'", "confirmed", o["stato"])
    prova("...perche' il venditore non ha un metodo d'incasso", "",
          o["invoice_venditore"])
    prova("...e la colonna porta il timbro", True, o["sbloccato_auto_il"] > 0)
    prova("...senza inventare nessuna disputa", 0, o["disputata"])

    al_compratore = [t for c, t in DETTO if c == 111]
    prova("il compratore riceve UNA notifica", 1, len(al_compratore))
    testo = "".join(al_compratore)
    prova("...che gli dice dove scrivere", True, "moderatori" in testo)
    prova("...col numero dell'ordine", True, f"#{oid}" in testo)
    prova("...e che i sats non sono usciti", True,
          "non sono ancora usciti" in testo)

    # ---- 2) la porta non e' del compratore -----------------------
    print("\n[la porta non e' sua]")
    come(111)
    try:
        chiama(SRV.apri_disputa, oid)
        prova("il compratore non puo' aprire una disputa", "400", "passata")
    except Exception as e:
        prova("il compratore non puo' aprire una disputa", 400,
              getattr(e, "status_code", None))

    # ---- 3) ...ma il moderatore c'e' -----------------------------
    print("\n[il moderatore decide]")
    come(999, admin=True)
    DETTO.clear()
    r = chiama(SRV.risolvi_disputa, oid, None, corpo={"esito": "rimborso"})
    o = riga(oid)
    prova("il moderatore rimborsa il compratore", "refunded", o["stato"])
    prova("...e la riapertura ha timbrato la disputa", 1, o["disputata"])
    prova("...con l'esito riportato dalla funzione", True, r.get("ok"))
    prova("il compratore viene avvisato", True,
          any(c == 111 for c, _ in DETTO))

    # ---- 4) LA REGRESSIONE: chi ha confermato di persona ---------
    print("\n[chi ha confermato di persona resta chiuso]")
    oid2 = ordine_digitale(a2)
    come(111)
    chiama(SRV.conferma_ricezione, oid2)
    o2 = riga(oid2)
    prova("la conferma a mano porta anch'essa in 'confirmed'",
          "confirmed", o2["stato"])
    prova("...ma la colonna resta a zero", 0, o2["sbloccato_auto_il"])

    prima = riga(oid2)
    come(999, admin=True)
    try:
        chiama(SRV.risolvi_disputa, oid2, None, corpo={"esito": "rimborso"})
        prova("...e per il moderatore NON e' decidibile", "400", "passata")
    except Exception as e:
        prova("...e per il moderatore NON e' decidibile", 400,
              getattr(e, "status_code", None))
    prova("...e l'ordine non si e' mosso di un byte", prima, riga(oid2))

    # ---- 5) e il libro mastro tace -------------------------------
    print("\n[la ronda]")
    allarmi = []

    async def raccogli(*a, **k):
        allarmi.append(a)

    vecchia = SRV.notifica
    SRV.notifica = raccogli
    asyncio.run(SRV.controlla_libro_mastro())
    SRV.notifica = vecchia
    prova("il libro mastro non ha niente da dire", [], allarmi)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
