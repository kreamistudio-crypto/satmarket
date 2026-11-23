# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ANNUNCIO NASCOSTO (23 nov 2026, cantiere
nascondi-annuncio, richiesta di un venditore).

Gira il SERVER VERO su un database usa-e-getta, con lo schema vero, e
risponde alle domande su cui il cantiere si regge:

  · nascosto, l'annuncio esce davvero da dove si vedeva: la vetrina, il
    negozio, il link condiviso — e resta in «I tuoi annunci»;
  · le due piazze fanno il gesto dell'esaurito (Nostr «sold», canale ✅)
    e al ritorno quello inverso; nascondere due volte non rifa' niente;
  · le offerte vive decadono al giro di `scadenze_offerte`;
  · un ordine in corso, un pezzo in pagamento, un'asta, un importato
    fermano il gesto, e l'annuncio resta com'era;
  · a leva spenta non si nasconde, ma si RIMETTE in vetrina;
  · il nascosto si puo' eliminare.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Le due piazze sono registri: si misura se il
gancio PARTE e con quale parola, non cosa arriva ai relay.

USO:  python collaudo_nascondi_annuncio.py
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
NOSTR, CANALE, RITIRI, AVVISI = [], [], [], []

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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-nascondi-"),
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

    async def nostr_finto(aid, status, **k):
        NOSTR.append((aid, status))
        return False

    async def canale_finto(aid, venduto=True):
        CANALE.append((aid, venduto))

    async def ritiro_finto(aid, *a, **k):
        RITIRI.append(aid)
        return 0

    async def notifica_finta(tg_id, testo, *a, **k):
        AVVISI.append((tg_id, testo))

    async def profilo_finto(*a, **k):
        return None

    server.annuncio_su_nostr = nostr_finto
    server.promo_venduto = canale_finto
    server.ritira_da_nostr = ritiro_finto
    server.promo_rimuovi = ritiro_finto
    server.notifica = notifica_finta
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


def nascondi(aid, valore=1):
    """La rotta vera, col corpo JSON che manda la Mini App."""
    async def leggi(_req):
        return {"nascosto": valore}
    SRV.leggi_json = leggi
    return chiama(SRV.nascondi_annuncio, aid, None, x_tg_init_data="",
                  barattolo_sessione="")


def codice(fn, *args, **kw):
    try:
        fn(*args, **kw)
        return 200
    except Exception as e:
        return getattr(e, "status_code", repr(e))


def semina():
    """Un venditore con sei annunci attivi: uno libero, uno con un ordine
    spedito, uno con un pezzo in pagamento adesso, un'asta, un importato
    da Nostr, e uno di riserva per la leva spenta. Un'offerta viva sul
    primo."""
    con = SRV.db()
    for t in ("offerte", "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "avatar_aggiornato) VALUES(222,'Vende','neg22222',1,?)",
                (int(time.time()),))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    adesso = int(time.time())
    ids = []
    for titolo, asta, nostr in (
            ("Miele di castagno", 0, ""),
            ("Lampada spedita", 0, ""),
            ("Libro in pagamento", 0, ""),
            ("Orologio all'asta", 5000, ""),
            ("Importato dai relay", 0, "npub1qualcuno"),
            ("Tazza di riserva", 0, "")):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
            "valuta,condizione,contatto_nostr,asta_base_sats,asta_scadenza) "
            "VALUES(222,?,'desc',44000,'Altro','Dro (TN)','attivo',?,"
            "'spedizione',3,3,'sats','usato',?,?,?)",
            (titolo, adesso - 100 + len(ids), nostr, asta,
             adesso + 86400 if asta else 0))
        ids.append(cur.lastrowid)
    for aid, stato in ((ids[1], "shipped"), (ids[2], "creato")):
        con.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,stato,creato,aggiornato,quantita) "
            "VALUES(?,111,222,44000,?,?,?,1)", (aid, stato, adesso, adesso))
    con.execute("INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
                "importo_sats,quantita,stato,creato,aggiornato,scadenza) "
                "VALUES(?,111,222,40000,1,'proposta',?,?,?)",
                (ids[0], adesso, adesso, adesso + 86400))
    con.commit()
    con.close()
    return ids


def conta(sql, *par):
    con = SRV.db()
    r = con.execute(sql, par).fetchone()[0]
    con.close()
    return r


def stato(aid):
    return conta("SELECT stato FROM annunci WHERE id=?", aid)


def in_vetrina(aid):
    d = chiama(SRV.lista_annunci, limit=100, x_tg_init_data="",
               barattolo_sessione="")
    righe = d.get("annunci", d) if isinstance(d, dict) else d
    return aid in [a["id"] for a in righe]


def nel_negozio(aid):
    d = chiama(SRV.negozio, "neg22222", x_tg_init_data="",
               barattolo_sessione="")
    tutti = list(d.get("annunci") or []) + list(d.get("esauriti") or [])
    return aid in [a["id"] for a in tutti]


def nei_miei(aid):
    righe = SRV.miei_annunci(x_tg_init_data="", barattolo_sessione="")
    return {a["id"]: a.get("stato") for a in righe}.get(aid)


def link_vivo(aid):
    return codice(SRV.un_annuncio, aid, x_tg_init_data="",
                  barattolo_sessione="")


def svuota():
    del NOSTR[:], CANALE[:], RITIRI[:], AVVISI[:]


# ---------------------------------------------------------------
def prove_nascondi():
    miele, lampada, libro, asta, importato, tazza = semina()
    print("\n── PRIMA: il miele si vede dappertutto ──")
    prova("in vetrina, nel negozio, col link vivo",
          [True, True, 200],
          [in_vetrina(miele), nel_negozio(miele), link_vivo(miele)])

    print("\n── 🙈 NASCONDI ──")
    svuota()
    r = nascondi(miele)
    prova("la rotta risponde ok, con un passaggio",
          {"ok": True, "nascosto": True, "cambiato": True}, r)
    prova("lo stato e' 'nascosto'", "nascosto", stato(miele))
    prova("i pezzi non si toccano", 3,
          conta("SELECT quantita FROM annunci WHERE id=?", miele))
    prova("Nostr dice «sold», il canale mette la spunta",
          ([(miele, "sold")], [(miele, True)]), (NOSTR, CANALE))
    prova("esce dalla vetrina", False, in_vetrina(miele))
    prova("esce dal negozio (anche dagli esauriti)", False,
          nel_negozio(miele))
    prova("il link condiviso risponde 404", 404, link_vivo(miele))
    prova("resta in «I tuoi annunci», come nascosto", "nascosto",
          nei_miei(miele))

    print("\n── DUE VOLTE E' UNA ──")
    svuota()
    prova("nascondere un nascosto non cambia niente",
          {"ok": True, "nascosto": True, "cambiato": False}, nascondi(miele))
    prova("...e nessun gancio riparte", ([], []), (NOSTR, CANALE))

    print("\n── LE OFFERTE VIVE DECADONO ──")
    chiama(SRV.scadenze_offerte)
    prova("l'offerta sul nascosto e' 'decaduta'", "decaduta",
          conta("SELECT stato FROM offerte WHERE annuncio_id=?", miele))
    prova("...e chi aveva offerto lo sa", True,
          any(t == 111 and "non è più disponibile" in s for t, s in AVVISI))

    print("\n── COSA FERMA IL GESTO ──")
    svuota()
    for nome, aid in (("un ordine spedito", lampada),
                      ("un pezzo in pagamento adesso", libro),
                      ("un'asta", asta),
                      ("un importato da Nostr", importato)):
        prova(f"{nome}: 400, e resta attivo", [400, "attivo"],
              [codice(nascondi, aid), stato(aid)])
    prova("...e nessun gancio parte", ([], []), (NOSTR, CANALE))
    prova("il pezzo in pagamento resta pagabile (l'ordine non si annulla)",
          "creato", conta("SELECT stato FROM ordini WHERE annuncio_id=?",
                          libro))
    prova("un annuncio d'altri non si nasconde (400)", 400,
          codice(nascondi, conta("SELECT MAX(id) FROM annunci") + 1))

    print("\n── LA LEVA SPENTA ──")
    SRV.NASCONDI_ANNUNCIO = False
    prova("/api/me lo dice", False,
          chiama(SRV.mio_profilo, x_tg_init_data="",
                 barattolo_sessione="").get("nascondi_annuncio"))
    prova("non si nasconde (404), e la tazza resta attiva",
          [404, "attivo"], [codice(nascondi, tazza), stato(tazza)])

    print("\n── 👁 RIMETTI IN VETRINA (anche a leva spenta) ──")
    svuota()
    r = nascondi(miele, 0)
    prova("la rotta risponde ok, con un passaggio",
          {"ok": True, "nascosto": False, "cambiato": True}, r)
    prova("torna 'attivo', coi suoi pezzi", ["attivo", 3],
          [stato(miele),
           conta("SELECT quantita FROM annunci WHERE id=?", miele)])
    prova("Nostr dice «active», il canale toglie la spunta",
          ([(miele, "active")], [(miele, False)]), (NOSTR, CANALE))
    prova("di nuovo in vetrina, nel negozio, col link vivo",
          [True, True, 200],
          [in_vetrina(miele), nel_negozio(miele), link_vivo(miele)])
    svuota()
    prova("rimettere un attivo non cambia niente, e niente riparte",
          [False, [], []],
          [nascondi(miele, 0)["cambiato"], NOSTR, CANALE])
    SRV.NASCONDI_ANNUNCIO = True
    prova("/api/me a leva accesa", True,
          chiama(SRV.mio_profilo, x_tg_init_data="",
                 barattolo_sessione="").get("nascondi_annuncio"))

    print("\n── IL NASCOSTO SI PUO' ELIMINARE ──")
    nascondi(tazza)
    svuota()
    r = chiama(SRV.rimuovi_annuncio, tazza, x_tg_init_data="",
               barattolo_sessione="")
    prova("ok, e diventa 'rimosso'", [{"ok": True}, "rimosso"],
          [r, stato(tazza)])
    prova("...coi ritiri da Nostr e dal canale", [tazza, tazza], RITIRI)


def main():
    avvio()
    prove_nascondi()
    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
