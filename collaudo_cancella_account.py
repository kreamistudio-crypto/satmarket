# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CANCELLAZIONE DELL'ACCOUNT (1 nov 2026, cantiere
cancella-account).

Il caso intero col server VERO, per HTTP con la TestClient, su un
database usa-e-getta: un venditore e un compratore con un ordine, una
recensione per parte, un annuncio venduto e uno ancora in vetrina, un
preferito, un mancato P2P, una busta in chat. Poi:
  1. a leva spenta le rotte non esistono (404) e /api/me non la offre;
  2. con l'ordine in corso il foglio dice cosa manca e il gesto si
     ferma (409, con le righe);
  3. a ordine chiuso, senza la parola il gesto non parte (400);
  4. con la parola l'account se ne va — e la PROVA CHE NON RESTA NIENTE
     e' la sentinella larga: si passano TUTTE le colonne di TUTTE le
     tabelle dei due database cercando il numero vecchio. Una tabella
     dimenticata in `CANCELLA_TOGLI`/`CANCELLA_ANONIMIZZA` la fa rossa
     da sola, anche quella che nascera' domani;
  5. l'altra parte vede ancora il suo ordine, con «Utente cancellato»;
  6. chi rientra parte da zero, ma il mancato P2P torna con lui;
  7. un moderatore non si cancella.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, nessuna rete, nessun LNbits.

USO:  python collaudo_cancella_account.py
"""

import json
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

PASSATE = FALLITE = 0
SRV = None

# numeri strani apposta: la sentinella larga li cerca in OGNI colonna, e un
# prezzo o un contatore non possono valere per caso cosi'
VENDE = 7654321987
COMPRA = 6543219876
ALTRO = 5432198765


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
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-cancella-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    # I segreti col setattr e mai come `NOME = "valore"` (lo scanner
    # della CI non distingue una chiave finta da una vera)
    for k, v in (("BOT_TOKEN", "0:collaudo"),
                 ("ANTHROPIC_API_KEY", "INCOLLA_QUI"),
                 ("LNBITS_URL", "http://127.0.0.1:1"),
                 ("LNBITS_INVOICE_KEY", "INCOLLA_QUI"),
                 ("LNBITS_ADMIN_KEY", "INCOLLA_QUI"),
                 ("ADMIN_IDS", [999]),
                 ("MODALITA_COLLAUDO", True),
                 ("COMMISSIONE_PERCENTO", 0),
                 ("ORE_CONFERMA", 72),
                 ("GIORNI_AUTO_SBLOCCO", 10),
                 ("MODELLO_RICERCA", "claude-haiku-4-5-20251001"),
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    os.chdir(QUI)
    import server
    return server


def h(tg, nome="Prova"):
    return {"X-Tg-Init-Data": f"collaudo:{tg}:{nome}"}


def semina(srv):
    """Il mondo di partenza, scritto dritto nel database: le rotte vere
    di un acquisto vorrebbero LNbits, e qui si collauda l'uscita, non
    l'entrata."""
    adesso = int(time.time())
    con = srv.db()
    for tg, nome in ((VENDE, "Vendo"), (COMPRA, "Compro"), (ALTRO, "Altro")):
        srv._upsert_da_telegram(con, tg, nome, nome.lower())
    con.execute("UPDATE utenti SET ln_address='vendo@esempio.it', "
                "xp=40 WHERE tg_id=?", (VENDE,))
    # l'annuncio VENDUTO (con l'ordine) e quello ANCORA IN VETRINA
    cur = con.execute(
        "INSERT INTO annunci(venditore_id, titolo, descrizione, categoria, "
        "prezzo_sats, zona, foto, stato, creato) VALUES(?,?,?,?,?,?,?,?,?)",
        (VENDE, "Bici rossa", "Casa mia in via Roma 1", "Sport", 50000,
         "Torino", json.dumps(["a1_0.jpg"]), "venduto", adesso))
    venduto = cur.lastrowid
    cur = con.execute(
        "INSERT INTO annunci(venditore_id, titolo, descrizione, categoria, "
        "prezzo_sats, zona, foto, stato, creato) VALUES(?,?,?,?,?,?,?,?,?)",
        (VENDE, "Lampada", "Ancora qui", "Casa", 9000, "Torino",
         json.dumps(["a2_0.jpg"]), "attivo", adesso))
    in_vetrina = cur.lastrowid
    cur = con.execute(
        "INSERT INTO ordini(annuncio_id, compratore_id, venditore_id, "
        "prezzo_sats, stato, payment_hash, indirizzo, busta_nome, "
        "creato, aggiornato) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (venduto, COMPRA, VENDE, 50000, "shipped", "ab" * 32,
         "Via dei Mille 3, Torino", "Mario Rossi", adesso, adesso))
    ordine = cur.lastrowid
    # una recensione per parte (si scrivono a ordine concluso: qui il
    # mondo e' gia' fatto, l'ordine si chiude piu' sotto)
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, "
                "commento, creato) VALUES(?,?,?,?,?,?)",
                (ordine, COMPRA, VENDE, 5, "Ottimo venditore", adesso))
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, "
                "commento, creato) VALUES(?,?,?,?,?,?)",
                (ordine, VENDE, COMPRA, 4, "Pagamento puntuale", adesso))
    con.execute("INSERT INTO preferiti(tg_id, annuncio_id, creato) "
                "VALUES(?,?,?)", (COMPRA, in_vetrina, adesso))
    con.execute("INSERT INTO preferiti(tg_id, annuncio_id, creato) "
                "VALUES(?,?,?)", (VENDE, venduto, adesso))
    # LA SUA VITA ATTORNO AGLI ALTRI, una riga per tabella: la sentinella
    # larga trova solo cio' che e' stato seminato, quindi si semina largo
    # (un preferito sul pezzo di un ALTRO, chi segue, cosa cerca, dove
    # ritira, il carrello, i punti, la chiave P2P, uno scambio P2P chiuso,
    # l'invito, l'annotazione del moderatore, un'offerta, un codice sconto)
    cur = con.execute(
        "INSERT INTO annunci(venditore_id, titolo, descrizione, categoria, "
        "prezzo_sats, zona, foto, stato, creato) VALUES(?,?,?,?,?,?,?,?,?)",
        (ALTRO, "Libro", "Di un altro", "Libri", 3000, "Roma", "[]",
         "attivo", adesso))
    altrui = cur.lastrowid
    for sql, par in (
            ("INSERT INTO preferiti(tg_id, annuncio_id, creato) VALUES(?,?,?)",
             (VENDE, altrui, adesso)),
            ("INSERT INTO venditori_seguiti(tg_id, venditore_id, creato) "
             "VALUES(?,?,?)", (VENDE, ALTRO, adesso)),
            ("INSERT INTO venditori_seguiti(tg_id, venditore_id, creato) "
             "VALUES(?,?,?)", (ALTRO, VENDE, adesso)),
            ("INSERT INTO avvisi_ricerca(tg_id, parole, creato) VALUES(?,?,?)",
             (VENDE, "bici", adesso)),
            ("INSERT INTO punti_ritiro(tg_id, rete, tipo, punto, creato) "
             "VALUES(?,?,?,?,?)", (VENDE, "inpost", "locker", "TO123", adesso)),
            ("INSERT INTO carrello_salvato(tg_id, venditore_id, righe, "
             "aggiornato) VALUES(?,?,?,?)", (VENDE, ALTRO, "[]", adesso)),
            ("INSERT INTO carrello_salvato(tg_id, venditore_id, righe, "
             "aggiornato) VALUES(?,?,?,?)", (COMPRA, VENDE, "[]", adesso)),
            ("INSERT INTO xp_eventi(tg_id, tipo, punti, riferimento, creato) "
             "VALUES(?,?,?,?,?)", (VENDE, "vendita", 40, "o:1", adesso)),
            ("INSERT INTO badge_utente(tg_id, badge_id, ottenuto_il) "
             "VALUES(?,?,?)", (VENDE, "primo", adesso)),
            ("INSERT INTO chiavi_p2p(pubkey, tg_id, creato) VALUES(?,?,?)",
             ("cd" * 32, VENDE, adesso)),
            ("INSERT INTO p2p_ordini(ordine, tg_id, creato, stato, preso_da) "
             "VALUES(?,?,?,?,?)", ("ord-due", ALTRO, adesso, "success", VENDE)),
            ("INSERT INTO p2p_scambi(ordine, compratore, venditore) "
             "VALUES(?,?,?)", ("ord-due", VENDE, ALTRO)),
            ("INSERT INTO inviti(invitato, invitante, creato) VALUES(?,?,?)",
             (VENDE, ALTRO, adesso)),
            ("INSERT INTO inviti(invitato, invitante, creato) VALUES(?,?,?)",
             (COMPRA, VENDE, adesso)),
            ("INSERT INTO account_insieme(chi, altro, cosa, quando) "
             "VALUES(?,?,?,?)", (VENDE, ALTRO, "compra", adesso)),
            ("INSERT INTO offerte(annuncio_id, compratore_id, venditore_id, "
             "importo_sats, stato, creato, aggiornato) VALUES(?,?,?,?,?,?,?)",
             (altrui, VENDE, ALTRO, 2000, "proposta", adesso, adesso)),
            ("INSERT INTO codici_sconto(venditore_id, codice, percento, "
             "attivo, creato) VALUES(?,?,?,?,?)",
             (VENDE, "BICI10", 10, 1, adesso))):
        con.execute(sql, par)
    con.execute("INSERT INTO sessioni(token_hash, tg_id, creato, scade) "
                "VALUES(?,?,?,?)", ("f" * 64, VENDE, adesso, adesso + 3600))
    con.execute("INSERT INTO viste_annuncio(annuncio_id, identita, vista) "
                "VALUES(?,?,?)", (in_vetrina, f"tg:{VENDE}", adesso))
    # il P2P: un mancato (la penalita' che resta) e un completato
    con.execute("INSERT INTO p2p_esiti(tg_id, ordine, giro, esito, ruolo, "
                "quando) VALUES(?,?,?,?,?,?)",
                (VENDE, "ord-uno", 0, "mancato", "compra", adesso - 60))
    con.execute("INSERT INTO p2p_esiti(tg_id, ordine, giro, esito, ruolo, "
                "quando) VALUES(?,?,?,?,?,?)",
                (VENDE, "ord-due", 0, "completato", "vende", adesso - 30))
    con.commit()
    con.close()
    cc = srv.db_chat()
    cc.execute("INSERT INTO buste(ordine, giro, da, tipo, busta, quando) "
               "VALUES(?,?,?,?,?,?)", ("ord-due", 0, VENDE, "chat", "x", adesso))
    cc.execute("INSERT INTO letture(ordine, giro, tg_id) VALUES(?,?,?)",
               ("ord-due", 0, VENDE))
    cc.commit()
    cc.close()
    return ordine, venduto, in_vetrina


def dove_resta(srv, numero: int) -> list:
    """LA SENTINELLA LARGA: ogni (tabella.colonna) dei due database in
    cui compare ancora `numero` — come intero, o dentro un testo
    («tg:123»). Vuota = non e' rimasto niente."""
    trovati = []
    for apri in (srv.db, srv.db_chat):
        con = apri()
        try:
            tabelle = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%'")]
            for t in tabelle:
                for col in [r[1] for r in con.execute(f"PRAGMA table_info({t})")]:
                    n = con.execute(
                        f"SELECT COUNT(*) FROM {t} WHERE {col}=? OR "
                        f"CAST({col} AS TEXT) LIKE ?",
                        (numero, f"%{numero}%")).fetchone()[0]
                    if n:
                        trovati.append(f"{t}.{col}")
        finally:
            con.close()
    return trovati


def main():
    global SRV
    SRV = avvio()
    from fastapi.testclient import TestClient
    import contextlib

    # SENZA L'AVVIO DEL SERVER (2 nov 2026, promozione rossa): `with
    # TestClient(app)` fa girare anche l'avvio vero, coi compiti di
    # sfondo, e uno di loro chiede il cambio a CoinGecko — la gabbia
    # della CI l'ha fermato (DNS api.coingecko.com). Gli altri collaudi
    # usano la TestClient senza `with`: qui lo stesso, tenendo i blocchi.
    def cliente():
        return contextlib.nullcontext(TestClient(SRV.app))

    print("\n[1. a leva spenta non esiste]")
    with cliente() as c:
        prova("la leva nasce spenta", False, SRV.ACCOUNT_CANCELLABILE)
        prova("GET 404", 404, c.get("/api/me/cancella-account",
                                    headers=h(VENDE)).status_code)
        prova("POST 404", 404, c.post("/api/me/cancella-account",
                                      headers=h(VENDE),
                                      json={"conferma": "CANCELLA"}).status_code)
        prova("/api/me non la offre", False,
              c.get("/api/me", headers=h(VENDE)).json().get("account_cancellabile"))

    SRV.ACCOUNT_CANCELLABILE = True
    ordine, venduto, in_vetrina = semina(SRV)
    with cliente() as c:
        prova("/api/me la offre a leva accesa", True,
              c.get("/api/me", headers=h(VENDE)).json().get("account_cancellabile"))

        print("\n[2. con un ordine in corso non si cancella]")
        r = c.get("/api/me/cancella-account", headers=h(VENDE)).json()
        prova("il foglio dice l'ordine che manca", True,
              any(f"#{ordine}" in x for x in r["impegni"]))
        prova("...e la parola da scrivere", "CANCELLA", r["parola"])
        prova("...e cosa si perde (un annuncio in vetrina, 40 punti)",
              (1, 40, 1), (r["perdi"]["annunci"], r["perdi"]["xp"],
                           r["perdi"]["recensioni"]))
        r = c.post("/api/me/cancella-account", headers=h(VENDE),
                   json={"conferma": "CANCELLA"})
        prova("il gesto si ferma: 409", 409, r.status_code)
        prova("...con le righe di cio' che manca", True,
              bool(r.json()["detail"]["impegni"]))
        prova("...e non ha toccato niente", True,
              bool(dove_resta(SRV, VENDE)))

        # l'ordine si chiude (rilasciato a chi vende)
        con = SRV.db()
        con.execute("UPDATE ordini SET stato='released' WHERE id=?", (ordine,))
        con.commit()
        con.close()

        print("\n[3. senza la parola non parte]")
        prova("foglio libero", [], c.get("/api/me/cancella-account",
                                         headers=h(VENDE)).json()["impegni"])
        prova("parola sbagliata: 400", 400,
              c.post("/api/me/cancella-account", headers=h(VENDE),
                     json={"conferma": "cancel"}).status_code)
        prova("parola assente: 400", 400,
              c.post("/api/me/cancella-account", headers=h(VENDE),
                     json={}).status_code)

        print("\n[4. con la parola se ne va, e non resta niente]")
        r = c.post("/api/me/cancella-account", headers=h(VENDE),
                   json={"conferma": "cancella"})
        prova("cancellato (la parola vale anche minuscola)", 200, r.status_code)
        prova("SENTINELLA LARGA: il numero vecchio non c'e' in nessuna colonna",
              [], dove_resta(SRV, VENDE))
        con = SRV.db()
        fantasma = con.execute("SELECT fantasma FROM account_cancellati"
                               ).fetchone()[0]
        prova("il fantasma vive in [2^52, 2^53)", True, SRV.e_fantasma(fantasma))
        u = con.execute("SELECT nome, username, ln_address FROM utenti "
                        "WHERE tg_id=?", (fantasma,)).fetchone()
        prova("la riga del fantasma dice «Utente cancellato»",
              ("Utente cancellato", "", ""), tuple(u))
        imp = con.execute("SELECT impronta FROM account_cancellati").fetchone()[0]
        prova("l'impronta e' quella lenta del numero", SRV.impronta_account(VENDE), imp)
        prova("...e non contiene il numero", False, str(VENDE) in imp)
        o = con.execute("SELECT venditore_id, compratore_id, prezzo_sats, "
                        "payment_hash, stato FROM ordini WHERE id=?",
                        (ordine,)).fetchone()
        prova("l'ordine resta, con cifra, hash e stato, e porta il fantasma",
              (fantasma, COMPRA, 50000, "ab" * 32, "released"), tuple(o))
        a = con.execute("SELECT stato, descrizione, foto FROM annunci WHERE id=?",
                        (in_vetrina,)).fetchone()
        prova("l'annuncio in vetrina e' rimosso, senza testo ne' foto",
              ("rimosso", "", ""), tuple(a))
        a = con.execute("SELECT stato, descrizione, foto FROM annunci WHERE id=?",
                        (venduto,)).fetchone()
        prova("quello venduto tiene la foto (la ricevuta di chi ha comprato)",
              ("rimosso", "", json.dumps(["a1_0.jpg"])), tuple(a))
        prova("la recensione RICEVUTA se n'e' andata", 0,
              con.execute("SELECT COUNT(*) FROM feedback WHERE commento="
                          "'Ottimo venditore'").fetchone()[0])
        prova("quella SCRITTA resta, col fantasma", (fantasma, COMPRA),
              tuple(con.execute("SELECT da_tg_id, per_tg_id FROM feedback "
                                "WHERE commento='Pagamento puntuale'").fetchone()))
        prova("il preferito di un altro sul suo annuncio se n'e' andato", 0,
              con.execute("SELECT COUNT(*) FROM preferiti WHERE tg_id=?",
                          (COMPRA,)).fetchone()[0])
        prova("le penalita' P2P stanno col fantasma", 2,
              con.execute("SELECT COUNT(*) FROM p2p_esiti WHERE tg_id=?",
                          (fantasma,)).fetchone()[0])
        prova("l'indirizzo di chi ha comprato e' ancora suo (non si tocca)",
              "Via dei Mille 3, Torino",
              con.execute("SELECT indirizzo FROM ordini WHERE id=?",
                          (ordine,)).fetchone()[0])
        con.close()

        print("\n[5. l'altra parte vede ancora il suo ordine]")
        lista = c.get("/api/orders", headers=h(COMPRA, "Compro")).json()
        mio = [x for x in lista if x["id"] == ordine]
        prova("l'ordine c'e' nella lista di chi ha comprato", 1, len(mio))
        prova("...e il venditore ha un nome che non e' piu' nessuno",
              "", (mio[0].get("venditore_username") if mio else None))
        prova("un avviso al fantasma non parte", "",
              SRV.asyncio.run(SRV.notifica(fantasma, "ciao")))

        print("\n[6. chi rientra parte da zero, col mancato]")
        me = c.get("/api/me", headers=h(VENDE, "Vendo")).json()
        prova("rientrato: riga nuova, zero punti", 0, me.get("xp"))
        con = SRV.db()
        esiti = sorted(r[0] for r in con.execute(
            "SELECT esito FROM p2p_esiti WHERE tg_id=?", (VENDE,)))
        prova("il mancato torna con lui, il completato no", ["mancato"], esiti)
        prova("...e il fantasma segna il rientro", True,
              con.execute("SELECT ripreso_il FROM account_cancellati"
                          ).fetchone()[0] > 0)
        con.close()

        print("\n[7. chi compra si cancella: i suoi dati escono dall'ordine]")
        r = c.post("/api/me/cancella-account", headers=h(COMPRA, "Compro"),
                   json={"conferma": "CANCELLA"})
        prova("cancellato", 200, r.status_code)
        prova("SENTINELLA LARGA anche per lui", [], dove_resta(SRV, COMPRA))
        con = SRV.db()
        o = con.execute("SELECT indirizzo, busta_nome, prezzo_sats FROM ordini "
                        "WHERE id=?", (ordine,)).fetchone()
        prova("indirizzo e busta svuotati, la cifra resta", ("", "", 50000), tuple(o))
        prova("due fantasmi diversi per due persone", 2,
              con.execute("SELECT COUNT(DISTINCT fantasma) FROM "
                          "account_cancellati").fetchone()[0])
        con.close()

        print("\n[8. un moderatore non si cancella]")
        r = c.get("/api/me/cancella-account", headers=h(999, "Admin")).json()
        prova("il foglio lo dice", True,
              any("moderatore" in x for x in r["impegni"]))
        prova("...e il gesto si ferma", 409,
              c.post("/api/me/cancella-account", headers=h(999, "Admin"),
                     json={"conferma": "CANCELLA"}).status_code)

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
