# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEGLI ESAURITI CHE NON TORNANO, E DELLA ZONA CHE SI RICORDA
(16 nov 2026, cantiere elimina-esauriti, richiesta di Andrea).

`prove_esauriti_eliminabili` fa girare `rimuovi_annuncio` su un database
di cartone con le sole colonne che servono. Qui gira il SERVER VERO su un
database usa-e-getta, con lo schema vero, e risponde alle domande su cui
il cantiere si regge:

  · l'esaurito si elimina, cioe' si ARCHIVIA: la riga resta 'rimosso',
    l'ordine concluso e la sua recensione restano dove sono, e i due
    ganci (Nostr e canale) partono;
  · da li' sparisce davvero dove si vedeva: lo scaffale «Esauriti di
    recente» del negozio e il link condiviso;
  · un reso ancora in giro ferma il gesto, e l'annuncio resta com'era;
  · /api/me porta la zona dell'ultimo annuncio, e non quella di un
    importato.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Le due piazze sono contatori: si misura se il
gancio PARTE, non cosa dice.

USO:  python collaudo_elimina_esauriti.py
"""

import asyncio
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
RITIRI_NOSTR, RITIRI_CANALE = [], []

VENDITORE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}


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
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-esauriti-"),
                      "usa-e-getta.db")
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

    async def nostr_finto(aid, *a, **k):
        RITIRI_NOSTR.append(aid)
        return 0

    async def canale_finto(aid):
        RITIRI_CANALE.append(aid)

    async def profilo_finto(*a, **k):
        return None

    server.ritira_da_nostr = nostr_finto
    server.promo_rimuovi = canale_finto
    # il rinfresco dell'avatar di /api/me andrebbe a Telegram
    server.aggiorna_profilo_social = profilo_finto
    server.verifica_utente = lambda *a, **k: VENDITORE
    server.utente_se_autenticato = lambda *a, **k: None
    return db


def chiama(fn, *args, **kw):
    """I ganci sono `create_task`: senza cedere il controllo almeno una
    volta il loop si chiuderebbe prima che partano."""
    async def giro():
        r = fn(*args, **kw)
        if asyncio.iscoroutine(r):
            r = await r
        await asyncio.sleep(0.05)
        return r
    return asyncio.run(giro())


def codice_di(fn, *args, **kw):
    try:
        chiama(fn, *args, **kw)
        return 200
    except Exception as e:
        return getattr(e, "status_code", repr(e))


def semina():
    """Un venditore con un negozio: un esaurito venduto davvero (ordine
    concluso e recensione), un esaurito con un reso in corso, e un
    importato da Nostr piu' recente con un'altra zona."""
    con = SRV.db()
    for t in ("feedback", "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "avatar_aggiornato) VALUES(222,'Vende','neg22222',1,?)",
                (int(time.time()),))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    ids = []
    for titolo, zona, creato, nostr in (
            ("Range extender usato", "Dro (TN)", 1000, ""),
            ("Shoyu artigianale", "Dro (TN)", 2000, ""),
            ("Importato dai relay", "Altrove", 9000, "npub1qualcuno")):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
            "valuta,condizione,contatto_nostr) VALUES(222,?,'desc',44000,"
            "'Altro',?,'venduto',?,'spedizione',0,1,'sats','usato',?)",
            (titolo, zona, creato, nostr))
        ids.append(cur.lastrowid)
    adesso = int(time.time())
    for aid, stato in ((ids[0], "released"), (ids[1], "return_pending")):
        con.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,stato,creato,aggiornato,quantita) "
            "VALUES(?,111,222,44000,?,?,?,1)", (aid, stato, adesso, adesso))
    oid = con.execute("SELECT id FROM ordini WHERE annuncio_id=?",
                      (ids[0],)).fetchone()[0]
    con.execute("INSERT INTO feedback(ordine_id,da_tg_id,per_tg_id,voto,commento,creato) "
                "VALUES(?,111,222,5,'Tutto perfetto',?)", (oid, adesso))
    con.commit()
    con.close()
    return ids, oid


def conta(sql, *par):
    con = SRV.db()
    r = con.execute(sql, par).fetchone()[0]
    con.close()
    return r


def stato(aid):
    return conta("SELECT stato FROM annunci WHERE id=?", aid)


def esauriti_del_negozio():
    d = chiama(SRV.negozio, "neg22222", x_tg_init_data="",
               barattolo_sessione="")
    return sorted(a["id"] for a in (d.get("esauriti") or []))


# ---------------------------------------------------------------
def prove_elimina():
    (extender, shoyu, importato), oid = semina()
    print("\n── PRIMA: tutti e due nello scaffale degli esauriti ──")
    prova("il negozio mostra i due esauriti nati qui", sorted([extender, shoyu]),
          [i for i in esauriti_del_negozio() if i != importato])

    print("\n── L'ESAURITO CHE NON TORNA SI ARCHIVIA ──")
    r = chiama(SRV.rimuovi_annuncio, extender, x_tg_init_data="",
               barattolo_sessione="")
    prova("la rotta risponde ok", {"ok": True}, r)
    prova("la riga resta, ed e' 'rimosso'", "rimosso", stato(extender))
    prova("l'ordine concluso resta 'released'", "released",
          conta("SELECT stato FROM ordini WHERE id=?", oid))
    prova("...e la sua recensione resta", 1,
          conta("SELECT COUNT(*) FROM feedback WHERE ordine_id=?", oid))
    prova("partono il ritiro da Nostr e dal canale", ([extender], [extender]),
          (RITIRI_NOSTR, RITIRI_CANALE))
    prova("esce dallo scaffale «Esauriti di recente»", False,
          extender in esauriti_del_negozio())
    prova("...e il link condiviso non lo serve piu' (404)", 404,
          codice_di(SRV.un_annuncio, extender, x_tg_init_data="",
                    barattolo_sessione=""))

    print("\n── UN RESO IN CORSO FERMA IL GESTO ──")
    del RITIRI_NOSTR[:], RITIRI_CANALE[:]
    prova("400 sull'esaurito col reso aperto", 400,
          codice_di(SRV.rimuovi_annuncio, shoyu, x_tg_init_data="",
                    barattolo_sessione=""))
    prova("...l'annuncio resta esaurito, nello scaffale", ["venduto", True],
          [stato(shoyu), shoyu in esauriti_del_negozio()])
    prova("...e nessun gancio parte", ([], []), (RITIRI_NOSTR, RITIRI_CANALE))


def prove_zona():
    print("\n── LA ZONA DELL'ULTIMO ANNUNCIO IN /api/me ──")
    me = chiama(SRV.mio_profilo, x_tg_init_data="", barattolo_sessione="")
    prova("e' quella del suo ultimo annuncio nato qui, anche archiviato, "
          "e non quella dell'importato piu' recente", "Dro (TN)",
          me.get("zona_ultima_vendi"))


def main():
    avvio()
    prove_elimina()
    prove_zona()
    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
