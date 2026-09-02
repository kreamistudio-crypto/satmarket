# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE BOZZE (ago 2026).

`prove.py` difende la FORMA — che il giudice della moderazione sia
uno, che i ganci restino trattenuti, che l'UPDATE della modifica porti
il suo `e_bozza`. Quello che non puo' fare e' far girare la cosa VERA:
le sue prove non hanno un database e non chiamano una rotta.

Le domande su cui il cantiere si regge, e a cui risponde solo il
codice che gira:

  · una BOZZA nasce e NON esce da nessuna parte — niente Nostr, niente
    canale, niente avvisi di ricerca, niente polso agli admin: e' la
    prova regina, e non e' una forma, e' una traccia di esecuzione;
  · e non e' in vetrina: `/api/listings` non la serve, e la sua scheda
    risponde 404 come per un annuncio che non c'e';
  · MODIFICARE una bozza NON la pubblica. Il difetto era a un carattere
    di distanza — l'UPDATE dello stato e' lo stesso della
    pubblicazione — e l'ha trovato un `assert` mentre nasceva;
  · PUBBLICARLA paga la moderazione SUL TESTO IN COLONNA e fa partire
    in un colpo i tre ganci trattenuti;
  · il RITIRO riporta indietro un annuncio vivo, spegne la piazza e
    NON passa dalla moderazione — chi torna sui suoi passi non si fa
    giudicare;
  · e i due 400 non dicono a un estraneo se un annuncio esiste.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato; Nostr, il canale e le notifiche sono contatori —
quello che si misura e' se il gancio PARTE, non cosa dice.

USO:  python collaudo_bozza.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
NOSTR, PROMO, MATCH, ADMIN, AVVISI = [], [], [], [], []

VENDITORE = {"id": 222, "first_name": "Vende", "username": "vende",
             "nome": "Vende", "admin": False}
ESTRANEO = {"id": 111, "first_name": "Altro", "username": "altro",
            "nome": "Altro", "admin": False}
CHI = VENDITORE


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alza(nome, fn, atteso=400, dentro=""):
    """Come `prova`, ma per i rifiuti: il messaggio conta quanto il
    codice — «non e' tuo» e «e' gia' pubblicato» sono due cose diverse
    da leggere, e la prima non si deve poter dire a un estraneo."""
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        codice = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if codice == atteso and (not dentro or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return testo
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso {atteso} con {dentro!r}"
              f"\n      avuto:  {codice} {testo!r}")
        return testo
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")
    return ""


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-bozza-"),
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
    # le due che server.py importa per NOME: senza, l'ImportError
    # cade nello stesso `except` del file mancante e il messaggio
    # manda a cercare dalla parte sbagliata (ci sono inciampato)
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    # SOLO SE IL MODULO VERO NON SI CARICA, ed e' la forma onesta: su
    # una macchina allineata `import server` prende quello di sempre e
    # qui non cambia niente. Serve dove anthropic e httpx sono di due
    # ere diverse — il client si crea al MOMENTO DELL'IMPORT, quindi
    # senza questa rete nessun collaudo del progetto partirebbe. Non
    # falsa niente di quel che si misura: con la chiave a segnaposto
    # `moderazione_ai` esce alla prima riga e quel client non lo tocca
    # nessuno.
    try:
        import anthropic                      # noqa: F401
        anthropic.Anthropic(api_key="INCOLLA_QUI")
    except Exception:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(
            messages=types.SimpleNamespace(create=None))
        sys.modules["anthropic"] = finto
        print("   (anthropic sostituito: le versioni locali non si parlano)")
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def nostr_finto(aid, status, solo_aggiornamento=False):
        NOSTR.append((aid, status, solo_aggiornamento))

    async def admin_finto(testo, **k):
        ADMIN.append(testo)

    async def notifica_finta(tg_id, testo, **k):
        AVVISI.append((tg_id, testo))

    async def ritiro_finto(aid, **k):
        NOSTR.append((aid, "ritirato", False))
        return 1

    async def promo_rimuovi_finta(aid):
        PROMO.append(("rimuovi", aid))

    server.annuncio_su_nostr = nostr_finto
    server.notifica_admin = admin_finto
    server.notifica = notifica_finta
    server.ritira_da_nostr = ritiro_finto
    server.promo_rimuovi = promo_rimuovi_finta
    server.accoda_promo = lambda aid: PROMO.append(("promo", aid))
    server.accoda_match = lambda aid: MATCH.append(aid)
    # L'AI non si chiama MAI da qui: senza chiave `moderazione_ai`
    # risponde None (fail-open), ed e' proprio il ramo che gira in
    # produzione quando Anthropic tace. Il verdetto si pilota di volta
    # in volta dove serve.
    server.verifica_utente = lambda *a, **k: CHI
    return db


def chiama(fn, *args, corpo=None):
    """I ganci sono `create_task`: senza cedere il controllo almeno una
    volta il loop si chiuderebbe prima che partano, e i contatori
    direbbero zero per il motivo sbagliato."""
    async def leggi(_req):
        return corpo if corpo is not None else {}
    SRV.leggi_json = leggi

    async def giro():
        r = await fn(*args)
        await asyncio.sleep(0.05)
        return r
    return asyncio.run(giro())


def azzera():
    del NOSTR[:], PROMO[:], MATCH[:], ADMIN[:], AVVISI[:]


def semina():
    con = SRV.db()
    for t in ("offerte", "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome, neg in ((222, "Vende", "neg22222"), (111, "Altro", "neg11111")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'a@b.it')",
                    (tg, nome, neg))
    con.commit()
    con.close()
    azzera()


def crea(bozza=True, **extra):
    """Un annuncio nuovo dalla rotta VERA, con o senza il verbo."""
    corpo = {"titolo": "Miele di acacia", "descrizione": "Un chilo, 2026",
             "prezzo_sats": 30000, "categoria": "Alimenti e bevande",
             "zona": "Torino (TO)", "consegna": "spedizione",
             "condizione": "nuovo", "quantita": 3, "foto": []}
    corpo.update(extra)
    if bozza:
        corpo["bozza"] = True
    azzera()
    return chiama(SRV.pubblica, None, corpo=corpo)


def riga(aid, campi="stato, quantita"):
    con = SRV.db()
    r = con.execute(f"SELECT {campi} FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return tuple(r) if r else None


# ─────────────────────────────────────────────────────────────
def prove_la_bozza_non_esce():
    print("\n── UNA BOZZA NON ESCE DA NESSUNA PARTE ──")
    semina()
    d = crea()
    aid = d["id"]
    prova("nasce col suo stato", ("bozza", 3), riga(aid))
    prova("...e la risposta lo dice al client", True, d.get("bozza") is True)
    # LA PROVA REGINA: i tre canali e il polso agli admin sono MUTI.
    # Non e' una forma — e' una traccia di esecuzione, e con `pubblica`
    # che li chiama tutti in coda bastava un `return` mancante.
    prova("niente Nostr", [], NOSTR)
    prova("niente canale", [], PROMO)
    prova("niente avvisi di ricerca", [], MATCH)
    prova("niente polso ai moderatori", [], ADMIN)

    # e non e' in vetrina: la garanzia e' la forma dei filtri, ma la
    # forma la si controlla girandola
    fuori = asyncio.run(SRV.lista_annunci())
    ids = [a["id"] for a in (fuori if isinstance(fuori, list)
                             else fuori.get("annunci", []))]
    prova("la vetrina non la serve", False, aid in ids)
    # e la sua scheda risponde come per un annuncio che non c'e': il
    # link non esiste finche' non lo si decide
    alza("...e la sua scheda risponde 404",
         lambda: SRV.un_annuncio(aid), atteso=404)

    # ma il suo venditore la vede: e' il libro mastro, e una bozza che
    # non compare li' non compare da NESSUNA parte
    miei = SRV.miei_annunci()      # sincrona, come il suo gemello un_annuncio
    righe = miei if isinstance(miei, list) else miei.get("annunci", [])
    prova("«I tuoi annunci» la mostra", True,
          any(a["id"] == aid for a in righe))


def prove_lo_scudo():
    """LO SCUDO ANTI-DOPPIONE CONOSCE LA BOZZA, e non e' una
    rifinitura: senza, il doppio tocco su «Salva senza pubblicare» —
    il fetch lento col dito che ritocca, la causa prima per cui quello
    scudo esiste — lascerebbe DUE bozze gemelle. Il caso e' saltato
    fuori da solo mentre si scriveva questo collaudo: due `crea()` di
    fila e la seconda ha risposto con l'id della prima."""
    print("\n── IL DOPPIO TOCCO NON FA DUE BOZZE ──")
    semina()
    primo = crea()
    secondo = crea()
    prova("il secondo tocco ritrova la stessa bozza",
          primo["id"], secondo["id"])
    prova("...e il client lo sa (non e' un annuncio nuovo)", True,
          secondo.get("bozza") is True)
    con = SRV.db()
    n = con.execute("SELECT COUNT(*) c FROM annunci").fetchone()["c"]
    con.close()
    prova("...e nel database la riga e' UNA", 1, n)


def prove_modificare_non_pubblica():
    print("\n── MODIFICARE UNA BOZZA NON LA PUBBLICA ──")
    semina()
    aid = crea()["id"]
    azzera()
    d = chiama(SRV.modifica_annuncio, aid, None,
           corpo={"titolo": "Miele di castagno", "descrizione": "altro",
                  "prezzo_sats": 40000, "categoria": "Alimenti e bevande",
                  "zona": "Torino (TO)", "consegna": "spedizione",
                  "condizione": "nuovo"})
    # IL DIFETTO ERA A UN CARATTERE DI DISTANZA: l'UPDATE dello stato
    # e' lo stesso della pubblicazione, e senza `e_bozza` ritoccare
    # una bozza la mandava in vetrina in silenzio.
    prova("resta una bozza", "bozza", riga(aid, "stato")[0])
    # E LA RISPOSTA LO DICE AL CLIENT: e' l'unico modo che ha di
    # sapere, perche' modificando una bozza il verbo non parte dal
    # bottone. Senza, il toast direbbe «pubblicato» e proverebbe ad
    # aprire un dettaglio che in vetrina non c'e' (trovato dal vivo).
    prova("...e la risposta lo dice al client", True, d.get("bozza") is True)
    prova("...e il testo e' cambiato davvero", "Miele di castagno",
          riga(aid, "titolo")[0])
    prova("...e la piazza non se ne accorge", [], NOSTR)
    prova("...ne' il canale", [], PROMO)


def prove_pubblicare():
    print("\n── PUBBLICARE: I GANCI PARTONO IN UN COLPO ──")
    semina()
    aid = crea()["id"]
    azzera()
    d = chiama(SRV.pubblica_bozza, aid)
    prova("la bozza diventa attiva", "attivo", riga(aid, "stato")[0])
    prova("...e la risposta porta il suo id", aid, d.get("id"))
    prova("adesso Nostr parla", [(aid, "active", False)], NOSTR)
    prova("...e il canale", [("promo", aid)], PROMO)
    prova("...e gli avvisi di ricerca", [aid], MATCH)
    prova("...e i moderatori vedono cosa e' entrato", 1, len(ADMIN))
    prova("   ...e il polso dice da dove viene", True,
          "da bozza" in ADMIN[0])

    # IL DOPPIO TOCCO SU RETE LENTA: la seconda POST trova il fatto
    # compiuto e NON rifa' partire niente.
    azzera()
    alza("il secondo tocco trova il fatto compiuto",
         lambda: chiama(SRV.pubblica_bozza, aid),
         atteso=400, dentro="")
    prova("...e nessun gancio riparte", ([], [], []), (NOSTR, PROMO, MATCH))


def prove_il_testo_giudicato():
    print("\n── SI GIUDICA IL TESTO CHE VA IN VETRINA ──")
    semina()
    # Alla NASCITA la moderazione non gira: la parola vietata entra in
    # bozza senza un fiato — e' il patto del cantiere.
    # IL CASO DEVE POTER FALLIRE SOLO PER LA RAGIONE CHE SORVEGLIA
    # (la lezione di `_pare_recapito`): «pistola» da sola NON e' nella
    # lista — «pistola sparachiodi» e' un caso ambiguo lasciato all'AI
    # apposta — quindi con quella parola la prova sarebbe passata
    # anche col filtro tolto. «glock» invece il filtro lo prende.
    d = crea(titolo="Vendo una glock")
    aid = d["id"]
    prova("la parola vietata entra in bozza", "bozza", riga(aid, "stato")[0])
    prova("...e nessuno l'ha giudicata", [], ADMIN)
    # ...e si paga alla PUBBLICAZIONE, sul testo IN COLONNA
    azzera()
    testo = alza("...e alla pubblicazione il filtro parole la ferma",
                 lambda: chiama(SRV.pubblica_bozza, aid), atteso=400)
    prova("   ...col motivo scritto a chi legge", True,
          "arm" in testo.lower() or "vietat" in testo.lower())
    prova("   ...e la riga resta una bozza", "bozza", riga(aid, "stato")[0])
    prova("   ...e la piazza non l'ha mai vista", [], NOSTR)

    # il DUBBIO dell'AI: la bozza va in revisione, non in vetrina
    semina()
    aid = crea()["id"]
    azzera()

    async def dubbio(t, d):
        return ("dubbio", "sembra un servizio")
    vero, SRV.moderazione_ai = SRV.moderazione_ai, dubbio
    try:
        d = chiama(SRV.pubblica_bozza, aid)
    finally:
        SRV.moderazione_ai = vero
    prova("il dubbio la manda in revisione", "revisione", riga(aid, "stato")[0])
    prova("...e la risposta lo dice", True, d.get("revisione") is True)
    prova("...e i ganci restano trattenuti", ([], [], []),
          (NOSTR, PROMO, MATCH))


def prove_lo_scaffale_vuoto():
    print("\n── UNA BOZZA A ZERO PEZZI NASCE ESAURITA ──")
    semina()
    aid = crea()["id"]
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita=0 WHERE id=?", (aid,))
    con.commit()
    con.close()
    azzera()
    chiama(SRV.pubblica_bozza, aid)
    # L'INVARIANTE DI CASA: venduto <=> quantita=0. Senza, sarebbe un
    # annuncio comprabile all'occhio che alla cassa dice di no.
    prova("nasce esaurita e non «attiva»", ("venduto", 0), riga(aid))
    prova("...e i tre canali tacciono su uno scaffale vuoto",
          ([], [], []), (NOSTR, PROMO, MATCH))
    prova("...ma i moderatori lo vedono, e sanno che e' vuoto", True,
          bool(ADMIN) and "scaffale vuoto" in ADMIN[0])


def prove_il_ritiro():
    print("\n── DALLA VETRINA ALLA BOZZA, E RITORNO ──")
    semina()
    aid = crea(bozza=False)["id"]
    prova("l'annuncio nasce in vetrina", "attivo", riga(aid, "stato")[0])
    azzera()
    chiama(SRV.ritira_in_bozza, aid)
    prova("il ritiro lo rimette in bozza", "bozza", riga(aid, "stato")[0])
    # quel che era in piazza si ritira DAVVERO: un link che resta vivo
    # su un annuncio che non c'e' piu' e' il difetto peggiore
    prova("...e la nota Nostr si ritira", [(aid, "ritirato", False)], NOSTR)
    prova("...e il post di canale si cancella", [("rimuovi", aid)], PROMO)
    # e NON si e' passati dalla moderazione: tornare sui propri passi
    # non e' un atto da giudicare
    prova("...senza passare dalla moderazione", [], ADMIN)

    # e da li' si ripubblica: il giro si chiude
    azzera()
    chiama(SRV.pubblica_bozza, aid)
    prova("e si ripubblica", "attivo", riga(aid, "stato")[0])
    # L'EVENTO NOSTR C'ERA GIA': si AGGIORNA invece di nascere due
    # volte — il tag `d` e' stabile, ed e' la regola di
    # decidi_revisione.
    prova("...e la piazza aggiorna invece di raddoppiare", True,
          bool(NOSTR) and NOSTR[0][1] == "active")


def prove_cosa_non_si_ritira():
    print("\n── COSA NON SI PUO' RIMETTERE IN BOZZA ──")
    semina()
    aid = crea(bozza=False)["id"]
    con = SRV.db()
    con.execute("INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
                "prezzo_sats,stato,creato,aggiornato,quantita) "
                "VALUES(?,111,222,30000,'locked',1,1,1)", (aid,))
    con.commit()
    con.close()
    azzera()
    alza("con dei sats in cassaforte, no",
         lambda: chiama(SRV.ritira_in_bozza, aid), atteso=400)
    prova("...e l'annuncio resta dov'era", "attivo", riga(aid, "stato")[0])

    # l'importato: la sua vetrina sono i relay, e di la' non comandiamo
    semina()
    aid = crea(bozza=False)["id"]
    con = SRV.db()
    con.execute("UPDATE annunci SET contatto_nostr='npub1x' WHERE id=?", (aid,))
    con.commit()
    con.close()
    alza("un importato da Nostr, no",
         lambda: chiama(SRV.ritira_in_bozza, aid), atteso=400)


def prove_chi_enumera_non_impara():
    print("\n── L'ANTI-ORACOLO, SUL DATABASE VERO ──")
    global CHI
    semina()
    aid = crea()["id"]           # una bozza VERA, di un altro
    mai = aid + 5000             # un id che non esiste
    CHI = ESTRANEO
    try:
        a = alza("la bozza di un altro: 400",
                 lambda: chiama(SRV.pubblica_bozza, aid), atteso=400)
        b = alza("...e un id che non esiste: lo stesso 400",
                 lambda: chiama(SRV.pubblica_bozza, mai), atteso=400)
        prova("...con le STESSE parole", True, a == b)
        c = alza("il ritiro di un annuncio altrui: 400",
                 lambda: chiama(SRV.ritira_in_bozza, aid), atteso=400)
        d = alza("...e di uno che non esiste: lo stesso 400",
                 lambda: chiama(SRV.ritira_in_bozza, mai), atteso=400)
        prova("...con le STESSE parole", True, c == d)
    finally:
        CHI = VENDITORE
    prova("e la bozza non si e' mossa", "bozza", riga(aid, "stato")[0])


def prove_il_mondo_di_ieri():
    print("\n── IL MONDO DI IERI E' INTATTO ──")
    semina()
    d = crea(bozza=False)
    aid = d["id"]
    prova("senza il verbo si pubblica come sempre", "attivo",
          riga(aid, "stato")[0])
    prova("...e la risposta non parla di bozze", False, "bozza" in d)
    prova("...e i tre canali partono", True,
          bool(NOSTR) and bool(PROMO) and bool(MATCH))
    # e la modifica di un annuncio VIVO ripassa dalla moderazione e
    # aggiorna la piazza, come ha sempre fatto
    azzera()
    chiama(SRV.modifica_annuncio, aid, None,
           corpo={"titolo": "Miele nuovo", "descrizione": "d",
                  "prezzo_sats": 31000, "categoria": "Alimenti e bevande",
                  "zona": "Torino (TO)", "consegna": "spedizione",
                  "condizione": "nuovo"})
    prova("la modifica di un annuncio vivo aggiorna la piazza", True,
          bool(NOSTR))


def prove_la_ronda_tace():
    print("\n── IL LIBRO MASTRO NON SI SVEGLIA ──")
    semina()
    crea()                                     # una bozza
    aid = crea(bozza=False, titolo="Altro miele")["id"]
    chiama(SRV.ritira_in_bozza, aid)           # e una ritirata
    con = SRV.db()
    rumore = []
    for nome, _perche, sql in SRV.CONTROLLI_LIBRO_MASTRO:
        try:
            if con.execute(sql).fetchall():
                rumore.append(nome)
        except sqlite3.Error as e:
            rumore.append(f"{nome} (esplosa: {e})")
    con.close()
    prova("nessun controllo suona su una bozza", [], rumore)


def main():
    db = avvio()
    print(f"database usa-e-getta: {db}")
    prove_la_bozza_non_esce()
    prove_lo_scudo()
    prove_modificare_non_pubblica()
    prove_pubblicare()
    prove_il_testo_giudicato()
    prove_lo_scaffale_vuoto()
    prove_il_ritiro()
    prove_cosa_non_si_ritira()
    prove_chi_enumera_non_impara()
    prove_il_mondo_di_ieri()
    prove_la_ronda_tace()
    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
