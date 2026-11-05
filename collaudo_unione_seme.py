# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'UNIONE COL SEME UNICO (5 nov 2026, cantiere unione-seme).

Andrea: un account Telegram e uno Nostr della stessa persona si uniscono
(ordini e catalogo), i conflitti si segnalano agli admin, e del wallet
on-chain resta UN seme solo: lo scartato vive una settimana e poi se ne
va, ma MAI se ha dei sats. Qui, col server VERO e un database
usa-e-getta:
  1. con un ordine on-chain aperto (con chiunque) l'unione si ferma, e
     la frase dice perche';
  2. chiuso l'ordine, l'unione passa e lo storico on-chain la segue;
  3. Telegram senza seme, Nostr con: il seme della meta' Nostr passa
     (xpub, impronta, destinazione firmata), e il telefono legge
     «spostalo» (`scade` 0);
  4. tutti e due col seme: resta quello di Telegram, lo scartato va in
     `unioni_semi` con la settimana, e il conflitto finisce nel cassetto
     degli admin («🔀 Unioni»), che solo un moderatore apre e che
     «Guardata» svuota;
  5. `lascia`: prima della settimana no; dopo, no con un ordine aperto o
     con dei sats su un suo indirizzo; no con la rete muta; si' vuoto.

NON TOCCA NIENTE DI VERO: config finto prima dell'import, nessuna rete
(la sonda di mempool e' sostituita da una finta).

USO:  python collaudo_unione_seme.py
"""

import json
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

PASSATE = FALLITE = 0

TG = 7712345601        # l'account Telegram (sopravvive)
ALTRO = 7712345699     # una terza persona
NOSTR_1 = -881234501   # le meta' Nostr dei tre giri
NOSTR_2 = -881234502
NOSTR_3 = -881234503
TG_2 = 7712345602
TG_3 = 7712345603
XPUB_TG = "tpubTELEGRAM" + "a" * 99
XPUB_N = "tpubNOSTR" + "b" * 102


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
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-unione-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
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
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    os.chdir(QUI)
    import server
    return server


def h(tg, nome="Prova"):
    return {"X-Tg-Init-Data": f"collaudo:{tg}:{nome}"}


def npub_di(n):
    return "npub1" + str(abs(n)).rjust(58, "q")[:58]


def due_meta(srv, tg, nostr, nome_tg="Mario", nome_n="mario_nostr"):
    con = srv.db()
    srv._upsert_da_telegram(con, tg, nome_tg, nome_tg.lower())
    srv._upsert_da_telegram(con, ALTRO, "Altro", "altro")
    con.execute("INSERT INTO utenti(tg_id, nome, npub, npub_verificata, "
                "npub_accesso, negozio) VALUES (?,?,?,?,?,?)",
                (nostr, nome_n, npub_di(nostr), 1, npub_di(nostr),
                 f"n{abs(nostr)}"))
    con.commit()
    con.close()


def seme(srv, tg, impronta, xpub):
    con = srv.db()
    srv._wallet_prepara(con)
    srv._onchain_prepara_tabelle(con)
    adesso = int(time.time())
    con.execute("INSERT INTO wallet_unico(tg_id, impronta, prossimo, creato, "
                "aggiornato) VALUES (?,?,?,?,?)", (tg, impronta, 3, adesso,
                                                   adesso))
    con.execute("INSERT INTO onchain_xpub(tg_id, xpub, creato, aggiornato) "
                "VALUES (?,?,?,?)", (tg, xpub, adesso, adesso))
    con.execute("INSERT INTO onchain_incasso(tg_id, tipo, valore, firma, "
                "creato, aggiornato) VALUES (?,?,?,?,?,?)",
                (tg, "indirizzo", f"tb1q{abs(tg)}", "f" * 128, adesso, adesso))
    con.commit()
    con.close()


def ordine_onchain(srv, compratore, venditore, xpub_c, stato, ind):
    """Un indirizzo 2-di-3 e il suo ordine, scritti dritti (la cassa
    vera vorrebbe embit e la rete: qui si collauda l'unione)."""
    con = srv.db()
    srv._onchain_prepara_tabelle(con)
    srv._onchain_prepara_ordini(con)
    adesso = int(time.time())
    cur = con.execute(
        "INSERT INTO onchain_indirizzi(rete, compratore_id, venditore_id, "
        "xpub_compratore, numero_compratore, xpub_venditore, "
        "numero_venditore, xpub_barattolo, numero_barattolo, "
        "chiave_compratore, chiave_venditore, chiave_barattolo, descrittore, "
        "indirizzo, creato) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("testnet4", compratore, venditore, xpub_c, ind, "tpubV" + str(ind),
         ind, "tpubB", ind, "02" + "1" * 64, "02" + "2" * 64, "02" + "3" * 64,
         "wsh(...)", f"tb1qmulti{ind}", adesso))
    iid = cur.lastrowid
    con.execute(
        "INSERT INTO onchain_ordini(indirizzo_id, annuncio_id, compratore_id, "
        "venditore_id, prezzo_sats, margine_sats, importo_sats, incasso, "
        "rimborso, stato, scade, creato, aggiornato) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (iid, 1, compratore, venditore, 10000, 600, 10600, "tb1qincasso",
         f"tb1qrimborso{ind}", stato, adesso + 86400, adesso, adesso))
    con.commit()
    con.close()
    return iid


def uno(srv, sql, *a):
    con = srv.db()
    try:
        return con.execute(sql, a).fetchone()
    finally:
        con.close()


def main():
    srv = avvio()
    from fastapi.testclient import TestClient
    cli = TestClient(srv.app)
    # le tabelle pigre degli ordini on-chain nascono qui
    con = srv.db()
    srv._onchain_prepara_tabelle(con)
    srv._onchain_prepara_ordini(con)
    con.commit()
    con.close()

    print("1-2. l'on-chain in corso ferma l'unione, chiuso passa")
    due_meta(srv, TG, NOSTR_1)
    seme(srv, NOSTR_1, "aaaa0001", XPUB_N)
    ordine_onchain(srv, NOSTR_1, ALTRO, XPUB_N, "attesa", 1)
    esito = srv.esegui_fusione(TG, NOSTR_1)
    prova("con un ordine on-chain aperto l'unione dice di no",
          True, isinstance(esito, str) and "on-chain" in esito)
    prova("...e la meta' Nostr c'e' ancora", True,
          uno(srv, "SELECT 1 FROM utenti WHERE tg_id=?", NOSTR_1) is not None)
    con = srv.db()
    con.execute("UPDATE onchain_ordini SET stato='rilasciato' "
                "WHERE compratore_id=?", (NOSTR_1,))
    con.commit()
    con.close()
    esito = srv.esegui_fusione(TG, NOSTR_1)
    prova("chiuso l'ordine, l'unione passa", True, isinstance(esito, dict))
    prova("lo storico on-chain segue l'account", (TG,),
          tuple(uno(srv, "SELECT compratore_id FROM onchain_ordini "
                         "WHERE rimborso='tb1qrimborso1'")))
    prova("...anche l'indirizzo del 2-di-3", (TG,),
          tuple(uno(srv, "SELECT compratore_id FROM onchain_indirizzi "
                         "WHERE indirizzo='tb1qmulti1'")))

    print("3. Telegram senza seme: passa quello della meta' Nostr")
    prova("la xpub passa a Telegram", (XPUB_N,),
          tuple(uno(srv, "SELECT xpub FROM onchain_xpub WHERE tg_id=?", TG)))
    prova("l'impronta passa", ("aaaa0001",),
          tuple(uno(srv, "SELECT impronta FROM wallet_unico WHERE tg_id=?", TG)))
    prova("la destinazione firmata passa",
          (f"tb1q{abs(NOSTR_1)}",),
          tuple(uno(srv, "SELECT valore FROM onchain_incasso WHERE tg_id=?",
                    TG)))
    prova("nessuna riga resta alla meta' che muore", None,
          uno(srv, "SELECT 1 FROM onchain_xpub WHERE tg_id=?", NOSTR_1))
    r = cli.get("/api/wallet/unione", headers=h(TG))
    prova("il telefono legge «sposta le parole» (scade 0)",
          [{"da_id": NOSTR_1, "impronta": "aaaa0001", "scade": 0}],
          r.json().get("semi"))
    r = cli.post("/api/wallet/unione/lascia", headers=h(TG),
                 json={"impronta": "aaaa0001"})
    prova("spostate, la riga se ne va", {"libero": True, "motivo": ""},
          r.json())
    prova("...e non c'e' piu'", [],
          cli.get("/api/wallet/unione", headers=h(TG)).json().get("semi"))

    print("4. due semi: resta Telegram, lo scartato aspetta una settimana")
    due_meta(srv, TG_2, NOSTR_2, nome_tg="Lucia", nome_n="lucia_n")
    seme(srv, TG_2, "bbbb0002", XPUB_TG)
    seme(srv, NOSTR_2, "cccc0002", XPUB_N + "2")
    prima = int(time.time())
    esito = srv.esegui_fusione(TG_2, NOSTR_2)
    prova("l'unione passa", True, isinstance(esito, dict))
    prova("il riepilogo conta i conflitti (nome + wallet)", 2,
          esito.get("conflitti"))
    prova("resta la xpub di Telegram", (XPUB_TG,),
          tuple(uno(srv, "SELECT xpub FROM onchain_xpub WHERE tg_id=?", TG_2)))
    prova("resta l'impronta di Telegram", ("bbbb0002",),
          tuple(uno(srv, "SELECT impronta FROM wallet_unico WHERE tg_id=?",
                    TG_2)))
    prova("la destinazione resta quella di Telegram",
          (f"tb1q{TG_2}",),
          tuple(uno(srv, "SELECT valore FROM onchain_incasso WHERE tg_id=?",
                    TG_2)))
    semi = cli.get("/api/wallet/unione", headers=h(TG_2)).json().get("semi")
    prova("lo scartato e' fra i semi dell'unione", ["cccc0002"],
          [s["impronta"] for s in semi])
    prova("...con la settimana", True,
          bool(semi) and abs(semi[0]["scade"] - prima - 7 * 86400) < 60)
    prova("un altro account non lo vede", [],
          cli.get("/api/wallet/unione", headers=h(ALTRO)).json().get("semi"))
    prova("chi non e' moderatore non apre il cassetto", 403,
          cli.get("/api/admin/unioni", headers=h(TG_2)).status_code)
    r = cli.get("/api/admin/unioni", headers=h(999, "Admin"))
    righe = [x for x in r.json() if x["tg_id"] == TG_2]
    prova("il cassetto degli admin ha l'unione", 1, len(righe))
    voci = righe[0]["conflitti"] if righe else []
    prova("...col wallet scartato detto a parole", True,
          any("due wallet on-chain" in v and "cccc0002" in v for v in voci))
    prova("...e il nome scartato", True,
          any("lucia_n" in v for v in voci))
    rid = righe[0]["id"] if righe else 0
    prova("«Guardata» da un non moderatore: 403", 403,
          cli.post(f"/api/admin/unioni/{rid}/guardata",
                   headers=h(TG_2)).status_code)
    prova("«Guardata» dal moderatore", 200,
          cli.post(f"/api/admin/unioni/{rid}/guardata",
                   headers=h(999, "Admin")).status_code)
    prova("...e il cassetto e' vuoto", [],
          [x for x in cli.get("/api/admin/unioni",
                              headers=h(999, "Admin")).json()
           if x["tg_id"] == TG_2])
    # il giro 1 aveva un seme solo (nessun conflitto on-chain): nel
    # cassetto c'e' solo il nome diverso
    prova("il giro 1 (un seme solo) ha nel cassetto solo il nome", [1],
          [len(x["conflitti"]) for x in cli.get(
              "/api/admin/unioni", headers=h(999, "Admin")).json()
           if x["tg_id"] == TG])

    print("5. lascia: la settimana, gli ordini, i sats, la rete")
    lascia = lambda: cli.post("/api/wallet/unione/lascia", headers=h(TG_2),
                              json={"impronta": "cccc0002"}).json()
    prova("prima della settimana: no", False, lascia()["libero"])
    con = srv.db()
    con.execute("UPDATE unioni_semi SET scade=? WHERE impronta='cccc0002'",
                (int(time.time()) - 1,))
    con.commit()
    con.close()
    # un ordine nato col seme scartato, ancora aperto: un pagamento tardo
    ordine_onchain(srv, TG_2, ALTRO, XPUB_N + "2", "pagato", 2)
    prova("con un ordine aperto nato con lui: no", False, lascia()["libero"])
    con = srv.db()
    con.execute("UPDATE onchain_ordini SET stato='rimborsato' "
                "WHERE rimborso='tb1qrimborso2'")
    con.commit()
    con.close()
    guardati = []

    async def sonda_con_sats(ind):
        guardati.append(ind)
        return [{"value": 1000}] if ind == "tb1qrimborso2" else []
    vera = srv.onchain_mempool_utxo
    srv.onchain_mempool_utxo = sonda_con_sats
    try:
        r = lascia()
        prova("con dei sats sul suo rimborso: no", False, r["libero"])
        prova("...e guarda il 2-di-3 e il rimborso", True,
              {"tb1qmulti2", "tb1qrimborso2"} <= set(guardati))

        async def sonda_muta(ind):
            raise RuntimeError("rete giu'")
        srv.onchain_mempool_utxo = sonda_muta
        prova("con la rete muta: no", False, lascia()["libero"])

        async def sonda_vuota(ind):
            return []
        srv.onchain_mempool_utxo = sonda_vuota
        prova("vuoto e scaduto: si'", True, lascia()["libero"])
        prova("...e la riga se ne va", [],
              cli.get("/api/wallet/unione", headers=h(TG_2)).json()["semi"])
    finally:
        srv.onchain_mempool_utxo = vera
    prova("un'impronta storta: 400", 400,
          cli.post("/api/wallet/unione/lascia", headers=h(TG_2),
                   json={"impronta": "nonvale"}).status_code)

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE or not PASSATE else 0


if __name__ == "__main__":
    sys.exit(main())
