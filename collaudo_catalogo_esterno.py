# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL CATALOGO ESTERNO (set 2026).

Dalla segnalazione di un venditore: nel cassetto dei negozi collegati
trovava dei campi di spedizione, li prendeva per i SUOI costi, e il
salvataggio gli diceva di no. Adesso il collegamento Shopify/WooCommerce
e' una sezione dentro «📥 Importa in blocco / catalogo esterno», la vede
chi ha gia' un negozio collegato e i moderatori (tutti, a leva
CONNETTORI_NEGOZIO_PER_TUTTI accesa), e i costi di un negozio si dicono
DOPO averlo collegato — col catalogo fermo finche' non arrivano, o
entrerebbe in vetrina a spedizione zero.

`prove.py` fa girare il giudice di chi vede e il modulo del client;
qui il server e' quello vero, su un database usa-e-getta, e le rotte si
chiamano dalla porta HTTP con `TestClient`. Le domande:
  · chi NON deve vederla non la vede, e la porta nuova gli dice di no
    PRIMA di bussare al negozio;
  · un moderatore collega un negozio senza costi: la riga nasce, il
    catalogo NO — ne' il primo giro, ne' quello dell'ora, ne' «Aggiorna
    ora», che dice perche';
  · i costi detti dopo fanno partire il primo giro, una volta;
  · il client di IERI (costi alla nascita) e il solo ritiro partono
    subito, come sempre;
  · NESSUN NEGOZIO GIA' COLLEGATO PERDE NIENTE: lo vede, lo ritocca, e il
    giro dell'ora continua a leggerlo;
  · la leva accesa apre la porta a tutti.

IL NEGOZIO NON SI CHIAMA MAI: la prova del negozio, il primo giro e il
giro dell'ora sono registri al posto delle funzioni vere, quindi nessuna
rete — e in CI lo garantisce la gabbia di `collaudi_ci.py`.

USO:  python collaudo_catalogo_esterno.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
VENDE, ADMIN, COLLEGATO = 222, 999, 333
PROVATI = []       # (fonte, url) di ogni prova del negozio
GIRI = []          # i primi giri fatti partire dal salvataggio
LETTI = []         # i collegamenti letti dal giro dell'ora


def riga(cid):
    con = banco.SRV.db()
    r = con.execute("SELECT * FROM connettori WHERE id=?", (cid,)).fetchone()
    con.close()
    return dict(r) if r else {}


def quanti(tg_id):
    con = banco.SRV.db()
    n = con.execute("SELECT COUNT(*) FROM connettori WHERE tg_id=?",
                    (tg_id,)).fetchone()[0]
    con.close()
    return n


def giro_dell_ora():
    """Il giro dell'orologio, fatto girare adesso: l'appuntamento si
    azzera prima, o la seconda chiamata tornerebbe senza guardare."""
    LETTI.clear()
    banco.SRV._prossimo_giro_connettori = 0.0
    asyncio.run(banco.SRV.sincronizza_connettori())
    return sorted(LETTI)


def main():
    print("=" * 58)
    print("  IL CATALOGO ESTERNO — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    SRV.CONNETTORI_NEGOZIO_APERTI = True
    SRV.CONNETTORI_NEGOZIO_PER_TUTTI = False    # il default, detto

    async def prova_negozio(fonte, url, credenziali):
        PROVATI.append((fonte, url))

    # il registro si scrive alla CHIAMATA e non quando il task gira: il
    # salvataggio la fa dentro `asyncio.create_task(...)`, e se il task
    # parta prima che il TestClient chiuda il suo giro non e' affar suo
    def sync_uno(cid):
        GIRI.append(cid)

        async def niente():
            return None
        return niente()

    async def un_connettore(c_, cambio, modulo):
        LETTI.append(c_["id"])
    SRV._prova_negozio = prova_negozio
    SRV._sync_uno = sync_uno
    SRV._un_connettore = un_connettore

    # UN NEGOZIO COLLEGATO IERI, com'era: la riga senza la colonna nuova
    # nel suo INSERT, cioe' col default che la migrazione le da'
    con = SRV.db()
    for tg, nome in ((VENDE, "Vende"), (ADMIN, "Admin"),
                     (COLLEGATO, "Collegato")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    ieri = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,spedizione_eur,creato) VALUES(?,'shopify',"
        "'ieri.myshopify.com','plain:{\"token\": \"shpat_ieri\"}',"
        "'spedizione',4.0,?)", (COLLEGATO, int(time.time()))).lastrowid
    con.commit()
    con.close()

    # ---------------------------------------------------------------
    print("\n[chi non deve vederla non la vede]")
    banco.come(VENDE)
    me = c.get("/api/me").json()
    prova("un venditore qualunque: la sezione non e' sua", False,
          me.get("connettori_visibile"))
    prova("...anche se il ponte e' acceso per tutti", True,
          (me.get("connettori_leve") or {}).get("attivo"))
    prova("...e la lista dice lo stesso", False,
          c.get("/api/me/connettori").json().get("visibile"))
    r = c.post("/api/me/connettori", json={
        "fonte": "shopify", "url_negozio": "miele.myshopify.com",
        "consegna": "spedizione", "credenziali": {"token": "shpat_x"}})
    prova("la porta nuova gli dice di no, e perche'", (400, True),
          (r.status_code, "non è aperto a tutti" in r.json().get("detail", "")))
    prova("...PRIMA di bussare al negozio, e senza scrivere niente",
          ([], 0), (PROVATI, quanti(VENDE)))

    # ---------------------------------------------------------------
    print("\n[un moderatore collega un negozio: i costi dopo]")
    banco.come(ADMIN, admin=True)
    prova("il moderatore la vede", True,
          c.get("/api/me").json().get("connettori_visibile"))
    r = c.post("/api/me/connettori", json={
        "fonte": "shopify", "url_negozio": "https://Miele.myshopify.com/",
        "consegna": "spedizione", "credenziali": {"token": "shpat_x"}})
    d = r.json()
    cid = (d.get("connettore") or {}).get("id")
    prova("collegato senza costi: 200", 200, r.status_code)
    prova("...il negozio si e' provato davvero, prima di scrivere",
          [("shopify", "miele.myshopify.com")], PROVATI)
    prova("...e la riga dice che aspetta i costi", (True, 1),
          ((d.get("connettore") or {}).get("tariffe_da_dire"),
           riga(cid).get("tariffe_da_dire")))
    prova("il primo giro NON parte", (False, []),
          (d.get("primo_giro"), GIRI))
    prova("il giro dell'ora lo salta, e legge il negozio di ieri", [ieri],
          giro_dell_ora())
    r = c.post(f"/api/me/connettori/{cid}/sincronizza")
    prova("«Aggiorna ora» dice cosa manca", (400, True),
          (r.status_code, "quanto costa spedire" in r.json().get("detail", "")))
    prova("...e non fa partire niente", [], GIRI)
    # il ritocco che NON dice i costi (qui la zona): il negozio resta ad
    # aspettarli — un aggiornamento qualunque che lo sbloccasse farebbe
    # entrare il catalogo a spedizione zero dalla porta di servizio
    r = c.post("/api/me/connettori", json={
        "id": cid, "fonte": "shopify", "url_negozio": "miele.myshopify.com",
        "consegna": "spedizione", "zona": "Pavia (PV)"})
    prova("un ritocco SENZA costi non lo sblocca", (200, 1, False, []),
          (r.status_code, riga(cid).get("tariffe_da_dire"),
           r.json().get("primo_giro"), GIRI))
    r = c.post("/api/me/connettori", json={
        "id": cid, "fonte": "shopify", "url_negozio": "miele.myshopify.com",
        "consegna": "spedizione", "zona": "", "spedizione_eur": "4,90",
        "spedizione_extra_eur": 0})
    d = r.json()
    prova("i costi detti: 200, e il primo giro parte", (200, True, [cid]),
          (r.status_code, d.get("primo_giro"), GIRI))
    prova("...coi costi scritti e il catalogo sbloccato", (4.9, 0),
          (riga(cid).get("spedizione_eur"), riga(cid).get("tariffe_da_dire")))
    prova("...senza riprovare il negozio (chiavi e indirizzo quelli)", 1,
          len(PROVATI))
    prova("il giro dell'ora adesso lo legge", sorted([ieri, cid]),
          giro_dell_ora())
    r = c.post("/api/me/connettori", json={
        "id": cid, "fonte": "shopify", "url_negozio": "miele.myshopify.com",
        "consegna": "spedizione", "spedizione_eur": "5"})
    prova("un ritocco dopo non rifa' il primo giro", (200, False, [cid]),
          (r.status_code, r.json().get("primo_giro"), GIRI))

    # ---------------------------------------------------------------
    print("\n[il client di ieri e il solo ritiro partono subito]")
    GIRI.clear()
    r = c.post("/api/me/connettori", json={
        "fonte": "shopify", "url_negozio": "fiori.myshopify.com",
        "consegna": "spedizione", "spedizione_eur": 6,
        "credenziali": {"token": "shpat_y"}})
    d = r.json()
    cid2 = (d.get("connettore") or {}).get("id")
    prova("i costi alla nascita: la strada di prima", (200, False, True),
          (r.status_code, (d.get("connettore") or {}).get("tariffe_da_dire"),
           d.get("primo_giro")))
    prova("...col suo primo giro", [cid2], GIRI)
    GIRI.clear()
    r = c.post("/api/me/connettori", json={
        "fonte": "shopify", "url_negozio": "orto.myshopify.com",
        "consegna": "ritiro", "zona": "Pavia (PV)",
        "credenziali": {"token": "shpat_z"}})
    d = r.json()
    cid3 = (d.get("connettore") or {}).get("id")
    prova("il solo ritiro non ha costi da dire", (200, False, True),
          (r.status_code, (d.get("connettore") or {}).get("tariffe_da_dire"),
           d.get("primo_giro")))
    prova("...e parte subito", [cid3], GIRI)

    # ---------------------------------------------------------------
    print("\n[chi era gia' collegato non perde niente]")
    banco.come(COLLEGATO)
    GIRI.clear()
    prova("vede la sezione", True,
          c.get("/api/me").json().get("connettori_visibile"))
    lista = c.get("/api/me/connettori").json()
    prova("...e il suo negozio, che NON aspetta niente", [(ieri, False)],
          [(x.get("id"), x.get("tariffe_da_dire"))
           for x in lista.get("connettori", [])])
    r = c.post("/api/me/connettori", json={
        "id": ieri, "fonte": "shopify", "url_negozio": "ieri.myshopify.com",
        "consegna": "spedizione", "spedizione_eur": "4,50",
        "spedizione_extra_eur": 0})
    prova("lo ritocca come sempre", (200, 4.5, 0),
          (r.status_code, riga(ieri).get("spedizione_eur"),
           riga(ieri).get("tariffe_da_dire")))
    prova("...e il ritocco non e' una nascita", (False, []),
          (r.json().get("primo_giro"), GIRI))
    r = c.post("/api/me/connettori", json={
        "id": ieri, "fonte": "shopify", "url_negozio": "ieri.myshopify.com",
        "consegna": "entrambe", "zona": "Pavia (PV)"})
    prova("un corpo senza costi non glieli toglie, ne' lo ferma",
          (200, 4.5, 0), (r.status_code, riga(ieri).get("spedizione_eur"),
                          riga(ieri).get("tariffe_da_dire")))
    prova("il giro dell'ora continua a leggerlo", True,
          ieri in giro_dell_ora())
    r = c.post("/api/me/connettori", json={
        "fonte": "shopify", "url_negozio": "secondo.myshopify.com",
        "consegna": "ritiro", "zona": "Pavia (PV)",
        "credenziali": {"token": "shpat_w"}})
    prova("...e un secondo negozio lo collega (la sezione e' sua)", 200,
          r.status_code)

    # ---------------------------------------------------------------
    print("\n[la leva accesa apre la porta a tutti]")
    SRV.CONNETTORI_NEGOZIO_PER_TUTTI = True
    try:
        banco.come(VENDE)
        prova("il venditore qualunque ora la vede", True,
              c.get("/api/me").json().get("connettori_visibile"))
        r = c.post("/api/me/connettori", json={
            "fonte": "shopify", "url_negozio": "pane.myshopify.com",
            "consegna": "spedizione", "credenziali": {"token": "shpat_v"}})
        prova("...e collega, coi costi da dire come tutti", (200, True),
              (r.status_code,
               (r.json().get("connettore") or {}).get("tariffe_da_dire")))
    finally:
        SRV.CONNETTORI_NEGOZIO_PER_TUTTI = False

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
