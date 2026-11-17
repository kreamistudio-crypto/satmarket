# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEGLI AVVISI DEL BARATTOLO (17 nov 2026, cantiere
avvisi-barattolo, voce #99 del Todo).

Chi mette un articolo nel barattolo sceglie cosa farsi dire dal bot su
quell'articolo: il prezzo che scende, lo sconto lampo, «ne resta solo
uno», il ritorno in vetrina. Qui il server VERO, per HTTP con la
TestClient e l'identita' di collaudo nell'header:
  1) la migrazione: un database di ieri, col barattolo senza le colonne
     nuove, si apre e la riga di prima resta NULL (solo la lampo);
  2) la riga nuova nasce con le quattro spunte e la fotografia, e il
     cassetto le rilegge;
  3) le spunte si cambiano, solo su una riga che c'e' e solo coi nomi
     ammessi;
  4) il giro dell'orologio: il calo, l'ultimo pezzo, il rifornimento
     dalla rotta vera della quantita', il tetto di un avviso al giorno;
  5) la lampo dalla rotta vera: alla riga di prima si', a chi l'ha tolta
     no;
  6) a leva spenta tutto torna com'era.
Di finto ci sono solo le notifiche (si contano) e la rete.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, nessuna rete.

USO:  python collaudo_avvisi_barattolo.py
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
NOTIFICHE = []
LAMPO = []          # i destinatari che la rotta della lampo ha scelto

COMPRA, VENDE, VECCHIO, SCHIZZINOSO = 111, 222, 333, 444


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il database di IERI prima dell'import: la tabella `preferiti`
    com'era fino al 16 nov 2026, con una riga dentro. L'avvio del server
    la deve allargare senza toccare la riga."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-avvisi-jar-"),
                      "usa-e-getta.db")
    vecchio = sqlite3.connect(db)
    vecchio.execute("CREATE TABLE preferiti(tg_id INTEGER NOT NULL, "
                    "annuncio_id INTEGER NOT NULL, creato INTEGER, "
                    "PRIMARY KEY(tg_id, annuncio_id))")
    vecchio.execute("INSERT INTO preferiti VALUES(?, 1, 1)", (VECCHIO,))
    vecchio.commit()
    vecchio.close()
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

    async def nota_finta(tg_id, testo, *a, **k):
        NOTIFICHE.append((tg_id, testo, k.get("bottone")))
        return ""

    async def zitto(*a, **k):
        return None

    async def lampo_finta(a, percento, scadenza, savers):
        # l'invio vero parte in create_task nel loop della TestClient, che
        # si ferma a risposta data: si guarda CHI la rotta ha scelto, cioe'
        # la parte che questo cantiere ha toccato
        LAMPO.append(sorted(savers))

    server.notifica = nota_finta
    server._avvisa_savers_lampo = lampo_finta
    server.accoda_colpo = lambda *a, **k: None
    for nome in ("notifica_admin", "annuncio_su_nostr", "promo_venduto",
                 "promo_lampo", "premia_distintivi", "premia_xp"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    return db


def chi(tg_id):
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:Utente{tg_id}"}


def semina():
    con = SRV.db()
    for tg_id in (COMPRA, VENDE, VECCHIO, SCHIZZINOSO):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg_id, f"Utente{tg_id}", f"neg{tg_id}"))
    # id 1 e' la bici, la stessa che la riga di ieri ha nel barattolo
    for titolo, sats, eur, valuta, qta in (("Bici", 100000, 0, "sats", 3),
                                           ("Vaso", 20000, 20.0, "eur", 1)):
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "prezzo_eur,categoria,zona,stato,creato,consegna,quantita,"
            "quantita_max,valuta,condizione) VALUES(?,?,'una cosa',?,?,"
            "'Altro','Pavia (PV)','attivo',1,'ritiro',?,?,?,'nuovo')",
            (VENDE, titolo, sats, eur, qta, qta, valuta))
    con.commit()
    con.close()
    return {"bici": 1, "vaso": 2}


def riga(tg_id, annuncio_id):
    con = SRV.db()
    r = con.execute("SELECT avvisi, avvisi_foto, avvisato FROM preferiti "
                    "WHERE tg_id=? AND annuncio_id=?",
                    (tg_id, annuncio_id)).fetchone()
    con.close()
    return dict(r) if r else None


def sql(q, *a):
    con = SRV.db()
    con.execute(q, a)
    con.commit()
    con.close()


def giro():
    NOTIFICHE.clear()
    asyncio.run(SRV.giro_avvisi_barattolo())
    return [(t, testo) for t, testo, _b in NOTIFICHE]


def main():
    print("=" * 58)
    print("  GLI AVVISI DEL BARATTOLO — il giro vero")
    print("=" * 58)
    avvio()
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    A = semina()
    bici, vaso = A["bici"], A["vaso"]

    # ------------------------------------------------------------------
    print("\n[1) la migrazione: il database di ieri si apre]")
    prova("la riga di prima e' ancora li', con avvisi NULL e niente "
          "fotografia", {"avvisi": None, "avvisi_foto": "", "avvisato": 0},
          riga(VECCHIO, bici))
    prova("/api/me dice la leva accesa", True,
          c.get("/api/me", headers=chi(COMPRA)).json().get("avvisi_barattolo"))

    # ------------------------------------------------------------------
    print("\n[2) la riga nuova nasce con le spunte e la fotografia]")
    r = c.post(f"/api/listings/{bici}/preferito", headers=chi(COMPRA))
    prova("il salvataggio risponde con le quattro spunte",
          (200, True, ["prezzo", "lampo", "ultimo", "rientro"]),
          (r.status_code, r.json().get("salvato"), r.json().get("avvisi")))
    rr = riga(COMPRA, bici)
    prova("nel database: le spunte e la fotografia di adesso",
          ("prezzo,lampo,ultimo,rientro",
           {"v": "sats", "p": 100000, "u": False, "c": True}),
          (rr["avvisi"], json.loads(rr["avvisi_foto"] or "null")))
    c.post(f"/api/listings/{vaso}/preferito", headers=chi(COMPRA))
    prova("il vaso in euro si fotografa in euro", {"v": "eur", "p": 20.0},
          {k: v for k, v in json.loads(riga(COMPRA, vaso)["avvisi_foto"]).items()
           if k in ("v", "p")})
    lista = c.get("/api/me/preferiti", headers=chi(COMPRA)).json()
    prova("il cassetto rilegge le spunte di ogni riga",
          {bici: ["prezzo", "lampo", "ultimo", "rientro"],
           vaso: ["prezzo", "lampo", "ultimo", "rientro"]},
          {x["id"]: x.get("avvisi_barattolo") for x in lista})
    prova("...e alla riga di prima promette solo la lampo", [["lampo"]],
          [x.get("avvisi_barattolo") for x in
           c.get("/api/me/preferiti", headers=chi(VECCHIO)).json()])
    prova("togliere dal barattolo risponde senza spunte", (False, None),
          (lambda j: (j.get("salvato"), j.get("avvisi")))(
              c.post(f"/api/listings/{vaso}/preferito", headers=chi(COMPRA)).json()))
    c.post(f"/api/listings/{vaso}/preferito", headers=chi(COMPRA))

    # ------------------------------------------------------------------
    print("\n[3) le spunte si cambiano: solo su una riga che c'e']")
    r = c.post(f"/api/listings/{bici}/preferito/avvisi",
               json={"avvisi": ["boh"]}, headers=chi(VENDE))
    prova("chi non ha l'articolo nel barattolo → 404, e nessuna riga nasce",
          (404, None), (r.status_code, riga(VENDE, bici)))
    foto_prima = riga(COMPRA, bici)["avvisi_foto"]
    r = c.post(f"/api/listings/{bici}/preferito/avvisi",
               json={"avvisi": ["ultimo", "<script>", "prezzo", "prezzo"]},
               headers=chi(COMPRA))
    prova("solo i nomi ammessi, una volta, nell'ordine di casa",
          (200, ["prezzo", "ultimo"]), (r.status_code, r.json().get("avvisi")))
    prova("...e la fotografia che c'era non si rifa' (il tetto potrebbe "
          "tenere da parte un passaggio)", foto_prima,
          riga(COMPRA, bici)["avvisi_foto"])
    r = c.post(f"/api/listings/{bici}/preferito/avvisi",
               json={"avvisi": ["lampo"]}, headers=chi(VECCHIO))
    prova("la riga di prima che sceglie: spunte salvate e fotografia NUOVA "
          "(parte da adesso)", (200, "lampo", True),
          (r.status_code, riga(VECCHIO, bici)["avvisi"],
           bool(riga(VECCHIO, bici)["avvisi_foto"])))
    sql("UPDATE preferiti SET avvisi=NULL, avvisi_foto='' WHERE tg_id=?", VECCHIO)
    r = c.post(f"/api/listings/{bici}/preferito/avvisi",
               json={"avvisi": "prezzo"}, headers=chi(COMPRA))
    prova("una forma storta vale nessun avviso, non un errore", (200, []),
          (r.status_code, r.json().get("avvisi")))
    c.post(f"/api/listings/{bici}/preferito/avvisi",
           json={"avvisi": ["prezzo", "ultimo", "rientro"]}, headers=chi(COMPRA))

    # ------------------------------------------------------------------
    print("\n[4) il giro dell'orologio]")
    prova("niente e' cambiato: nessun avviso", [], giro())
    sql("UPDATE annunci SET prezzo_sats=80000, quantita=1 WHERE id=?", bici)
    out = giro()
    prova("prezzo sceso e ne resta uno: UN messaggio, solo a chi ha scelto",
          [COMPRA], [t for t, _ in out])
    testo = out[0][1] if out else ""
    prova("...che dice tutti e due i passaggi, col prezzo barrato",
          [True, True], ["<s>100.000 sats</s> → <b>80.000 sats</b> (−20%)" in testo,
                         "Ne resta solo uno" in testo])
    prova("...col tasto che apre l'annuncio", "🫙 Apri l'annuncio",
          (NOTIFICHE[0][2] or ("",))[0] if NOTIFICHE else None)
    prova("la riga di prima non riceve niente dal giro", 0,
          riga(VECCHIO, bici)["avvisato"])
    sql("UPDATE annunci SET prezzo_eur=15.0 WHERE id=?", vaso)
    prova("il vaso sceso in euro: avvisa anche lui (altro articolo, altro "
          "tetto)", [True], [("<s>20,00 €</s> → <b>15,00 €</b>" in t) for _, t in giro()])
    # l'esaurito e il rifornimento, dalla rotta vera della quantita'
    r = c.post(f"/api/listings/{bici}/quantita", json={"quantita": 0},
               headers=chi(VENDE))
    prova("il venditore lo segna esaurito (rotta vera)", (200, True),
          (r.status_code, r.json().get("esaurito")))
    prova("l'esaurito non avvisa", [], giro())
    r = c.post(f"/api/listings/{bici}/quantita", json={"quantita": 4},
               headers=chi(VENDE))
    prova("...e lo rifornisce", (200, True),
          (r.status_code, r.json().get("riattivato")))
    prova("dentro il tetto di 24 ore il rientro aspetta", [], giro())
    sql("UPDATE preferiti SET avvisato=avvisato-? WHERE tg_id=? AND annuncio_id=?",
        25 * 3600, COMPRA, bici)
    out = giro()
    prova("passato il tetto lo dice: «di nuovo disponibile»",
          [(COMPRA, True)], [(t, "di nuovo disponibile" in x) for t, x in out])
    prova("...e una volta sola", [], giro())

    # ------------------------------------------------------------------
    print("\n[5) la lampo dalla rotta vera]")
    c.post(f"/api/listings/{vaso}/preferito", headers=chi(SCHIZZINOSO))
    c.post(f"/api/listings/{vaso}/preferito/avvisi",
           json={"avvisi": ["prezzo"]}, headers=chi(SCHIZZINOSO))
    sql("INSERT INTO preferiti(tg_id, annuncio_id, creato) VALUES(?,?,1)",
        VECCHIO, vaso)
    sql("UPDATE preferiti SET avvisato=0 WHERE annuncio_id=?", vaso)
    r = c.post(f"/api/listings/{vaso}/lampo",
               json={"percento": SRV.LAMPO_MIN_PERCENTO,
                     "ore": SRV.ORE_LAMPO_OPZIONI[0]},
               headers=chi(VENDE))
    prova("la lampo parte", 200, r.status_code)
    prova("arriva a chi l'ha spuntata e alla riga di prima, non a chi "
          "l'ha tolta", [[COMPRA, VECCHIO]], LAMPO)
    prova("...e timbra il tetto di chi l'ha ricevuta, prima dell'invio",
          [True, True, False],
          [riga(t, vaso)["avvisato"] > 0 for t in (COMPRA, VECCHIO, SCHIZZINOSO)])

    # ------------------------------------------------------------------
    print("\n[6) a leva spenta, com'era]")
    SRV.AVVISI_BARATTOLO_ATTIVI = False
    sql("UPDATE annunci SET prezzo_sats=1000 WHERE id=?", bici)
    sql("UPDATE preferiti SET avvisato=0")
    prova("il giro tace", [], giro())
    prova("/api/me dice spento", False,
          c.get("/api/me", headers=chi(COMPRA)).json().get("avvisi_barattolo"))
    r = c.post(f"/api/listings/{bici}/preferito", headers=chi(SCHIZZINOSO))
    prova("la riga nuova nasce come ieri (NULL) e senza spunte in risposta",
          (None, None), (riga(SCHIZZINOSO, bici)["avvisi"], r.json().get("avvisi")))
    prova("la rotta delle spunte dice che non sono attivi", 400,
          c.post(f"/api/listings/{bici}/preferito/avvisi",
                 json={"avvisi": ["prezzo"]}, headers=chi(COMPRA)).status_code)
    SRV.AVVISI_BARATTOLO_ATTIVI = True

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
