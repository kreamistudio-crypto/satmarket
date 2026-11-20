# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CATEGORIA DI UN NEGOZIO COLLEGATO (16 nov 2026).

Da Andrea: «l'importazione WooCommerce inserisce di default nella
categoria Altro; se tutti gli articoli sono di una categoria sola
sarebbe utile poterla dichiarare nella configurazione del collegamento
(anche per Shopify)». Fino a ieri il traduttore leggeva la categoria del
negozio e nessuno la usava: ogni prodotto nasceva in «Altro».

`prove.py` fa girare i giudici uno per uno; qui gira il SERVER VERO su
un database usa-e-getta — la rotta del cassetto, la migrazione, il giro
dell'ora con `_un_connettore`, la traduzione e la riconciliazione vere —
con un WooCommerce di cartone. Le domande:
  · un negozio collegato IERI, senza la colonna nel suo INSERT, si legge
    come «decide il negozio» e nessun annuncio cambia casella da solo;
  · senza dichiarazione decide il negozio, ma solo quando il suo nome
    combacia per intero con una nostra categoria («Accessori Bitcoin»
    resta in «Altro»);
  · la categoria dichiarata nel cassetto scende SUBITO su tutti gli
    annunci vivi del negozio, e vale per quelli che nasceranno;
  · un client vecchio (senza la chiave) non la cancella; un nome fuori
    catalogo si rifiuta e non tocca niente;
  · tornare a «decide il negozio» rimette in «Altro» le righe della
    dichiarazione, e il giro dopo le porta dove dice il negozio — ma chi
    un moderatore ha spostato resta dov'e'.
  · (20 nov 2026) se cassetto e negozio tacciono decide il NOME del
    prodotto: i biscotti di un WooCommerce senza categorie nascono negli
    alimenti, e quelli gia' entrati in «Altro» ne escono al giro dopo.

IL NEGOZIO NON SI CHIAMA MAI: la prova del collegamento e le risposte
dell'API sono di cartone, e in CI lo garantisce la gabbia di
`collaudi_ci.py`.

USO:  python collaudo_categoria_negozio.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
VENDE = 333
NEGOZIO = "https://miele.test"
CATALOGO = []


def prodotto(pid, nome, *categorie):
    return {"id": pid, "name": nome, "description": "<p>Buono</p>",
            "type": "simple", "status": "publish",
            "catalog_visibility": "visible",
            "price": "7.50", "regular_price": "7.50", "manage_stock": True,
            "stock_quantity": 4, "stock_status": "instock",
            "images": [{"src": f"https://miele.test/{pid}.jpg"}],
            "categories": [{"id": n, "name": c}
                           for n, c in enumerate(categorie, 1)]}


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


def categorie(cid):
    con = banco.SRV.db()
    righe = {r["origine_chiave"]: r["categoria"] for r in con.execute(
        "SELECT origine_chiave, categoria FROM annunci WHERE connettore_id=? "
        "ORDER BY id", (cid,))}
    con.close()
    return righe


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
    print("  LA CATEGORIA DI UN NEGOZIO COLLEGATO — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    SRV.CONNETTORI_NEGOZIO_APERTI = True
    SRV.chiama_api_negozio = api_finta
    SRV._salva_foto_connettore = lambda annuncio_id, indice, url: None

    async def prova_negozio(fonte, url, credenziali):
        return None

    async def lotto_finto(voci):
        return {}

    def sync_uno(cid):
        async def niente():
            return None
        return niente()
    SRV._prova_negozio = prova_negozio
    SRV._sync_uno = sync_uno
    SRV.moderazione_ai_lotto = lotto_finto

    # UN NEGOZIO COLLEGATO IERI, com'era: la riga senza la colonna nuova
    # nel suo INSERT, cioe' col default che la migrazione le da'
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(?,?,?,1)", (VENDE, "Vende", "miele"))
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
    print("\n[senza dichiarazione decide il negozio, stretto]")
    lista = c.get("/api/me/connettori").json().get("connettori") or []
    prova("il negozio di ieri si legge «decide il negozio»", [""],
          [x.get("categoria") for x in lista])
    CATALOGO[:] = [prodotto(1, "Jade", "Uncategorized", "Bitcoin"),
                   prodotto(2, "Barattolo di miele", "Senza categoria"),
                   prodotto(3, "Cover per Jade", "Accessori Bitcoin"),
                   prodotto(4, "Vaso", "Casa &amp; Giardino")]
    giro(cid)
    prova("ognuno dove dice il negozio, il dubbio in «Altro»",
          {"1": "Bitcoin", "2": "Altro", "3": "Altro",
           "4": "Casa e giardino"}, categorie(cid))

    # ---------------------------------------------------------------
    print("\n[la categoria dichiarata nel cassetto]")
    corpo = {"id": cid, "fonte": "woo", "url_negozio": NEGOZIO,
             "consegna": "ritiro", "zona": "Pavia (PV)"}
    r = c.post("/api/me/connettori", json={**corpo, "categoria": "Cose belle"})
    prova("un nome fuori catalogo si rifiuta", 400, r.status_code)
    prova("...e non tocca niente", ("", "Bitcoin"),
          (connettore(cid)["categoria"], categorie(cid)["1"]))
    r = c.post("/api/me/connettori",
               json={**corpo, "categoria": "Alimenti e bevande"})
    prova("dichiarata: il cassetto la salva e la rilegge",
          (200, "Alimenti e bevande"),
          (r.status_code, (r.json().get("connettore") or {}).get("categoria")))
    prova("...e scende SUBITO su tutti gli annunci del negozio",
          {"1": "Alimenti e bevande", "2": "Alimenti e bevande",
           "3": "Alimenti e bevande", "4": "Alimenti e bevande"},
          categorie(cid))
    prova("...dicendo quanti ne ha spostati", 4,
          r.json().get("categoria_spostati"))
    CATALOGO.append(prodotto(5, "Melata", "Bitcoin"))
    giro(cid)
    prova("chi nasce dopo prende la categoria dichiarata",
          "Alimenti e bevande", categorie(cid).get("5"))
    r = c.post("/api/me/connettori", json=corpo)      # il client di ieri
    prova("un client senza la chiave non la cancella",
          (200, "Alimenti e bevande", None),
          (r.status_code, connettore(cid)["categoria"],
           r.json().get("categoria_spostati")))

    # ---------------------------------------------------------------
    print("\n[si torna a «decide il negozio»]")
    con = SRV.db()
    con.execute("UPDATE annunci SET categoria='Collezionismo' "
                "WHERE connettore_id=? AND origine_chiave='3'", (cid,))
    con.commit()                                    # un moderatore
    con.close()
    r = c.post("/api/me/connettori", json={**corpo, "categoria": ""})
    prova("le righe della dichiarazione tornano in «Altro», il moderatore "
          "resta", (200, {"1": "Altro", "2": "Altro", "3": "Collezionismo",
                          "4": "Altro", "5": "Altro"}),
          (r.status_code, categorie(cid)))
    giro(cid)
    prova("...e il giro dopo le rimette dove dice il negozio",
          {"1": "Bitcoin", "2": "Altro", "3": "Collezionismo",
           "4": "Casa e giardino", "5": "Bitcoin"}, categorie(cid))

    # ---------------------------------------------------------------
    # (20 nov 2026, Luca di «Un tempo per te»: un WooCommerce senza
    # categorie, e i biscotti in «Altro»)
    print("\n[il nome del prodotto, quando cassetto e negozio tacciono]")
    CATALOGO.append(prodotto(6, "Augurelli Biscotti farciti con "
                                "cioccolato al latte veg",
                             "Senza categoria"))
    giro(cid)
    prova("un prodotto nuovo coi biscotti nel nome nasce negli alimenti",
          "Alimenti e bevande", categorie(cid).get("6"))
    con = SRV.db()
    con.execute("UPDATE annunci SET categoria='Altro' "
                "WHERE connettore_id=? AND origine_chiave='6'", (cid,))
    con.commit()                        # com'era prima di oggi
    con.close()
    giro(cid)
    prova("quello gia' entrato in «Altro» ci esce al giro dopo, gli altri "
          "fermi", {"1": "Bitcoin", "2": "Altro", "3": "Collezionismo",
                    "4": "Casa e giardino", "5": "Bitcoin",
                    "6": "Alimenti e bevande"}, categorie(cid))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
