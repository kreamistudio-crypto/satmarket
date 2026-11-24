# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL CARRELLO SALVATO (6 ott 2026).

La richiesta di un utente, «salvare il carrello cosi' quando uno
rientra in app se lo ritrova», e le quattro decisioni di Andrea:
  1) comporre un carrello con un ALTRO venditore chiede prima «vuoi
     sostituirlo?» (e' del client: qui si prova che il salvataggio di un
     carrello nuovo prende il posto del vecchio, UNO per persona);
  2) comprare al volo un oggetto di un altro venditore NON tocca il
     carrello salvato;
  3) pagare un ordine dello STESSO venditore lo svuota — dal carrello o
     da una scheda sola;
  4) sette giorni dall'ultimo tocco, poi se ne va.
E il caso chiesto per nome: L'ANNUNCIO VENDUTO MENTRE IL CARRELLO
ASPETTAVA — un altro lo compra davvero (ordine, fattura, incasso), e al
rientro il carrello lo dice.

Il server e' quello VERO, chiamato per HTTP con la TestClient e
l'identita' di collaudo nell'header (`collaudo:<id>:<Nome>`): passano di
qui autenticazione, lettura del corpo, ordini, incasso, la scopa
dell'orologio e la fusione dei due account. Di finto ci sono solo la
cassaforte (la fattura e il suo «pagata») e le notifiche.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, nessuna rete.

USO:  python collaudo_carrello_salvato.py
"""

import json
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
NOTIFICHE = []

# 1 BTC = 100.000 €, cioe' MILLE SATS = UN EURO (il patto di
# collaudo_conto): le cifre si leggono a mente nelle due unita'
CAMBIO = 100_000.0

COMPRA, VENDE, RIVALE, ALTRO = 111, 222, 333, 444


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
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-carrello-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio, la convenzione che lo scanner
    # dei segreti riconosce (vedi collaudo_conto.py per il perche')
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

    conta = [0]

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        conta[0] += 1
        return {"payment_hash": f"hash{conta[0]}",
                "payment_request": f"lnbc{sats}collaudo{conta[0]}"}

    async def cambio_finto():
        return CAMBIO

    async def pagata_finta(payment_hash, _cassaforte=""):
        # la cassaforte dice sempre di si': il saldo e' il giro vero
        # (verifica_pagamento -> _incassa_ordine), solo i sats sono finti
        return True

    async def nota_finta(tg_id, testo, *a, **k):
        NOTIFICHE.append((tg_id, testo))

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.invoice_pagata = pagata_finta
    server.notifica = nota_finta
    for nome in ("notifica_admin", "polso_ordini_admin", "annuncio_su_nostr",
                 "promo_venduto", "premia_distintivi", "premia_xp"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    return db


def chi(tg_id):
    nomi = {COMPRA: "Compra", VENDE: "Vende", RIVALE: "Rivale",
            ALTRO: "Altro"}
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:{nomi.get(tg_id, 'Utente')}"}


def semina():
    """Due venditori e un compratore. Anna (222) ha quattro oggetti, uno
    in EURO; Altro (444) ne ha uno; il compratore (111) uno suo, che nel
    suo carrello non puo' entrare."""
    con = SRV.db()
    for tg_id, nome in ((COMPRA, "Compra"), (VENDE, "Anna"),
                        (RIVALE, "Rivale"), (ALTRO, "Altro")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg_id, nome, f"neg{tg_id}"))
    ids = {}
    for chiave, vend, titolo, sats, eur, valuta, qta in (
            ("lampada", VENDE, "Lampada", 30000, 0, "sats", 1),
            ("tazza", VENDE, "Tazza", 5000, 0, "sats", 3),
            ("vaso", VENDE, "Vaso", 10000, 10.0, "eur", 2),
            ("sedia", VENDE, "Sedia", 8000, 0, "sats", 2),
            ("libro", ALTRO, "Libro", 4000, 0, "sats", 1),
            ("mio", COMPRA, "Il mio", 1000, 0, "sats", 1)):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "prezzo_eur,categoria,zona,stato,creato,consegna,quantita,valuta,"
            "condizione) VALUES(?,?,'una cosa',?,?,'Altro','Pavia (PV)',"
            "'attivo',1,'ritiro',?,?,'nuovo')",
            (vend, titolo, sats, eur, qta, valuta))
        ids[chiave] = cur.lastrowid
    con.commit()
    con.close()
    return ids


def riga_db(tg_id):
    con = SRV.db()
    r = con.execute("SELECT venditore_id, righe, aggiornato FROM "
                    "carrello_salvato WHERE tg_id=?", (tg_id,)).fetchone()
    con.close()
    return dict(r) if r else None


def main():
    print("=" * 58)
    print("  IL CARRELLO SALVATO — il giro vero")
    print("=" * 58)
    avvio()
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    A = semina()

    def salva(tg_id, righe, **extra):
        corpo = {"tg_id": tg_id, "righe": [
            {"annuncio_id": a, "quantita": q} for a, q in righe]}
        corpo.update(extra)
        return c.post("/api/me/carrello", json=corpo, headers=chi(tg_id))

    def leggi(tg_id):
        r = c.get("/api/me/carrello", headers=chi(tg_id))
        return r.status_code, r.json().get("carrello")

    def paga(tg_id, corpo):
        """Un ordine fino in fondo coi percorsi veri: compra, poi la
        verifica del pagamento, che passa da _incassa_ordine."""
        o = c.post("/api/orders", json=corpo, headers=chi(tg_id))
        oid = o.json().get("ordine_id")
        v = c.post(f"/api/orders/{oid}/verifica-pagamento", headers=chi(tg_id))
        return o.status_code, oid, v.json().get("stato")

    # ------------------------------------------------------------------
    print("\n[1) si salva e si ritrova]")
    prova("senza carrello la lettura dice null", (200, None), leggi(COMPRA))
    r = salva(COMPRA, [(A["lampada"], 1), (A["tazza"], 2), (A["vaso"], 1)])
    prova("il salvataggio risponde 200 e salvato", (200, True),
          (r.status_code, r.json().get("salvato")))
    prova("...e dice quando scade: sette giorni da adesso", True,
          abs(r.json()["scade"] - (time.time() + 7 * 86400)) < 60)
    st, k = leggi(COMPRA)
    prova("rientrando lo ritrovo: venditore, nome, tre righe", (200, VENDE, "Anna", 3),
          (st, k and k["venditore_id"], k and k["venditore"],
           len(k["righe"]) if k else 0))
    prova("...con le quantita' com'erano e nell'ordine di prima",
          [(A["lampada"], 1), (A["tazza"], 2), (A["vaso"], 1)],
          [(x["annuncio_id"], x["quantita"]) for x in k["righe"]])
    prova("...ogni riga con la sua card viva e senza prezzi cambiati",
          [True, True, True, None, None, None],
          [bool(x["annuncio"]) for x in k["righe"]]
          + [x["prezzo_prima"] for x in k["righe"]])
    prova("...e la card e' quella della vetrina (titolo, stato, quantita')",
          ("Tazza", "attivo", 3),
          (k["righe"][1]["annuncio"]["titolo"],
           k["righe"][1]["annuncio"]["stato"],
           k["righe"][1]["annuncio"]["quantita"]))
    salvate = json.loads(riga_db(COMPRA)["righe"])
    prova("nel database il prezzo visto e' quello dell'annuncio, nella sua "
          "valuta (sats per la lampada, euro per il vaso)",
          [("sats", 30000), ("sats", 5000), ("eur", 10.0)],
          [(x["v"], x["p"]) for x in salvate])
    prova("chi vende non vede il carrello di chi compra", (200, None),
          leggi(VENDE))

    # ------------------------------------------------------------------
    print("\n[2) il corpo non comanda: guardie e rifiuti, senza scritture]")
    prima = riga_db(COMPRA)
    # il cambio di conto sullo stesso browser: la pagina ha in memoria il
    # carrello di 222, il cookie e' gia' quello di 111
    prova("il carrello di un altro conto (tg_id diverso) → 409", 409,
          c.post("/api/me/carrello", json={"tg_id": VENDE, "righe": []},
                 headers=chi(COMPRA)).status_code)
    prova("...senza tg_id → 409", 409, c.post(
        "/api/me/carrello", json={"righe": []},
        headers=chi(COMPRA)).status_code)
    prova("...col tg_id booleano → 409", 409, c.post(
        "/api/me/carrello", json={"tg_id": True, "righe": []},
        headers=chi(COMPRA)).status_code)
    prova("due venditori nello stesso carrello → 400", 400,
          salva(COMPRA, [(A["lampada"], 1), (A["libro"], 1)]).status_code)
    prova("un annuncio proprio → 400", 400,
          salva(COMPRA, [(A["mio"], 1)]).status_code)
    prova("nove righe (oltre MAX_RIGHE_SET) → 400", 400,
          salva(COMPRA, [(900000 + i, 1) for i in range(9)]).status_code)
    prova("la stessa riga due volte → 400", 400,
          salva(COMPRA, [(A["tazza"], 1), (A["tazza"], 2)]).status_code)
    prova("righe che non sono una lista → 400", 400, c.post(
        "/api/me/carrello", json={"tg_id": COMPRA, "righe": "tutto"},
        headers=chi(COMPRA)).status_code)
    prova("un id che non e' un numero → 400", 400, c.post(
        "/api/me/carrello",
        json={"tg_id": COMPRA, "righe": [{"annuncio_id": "abc"}]},
        headers=chi(COMPRA)).status_code)
    prova("...e dopo tutti questi rifiuti il carrello e' intatto, al byte",
          prima, riga_db(COMPRA))
    r = c.post("/api/me/carrello", json={"tg_id": COMPRA, "righe": [
        {"annuncio_id": A["lampada"], "quantita": 1, "prezzo": 1},
        {"annuncio_id": A["tazza"], "quantita": 2, "prezzo_sats": 1},
        {"annuncio_id": A["vaso"], "quantita": 1}]}, headers=chi(COMPRA))
    prova("un prezzo nel corpo non entra: il server lo legge dall'annuncio",
          [30000, 5000, 10.0],
          [x["p"] for x in json.loads(riga_db(COMPRA)["righe"])])
    prova("senza identita' → 401 (lettura e scrittura)", (401, 401),
          (c.get("/api/me/carrello").status_code,
           c.post("/api/me/carrello",
                  json={"tg_id": COMPRA, "righe": []}).status_code))

    # ------------------------------------------------------------------
    print("\n[3) L'ANNUNCIO VENDUTO MENTRE IL CARRELLO ASPETTAVA]")
    # un altro compratore prende l'ultima lampada, coi percorsi veri
    st_o, oid, stato = paga(RIVALE, {"annuncio_id": A["lampada"],
                                     "consegna": "ritiro"})
    prova("Rivale compra la lampada e la paga (ordine locked)",
          (200, "locked"), (st_o, stato))
    con = SRV.db()
    lamp = con.execute("SELECT stato, quantita FROM annunci WHERE id=?",
                       (A["lampada"],)).fetchone()
    con.close()
    prova("...la lampada e' venduta (stato e pezzi)", ("venduto", 0),
          (lamp["stato"], lamp["quantita"]))
    prova("il pagamento di UN ALTRO non tocca il mio carrello salvato",
          True, riga_db(COMPRA) is not None)
    # intanto la venditrice ritocca: due tazze vendute fuori, il prezzo
    # della tazza sale, e il CAMBIO si muove sul vaso in euro
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=1, prezzo_sats=6000 WHERE id=?",
                (A["tazza"],))
    con.execute("UPDATE annunci SET prezzo_sats=11000 WHERE id=?",
                (A["vaso"],))
    con.commit()
    con.close()
    st, k = leggi(COMPRA)
    per = {x["annuncio_id"]: x for x in k["righe"]}
    prova("rientrando la lampada c'e' ancora come riga, SENZA card",
          (True, None, "Lampada"),
          (A["lampada"] in per, per[A["lampada"]]["annuncio"],
           per[A["lampada"]]["titolo"]))
    prova("la tazza: volevo 2, ne resta 1 (la card dice il vero)", (2, 1),
          (per[A["tazza"]]["quantita"], per[A["tazza"]]["annuncio"]["quantita"]))
    prova("...e il prezzo e' cambiato: il PRIMA arriva, nella sua valuta",
          {"valuta": "sats", "prezzo": 5000}, per[A["tazza"]]["prezzo_prima"])
    prova("il vaso in EURO: il cambio che si muove NON e' un prezzo cambiato",
          None, per[A["vaso"]]["prezzo_prima"])
    con = SRV.db()
    con.execute("UPDATE annunci SET prezzo_eur=12.5 WHERE id=?", (A["vaso"],))
    con.commit()
    con.close()
    k = leggi(COMPRA)[1]
    per = {x["annuncio_id"]: x for x in k["righe"]}
    prova("...ma se la venditrice ritocca gli euro, si', col prima in euro",
          ({"valuta": "eur", "prezzo": 10.0}, 12.5),
          (per[A["vaso"]]["prezzo_prima"],
           per[A["vaso"]]["annuncio"]["prezzo_eur"]))
    # riaperto e visto: il client risalva il carrello potato
    salva(COMPRA, [(A["tazza"], 1), (A["vaso"], 1)])
    k = leggi(COMPRA)[1]
    prova("risalvato dopo averlo visto, i prezzi visti si spostano: "
          "niente piu' «prima»", [None, None],
          [x["prezzo_prima"] for x in k["righe"]])
    prova("...e il carrello potato ha due righe", 2, len(k["righe"]))

    # ------------------------------------------------------------------
    print("\n[4) decisione 2: un acquisto al volo da un ALTRO venditore]")
    st_o, oid, stato = paga(COMPRA, {"annuncio_id": A["libro"],
                                     "consegna": "ritiro"})
    prova("compro e pago il libro di Altro", (200, "locked"), (st_o, stato))
    prova("...il carrello di Anna resta", (VENDE, 2),
          (leggi(COMPRA)[1]["venditore_id"], len(leggi(COMPRA)[1]["righe"])))

    print("\n[5) un ordine NON pagato non svuota niente]")
    o = c.post("/api/orders", json={"annuncio_id": A["sedia"],
                                    "consegna": "ritiro"}, headers=chi(COMPRA))
    prova("un ordine della stessa venditrice, ancora da pagare", 200,
          o.status_code)
    prova("...il carrello c'e' ancora (si svuota al PAGAMENTO)", True,
          riga_db(COMPRA) is not None)
    # la fattura non pagata non resta a prenotare la sedia: la si lascia
    # cadere come farebbe l'orologio
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='annullato' WHERE id=?",
                (o.json()["ordine_id"],))
    con.commit()
    con.close()

    # ------------------------------------------------------------------
    print("\n[6) decisione 3: pagare un ordine della STESSA venditrice]")
    st_o, oid, stato = paga(COMPRA, {"annuncio_id": A["sedia"],
                                     "consegna": "ritiro"})
    prova("compro al volo la sedia di Anna (non era nel carrello)",
          (200, "locked"), (st_o, stato))
    prova("...e il carrello di Anna se ne va: lo stock di quel negozio e' "
          "cambiato", (None, (200, None)), (riga_db(COMPRA), leggi(COMPRA)))
    salva(COMPRA, [(A["tazza"], 1), (A["vaso"], 1)])
    prova("ricomposto il carrello di Anna", True, riga_db(COMPRA) is not None)
    st_o, oid, stato = paga(COMPRA, {"righe": [
        {"annuncio_id": A["tazza"], "quantita": 1},
        {"annuncio_id": A["vaso"], "quantita": 1}], "consegna": "ritiro"})
    prova("lo pago intero dalla cassa (un ordine, due righe)",
          (200, "locked"), (st_o, stato))
    prova("...e il carrello salvato e' vuoto", None, riga_db(COMPRA))

    # ------------------------------------------------------------------
    print("\n[7) decisione 1, la meta' del server: UNO per persona]")
    con = SRV.db()
    for t in ("tazza", "sedia"):
        con.execute("UPDATE annunci SET stato='attivo', quantita=2 "
                    "WHERE id=?", (A[t],))
    con.commit()
    con.close()
    salva(COMPRA, [(A["tazza"], 1), (A["sedia"], 1)])
    salva(COMPRA, [(A["libro"], 1)])
    con = SRV.db()
    quante = con.execute("SELECT COUNT(*) FROM carrello_salvato WHERE "
                         "tg_id=?", (COMPRA,)).fetchone()[0]
    con.close()
    prova("il carrello di un altro venditore PRENDE IL POSTO del primo "
          "(una riga sola)", (1, ALTRO), (quante, riga_db(COMPRA)["venditore_id"]))
    prova("le righe vuote lo cancellano", (200, False, None),
          (salva(COMPRA, []).status_code,
           salva(COMPRA, []).json().get("salvato"), riga_db(COMPRA)))
    prova("...e anche righe fatte solo di annunci che non esistono", None,
          (salva(COMPRA, [(987654, 1)]), riga_db(COMPRA))[1])

    # ------------------------------------------------------------------
    print("\n[8) decisione 4: sette giorni dall'ultimo tocco]")
    salva(COMPRA, [(A["tazza"], 1)])
    salva(RIVALE, [(A["sedia"], 1)])
    adesso = int(time.time())
    con = SRV.db()
    con.execute("UPDATE carrello_salvato SET aggiornato=? WHERE tg_id=?",
                (adesso - 7 * 86400 + 120, COMPRA))
    con.commit()
    con.close()
    prova("a sette giorni meno due minuti c'e' ancora", True,
          leggi(COMPRA)[1] is not None)
    con = SRV.db()
    con.execute("UPDATE carrello_salvato SET aggiornato=? WHERE tg_id=?",
                (adesso - 7 * 86400 - 120, COMPRA))
    con.commit()
    con.close()
    prova("a sette giorni e due minuti la lettura dice null", (200, None),
          leggi(COMPRA))
    prova("...e la riga se n'e' andata davvero", None, riga_db(COMPRA))
    # la scopa dell'orologio: chi non torna piu' perde il carrello lo stesso
    con = SRV.db()
    con.execute("UPDATE carrello_salvato SET aggiornato=? WHERE tg_id=?",
                (adesso - 8 * 86400, RIVALE))
    con.commit()
    con.close()
    salva(COMPRA, [(A["tazza"], 1)])
    SRV.pulisci_carrelli()
    prova("la scopa toglie il carrello vecchio di chi non torna, e "
          "lascia il fresco", (None, True),
          (riga_db(RIVALE), riga_db(COMPRA) is not None))
    # la busta di prima pagina (con `limit`: senza, la rotta risponde
    # ancora la lista nuda dei client di ieri)
    pag = c.get("/api/listings?limit=20").json()
    prova("la pagina «I tuoi dati» riceve la durata dal server",
          7, (pag.get("durate") or {}).get("carrello"))

    # ------------------------------------------------------------------
    print("\n[9) la fusione dei due account: il carrello segue, ma resta UNO]")
    NOSTR = -77
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,registrato,"
                "npub_accesso) VALUES(?,'Nostrino',1,'npub1collaudo')",
                (NOSTR,))
    con.execute("INSERT OR REPLACE INTO carrello_salvato(tg_id,venditore_id,"
                "righe,aggiornato) VALUES(?,?,?,?)",
                (NOSTR, ALTRO, json.dumps([{"id": A["libro"], "q": 1,
                                            "v": "sats", "p": 4000}]),
                 adesso))
    con.commit()
    con.close()
    esito = SRV.esegui_fusione(COMPRA, NOSTR)
    prova("la fusione passa", True, not isinstance(esito, str))
    prova("...il carrello di Telegram resta quello (uno per persona), "
          "quello della meta' Nostr se ne va", (VENDE, None),
          (riga_db(COMPRA)["venditore_id"], riga_db(NOSTR)))
    con = SRV.db()
    con.execute("DELETE FROM carrello_salvato WHERE tg_id=?", (COMPRA,))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,registrato,"
                "npub_accesso) VALUES(-78,'Nostrina',1,'npub1collaudo2')")
    con.execute("INSERT OR REPLACE INTO carrello_salvato(tg_id,venditore_id,"
                "righe,aggiornato) VALUES(-78,?,?,?)",
                (ALTRO, json.dumps([{"id": A["libro"], "q": 1, "v": "sats",
                                     "p": 4000}]), adesso))
    con.execute("UPDATE utenti SET npub_accesso='' WHERE tg_id=?", (COMPRA,))
    con.commit()
    con.close()
    esito = SRV.esegui_fusione(COMPRA, -78)
    prova("...e se Telegram non ne aveva, arriva quello della meta' Nostr",
          (True, ALTRO), (not isinstance(esito, str),
                          (riga_db(COMPRA) or {}).get("venditore_id")))

    # ------------------------------------------------------------------
    print("\n[10) il freno: un dito non ci arriva, un ciclo si']")
    NUOVO = 555
    # (24 nov 2026, freno-fermo) l'orologio del freno fermo: si prova il
    # conto del secchio, non la velocita' del runner (vedi
    # collaudo_lnbits_muto.freno_fermo; qui il banco e' un altro)
    vero_secchio = SRV._secchio_passa
    ora_ferma = time.time()
    SRV._secchio_passa = (lambda chiave, tetto, finestra, adesso:
                          vero_secchio(chiave, tetto, finestra, ora_ferma))
    try:
        codici = [c.post("/api/me/carrello", json={"tg_id": NUOVO, "righe": []},
                         headers=chi(NUOVO)).status_code for _ in range(120)]
        ultimo = c.post("/api/me/carrello", json={"tg_id": NUOVO, "righe": []},
                        headers=chi(NUOVO)).status_code
    finally:
        SRV._secchio_passa = vero_secchio
    prova("centoventi salvataggi in un minuto passano", {200}, set(codici))
    prova("...il centoventunesimo no (429)", 429, ultimo)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
