# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA PAUSA: «per ora e' finito» (ago 2026).

`prove.py` difende la FORMA — che il permesso dello zero viva in un
posto solo, che i due verbi guardino lo stato di partenza, che i ganci
non escano dal loro ramo. Quello che non puo' fare e' far girare la
cosa VERA: le sue prove non hanno un database e non chiamano una rotta.

Questo script chiude quel buco, ed e' il calco di `collaudo_reti.py`.
Le domande a cui risponde sono quelle su cui il cantiere si regge:

  · la PAUSA scrive davvero (venduto, 0), e da li' la vetrina non lo
    serve piu' mentre il LINK CONDIVISO si', che e' la ragione per cui
    tutto questo esiste — chi finisce le scorte non deve piu' scegliere
    fra rimuovere e chiudere il negozio;
  · il NO-OP e' muto: segnare esaurito cio' che e' gia' esaurito non
    riscrive niente e non fa ripartire NESSUN gancio. E' la prova
    regina, e non e' una forma: e' una traccia di esecuzione;
  · la MEMORIA DEI PEZZI attraversa la pausa (quantita_max non scende),
    o il badge «Ne resta 1» morirebbe per sempre al primo rifornimento;
  · le OFFERTE vive decadono tutte e tre in un colpo, e chi aveva
    offerto riceve UNA notifica sola;
  · il MONDO DI IERI e' intatto: `pubblica` e `modifica` con uno zero
    nel payload scrivono 1 come hanno sempre fatto.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato, e le due piazze (Nostr e il canale) sono sostituite
da contatori: quello che si misura e' se il gancio PARTE, non cosa dice.

USO:  python collaudo_pausa.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
# i tre contatori: quello che parte verso il mondo di fuori
NOSTR, CANALE, AVVISI = [], [], []

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


def alza(nome, fn, dentro=""):
    """Come `prova`, ma per i rifiuti: il messaggio conta quanto il
    codice — «scegli un numero piu' alto» e «potrai segnarlo esaurito»
    sono due consigli diversi per chi legge."""
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        codice = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if codice == 400 and (not dentro or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso 400 con {dentro!r}"
              f"\n      avuto:  {codice} {testo!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-pausa-"),
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

    async def nostr_finto(aid, status, solo_aggiornamento=False):
        NOSTR.append((aid, status))

    async def canale_finto(aid, venduto=True):
        CANALE.append((aid, venduto))

    async def notifica_finta(tg_id, testo):
        AVVISI.append((tg_id, testo))

    server.annuncio_su_nostr = nostr_finto
    server.promo_venduto = canale_finto
    server.notifica = notifica_finta
    server.verifica_utente = lambda *a, **k: VENDITORE
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


def ricarica(aid, q):
    return chiama(SRV.ricarica_quantita, aid, None, corpo={"quantita": q})


def riga(aid):
    con = SRV.db()
    r = con.execute("SELECT stato, quantita, quantita_max FROM annunci "
                    "WHERE id=?", (aid,)).fetchone()
    con.close()
    return (r["stato"], r["quantita"], r["quantita_max"])


def semina(quantita=5, stato="attivo"):
    """Un venditore, un annuncio suo, niente altro."""
    con = SRV.db()
    for t in ("offerte", "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(222,'Vende','neg22222',1)")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,quantita_max,valuta,"
        "condizione) VALUES(222,'Miele di acacia','desc',30000,'Altro',"
        "'Torino (TO)',?,1,'spedizione',?,?,'sats','nuovo')",
        (stato, quantita, max(quantita, 1)))
    con.commit()
    aid = cur.lastrowid
    con.close()
    del NOSTR[:], CANALE[:], AVVISI[:]
    return aid


# ---------------------------------------------------------------
def prove_pausa():
    print("\n── LA PAUSA: (venduto, 0) e le due piazze ──")
    aid = semina(5)
    r = ricarica(aid, 0)
    prova("la riga diventa (venduto, 0)", ("venduto", 0, 5), riga(aid))
    prova("...e la risposta lo dice al client", (True, False),
          (r["esaurito"], r["riattivato"]))
    prova("LA MEMORIA DEI PEZZI ATTRAVERSA LA PAUSA", 5, riga(aid)[2])
    prova("la piazza Nostr lo sa, e con la parola giusta",
          [(aid, "sold")], NOSTR)
    prova("il canale mette la spunta", [(aid, True)], CANALE)

    print("\n── IL NO-OP E' MUTO (la prova regina) ──")
    prima = riga(aid)
    del NOSTR[:], CANALE[:], AVVISI[:]
    r2 = ricarica(aid, 0)
    prova("la riga non si muove di un byte", prima, riga(aid))
    prova("...e la risposta non annuncia nessun passaggio", (False, False),
          (r2["esaurito"], r2["riattivato"]))
    prova("nessun gancio riparte verso Nostr", [], NOSTR)
    prova("nessun gancio riparte verso il canale", [], CANALE)

    print("\n── IL RITORNO, e il badge che si riaccende ──")
    del NOSTR[:], CANALE[:], AVVISI[:]
    r3 = ricarica(aid, 1)
    prova("torna in vetrina con un pezzo", ("attivo", 1, 5), riga(aid))
    prova("...e la risposta dice il passaggio opposto", (False, True),
          (r3["esaurito"], r3["riattivato"]))
    prova("Nostr lo rimette in vendita", [(aid, "active")], NOSTR)
    prova("il canale toglie la spunta", [(aid, False)], CANALE)
    # E' il senso di quantita_max: ne aveva 5, ne resta 1 -> e' una
    # notizia. Se la pausa l'avesse abbassata, questo direbbe False.
    prova("il badge «Ne resta 1» si riaccende", True,
          SRV.ultimo_pezzo(1, riga(aid)[2]))

    print("\n── IL GIRO COMPLETO, due volte ──")
    del NOSTR[:], CANALE[:], AVVISI[:]
    ricarica(aid, 0)
    ricarica(aid, 3)
    prova("pausa -> rifornimento -> (attivo, 3)", ("attivo", 3, 5), riga(aid))
    prova("due passaggi, due giri di ganci", 2, len(NOSTR))
    prova("...e nell'ordine giusto", [(aid, "sold"), (aid, "active")], NOSTR)


def prove_prenotati():
    print("\n── CHI STA PAGANDO PROPRIO ORA ──")
    aid = semina(5)
    con = SRV.db()
    con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,stato,creato,aggiornato,quantita) "
        "VALUES(?,111,222,30000,'creato',?,?,2)",
        (aid, int(time.time()), int(time.time())))
    con.commit()
    con.close()
    alza("lo zero si rifiuta finche' la fattura e' viva",
         lambda: ricarica(aid, 0), "potrai segnarlo esaurito")
    prova("...e l'annuncio non si e' mosso", ("attivo", 5, 5), riga(aid))
    prova("...senza toccare le due piazze", ([], []), (NOSTR, CANALE))
    # il consiglio dell'altro ramo resta quello di sempre
    alza("chi RIFORNISCE troppo poco sente l'altro consiglio",
         lambda: ricarica(aid, 1), "numero più alto")


def prove_offerte():
    print("\n── LE OFFERTE: decadono tutte e tre ──")
    aid = semina(5)
    con = SRV.db()
    for i, (compratore, stato) in enumerate(
            [(111, "proposta"), (333, "controproposta"), (444, "accettata"),
             (555, "rifiutata")]):
        con.execute(
            "INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
            "importo_sats,stato,creato,aggiornato) VALUES(?,?,222,900,?,1,1)",
            (aid, compratore, stato))
    con.commit()
    con.close()
    ricarica(aid, 0)
    con = SRV.db()
    stati = dict(con.execute(
        "SELECT compratore_id, stato FROM offerte WHERE annuncio_id=?",
        (aid,)).fetchall())
    con.close()
    prova("la proposta decade", "decaduta", stati[111])
    prova("la controproposta decade", "decaduta", stati[333])
    prova("e ANCHE l'accordo gia' accettato", "decaduta", stati[444])
    prova("chi era gia' fuori non si tocca", "rifiutata", stati[555])
    prova("tre avvisi, uno per persona", 3, len(AVVISI))
    prova("...e vanno alle tre persone giuste", {111, 333, 444},
          {a[0] for a in AVVISI})
    testo = AVVISI[0][1]
    prova("il testo non dice la bugia della vendita", False,
          "qualcun altro" in testo)
    prova("...ne' quella della vetrina", False, "in vetrina" in testo)
    prova("...e nomina l'annuncio", True, "Miele di acacia" in testo)

    print("\n── ...ma il no-op non riavvisa nessuno ──")
    con = SRV.db()
    con.execute("UPDATE offerte SET stato='proposta' WHERE compratore_id=111")
    con.commit()
    con.close()
    del AVVISI[:]
    ricarica(aid, 0)
    prova("l'annuncio era gia' esaurito: nessun avviso", [], AVVISI)


def prove_il_titolo_cattivo():
    print("\n── IL TITOLO CHE SPEGNEREBBE L'AVVISO ──")
    aid = semina(2)
    con = SRV.db()
    con.execute("UPDATE annunci SET titolo=? WHERE id=?",
                ("Cuffie <b>AKG</b> & \"K371\"", aid))
    con.execute(
        "INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
        "importo_sats,stato,creato,aggiornato) "
        "VALUES(?,111,222,900,'proposta',1,1)", (aid,))
    con.commit()
    con.close()
    ricarica(aid, 0)
    testo = AVVISI[0][1] if AVVISI else ""
    prova("il titolo nasce scappato", True, "&lt;b&gt;" in testo)
    prova("...e i grassetti restano PARI (Telegram li conta)",
          testo.count("<b>"), testo.count("</b>"))


def prove_la_porta_del_link():
    print("\n── IL LINK CONDIVISO NON MUORE ──")
    aid = semina(1)
    ricarica(aid, 0)
    con = SRV.db()
    in_vetrina = con.execute(
        "SELECT COUNT(*) FROM annunci WHERE id=? AND stato='attivo'",
        (aid,)).fetchone()[0]
    scaffale = con.execute(
        "SELECT COUNT(*) FROM annunci WHERE venditore_id=222 "
        "AND stato='venduto'").fetchone()[0]
    con.close()
    prova("la vetrina non lo serve piu'", 0, in_vetrina)
    prova("lo scaffale del negozio se lo prende", 1, scaffale)
    r = SRV.un_annuncio(aid)
    prova("...e il link condiviso risponde ancora", aid, r["id"])
    prova("...dicendo com'e' messo", "venduto", r["stato"])


def prove_il_mondo_di_ieri():
    print("\n── IL MONDO DI IERI, INTATTO ──")
    q = SRV.quantita_da_payload
    prova("pubblica: lo zero resta 1", 1, q({"quantita": 0}))
    prova("modifica: lo zero resta 1 e non azzera lo stock", 1,
          q({"quantita": 0}, se_manca=7))
    prova("l'assenza conserva ancora", 7, q({}, se_manca=7))
    prova("col permesso lo zero e' un gesto", 0,
          q({"quantita": 0}, zero_ammesso=True))
    prova("lo zero in stringa lo e' lo stesso", 0,
          q({"quantita": "0"}, zero_ammesso=True))
    # LE TRE CHE CONTANO: un numero rotto non e' mai un gesto
    prova("il negativo NON e' un gesto", 1,
          q({"quantita": -3}, zero_ammesso=True))
    prova("la parola storta non e' un gesto", 1,
          q({"quantita": "abc"}, zero_ammesso=True))
    prova("il falso non e' un gesto (int(False) fa 0)", 1,
          q({"quantita": False}, zero_ammesso=True))


def prove_la_ronda_tace():
    print("\n── IL LIBRO MASTRO NON SI SVEGLIA ──")
    aid = semina(4)
    ricarica(aid, 0)
    con = SRV.db()
    rumore = []
    for nome, _perche, sql in SRV.CONTROLLI_LIBRO_MASTRO:
        try:
            if con.execute(sql).fetchall():
                rumore.append(nome)
        except sqlite3.Error as e:
            rumore.append(f"{nome} (esplosa: {e})")
    con.close()
    prova("nessun controllo suona su un annuncio in pausa", [], rumore)


def main():
    db = avvio()
    print(f"database usa-e-getta: {db}")
    prove_pausa()
    prove_prenotati()
    prove_offerte()
    prove_il_titolo_cattivo()
    prove_la_porta_del_link()
    prove_il_mondo_di_ieri()
    prove_la_ronda_tace()
    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
