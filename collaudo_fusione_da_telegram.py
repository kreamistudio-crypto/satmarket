# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA FUSIONE DAL LATO TELEGRAM (20 ott 2026, cantiere
fusione-da-telegram).

Il caso dal campo, rifatto per intero: un utente entra con NOSTR (da
Tor), si accorge che voleva l'account Telegram, entra con TELEGRAM —
nasce un secondo account — e da li' prova «Entra anche con Nostr» con
la stessa chiave. Prima la risposta era solo «questa chiave apre gia'
un altro account». Ora la firma propone di UNIRE i due, e al «Si'»
tutto quel che era dell'account Nostr passa all'account Telegram:
annunci, affari, recensioni, contatori. Dopo, la chiave Nostr apre
l'account unito.

Il server e' quello VERO, per HTTP con la TestClient, e la firma e' VERA
(Schnorr con coincurve): passano di qui il login Nostr, il login
Telegram di collaudo, la sfida, la verifica della firma, l'indice unico
su npub_accesso e `esegui_fusione` col suo database usa-e-getta.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, nessuna rete, nessun LNbits.

USO:  python collaudo_fusione_da_telegram.py
"""

import hashlib
import json
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = SALTATE = 0
SRV = None


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def salta(nome, perche):
    """Si salta CONTANDO, come collaudo_consegna_firmata: dove manca
    coincurve (il runner della CI) il server non apre nemmeno la porta
    Nostr, e una firma non si puo' fare. Il giro vero gira dove
    coincurve c'e': il PC e il VPS."""
    global SALTATE
    SALTATE += 1
    print(f"  ⊘ {nome} — SALTATA: {perche}")


def avvio():
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-fusione-tg-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    # I segreti col setattr e mai come `NOME = "valore"` (lo scanner
    # della CI non distingue una chiave finta da una vera)
    for k, v in (("BOT_TOKEN", "0:collaudo"),
                 ("ANTHROPIC_API_KEY", "INCOLLA_QUI"),
                 ("LNBITS_URL", "http://127.0.0.1:1"),
                 ("LNBITS_INVOICE_KEY", "INCOLLA_QUI"),
                 ("LNBITS_ADMIN_KEY", "INCOLLA_QUI"),
                 ("ADMIN_IDS", [999]),
                 ("MODALITA_COLLAUDO", True),
                 ("COMMISSIONE_PERCENTO", 0),
                 ("ORE_CONFERMA", 72),
                 ("GIORNI_AUTO_SBLOCCO", 10),
                 ("MODELLO_RICERCA", "claude-haiku-4-5-20251001"),
                 ("MAX_ACCOUNT_BROWSER", 3),
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    return server


def evento_firmato(c, sk):
    """La sfida del login vero, firmata davvero con la chiave `sk`."""
    pub = sk.public_key_xonly.format().hex()
    sfida = c.get("/api/login/nostr/sfida").json()["sfida"]
    ev = {"pubkey": pub, "created_at": int(time.time()), "kind": 22242,
          "tags": [["relay", "http://testserver"], ["challenge", sfida]],
          "content": ""}
    ser = json.dumps([0, pub, ev["created_at"], 22242, ev["tags"], ""],
                     separators=(",", ":"), ensure_ascii=False)
    ev["id"] = hashlib.sha256(ser.encode()).hexdigest()
    ev["sig"] = sk.sign_schnorr(bytes.fromhex(ev["id"])).hex()
    return ev


def entra_nostr(c, sk):
    return c.post("/api/login/nostr", json={"evento": evento_firmato(c, sk)})


def entra_telegram(c, tg, nome):
    return c.post("/api/login/telegram",
                  json={"collaudo": True, "id": tg, "first_name": nome})


def collega(c, sk):
    return c.post("/api/me/npub/collega-firma",
                  json={"evento": evento_firmato(c, sk)})


def unisci(c, token):
    return c.post("/api/me/unisci-nostr", json={"token": token})


def uno(sql, *a):
    con = SRV.db()
    try:
        r = con.execute(sql, a).fetchone()
        return tuple(r) if r is not None else None
    finally:
        con.close()


def scrivi(sql, *a):
    con = SRV.db()
    try:
        con.execute(sql, a)
        con.commit()
    finally:
        con.close()


def main():
    global SRV
    SRV = avvio()
    from fastapi.testclient import TestClient
    try:
        from coincurve import PrivateKey
    except ImportError:
        salta("tutto il collaudo", "manca coincurve: non si puo' firmare, "
              "e il server non apre la porta Nostr")
        print(f"\n  {PASSATE} passate, {FALLITE} fallite, {SALTATE} saltate")
        return 0

    print("=" * 58)
    print("  LA FUSIONE DAL LATO TELEGRAM")
    print("=" * 58)

    # ------------------------------------------------------------------
    print("\n[1) il caso dal campo: prima Nostr, poi Telegram, stesso browser]")
    b = TestClient(SRV.app)
    chiave = PrivateKey()
    npub = SRV.hex_to_npub(chiave.public_key_xonly.format().hex())
    prova("entra con Nostr", 200, entra_nostr(b, chiave).status_code)
    nativo = b.get("/api/me").json()["tg_id"]
    prova("...ed e' un account nato con Nostr (id negativo)", True, nativo < 0)
    # La sua storia: due annunci, una vendita conclusa con la sua
    # recensione, i contatori. Scritti nel database come li lascia l'app.
    adesso = int(time.time())
    for titolo in ("Miele di castagno", "Bici da corsa"):
        scrivi("INSERT INTO annunci(venditore_id, titolo, prezzo_sats, stato, "
               "creato) VALUES(?,?,21000,'attivo',?)", nativo, titolo, adesso)
    entra_telegram(TestClient(SRV.app), 333, "Compratrice")
    scrivi("INSERT INTO ordini(id, compratore_id, venditore_id, prezzo_sats, "
           "stato, creato, aggiornato) VALUES(900, 333, ?, 21000, 'released', ?, ?)",
           nativo, adesso, adesso)
    scrivi("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, commento, "
           "creato) VALUES(900, 333, ?, 5, 'Perfetto', ?)", nativo, adesso)
    scrivi("UPDATE utenti SET vendite_ok=1 WHERE tg_id=?", nativo)

    prova("poi entra con Telegram, nello stesso browser", 200,
          entra_telegram(b, 111, "Mario").status_code)
    prova("...e ora e' l'account Telegram", 111, b.get("/api/me").json()["tg_id"])
    prova("...con i due account aperti, separati", sorted([111, nativo]),
          sorted(x["tg_id"] for x in b.get("/api/sessioni").json()["conti"]))

    # ------------------------------------------------------------------
    print("\n[2) «Entra anche con Nostr» con la stessa chiave: la proposta]")
    r = collega(b, chiave)
    det = r.json().get("detail")
    un = det.get("unione", {}) if isinstance(det, dict) else {}
    prova("non dice piu' solo «gia' creato»: propone l'unione (409 con la "
          "proposta)", (409, True, npub), (r.status_code, bool(un.get("token")),
                                          un.get("npub")))
    prova("...e dice cosa passerebbe di qua", (2, 1), (un.get("annunci"),
                                                     un.get("ordini")))
    prova("...senza il si' non cambia niente: due account, la chiave "
          "all'altro", (npub, ""),
          (uno("SELECT npub_accesso FROM utenti WHERE tg_id=?", nativo)[0],
           uno("SELECT npub_accesso FROM utenti WHERE tg_id=111")[0]))

    # Un altro account Telegram non puo' incassare la proposta di Mario
    altro = TestClient(SRV.app)
    entra_telegram(altro, 222, "Estraneo")
    prova("il token in mano a un altro account non vale", 409,
          unisci(altro, un["token"]).status_code)
    prova("...e intanto l'ha bruciato: nemmeno Mario lo puo' piu' usare", 409,
          unisci(b, un["token"]).status_code)
    prova("...e niente e' stato fuso", True,
          uno("SELECT tg_id FROM utenti WHERE tg_id=?", nativo) is not None)

    # ------------------------------------------------------------------
    print("\n[3) il «Si', unisci»: tutto passa all'account Telegram]")
    un = collega(b, chiave).json()["detail"]["unione"]
    r = unisci(b, un["token"])
    d = r.json()
    prova("l'unione riesce", (200, True, npub, 2, 1),
          (r.status_code, d.get("ok"), d.get("npub"), d.get("annunci"),
           d.get("ordini")))
    prova("l'account nato con Nostr non c'e' piu'", None,
          uno("SELECT tg_id FROM utenti WHERE tg_id=?", nativo))
    prova("...la chiave ora apre l'account Telegram, verificata", (npub, npub, 1),
          uno("SELECT npub, npub_accesso, npub_verificata FROM utenti WHERE tg_id=111"))
    prova("...i suoi annunci sono di Mario", (2, 0),
          (uno("SELECT COUNT(*) FROM annunci WHERE venditore_id=111")[0],
           uno("SELECT COUNT(*) FROM annunci WHERE venditore_id=?", nativo)[0]))
    prova("...e anche la vendita", 111,
          uno("SELECT venditore_id FROM ordini WHERE id=900")[0])
    prova("...e la recensione, col voto che entra nella media", (111, 5.0, 1),
          (uno("SELECT per_tg_id FROM feedback WHERE ordine_id=900")[0],
           *uno("SELECT rating, n_feedback FROM utenti WHERE tg_id=111")))
    prova("...e il contatore delle vendite", 1,
          uno("SELECT vendite_ok FROM utenti WHERE tg_id=111")[0])
    prova("il token non si riusa", 409, unisci(b, un["token"]).status_code)
    prova("nel menu degli account ora ce n'e' uno solo, Mario", [111],
          [x["tg_id"] for x in b.get("/api/sessioni").json()["conti"]])

    # ------------------------------------------------------------------
    print("\n[4) da adesso Telegram o Nostr: e' lo stesso account]")
    nuovo = TestClient(SRV.app)
    prova("un browser nuovo entra con la chiave Nostr", 200,
          entra_nostr(nuovo, chiave).status_code)
    me = nuovo.get("/api/me").json()
    prova("...ed e' l'account di Mario, coi suoi annunci", 111, me["tg_id"])
    prova("«Entra anche con Nostr» di nuovo: l'accesso c'e' gia'", 400,
          collega(b, chiave).status_code)

    # ------------------------------------------------------------------
    print("\n[5) quando NON si unisce]")
    # a) la chiave e' gia' l'accesso di un ALTRO account Telegram
    k2 = PrivateKey()
    t2 = TestClient(SRV.app)
    entra_telegram(t2, 444, "Gianni")
    prova("Gianni collega la sua chiave", 200, collega(t2, k2).status_code)
    t3 = TestClient(SRV.app)
    entra_telegram(t3, 555, "Lucia")
    r = collega(t3, k2)
    prova("Lucia firma con la chiave di Gianni: 409 senza proposta, due "
          "Telegram non diventano uno",
          (409, "Questa chiave e' gia' l'accesso Nostr di un altro account "
                "Telegram: un account, una chiave"),
          (r.status_code, r.json().get("detail")))
    # b) un affare ancora aperto fra le due meta'
    k3 = PrivateKey()
    t4 = TestClient(SRV.app)
    entra_nostr(t4, k3)
    nat3 = t4.get("/api/me").json()["tg_id"]
    entra_telegram(t4, 666, "Paolo")
    scrivi("INSERT INTO ordini(id, compratore_id, venditore_id, prezzo_sats, "
           "stato, creato, aggiornato) VALUES(901, 666, ?, 5000, 'locked', ?, ?)",
           nat3, adesso, adesso)
    r = collega(t4, k3)
    prova("un affare aperto fra le due meta': 409 con la frase della guardia",
          (409, True), (r.status_code, isinstance(r.json().get("detail"), str)
                        and "affare ancora aperto" in r.json()["detail"]))
    prova("...e i due account restano separati", True,
          uno("SELECT tg_id FROM utenti WHERE tg_id=?", nat3) is not None)
    # c) chiuso l'affare, l'unione passa
    scrivi("UPDATE ordini SET stato='released' WHERE id=901")
    un = collega(t4, k3).json()["detail"]["unione"]
    prova("chiuso l'affare, l'unione passa", 200, unisci(t4, un["token"]).status_code)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite, {SALTATE} saltate")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
