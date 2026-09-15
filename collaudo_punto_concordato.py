# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL PUNTO CONCORDATO (ago 2026).

`prove.py` difende la FORMA — che il silenzio sia nella WHERE, che
l'ancora non sia `aggiornato`, che il contatore stia nei due MAX della
coda. Quello che non puo' fare e' camminare il GIRO INTERO: un ordine
vero via punto, il venditore che segnala, il compratore che accetta una
proposta col gesto che ha gia', e il pacco che finalmente parte.

Questo script chiude quel buco. Fa partire il SERVER VERO su un
database usa-e-getta, con LNbits finto, e cammina la storia:

  1. ordine via punto: il compratore indica un locker InPost;
  2. il venditore obietta («non e' della mia rete») e propone DUE
     punti; il compratore riceve la notifica, e dentro c'e' SOLO
     l'etichetta del motivo — mai il testo del venditore;
  3. `segna_spedito` passa lo stesso: obiettare non e' un lucchetto —
     se si sono chiariti in chat il pacco parte, e l'obiezione si
     chiude con la spedizione (su un ordine gemello);
  4. il compratore ACCETTA una proposta, che e' il gesto di sempre
     (`indica_punto_ritiro` col testo proposto dentro): l'obiezione si
     chiude, `punto_obiezioni` RESTA a 1 — e' la memoria del
     moderatore — e da li' `segna_spedito` passa.

E I RIFIUTI, che sono la meta' che conta: il compratore che prova a
obiettare, l'estraneo, l'ordine senza punto, l'ordine gia' spedito, il
motivo inventato, la nota troppo lunga, le proposte oltre il tetto.
L'anti-oracolo si prova sul DATABASE VERO: «non e' tuo» e «non esiste»
devono rispondere IDENTICO.

Piu' i due promemoria, che sono la promessa del cantiere:
`sollecita_venditori_fermi` TACE su un ordine con l'obiezione aperta e
torna a squillare appena il compratore risponde; e
`sollecita_punti_obiettati` bussa a CHI COMPRA. E la ronda del libro
mastro, che su tutto questo deve TACERE.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato, quindi lo script gira senza rete e senza chiavi.

USO:  python collaudo_punto_concordato.py
"""

import asyncio
import json
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
        print(f"  [KO] {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server. Le leve restano
    quelle di produzione: il tempo lo si fa passare RETRODATANDO
    l'ordine, non accorciando la finestra — cosi' si prova il numero
    vero, e il conto del 🧊 e' quello che gira in piazza."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("[!] server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-punto-"),
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
    """Un venditore che spedisce con InPost — la rete e' quel che rende
    vero il caso: chi compra indica un punto Poste e il pacco non parte
    — e un compratore. Tre annunci: uno per il giro pieno, uno per la
    spedizione che chiude l'obiezione, uno per i promemoria."""
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
    for n in range(4):
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


def ordine_al_punto(annuncio_id, punto="Locker Poste Via Verdi 3"):
    """Compra via punto e porta l'ordine a 'locked' coi percorsi veri:
    il pagamento e' l'unico pezzo simulato."""
    come(111)
    c = chiama(SRV.compra, None, corpo={
        "annuncio_id": annuncio_id, "consegna": "spedizione",
        "spedizione_via": "punto", "punto_ritiro": punto,
        "tipo_punto": "locker"})
    oid = c["ordine_id"]
    tocca(oid, stato="locked")
    return oid


def main():
    print("=" * 60)
    print("  IL PUNTO CONCORDATO — il giro vero")
    print("=" * 60)
    avvio()
    a1, a2, a3, a4 = semina()

    # ---- 1) l'ordine nasce via punto ------------------------------
    print("\n[l'ordine via punto]")
    oid = ordine_al_punto(a1)
    o = riga(oid)
    prova("nasce sulla via punto", 1, o["via_punto"])
    prova("...col punto che ha scritto chi compra",
          "Locker Poste Via Verdi 3", o["punto_ritiro"])
    prova("...e nessuna obiezione aperta", 0, o["punto_obiettato_il"])

    # ---- 2) il venditore obietta ----------------------------------
    print("\n[il venditore segnala che il punto non va bene]")
    DETTO.clear()
    come(222)
    r = chiama(SRV.obietta_punto, oid, None, corpo={
        "motivo": "rete", "nota": "Io spedisco solo con InPost",
        "proposte": ["Locker InPost Via Roma 1",
                     "Punto InPost Tabaccheria Bar Sport",
                     "Locker InPost Via Roma 1",      # doppione: cade
                     ""]})                            # vuota: cade
    o = riga(oid)
    prova("il motivo va in colonna", "rete", o["punto_obiezione"])
    prova("...la nota pure", "Io spedisco solo con InPost",
          o["punto_obiezione_nota"])
    prova("...il timbro si scrive", True, o["punto_obiettato_il"] > 0)
    prova("...il contatore sale a 1", 1, o["punto_obiezioni"])
    prova("le proposte perdono doppioni e vuote", 2,
          len(json.loads(o["punto_proposte"])))
    prova("...e sono quelle che tornano al client", 2, len(r["proposte"]))
    prova("l'ordine NON cambia stato", "locked", o["stato"])

    dest = [d for d, _ in DETTO]
    prova("la notifica va a chi compra", [111], dest)
    testo = DETTO[0][1] if DETTO else ""
    prova("...e dentro c'e' l'etichetta NOSTRA del motivo",
          True, "Non è della mia rete" in testo)
    prova("...MAI il testo del venditore", False,
          "Io spedisco solo con InPost" in testo)
    prova("...ne' le proposte", False, "Via Roma 1" in testo)

    # ---- 3) i rifiuti ---------------------------------------------
    print("\n[i rifiuti]")
    come(111)
    prova("il compratore non puo' obiettare", 400,
          rifiuto(SRV.obietta_punto, oid, None,
                  corpo={"motivo": "rete"})[0])
    come(333)
    est = rifiuto(SRV.obietta_punto, oid, None, corpo={"motivo": "rete"})
    ines = rifiuto(SRV.obietta_punto, 99999, None, corpo={"motivo": "rete"})
    prova("l'estraneo e l'ordine inesistente rispondono IDENTICO",
          est, ines)
    prova("...e il codice e' il 400 dei fratelli, mai un 404", 400, est[0])

    come(222)
    prova("il motivo inventato si rifiuta", 400,
          rifiuto(SRV.obietta_punto, oid, None,
                  corpo={"motivo": "perche-si"})[0])
    lunga = rifiuto(SRV.obietta_punto, oid, None,
                    corpo={"motivo": "altro", "nota": "x" * 400})
    prova("la nota troppo lunga si RIFIUTA (non si tronca)", 400, lunga[0])
    prova("...e l'ordine resta com'era",
          "Io spedisco solo con InPost", riga(oid)["punto_obiezione_nota"])

    # il tetto delle proposte LIMA (non rifiuta): una segnalazione non
    # deve fallire per un client che ne manda cinque
    r5 = chiama(SRV.obietta_punto, oid, None, corpo={
        "motivo": "inesistente",
        "proposte": [f"Locker InPost {i}" for i in range(5)]})
    prova("cinque proposte si limano a tre", 3, len(r5["proposte"]))
    prova("...e il contatore ricorda la seconda segnalazione", 2,
          riga(oid)["punto_obiezioni"])

    # ---- 4) il silenzio del promemoria al venditore ---------------
    print("\n[i due promemoria: la palla e' di chi compra]")
    # 40 giorni fa: ben oltre PROMEMORIA_SPEDIZIONE_GIORNI
    vecchio = int(time.time()) - 40 * 86400
    tocca(oid, creato=vecchio)
    DETTO.clear()
    asyncio.run(SRV.sollecita_venditori_fermi())
    prova("il venditore NON viene rimproverato per la merce mai partita",
          [], DETTO)

    # e appena il compratore risponde, il promemoria torna a squillare
    con = SRV.db()
    con.execute("UPDATE ordini SET punto_obiettato_il=0 WHERE id=?", (oid,))
    con.commit()
    con.close()
    DETTO.clear()
    asyncio.run(SRV.sollecita_venditori_fermi())
    prova("...e torna a squillare quando l'obiezione si chiude",
          True, any(d == 222 for d, _ in DETTO))
    tocca(oid, punto_obiettato_il=vecchio, solleciti_venditore=0,
          sollecito_venditore_il=0)

    # il promemoria NUOVO bussa a chi compra
    DETTO.clear()
    asyncio.run(SRV.sollecita_punti_obiettati())
    prova("il promemoria del punto bussa a CHI COMPRA",
          [111], [d for d, _ in DETTO])
    o = riga(oid)
    prova("...e il suo contatore sale", 1, o["solleciti_obiezione"])
    prova("...col timbro suo, mai quello del venditore", True,
          o["sollecito_obiezione_il"] > 0)

    # al tetto: il 🧊 ai moderatori, e poi silenzio
    ADMIN.clear()
    for _ in range(SRV.PROMEMORIA_CONFERMA_MAX + 2):
        tocca(oid, sollecito_obiezione_il=0, punto_obiettato_il=vecchio)
        asyncio.run(SRV.sollecita_punti_obiettati())
    prova("al tetto parte UN solo ghiaccio ai moderatori", 1, len(ADMIN))
    prova("...e poi si tace per sempre", True,
          riga(oid)["solleciti_obiezione"] > SRV.PROMEMORIA_CONFERMA_MAX)

    # ---- 5) il compratore accetta una proposta --------------------
    print("\n[il compratore accetta una proposta]")
    tocca(oid, punto_obiettato_il=vecchio, punto_obiezione="rete",
          punto_proposte=json.dumps(["Locker InPost Via Roma 1"]))
    come(111)
    DETTO.clear()
    chiama(SRV.indica_punto_ritiro, oid, None,
           corpo={"punto_ritiro": "Locker InPost Via Roma 1",
                  "tipo_punto": "locker"})
    o = riga(oid)
    prova("il punto e' quello proposto", "Locker InPost Via Roma 1",
          o["punto_ritiro"])
    prova("l'obiezione si chiude", 0, o["punto_obiettato_il"])
    prova("...motivo, nota e proposte si svuotano",
          ("", "", ""), (o["punto_obiezione"], o["punto_obiezione_nota"],
                         o["punto_proposte"]))
    prova("...ma il CONTATORE resta (la memoria del moderatore)",
          2, o["punto_obiezioni"])
    prova("il venditore riceve la risposta", True,
          any(d == 222 for d, _ in DETTO))

    DETTO.clear()
    asyncio.run(SRV.sollecita_punti_obiettati())
    prova("e il promemoria del punto smette da solo", [], DETTO)

    # ---- 6) da li' il pacco parte ---------------------------------
    print("\n[il pacco parte]")
    come(222)
    chiama(SRV.segna_spedito, oid, None,
           corpo={"corriere": "InPost", "tracking": "123456789012345678"})
    prova("segna_spedito passa", "shipped", riga(oid)["stato"])

    # ---- 7) obiettare non e' un lucchetto -------------------------
    print("\n[obiettare non blocca la spedizione]")
    o2 = ordine_al_punto(a2)
    come(222)
    chiama(SRV.obietta_punto, o2, None, corpo={"motivo": "inesistente"})
    prova("l'obiezione e' aperta", True, riga(o2)["punto_obiettato_il"] > 0)
    chiama(SRV.segna_spedito, o2, None,
           corpo={"corriere": "InPost", "tracking": "987654321098765432"})
    r2 = riga(o2)
    prova("...ma il venditore puo' spedire lo stesso (chiariti in chat)",
          "shipped", r2["stato"])
    prova("...e la spedizione CHIUDE l'obiezione", (0, ""),
          (r2["punto_obiettato_il"], r2["punto_obiezione"]))
    prova("...senza cancellare il contatore", 1, r2["punto_obiezioni"])

    come(222)
    prova("su un ordine gia' spedito non si obietta piu'", 400,
          rifiuto(SRV.obietta_punto, o2, None,
                  corpo={"motivo": "rete"})[0])

    # ---- 8) l'ordine senza punto ----------------------------------
    print("\n[l'ordine nato senza punto]")
    o3 = ordine_al_punto(a3)
    tocca(o3, punto_ritiro="")
    come(222)
    codice, msg = rifiuto(SRV.obietta_punto, o3, None,
                          corpo={"motivo": "rete"})
    prova("non si obietta su un punto che non c'e'", 400, codice)
    prova("...e il messaggio manda alla strada giusta", True,
          "non ha ancora indicato" in msg)

    # ---- 9) la ronda del libro mastro -----------------------------
    print("\n[il libro mastro]")
    ADMIN.clear()
    SRV.timbro_scrivi(SRV.TIMBRO_LIBRO_MASTRO, "")
    asyncio.run(SRV.controlla_libro_mastro())
    prova("sul sano la ronda TACE", [], ADMIN)

    o4 = ordine_al_punto(a4)
    tocca(o4, punto_obiettato_il=int(time.time()), punto_obiezione="")
    ADMIN.clear()
    SRV.timbro_scrivi(SRV.TIMBRO_LIBRO_MASTRO, "")
    asyncio.run(SRV.controlla_libro_mastro())
    prova("...e sulla riga rotta parla, col nome del controllo", True,
          bool(ADMIN) and "obiezione sul punto fuori contratto" in ADMIN[0])
    prova("...e col suo id", True,
          bool(ADMIN) and f"<code>{o4}</code>" in ADMIN[0])

    print("\n" + "=" * 60)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 60)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
