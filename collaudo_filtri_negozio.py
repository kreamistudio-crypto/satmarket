# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL FILTRO DEL CATALOGO (21 nov 2026).

Da Andrea: «quando integriamo un servizio su WooCommerce o Shopify devo
poter filtrare certi prodotti o categorie o comunque escluderle in un
secondo momento: Barattolo e questi shop sincronizzati, ma che si
possano comunque customizzare». E la sua scelta sul bottone: «elimina»
su un annuncio di un negozio collegato lo ESCLUDE, e si riaccoglie.

`prove.py` fa girare il giudice (`entra_nel_filtro`) a pezzi; qui gira
il SERVER VERO su un database usa-e-getta — le rotte del cassetto, la
migrazione, il giro dell'ora con `_un_connettore`, la traduzione, la
moderazione (di cartone) e la riconciliazione vere — con un WooCommerce
di cartone. Le domande:
  · un negozio collegato IERI non cambia niente: filtro vuoto, gia'
    scelto, entra tutto come prima;
  · «tutto tranne» una categoria: chi ne fa parte va in PANCHINA
    ('escluso', non 'rimosso') e gli altri restano;
  · il prodotto vince sulla categoria: riaccolto torna LO STESSO
    annuncio (stesso id);
  · «solo questi» per tag;
  · «elimina» dalla lista dei propri annunci = panchina + eccezione nel
    filtro, e il giro dopo non lo rimette dentro;
  · la bozza sul negozio = panchina, e ripubblicato torna;
  · il prodotto escluso che sparisce dal negozio diventa la lapide;
  · un negozio NUOVO col cassetto di oggi aspetta la prima scelta: il
    giro fotografa il catalogo e non fa entrare niente finche' il
    venditore non salva il filtro.

IL NEGOZIO NON SI CHIAMA MAI: la prova del collegamento e le risposte
dell'API sono di cartone, e in CI lo garantisce la gabbia di
`collaudi_ci.py`.

USO:  python collaudo_filtri_negozio.py
"""

import asyncio
import json
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
VENDE = 333
NEGOZIO = "https://bottega.test"
CATALOGO = []


def prodotto(pid, nome, categorie=(), tag=(), stato="publish"):
    return {"id": pid, "name": nome, "description": "<p>Bello</p>",
            "type": "simple", "status": stato,
            "catalog_visibility": "visible",
            "price": "12.00", "regular_price": "12.00", "manage_stock": True,
            "stock_quantity": 3, "stock_status": "instock",
            "images": [{"src": f"https://bottega.test/{pid}.jpg"}],
            "categories": [{"id": n, "name": c}
                           for n, c in enumerate(categorie, 1)],
            "tags": [{"id": n, "name": t} for n, t in enumerate(tag, 1)]}


def api_finta(metodo, url, intestazioni):
    """Il WooCommerce di cartone: le impostazioni dell'IVA (prezzi gia'
    finiti) e una pagina di catalogo."""
    if url.endswith("/settings/general"):
        return 200, {"lista": [{"id": "woocommerce_calc_taxes",
                                "value": "yes"}]}, {}
    if url.endswith("/settings/tax"):
        return 200, {"lista": [{"id": "woocommerce_prices_include_tax",
                                "value": "yes"}]}, {}
    pagina = 1 if "page=1" in url.split("per_page")[-1] else 2
    return 200, {"lista": CATALOGO if pagina == 1 else []}, \
        {"X-WP-Total": str(len(CATALOGO))}


def righe(cid):
    """{chiave: (id, stato)} degli annunci del collegamento."""
    con = banco.SRV.db()
    fuori = {r["origine_chiave"]: (r["id"], r["stato"]) for r in con.execute(
        "SELECT id, origine_chiave, stato FROM annunci WHERE connettore_id=? "
        "ORDER BY id", (cid,))}
    con.close()
    return fuori


def stati(cid):
    return {k: v[1] for k, v in righe(cid).items()}


def connettore(cid):
    con = banco.SRV.db()
    r = dict(con.execute("SELECT * FROM connettori WHERE id=?",
                         (cid,)).fetchone())
    con.close()
    return r


def giro(cid):
    """Il giro dell'ora sul solo collegamento `cid`, col modulo vero."""
    import importa_negozio
    asyncio.run(banco.SRV._un_connettore(connettore(cid),
                                         {"EUR": 100_000.0},
                                         importa_negozio))


def main():
    print("=" * 58)
    print("  IL FILTRO DEL CATALOGO — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    SRV.CONNETTORI_NEGOZIO_APERTI = True
    SRV.chiama_api_negozio = api_finta
    SRV._salva_foto_connettore = lambda annuncio_id, indice, url: None
    giudicati = []

    async def prova_negozio(fonte, url, credenziali):
        return None

    async def lotto_finto(voci):
        giudicati.extend(t for _, t, _ in voci)
        return {}

    partiti = []

    def sync_uno(cid):
        partiti.append(cid)

        async def niente():
            return None
        return niente()
    SRV._prova_negozio = prova_negozio
    SRV._sync_uno = sync_uno
    SRV.moderazione_ai_lotto = lotto_finto

    # UN NEGOZIO COLLEGATO IERI, com'era: la riga senza le colonne nuove
    # nel suo INSERT, cioe' coi default che la migrazione le da'
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(?,?,?,1)", (VENDE, "Vende", "bottega"))
    cid = con.execute(
        "INSERT INTO connettori(tg_id,fonte,url_negozio,credenziali,"
        "consegna,zona,creato) VALUES(?,'woo',?,"
        "'plain:{\"consumer_key\": \"ck_x\", \"consumer_secret\": \"cs_x\"}',"
        "'ritiro','Pavia (PV)',?)", (VENDE, NEGOZIO, int(time.time()))
    ).lastrowid
    con.commit()
    con.close()
    banco.come(VENDE)

    # ---------------------------------------------------------------
    print("\n[il negozio di ieri non cambia]")
    lista = c.get("/api/me/connettori").json().get("connettori") or []
    prova("filtro gia' scelto, modo «tutto», nessuna regola",
          [(True, "tutto", 0, 0)],
          [(x.get("filtro_scelto"), x.get("filtro_modo"),
            x.get("filtro_regole"), x.get("in_panchina")) for x in lista])
    CATALOGO[:] = [prodotto(1, "Miele di acacia", ["Alimenti"], ["bio"]),
                   prodotto(2, "Maglia di lana", ["Abbigliamento"]),
                   prodotto(3, "Cappello", ["Abbigliamento"], ["bio"]),
                   prodotto(4, "Jade usato", ["Bitcoin"], ["usato"])]
    giro(cid)
    prova("entra tutto, come prima", {"1": "attivo", "2": "attivo",
                                      "3": "attivo", "4": "attivo"},
          stati(cid))
    foto = json.loads(connettore(cid)["catalogo_visto"] or "{}")
    prova("...e il catalogo e' fotografato per il cassetto",
          ({"Abbigliamento": 2, "Alimenti": 1, "Bitcoin": 1},
           {"bio": 2, "usato": 1}, 4),
          ({n: k for n, k in foto.get("categorie", [])},
           {n: k for n, k in foto.get("tag", [])},
           len(foto.get("prodotti", []))))
    id_cappello = righe(cid)["3"][0]

    # ---------------------------------------------------------------
    print("\n[«tutto tranne» una categoria]")
    r = c.post(f"/api/me/connettori/{cid}/filtro",
               json={"filtro": {"modo": "tutto",
                                "categorie": ["abbigliamento "]}})
    prova("salvato: due prodotti resterebbero fuori, il giro parte",
          (200, 2, 4, True),
          (r.status_code, r.json().get("fuori"), r.json().get("totale"),
           r.json().get("giro_partito")))
    giudicati.clear()
    giro(cid)
    prova("maglia e cappello in panchina (non lapide), gli altri restano",
          {"1": "attivo", "2": "escluso", "3": "escluso", "4": "attivo"},
          stati(cid))
    prova("...e il report lo dice", (2, 2),
          (json.loads(connettore(cid)["ultimo_esito"]).get("in_panchina"),
           json.loads(connettore(cid)["ultimo_esito"]).get("esclusi")))
    prova("...senza chiedere niente alla moderazione", [], giudicati)
    lista = c.get("/api/me/connettori").json()["connettori"]
    prova("il cassetto conta la panchina", (2, 1),
          (lista[0]["in_panchina"], lista[0]["filtro_regole"]))
    miei = c.get("/api/listings/miei").json()
    prova("«I tuoi annunci» non li mostra", {"Miele di acacia",
                                            "Jade usato"},
          {a["titolo"] for a in (miei if isinstance(miei, list)
                                 else miei.get("annunci", []))})
    prova("la scheda pubblica risponde 404", 404,
          c.get(f"/api/listings/{id_cappello}").status_code)

    # ---------------------------------------------------------------
    print("\n[il prodotto vince sulla categoria: si riaccoglie]")
    d = c.get(f"/api/me/connettori/{cid}/filtro").json()
    prova("la panchina si legge col prodotto di ognuno",
          {"Cappello": "3", "Maglia di lana": "2"},
          {a["titolo"]: a["prodotto"] for a in d["panchina"]})
    filtro = d["filtro"]
    filtro["prodotti_dentro"] = ["3"]
    c.post(f"/api/me/connettori/{cid}/filtro", json={"filtro": filtro})
    giudicati.clear()
    giro(cid)
    prova("il cappello torna, la maglia resta fuori",
          {"1": "attivo", "2": "escluso", "3": "attivo", "4": "attivo"},
          stati(cid))
    prova("...ed e' LO STESSO annuncio", id_cappello, righe(cid)["3"][0])
    prova("...passato da un giudizio fresco (e solo lui)", ["Cappello"],
          giudicati)
    prova("...e il report lo conta fra i riaccolti", 1,
          json.loads(connettore(cid)["ultimo_esito"]).get("riaccolti"))

    # ---------------------------------------------------------------
    print("\n[«solo questi», per tag]")
    c.post(f"/api/me/connettori/{cid}/filtro",
           json={"filtro": {"modo": "solo", "tag": ["bio"],
                            "prodotti_dentro": []}})
    giro(cid)
    prova("entra solo il «bio»",
          {"1": "attivo", "2": "escluso", "3": "attivo", "4": "escluso"},
          stati(cid))
    r = c.post(f"/api/me/connettori/{cid}/filtro",
               json={"filtro": {"modo": "qualcosa"}})
    prova("un modo sconosciuto si rifiuta e non tocca niente",
          (400, "solo"), (r.status_code,
                          json.loads(connettore(cid)["filtro_regole"])["modo"]))

    # ---------------------------------------------------------------
    print("\n[«elimina» su un annuncio del negozio = panchina]")
    id_miele = righe(cid)["1"][0]
    r = c.post(f"/api/listings/{id_miele}/rimuovi")
    prova("la rotta risponde e dice che e' un'esclusione", (200, True),
          (r.status_code, r.json().get("escluso")))
    prova("il miele e' in panchina, non lapide", "escluso",
          stati(cid)["1"])
    prova("...e il suo prodotto e' fra le eccezioni del filtro", ["1"],
          json.loads(connettore(cid)["filtro_regole"])["prodotti_fuori"])
    giro(cid)
    prova("il giro dopo non lo rimette dentro", "escluso", stati(cid)["1"])

    # ---------------------------------------------------------------
    print("\n[la bozza sul negozio va in panchina, e torna]")
    c.post(f"/api/me/connettori/{cid}/filtro",
           json={"filtro": {"modo": "tutto"}})
    giro(cid)
    prova("filtro vuoto: rientrano tutti", {"1": "attivo", "2": "attivo",
                                           "3": "attivo", "4": "attivo"},
          stati(cid))
    id_jade = righe(cid)["4"][0]
    CATALOGO[3] = prodotto(4, "Jade usato", ["Bitcoin"], ["usato"],
                           stato="draft")
    giro(cid)
    prova("messo in bozza sul negozio: panchina e non lapide", "escluso",
          stati(cid)["4"])
    CATALOGO[3] = prodotto(4, "Jade usato", ["Bitcoin"], ["usato"])
    giro(cid)
    prova("ripubblicato: torna lo stesso annuncio", (id_jade, "attivo"),
          righe(cid)["4"])

    # ---------------------------------------------------------------
    print("\n[l'escluso che sparisce dal negozio]")
    c.post(f"/api/me/connettori/{cid}/filtro",
           json={"filtro": {"modo": "tutto", "prodotti_fuori": ["2"]}})
    giro(cid)
    prova("la maglia esclusa a mano", "escluso", stati(cid)["2"])
    del CATALOGO[1]
    giro(cid)
    prova("tolta dal negozio: adesso e' la lapide", "rimosso",
          stati(cid)["2"])

    # ---------------------------------------------------------------
    print("\n[un negozio nuovo aspetta la prima scelta]")
    r = c.post("/api/me/connettori",
               json={"fonte": "woo", "url_negozio": "https://nuovo.test",
                     "consegna": "ritiro", "zona": "Pavia (PV)",
                     "credenziali": {"consumer_key": "ck_y",
                                     "consumer_secret": "cs_y"},
                     "scegli_prima": True})
    prova("collegato, e in attesa della scelta", (200, False),
          (r.status_code, (r.json().get("connettore") or {})
           .get("filtro_scelto")))
    nuovo = r.json()["connettore"]["id"]
    giro(nuovo)
    prova("il giro fotografa ma non fa entrare niente", {}, stati(nuovo))
    d = c.get(f"/api/me/connettori/{nuovo}/filtro").json()
    prova("...e il cassetto ha le categorie per scegliere",
          (False, {"Alimenti", "Abbigliamento", "Bitcoin"}),
          (d["filtro_scelto"], {n for n, _ in d["catalogo"]["categorie"]}))
    prova("...e la riga dice che aspetta la scelta", True,
          json.loads(connettore(nuovo)["ultimo_esito"]).get(
              "in_attesa_scelta"))
    r = c.post(f"/api/me/connettori/{nuovo}/filtro",
               json={"filtro": {"modo": "solo",
                                "categorie": ["Abbigliamento"]}})
    prova("la scelta apre la porta", (200, True),
          (r.status_code, r.json()["connettore"]["filtro_scelto"]))
    giro(nuovo)
    prova("entra solo quel che ha scelto", {"3": "attivo"}, stati(nuovo))
    r = c.post("/api/me/connettori",
               json={"fonte": "woo", "url_negozio": "https://ieri.test",
                     "consegna": "ritiro", "zona": "Pavia (PV)",
                     "credenziali": {"consumer_key": "ck_z",
                                     "consumer_secret": "cs_z"}})
    prova("un client di ieri (senza `scegli_prima`) entra tutto subito",
          (200, True), (r.status_code, (r.json().get("connettore") or {})
                        .get("filtro_scelto")))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
