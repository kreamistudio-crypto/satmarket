# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'EMAIL PER IL CORRIERE (ago 2026, tappa B).

Spedendo a un locker il venditore puo' mettere i recapiti del
COMPRATORE come destinatario — la busta diretta, cantiere 45 — e da li'
il codice glielo manda il corriere. La META' che mancava era procurarsi
quel recapito senza la chat: `prove.py` difende la FORMA e fa girare i
due endpoint su un database di cartone, questo script CAMMINA IL GIRO
INTERO col server vero, dal pagamento alla scopa.

  1. il compratore la lascia sull'ordine appena pagato, e in colonna
     arriva CIFRATA — mai in chiaro;
  2. il venditore la legge dalla sua rotta e la mette sull'etichetta,
     poi spedisce con la spunta della busta diretta;
  3. dopo la spedizione il campo e' CHIUSO: l'etichetta e' stampata, e
     un'email nuova non ci arriverebbe mai;
  4. il moderatore in disputa riceve il FATTO con la data e MAI il
     valore — la regola dell'indirizzo di casa;
  5. la SCOPA la cancella con l'indirizzo, alle stesse due velocita';
  6. l'anti-oracolo sul database VERO: estraneo, ordine di un altro e
     ordine inesistente rispondono IDENTICO;
  7. il caso normale non cambia di un byte: chi non la lascia riceve il
     codice dal venditore, come sempre;
  8. la ronda del libro mastro che TACE sul sano e trova la riga rotta
     col suo id.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. LNbits non viene mai chiamato: gira senza rete
e senza chiavi.

USO:  python collaudo_email_corriere.py
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
ADMIN = []          # i testi arrivati ai moderatori


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
    collaudo_punto_concordato). Le leve restano quelle di produzione:
    il tempo si fa passare RETRODATANDO l'ordine."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("[!] server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-diretta-"),
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
    # LA CHIAVE C'E': senza, l'email si scriverebbe 'plain:' e
    # il caso che conta — «in colonna arriva CIFRATA» — non si
    # potrebbe provare affatto
    cfg.CHIAVE_CONTENUTI_DIGITALI = "collaudo-usa-e-getta"
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

    async def admin_finto(testo, *a, **k):
        ADMIN.append(testo)

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.notifica_admin = admin_finto
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


def rifiuto(fn, *args, corpo=None):
    """Torna (codice, messaggio) invece di far esplodere il collaudo."""
    try:
        chiama(fn, *args, corpo=corpo)
        return 0, ""
    except SRV.HTTPException as e:
        return e.status_code, str(e.detail)


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
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(333,'Estraneo','neg33333',1,'')")
    ids = []
    for n in range(6):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(222,?,'una cosa vera',50000,'Altro',"
            "'Pavia (PV)','attivo',1,'spedizione',9,'sats','nuovo',1000)",
            (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_al_punto(annuncio_id, punto="Locker InPost Via Verdi 3"):
    come(111)
    c = chiama(SRV.compra, None, corpo={
        "annuncio_id": annuncio_id, "consegna": "spedizione",
        "spedizione_via": "punto", "punto_ritiro": punto,
        "tipo_punto": "locker"})
    oid = c["ordine_id"]
    tocca(oid, stato="locked")
    return oid


def ordine_a_casa(annuncio_id):
    come(111)
    c = chiama(SRV.compra, None, corpo={
        "annuncio_id": annuncio_id, "consegna": "spedizione",
        "spedizione_via": "casa",
        "indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                      "cap": "27100", "citta": "Pavia",
                      "provincia": "PV"}})
    oid = c["ordine_id"]
    tocca(oid, stato="locked")
    return oid


def scrivi_email(oid, mail, chi=111):
    come(chi)
    return chiama(SRV.indica_email_corriere, oid, None,
                  corpo={"email_corriere": mail})


def leggi_email(oid, chi=111, admin=False):
    come(chi, admin)
    return chiama(SRV.leggi_email_corriere, oid)


def main():
    G = 86400
    ora = int(time.time())
    tmp = avvio()
    print(f"\n  database usa-e-getta: {tmp}\n")
    ann = semina()

    # ============================================================
    print("\n[1] IL COMPRATORE LA LASCIA, E IN COLONNA E' CIFRATA")
    # ============================================================
    o_mail = ordine_al_punto(ann[0])
    DETTO.clear()
    r = scrivi_email(o_mail, "  Mario.Rossi@Esempio.IT  ")
    prova("il compratore la scrive", True, bool(r.get("ok")))
    col = riga(o_mail)["email_corriere"]
    prova("...e in colonna NON c'e' in chiaro", False,
          "Mario.Rossi@Esempio.IT" in col)
    prova("...perche' e' cifrata col trasporto dei contenuti", True,
          col.startswith("f2:"))
    prova("...col timbro del PRIMO", True,
          riga(o_mail)["email_corriere_il"] > 0)
    msg = " || ".join(t for chi, t in DETTO if chi == 222)
    prova("il venditore lo viene a sapere", True,
          "email per il corriere" in msg)
    prova("...ma nella notifica il VALORE non c'e' MAI", False,
          "Mario.Rossi@Esempio.IT" in msg or "esempio.it" in msg.lower())

    # ============================================================
    print("\n[2] IL VENDITORE LA LEGGE E LA METTE SULL'ETICHETTA")
    # ============================================================
    d = leggi_email(o_mail, 222)
    prova("il venditore la legge dalla sua rotta",
          "Mario.Rossi@Esempio.IT", d.get("email"))
    prova("...e il compratore pure", "Mario.Rossi@Esempio.IT",
          leggi_email(o_mail, 111).get("email"))
    dump = [tuple(x) for x in SRV.db().execute("SELECT * FROM ordini")]
    leggi_email(o_mail, 222); leggi_email(o_mail, 111)
    prova("...e la lettura non scrive NIENTE", dump,
          [tuple(x) for x in SRV.db().execute("SELECT * FROM ordini")])

    # ============================================================
    print("\n[3] LA CORREZIONE FINCHE' NON SI SPEDISCE, POI CHIUSO")
    # ============================================================
    DETTO.clear()
    scrivi_email(o_mail, "Mario.Rossi@Esempio.IT")
    prova("riscriverla identica non e' un cambio: niente avviso",
          (0, 0), (len([1 for c, _ in DETTO if c == 222]),
                   riga(o_mail)["email_corriere_correzioni"]))
    primo = riga(o_mail)["email_corriere_il"]
    scrivi_email(o_mail, "nuova@esempio.it")
    prova("la correzione si conta", 1,
          riga(o_mail)["email_corriere_correzioni"])
    prova("...e il timbro del PRIMO non si muove", primo,
          riga(o_mail)["email_corriere_il"])
    come(222)
    chiama(SRV.segna_spedito, o_mail, None,
           corpo={"corriere": "InPost", "tracking": "616555400308780213",
                  "busta_diretta": True})
    prova("spedito con la busta diretta", True,
          riga(o_mail)["busta_diretta_il"] > 0)
    cod, _ = rifiuto(SRV.indica_email_corriere, o_mail, None,
                     corpo={"email_corriere": "tardi@esempio.it"})
    prova("dopo la spedizione il campo e' CHIUSO", 400, cod)
    prova("...e il valore di prima e' ancora quello",
          "nuova@esempio.it", leggi_email(o_mail, 111).get("email"))

    # ============================================================
    print("\n[4] IL MODERATORE: IL FATTO, MAI IL VALORE")
    # ============================================================
    DETTO.clear()
    come(111)
    chiama(SRV.apri_disputa, o_mail)
    # la nota ai moderatori viaggia con notifica() verso ADMIN_IDS
    nota = " || ".join(t for chi, t in DETTO if chi == 999)
    prova("in disputa la nota dice CHE c'era un'email", True,
          "aveva lasciato un'email per il corriere" in nota)
    prova("...e quando", True, "lasciata il" in nota)
    prova("...e che e' stata corretta una volta", True,
          "corretta 1 volta" in nota)
    # ⚠️ il caso si scrive in COPPIA: da solo, «il valore non c'e'»
    # sarebbe verde anche su una nota VUOTA — cioe' passerebbe per la
    # ragione sbagliata (la lezione di _pare_recapito)
    prova("...ma il VALORE non c'e'", (True, False),
          (bool(nota), "nuova@esempio.it" in nota))
    come(999, admin=True)
    cod2, _ = rifiuto(SRV.leggi_email_corriere, o_mail)
    prova("e il moderatore non la legge nemmeno dalla rotta", 400, cod2)

    # ============================================================
    print("\n[5] L'ANTI-ORACOLO SUL DATABASE VERO")
    # ============================================================
    o_altro = ordine_al_punto(ann[1])
    scrivi_email(o_altro, "altro@esempio.it")
    come(333)
    e1 = rifiuto(SRV.leggi_email_corriere, o_altro)
    e2 = rifiuto(SRV.leggi_email_corriere, 999999)
    prova("l'estraneo e l'ordine inesistente: la STESSA risposta",
          e1, e2)
    prova("...ed e' quella opaca dei fratelli",
          (400, "Operazione non permessa"), e1)
    s1 = rifiuto(SRV.indica_email_corriere, o_altro, None,
                 corpo={"email_corriere": "x@y.it"})
    s2 = rifiuto(SRV.indica_email_corriere, 999999, None,
                 corpo={"email_corriere": "x@y.it"})
    prova("in scrittura idem", s1, s2)
    come(222)
    s3 = rifiuto(SRV.indica_email_corriere, o_altro, None,
                 corpo={"email_corriere": "x@y.it"})
    prova("...e il venditore non la scrive", 400, s3[0])

    # ============================================================
    print("\n[6] LA SPEDIZIONE A CASA NON LA VUOLE")
    # ============================================================
    o_casa = ordine_a_casa(ann[2])
    cod, msg = rifiuto(SRV.indica_email_corriere, o_casa, None,
                       corpo={"email_corriere": "casa@esempio.it"})
    prova("niente email sulla spedizione a casa", 400, cod)
    prova("...e il motivo lo dice", True, "punto di ritiro" in msg)

    # ============================================================
    print("\n[7] IL CASO NORMALE NON CAMBIA DI UN BYTE")
    # ============================================================
    o_senza = ordine_al_punto(ann[3])
    prima = riga(o_senza)
    prova("chi non la lascia ha le colonne a zero",
          ("", 0, 0, 0),
          (prima["email_corriere"], prima["email_corriere_il"],
           prima["email_corriere_correzioni"],
           prima["email_corriere_purgata_il"]))
    cod, _ = rifiuto(SRV.leggi_email_corriere, o_senza)
    prova("...e la lettura dice 404, non un valore", 404, cod)
    come(222)
    chiama(SRV.segna_spedito, o_senza, None,
           corpo={"corriere": "InPost", "tracking": "616555400308780214"})
    prova("...e la spedizione funziona come sempre", "shipped",
          riga(o_senza)["stato"])

    # ============================================================
    print("\n[8] LA SCOPA: SPARISCE CON L'INDIRIZZO")
    # ============================================================
    # o_veloce: chiuso dalla CONFERMA del compratore -> corsia veloce
    o_veloce = ordine_al_punto(ann[4])
    scrivi_email(o_veloce, "veloce@esempio.it")
    tocca(o_veloce, stato="released", disputata=0, aggiornato=ora)
    # o_lento: chiuso da una DISPUTA ieri -> vale la finestra
    o_lento = ordine_al_punto(ann[5])
    scrivi_email(o_lento, "lento@esempio.it")
    tocca(o_lento, stato="released", disputata=1, aggiornato=ora - G)
    # o_vecchio: chiuso da un pezzo -> la finestra e' passata
    tocca(o_altro, stato="refunded",
          aggiornato=ora - (SRV.GIORNI_INDIRIZZO + 2) * G)

    SRV.pulisci_indirizzi()
    prova("la conferma la cancella SUBITO",
          ("", True), (riga(o_veloce)["email_corriere"],
                       riga(o_veloce)["email_corriere_purgata_il"] > 0))
    prova("...ma il timbro del PRIMO resta (e' il fatto)", True,
          riga(o_veloce)["email_corriere_il"] > 0)
    prova("chiuso da una disputa ieri: la finestra lo tiene", True,
          bool(riga(o_lento)["email_corriere"]))
    prova("...e passata la finestra se ne va", "",
          riga(o_altro)["email_corriere"])
    prova("l'ordine VIVO non si tocca", True,
          bool(riga(o_mail)["email_corriere"]))
    # l'ancora dei promemoria non si muove per una manutenzione
    agg = riga(o_lento)["aggiornato"]
    SRV.pulisci_indirizzi()
    prova("la scopa e' idempotente", agg, riga(o_lento)["aggiornato"])
    cod, msg = rifiuto(SRV.leggi_email_corriere, o_veloce)
    prova("il purgato lo dice a chi lo cerca", (404, True),
          (cod, "cancellata" in msg))

    # ============================================================
    print("\n[9] LA RONDA DEL LIBRO MASTRO")
    # ============================================================
    ADMIN.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    fuori = " || ".join(ADMIN)
    prova("sul sano la ronda TACE sull'email", False,
          "email per il corriere" in fuori)
    # e la riga rotta la trova col suo id: piena su un ordine che
    # non e' via punto
    tocca(o_senza, email_corriere="f2:x", email_corriere_il=1,
          via_punto=0)
    ADMIN.clear()
    SRV.timbro_scrivi("libro_mastro", "")
    asyncio.run(SRV.controlla_libro_mastro())
    fuori = " || ".join(ADMIN)
    prova("...e la riga rotta la trova", True,
          "email per il corriere fuori contratto" in fuori)
    prova("...col suo id", True, f"#{o_senza}" in fuori
          or str(o_senza) in fuori)

    print("\n" + "=" * 60)
    print(f"  {PASSATE} verdi, {FALLITE} rosse")
    print("=" * 60)
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
