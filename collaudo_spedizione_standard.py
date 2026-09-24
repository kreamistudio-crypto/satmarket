# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL COSTO DI SPEDIZIONE STANDARD (set 2026).

`prove.py` fa girare i giudici estratti — il costo, i motivi, i numeri
nuovi — e guarda la forma delle rotte. Quello che non puo' fare e' far
girare la cosa VERA: una colonna che manca, una transazione che si
pesta i piedi, un «niente moderazione» che resta vero solo finche'
nessuno lo chiama. Qui il server e' quello vero, su un database
usa-e-getta, e le rotte si chiamano dalla porta HTTP con `TestClient`.

Le domande, nell'ordine in cui si fanno:
  · il SALVA del cassetto porta lo standard, lo rifiuta con un 400
    parlante quando e' storto, e non tocca le reti se non le nomina
    (ne' il client di ieri tocca lo standard);
  · l'ANTEPRIMA dice chi cambia e chi resta, ognuno col suo motivo — e
    non scrive NIENTE, nemmeno lo standard che le si fa provare;
  · l'APPLICAZIONE porta le tariffe (sats fissi, euro ancorati, euro del
    listino in euro, tradotti al cambio) sui soli idonei, con la copia
    di casa nella mappa e l'estero com'era, SENZA passare dalla
    moderazione e senza toccare testo, stato e ordini;
  · la CORSA: chi compra fra il piano e la scrittura lascia l'articolo
    com'era, e una riga cambiata sotto i piedi non si prende numeri
    pensati per un'altra;
  · i RELAY: a lotti, un giro per venditore, il secondo si accoda.

NON TOCCA NIENTE DI VERO: il config di cartone lo installa `avvio()` del
banco PRIMA dell'import del server. Nessuna rete — e in CI lo garantisce
la gabbia di `collaudi_ci.py`, non questa riga.

USO:  python collaudo_spedizione_standard.py
"""

import asyncio
import json
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
VENDE, COMPRA = 222, 111
MODERATI = []      # ogni chiamata alla moderazione: deve restare vuoto
RELAY = []         # (id, status, solo_aggiornamento) di ogni rilancio


def db():
    return banco.SRV.db()


def semina():
    """Il negozio di 222 — un articolo per ogni caso — piu' un articolo
    di 111 che nessuno deve toccare. Torna {nome: id}."""
    con = db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((VENDE, "Vende"), (COMPRA, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    zone_ieri = json.dumps({"dom": {"sats": 3000, "eur": 0.0},
                            "eu": {"sats": 3000, "eur": 0.0}})
    casi = {
        "fisso": dict(spedizione_sats=3000, spedizione_zone=zone_ieri),
        "ancorato": dict(spedizione_sats=0, spedizione_eur=4.5,
                         spedizione_zone=json.dumps(
                             {"dom": {"sats": 0, "eur": 4.5}})),
        "euro": dict(valuta="eur", prezzo_eur=20.0, spedizione_sats=3500,
                     spedizione_eur=3.5, spedizione_zone=json.dumps(
                         {"dom": {"sats": 3500, "eur": 3.5}})),
        "entrambe": dict(consegna="entrambe", spedizione_sats=2000,
                         spedizione_punto_sats=1500,
                         spedizione_punto_dichiarata=1),
        "gratis": dict(spedizione_sats=0),
        "ritiro": dict(consegna="ritiro", spedizione_sats=0),
        "digitale": dict(consegna="digitale", spedizione_sats=0),
        "revisione": dict(stato="revisione", spedizione_sats=3000),
        "nostr": dict(contatto_nostr="npub1collaudo", spedizione_sats=3000),
        "shopify": dict(fonte="shopify", connettore_id=7,
                        spedizione_sats=3000),
        "ordine": dict(spedizione_sats=3000),
        "set": dict(spedizione_sats=3000),
        "uguale": dict(spedizione_sats=5000),
        "no_casa": dict(non_spedisce_casa=1, spedizione_sats=0,
                        spedizione_zone=json.dumps(
                            {"eu": {"sats": 9000, "eur": 0.0}})),
        "asta": dict(asta_base_sats=10_000, spedizione_sats=0),
        "esaurito": dict(stato="venduto", quantita=0, spedizione_sats=3000),
    }
    ids = {}
    for nome, extra in casi.items():
        r = dict(venditore_id=VENDE, titolo=f"Articolo {nome}",
                 descrizione="descrizione", prezzo_sats=30_000,
                 categoria="Altro", zona="Torino (TO)", stato="attivo",
                 creato=1, consegna="spedizione", quantita=3, valuta="sats",
                 condizione="buono", modificato=0)
        r.update(extra)
        ids[nome] = con.execute(
            f"INSERT INTO annunci({','.join(r)}) "
            f"VALUES({','.join('?' * len(r))})", tuple(r.values())).lastrowid
    ids["altrui"] = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats) VALUES(?,'Altrui','d',1000,'Altro','Torino (TO)',"
        "'attivo',1,'spedizione',1,'sats','buono',3000)",
        (COMPRA,)).lastrowid
    adesso = int(time.time())
    # un ordine MONO vivo sull'«ordine», con la spedizione fotografata
    con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,quantita,stato,consegna_scelta,spedizione_sats,creato,"
        "aggiornato) VALUES(?,?,?,33000,1,'locked','spedizione',3000,?,?)",
        (ids["ordine"], COMPRA, VENDE, adesso, adesso))
    # un SET vivo che porta il «set» come RIGA: la testata ha
    # annuncio_id=0, ed e' il caso che un controllo sulla sola testata
    # si dimenticherebbe
    oid = con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,quantita,stato,consegna_scelta,spedizione_sats,creato,"
        "aggiornato) VALUES(0,?,?,63000,2,'shipped','spedizione',3000,?,?)",
        (COMPRA, VENDE, adesso, adesso)).lastrowid
    con.execute("INSERT INTO ordine_righe(ordine_id,annuncio_id,quantita,"
                "unitario_sats,titolo) VALUES(?,?,1,30000,'Articolo set')",
                (oid, ids["set"]))
    # e un ordine CONCLUSO sul «fisso»: terminale, non ferma niente
    con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,quantita,stato,consegna_scelta,spedizione_sats,creato,"
        "aggiornato) VALUES(?,?,?,33000,1,'released','spedizione',3000,?,?)",
        (ids["fisso"], COMPRA, VENDE, adesso, adesso))
    con.commit()
    con.close()
    return ids


def riga(aid):
    con = db()
    r = con.execute("SELECT * FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return dict(r) if r else {}


def tariffa(aid):
    r = riga(aid)
    return (r.get("spedizione_sats"), r.get("spedizione_eur"))


def zone(aid):
    return json.loads(riga(aid).get("spedizione_zone") or "{}")


def fotografia():
    """Tutto quel che un'anteprima NON deve toccare, byte per byte."""
    con = db()
    f = ([tuple(x) for x in con.execute("SELECT * FROM annunci ORDER BY id")],
         [tuple(x) for x in con.execute(
             "SELECT tg_id, spedizione_standard FROM utenti ORDER BY tg_id")],
         [tuple(x) for x in con.execute("SELECT * FROM ordini ORDER BY id")])
    con.close()
    return f


def standard_salvato():
    con = db()
    r = con.execute("SELECT spedizione_standard FROM utenti WHERE tg_id=?",
                    (VENDE,)).fetchone()
    con.close()
    return banco.SRV.spedizione_standard_leggi(r["spedizione_standard"])


def main():
    print("=" * 58)
    print("  IL COSTO DI SPEDIZIONE STANDARD — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    banco.come(VENDE)

    # LA MODERAZIONE NON DEVE MAI ESSERE CHIAMATA: la si sostituisce con
    # un registro che, se qualcuno la chiama, lo dice
    async def modera(*a, **k):
        MODERATI.append(("ai", a))
        return None

    def vietato(*a, **k):
        MODERATI.append(("parole", a))
        return ""
    SRV.moderazione_ai = modera
    SRV.controlla_vietato = vietato
    ids = semina()

    # ---------------------------------------------------------------
    print("\n[il Salva del cassetto porta lo standard]")
    r = c.post("/api/me/spedizioniere", json={
        "spedizionieri": ["InPost"],
        "spedizione_standard": {"valuta": "sats", "casa": "5000",
                                "extra": "500"}})
    prova("il Salva risponde 200", 200, r.status_code)
    prova("...e rimanda lo standard normalizzato",
          {"valuta": "sats", "casa": 5000, "extra": 500},
          r.json().get("spedizione_standard"))
    prova("...con le reti di sempre", ["InPost"], r.json().get("spedizionieri"))
    me = c.get("/api/me")
    prova("/api/me risponde", 200, me.status_code)
    prova("...e consegna lo standard gia' letto (un oggetto, non la stringa)",
          {"valuta": "sats", "casa": 5000, "extra": 500},
          me.json().get("spedizione_standard"))
    r = c.post("/api/me/spedizioniere", json={
        "spedizione_standard": {"valuta": "sats", "casa": "5.000"}})
    prova("«5.000» in sats: 400, e il perche'", (400, True),
          (r.status_code, "senza punti" in r.json().get("detail", "")))
    prova("...e il rifiuto non ha scritto niente",
          {"valuta": "sats", "casa": 5000, "extra": 500}, standard_salvato())
    r = c.post("/api/me/spedizioniere", json={
        "spedizione_standard": {"valuta": "sats", "casa": "", "punto": "3"}})
    prova("il punto senza la casa: 400, e il perche'", (400, True),
          (r.status_code, "Scrivi prima" in r.json().get("detail", "")))
    r = c.post("/api/me/spedizioniere", json={
        "spedizione_standard": {"valuta": "eur", "casa": "4,50"}})
    prova("un corpo senza reti salva lo standard...",
          {"valuta": "eur", "casa": 4.5}, r.json().get("spedizione_standard"))
    prova("...e le reti restano com'erano", ["InPost"],
          r.json().get("spedizionieri"))
    r = c.post("/api/me/spedizioniere",
               json={"spedizionieri": ["InPost", "Poste Italiane"]})
    prova("il client di IERI (senza la chiave) non cancella lo standard",
          {"valuta": "eur", "casa": 4.5}, r.json().get("spedizione_standard"))
    prova("...e le sue reti si scrivono come sempre",
          ["InPost", "Poste Italiane"], r.json().get("spedizionieri"))
    r = c.post("/api/me/spedizioniere", json={
        "spedizione_standard": {"valuta": "sats", "casa": ""}})
    prova("la casella vuota lo toglie", None,
          r.json().get("spedizione_standard"))
    r = c.post("/api/me/spedizione-standard/anteprima", json={})
    prova("senza standard, l'anteprima dice cosa fare", (400, True),
          (r.status_code, "Scrivi prima" in r.json().get("detail", "")))
    c.post("/api/me/spedizioniere", json={
        "spedizione_standard": {"valuta": "sats", "casa": "5000"}})

    # ---------------------------------------------------------------
    print("\n[l'anteprima: chi cambia, chi resta, e non scrive niente]")
    prima = fotografia()
    r = c.post("/api/me/spedizione-standard/anteprima", json={})
    d = r.json()
    prova("l'anteprima col costo salvato risponde 200", 200, r.status_code)
    idonei = {ids[k] for k in ("fisso", "ancorato", "euro", "entrambe")}
    prova("cambiano gli idonei, e SOLO loro", idonei,
          {v["id"] for v in d.get("cambiano", [])})
    attesi = {ids["gratis"]: "gratis", ids["ritiro"]: "ritiro",
              ids["digitale"]: "digitale", ids["revisione"]: "revisione",
              ids["nostr"]: "nostr", ids["shopify"]: "negozio",
              ids["ordine"]: "ordine", ids["set"]: "ordine",
              ids["uguale"]: "uguale", ids["no_casa"]: "no_casa",
              ids["asta"]: "asta"}
    prova("...e chi resta com'era lo dice col suo motivo", attesi,
          {v["id"]: v["motivo"] for v in d.get("fuori", [])})
    prova("il negozio collegato si nomina", "Shopify",
          next((v.get("origine") for v in d.get("fuori", [])
                if v["id"] == ids["shopify"]), None))
    prova("l'articolo di un ALTRO venditore non compare da nessuna parte",
          False, ids["altrui"] in {v["id"] for v in
                                   d.get("cambiano", []) + d.get("fuori", [])})
    prova("gli esauriti si contano e basta", 1, d.get("esauriti"))
    per_id = {v["id"]: v for v in d.get("cambiano", [])}
    prova("il listino in euro col costo in sats: tradotto, e detto",
          (True, [5000, 5.0]), (per_id.get(ids["euro"], {}).get("convertito"),
                                per_id.get(ids["euro"], {}).get("dopo", {})
                                .get("casa")))
    prova("l'estero copiato dalla casa di ieri e' DIVERSO, e lo si dice",
          True, per_id.get(ids["fisso"], {}).get("estero_diverso"))
    prova("...da quanto a quanto", ([3000, 0.0], [5000, 0.0]),
          (per_id.get(ids["fisso"], {}).get("prima", {}).get("casa"),
           per_id.get(ids["fisso"], {}).get("dopo", {}).get("casa")))
    prova("le chiavi di servizio non escono verso il client", False,
          any(k.startswith("_") for v in d.get("cambiano", []) for k in v))
    prova("l'anteprima NON ha scritto niente, standard compreso", prima,
          fotografia())
    r = c.post("/api/me/spedizione-standard/anteprima", json={
        "spedizione_standard": {"valuta": "sats", "casa": "9999"}})
    prova("...nemmeno quando le si fa provare un costo nuovo", (200, prima),
          (r.status_code, fotografia()))

    # ---------------------------------------------------------------
    print("\n[l'applicazione: i soli idonei, niente moderazione]")
    moderazioni = db().execute("SELECT COUNT(*) FROM moderazione_log") \
        .fetchone()[0]
    ordini_prima = prima[2]
    r = c.post("/api/me/spedizione-standard/applica", json={})
    d = r.json()
    prova("l'applicazione risponde 200", 200, r.status_code)
    prova("...e ne aggiorna quattro", 4, d.get("aggiornati"))
    prova("il fisso: 5000 sats", (5000, 0.0), tariffa(ids["fisso"]))
    prova("...la copia di casa nella mappa, l'estero COM'ERA",
          {"dom": {"sats": 5000, "eur": 0.0}, "eu": {"sats": 3000, "eur": 0.0}},
          zone(ids["fisso"]))
    prova("l'ancorato all'euro diventa fisso in sats (lo standard e' in sats)",
          (5000, 0.0), tariffa(ids["ancorato"]))
    prova("il listino in euro: 5,00 € e l'equivalente al cambio",
          (5000, 5.0), tariffa(ids["euro"]))
    prova("spedizione + ritiro: la casa cambia...", (5000, 0.0),
          tariffa(ids["entrambe"]))
    prova("...e il punto dichiarato resta suo (lo standard non lo dice)",
          (1500, 1), (riga(ids["entrambe"])["spedizione_punto_sats"],
                      riga(ids["entrambe"])["spedizione_punto_dichiarata"]))
    prova("...e la mappa vuota prende la sola casa",
          {"dom": {"sats": 5000, "eur": 0.0}}, zone(ids["entrambe"]))
    r_f = riga(ids["fisso"])
    prova("testo, stato e prezzo restano quelli di prima",
          ("Articolo fisso", "descrizione", "attivo", 30_000),
          (r_f["titolo"], r_f["descrizione"], r_f["stato"], r_f["prezzo_sats"]))
    prova("...e la data di «aggiornato» si scrive", True, r_f["modificato"] > 0)
    fuori = {v["id"] for v in d.get("fuori", [])}
    prova("gli esclusi restano BYTE PER BYTE com'erano", True,
          all(tuple(x) in prima[0] for x in db().execute(
              "SELECT * FROM annunci WHERE id IN (%s)"
              % ",".join(str(i) for i in fuori | {ids["altrui"],
                                                   ids["esaurito"]}))))
    prova("gli ordini non si toccano (la spedizione e' quella di quando "
          "sono nati)", ordini_prima, fotografia()[2])
    prova("NESSUNA chiamata alla moderazione", [], MODERATI)
    prova("...e nessuna riga nuova nel suo registro", moderazioni,
          db().execute("SELECT COUNT(*) FROM moderazione_log").fetchone()[0])
    prova("lo standard salvato non si e' mosso (non arrivava dal corpo)",
          {"valuta": "sats", "casa": 5000}, standard_salvato())
    r = c.post("/api/me/spedizione-standard/applica", json={})
    prova("rifatto subito: nessuno da aggiornare (e' idempotente)",
          0, r.json().get("aggiornati"))
    prova("...e i quattro ora sono «gia' con questo costo»", True,
          all(v["motivo"] == "uguale" for v in r.json().get("fuori", [])
              if v["id"] in idonei))

    # ---------------------------------------------------------------
    print("\n[lo standard in euro, dal corpo, coi tre costi]")
    r = c.post("/api/me/spedizione-standard/applica", json={
        "spedizione_standard": {"valuta": "eur", "casa": "4,50",
                                "punto": "3,90", "extra": "1"}})
    d = r.json()
    prova("risponde 200 e aggiorna anche chi era gia' a 5000 sats",
          (200, 5), (r.status_code, d.get("aggiornati")))
    prova("listino sats: la casa ANCORATA all'euro", (0, 4.5),
          tariffa(ids["fisso"]))
    rf = riga(ids["fisso"])
    prova("...il punto dichiarato e il supplemento, ancorati",
          (0, 3.9, 1, 0, 1.0),
          (rf["spedizione_punto_sats"], rf["spedizione_punto_eur"],
           rf["spedizione_punto_dichiarata"], rf["spedizione_extra_sats"],
           rf["spedizione_extra_eur"]))
    prova("...e l'estero ancora com'era",
          {"dom": {"sats": 0, "eur": 4.5}, "eu": {"sats": 3000, "eur": 0.0}},
          zone(ids["fisso"]))
    re_ = riga(ids["euro"])
    prova("listino euro: euro e equivalenti al cambio, i tre costi",
          (4500, 4.5, 3900, 3.9, 1, 1000, 1.0),
          (re_["spedizione_sats"], re_["spedizione_eur"],
           re_["spedizione_punto_sats"], re_["spedizione_punto_eur"],
           re_["spedizione_punto_dichiarata"], re_["spedizione_extra_sats"],
           re_["spedizione_extra_eur"]))
    prova("lo standard arrivato dal corpo si salva insieme",
          {"valuta": "eur", "casa": 4.5, "punto": 3.9, "extra": 1.0},
          standard_salvato())
    prova("ancora nessuna moderazione", [], MODERATI)

    # ---------------------------------------------------------------
    print("\n[la corsa: chi compra a meta' lascia l'articolo com'era]")
    vero_giro = SRV._sped_std_giro

    async def giro_poi_compra(tg, std):
        piano = await vero_giro(tg, std)
        adesso = int(time.time())
        con = db()
        con.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,quantita,stato,consegna_scelta,spedizione_sats,"
            "creato,aggiornato) VALUES(?,?,?,30000,1,'creato','spedizione',"
            "0,?,?)", (ids["fisso"], COMPRA, VENDE, adesso, adesso))
        con.execute("UPDATE annunci SET spedizione_eur=4.0 WHERE id=?",
                    (ids["ancorato"],))
        con.commit()
        con.close()
        return piano
    SRV._sped_std_giro = giro_poi_compra
    try:
        r = c.post("/api/me/spedizione-standard/applica", json={
            "spedizione_standard": {"valuta": "sats", "casa": "7000"}})
    finally:
        SRV._sped_std_giro = vero_giro
    d = r.json()
    motivi = {v["id"]: v["motivo"] for v in d.get("fuori", [])}
    prova("l'ordine arrivato fra il piano e la scrittura: resta fuori",
          "ordine", motivi.get(ids["fisso"]))
    prova("...e il suo articolo e' quello che il compratore ha visto",
          (0, 4.5), tariffa(ids["fisso"]))
    prova("la riga cambiata sotto i piedi: «cambiato», e resta la sua",
          ("cambiato", (0, 4.0)), (motivi.get(ids["ancorato"]),
                                   tariffa(ids["ancorato"])))
    prova("gli altri si aggiornano lo stesso", (7000, 0.0),
          tariffa(ids["entrambe"]))

    # ---------------------------------------------------------------
    print("\n[i relay: a lotti, un giro per venditore]")
    async def rilancia(aid, status, solo_aggiornamento=False):
        RELAY.append((aid, status, solo_aggiornamento))
        await asyncio.sleep(0)
    vero_nostr, vero_rilancio = SRV._NOSTR, SRV.annuncio_su_nostr
    vera_pausa, vero_lotto = SRV.PAUSA_NOSTR, SRV.LOTTO_NOSTR
    SRV.annuncio_su_nostr = rilancia
    SRV.PAUSA_NOSTR, SRV.LOTTO_NOSTR = 0, 5
    try:
        SRV._NOSTR = None
        asyncio.run(SRV._sped_std_su_nostr(VENDE, [1, 2, 3]))
        prova("senza la chiave della piattaforma: nessun rilancio", [], RELAY)
        SRV._NOSTR = ("collaudo", "collaudo")
        asyncio.run(SRV._sped_std_su_nostr(VENDE, list(range(1, 13))))
        prova("dodici articoli: dodici rilanci, uno a testa",
              list(range(1, 13)), sorted(x[0] for x in RELAY))
        prova("...tutti come aggiornamento di un evento che c'e' gia'",
              {("active", True)}, {(x[1], x[2]) for x in RELAY})
        RELAY.clear()

        async def due_giri():
            primo = asyncio.create_task(
                SRV._sped_std_su_nostr(VENDE, [1, 2, 3, 4, 5, 6, 7]))
            await asyncio.sleep(0)
            await SRV._sped_std_su_nostr(VENDE, [7, 8, 20])
            prova("...il secondo giro si ACCODA e torna subito", True,
                  VENDE in SRV._SPED_STD_NOSTR)
            await primo
        asyncio.run(due_giri())
        prova("il bottone ripremuto a meta': ogni articolo una volta sola",
              [1, 2, 3, 4, 5, 6, 7, 8, 20], sorted(x[0] for x in RELAY))
        prova("...e a giro finito la coda si chiude", {},
              SRV._SPED_STD_NOSTR)
    finally:
        SRV._NOSTR, SRV.annuncio_su_nostr = vero_nostr, vero_rilancio
        SRV.PAUSA_NOSTR, SRV.LOTTO_NOSTR = vera_pausa, vero_lotto

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
