# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL NODO MUTO (ago 2026).

Il caso che ha aperto il cantiere e' successo davvero: Spark giu',
LNbits che risponde 520, e gli sblocchi ai venditori che non solo non
partivano — quello e' inevitabile — ma **cancellavano la invoice che il
venditore aveva incollato**, gli dicevano che il suo wallet non aveva
risposto come doveva, e segnalavano ai moderatori un tentativo di
prelievo. Tre cose false in fila, su un guasto nostro.

`prove.py` difende la FORMA: che il ramo esista, che il timbro non
tocchi l'ancora dei promemoria, che il quarto esito nasca prima della
chiave che paga. Quello che non puo' fare e' far girare la STORIA — e
la storia e' l'unica cosa che dimostra che la invoice e' ancora li'.

Qui gira il SERVER VERO su un database usa-e-getta, con un LNbits di
cartone il cui stato si accende e si spegne a comando. `paga_venditore`,
`importo_invoice`, `decodifica_invoice`, `_sospendi_pagamento`, i quattro
rami d'uscita e il giro dell'orologio sono TUTTI quelli veri: di finto
c'e' solo il nodo.

  1. il venditore deposita la sua invoice, il nodo va giu', il
     compratore conferma la ricezione → la invoice E' ANCORA LI', lo
     stato e' quello di prima, e a nessuno e' arrivato un messaggio;
  2. il nodo torna su, gira l'orologio → il pagamento parte, l'ordine
     si chiude, e il timbro dice «uscito»;
  3. col nodo giu' anche il DEPOSITO di una invoice risponde 503 e non
     scrive niente: chi ne ha incollata una buona non se la sente dire
     sbagliata;
  4. il nodo che dice davvero 400 continua a rifiutare come sempre —
     la regressione che conta, o la cura avrebbe spento la cintura;
  5. il caso del TIMER: un ordine chiuso da un timer e ripreso dal giro
     deve mandare il messaggio dell'AUTOMATICO, non «l'acquirente ha
     confermato la ricezione» — cioe' la classe di bugie che il
     cantiere esiste per chiudere, che la cura poteva reintrodurre;
  6. e la ronda del libro mastro, che su tutto questo deve TACERE;
  7. L'ECO (set 2026, dal campo): un nodo che prende la richiesta,
     risponde 201 e poi NON consegna. L'ordine non si chiude, i
     moderatori lo sanno, e la stessa bolt11 ridepositata non fa
     partire nessun secondo pagamento — perche' LNbits tiene una riga
     per payment hash e a chiederglielo due volte restituisce quella
     vecchia. E' il difetto che ha lasciato un venditore non pagato
     con un ordine scritto 'released'.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna rete,
nessuna chiave.

USO:  python collaudo_lnbits_muto.py
"""

import asyncio
import hashlib
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
AVVISI = []         # quel che arriva ai moderatori
USCITE = []         # ogni POST verso la chiave che paga

# Lo stato del nodo, a comando. `codice` e' quello che risponde alla
# DECODIFICA: 520 = il canale sta male, 400 = la fattura non si legge.
# `esito` e' come finisce un pagamento in USCITA, e dal set 2026 e' una
# leva a se': un nodo che prende la richiesta e poi non consegna e' il
# caso vero del 14 settembre, e prima di quella data qui non si poteva
# nemmeno mettere in scena.
NODO = {"codice": 200, "sats": 50_000, "esito": "success",
        # (27 ott 2026, margine-cassaforte) il saldo che `/api/v1/wallet`
        # dichiara, in sats: grande di serie, cosi' la domanda del margine
        # non ferma i banchi di ieri; None = il wallet non risponde
        "saldo": 100_000_000}

# IL REGISTRO DEI PAGAMENTI, hash per hash. Non e' un vezzo del banco:
# e' LA proprieta' di LNbits che ci e' costata un ordine — tiene UNA
# riga per payment hash, e a una seconda richiesta sulla stessa bolt11
# restituisce quella vecchia senza ritentare niente. Un nodo di
# cartone che accettasse due volte direbbe che il ritentativo funziona,
# cioe' proprio la cosa falsa.
PAGAMENTI = {}


def _hash_di(bolt11):
    """L'hash di una bolt11, come lo darebbe il decode vero: fatture
    diverse, hash diversi — o il registro qui sopra non proverebbe
    niente."""
    return "h-" + hashlib.sha256(str(bolt11).encode()).hexdigest()[:16]


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


class _Risposta:
    def __init__(self, codice, corpo):
        self.status_code = codice
        self._corpo = corpo

    def raise_for_status(self):
        if self.status_code >= 300:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._corpo


class _FintoHttpx:
    """Il nodo di cartone. Distingue le due POST dall'URL, che e'
    l'unica cosa che le separa anche in produzione: /payments/decode
    con la chiave che LEGGE, /payments con quella che PAGA."""

    class AsyncClient:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kw):
            if "decode" in url:
                if NODO["codice"] >= 300:
                    return _Risposta(NODO["codice"], {})
                # il payment_hash sta nel decode anche in produzione: e'
                # da li' che il pagamento prende un nome PRIMA che i
                # sats si muovano
                return _Risposta(200, {
                    "amount_msat": NODO["sats"] * 1000,
                    "payment_hash": _hash_di(
                        (kw.get("json") or {}).get("data", ""))})
            USCITE.append(url)          # la richiesta di PAGAMENTO
            h = _hash_di((kw.get("json") or {}).get("bolt11", ""))
            PAGAMENTI[h] = NODO["esito"]
            # 201 CON L'ESITO DENTRO: e' la forma vera, ed e' quella su
            # cui il vecchio codice si e' rotto — guardava il 201 e non
            # leggeva mai questa riga
            return _Risposta(201, {"payment_hash": h,
                                   "status": NODO["esito"]})

        async def get(self, url, **kw):
            if url.endswith("/api/v1/wallet"):
                # la domanda del margine (27 ott 2026): il saldo in msat
                if NODO.get("saldo") is None:
                    return _Risposta(500, {})
                return _Risposta(200, {"balance": int(NODO["saldo"]) * 1000})
            h = url.rsplit("/", 1)[-1]
            if h not in PAGAMENTI:
                return _Risposta(404, {})   # mai visto: si puo' pagare
            s = PAGAMENTI[h]
            return _Risposta(200, {"status": s, "paid": s == "success"})


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-muto-"),
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

    async def avvisa_finto(testo, *a, **k):
        AVVISI.append(testo)

    async def zitto(*a, **k):
        return None

    # DI FINTO C'E' SOLO IL NODO: paga_venditore, importo_invoice,
    # decodifica_invoice e le quattro uscite restano quelle vere.
    server.httpx = _FintoHttpx
    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.notifica_admin = avvisa_finto
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


def _passa_un_minuto():
    """Il ritentativo per cause nostre aspetta il suo turno (1, 5, 15...
    minuti): invece di fermare l'orologio si INVECCHIA la linea del
    tempo, che e' da dove il giro legge l'ora dell'ultimo guasto."""
    con = SRV.db()
    con.execute("UPDATE payout_passi SET quando=quando-61, ultimo=ultimo-61")
    con.commit()
    con.close()


def riga(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return dict(o)


def fattura_di_ieri(oid, bolt11):
    """LA FATTURA GIA' IN COLONNA (21 set 2026). Fino al 20 set il
    venditore la incollava appena venduto, e i banchi la mettevano li'
    passando da `deposita_invoice`; da quando la fattura si incolla solo
    all'incasso quella porta prima della conferma e' CHIUSA. Gli ordini
    che una fattura ce l'hanno gia' pero' esistono, e si pagano come
    ieri: e' il caso che queste scene tengono vivo, e si semina
    scrivendo la colonna, come ha fatto il tempo."""
    con = SRV.db()
    con.execute("UPDATE ordini SET invoice_venditore=? WHERE id=?",
                (bolt11, oid))
    con.commit()
    con.close()


def semina():
    """Un venditore SENZA Lightning address: cosi' l'unica strada e' la
    invoice depositata a mano, che e' proprio quella che il vecchio
    codice cancellava."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(222,'Vende','neg22222',1,'')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,"
                "'compra@wallet.tld')")
    ids = []
    for n in range(4):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',5,'sats','nuovo')", (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_pagato(annuncio_id):
    """Un ordine fino a 'locked', coi percorsi veri: l'unica cosa
    simulata e' l'arrivo dei sats in cassaforte."""
    come(111)
    c = chiama(SRV.compra, None, corpo={"annuncio_id": annuncio_id,
                                        "consegna": "ritiro"})
    oid = c["ordine_id"]
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (oid,))
    con.commit()
    con.close()
    return oid


def main():
    print("=" * 58)
    print("  IL NODO MUTO — il giro vero")
    print("=" * 58)
    avvio()
    a1, a2, a3, a4 = semina()

    # ---- 1) il caso che ha aperto il cantiere --------------------
    print("\n[il nodo tace mentre il compratore conferma]")
    oid = ordine_pagato(a1)
    NODO["codice"] = 200
    fattura_di_ieri(oid, "lnbc-del-venditore")
    prima = riga(oid)
    prova("la invoice depositata e' in colonna", "lnbc-del-venditore",
          prima["invoice_venditore"])

    NODO["codice"] = 520                       # Spark giu'
    DETTO.clear(); AVVISI.clear(); USCITE.clear()
    come(111)
    esito = chiama(SRV.conferma_ricezione, oid, None)
    dopo = riga(oid)

    prova("il pagamento non parte, e lo dice", True,
          bool(esito.get("non_chiesto")))
    prova("LA INVOICE DEL VENDITORE E' ANCORA LI'", "lnbc-del-venditore",
          dopo["invoice_venditore"])
    prova("lo stato non si muove", prima["stato"], dopo["stato"])
    prova("...e nemmeno l'ancora dei promemoria",
          prima["aggiornato"], dopo["aggiornato"])
    prova("la riga si timbra «da riprovare»", "da_riprovare",
          dopo["payout_stato"])
    prova("...e ricorda chi aspettava i sats", "venditore",
          dopo["payout_verso"])
    prova("nessuna richiesta di pagamento e' partita", 0, len(USCITE))
    prova("al venditore non si dice che il suo wallet non risponde",
          [], [t for _, t in DETTO if "wallet" in t])
    prova("ai moderatori non arriva nessun allarme", [], AVVISI)
    # DAL SET 2026 (lo stadio «in pagamento») DAL RAMO MITE PARTONO DUE
    # AVVISI, E SOLO QUELLI: chi ha confermato sente che ha finito, chi
    # vende che i sats sono in arrivo. La regola di ago 2026 resta nella
    # sua sostanza — NESSUNO sente parlare del guasto, che e' nostro:
    # prima qui si contava zero, adesso si conta due e si guarda cosa
    # dicono.
    prova("alle due parti arriva SOLO l'ingresso nello stadio", [111, 222],
          sorted(chi for chi, _ in DETTO))
    prova("...e a nessuno dei due si nomina il guasto", [],
          [t for _, t in DETTO if any(x in t.lower() for x in (
              "nodo", "problema", "non risponde", "riprov"))])

    # ---- 2) il nodo torna, e il giro paga ------------------------
    print("\n[il nodo torna su]")
    NODO["codice"] = 200
    DETTO.clear(); USCITE.clear()
    # UN GUASTO NOSTRO SI RITENTA DOPO UN MINUTO (set 2026), non al
    # primo battito: prima del suo turno il giro non tocca la riga
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    prova("prima del suo minuto il giro non la tocca", 0, len(USCITE))
    _passa_un_minuto()
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    fine = riga(oid)
    prova("il giro paga davvero", 1, len(USCITE))
    prova("...e l'ordine si chiude", "released", fine["stato"])
    # DAL SET 2026 NON SI AZZERA PIU', ed e' la cura di un buco: il
    # ramo riuscito scrive 'uscito', e l'azzeramento del giro resta
    # CONDIZIONATO a 'da_riprovare' apposta, per non cancellare il
    # timbro di un pagamento verificato. Prima qui restava il vuoto,
    # che voleva dire sia «mai provato» sia «riuscito» — cioe' niente,
    # ed e' il motivo per cui il 14 settembre da questa riga non si e'
    # potuto sapere se i sats fossero usciti.
    prova("il timbro dice che i sats sono usciti", "uscito",
          fine["payout_stato"])
    prova("...e la riga porta l'hash di quel pagamento", True,
          bool(fine["payout_hash"]))
    prova("il venditore lo viene a sapere", True,
          any(chi == 222 for chi, _ in DETTO))
    # «Arrivati ✓» (set 2026): che l'acquirente ha confermato gliel'ha
    # gia' detto l'avviso d'ingresso nello stadio, qui arriva la sola
    # cosa nuova — e di certo NON le parole del timer
    prova("...con «Arrivati ✓», non con le parole del timer", (True, False),
          (any("Arrivati ✓" in t for chi, t in DETTO if chi == 222),
           any("scaduto" in t or "automaticamente" in t
               for chi, t in DETTO if chi == 222)))

    # ---- 3) il deposito col nodo giu' ----------------------------
    print("\n[depositare una invoice mentre il nodo tace]")
    oid2 = ordine_pagato(a2)
    # la porta si apre solo all'incasso (21 set 2026): l'ordine e' gia'
    # confermato, e il venditore senza metodo incolla la sua fattura
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='confirmed' WHERE id=?", (oid2,))
    con.commit()
    con.close()
    com_era = riga(oid2)["invoice_venditore"]
    NODO["codice"] = 520
    come(222)
    try:
        chiama(SRV.deposita_invoice, oid2, None,
               corpo={"invoice": "lnbc-buona"})
        codice = 0
    except Exception as e:
        codice = getattr(e, "status_code", 0)
    prova("il deposito risponde 503, non «invoice non valida»", 503, codice)
    # una invoice non verificata non entra in una colonna da cui si paga
    prova("...e la colonna resta com'era", com_era,
          riga(oid2)["invoice_venditore"])

    # ---- 4) la regressione: il 400 rifiuta come sempre -----------
    print("\n[il nodo dice davvero che la fattura non si legge]")
    NODO["codice"] = 400
    try:
        chiama(SRV.deposita_invoice, oid2, None,
               corpo={"invoice": "lnbc-storta"})
        codice = 0
    except Exception as e:
        codice = getattr(e, "status_code", 0)
    prova("il 400 continua a dire che la invoice non va", 400, codice)

    # e la cintura dell'importo non si e' allentata
    NODO["codice"], NODO["sats"] = 200, 999_999
    come(222)
    try:
        chiama(SRV.deposita_invoice, oid2, None,
               corpo={"invoice": "lnbc-gonfia"})
        codice = 0
    except Exception as e:
        codice = getattr(e, "status_code", 0)
    prova("l'importo sbagliato si rifiuta come sempre", 400, codice)
    NODO["sats"] = 50_000

    # ---- 5) il timer, e le parole giuste -------------------------
    print("\n[un ordine chiuso dal timer e ripreso dal giro]")
    oid3 = ordine_pagato(a3)
    NODO["codice"] = 200
    fattura_di_ieri(oid3, "lnbc-terza")
    NODO["codice"] = 520
    DETTO.clear()
    # e' il timer a chiudere: `automatico=True`, come da controlla_scadenze
    asyncio.run(SRV._sblocca_sats(oid3, automatico=True))
    tre = riga(oid3)
    prova("timer col nodo muto: si timbra e basta", "da_riprovare",
          tre["payout_stato"])
    prova("...e il timbro del timer resta scritto", True,
          tre["sbloccato_auto_il"] > 0)
    # a chi COMPRA niente (non ha confermato lui); a chi vende l'ingresso
    # nello stadio, con le parole del timer — e nessuna parola sul guasto
    prova("...a chi compra non si dice niente", 0,
          sum(1 for chi, _ in DETTO if chi == 111))
    prova("...a chi vende che i sats sono in arrivo, e PERCHE'", [True],
          ["Il tempo di conferma è scaduto" in t
           for chi, t in DETTO if chi == 222])

    NODO["codice"] = 200
    DETTO.clear()
    _passa_un_minuto()
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    prova("ripreso dal giro, l'ordine si chiude", "released",
          riga(oid3)["stato"])
    # LA RIGA CHE CONTA: al venditore va il messaggio dell'AUTOMATICO.
    # Senza il timbro riletto dal giro, qui direbbe «l'acquirente ha
    # confermato la ricezione» — e non ha confermato nessuno.
    detto_al_venditore = " ".join(t for chi, t in DETTO if chi == 222)
    prova("il venditore NON si sente dire che qualcuno ha confermato",
          False, "confermato la ricezione" in detto_al_venditore)
    prova("...ma che e' scaduto il tempo", True,
          "automaticamente" in detto_al_venditore
          or "scaduto" in detto_al_venditore)

    # ---- 6) la ronda deve tacere ---------------------------------
    print("\n[il libro mastro]")
    # una riga timbrata «da riprovare» in questo istante, per vedere che
    # la ronda non la scambi per un valore fuori contratto
    oid4 = ordine_pagato(a4)
    con = SRV.db()
    con.execute("UPDATE ordini SET payout_stato='da_riprovare' WHERE id=?",
                (oid4,))
    con.commit()
    con.close()
    AVVISI.clear()
    SRV.timbro_scrivi(SRV.TIMBRO_LIBRO_MASTRO, "")
    asyncio.run(SRV.controlla_libro_mastro())
    prova("la ronda tace su una riga da riprovare", [], AVVISI)

    # ---- 7) L'ECO: una fattura bruciata non si ritenta -----------
    # IL FATTO DEL 14 SET 2026, messo in scena. Il nodo prende la
    # richiesta e risponde 201 — cioe' esattamente come quando va bene
    # — ma dentro il corpo c'e' scritto che non ha consegnato. Prima
    # della cura questo ordine finiva 'released' con un venditore mai
    # pagato, e la notifica diceva «Ordine concluso».
    print("\n[l'eco di una fattura bruciata]")
    oid5 = ordine_pagato(a2)
    NODO["codice"] = 200
    NODO["esito"] = "failed"        # prende, e poi non consegna
    fattura_di_ieri(oid5, "lnbc-che-fallisce")
    DETTO.clear(); AVVISI.clear(); USCITE.clear()
    come(111)
    chiama(SRV.conferma_ricezione, oid5, None)
    uno = riga(oid5)
    prova("201 col fallimento dentro: l'ordine NON si chiude",
          "confirmed", uno["stato"])
    prova("...il pagamento e' partito davvero", 1, len(USCITE))
    prova("...e il diario scrive l'hash di quel tentativo", True,
          bool(uno["payout_hash"]))
    prova("...e lo conta", 1, uno["payout_tentativi"])
    # PRIMA DI OGGI QUESTO NON ARRIVAVA A NESSUNO DI NOI: l'unico
    # avviso che c'era parlava di importi storti, mai di sats che non
    # raggiungono chi li aspetta.
    prova("...e i moderatori lo vengono a sapere", 1, len(AVVISI))
    prova("...con le parole giuste", True, "FALLITO" in " ".join(AVVISI))

    # Il venditore ci riprova con LA STESSA fattura — il gesto piu'
    # naturale del mondo. Qui il vecchio codice avrebbe letto l'eco del
    # record vecchio come una risposta fresca, e chiuso l'ordine.
    AVVISI.clear(); USCITE.clear()
    come(222)
    chiama(SRV.deposita_invoice, oid5, None,
           corpo={"invoice": "lnbc-che-fallisce"})
    due = riga(oid5)
    prova("la stessa bolt11 non fa partire NESSUN pagamento",
          0, len(USCITE))
    prova("...l'ordine resta in 'confirmed'", "confirmed", due["stato"])
    prova("...il conto dei tentativi non sale", 1, due["payout_tentativi"])
    prova("...e il motivo dice che la fattura e' bruciata", True,
          "bruciata" in (due["payout_errore"] or ""))
    NODO["esito"] = "success"

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
