# -*- coding: utf-8 -*-
"""
GLI AVVISI DEL MERCATINO, SUL SERVER VERO (9 ott 2026, richiesta di Andrea).

Due identita': Compra (222) SEGUE Vende (333) e accende «🆕 Avvisami dei
nuovi annunci» con un filtro di categoria («Alimenti e bevande»); Vende
pubblica TRE annunci dalla rotta vera — due nella categoria, uno no — e
si guarda cosa parte davvero:
  1. il bottone: /api/negozio dice `seguito` a chi guarda (falso prima,
     vero dopo, mai sulla propria pagina), seguirsi da soli e' un 400,
     la lista del cassetto arriva con la risposta;
  2. L'AVVISO DI CHI SEGUE, raggruppato: i tre annunci escono in UN
     messaggio a Compra (chi segue riceve TUTTO quel che pubblica il
     venditore, filtro o no), subito, col nome del venditore e i titoli;
     Terzo (444), che non segue ma ha «tutti» con lo stesso filtro,
     riceve i DUE della categoria e non il terzo;
  3. MAI DUE VOLTE: un quarto annuncio ripassato nel drenatore (la
     modifica approvata) non riaccoda niente; e dentro la finestra il
     quarto aspetta — esce al giro dell'orologio, da solo;
  4. MAI PER I PROPRI: Vende, con «tutti» acceso, non riceve i suoi;
  5. IN MODERAZIONE non avvisa: un annuncio nato in 'revisione' non
     passa dal drenatore finche' un moderatore non lo approva, e un
     annuncio tolto prima del suo minuto si consuma senza messaggio;
  6. IL CANALE: Compra entra da Telegram e riceve sul bot; Nativa (-5)
     entra con Nostr, segue Vende, e riceve il DM cifrato — e' la
     `notifica()` VERA a decidere, coi due trasporti di cartone;
  7. SMETTI e SPEGNI: la coda arretrata si consuma senza messaggio;
  8. la leva globale spenta chiude le rotte (409).

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, niente rete, niente
Telegram (i trasporti finiscono in una lista), niente relay.

USO:  python collaudo_avvisi_mercatino.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
VIA = []          # (canale, destinatario, testo)

COMPRA, VENDE, TERZO, NATIVA = 222, 333, 444, -5
NOMI = {COMPRA: "Compra", VENDE: "Vende", TERZO: "Terzo", NATIVA: "Nativa"}
CAT = "Alimenti e bevande"


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
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-avvisi-mercatino-")
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
    cfg.DB = os.path.join(tmp, "usa-e-getta.db")
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def zitto(*a, **k):
        return None

    async def cambio_finto():
        return 100_000.0

    async def telegram_finto(tg_id, testo):
        VIA.append(("telegram", tg_id, testo))
        return "ok"

    async def dm_finto(npub, testo, ripiego):
        VIA.append(("nostr", npub, testo))

    server.cambio_btc_eur = cambio_finto
    server._manda_telegram = telegram_finto
    server._dm_nostr_con_ripiego = dm_finto
    for nome in ("notifica_admin", "annuncio_su_nostr", "premia_distintivi",
                 "avvisa_contatto_mancante", "premia_xp"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    server.accoda_promo = lambda *a, **k: None
    server.ATTESA_RAGGRUPPO = 1        # il drenatore dorme un secondo, non novanta
    server.FRENI["annunci"] = (1000, 3600)   # tre annunci di fila, senza freno
    return tmp


def testata(tg_id):
    return f"collaudo:{tg_id}:{NOMI.get(tg_id, 'Utente')}"


async def _rotta(rotta, corpo, tg_id, args):
    """Una rotta POST del server vero, col suo giro di ganci: il corpo
    arriva da `leggi_json`, l'identita' dall'header di collaudo."""
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    try:
        return await rotta(*args, None, x_tg_init_data=testata(tg_id))
    except SRV.HTTPException as e:
        return {"errore": e.status_code, "detail": e.detail}


def chiama(rotta, corpo, tg_id, *args):
    """Una chiamata sola; dopo si lascia un attimo al drenatore (che
    dorme un secondo) e ai create_task — nello STESSO loop, o il
    drenatore morirebbe col loop prima di svegliarsi."""
    async def giro():
        r = await _rotta(rotta, corpo, tg_id, args)
        await asyncio.sleep(1.5)
        return r
    return asyncio.run(giro())


def corpo_annuncio(titolo, categoria, sats):
    return {"titolo": titolo, "prezzo_sats": sats, "categoria": categoria,
            "zona": "Torino (TO)", "descrizione": "Una cosa", "consegna": "ritiro",
            "quantita": 1, "condizione": "nuovo", "foto": []}


def pubblica(tg_id, titolo, categoria=CAT, sats=30000):
    return chiama(SRV.pubblica, corpo_annuncio(titolo, categoria, sats), tg_id).get("id")


def pubblica_insieme(tg_id, annunci):
    """Piu' annunci nella STESSA finestra del drenatore: e' il caso del
    venditore che ne pubblica tre di fila, e il raggruppamento si prova
    solo cosi'."""
    async def giro():
        ids = []
        for titolo, categoria in annunci:
            r = await _rotta(SRV.pubblica, corpo_annuncio(titolo, categoria, 30000), tg_id, ())
            ids.append(r.get("id"))
        await asyncio.sleep(1.5)
        return ids
    return asyncio.run(giro())


def giro_orologio(adesso=None):
    """Un battito dell'orologio degli avvisi, con un'ora a scelta: la
    finestra si prova spostando l'orologio, non aspettando un'ora."""
    if adesso is not None:
        vero = SRV.time.time
        SRV.time.time = lambda: adesso
    try:
        asyncio.run(SRV._giro_avvisi_mercatino())
    finally:
        if adesso is not None:
            SRV.time.time = vero


def coda(tg_id):
    con = SRV.db()
    r = [tuple(x) for x in con.execute(
        "SELECT annuncio_id, motivo, mandato FROM mercatino_avvisi_coda "
        "WHERE tg_id=? ORDER BY annuncio_id", (tg_id,))]
    con.close()
    return r


def semina():
    con = SRV.db()
    for tg_id, nome in NOMI.items():
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg_id, nome, f"neg{abs(tg_id)}"))
    # Nativa entra con Nostr: tg_id negativo e la chiave d'accesso
    con.execute("UPDATE utenti SET npub_accesso='npub1nativa' WHERE tg_id=?",
                (NATIVA,))
    con.commit()
    con.close()


def main():
    print("=" * 58)
    print("  GLI AVVISI DEL MERCATINO — il giro vero")
    print("=" * 58)
    tmp = avvio()
    semina()
    T0 = int(SRV.time.time())

    print("\n[1) il bottone «🔔 Segui» e il cassetto]")
    v = SRV.negozio("neg333", x_tg_init_data=testata(COMPRA))["venditore"]
    prova("prima: /api/negozio dice seguito=false a chi guarda, e il tg_id non esce",
          (False, False), (v.get("seguito"), "tg_id" in v))
    r = chiama(SRV.segui_venditore, {"segui": True}, COMPRA, "neg333")
    prova("Compra segue Vende: seguito=true e l'elenco del cassetto con lui",
          (True, ["Vende"]), (r.get("seguito"), [s["nome"] for s in r.get("seguiti", [])]))
    prova("...e l'elenco non porta il tg_id del venditore", False,
          any("tg_id" in s for s in r.get("seguiti", [])))
    v = SRV.negozio("neg333", x_tg_init_data=testata(COMPRA))["venditore"]
    prova("dopo: /api/negozio dice seguito=true", True, v.get("seguito"))
    mio = SRV.negozio("neg333", x_tg_init_data=testata(VENDE))["venditore"]
    prova("sulla PROPRIA pagina vale falso", False, mio.get("seguito"))
    r = chiama(SRV.segui_venditore, {"segui": True}, VENDE, "neg333")
    prova("seguirsi da soli e' un 400", 400, r.get("errore"))
    r = chiama(SRV.segui_venditore, {"segui": True}, COMPRA, "nessuno-cosi")
    prova("un negozio che non c'e' e' un 404", 404, r.get("errore"))
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(COMPRA)))
    prova("/api/me porta i seguiti, le preferenze SPENTE di serie e le leve",
          (["Vende"], False, True, 60, 15),
          ([s["nome"] for s in me["seguiti"]], me["avvisi_mercatino"]["attivo"],
           me["avvisi_mercatino_leve"]["attivi"], me["avvisi_mercatino_leve"]["minuti"],
           me["avvisi_mercatino_leve"]["seguiMinuti"]))
    # Compra e Terzo accendono «tutti» con la categoria; Vende lo accende
    # senza filtri (riceverebbe tutto — tranne i suoi); Nativa segue Vende
    r = chiama(SRV.scegli_avvisi_mercatino,
               {"attivo": True, "categorie": [CAT, "Non esiste"], "prezzo_max": "0", "valuta": "sats"},
               COMPRA)
    prova("«tutti i nuovi annunci» acceso con la categoria: la risposta e' il giudice",
          {"attivo": True, "categorie": [CAT], "prezzo_max": 0, "valuta": "sats"},
          r.get("avvisi_mercatino"))
    chiama(SRV.scegli_avvisi_mercatino,
           {"attivo": True, "categorie": [CAT], "prezzo_max": 0, "valuta": "sats"}, TERZO)
    chiama(SRV.scegli_avvisi_mercatino,
           {"attivo": True, "categorie": [], "prezzo_max": 0, "valuta": "sats"}, VENDE)
    chiama(SRV.segui_venditore, {"segui": True}, NATIVA, "neg333")
    r = chiama(SRV.scegli_avvisi_mercatino,
               {"attivo": True, "categorie": [], "prezzo_max": "-3", "valuta": "eur"}, COMPRA)
    prova("un prezzo massimo negativo e' un 400", 400, r.get("errore"))

    print("\n[2) Vende pubblica tre annunci: due nella categoria, uno no]")
    VIA.clear()
    a1, a2, a3 = pubblica_insieme(VENDE, (("Miele di acacia", CAT), ("Noci sgusciate", CAT),
                                          ("Lampada da tavolo", "Casa e giardino")))
    prova("i tre annunci sono nati attivi", True, all((a1, a2, a3)))
    per = {}
    for canale, chi, testo in VIA:
        per.setdefault((canale, chi), []).append(testo)
    prova("Compra (segue): UN messaggio sul bot Telegram coi TRE annunci — nome del venditore e titoli",
          (1, True, True, True, True),
          (len(per.get(("telegram", COMPRA), [])),
           "🔔 <b>Vende</b> ha pubblicato 3 nuovi annunci" in per.get(("telegram", COMPRA), [""])[0],
           "• Miele di acacia" in per.get(("telegram", COMPRA), [""])[0],
           "• Lampada da tavolo" in per.get(("telegram", COMPRA), [""])[0],
           "/negozio/neg333\">🫙 Apri il suo negozio" in per.get(("telegram", COMPRA), [""])[0]))
    prova("Terzo («tutti» con la categoria): UN messaggio coi DUE della categoria, e il tocco apre il reparto",
          (1, True, True, False, True, True),
          (len(per.get(("telegram", TERZO), [])),
           "🆕 <b>2 nuovi annunci nel mercatino</b>" in per.get(("telegram", TERZO), [""])[0],
           "• Noci sgusciate" in per.get(("telegram", TERZO), [""])[0],
           "Lampada" in per.get(("telegram", TERZO), [""])[0],
           f"Il tuo filtro: {CAT}" in per.get(("telegram", TERZO), [""])[0],
           "/categoria/alimenti-e-bevande\">🫙 Apri Esplora" in per.get(("telegram", TERZO), [""])[0]))
    prova("Nativa (entra con Nostr, segue): il DM cifrato alla sua npub, e niente Telegram",
          (1, 0), (len(per.get(("nostr", "npub1nativa"), [])),
                   len([1 for c, chi, _ in VIA if c == "telegram" and chi == NATIVA])))
    prova("MAI PER I PROPRI: Vende, con «tutti» acceso, non riceve niente", 0,
          len([1 for _, chi, _ in VIA if chi == VENDE]))
    prova("le righe della coda sono timbrate con l'ora del messaggio (mai 0)", True,
          all(m > 1 for _, _, m in coda(COMPRA) + coda(TERZO)))

    print("\n[3) mai due volte, e la finestra]")
    VIA.clear()
    # la modifica approvata ripassa dal drenatore: stesso annuncio, niente
    asyncio.run(_ripassa(a1))
    prova("un annuncio ripassato nel drenatore non riaccoda e non rimanda", (0, 3),
          (len(VIA), len(coda(COMPRA))))
    a4 = pubblica(VENDE, "Confettura di fichi")
    prova("il quarto, dentro la finestra, ASPETTA: in coda a Compra e Terzo, nessun messaggio",
          (0, (a4, "segui", 0), (a4, "tutti", 0)),
          (len(VIA), coda(COMPRA)[-1], coda(TERZO)[-1]))
    giro_orologio(T0 + 14 * 60)
    prova("a quattordici minuti ancora niente (la finestra di chi segue e' di quindici)", 0, len(VIA))
    giro_orologio(T0 + 16 * 60)
    prova("a sedici minuti esce il messaggio di chi segue, da solo, con un annuncio e il link all'annuncio",
          (1, True, True),
          (len([1 for c, chi, _ in VIA if chi == COMPRA]),
           "ha pubblicato 1 nuovo annuncio" in (VIA[0][2] if VIA else ""),
           f"/annuncio/{a4}\">🫙 Apri l'annuncio" in (VIA[0][2] if VIA else "")))
    prova("...e Terzo («tutti», finestra di sessanta) aspetta ancora", 0,
          len([1 for c, chi, _ in VIA if chi == TERZO]))
    giro_orologio(T0 + 61 * 60)
    prova("a sessantuno minuti esce anche il suo, con un annuncio", (1, True),
          (len([1 for c, chi, _ in VIA if chi == TERZO]),
           any("🆕 <b>1 nuovo annuncio nel mercatino</b>" in t for c, chi, t in VIA if chi == TERZO)))

    print("\n[4) in moderazione, tolto, e chi smette o spegne]")
    VIA.clear()
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,prezzo_eur,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione) "
        "VALUES(?,?,'x',1000,0,?,'Torino (TO)','revisione',?,'ritiro',1,'sats','nuovo')",
        (VENDE, "In revisione", CAT, T0))
    rev = cur.lastrowid
    con.commit()
    con.close()
    asyncio.run(_ripassa(rev))
    prova("un annuncio in 'revisione' non entra in coda nemmeno se qualcuno lo spinge nel drenatore",
          [], [r for r in coda(COMPRA) + coda(TERZO) if r[0] == rev])
    # il quinto nasce, poi viene tolto prima del suo minuto
    a5 = pubblica(VENDE, "Candele profumate")
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='rimosso' WHERE id=?", (a5,))
    con.commit()
    con.close()
    giro_orologio(T0 + 200 * 60)
    prova("un annuncio tolto prima del suo minuto non si annuncia, e la riga si consuma (mandato=1)",
          (0, [(a5, "segui", 1)], [(a5, "tutti", 1)]),
          (len(VIA), [r for r in coda(COMPRA) if r[0] == a5], [r for r in coda(TERZO) if r[0] == a5]))
    # chi smette e chi spegne: l'arretrato si consuma
    a6 = pubblica(VENDE, "Olio nuovo")
    chiama(SRV.segui_venditore, {"segui": False}, COMPRA, "neg333")
    chiama(SRV.scegli_avvisi_mercatino,
           {"attivo": False, "categorie": [CAT], "prezzo_max": 0, "valuta": "sats"}, TERZO)
    giro_orologio(T0 + 400 * 60)
    prova("chi ha smesso di seguire e chi ha spento non ricevono l'arretrato; le righe si consumano",
          (0, [(a6, "segui", 1)], [(a6, "tutti", 1)]),
          (len([1 for _, chi, _ in VIA if chi in (COMPRA, TERZO)]),
           [r for r in coda(COMPRA) if r[0] == a6], [r for r in coda(TERZO) if r[0] == a6]))
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(COMPRA)))
    prova("il cassetto di Compra ora e' vuoto", [], me["seguiti"])
    prova("...mentre Nativa, che segue ancora, il DM dell'olio l'ha ricevuto", 1,
          len([1 for c, chi, t in VIA if chi == "npub1nativa" and "Olio nuovo" in t]))

    print("\n[5) la leva globale spenta]")
    SRV.MERCATINO_AVVISI_NUOVI = False
    r1 = chiama(SRV.segui_venditore, {"segui": True}, COMPRA, "neg333")
    r2 = chiama(SRV.scegli_avvisi_mercatino, {"attivo": True}, COMPRA)
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(COMPRA)))
    prova("le due rotte rispondono 409 e /api/me dice che gli avvisi non sono in casa",
          (409, 409, False), (r1.get("errore"), r2.get("errore"), me["avvisi_mercatino_leve"]["attivi"]))
    VIA.clear()
    pubblica(VENDE, "A leva spenta")
    giro_orologio(T0 + 900 * 60)
    prova("...e a leva spenta non parte niente, nemmeno a chi segue", 0, len(VIA))
    SRV.MERCATINO_AVVISI_NUOVI = True

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


async def _ripassa(annuncio_id):
    """Lo stesso gesto della modifica approvata: l'annuncio torna nel
    drenatore degli avvisi."""
    SRV.accoda_match(annuncio_id)
    await asyncio.sleep(1.5)


if __name__ == "__main__":
    sys.exit(main())
