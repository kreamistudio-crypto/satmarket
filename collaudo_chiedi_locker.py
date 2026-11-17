# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «CHIEDI AL VENDITORE SE SPEDISCE CON INPOST O POSTE»
(17 nov 2026, cantiere chiedi-locker, voce #359 del Todo).

DA DOVE NASCE. Dal 12 ott 2026 (il 213) la via punto si offre solo dove
il venditore ha dichiarato un corriere che ai punti consegna. Chi
compra da un venditore senza corrieri trovava la riga del locker
sparita e basta: una porta chiusa senza campanello. Il campanello e'
questo — la riga resta in vista, spenta, con un tasto che bussa al
venditore; il bot gli dice che QUALCUNO vorrebbe un locker, lo porta
a «📦 Come spedisci», e quando spunta una rete chi aveva chiesto lo sa.

`prove.py` difende la FORMA e fa girare i giudici puri. Questo script
fa girare la cosa VERA — database, rotte, avvisi contati — e risponde
alle domande su cui il cantiere si regge:

  · il preventivo di un venditore senza corrieri dice «si puo'
    chiedere», quello di un venditore con InPost no, e la via punto
    resta com'era nei due casi (nessuna vendita cambia);
  · la richiesta scrive la riga e avvisa il venditore UNA volta, senza
    dire chi ha chiesto e col bottone che apre «Come spedisci»;
  · la stessa coppia entro sette giorni non rifa' partire niente, e
    dopo sette giorni si';
  · al venditore arrivano al piu' tre avvisi al giorno: la quarta
    persona resta scritta ma il bot tace;
  · quando il venditore spunta InPost dal Salva VERO del Profilo, tutti
    quelli che avevano chiesto ricevono l'avviso, una volta sola, col
    bottone sull'annuncio se e' ancora in vetrina; togliere i corrieri
    non fa partire niente;
  · i rifiuti dicono il motivo: venditore che ai punti ci arriva gia',
    annuncio che non si spedisce, annuncio mio, annuncio sparito;
  · a leva spenta la rotta non esiste e il preventivo non propone il
    tasto, e il Salva del Profilo non avvisa nessuno.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Le
notifiche si registrano invece di partire, LNbits non si chiama mai:
gira senza rete e senza chiavi, ed e' cosi' che gira nella gabbia
della CI.

USO:  python collaudo_chiedi_locker.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
DETTI = []      # (a chi, testo, bottone): le notifiche alle persone
BOT = "https://t.me/ilbarattolobot"


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alza(nome, fn, codice=400, dentro=""):
    """Come `prova`, ma per i rifiuti: il codice e un pezzo del
    messaggio — qui il messaggio E' il prodotto."""
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        c = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if c == codice and (not dentro or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso {codice} con {dentro!r}"
              f"\n      avuto:  {c} {testo!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-chiedi-locker-"),
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
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    cfg.PROTEZIONE_PERCENTO = 0
    # la Mini App c'e': il bottone dell'avviso deve diventare un
    # `?startapp=corrieri`, non restare un indirizzo del sito
    cfg.TELEGRAM_MINIAPP_LINK = BOT
    # la leva NON si scrive qui apposta: deve nascere ACCESA dal
    # default del codice, ed e' una delle cose da provare
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def cambio_finto():
        return 100_000.0

    async def zitta(*a, **k):
        return None

    async def detta(chi, testo, bottone=None):
        DETTI.append((chi, testo, bottone))

    server.cambio_btc_eur = cambio_finto
    server.notifica = detta
    server.notifica_admin = zitta
    server.premia_distintivi = zitta
    server.premia_xp = zitta
    server.verifica_utente = lambda *a, **k: {
        "id": 111, "nome": "Compra", "username": "compra", "admin": False}
    return db


def come(tg_id):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": False}


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def chiedi(aid, chi=111):
    come(chi)
    return asyncio.run(SRV.chiedi_punti(aid, "", ""))


def salva_corrieri(corrieri, chi=222):
    come(chi)
    return chiama(SRV.scegli_spedizioniere, {"spedizionieri": list(corrieri)})


def semina(corrieri, venditore=222):
    """Un venditore coi corrieri che ha dichiarato (dalla ROTTA VERA) e
    tre annunci: due che si spediscono, uno solo a mano."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci", "richieste_punti"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(?,?,?,1)",
                (venditore, f"Vende{venditore}", f"neg{venditore}"))
    for chi in (111, 333, 444, 555, 666):
        con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio,"
                    "registrato) VALUES(?,?,?,1)",
                    (chi, f"Compra{chi}", f"neg{chi}"))
    ids = []
    for titolo, consegna in (("Lampada <b>&</b> co", "spedizione"),
                             ("Altra", "spedizione"),
                             ("Solo a mano", "ritiro")):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(?,?,'desc',30000,'Altro',"
            "'Torino (TO)','attivo',1,?,5,'sats','buono',1000)",
            (venditore, titolo, consegna))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    salva_corrieri(corrieri, venditore)
    DETTI.clear()
    come(111)
    return ids


def preventivo(aid):
    come(111)
    return chiama(SRV.preventivo_ordine,
                  {"annuncio_id": aid, "quantita": 1, "offerta_id": 0})


def preventivo_set(ids):
    come(111)
    return chiama(SRV.preventivo_ordine,
                  {"righe": [{"annuncio_id": a, "quantita": 1} for a in ids]})


def vie(p):
    return [s["via"] for s in p["strade"]]


def righe_richieste():
    con = SRV.db()
    r = con.execute("SELECT compratore, venditore, annuncio_id, chiesto, "
                    "avvisato FROM richieste_punti ORDER BY compratore"
                    ).fetchall()
    con.close()
    return [dict(x) for x in r]


def sposta_indietro(compratore, venditore, secondi):
    con = SRV.db()
    con.execute("UPDATE richieste_punti SET chiesto=chiesto-? "
                "WHERE compratore=? AND venditore=?",
                (secondi, compratore, venditore))
    con.commit()
    con.close()


# ---------------------------------------------------------------
def prove_preventivo():
    print("\n── IL PREVENTIVO: quando il tasto si propone ──")
    aid, bid, rid = semina([])
    p = preventivo(aid)
    prova("senza corrieri la via punto NON c'e', come dal 12 ott",
          ["casa"], vie(p))
    prova("...ma il preventivo dice «si puo' chiedere», e non ancora chiesto",
          (True, False), (p["punto_chiedibile"], p["punto_chiesto"]))
    ps = preventivo_set([aid, bid])
    prova("...anche nel carrello", (["casa"], True, False),
          (vie(ps), ps["punto_chiedibile"], ps["punto_chiesto"]))
    aid2, _, _ = semina(["InPost"])
    p = preventivo(aid2)
    prova("con InPost la via punto c'e' e il tasto no",
          (["casa", "punto"], False, False),
          (vie(p), p["punto_chiedibile"], p["punto_chiesto"]))
    aid3, _, _ = semina(["DHL"])
    p = preventivo(aid3)
    prova("con un corriere senza mappa: niente via punto, e si puo' chiedere",
          (["casa"], True), (vie(p), p["punto_chiedibile"]))


def prove_richiesta():
    print("\n── LA RICHIESTA: la riga, l'avviso, il bottone ──")
    aid, bid, rid = semina([])
    r = chiedi(aid)
    prova("la richiesta passa e il venditore e' avvisato",
          {"ok": True, "avvisato": True}, r)
    prova("UNA riga per la coppia, con l'annuncio e senza timbro di ritorno",
          [(111, 222, aid, 0)],
          [(x["compratore"], x["venditore"], x["annuncio_id"], x["avvisato"])
           for x in righe_richieste()])
    prova("un avviso solo, al venditore", [222], [chi for chi, _, _ in DETTI])
    chi, testo, bottone = DETTI[0]
    prova("...che dice l'annuncio, scappato per Telegram, e cosa fare", True,
          "Lampada &lt;b&gt;&amp;&lt;/b&gt; co" in testo
          and "Come spedisci" in testo and "InPost" in testo
          and "Poste Italiane" in testo and "SDA" in testo)
    prova("...SENZA dire chi ha chiesto", False,
          "Compra111" in testo or "111" in testo or "u111" in testo)
    prova("...col bottone che apre la Mini App su «Come spedisci»",
          ("📦 Come spedisci", BOT + "?startapp=corrieri"), bottone)
    p = preventivo(aid)
    prova("il preventivo adesso dice «gia' chiesto» (anche sull'altro "
          "annuncio dello stesso venditore)", (True, True, True),
          (p["punto_chiedibile"], p["punto_chiesto"],
           preventivo(bid)["punto_chiesto"]))
    DETTI.clear()
    alza("la stessa coppia entro sette giorni: «gliel'hai gia' chiesto»",
         lambda: chiedi(aid), 400, "già chiesto")
    prova("...e il venditore non riceve un secondo avviso", [], DETTI)
    sposta_indietro(111, 222, SRV.RICHIESTA_PUNTI_OGNI_GIORNI * 86400 + 60)
    prova("passati i sette giorni il preventivo torna a proporre il tasto",
          False, preventivo(aid)["punto_chiesto"])
    r = chiedi(bid)
    prova("...e la richiesta riparte, sull'altro annuncio",
          ({"ok": True, "avvisato": True}, [222], bid),
          (r, [chi for chi, _, _ in DETTI], righe_richieste()[0]["annuncio_id"]))
    prova("...sempre UNA riga per la coppia", 1, len(righe_richieste()))


def prove_tetto_venditore():
    print("\n── IL TETTO DEL VENDITORE: tre avvisi al giorno ──")
    aid, _, _ = semina([])
    esiti = [chiedi(aid, chi)["avvisato"] for chi in (111, 333, 444, 555)]
    prova("tre persone avvisano, la quarta resta scritta ma il bot tace",
          [True, True, True, False], esiti)
    prova("...gli avvisi al venditore sono tre", [222, 222, 222],
          [chi for chi, _, _ in DETTI])
    prova("...le righe quattro", [111, 333, 444, 555],
          [x["compratore"] for x in righe_richieste()])
    prova("il tetto e' quello scritto accanto al giudice", 3,
          SRV.RICHIESTA_PUNTI_AL_GIORNO)


def prove_ritorno():
    print("\n── IL RITORNO: il venditore spunta InPost ──")
    aid, bid, _ = semina([])
    for chi in (111, 333, 444, 555):
        chiedi(aid, chi)
    # il 555 aveva chiesto su un annuncio che poi sparisce
    con = SRV.db()
    con.execute("UPDATE richieste_punti SET annuncio_id=? WHERE compratore=555",
                (bid,))
    con.execute("UPDATE annunci SET stato='venduto' WHERE id=?", (bid,))
    con.commit()
    con.close()
    DETTI.clear()
    r = salva_corrieri(["InPost"])
    prova("il Salva del Profilo risponde come sempre", ["InPost"],
          r["spedizionieri"])
    prova("...e avvisa i quattro che avevano chiesto", [111, 333, 444, 555],
          sorted(chi for chi, _, _ in DETTI))
    chi, testo, bottone = next(x for x in DETTI if x[0] == 111)
    prova("...dicendo il NOME del venditore (non il codice negozio) e la "
          "rete dei punti, non il corriere",
          True, "Vende222" in testo and "neg222" not in testo and "InPost" in testo
          and "Glielo avevi chiesto" in testo)
    prova("...col bottone sull'annuncio ancora in vetrina",
          ("🔎 Apri l'annuncio", BOT + f"?startapp=annuncio_{aid}"), bottone)
    prova("...e SENZA bottone a chi aveva chiesto su un annuncio sparito",
          None, next(x for x in DETTI if x[0] == 555)[2])
    prova("il timbro di ritorno e' scritto su tutte", 4,
          sum(1 for x in righe_richieste() if x["avvisato"] > 0))
    DETTI.clear()
    salva_corrieri(["InPost", "SDA"])
    prova("un secondo Salva non riavvisa nessuno", [], DETTI)
    prova("adesso la via punto c'e' e il tasto no",
          (["casa", "punto"], False), (lambda p: (vie(p), p["punto_chiedibile"]))(preventivo(aid)))
    alza("...e chi ha la pagina vecchia e chiede lo stesso: «ricarica»",
         lambda: chiedi(aid, 666), 400, "spedisce già ai punti")
    salva_corrieri([])
    prova("togliere i corrieri non fa partire niente", [], DETTI)
    r = chiedi(aid, 666)
    prova("il 666 adesso puo' chiedere: il venditore e' tornato senza reti",
          True, r["ok"])
    DETTI.clear()
    salva_corrieri(["Poste Italiane"])
    prova("...e al prossimo Salva e' avvisato SOLO lui (gli altri lo sanno gia')",
          [666], [chi for chi, _, _ in DETTI])
    prova("...con la rete dei punti di Poste", True,
          "Poste Italiane" in DETTI[0][1])


def prove_rifiuti():
    print("\n── I RIFIUTI, col motivo ──")
    aid, _, rid = semina([])
    alza("un annuncio che non si spedisce: niente locker da chiedere",
         lambda: chiedi(rid), 400, "non si spedisce")
    alza("il mio annuncio", lambda: chiedi(aid, 222), 400, "tuo annuncio")
    alza("un annuncio che non c'e'", lambda: chiedi(999999), 404)
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='venduto' WHERE id=?", (aid,))
    con.commit()
    con.close()
    alza("un annuncio non piu' in vetrina", lambda: chiedi(aid), 404)
    prova("nessun rifiuto ha scritto una riga", [], righe_richieste())
    prova("...ne' avvisato nessuno", [], DETTI)


def prove_leva():
    print("\n── LA LEVA: accesa di serie, spenta non esiste niente ──")
    prova("nel codice nasce ACCESA (senza la riga nel config)", True,
          SRV.RICHIESTA_PUNTI is True)
    aid, _, _ = semina([])
    SRV.RICHIESTA_PUNTI = False
    try:
        p = preventivo(aid)
        prova("a leva spenta il preventivo non propone il tasto",
              (False, False), (p["punto_chiedibile"], p["punto_chiesto"]))
        alza("...e la rotta non esiste", lambda: chiedi(aid), 404)
        con = SRV.db()
        con.execute("INSERT INTO richieste_punti(compratore,venditore,"
                    "annuncio_id,chiesto,avvisato) VALUES(111,222,?,1,0)",
                    (aid,))
        con.commit()
        con.close()
        DETTI.clear()
        salva_corrieri(["InPost"])
        prova("...e il Salva del Profilo non avvisa nessuno, nemmeno con "
              "una richiesta vecchia in tabella", [], DETTI)
    finally:
        SRV.RICHIESTA_PUNTI = True
    DETTI.clear()
    salva_corrieri(["SDA"])
    prova("riaccesa, la richiesta rimasta in tabella si onora", [111],
          [chi for chi, _, _ in DETTI])


def main():
    db = avvio()
    print("=" * 66)
    print("COLLAUDO «CHIEDI AL VENDITORE» — db usa-e-getta, bot finto")
    print("=" * 66)
    prove_preventivo()
    prove_richiesta()
    prove_tetto_venditore()
    prove_ritorno()
    prove_rifiuti()
    prove_leva()
    print("\n" + "=" * 66)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 66)
    try:
        os.remove(db)
    except OSError:
        pass
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
