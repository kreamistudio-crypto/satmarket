# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA MODIFICA DI PIU' ANNUNCI INSIEME (16 ott 2026).

`prove.py` fa girare i giudici estratti (i parametri, le esclusioni, i
numeri nuovi) e guarda la forma delle rotte. Qui gira la cosa VERA: il
server su un database usa-e-getta, le rotte chiamate dalla porta HTTP
con `TestClient`.

Le domande, nell'ordine in cui si fanno:
  · la LEVA spenta chiude tutte le porte (404), accesa le apre;
  · i PARAMETRI storti e il TETTO dei cento si dicono con un 400;
  · l'ANTEPRIMA dice chi cambia e da quanto a quanto, chi resta fuori
    e perche' — e non scrive NIENTE;
  · il PREZZO (in percentuale e fisso), la QUANTITA', la PAUSA, la
    RIATTIVAZIONE, la CATEGORIA, la SPEDIZIONE e l'ELIMINAZIONE fanno
    quel che dicono, sui soli ammessi, senza moderazione e senza avvisi
    a nessuno — tranne UN messaggio per compratore le cui offerte
    decadono con la pausa;
  · l'ANNULLA rimette il prima sulle righe intatte, lascia stare quelle
    toccate dopo, non si ripete, scade a 24 ore e non vale per
    l'eliminazione;
  · la CORSA: chi compra fra il piano e la scrittura lascia l'annuncio
    com'era;
  · i RELAY: a lotti, un giro per venditore, e i gesti giusti (NIP-99,
    kind 5, il canale) — mai un kind 1.

NON TOCCA NIENTE DI VERO: il config di cartone lo installa `avvio()` del
banco PRIMA dell'import del server. Nessuna rete, e in CI lo garantisce
la gabbia di `collaudi_ci.py`.

USO:  python collaudo_modifica_massiva.py
"""

import asyncio
import json
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
VENDE, COMPRA, ALTRO = 222, 111, 333
MODERATI = []      # ogni chiamata alla moderazione: deve restare vuoto
DOPO = []          # (tg_id, gesti, decadute) di ogni giro in sottofondo


def db():
    return banco.SRV.db()


def semina():
    """Il negozio di 222, un annuncio per ogni caso, piu' uno di 111 che
    nessuno deve toccare. Torna {nome: id}."""
    con = db()
    for t in ("modifiche_massive", "offerte_righe", "offerte",
              "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((VENDE, "Vende"), (COMPRA, "Compra"), (ALTRO, "Altro")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    adesso = int(time.time())
    casi = {
        "a": dict(foto='["a1_0.jpg", "a1_1.jpg"]'),
        "b": dict(prezzo_sats=10_000, quantita=1),
        "euro": dict(valuta="eur", prezzo_eur=20.0, prezzo_sats=20_000),
        "ordine": {},
        "creato": {},
        "offerta": {},
        "accettata": {},
        "lampo": dict(lampo_percento=20, lampo_scadenza=adesso + 3600),
        "asta": dict(asta_base_sats=10_000, quantita=1),
        "revisione": dict(stato="revisione"),
        "esaurito": dict(stato="venduto", quantita=0),
        # un secondo esaurito che nessun passo riattiva
        "fermo": dict(stato="venduto", quantita=0),
        "servizio": dict(consegna="servizio", quantita=999),
        "nostr": dict(contatto_nostr="npub1collaudo"),
        "alimenti": dict(categoria="Alimenti e bevande", condizione=""),
        "ritiro": dict(consegna="ritiro", spedizione_sats=0),
    }
    ids = {}
    for nome, extra in casi.items():
        r = dict(venditore_id=VENDE, titolo=f"Annuncio {nome}",
                 descrizione="descrizione", prezzo_sats=30_000,
                 categoria="Altro", zona="Torino (TO)", stato="attivo",
                 creato=1, consegna="spedizione", quantita=3, valuta="sats",
                 condizione="buono", modificato=0, spedizione_sats=3000,
                 spedizione_zone=json.dumps({"dom": {"sats": 3000,
                                                     "eur": 0.0}}))
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
    # un affare SALDO sull'«ordine», e uno appena CREATO sul «creato»
    for nome, stato in (("ordine", "locked"), ("creato", "creato")):
        con.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,quantita,stato,consegna_scelta,spedizione_sats,"
            "creato,aggiornato) VALUES(?,?,?,33000,1,?,'spedizione',3000,"
            "?,?)", (ids[nome], COMPRA, VENDE, stato, adesso, adesso))
    # una trattativa APERTA sull'«offerta», una ACCETTATA sull'«accettata»
    # e una aperta di un altro compratore sulla «b»
    for nome, chi, stato in (("offerta", COMPRA, "proposta"),
                             ("accettata", COMPRA, "accettata"),
                             ("b", ALTRO, "proposta")):
        con.execute(
            "INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
            "valuta,importo_sats,stato,scadenza,quantita,creato) "
            "VALUES(?,?,?,'sats',25000,?,?,1,?)",
            (ids[nome], chi, VENDE, stato, adesso + 86400, adesso))
    con.commit()
    con.close()
    return ids


def riga(aid):
    con = db()
    r = con.execute("SELECT * FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return dict(r) if r else {}


def campi(aid, *nomi):
    r = riga(aid)
    return tuple(r.get(n) for n in nomi)


def fotografia():
    """Tutto quel che un'anteprima NON deve toccare, byte per byte."""
    con = db()
    f = tuple([tuple(x) for x in con.execute(f"SELECT * FROM {t} ORDER BY 1")]
              for t in ("annunci", "ordini", "offerte", "modifiche_massive"))
    con.close()
    return f


def registro(rid):
    con = db()
    r = con.execute("SELECT * FROM modifiche_massive WHERE id=?",
                    (rid,)).fetchone()
    con.close()
    return dict(r) if r else {}


def motivi(d):
    return {v["id"]: v["motivo"] for v in d.get("fuori", [])}


def main():
    print("=" * 58)
    print("  LA MODIFICA DI PIU' ANNUNCI INSIEME — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    banco.come(VENDE)

    # LA MODERAZIONE NON DEVE MAI ESSERE CHIAMATA
    async def modera(*a, **k):
        MODERATI.append(("ai", a))
        return None

    def vietato(*a, **k):
        MODERATI.append(("parole", a))
        return ""
    SRV.moderazione_ai = modera
    SRV.controlla_vietato = vietato
    # il giro in sottofondo si REGISTRA: lo si fa girare a parte, qui
    # sotto, dove lo si puo' guardare lotto per lotto
    SRV._mm_dopo = lambda tg, gesti, decadute: DOPO.append(
        (tg, dict(gesti), {k: list(v) for k, v in decadute.items()}))
    ids = semina()
    tutti = [i for n, i in ids.items()]

    # ---------------------------------------------------------------
    print("\n[la leva spenta chiude tutte le porte]")
    SRV.MODIFICA_MASSIVA_ATTIVA = False
    prova("di serie e' spenta", False, banco.SRV.MODIFICA_MASSIVA_ATTIVA)
    corpo = {"ids": [ids["a"]], "azione": "pausa"}
    prova("l'elenco: 404", 404, c.get("/api/me/modifica-massiva").status_code)
    prova("l'anteprima: 404", 404,
          c.post("/api/me/modifica-massiva/anteprima", json=corpo).status_code)
    prova("l'applica: 404, e niente cambia", (404, "attivo"),
          (c.post("/api/me/modifica-massiva/applica", json=corpo).status_code,
           riga(ids["a"])["stato"]))
    prova("l'annulla: 404", 404,
          c.post("/api/me/modifica-massiva/annulla",
                 json={"registro": 1}).status_code)
    prova("/api/me lo dice al client: niente bottone", False,
          c.get("/api/me").json().get("modifica_massiva"))
    SRV.MODIFICA_MASSIVA_ATTIVA = True
    prova("...e accesa, il bottone c'e'", True,
          c.get("/api/me").json().get("modifica_massiva"))

    # ---------------------------------------------------------------
    print("\n[l'elenco da cui si sceglie]")
    r = c.get("/api/me/modifica-massiva")
    d = r.json()
    visti = {v["id"] for v in d.get("annunci", [])}
    prova("risponde 200 col tetto dei cento", (200, 100),
          (r.status_code, d.get("tetto")))
    prova("ci sono tutti i suoi: in vetrina, esauriti, in revisione",
          True, {ids["a"], ids["esaurito"], ids["revisione"]} <= visti)
    prova("...e mai quelli di un altro", False, ids["altrui"] in visti)
    va = next((v for v in d.get("annunci", []) if v["id"] == ids["euro"]), {})
    prova("una riga dice valuta e prezzo del suo listino",
          ("eur", 20.0), (va.get("valuta"), va.get("prezzo_eur")))
    prova("nessuna modifica da annullare, all'inizio", None, d.get("ultima"))
    per_id = {v["id"]: v for v in d.get("annunci", [])}
    prova("ogni riga porta la PRIMA foto (il client ne fa la miniatura), "
          "e senza foto la stringa vuota",
          ("a1_0.jpg", ""), (per_id.get(ids["a"], {}).get("foto"),
                             per_id.get(ids["b"], {}).get("foto")))

    # ---------------------------------------------------------------
    print("\n[i parametri storti e il tetto]")
    def no(corpo, dentro=""):
        r = c.post("/api/me/modifica-massiva/anteprima", json=corpo)
        det = (r.json() or {}).get("detail", "")
        return r.status_code == 400 and dentro.lower() in str(det).lower()
    prova("nessun annuncio scelto: 400", True,
          no({"ids": [], "azione": "pausa"}, "almeno un annuncio"))
    prova("un id che non e' un numero: 400", True,
          no({"ids": ["7"], "azione": "pausa"}, "formato"))
    prova("un booleano non e' un id", True,
          no({"ids": [True], "azione": "pausa"}, "formato"))
    prova("centouno annunci: 400 che dice quanti", True,
          no({"ids": list(range(1, 102)), "azione": "pausa"}, "ne hai scelti 101"))
    prova("...i doppioni non contano due volte", False,
          no({"ids": [ids["a"]] * 150, "azione": "pausa"}))
    prova("un'azione che non c'e'", True,
          no({"ids": [ids["a"]], "azione": "titolo"}, "cosa cambiare"))
    prova("«5.000» sats si rifiuta (sarebbero cinque)", True,
          no({"ids": [ids["a"]], "azione": "prezzo", "valuta": "sats",
              "prezzo": "5.000"}, "senza punti"))
    prova("percentuale zero", True,
          no({"ids": [ids["a"]], "azione": "percento", "percento": "0"},
             "zero"))
    prova("percentuale oltre il -90", True,
          no({"ids": [ids["a"]], "azione": "percento", "percento": "-95"},
             "da -90"))
    prova("una categoria inventata", True,
          no({"ids": [ids["a"]], "azione": "categoria",
              "categoria": "Pozioni"}, "categoria"))
    prova("quantita' zero (la pausa ha il suo verbo)", True,
          no({"ids": [ids["a"]], "azione": "quantita", "quantita": "0"},
             "almeno 1"))

    # ---------------------------------------------------------------
    print("\n[l'anteprima del -10 % su tutto: dice e non scrive]")
    prima = fotografia()
    r = c.post("/api/me/modifica-massiva/anteprima", json={
        "ids": tutti, "azione": "percento", "percento": "−10 %"})
    d = r.json()
    prova("risponde 200", 200, r.status_code)
    prova("non ha scritto niente, in nessuna tabella", True,
          prima == fotografia())
    cambia = {v["id"]: v for v in d.get("cambiano", [])}
    prova("cambiano i liberi (e l'accettata: l'accordo e' stretto; e il "
          "servizio, che ha un prezzo come tutti)",
          {ids["a"], ids["euro"], ids["accettata"], ids["alimenti"],
           ids["ritiro"], ids["servizio"]}, set(cambia) - {ids["b"]})
    prova("la «b» resta fuori: ha un'offerta aperta", "offerta",
          motivi(d).get(ids["b"]))
    prova("da 30.000 a 27.000 sats", ([30000, 0], [27000, 0.0]),
          (cambia.get(ids["a"], {}).get("prima"),
           cambia.get(ids["a"], {}).get("dopo")))
    prova("il listino in euro: da 20 € a 18 €, i sats al cambio",
          ("eur", [18000, 18.0]),
          (cambia.get(ids["euro"], {}).get("valuta"),
           cambia.get(ids["euro"], {}).get("dopo")))
    m = motivi(d)
    prova("i motivi, uno per caso",
          {"ordine": "ordine", "creato": "ordine", "offerta": "offerta",
           "lampo": "lampo", "asta": "asta", "revisione": "revisione",
           "esaurito": "esaurito", "nostr": "nostr", "altrui": "sparito"},
          {n: m.get(ids[n]) for n in ("ordine", "creato", "offerta", "lampo",
                                       "asta", "revisione", "esaurito",
                                       "nostr", "altrui")})
    altrui = next((v for v in d.get("fuori", []) if v["id"] == ids["altrui"]),
                  {})
    prova("l'annuncio di un altro esce SENZA titolo", "", altrui.get("titolo"))
    prova("niente chiavi di servizio verso il client", False,
          any(k.startswith("_") for v in d.get("cambiano", []) for k in v))

    # ---------------------------------------------------------------
    print("\n[l'applica del -10 %]")
    DOPO.clear()
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": tutti, "azione": "percento", "percento": "-10"})
    d = r.json()
    prova("risponde 200 e ne cambia sei", (200, 6),
          (r.status_code, d.get("aggiornati")))
    prova("la «a» a 27.000", 27000, riga(ids["a"])["prezzo_sats"])
    prova("l'euro a 18 € e 18.000 sats", (18.0, 18000),
          campi(ids["euro"], "prezzo_eur", "prezzo_sats"))
    prova("...con la data della modifica", True, riga(ids["a"])["modificato"] > 0)
    prova("...e lo stato com'era: niente revisione", "attivo",
          riga(ids["a"])["stato"])
    prova("chi aveva un ordine resta col prezzo di prima", 30000,
          riga(ids["ordine"])["prezzo_sats"])
    prova("l'offerta aperta non e' decaduta (l'annuncio era fuori)",
          "proposta", banco.SRV.db().execute(
              "SELECT stato FROM offerte WHERE annuncio_id=?",
              (ids["offerta"],)).fetchone()["stato"])
    rid = d.get("registro")
    reg = registro(rid)
    prova("il registro: chi, cosa, quanti", (VENDE, "percento", 6),
          (reg.get("tg_id"), reg.get("azione"), reg.get("quanti")))
    righe_reg = {x["id"]: x for x in json.loads(reg.get("righe") or "[]")}
    prova("...col prima e il dopo della «a»",
          ({"prezzo_sats": 30000, "prezzo_eur": 0.0},
           {"prezzo_sats": 27000, "prezzo_eur": 0.0}),
          (righe_reg.get(ids["a"], {}).get("prima"),
           righe_reg.get(ids["a"], {}).get("dopo")))
    prova("annullabile per 24 ore", True,
          abs(d.get("annullabile_fino", 0) - (reg.get("creato", 0) + 86400)) < 2)
    prova("nessuna moderazione", [], MODERATI)
    prova("nessun avviso ai moderatori", [], banco.AVVISI)
    prova("nessun messaggio a nessuno", [], banco.DETTO)
    prova("in sottofondo: l'evento NIP-99 rilanciato per i sei",
          {i: "aggiorna" for i in cambia if i != ids["b"]},
          DOPO[-1][1] if DOPO else {})
    r = c.get("/api/me/modifica-massiva")
    prova("l'elenco ora dice l'ultima, annullabile",
          (rid, "percento", 6), tuple((r.json().get("ultima") or {}).get(k)
                                      for k in ("id", "azione", "quanti")))

    # ---------------------------------------------------------------
    print("\n[l'annulla del -10 %]")
    DOPO.clear()
    r = c.post("/api/me/modifica-massiva/annulla", json={"registro": rid})
    d = r.json()
    prova("risponde 200 e ne rimette sei", (200, 6),
          (r.status_code, d.get("ripristinati")))
    prova("la «a» torna a 30.000", 30000, riga(ids["a"])["prezzo_sats"])
    prova("l'euro torna a 20 €, i sats al cambio di adesso", (20.0, 20000),
          campi(ids["euro"], "prezzo_eur", "prezzo_sats"))
    prova("il registro e' timbrato", (True, 6),
          (registro(rid).get("annullata", 0) > 0,
           registro(rid).get("annullate_n")))
    r = c.post("/api/me/modifica-massiva/annulla", json={"registro": rid})
    prova("il secondo annulla: 400", (400, True),
          (r.status_code, "già" in r.json().get("detail", "")))
    banco.come(ALTRO)
    r = c.post("/api/me/modifica-massiva/annulla", json={"registro": rid})
    prova("il registro di un altro non si trova", 404, r.status_code)
    banco.come(VENDE)

    # ---------------------------------------------------------------
    print("\n[il prezzo fisso: solo nella valuta del listino]")
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"], ids["euro"]], "azione": "prezzo", "valuta": "sats",
        "prezzo": "15000"})
    d = r.json()
    prova("la «a» a 15.000 sats", (1, 15000),
          (d.get("aggiornati"), riga(ids["a"])["prezzo_sats"]))
    prova("il listino in euro resta fuori: «valuta»", "valuta",
          motivi(d).get(ids["euro"]))
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"]], "azione": "prezzo", "valuta": "sats",
        "prezzo": "15000"})
    prova("lo stesso prezzo di nuovo: «uguale», e nessun registro",
          ("uguale", 0), (motivi(r.json()).get(ids["a"]),
                          r.json().get("registro")))

    # ---------------------------------------------------------------
    print("\n[la quantita': anche con un ordine in corso]")
    DOPO.clear()
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"], ids["ordine"], ids["esaurito"], ids["servizio"],
                ids["nostr"], ids["asta"]], "azione": "quantita",
        "quantita": "7"})
    d = r.json()
    m = motivi(d)
    prova("«a», «ordine» ed «esaurito» a 7 pezzi", (7, 7, 7),
          (riga(ids["a"])["quantita"], riga(ids["ordine"])["quantita"],
           riga(ids["esaurito"])["quantita"]))
    prova("l'esaurito torna in vetrina", "attivo", riga(ids["esaurito"])["stato"])
    prova("...e il mondo lo sa: «active» (NIP-99 e canale)", "active",
          (DOPO[-1][1] if DOPO else {}).get(ids["esaurito"]))
    prova("...ma la quantita' sola non rilancia l'evento", False,
          ids["a"] in (DOPO[-1][1] if DOPO else {}))
    prova("servizio, importato e asta restano fuori",
          ("servizio", "nostr", "asta"),
          (m.get(ids["servizio"]), m.get(ids["nostr"]), m.get(ids["asta"])))
    prova("la quantita' non scrive la data della modifica", 0,
          riga(ids["ordine"])["modificato"])

    # ---------------------------------------------------------------
    print("\n[la pausa: le offerte decadono, un avviso per compratore]")
    con = db()
    # una seconda offerta aperta di 111, sulla «a»: con l'accettata fanno
    # due annunci per lo stesso compratore
    con.execute("INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
                "valuta,importo_sats,stato,scadenza,quantita,creato) "
                "VALUES(?,?,?,'sats',9000,'proposta',?,1,?)",
                (ids["a"], COMPRA, VENDE, int(time.time()) + 86400,
                 int(time.time())))
    con.commit()
    con.close()
    DOPO.clear()
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"], ids["b"], ids["accettata"], ids["ordine"],
                ids["esaurito"], ids["fermo"], ids["revisione"]],
        "azione": "pausa"})
    d = r.json()
    rid_pausa = d.get("registro")
    prova("in pausa «a», «b», «accettata», l'esaurito riattivato poco fa "
          "e anche «ordine»", 5, d.get("aggiornati"))
    prova("chi e' gia' esaurito: «uguale»", "uguale",
          motivi(d).get(ids["fermo"]))
    prova("esauriti: quantita' 0, stato venduto", (0, "venduto"),
          campi(ids["b"], "quantita", "stato"))
    prova("la revisione resta fuori", "revisione",
          motivi(d).get(ids["revisione"]))
    con = db()
    stati = {r["annuncio_id"]: r["stato"] for r in con.execute(
        "SELECT annuncio_id, stato FROM offerte")}
    con.close()
    prova("le offerte su quegli annunci decadono, accettate comprese",
          ("decaduta", "decaduta", "decaduta"),
          (stati.get(ids["a"]), stati.get(ids["b"]), stati.get(ids["accettata"])))
    dec = DOPO[-1][2] if DOPO else {}
    prova("da avvisare: 111 con due annunci, 333 con uno",
          {COMPRA: 2, ALTRO: 1}, {k: len(v) for k, v in dec.items()})
    prova("il mondo: «sold» per i cinque",
          {ids[n]: "sold" for n in ("a", "b", "accettata", "ordine",
                                    "esaurito")},
          DOPO[-1][1] if DOPO else {})
    banco.DETTO.clear()
    asyncio.run(SRV._mm_avvisa_offerte(dec))
    prova("UN messaggio per compratore, non uno per annuncio",
          sorted([COMPRA, ALTRO]), sorted(x[0] for x in banco.DETTO))
    testo_111 = next((t for chi, t in banco.DETTO if chi == COMPRA), "")
    prova("...e il suo dice i due titoli", True,
          "2 annunci" in testo_111 and "Annuncio a" in testo_111
          and "Annuncio accettata" in testo_111)
    prova("nessun avviso ai moderatori", [], banco.AVVISI)

    # ---------------------------------------------------------------
    print("\n[la riattivazione: i pezzi di prima della pausa]")
    DOPO.clear()
    r = c.post("/api/me/modifica-massiva/anteprima", json={
        "ids": [ids["a"], ids["b"], ids["euro"]], "azione": "riattiva"})
    d = r.json()
    dopo = {v["id"]: v["dopo"] for v in d.get("cambiano", [])}
    prova("l'anteprima: «a» con 7, «b» con 1",
          ([7, "attivo"], [1, "attivo"]), (dopo.get(ids["a"]), dopo.get(ids["b"])))
    prova("...e chi e' gia' in vetrina: «uguale»", "uguale",
          motivi(d).get(ids["euro"]))
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"], ids["b"]], "azione": "riattiva"})
    prova("tornano in vetrina coi loro pezzi", ((7, "attivo"), (1, "attivo")),
          (campi(ids["a"], "quantita", "stato"),
           campi(ids["b"], "quantita", "stato")))
    prova("il mondo: «active»", {ids["a"]: "active", ids["b"]: "active"},
          DOPO[-1][1] if DOPO else {})
    r = c.post("/api/me/modifica-massiva/annulla", json={"registro": rid_pausa})
    d = r.json()
    prova("annullare la pausa DOPO la riattivazione: «a» e «b» sono "
          "cambiate da allora, restano come sono",
          ("cambiato", "cambiato", "attivo"),
          (motivi(d).get(ids["a"]), motivi(d).get(ids["b"]),
           riga(ids["a"])["stato"]))
    prova("...gli altri tre tornano coi loro pezzi", (3, (7, "attivo")),
          (d.get("ripristinati"), campi(ids["ordine"], "quantita", "stato")))

    # ---------------------------------------------------------------
    print("\n[la categoria]")
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"], ids["alimenti"]], "azione": "categoria",
        "categoria": "Elettronica"})
    d = r.json()
    prova("la «a» in Elettronica, la condizione resta",
          ("Elettronica", "buono"), campi(ids["a"], "categoria", "condizione"))
    prova("gli alimenti senza condizione restano fuori: «condizione»",
          ("condizione", "Alimenti e bevande"),
          (motivi(d).get(ids["alimenti"]), riga(ids["alimenti"])["categoria"]))
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"]], "azione": "categoria",
        "categoria": "Alimenti e bevande"})
    d = r.json()
    prova("verso una categoria senza condizione: la condizione si toglie",
          (("Alimenti e bevande", ""), True),
          (campi(ids["a"], "categoria", "condizione"),
           (d.get("cambiano") or [{}])[0].get("condizione_via")))
    r = c.post("/api/me/modifica-massiva/annulla",
               json={"registro": r.json().get("registro")})
    prova("l'annulla rimette categoria E condizione",
          ("Elettronica", "buono"), campi(ids["a"], "categoria", "condizione"))

    # ---------------------------------------------------------------
    print("\n[la spedizione: il costo standard del negozio]")
    r = c.post("/api/me/modifica-massiva/anteprima", json={
        "ids": [ids["a"]], "azione": "spedizione"})
    prova("senza costo standard: un 400 che dice di scriverlo", (400, True),
          (r.status_code, "costo di spedizione standard"
           in r.json().get("detail", "")))
    con = db()
    con.execute("UPDATE utenti SET spedizione_standard=? WHERE tg_id=?",
                (json.dumps({"valuta": "sats", "casa": 5000}), VENDE))
    con.commit()
    con.close()
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["a"], ids["ritiro"], ids["euro"]], "azione": "spedizione"})
    d = r.json()
    prova("la «a» a 5.000 a casa, e la copia nella mappa", (5000, 5000),
          (riga(ids["a"])["spedizione_sats"],
           json.loads(riga(ids["a"])["spedizione_zone"])["dom"]["sats"]))
    prova("il solo ritiro resta fuori: «ritiro»", "ritiro",
          motivi(d).get(ids["ritiro"]))
    prova("il listino in euro: 5.000 sats tradotti al cambio (5 €)", 5.0,
          riga(ids["euro"])["spedizione_eur"])
    r = c.post("/api/me/modifica-massiva/annulla",
               json={"registro": d.get("registro")})
    prova("l'annulla rimette tariffa e mappa", (3000, 3000),
          (riga(ids["a"])["spedizione_sats"],
           json.loads(riga(ids["a"])["spedizione_zone"])["dom"]["sats"]))

    # ---------------------------------------------------------------
    print("\n[la corsa: chi compra a meta' lascia l'annuncio com'era]")
    vero_giro = SRV._mm_giro

    async def giro_poi_compra(tg, azione, par, scelti):
        piano = await vero_giro(tg, azione, par, scelti)
        adesso = int(time.time())
        con = db()
        con.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,quantita,stato,consegna_scelta,spedizione_sats,"
            "creato,aggiornato) VALUES(?,?,?,30000,1,'creato','spedizione',"
            "0,?,?)", (ids["a"], COMPRA, VENDE, adesso, adesso))
        con.execute("UPDATE annunci SET prezzo_eur=21.0 WHERE id=?",
                    (ids["euro"],))
        con.commit()
        con.close()
        return piano
    SRV._mm_giro = giro_poi_compra
    try:
        r = c.post("/api/me/modifica-massiva/applica", json={
            "ids": [ids["a"], ids["euro"], ids["accettata"]],
            "azione": "percento", "percento": "+10"})
    finally:
        SRV._mm_giro = vero_giro
    d = r.json()
    m = motivi(d)
    prova("l'ordine nato fra il piano e la scrittura: «ordine»",
          ("ordine", 15000), (m.get(ids["a"]), riga(ids["a"])["prezzo_sats"]))
    prova("la riga cambiata sotto i piedi: «cambiato», e resta la sua",
          ("cambiato", 21.0), (m.get(ids["euro"]), riga(ids["euro"])["prezzo_eur"]))

    # ---------------------------------------------------------------
    print("\n[l'eliminazione: conferma scritta, niente annulla]")
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["creato"]], "azione": "elimina"})
    prova("senza la conferma: 400, e resta", (400, "attivo"),
          (r.status_code, riga(ids["creato"])["stato"]))
    DOPO.clear()
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["creato"], ids["ordine"], ids["revisione"], ids["nostr"],
                ids["fermo"]], "azione": "elimina", "conferma": "elimina"})
    d = r.json()
    m = motivi(d)
    prova("via «creato», «revisione» e l'importato", ("rimosso",) * 3,
          (riga(ids["creato"])["stato"], riga(ids["revisione"])["stato"],
           riga(ids["nostr"])["stato"]))
    con = db()
    ordine_creato = con.execute(
        "SELECT stato FROM ordini WHERE annuncio_id=? AND prezzo_sats=33000",
        (ids["creato"],)).fetchone()["stato"]
    con.close()
    prova("...e l'ordine mai pagato su «creato» si annulla", "annullato",
          ordine_creato)
    prova("l'affare saldo ferma l'eliminazione: «ordine»", "ordine",
          m.get(ids["ordine"]))
    prova("l'esaurito non si elimina da qui: «esaurito»",
          ("esaurito", "venduto"), (m.get(ids["fermo"]), riga(ids["fermo"])["stato"]))
    prova("il mondo: kind 5 e canale («ritira»)",
          {ids[n]: "ritira" for n in ("creato", "revisione", "nostr")},
          DOPO[-1][1] if DOPO else {})
    prova("nessun registro da annullare", (0, 0),
          (d.get("registro"), d.get("annullabile_fino")))
    con = db()
    rid_el = con.execute("SELECT id FROM modifiche_massive WHERE "
                         "azione='elimina'").fetchone()["id"]
    con.close()
    r = c.post("/api/me/modifica-massiva/annulla", json={"registro": rid_el})
    prova("l'annulla di un'eliminazione: 400", (400, True),
          (r.status_code, "non si annulla" in r.json().get("detail", "")))

    # ---------------------------------------------------------------
    print("\n[l'annulla scade a 24 ore]")
    r = c.post("/api/me/modifica-massiva/applica", json={
        "ids": [ids["accettata"]], "azione": "quantita", "quantita": "9"})
    rid_q = r.json().get("registro")
    con = db()
    con.execute("UPDATE modifiche_massive SET creato=creato-86401 WHERE id=?",
                (rid_q,))
    con.commit()
    con.close()
    r = c.post("/api/me/modifica-massiva/annulla", json={"registro": rid_q})
    prova("oltre le 24 ore: 400, e la quantita' resta", (400, 9),
          (r.status_code, riga(ids["accettata"])["quantita"]))
    prova("...e l'elenco non la propone piu' come ultima", True,
          (c.get("/api/me/modifica-massiva").json().get("ultima") or {})
          .get("id") != rid_q)
    prova("l'annuncio di 111 non l'ha toccato nessuno",
          (1000, "attivo", 1), campi(ids["altrui"], "prezzo_sats", "stato",
                                     "quantita"))
    prova("in tutto il giro, nessuna moderazione", [], MODERATI)
    prova("...e nessun avviso ai moderatori", [], banco.AVVISI)

    # ---------------------------------------------------------------
    print("\n[i relay: a lotti, un giro per venditore, i gesti giusti]")
    FUORI = []

    async def rilancia(aid, status, solo_aggiornamento=False):
        FUORI.append(("nip99", aid, status, solo_aggiornamento))
        await asyncio.sleep(0)

    async def ritira(aid, *a, **k):
        FUORI.append(("kind5", aid))
        return 1

    async def canale_venduto(aid, venduto=True):
        FUORI.append(("canale", aid, venduto))

    async def canale_via(aid):
        FUORI.append(("canale_via", aid))
    veri = (SRV.annuncio_su_nostr, SRV.ritira_da_nostr, SRV.promo_venduto,
            SRV.promo_rimuovi, SRV.PAUSA_NOSTR, SRV.LOTTO_NOSTR)
    SRV.annuncio_su_nostr, SRV.ritira_da_nostr = rilancia, ritira
    SRV.promo_venduto, SRV.promo_rimuovi = canale_venduto, canale_via
    SRV.PAUSA_NOSTR, SRV.LOTTO_NOSTR = 0, 5
    lotti = []
    vero_gather = SRV.asyncio.gather

    async def conta_lotti(*coros, **k):
        lotti.append(len(coros))
        return await vero_gather(*coros, **k)
    SRV.asyncio.gather = conta_lotti
    try:
        asyncio.run(SRV._mm_fuori(VENDE, {i: "aggiorna" for i in range(1, 13)}))
        prova("dodici rilanci in lotti da cinque", [5, 5, 2], lotti)
        prova("...tutti NIP-99 in aggiornamento",
              {("nip99", "active", True)},
              {(x[0], x[2], x[3]) for x in FUORI})
        FUORI.clear()
        asyncio.run(SRV._mm_fuori(VENDE, {1: "sold", 2: "active", 3: "ritira"}))
        prova("sold: lo stato NIP-99 e la spunta del canale", True,
              ("nip99", 1, "sold", True) in FUORI
              and ("canale", 1, True) in FUORI)
        prova("active: il viaggio inverso", True,
              ("nip99", 2, "active", True) in FUORI
              and ("canale", 2, False) in FUORI)
        prova("ritira: kind 5 e post del canale tolto", True,
              ("kind5", 3) in FUORI and ("canale_via", 3) in FUORI)
        FUORI.clear()

        async def due_giri():
            primo = asyncio.create_task(
                SRV._mm_fuori(VENDE, {i: "aggiorna" for i in range(1, 9)}))
            await asyncio.sleep(0)
            await SRV._mm_fuori(VENDE, {20: "aggiorna"})
            prova("il secondo giro si ACCODA al primo", True,
                  VENDE in SRV._MM_CODA)
            await primo
        asyncio.run(due_giri())
        prova("...e alla fine ci sono tutti, una volta sola",
              [1, 2, 3, 4, 5, 6, 7, 8, 20], sorted(x[1] for x in FUORI))
        prova("la coda si chiude a giro finito", False, VENDE in SRV._MM_CODA)
    finally:
        (SRV.annuncio_su_nostr, SRV.ritira_da_nostr, SRV.promo_venduto,
         SRV.promo_rimuovi, SRV.PAUSA_NOSTR, SRV.LOTTO_NOSTR) = veri
        SRV.asyncio.gather = vero_gather

    # ---------------------------------------------------------------
    # IL GIRO ARRIVA AI CANALI (17 ott 2026, cantiere venduto-canale):
    # pausa ed eliminazione in blocco su annunci col post nel canale, con
    # `promo_venduto` e `promo_rimuovi` VERI — e' qui che il giro dal
    # vivo del 16 ott ha visto «'sqlite3.Row' object has no attribute
    # 'get'». Di cartone solo Telegram (chi chiama e con cosa) e i relay.
    print("\n[il giro della modifica in blocco arriva ai canali: pausa ed "
          "elimina]")
    con = db()
    pausa_id, via_id = (con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats,post_canale_id) VALUES(?,?,'d',20000,'Altro',"
        "'Torino (TO)','attivo',1,'spedizione',2,'sats','buono',3000,?)",
        (VENDE, titolo, msg)).lastrowid
        for titolo, msg in (("Col post, in pausa", 501), ("Col post, via", 502)))
    con.commit()
    con.close()
    TELEGRAM, STAMPE = [], []

    async def bot_api(metodo, dati):
        TELEGRAM.append((metodo, dati.get("chat_id"), dati.get("message_id")))
        return {"ok": True}

    async def niente(*a, **k):
        return 0
    veri = (SRV.bot_api, SRV.canale_id, SRV.canale_vetrina,
            SRV.canale_bitcoin_podcast, SRV.annuncio_su_nostr,
            SRV.ritira_da_nostr, SRV.PAUSA_NOSTR)
    SRV.bot_api = bot_api
    SRV.canale_id = lambda: "@nostro"
    SRV.canale_vetrina = lambda: ""
    SRV.canale_bitcoin_podcast = lambda: ""
    SRV.annuncio_su_nostr = SRV.ritira_da_nostr = niente
    SRV.PAUSA_NOSTR = 0
    # le stampe del server: un «saltato» qui e' il guasto
    SRV.print = lambda *a, **k: STAMPE.append(" ".join(map(str, a)))
    try:
        DOPO.clear()
        r = c.post("/api/me/modifica-massiva/applica", json={
            "ids": [pausa_id], "azione": "pausa"})
        prova("la pausa in blocco: 200, e il gesto verso il mondo e' «sold»",
              (200, {pausa_id: "sold"}),
              (r.status_code, DOPO[-1][1] if DOPO else {}))
        asyncio.run(SRV._mm_fuori(VENDE, DOPO[-1][1] if DOPO else {}))
        # (18 nov 2026, vetrina-pulita) a leva VETRINA_SI_PULISCE accesa,
        # di serie, il post di un annuncio che non si compra piu' si
        # CANCELLA invece di prendere il ✅ (quello resta a leva spenta,
        # o dove Telegram non lascia cancellare: prove_venduto_canale)
        prova("...il post nel canale si cancella (la vetrina si pulisce)",
              True, any(m == "deleteMessage" and ch == "@nostro" and mid == 501
                        for m, ch, mid in TELEGRAM))
        TELEGRAM.clear()
        DOPO.clear()
        r = c.post("/api/me/modifica-massiva/applica", json={
            "ids": [via_id], "azione": "elimina", "conferma": "elimina"})
        prova("l'eliminazione in blocco: 200, e il gesto e' «ritira»",
              (200, {via_id: "ritira"}),
              (r.status_code, DOPO[-1][1] if DOPO else {}))
        asyncio.run(SRV._mm_fuori(VENDE, DOPO[-1][1] if DOPO else {}))
        prova("...il post si cancella dal canale", [("deleteMessage", "@nostro", 502)],
              TELEGRAM)
        prova("...e la colonna del post si azzera", 0,
              riga(via_id)["post_canale_id"])
        prova("nessun «saltato» nelle stampe del server", [],
              [s for s in STAMPE if "saltato" in s])
    finally:
        (SRV.bot_api, SRV.canale_id, SRV.canale_vetrina,
         SRV.canale_bitcoin_podcast, SRV.annuncio_su_nostr,
         SRV.ritira_da_nostr, SRV.PAUSA_NOSTR) = veri
        del SRV.print

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
