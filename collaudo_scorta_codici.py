# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA SCORTA DI CODICI (24 nov 2026, cantiere scorta-codici;
Andrea: «c'e' modo di precaricare una serie di codici coupon che il
cliente usa in autonomia?», per i corsi di BitcoinLabs).

IL CASO: chi vende un digitale incolla PRIMA i codici, uno per riga; al
pagamento Barattolo ne consegna uno da solo, e chi vende non fa niente.
Gira la STORIA sul SERVER VERO con un database usa-e-getta e il nodo di
cartone del banco di casa (`collaudo_lnbits_muto`): compra, incasso,
consegna, lettura e «Funziona» sono quelli veri.

Le domande a cui risponde:
  1. le guardie della rotta: solo il codice online puro, solo chi vende,
     il vuoto, il troppo lungo, i doppioni (nella lista e gia' caricati),
     il tetto; la risposta dice QUANTI e mai i codici;
  2. un pezzo: al pagamento l'ordine e' consegnato col PRIMO codice,
     chi compra lo rivela, chi vende sa quanti ne restano;
  3. tre pezzi: i riquadri di «un codice alla volta», coi codici della
     scorta in ordine, e il primo si apre;
  4. la scorta che non basta: l'ordine resta da consegnare a mano, i
     codici restano liberi, chi vende e' avvisato;
  5. senza scorta: la consegna a mano di sempre, senza avvisi nuovi;
  6. un codice uscito non torna: l'ordine dopo prende il successivo;
  7. a leva spenta: niente consegna da sola, niente codici nuovi, ma
     toglierli si puo';
  8. «togli» porta via solo i liberi.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete,
nessuna chiave.

USO:  python collaudo_scorta_codici.py
"""

import time

import collaudo_lnbits_muto as banco

prova = banco.prova
SRV = None

PREZZO = 20_000
CODICI = ["CORSO-AAAA-1111", "CORSO-BBBB-2222", "CORSO-CCCC-3333",
          "https://t.me/ilragiondomobot?start=c4", "CORSO-EEEE-5555"]


def alza(nome, fn, codice, dentro=""):
    try:
        fn()
    except Exception as e:
        cod = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        dice = (not dentro) or dentro.lower() in testo.lower()
        prova(nome, (codice, True), (cod, dice))
        if not (cod == codice and dice):
            print(f"      testo: {testo!r}")
        return
    prova(nome, codice, "nessun rifiuto")


def avvio():
    global SRV
    banco.avvio()
    SRV = banco.SRV

    async def zitto(*a, **k):
        return None

    SRV.annuncio_su_nostr = zitto
    SRV.promo_venduto = zitto


def db_uno(sql, *args):
    con = SRV.db()
    r = con.execute(sql, args).fetchone()
    con.close()
    return r


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci", "codici_digitali",
              "codici_scorta"):
        try:
            con.execute(f"DELETE FROM {t}")
        except Exception:
            pass
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(222,'Vende','neg22222',1,"
                "'vende@wallet.tld')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,"
                "'compra@wallet.tld')")
    ids = {}
    for nome, consegna in (("corso", "digitale"), ("altro", "digitale"),
                           ("libro", "spedizione")):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
            "valuta,condizione) VALUES(222,?,'desc',?,'Buoni ed esperienze',"
            "'Torino (TO)','attivo',1,?,20,20,'sats','nuovo')",
            (f"Il {nome}", PREZZO, consegna))
        ids[nome] = cur.lastrowid
    con.commit()
    con.close()
    return ids


def pulisci_giro():
    banco.DETTO.clear()
    banco.AVVISI.clear()


def scrivi(aid, corpo, chi=222):
    banco.come(chi)
    return banco.chiama(SRV.scrivi_scorta_codici, aid, None, "", "",
                        corpo=corpo)


def conta(aid, chi=222):
    banco.come(chi)
    return banco.chiama(SRV.scorta_codici, aid, "", "")


def compra(aid, pezzi=1):
    """Un ordine pagato, dai percorsi veri: l'incasso fa il resto."""
    banco.come(111)
    c = banco.chiama(SRV.compra, None,
                     corpo={"annuncio_id": aid, "quantita": pezzi,
                            "consegna": "digitale"})
    oid = c["ordine_id"]
    pulisci_giro()
    banco.chiama(SRV._incassa_ordine, oid)
    return oid


def leggi(oid, chi=111):
    banco.come(chi)
    return banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", None)


def detti_a(chi):
    return " || ".join(t for c, t in banco.DETTO if c == chi)


def liberi(aid):
    return db_uno("SELECT COUNT(*) FROM codici_scorta WHERE annuncio_id=? "
                  "AND ordine_id=0", aid)[0]


# ---------------------------------------------------------------
def scena_guardie(ids):
    print("\n── 1. LE GUARDIE DELLA ROTTA ──")
    aid = ids["corso"]
    alza("un annuncio spedito non ha scorta",
         lambda: scrivi(ids["libro"], {"aggiungi": "X"}), 400,
         "codice online")
    alza("l'annuncio di un altro no",
         lambda: scrivi(aid, {"aggiungi": "X"}, chi=111), 400,
         "non permess")
    alza("una lista vuota si rifiuta",
         lambda: scrivi(aid, {"aggiungi": " \n \n"}), 400, "uno per riga")
    alza("un codice troppo lungo si rifiuta, con la sua riga",
         lambda: scrivi(aid, {"aggiungi": "OK\n" + "x" * 1001}), 400,
         "riga 2")
    r = scrivi(aid, {"aggiungi": "\n".join(CODICI[:3] + [CODICI[0]])})
    prova("tre codici entrano, il doppione della lista no",
          (3, 1, 3), (r["aggiunti"], r["doppioni"], r["liberi"]))
    r = scrivi(aid, {"aggiungi": "\n".join(CODICI[2:])})
    prova("...e quello gia' caricato nemmeno", (2, 1, 5),
          (r["aggiunti"], r["doppioni"], r["liberi"]))
    d = conta(aid)
    prova("la lettura dice quanti, e nessun codice", (5, 0, True, []),
          (d["liberi"], d["consegnati"], d["attiva"],
           [c for c in CODICI if c in repr(d)]))
    cif = [x[0] for x in SRV.db().execute(
        "SELECT contenuto FROM codici_scorta").fetchall()]
    prova("nel database i codici non stanno in chiaro... o sono marcati",
          True, all(c.startswith(("f2:", "plain:")) for c in cif))
    vecchio = SRV.MAX_CODICI_SCORTA
    SRV.MAX_CODICI_SCORTA = 6
    alza("oltre il tetto si rifiuta",
         lambda: scrivi(aid, {"aggiungi": "NUOVO-1\nNUOVO-2"}), 400,
         "al massimo 6")
    SRV.MAX_CODICI_SCORTA = vecchio
    prova("...e non ne entra nessuno", 5, liberi(aid))


def scena_un_pezzo(ids):
    print("\n── 2. UN PEZZO: IL CODICE PARTE DA SOLO ──")
    aid = ids["corso"]
    oid = compra(aid)
    o = banco.riga(oid)
    prova("l'ordine pagato e' gia' consegnato", ("shipped",
          "Consegna digitale"), (o["stato"], o["corriere"]))
    prova("...col primo codice della scorta", CODICI[0],
          SRV._decifra_contenuto(o["contenuto_digitale"]))
    prova("...e timbrato «dalla scorta» (il link a un bot si tocca)", 1,
          o["dalla_scorta"])
    prova("chi compra sa che c'e' da rivelare", True,
          "ha consegnato il contenuto" in detti_a(111))
    prova("chi vende sa che e' partito e quanti ne restano", True,
          "Ne restano 4" in detti_a(222) and "da solo" in detti_a(222))
    d = leggi(oid)
    prova("la rivelazione da' il codice", CODICI[0], d.get("contenuto"))
    prova("la scorta scende di uno", (4, 1),
          (conta(aid)["liberi"], conta(aid)["consegnati"]))
    prova("il codice sa di che ordine e'", oid,
          db_uno("SELECT ordine_id FROM codici_scorta WHERE annuncio_id=? "
                 "ORDER BY id LIMIT 1", aid)[0])


def scena_riquadri(ids):
    print("\n── 3. TRE PEZZI: I RIQUADRI ──")
    aid = ids["corso"]
    oid = compra(aid, 3)
    o = banco.riga(oid)
    prova("consegnato a riquadri, tre, dalla scorta", ("shipped", 3, 1),
          (o["stato"], o["codici_n"], o["dalla_scorta"]))
    righe = SRV.db().execute("SELECT n, contenuto FROM codici_digitali "
                             "WHERE ordine_id=? ORDER BY n",
                             (oid,)).fetchall()
    prova("...coi codici 2, 3 e 4 della scorta, in ordine", CODICI[1:4],
          [SRV._decifra_contenuto(r[1]) for r in righe])
    prova("chi compra legge l'avviso dei riquadri", True,
          "uno alla volta" in detti_a(111))
    d = leggi(oid)
    prova("si apre solo il primo", [CODICI[1]],
          [c["testo"] for c in d["codici"] if c.get("testo")])
    prova("ne resta uno", 1, liberi(aid))


def scena_non_basta(ids):
    print("\n── 4. LA SCORTA CHE NON BASTA ──")
    aid = ids["corso"]
    oid = compra(aid, 2)
    o = banco.riga(oid)
    prova("l'ordine resta da consegnare a mano", ("locked", ""),
          (o["stato"], o["contenuto_digitale"] or ""))
    prova("...il codice rimasto resta libero", 1, liberi(aid))
    prova("...e chi vende e' avvisato", True,
          "sono finiti" in detti_a(222) and f"#{oid}" in detti_a(222))
    oid1 = compra(aid, 1)
    prova("un pezzo solo prende l'ultimo", ("shipped", CODICI[4]),
          (banco.riga(oid1)["stato"], SRV._decifra_contenuto(
              banco.riga(oid1)["contenuto_digitale"])))
    prova("...e chi vende sa che non ne restano", True,
          "Non ne restano più" in detti_a(222))
    oid2 = compra(aid, 1)
    prova("finita la scorta, a mano e con l'avviso", ("locked", True),
          (banco.riga(oid2)["stato"], "sono finiti" in detti_a(222)))


def scena_senza_scorta(ids):
    print("\n── 5. SENZA SCORTA: COME IERI ──")
    oid = compra(ids["altro"])
    prova("l'ordine resta da consegnare, senza timbro", ("locked", 0),
          (banco.riga(oid)["stato"], banco.riga(oid)["dalla_scorta"]))
    prova("...e nessun avviso della scorta", False,
          "codici pronti" in detti_a(222))


def scena_leva(ids):
    print("\n── 6. LA LEVA SPENTA ──")
    aid = ids["altro"]
    scrivi(aid, {"aggiungi": "LEVA-1\nLEVA-2"})
    SRV.SCORTA_CODICI = False
    try:
        oid = compra(aid)
        prova("a leva spenta il codice non parte", ("locked", 2),
              (banco.riga(oid)["stato"], liberi(aid)))
        alza("...e non se ne aggiungono", lambda: scrivi(
            aid, {"aggiungi": "LEVA-3"}), 400, "spenti")
        prova("la lettura lo dice", False, conta(aid)["attiva"])
        r = scrivi(aid, {"togli": True})
        prova("...ma toglierli si puo'", (2, 0), (r["tolti"], liberi(aid)))
    finally:
        SRV.SCORTA_CODICI = True


def scena_togli(ids):
    print("\n── 7. TOGLI: SOLO I LIBERI ──")
    aid = ids["corso"]
    usati = db_uno("SELECT COUNT(*) FROM codici_scorta WHERE annuncio_id=? "
                   "AND ordine_id<>0", aid)[0]
    scrivi(aid, {"aggiungi": "ULTIMO-1"})
    r = scrivi(aid, {"togli": True})
    prova("via il libero, restano i consegnati", (1, 0, usati),
          (r["tolti"], liberi(aid), conta(aid)["consegnati"]))
    r = scrivi(aid, {"aggiungi": CODICI[0]})
    prova("un codice gia' consegnato non rientra (doppione)", (0, 1),
          (r["aggiunti"], r["doppioni"]))


def main():
    print("=" * 58)
    print("  LA SCORTA DI CODICI — il giro vero")
    print("=" * 58)
    avvio()
    ids = semina()
    scena_guardie(ids)
    scena_un_pezzo(ids)
    scena_riquadri(ids)
    scena_non_basta(ids)
    scena_senza_scorta(ids)
    scena_leva(ids)
    scena_togli(ids)
    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
