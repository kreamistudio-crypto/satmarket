# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CACCIA A TAPPO (17 nov 2026, richiesta di Andrea: «un
gioco di barattolo con dentro Tappo... bello complesso, deve durare anche
tra vent'anni... una mappa, un inventario»). Il SERVER VERO su un
database usa-e-getta:
  · a leva spenta il gioco non esiste (404), e /api/me non accende la voce;
  · la dispensa: sei scaffali, il corredo nello zaino, nessuna caccia
    finche' non si sceglie lo scaffale;
  · la caccia parte una volta al giorno, sullo scaffale e al grado scelti
    (un grado chiuso e uno scaffale vuoto sono un 400);
  · IL NASCONDIGLIO NON ESCE dal server finche' non e' trovato;
  · le occhiate: il proprio annuncio e uno che non c'e' non costano, una
    sbagliata si' e dice «acqua»/«tiepido»/«fuochino» ai gradi col calore;
  · gli indizi pagati abbassano il premio, la lampadina no; ogni attrezzo
    una volta al giorno; la torcia allunga le occhiate;
  · trovato: i bulloni, il barattolo che si accende, le sfide pagate UNA
    volta, l'avviso ANONIMO al venditore;
  · LA PISTA A TAPPE (dal Detective): «biglietto», poi «trovato»;
  · i gradi si aprono coi ritrovamenti, e la calamita ridà il calore;
  · la bottega: cappello, sfondo, titolo, posti nel barattolo; il saldo
    si conta sul server;
  · NIENTE XP: `xp_eventi` e gli xp dell'utente non si muovono;
  · il nascondiglio venduto si ripara; a mezzanotte si ricomincia;
  · IL MONDO (17 nov 2026): le zone si aprono coi ritrovamenti (una zona
    chiusa non fa partire la caccia), i bulloni sparsi si raccolgono una
    volta sola, il Banco del cambio segue la vista del P2P;
  · L'EVIDENZA NEL MONDO: solo un annuncio proprio e in vetrina, uno al
    giorno, coi bulloni contati sul server, palco pieno = 400, l'annuncio
    venduto scende dal palco da solo;
  · LE MISSIONI: valgono solo dopo il tempo minimo dalla partenza, le
    stelle da 1 a 3, i bulloni la prima volta sola, e il tabellone le
    legge da `missioni_superate`;
  · il freno delle occhiate morde.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco,
e `notifica` e' sostituita da un registro.

USO:  python collaudo_caccia_a_tappo.py
"""

import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova

COMPRA = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
VENDE = {"X-Tg-Init-Data": "collaudo:222:Venditore"}
ADMIN = {"X-Tg-Init-Data": "collaudo:999:Admin"}
B = "/api/gioco/tappo"


def main():
    print("=" * 58)
    print("  LA CACCIA A TAPPO — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    S._SECCHI.clear()
    avvisi = []

    async def registra(tg_id, testo, bottone=None):
        avvisi.append((tg_id, testo, bottone))
        return "registrato"
    S.notifica = registra

    def annuncio(venditore, titolo, categoria, sats, stato="attivo"):
        con = S.db()
        cur = con.execute(
            "INSERT INTO annunci(venditore_id, titolo, descrizione, categoria, "
            "prezzo_sats, zona, stato, creato) VALUES(?,?,?,?,?,?,?,?)",
            (venditore, titolo, f"{titolo}, come nuovo", categoria, sats,
             "Torino", stato, int(time.time())))
        con.commit()
        aid = cur.lastrowid
        con.close()
        return aid

    def riga(tg):
        con = S.db()
        r = con.execute("SELECT * FROM gioco_tappo WHERE tg_id=? AND giorno=?",
                        (tg, S._giorno_roma(time.time()))).fetchone()
        con.close()
        return dict(r) if r else None

    def conta(sql, *arg):
        con = S.db()
        n = con.execute(sql, arg).fetchone()[0]
        con.close()
        return n

    con = S.db()
    for tg, nome in ((111, "Compratore"), (222, "Venditore"), (999, "Admin")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato) "
                    "VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    con.execute("DELETE FROM annunci")
    for t in ("gioco_tappo", "gioco_tappo_oggetti", "gioco_tappo_attrezzi",
              "gioco_tappo_sfide", "gioco_tappo_mondo", "gioco_tappo_evidenza",
              "gioco_tappo_missioni"):
        con.execute(f"DELETE FROM {t}")
    con.commit()
    con.close()
    cuffie = annuncio(222, "Cuffie bluetooth Sony", "Elettronica", 15000)
    tastiera = annuncio(222, "Tastiera meccanica", "Informatica", 40000)
    lampada = annuncio(222, "Lampada da tavolo", "Casa e giardino", 8000)
    nokia = annuncio(999, "Telefono Nokia vintage", "Telefonia", 30000)
    radio = annuncio(111, "Radio di mio nonno", "Elettronica", 12000)
    xp_prima = conta("SELECT COUNT(*) FROM xp_eventi")

    print("\n[a leva spenta il gioco non esiste]")
    S.GIOCO_TAPPO_ATTIVO = False
    prova("GET della pagina: 404", 404, c.get(B, headers=COMPRA).status_code)
    prova("le otto POST: 404", [404] * 8,
          [c.post(f"{B}/{r}", json={}, headers=COMPRA).status_code
           for r in ("parti", "indizio", "attrezzo", "guarda", "oggetto",
                     "raccogli", "evidenza", "missione")])
    prova("/api/me dice gioco_tappo: false", (False, False),
          (c.get("/api/me", headers=COMPRA).json().get("gioco_tappo"),
           c.get("/api/me", headers=COMPRA).json().get("tappo_caccia")))
    S.GIOCO_TAPPO_ATTIVO = True

    print("\n[la dispensa, prima di partire]")
    prova("senza identita' non si entra", True,
          c.get(B).status_code in (401, 403))
    st = c.get(B, headers=COMPRA).json()
    prova("nessuna caccia finche' non si sceglie lo scaffale", None, st["caccia"])
    prova("sei scaffali, ventinove barattoli, tutti spenti", (6, 29, 0),
          (len(st["scaffali"]), st["barattoli_totale"], st["barattoli_accesi"]))
    prova("lo scaffale 1 ha tre annunci (il suo non conta), il 3 uno, il 4 nessuno",
          (3, 1, 0), tuple(st["scaffali"][i]["annunci"] for i in (0, 2, 3)))
    prova("il corredo: un attrezzo per tipo nello zaino", [1, 1, 1],
          [a["quanti"] for a in st["attrezzi"]])
    prova("si parte dal primo grado, a saldo zero", (1, 0), (st["grado_max"], st["saldo"]))
    prova("...e /api/me accende la voce, senza caccia aperta", (True, False),
          (c.get("/api/me", headers=COMPRA).json().get("gioco_tappo"),
           c.get("/api/me", headers=COMPRA).json().get("tappo_caccia")))
    prova("un'occhiata prima di partire: 400, e non nasce niente", (400, None),
          (c.post(f"{B}/guarda", json={"annuncio_id": cuffie}, headers=COMPRA).status_code,
           riga(111)))

    print("\n[la caccia parte]")
    prova("uno scaffale che non c'e': 400", 400,
          c.post(f"{B}/parti", json={"scaffale": 9}, headers=COMPRA).status_code)
    prova("uno scaffale vuoto: 400", 400,
          c.post(f"{B}/parti", json={"scaffale": 4}, headers=COMPRA).status_code)
    prova("un grado ancora chiuso: 400", 400,
          c.post(f"{B}/parti", json={"scaffale": 1, "grado": 2}, headers=COMPRA).status_code)
    r = c.post(f"{B}/parti", json={"scaffale": 1}, headers=COMPRA)
    ca = r.json()["caccia"]
    prova("parte sullo scaffale 1, da Curioso: 12 occhiate, premio 3, una tappa",
          (200, 1, 1, 12, 3, 1),
          (r.status_code, ca["scaffale"], ca["grado"], ca["occhiate"], ca["premio"], ca["tappe"]))
    prova("un indizio solo, ed e' il barattolo", ["barattolo"], [i["tipo"] for i in ca["indizi"]])
    qui = riga(111)["annuncio_id"]
    prova("il nascondiglio e' un annuncio ALTRUI dello scaffale 1", True,
          qui in (cuffie, tastiera, nokia))
    prova("...e NON esce nella risposta", (False, False),
          ("annuncio" in ca, f'"id":{qui}' in r.text.replace(" ", "")))
    prova("ripartire su un altro scaffale non cambia niente", (1, qui),
          (c.post(f"{B}/parti", json={"scaffale": 3}, headers=COMPRA).json()["caccia"]["scaffale"],
           riga(111)["annuncio_id"]))
    prova("/api/me: caccia aperta", True,
          c.get("/api/me", headers=COMPRA).json().get("tappo_caccia"))

    print("\n[le occhiate]")
    prova("nel proprio annuncio Tappo non c'e' mai: 400, e non costa", (400, 0),
          (c.post(f"{B}/guarda", json={"annuncio_id": radio}, headers=COMPRA).status_code,
           riga(111)["occhiate"]))
    prova("un annuncio che non esiste: 404, e non costa", (404, 0),
          (c.post(f"{B}/guarda", json={"annuncio_id": 99999}, headers=COMPRA).status_code,
           riga(111)["occhiate"]))
    r = c.post(f"{B}/guarda", json={"annuncio_id": lampada}, headers=COMPRA).json()
    prova("un altro scaffale: «no», acqua, un'occhiata e uno sbaglio in meno",
          ("no", "acqua", 11, 1),
          (r["esito"], r["calore"], r["caccia"]["occhiate"], r["caccia"]["sbagli"]))
    altro = next(a for a in (cuffie, tastiera, nokia) if a != qui)
    r = c.post(f"{B}/guarda", json={"annuncio_id": altro}, headers=COMPRA).json()
    prova("stesso scaffale, altro barattolo: tiepido", ("no", "tiepido"),
          (r["esito"], r["calore"]))

    print("\n[indizi e attrezzi]")
    r = c.post(f"{B}/indizio", headers=COMPRA).json()["caccia"]
    prova("un indizio pagato: due indizi, premio 2", (["barattolo", "fascia"], 2),
          ([i["tipo"] for i in r["indizi"]], r["premio"]))
    r = c.post(f"{B}/attrezzo", json={"attrezzo": "lampadina", "azione": "usa"},
               headers=COMPRA).json()
    prova("la lampadina apre il terzo SENZA abbassare il premio", (3, 2, 0),
          (len(r["caccia"]["indizi"]), r["caccia"]["premio"],
           next(a["quanti"] for a in r["attrezzi"] if a["id"] == "lampadina")))
    prova("un indizio oltre l'ultimo non costa", 2,
          c.post(f"{B}/indizio", headers=COMPRA).json()["caccia"]["premio"])
    prova("la calamita dove il calore c'e' gia': 400", 400,
          c.post(f"{B}/attrezzo", json={"attrezzo": "calamita", "azione": "usa"},
                 headers=COMPRA).status_code)
    r = c.post(f"{B}/attrezzo", json={"attrezzo": "torcia", "azione": "usa"},
               headers=COMPRA).json()["caccia"]
    prova("la torcia: tre occhiate in piu'", (15, 13), (r["occhiate_max"], r["occhiate"]))
    prova("...ma una al giorno: 400", 400,
          c.post(f"{B}/attrezzo", json={"attrezzo": "torcia", "azione": "usa"},
                 headers=COMPRA).status_code)
    prova("prendere un attrezzo senza bulloni: 400", 400,
          c.post(f"{B}/attrezzo", json={"attrezzo": "torcia", "azione": "prendi"},
                 headers=COMPRA).status_code)

    print("\n[trovato]")
    r = c.post(f"{B}/guarda", json={"annuncio_id": qui}, headers=COMPRA).json()
    prova("l'annuncio giusto: trovato, coi bulloni del premio", ("trovato", True, 2),
          (r["esito"], r["caccia"]["trovato"], r["caccia"]["bulloni"]))
    prova("le sfide appena pagate: il primo tappo e il fulmine (sbagli e aiuti: niente naso, niente colpo secco)",
          ["fulmine:1", "tappi:1"], sorted(s["id"] for s in r["sfide_nuove"]))
    prova("il saldo: 2 del premio + 2 + 3 delle sfide", 7, r["saldo"])
    prova("adesso il nascondiglio si puo' dire", qui, r["caccia"]["annuncio"]["id"])
    prova("un barattolo acceso, di bronzo", (1, ["bronzo"]),
          (r["barattoli_accesi"],
           [b["metallo"] for s in r["scaffali"] for b in s["barattoli"] if b["volte"]]))
    c.get("/api/salute")
    al_venditore = [a for a in avvisi if a[0] in (222, 999)]
    prova("il venditore lo viene a sapere, una volta, senza il nome di chi gioca",
          (1, False), (len(al_venditore), "Compratore" in al_venditore[0][1]))
    r = c.post(f"{B}/guarda", json={"annuncio_id": altro}, headers=COMPRA).json()
    prova("un'altra occhiata dopo: «gia'», e non costa", ("gia", 3),
          (r["esito"], riga(111)["occhiate"]))
    prova("riaprire la pagina non ripaga le sfide", 7, c.get(B, headers=COMPRA).json()["saldo"])
    prova("/api/me: la caccia di oggi e' chiusa", False,
          c.get("/api/me", headers=COMPRA).json().get("tappo_caccia"))

    print("\n[la bottega]")
    r = c.post(f"{B}/oggetto", json={"oggetto": "berretto", "azione": "prendi"}, headers=COMPRA)
    prova("un berretto: 6 bulloni, e Tappo se lo mette", (200, 1, "berretto"),
          (r.status_code, r.json()["saldo"], r.json()["indossato"]))
    prova("...ed esce da /api/me per la stradina", "berretto",
          c.get("/api/me", headers=COMPRA).json().get("tappo_oggetto"))
    prova("due volte lo stesso: 400", 400,
          c.post(f"{B}/oggetto", json={"oggetto": "berretto", "azione": "prendi"},
                 headers=COMPRA).status_code)
    prova("la corona senza bulloni: 400", 400,
          c.post(f"{B}/oggetto", json={"oggetto": "corona", "azione": "prendi"},
                 headers=COMPRA).status_code)
    prova("indossare quel che non si ha: 400", 400,
          c.post(f"{B}/oggetto", json={"oggetto": "cilindro", "azione": "indossa"},
                 headers=COMPRA).status_code)
    prova("un oggetto inventato: 400", 400,
          c.post(f"{B}/oggetto", json={"oggetto": "sats", "azione": "prendi"},
                 headers=COMPRA).status_code)
    prova("toglierlo: testa nuda", "",
          c.post(f"{B}/oggetto", json={"oggetto": "berretto", "azione": "togli"},
                 headers=COMPRA).json()["indossato"])
    # i bulloni per il resto della bottega: una ricevuta di sfida scritta
    # a mano (il saldo si conta dalle tabelle, mai da un numero del client)
    con = S.db()
    con.execute("INSERT INTO gioco_tappo_sfide(tg_id, sfida, bulloni, creato) "
                "VALUES(111, 'collaudo:1', 200, 1)")
    con.commit()
    con.close()
    tetto = c.get("/api/me", headers=COMPRA).json()["max_barattolo"]
    r = c.post(f"{B}/oggetto", json={"oggetto": "posti", "azione": "prendi"}, headers=COMPRA)
    prova("i posti in piu': il barattolo dei preferiti si allarga di cinque",
          (tetto + 5, tetto + 5),
          (r.json()["max_barattolo"], c.get("/api/me", headers=COMPRA).json()["max_barattolo"]))
    r = c.post(f"{B}/oggetto", json={"oggetto": "alba", "azione": "prendi"}, headers=COMPRA)
    prova("uno sfondo: si mette da solo", "alba", r.json()["palco"])
    c.post(f"{B}/oggetto", json={"oggetto": "amico", "azione": "prendi"}, headers=COMPRA)
    prova("il titolo «Amico di Tappo» e' fra quelli sbloccati", True,
          "t_amico_tappo" in [t["id"] for t in c.get("/api/me", headers=COMPRA).json()["titoli"]])
    r = c.post(f"{B}/attrezzo", json={"attrezzo": "torcia", "azione": "prendi"}, headers=COMPRA)
    prova("una torcia nuova nello zaino, pagata", (200, 1),
          (r.status_code, next(a["quanti"] for a in r.json()["attrezzi"] if a["id"] == "torcia")))
    prova("gli attrezzi a caccia finita non si usano: 400", 400,
          c.post(f"{B}/attrezzo", json={"attrezzo": "torcia", "azione": "usa"},
                 headers=COMPRA).status_code)

    print("\n[i gradi e la pista a tappe]")
    con = S.db()
    for i in range(15):
        con.execute(
            "INSERT INTO gioco_tappo(tg_id, giorno, annuncio_id, scaffale, grado, "
            "trovato, bulloni, categoria, partito, creato) "
            "VALUES(222, ?, 0, 1, 3, 1000, 8, 'Motori', 1, 1)", (f"2020-01-{i + 1:02d}",))
    con.commit()
    con.close()
    st = c.get(B, headers=VENDE).json()
    prova("quindici ritrovamenti da Esploratore aprono il Detective, non la Volpe", 4,
          st["grado_max"])
    prova("...e le sfide arretrate si pagano da sole all'apertura", True,
          st["saldo"] >= 15 * 8 + 2 + 4 + 8)
    prova("...il barattolo «Motori» e' d'argento", "argento",
          next(b["metallo"] for s in st["scaffali"] for b in s["barattoli"]
               if b["categoria"] == "Motori"))
    ca = c.post(f"{B}/parti", json={"scaffale": 1}, headers=VENDE).json()["caccia"]
    prova("parte al grado piu' alto aperto: Detective, due tappe, senza calore",
          (4, 2, 1, False), (ca["grado"], ca["tappe"], ca["tappa"], ca["calore"]))
    primo = riga(222)["annuncio_id"]
    secondo = next(a for a in (radio, nokia) if a != primo)
    prova("il nascondiglio e' uno dei due annunci altrui dello scaffale", True,
          primo in (radio, nokia))
    r = c.post(f"{B}/guarda", json={"annuncio_id": secondo}, headers=VENDE).json()
    prova("sbagliata, senza calore: «no» e basta", ("no", ""), (r["esito"], r["calore"]))
    r = c.post(f"{B}/attrezzo", json={"attrezzo": "calamita", "azione": "usa"},
               headers=VENDE).json()
    prova("la calamita ridà il calore", True, r["caccia"]["calore"])
    r = c.post(f"{B}/guarda", json={"annuncio_id": secondo}, headers=VENDE).json()
    prova("...e la stessa occhiata adesso dice quanto e' vicina", True,
          r["calore"] in ("fuoco", "fuochino", "tiepido"))
    c.post(f"{B}/indizio", headers=VENDE)
    r = c.post(f"{B}/guarda", json={"annuncio_id": primo}, headers=VENDE).json()
    prova("la prima tappa: un BIGLIETTO, non e' finita", ("biglietto", False, 2),
          (r["esito"], r["caccia"]["trovato"], r["caccia"]["tappa"]))
    prova("...la tappa nuova riparte dal primo indizio, e Tappo e' altrove",
          (1, secondo, str(primo)),
          (len(r["caccia"]["indizi"]), riga(222)["annuncio_id"], riga(222)["pista"]))
    r = c.post(f"{B}/guarda", json={"annuncio_id": secondo}, headers=VENDE).json()
    prova("la seconda tappa: trovato; 12 meno un indizio pagato (2)", ("trovato", 10),
          (r["esito"], r["caccia"]["bulloni"]))
    nuove = sorted(s["id"] for s in r["sfide_nuove"])
    prova("...pagano «Sulla pista» e il gradino del Detective", True,
          "pista:1" in nuove and "scala:4" in nuove)

    print("\n[niente XP, mai]")
    prova("xp_eventi non si e' mosso", xp_prima, conta("SELECT COUNT(*) FROM xp_eventi"))
    prova("gli xp di chi ha giocato sono quelli di prima", 0,
          conta("SELECT COALESCE(SUM(xp),0) FROM utenti WHERE tg_id IN (111, 222)"))

    print("\n[il mondo: le zone si aprono coi ritrovamenti]")
    m = c.get(B, headers=ADMIN).json()["mondo"]
    prova("chi non ha mai trovato Tappo cammina solo nella prima zona",
          [True, False, False, False, False, False], [z["aperta"] for z in m["zone"]])
    prova("...e la terza gli dice quanti ritrovamenti mancano", 3, m["zone"][2]["mancano"])
    r = c.post(f"{B}/parti", json={"scaffale": 3}, headers=ADMIN)
    prova("una zona chiusa non fa partire la caccia: 400, e non nasce niente",
          (400, True, None), (r.status_code, "chiusa" in r.text, riga(999)))
    con = S.db()
    for g in ("2020-01-01", "2020-01-02", "2020-01-03"):
        con.execute("INSERT INTO gioco_tappo(tg_id, giorno, annuncio_id, scaffale, "
                    "partito, trovato, bulloni, categoria) VALUES(999,?,1,1,1,2,0,"
                    "'Elettronica')", (g,))
    con.commit()
    con.close()
    m = c.get(B, headers=ADMIN).json()["mondo"]
    prova("tre ritrovamenti aprono le prime tre zone",
          [True, True, True, False, False, False], [z["aperta"] for z in m["zone"]])

    print("\n[il nascondiglio che sparisce si ripara]")
    r = c.post(f"{B}/parti", json={"scaffale": 3}, headers=ADMIN)
    prova("l'admin caccia sulla mensola di casa: c'e' solo la lampada", lampada,
          riga(999)["annuncio_id"])
    con = S.db()
    con.execute("UPDATE annunci SET stato='venduto' WHERE id=?", (lampada,))
    con.commit()
    con.close()
    st = c.get(B, headers=ADMIN).json()
    nuovo = riga(999)["annuncio_id"]
    prova("venduta la lampada, Tappo si sposta in un annuncio vivo (e lo scaffale lo segue)",
          (True, 1), (nuovo in (cuffie, tastiera, radio), st["caccia"]["scaffale"]))

    print("\n[a mezzanotte si ricomincia]")
    con = S.db()
    con.execute("UPDATE gioco_tappo SET giorno='2020-02-01' WHERE tg_id=111 AND giorno=?",
                (S._giorno_roma(time.time()),))
    con.commit()
    con.close()
    st = c.get(B, headers=COMPRA).json()
    prova("il giorno dopo: nessuna caccia, il barattolo resta acceso, il cappello pure",
          (None, 1, True),
          (st["caccia"], st["barattoli_accesi"],
           any(o["mio"] for o in st["oggetti"] if o["id"] == "berretto")))

    print("\n[il mondo: i bulloni sparsi]")
    st = c.get(B, headers=COMPRA).json()
    m = st["mondo"]
    aperte = {z["n"] for z in m["zone"] if z["aperta"]}
    prova("cinque bulloni oggi, tutti in zone aperte, nessuno ancora raccolto",
          (5, True, 0), (m["pezzi_totale"], all(p["zona"] in aperte for p in m["pezzi"]),
                         m["pezzi_presi"]))
    n = m["pezzi"][0]["n"]
    r = c.post(f"{B}/raccogli", json={"pezzo": n}, headers=COMPRA).json()
    prova("raccolto: un bullone in piu' nel saldo", (True, st["saldo"] + 1, 1),
          (r["preso"], r["saldo"], r["mondo"]["pezzi_presi"]))
    r = c.post(f"{B}/raccogli", json={"pezzo": n}, headers=COMPRA).json()
    prova("lo stesso bullone una seconda volta non da' niente", (False, st["saldo"] + 1),
          (r["preso"], r["saldo"]))
    prova("un bullone che oggi non c'e': 400", 400,
          c.post(f"{B}/raccogli", json={"pezzo": 99}, headers=COMPRA).status_code)
    prova("la ricevuta del giorno: un pezzo, un bullone", 1,
          conta("SELECT bulloni FROM gioco_tappo_mondo WHERE tg_id=111"))

    print("\n[il Banco del cambio]")
    prova("c'e' nel mondo se e solo se il P2P c'e' per lei, coi suoi scambi",
          (bool(S._p2p_per(111).get("attivo")), 0),
          (st["mondo"]["cambio"]["attivo"], st["mondo"]["cambio"]["scambi"]))
    prova("...e le sue sfide stanno con le altre", True,
          any(f["id"] == "cambio" for f in st["sfide"]))

    print("\n[l'annuncio in evidenza nel mondo]")
    ev = c.get(B, headers=VENDE).json()["mondo"]["evidenza"]
    prova("nessuno sul palco; costa 40; fra i suoi annunci ci sono le cuffie (zona 1)",
          ([], 0, 40, True),
          (ev["palchi"], ev["mio"], ev["bulloni"],
           any(x["annuncio"] == cuffie and x["zona"] == 1 for x in ev["candidati"])))
    prova("l'annuncio di un altro: 400", 400,
          c.post(f"{B}/evidenza", json={"annuncio": nokia}, headers=VENDE).status_code)
    saldo = c.get(B, headers=VENDE).json()["saldo"]
    if saldo >= 40:
        con = S.db()
        con.execute("INSERT INTO gioco_tappo_oggetti(tg_id, oggetto, bulloni, creato) "
                    "VALUES(222, 'zavorra', ?, 0)", (saldo - 10,))
        con.commit()
        con.close()
    r = c.post(f"{B}/evidenza", json={"annuncio": cuffie}, headers=VENDE)
    prova("senza abbastanza bulloni: 400, e il palco resta vuoto", (400, 0),
          (r.status_code, conta("SELECT COUNT(*) FROM gioco_tappo_evidenza")))
    con = S.db()
    con.execute("INSERT INTO gioco_tappo_mondo(tg_id, giorno, presi, bulloni, creato) "
                "VALUES(222, '2020-01-01', '', 50, 0)")
    con.commit()
    con.close()
    prima = c.get(B, headers=VENDE).json()["saldo"]
    r = c.post(f"{B}/evidenza", json={"annuncio": cuffie}, headers=VENDE).json()
    prova("con i bulloni: le cuffie salgono sul palco, il saldo scende di 40",
          ([(cuffie, 1, True)], cuffie, prima - 40, []),
          ([(p["annuncio"], p["zona"], p["mio"]) for p in r["mondo"]["evidenza"]["palchi"]],
           r["mondo"]["evidenza"]["mio"], r["saldo"], r["mondo"]["evidenza"]["candidati"]))
    r = c.post(f"{B}/evidenza", json={"annuncio": tastiera}, headers=VENDE)
    prova("un secondo annuncio lo stesso giorno: 400", (400, True),
          (r.status_code, "domani" in r.text))
    ev = c.get(B, headers=COMPRA).json()["mondo"]["evidenza"]
    prova("gli altri giocatori le vedono, e non sono loro", [(cuffie, False)],
          [(p["annuncio"], p["mio"]) for p in ev["palchi"]])
    S.GIOCO_TAPPO_EVIDENZA_POSTI = 1
    con = S.db()
    con.execute("INSERT INTO gioco_tappo_mondo(tg_id, giorno, presi, bulloni, creato) "
                "VALUES(111, '2020-01-01', '', 50, 0)")
    con.commit()
    con.close()
    r = c.post(f"{B}/evidenza", json={"annuncio": radio}, headers=COMPRA)
    prova("il palco della zona pieno: 400", (400, True), (r.status_code, "pieno" in r.text))
    S.GIOCO_TAPPO_EVIDENZA_POSTI = 3
    con = S.db()
    con.execute("UPDATE annunci SET stato='venduto' WHERE id=?", (cuffie,))
    con.commit()
    con.close()
    prova("venduto l'annuncio, scende dal palco da solo", [],
          c.get(B, headers=COMPRA).json()["mondo"]["evidenza"]["palchi"])

    print("\n[le missioni di Tappo]")
    st = c.get(B, headers=COMPRA).json()
    prova("otto missioni, una per zona, la prima la piu' facile, nessuna finita; il tabellone legge l'insieme vuoto",
          (["sats", "lucchetto", "parole", "staffetta", "oblo", "quaderno", "antenna", "halving"], [0] * 8, set()),
          ([x["id"] for x in st["missioni"]], [x["stelle"] for x in st["missioni"]],
           S.missioni_superate(S.db(), 111)))
    M = f"{B}/missione"
    prova("una missione che non c'e': 400", 400,
          c.post(M, json={"missione": "tesoro", "azione": "inizia"}, headers=COMPRA).status_code)
    prova("finire senza essere partiti: 400", 400,
          c.post(M, json={"missione": "quaderno", "azione": "finisci", "stelle": 3},
                 headers=COMPRA).status_code)
    c.post(M, json={"missione": "quaderno", "azione": "inizia"}, headers=COMPRA)
    r = c.post(M, json={"missione": "quaderno", "azione": "finisci", "stelle": 3}, headers=COMPRA)
    prova("finire subito dopo la partenza: 400, troppo presto", (400, True),
          (r.status_code, "presto" in r.text))
    con = S.db()
    con.execute("UPDATE gioco_tappo_missioni SET iniziata=iniziata-60 WHERE tg_id=111")
    con.commit()
    con.close()
    prova("le stelle vanno da 1 a 3", 400,
          c.post(M, json={"missione": "quaderno", "azione": "finisci", "stelle": 4},
                 headers=COMPRA).status_code)
    r = c.post(M, json={"missione": "quaderno", "azione": "finisci", "stelle": 2},
               headers=COMPRA).json()
    prova("finita: 15 bulloni la prima volta, due stelle, e il tabellone la vede",
          (30, st["saldo"] + 30, 2, {"quaderno"}),
          (r["bulloni_nuovi"], r["saldo"], next(x["stelle"] for x in r["missioni"] if x["id"] == "quaderno"),
           S.missioni_superate(S.db(), 111)))
    c.post(M, json={"missione": "quaderno", "azione": "inizia"}, headers=COMPRA)
    con = S.db()
    con.execute("UPDATE gioco_tappo_missioni SET iniziata=iniziata-60 WHERE tg_id=111")
    con.commit()
    con.close()
    r = c.post(M, json={"missione": "quaderno", "azione": "finisci", "stelle": 3},
               headers=COMPRA).json()
    prova("rigiocata: nessun bullone in piu', le stelle salgono a tre",
          (0, st["saldo"] + 30, 3), (r["bulloni_nuovi"], r["saldo"], next(x["stelle"] for x in r["missioni"] if x["id"] == "quaderno")))
    prova("...e niente XP nemmeno qui", xp_prima, conta("SELECT COUNT(*) FROM xp_eventi"))

    print("\n[il freno delle occhiate]")
    S._SECCHI.clear()
    with banco.freno_fermo(S):          # il conto, non la velocita' del runner
        stati = [c.post(f"{B}/guarda", json={"annuncio_id": 99999}, headers=COMPRA).status_code
                 for i in range(61)]
    prova("sessanta l'ora, la sessantunesima e' un 429", (60, 429),
          (len([x for x in stati[:60] if x != 429]), stati[60]))
    S._SECCHI.clear()

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
