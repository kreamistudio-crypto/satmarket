# -*- coding: utf-8 -*-
"""
📊 IL TUO NEGOZIO, SUL SERVER VERO (24 set 2026).

Un venditore consigliato chiedeva dove vede il contatore delle visite: fino
a oggi le aperture dello spazio in vetrina le leggeva solo il moderatore con
`/sponsor`. Da questo cantiere il venditore ha nel Profilo il cassetto
«📊 Il tuo negozio» — visite alla pagina negli ultimi 7 e 30 giorni, aperture
da «Da scoprire» se il suo spazio e' acceso, vendite e sats degli ultimi 30
giorni e da sempre, recensioni — e i moderatori lo stesso cassetto per ogni
negozio dal pannello.
`prove.py` gira il giudice estratto su un database in memoria; qui si fa la
domanda che solo il server VERO risponde: cosa contano DAVVERO le rotte, con
le identita' di collaudo e la rotta del negozio che si apre come la apre il
client.

IL GIRO:
  - la porta del venditore: all'anonimo 401, senza annunci «mostra: false»;
  - le aperture: `vista=1` conta, senza non conta, il venditore sul suo
    negozio non conta, la pagina dopo e «Altri oggetti» non contano;
  - NIENTE IP NEL DATABASE: dopo il giro nessuna tabella contiene
    l'indirizzo con cui il banco bussa, e `negozio_visite` ha tre colonne;
  - le vendite: una conclusa dieci giorni fa, una quaranta, un rimborso —
    30 giorni e da sempre, col «da sempre» che e' `vendite_ok`;
  - lo spazio in vetrina: acceso, il tocco della card conta un'apertura
    dello spazio E una visita, e il cassetto lo dice con la scadenza;
  - la porta dei moderatori: 403 a chi non lo e', 404 al codice che non
    c'e' o che non ha la forma, e per il moderatore gli STESSI numeri che
    il venditore legge nel suo cassetto.

Niente parla con Telegram ne' coi relay: il `config` finto e il nodo finto
li installa `avvio()` del banco PRIMA dell'import di server, e in CI c'e' la
gabbia senza rete di `collaudi_ci.py`.

USO:  python collaudo_numeri_negozio.py
"""

import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
ANONIMO = {}
MODERATORE = {"X-Tg-Init-Data": "collaudo:999:Admin"}
VENDITORE = {"X-Tg-Init-Data": "collaudo:222:Venditore"}
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
PAGINA = "un-tempo-per-te"


def main():
    print("=" * 58)
    print("  📊 IL TUO NEGOZIO — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    SRV = banco.SRV
    c = TestClient(SRV.app)
    cat = SRV.RACCONTI_NEGOZI[PAGINA]
    salvato = {k: cat.get(k) for k in ("negozio", "venditore_tg")}
    cat["negozio"], cat["venditore_tg"] = "", 222
    # il giro con gli acquisti nel Profilo (la strada resta, dietro la
    # leva); in fondo `giro_acquisti_spenti` prova la leva spenta, quella
    # di serie dal 17 nov 2026 sera
    prima = SRV.ACQUISTI_NEL_PROFILO
    try:
        SRV.ACQUISTI_NEL_PROFILO = True
        giro(c, SRV)
        SRV.ACQUISTI_NEL_PROFILO = False
        giro_acquisti_spenti(c, SRV)
    finally:
        SRV.ACQUISTI_NEL_PROFILO = prima
        for k, v in salvato.items():
            if v is None:
                cat.pop(k, None)
            else:
                cat[k] = v

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


def giro(c, SRV):
    def numeri(h=VENDITORE):
        r = c.get("/api/me/negozio/numeri", headers=h)
        return r.status_code, r.json()

    def apri(cod, h=ANONIMO, coda="&vista=1"):
        return c.get(f"/api/negozio/{cod}?limit=12{coda}",
                     headers=h).status_code

    def righe_visite():
        con = SRV.db()
        r = [tuple(x) for x in con.execute(
            "SELECT negozio, giorno, quante FROM negozio_visite "
            "ORDER BY negozio, giorno")]
        con.close()
        return r

    print("\n[la porta del venditore]")
    r = c.get("/api/me/negozio/numeri", headers=ANONIMO)
    prova("all'anonimo la porta risponde 401", 401, r.status_code)
    prova("senza annunci il cassetto non c'e'", (200, {"mostra": False}),
          numeri())
    con = SRV.db()
    cod = con.execute("SELECT negozio FROM utenti WHERE tg_id=222"
                      ).fetchone()["negozio"]
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(222,'Tazza','desc',1000,'Altro','Torino (TO)','attivo',?,"
        "'ritiro',1,'sats','buono')", (int(time.time()),))
    con.commit()
    con.close()
    s, d = numeri()
    prova("con un annuncio il cassetto c'e', col suo codice",
          (200, True, cod), (s, d.get("mostra"), d.get("negozio")))
    prova("...e parte da zero", (0, 0, 0, 0, 0),
          (d["visite_7"], d["visite_30"], d["vendite_30"], d["sats_30"],
           d["n_feedback"]))
    prova("...e dice da che giorno si conta: oggi",
          time.strftime("%Y-%m-%d"), d["visite_dal"])
    prova("chi non ha annunci (111) non ha il cassetto", {"mostra": False},
          numeri(COMPRATORE)[1])

    print("\n[le aperture]")
    prova("l'anonimo apre il negozio: 200", 200, apri(cod))
    apri(cod, COMPRATORE)
    prova("due aperture, due visite", 2, numeri()[1]["visite_7"])
    apri(cod, VENDITORE)
    prova("il venditore sul suo negozio non conta", 2,
          numeri()[1]["visite_7"])
    apri(cod, coda="")
    apri(cod, coda="&cursore=abc")
    prova("senza vista=1 non conta: «Altri oggetti», la pagina dopo", 2,
          numeri()[1]["visite_30"])
    apri(cod, coda="&vista=2")
    apri(cod, coda="&vista=0")
    prova("...e un vista che non e' 1 nemmeno", 2, numeri()[1]["visite_30"])
    prova("nel database: una riga per negozio e giorno, solo il numero",
          [(cod, time.strftime("%Y-%m-%d"), 2)], righe_visite())
    prova("un codice che non c'e' risponde 404 e non scrive niente",
          (404, 1), (apri("zzzzzzzz"), len(righe_visite())))

    print("\n[niente IP, niente chi]")
    con = SRV.db()
    colonne = [x[1] for x in con.execute("PRAGMA table_info(negozio_visite)")]
    prova("la tabella ha tre colonne", ["negozio", "giorno", "quante"],
          colonne)
    # TestClient bussa come «testclient»: se una riga qualunque di una
    # tabella qualunque lo avesse scritto, qualcuno ha salvato l'indirizzo
    trovate = []
    for (t,) in con.execute("SELECT name FROM sqlite_master "
                            "WHERE type='table'").fetchall():
        for riga in con.execute(f'SELECT * FROM "{t}"').fetchall():
            if any("testclient" in str(x) for x in tuple(riga)):
                trovate.append(t)
                break
    con.close()
    prova("nessuna tabella contiene l'indirizzo di chi ha bussato", [],
          trovate)

    print("\n[le vendite]")
    ora = int(time.time())
    con = SRV.db()
    for oid, stato, prezzo, prot, agg in (
            (901, "released", 10000, 0, ora - 3600),
            (902, "released", 5000, 1000, ora - 40 * 86400),
            (903, "refunded", 7777, 0, ora)):
        con.execute("INSERT INTO ordini(id, annuncio_id, compratore_id, "
                    "venditore_id, prezzo_sats, protezione_sats, stato, "
                    "creato, aggiornato) VALUES(?,1,111,222,?,?,?,?,?)",
                    (oid, prezzo, prot, stato, agg, agg))
    con.execute("INSERT INTO payout_passi(tabella, riga_id, passo, motivo, "
                "via, quando, ultimo) VALUES('ordini', 901, 'arrivato', '', "
                "'lightning', ?, ?)", (ora - 10 * 86400, ora - 10 * 86400))
    # il contatore del profilo, come lo scrive il rilascio (due vendite)
    con.execute("UPDATE utenti SET vendite_ok=2, rating=4.5, n_feedback=2, "
                "n_recensori=1 WHERE tg_id=222")
    con.commit()
    con.close()
    d = numeri()[1]
    prova("30 giorni: la vendita di 10 giorni fa, coi suoi sats",
          (1, 10000), (d["vendite_30"], d["sats_30"]))
    prova("da sempre: vendite_ok e i sats delle due concluse (senza il "
          "rimborso)", (2, 14000), (d["vendite_tot"], d["sats_tot"]))
    prova("le recensioni come il profilo", (4.5, 2, 1),
          (d["rating"], d["n_feedback"], d["n_recensori"]))
    r = c.get(f"/api/negozio/{cod}", headers=ANONIMO).json()["venditore"]
    prova("...e il «da sempre» e' il numero che il negozio mostra a tutti",
          r["vendite_ok"], d["vendite_tot"])
    prova("il venditore che non ha mai comprato: acquisti a zero",
          (True, 0, 0, 0, 0), (d["venditore"], d["acquisti_30"],
                               d["sats_acq_30"], d["acquisti_tot"],
                               d["sats_acq_tot"]))

    print("\n[gli acquisti (17 nov 2026)]")
    # 111 ha comprato le due concluse qui sopra: il contatore come lo
    # scrive il rilascio, e nessun annuncio suo
    con = SRV.db()
    con.execute("UPDATE utenti SET acquisti_ok=2 WHERE tg_id=111")
    con.commit()
    con.close()
    s, d = numeri(COMPRATORE)
    prova("chi ha SOLO comprato ha il cassetto, da compratore",
          (200, True, False), (s, d.get("mostra"), d.get("venditore")))
    prova("30 giorni: l'acquisto di 10 giorni fa, il totale pagato",
          (1, 10000), (d["acquisti_30"], d["sats_acq_30"]))
    prova("da sempre: acquisti_ok e il TOTALE PAGATO, protezione compresa "
          "(il venditore ne ha incassati 14 000)", (2, 15000),
          (d["acquisti_tot"], d["sats_acq_tot"]))
    prova("...e il rimborso non conta", False, "7777" in repr(d))

    print("\n[lo spazio in vetrina]")
    prova("spento, il cassetto non lo nomina", [], d["sponsor"])
    fino = ora + 10 * 86400
    SRV.imposta_sponsor(PAGINA, fino)
    apri(cod, coda=f"&da=sponsor%3A{PAGINA}&vista=1")
    d = numeri()[1]
    prova("acceso, il tocco della card: un'apertura dello spazio...",
          [{"slug": PAGINA, "fino": fino, "aperture_30": 1}], d["sponsor"])
    prova("...ed e' anche una visita", 3, d["visite_7"])
    SRV.imposta_sponsor(PAGINA, 0)
    prova("spento di nuovo, sparisce", [], numeri()[1]["sponsor"])

    print("\n[la porta dei moderatori]")
    r = c.get(f"/api/admin/negozio/{cod}/numeri", headers=COMPRATORE)
    prova("a chi non e' moderatore: 403", 403, r.status_code)
    r = c.get(f"/api/admin/negozio/{cod}/numeri", headers=ANONIMO)
    prova("all'anonimo: 401", 401, r.status_code)
    r = c.get("/api/admin/negozio/zzzzzzzz/numeri", headers=MODERATORE)
    prova("un codice che non c'e': 404", 404, r.status_code)
    r = c.get("/api/admin/negozio/ab%27cd/numeri", headers=MODERATORE)
    prova("...e uno che non ha la forma: 404", 404, r.status_code)
    r = c.get(f"/api/admin/negozio/{cod}/numeri", headers=MODERATORE)
    mio = numeri()[1]
    adm = r.json()
    prova("il moderatore legge gli STESSI numeri del venditore", True,
          r.status_code == 200 and all(adm.get(k) == v for k, v in
                                       mio.items()))
    prova("...col nome del negozio accanto", True, bool(adm.get("nome")))
    con = SRV.db()
    cod111 = con.execute("SELECT negozio FROM utenti WHERE tg_id=111"
                         ).fetchone()["negozio"]
    con.close()
    r = c.get(f"/api/admin/negozio/{cod111}/numeri", headers=MODERATORE)
    prova("...e anche di un negozio senza annunci (tutto a zero)",
          (200, True, 0), (r.status_code, r.json().get("mostra"),
                           r.json().get("visite_30")))



def giro_acquisti_spenti(c, SRV):
    """🛍️ GLI ACQUISTI FUORI DAL PROFILO (17 nov 2026 sera, Andrea: «le
    vendite lasciale, rimetti come era prima. Gli acquisti non li
    aggiungere»), a leva ACQUISTI_NEL_PROFILO spenta, sul database che
    `giro` ha lasciato: 222 ha venduto, 111 ha solo comprato."""
    print("\n[🛍️ gli acquisti fuori dal Profilo (leva spenta, di serie)]")
    r = c.get("/api/me/negozio/numeri", headers=VENDITORE)
    d = r.json()
    prova("il venditore ha il cassetto con le vendite di prima",
          (200, True, 2, 14000), (r.status_code, d.get("mostra"),
                                  d.get("vendite_tot"), d.get("sats_tot")))
    prova("...e senza acquisti", [], sorted(k for k in d if "acq" in k))
    prova("chi ha SOLO comprato non ha il cassetto, come prima",
          (200, {"mostra": False}),
          (lambda r: (r.status_code, r.json()))(
              c.get("/api/me/negozio/numeri", headers=COMPRATORE)))
    con = SRV.db()
    cod111 = con.execute("SELECT negozio FROM utenti WHERE tg_id=111"
                         ).fetchone()["negozio"]
    acq = con.execute("SELECT acquisti_ok FROM utenti WHERE tg_id=111"
                      ).fetchone()["acquisti_ok"]
    con.close()
    adm = c.get(f"/api/admin/negozio/{cod111}/numeri",
                headers=MODERATORE).json()
    prova("il moderatore non vede gli acquisti di chi ha comprato", [],
          sorted(k for k in adm if "acq" in k))
    prova("il contatore acquisti_ok resta com'era (livello e distintivi)",
          2, acq)
    me = c.get("/api/me", headers=COMPRATORE).json()
    prova("/api/me: la testata non mostra gli acquisti, ma il numero "
          "arriva per il livello", (False, 2),
          (me.get("acquisti_nel_profilo"), me.get("acquisti_ok")))


if __name__ == "__main__":
    sys.exit(main())
