# -*- coding: utf-8 -*-
"""
IL FEEDBACK SI APRE ALLA CONFERMA, NON ALL'INCASSO (ago 2026).

Il compratore conferma la ricezione; se il venditore non ha un metodo
d'incasso il pagamento non parte e l'ordine finisce in 'confirmed'. Per
chi ha comprato l'affare E' FINITO — ha ricevuto l'oggetto e ha detto
che va bene — ma il feedback era vietato, e cio' che mancava non
dipendeva da lui: dipendeva dal wallet di un altro.

`prove.py` difende la FORMA (il giudice sui suoi casi, la parita' col
client, la PROVA REGINA che lega il giudice alla porta del moderatore).
Quello che non puo' fare e' far girare il GIRO INTERO. Qui si cammina:

  1. ordine fisico pagato e spedito; il compratore conferma → l'ordine
     va in 'confirmed' perche' il venditore non ha modo di incassare;
  2. il compratore VOTA — ed e' il caso per cui esiste il cantiere;
  3. vota anche il VENDITORE, e i due si vedono a vicenda;
  4. il venditore mette il Lightning address → 'released': il feedback
     lasciato in 'confirmed' SOPRAVVIVE, rating e n_recensori non si
     muovono, e un secondo voto trova la UNIQUE;
  5. i quattro rifiuti: confirmed dal TIMER, confirmed DISPUTATO,
     'refund' e 'locked';
  6. la ronda del libro mastro TACE su tutto questo.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato: gira senza rete e senza chiavi.

USO:  python collaudo_feedback_confermato.py
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
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-feedback-"),
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

    async def invoice_finta(sats, memo, expiry=None):
        return {"payment_hash": f"hash{int(time.time()*1000000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    async def paga_finto(bolt11, atteso_sats):
        return SRV.PAGATO

    async def invoice_da_address(addr, sats):
        return f"lnbc{sats}address"

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.paga_venditore = paga_finto
    server.invoice_da_ln_address = invoice_da_address

    async def zitto(*a, **k):
        return None

    server.polso_ordini_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.notifica_admin = zitto
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": admin}


def chiama(fn, *args, corpo=None):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def errore(fn, *args, corpo=None):
    """Il codice e il messaggio di un rifiuto, o None se e' passato."""
    try:
        chiama(fn, *args, corpo=corpo)
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def riga(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return dict(o)


def utente(tg_id):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?", (tg_id,)).fetchone()
    con.close()
    return dict(u)


def voti(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    r = [dict(x) for x in con.execute(
        "SELECT da_tg_id, per_tg_id, voto FROM feedback WHERE ordine_id=? "
        "ORDER BY da_tg_id", (oid,))]
    con.close()
    return r


def scrivi(oid, **campi):
    """Porta l'ordine in uno stato che qui non si raggiunge camminando
    (il confirmed dal timer, quello disputato): e' un collaudo, e il
    percorso che li produce ha gia' il suo — collaudo_porta_timer."""
    con = SRV.db()
    con.execute("UPDATE ordini SET "
                + ", ".join(f"{k}=?" for k in campi) + " WHERE id=?",
                tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def semina():
    """Un venditore SENZA metodo d'incasso: e' il caso del cantiere."""
    con = SRV.db()
    for t in ("feedback", "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("UPDATE utenti SET rating=0, n_feedback=0, n_recensori=0")
    for tg, nome, neg in ((222, "Vende", "neg22222"),
                          (111, "Compra", "neg11111")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, neg))
    ids = []
    for n in range(6):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa vera',50000,'Altro','Pavia (PV)',"
            "'attivo',1,'spedizione',9,'sats','nuovo')", (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_confermato(annuncio_id):
    """Il giro vero fino a 'confirmed': compra, paga, spedisce, e il
    compratore conferma — col venditore che non puo' incassare."""
    come(111)
    c = chiama(SRV.compra, None, corpo={"annuncio_id": annuncio_id,
                                        "consegna": "spedizione",
                                        "indirizzo": {"nome": "Mario Rossi",
                                                      "via": "Via Roma 1",
                                                      "cap": "27100",
                                                      "citta": "Pavia",
                                                      "prov": "PV",
                                                      "tel": "3330000000"}})
    oid = c["ordine_id"]
    scrivi(oid, stato="locked")
    come(222)
    chiama(SRV.segna_spedito, oid, None,
           corpo={"corriere": "Poste Italiane", "tracking": "AB123456789IT"})
    come(111)
    esito = chiama(SRV.conferma_ricezione, oid)
    # LA RETE CHE IMPEDISCE UN BANCO BUGIARDO: se il venditore ha un
    # metodo d'incasso l'ordine vola dritto a 'released', e i casi che
    # si volevano provare su 'confirmed' passerebbero per la ragione
    # sbagliata — dicendo verde. E' successo scrivendo questo file.
    if riga(oid)["stato"] != "confirmed":
        raise SystemExit(f"⚠️  l'ordine {oid} e' in "
                         f"'{riga(oid)['stato']}' e non in 'confirmed': "
                         f"il venditore ha un metodo d'incasso?")
    return oid, esito


def main():
    print("=" * 60)
    print("  IL FEEDBACK SI APRE ALLA CONFERMA")
    print("=" * 60)
    avvio()
    ann = semina()

    # ---- 1. Il giro vero fino a 'confirmed' ------------------------
    print("\n[1. il compratore conferma, il venditore non puo' incassare]")
    oid, esito = ordine_confermato(ann[0])
    prova("l'ordine finisce in 'confirmed'", "confirmed", riga(oid)["stato"])
    prova("...e lo dice anche la risposta", False, esito["ok"])
    r = riga(oid)
    prova("nessun timer c'entra: il timbro e' a zero", 0,
          r["sbloccato_auto_il"])
    prova("e non e' una disputa", 0, r["disputata"])

    # ---- 2. Il compratore vota. E' il cantiere. --------------------
    print("\n[2. il compratore vota da 'confirmed']")
    come(111)
    d = chiama(SRV.lascia_feedback, oid, None,
               corpo={"voto": 5, "commento": "Tutto perfetto, grazie!"})
    prova("il voto passa", True, d["ok"])
    prova("...ed e' finito nella tabella",
          [{"da_tg_id": 111, "per_tg_id": 222, "voto": 5}], voti(oid))
    prova("il venditore ha rating anche senza aver incassato", 5.0,
          utente(222)["rating"])
    prova("...e un recensore", 1, utente(222)["n_recensori"])
    prova("l'ordine non si e' mosso di un byte", "confirmed",
          riga(oid)["stato"])

    # ---- 3. Vota anche il venditore --------------------------------
    print("\n[3. e vota anche il venditore]")
    come(222)
    chiama(SRV.lascia_feedback, oid, None,
           corpo={"voto": 4, "commento": "Pagamento immediato"})
    prova("i due si sono votati a vicenda",
          [(111, 222, 5), (222, 111, 4)],
          [(v["da_tg_id"], v["per_tg_id"], v["voto"]) for v in voti(oid)])
    prova("il compratore ha il suo rating", 4.0, utente(111)["rating"])
    # la UNIQUE e' il giudice dei doppioni, e resta tale
    e = errore(SRV.lascia_feedback, oid, None,
               corpo={"voto": 1, "commento": ""})
    prova("il secondo voto trova la UNIQUE",
          (400, "Hai già lasciato il feedback per questo ordine"), e)

    # ---- 4. Il venditore incassa: il voto sopravvive ---------------
    print("\n[4. il venditore mette il wallet e incassa]")
    con = SRV.db()
    con.execute("UPDATE utenti SET ln_address=? WHERE tg_id=222",
                ("vende@wallet.tld",))
    con.commit()
    con.close()
    asyncio.run(SRV._sblocca_sats(oid))
    prova("l'ordine chiude a 'released'", "released", riga(oid)["stato"])
    prova("IL FEEDBACK SOPRAVVIVE al cambio di stato", 2, len(voti(oid)))
    prova("...e il rating non si e' mosso", (5.0, 1),
          (utente(222)["rating"], utente(222)["n_recensori"]))

    # ---- 5. I quattro rifiuti --------------------------------------
    print("\n[5. chi resta fuori, e resta fuori per un motivo]")
    # il venditore torna senza wallet, o gli ordini qui sotto
    # volerebbero a 'released' e proverebbero un'altra cosa
    con = SRV.db()
    con.execute("UPDATE utenti SET ln_address='' WHERE tg_id=222")
    con.commit()
    con.close()
    come(111)

    oid_t, _ = ordine_confermato(ann[1])
    scrivi(oid_t, sbloccato_auto_il=int(time.time()))
    e = errore(SRV.lascia_feedback, oid_t, None, corpo={"voto": 5})
    prova("confirmed chiuso dal TIMER: rifiutato",
          (400, "Il feedback si lascia a affare concluso"), e)

    oid_d, _ = ordine_confermato(ann[2])
    scrivi(oid_d, disputata=1)
    e = errore(SRV.lascia_feedback, oid_d, None, corpo={"voto": 5})
    prova("confirmed da DISPUTA decisa: rifiutato",
          (400, "Il feedback si lascia a affare concluso"), e)

    oid_r, _ = ordine_confermato(ann[3])
    scrivi(oid_r, stato="refund", disputata=1)
    e = errore(SRV.lascia_feedback, oid_r, None, corpo={"voto": 5})
    prova("'refund': rifiutato (e' il gemello, ma nasce disputato)",
          (400, "Il feedback si lascia a affare concluso"), e)

    come(111)
    c = chiama(SRV.compra, None, corpo={"annuncio_id": ann[4],
                                        "consegna": "spedizione",
                                        "indirizzo": {"nome": "Mario Rossi",
                                                      "via": "Via Roma 1",
                                                      "cap": "27100",
                                                      "citta": "Pavia",
                                                      "prov": "PV",
                                                      "tel": "3330000000"}})
    scrivi(c["ordine_id"], stato="locked")
    e = errore(SRV.lascia_feedback, c["ordine_id"], None, corpo={"voto": 5})
    prova("'locked': l'affare non e' finito, rifiutato",
          (400, "Il feedback si lascia a affare concluso"), e)

    # l'estraneo prende il 403 di sempre, e su un ordine che ammette
    # il voto: cosi' il rifiuto e' quello della PROPRIETA', non dello
    # stato — le due guardie restano distinte
    come(333)
    e = errore(SRV.lascia_feedback, oid, None, corpo={"voto": 5})
    prova("l'estraneo prende il 403, non il 400 dello stato",
          (403, "Operazione non permessa"), e)

    prova("nessuno dei rifiuti ha scritto una riga", 0,
          sum(len(voti(x)) for x in (oid_t, oid_d, oid_r, c["ordine_id"])))

    # ---- 6. La ronda del libro mastro tace -------------------------
    print("\n[6. e il libro mastro non ha niente da dire]")
    DETTO.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    guai = [t for _, t in DETTO if "\U0001f9ca" in t or "libro" in t.lower()]
    prova("la ronda tace", [], guai)

    print("\n" + "=" * 60)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 60)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
