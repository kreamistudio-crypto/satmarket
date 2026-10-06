# -*- coding: utf-8 -*-
"""
🛡️ IL BOLLINO STAFF, SUL SERVER VERO (6 ott 2026).

Il bollino accanto al nome di un admin o di un moderatore lo decide SOLO
il server (`e_staff`), e il client lo disegna dove arriva un si'. `prove.py`
gira i giudici estratti; qui si fa la domanda che solo il server VERO
risponde: le rotte che portano un nome portano anche il si' giusto — e
il tg_id, per dirlo, non esce.

IL GIRO (nel collaudo lo staff e' l'identita' 999, come per `e_admin`):
  - la vetrina, ANONIMA (senza `venditore_id`: si giudica sul codice del
    negozio) e con una sessione (col `venditore_id`);
  - il negozio: il venditore, e le recensioni con chi le ha scritte —
    senza il tg_id di chi scrive;
  - la card dell'altra parte in un ordine (`/api/orders`);
  - il libro del P2P (`/api/p2p/facce`) e la controparte di uno scambio
    (`/api/p2p/controparte`);
  - le dispute P2P viste da un moderatore (`/api/p2p/moderazione`).

Niente parla con Telegram ne' coi relay: il `config` finto e il nodo finto
li installa `avvio()` del banco PRIMA dell'import di server, e in CI c'e' la
gabbia senza rete di `collaudi_ci.py`.

USO:  python collaudo_bollino_staff.py
"""

import time

import collaudo_lnbits_muto as banco

prova = banco.prova
ANONIMO = {}
STAFF = {"X-Tg-Init-Data": "collaudo:999:Admin"}
VENDITORE = {"X-Tg-Init-Data": "collaudo:222:Venditore"}
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
ORD_STAFF = "bollino-staff-0001"     # pubblicato dallo staff, preso da 111
ORD_ALTRO = "bollino-altro-0002"     # pubblicato da 222, preso da 999


def main():
    print("=" * 58)
    print("  🛡️ IL BOLLINO STAFF — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    c = TestClient(banco.SRV.app)
    giro(c, banco.SRV)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


def annuncio(con, chi, titolo):
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(?,?,'desc',1000,'Altro','Torino (TO)','attivo',?,"
        "'ritiro',1,'sats','buono')", (chi, titolo, int(time.time())))
    return cur.lastrowid


def giro(c, SRV):
    # le tre identita' nascono alla prima richiesta, col loro negozio
    for h in (STAFF, VENDITORE, COMPRATORE):
        prova("l'identita' di collaudo entra", 200,
              c.get("/api/me", headers=h).status_code)
    con = SRV.db()
    cod = {r["tg_id"]: r["negozio"] for r in con.execute(
        "SELECT tg_id, negozio FROM utenti WHERE tg_id IN (111,222,999)")}
    a_staff = annuncio(con, 999, "Tazza dello staff")
    a_altro = annuncio(con, 222, "Tazza del venditore")
    con.commit()
    con.close()
    prova("ognuno ha il suo codice del negozio", True,
          all(cod.get(t) for t in (111, 222, 999)))

    print("\n[la vetrina]")
    for chi, h in (("anonima", ANONIMO), ("con una sessione", COMPRATORE)):
        r = c.get("/api/listings?limit=50", headers=h)
        righe = r.json()
        righe = righe.get("annunci", righe) if isinstance(righe, dict) else righe
        per_id = {x["id"]: x for x in righe}
        prova(f"vetrina {chi}: l'annuncio dello staff porta il bollino, "
              "l'altro no", (True, False),
              (per_id.get(a_staff, {}).get("venditore_staff"),
               per_id.get(a_altro, {}).get("venditore_staff")))
        if not h:
            prova("...e all'anonimo il tg_id di chi vende non esce (il si' "
                  "nasce dal codice del negozio)", False,
                  any("venditore_id" in x for x in righe))
    r = c.get(f"/api/listings/{a_staff}", headers=ANONIMO)
    prova("la scheda dell'annuncio, aperta da sola, lo porta",
          (200, True), (r.status_code, r.json().get("venditore_staff")))

    print("\n[il negozio e le recensioni]")
    con = SRV.db()
    adesso = int(time.time())
    for da in (999, 111):
        con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, "
                    "voto, commento, creato) VALUES(0,?,222,5,'ok',?)",
                    (da, adesso - da))
    con.commit()
    con.close()
    d = c.get(f"/api/negozio/{cod[999]}", headers=ANONIMO).json()
    prova("il negozio dello staff: il venditore porta il bollino",
          True, d["venditore"].get("staff"))
    prova("...e il tg_id resta dentro", False, "tg_id" in d["venditore"])
    d = c.get(f"/api/negozio/{cod[222]}", headers=ANONIMO).json()
    prova("il negozio di un altro no", False, d["venditore"].get("staff"))
    # la piu' recente in testa: quella di 111 (adesso-111), poi lo staff
    prova("le recensioni: chi le ha scritte, col suo nome di sempre",
          ["Compratore", "Admin"], [f.get("da_nome") for f in d["feedback"]])
    prova("...quella dello staff col bollino, l'altra senza",
          [False, True], [f.get("da_staff") for f in d["feedback"]])
    prova("...e chi scrive esce senza il suo tg_id", False,
          any("da_tg_id" in f for f in d["feedback"]))

    print("\n[la card dell'altra parte in un ordine]")
    con = SRV.db()
    con.execute("INSERT INTO ordini(annuncio_id, compratore_id, venditore_id, "
                "prezzo_sats, stato, creato) VALUES(?,111,999,1000,'locked',?)",
                (a_staff, adesso))
    con.commit()
    con.close()
    o = [x for x in c.get("/api/orders", headers=COMPRATORE).json()
         if x.get("annuncio_id") == a_staff]
    prova("chi compra dallo staff vede il bollino sul volto di chi vende",
          True, bool(o) and (o[0].get("volto_venditore") or {}).get("staff"))
    o = [x for x in c.get("/api/orders", headers=STAFF).json()
         if x.get("annuncio_id") == a_staff]
    prova("...e lo staff, dall'altra parte, vede chi compra senza (la "
          "chiave non c'e' proprio)", (True, False),
          (bool(o) and bool(o[0].get("volto_compratore")),
           bool(o) and "staff" in (o[0].get("volto_compratore") or {})))

    print("\n[il libro e la controparte del P2P]")
    con = SRV.db()
    con.execute("INSERT INTO p2p_ordini(ordine, tg_id, creato, maker, preso_da) "
                "VALUES(?,999,?,1,111)", (ORD_STAFF, adesso))
    con.execute("INSERT INTO p2p_ordini(ordine, tg_id, creato, maker, preso_da) "
                "VALUES(?,222,?,1,999)", (ORD_ALTRO, adesso))
    con.commit()
    con.close()
    r = c.post("/api/p2p/facce", headers=COMPRATORE,
               json={"ordini": [ORD_STAFF, ORD_ALTRO]})
    f = r.json().get("facce", {})
    prova("il libro: il volto di chi ha pubblicato porta il si' giusto (e "
          "negli altri la chiave non c'e')", (200, True, True, False),
          (r.status_code, f.get(ORD_STAFF, {}).get("staff"),
           bool(f.get(ORD_ALTRO)), "staff" in f.get(ORD_ALTRO, {})))
    prova("...e il tg_id di chi pubblica non esce", False,
          any("tg_id" in v for v in f.values()))
    r = c.post("/api/p2p/controparte", headers=COMPRATORE,
               json={"ordini": [ORD_STAFF]})
    prova("la controparte: chi ha preso dallo staff vede il bollino",
          (200, True), (r.status_code,
                        r.json().get("controparti", {}).get(ORD_STAFF, {}).get("staff")))
    r = c.post("/api/p2p/controparte", headers=STAFF,
               json={"ordini": [ORD_STAFF, ORD_ALTRO]})
    cp = r.json().get("controparti", {})
    prova("...e lo staff vede le sue controparti senza",
          (True, True, False, False),
          (bool(cp.get(ORD_STAFF)), bool(cp.get(ORD_ALTRO)),
           "staff" in cp.get(ORD_STAFF, {}), "staff" in cp.get(ORD_ALTRO, {})))

    print("\n[le dispute, viste da un moderatore]")
    con = SRV.db()
    con.execute("INSERT INTO p2p_dispute(ordine, aperta_il, compratore, venditore, "
                "stato, presa_da) VALUES(?,?,999,222,'presa',999)",
                (ORD_ALTRO, adesso))
    con.commit()
    con.close()
    r = c.post("/api/p2p/moderazione", headers=STAFF)
    dd = [x for x in r.json().get("dispute", []) if x["ordine"] == ORD_ALTRO]
    prova("le parti: chi compra e' dello staff, chi vende no; e chi l'ha "
          "presa lo e'", (200, True, False, True),
          (r.status_code,) + ((dd[0].get("compra_staff"), dd[0].get("vende_staff"),
                               dd[0].get("presa_da_staff")) if dd else (None,) * 3))
    prova("...e a chi non e' moderatore la porta resta chiusa", 403,
          c.post("/api/p2p/moderazione", headers=VENDITORE).status_code)


if __name__ == "__main__":
    raise SystemExit(main())
