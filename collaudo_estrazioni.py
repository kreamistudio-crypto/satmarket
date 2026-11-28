# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE ESTRAZIONI (26 nov 2026, cantiere estrazioni).

Chi vende mette in palio il SUO annuncio; partecipano i suoi invitati
della finestra o chi apre il link dedicato; alla chiusura il primo
blocco dopo la scadenza sceglie il numero. Qui girano le ROTTE VERE e il
giro VERO dell'orologio su un database usa-e-getta, con la catena finta
del collaudo (un blocco al minuto, hash = sha256("collaudo-blocco:h")):

  1. l'apertura e i suoi no (modo, durata, non tuo, piu' pezzi, doppia);
  2. il nastro e le guardie: in palio non si compra;
  3. il «Partecipo» del link: un numero a testa, in ordine d'arrivo, e
     mai a chi regala, a un Nostr o senza il codice giusto;
  4. la vista: il link solo a chi regala, il biglietto solo al suo, mai
     un nome;
  5. l'annullo: solo a lista vuota;
  6. la chiusura: lista congelata con la sua impronta, poi il blocco,
     il vincitore giusto, l'annuncio esaurito, gli avvisi coi contatti;
  7. il modo 'inviti': entra chi si collega DENTRO la finestra, e solo
     se e' Telegram; l'avviso «Sei dentro» parte una volta;
  8. la lista vuota e l'annuncio sparito.

USO:  python collaudo_estrazioni.py
"""

import asyncio
import hashlib
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def _db():
    return banco.SRV.db()


def persona(tg_id, nome, username=""):
    con = _db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, username, "
                "negozio, registrato) VALUES(?,?,?,?,?)",
                (tg_id, nome, username, f"neg{abs(tg_id)}", int(time.time())))
    con.commit()
    con.close()


def annuncio(titolo, quantita=1, venditore=222):
    con = _db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(?,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
        "'spedizione',?,'sats','nuovo')", (venditore, titolo, quantita))
    con.commit()
    con.close()
    return cur.lastrowid


def errore(fn, *args, corpo=None):
    """(codice, testo) di un no, o None se la rotta ha detto si'."""
    try:
        banco.chiama(fn, *args, corpo=corpo)
    except banco.SRV.HTTPException as e:
        return e.status_code, e.detail
    return None


def apri(aid, corpo, chi=222):
    banco.come(chi)
    return banco.chiama(banco.SRV.apri_estrazione, aid, None, "x", "",
                        corpo=corpo)


def vista(aid, chi):
    if chi is None:
        banco.SRV.utente_se_autenticato = lambda *a, **k: None
    else:
        banco.come(chi)
        banco.SRV.utente_se_autenticato = lambda *a, **k: {"id": chi}
    return banco.SRV.leggi_estrazione(aid, "x", "")["estrazione"]


def partecipa(codice, chi):
    banco.come(chi)
    return banco.chiama(banco.SRV.partecipa_estrazione, None, "x", "",
                        corpo={"codice": codice})


def riga(eid):
    con = _db()
    r = dict(con.execute("SELECT * FROM estrazioni WHERE id=?",
                         (eid,)).fetchone())
    con.close()
    return r


def stato_annuncio(aid):
    con = _db()
    r = con.execute("SELECT stato FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return r["stato"]


def detti_a(tg_id):
    return [t for chi, t in banco.DETTO if chi == tg_id]


def main():
    print("=" * 58)
    print("  LE ESTRAZIONI — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    persona(222, "Jj", "jj_regala")
    persona(111, "Primo", "primo_tg")
    persona(333, "Seconda", "")
    persona(-5, "Nostrano")

    # ---- 0) le pure -------------------------------------------------
    print("\n[le pure]")
    prova("hash 0 su 5 partecipanti: il numero 1", 1,
          SRV.estrazione_vincitore("00" * 32, 5))
    prova("hash 7 su 5: il numero 3 (7 mod 5 + 1)", 3,
          SRV.estrazione_vincitore("00" * 31 + "07", 5))
    prova("nessun partecipante, nessun numero", 0,
          SRV.estrazione_vincitore("ff" * 32, 0))
    prova("l'impronta e' lo sha256 delle righe numero:biglietto",
          hashlib.sha256(b"1:AAAA\n2:BBBB").hexdigest(),
          SRV.estrazione_impronta([(1, "AAAA"), (2, "BBBB")]))

    # ---- 1) l'apertura ----------------------------------------------
    print("\n[l'apertura]")
    ps4 = annuncio("PS4 Slim")
    tre = annuncio("Tre tazze", quantita=3)
    banco.come(222)
    prova("un modo che non c'e' e' un no", 400,
          (errore(SRV.apri_estrazione, ps4, None, "x", "",
                  corpo={"modo": "boh", "giorni": 30}) or [0])[0])
    prova("zero giorni e' un no", 400,
          (errore(SRV.apri_estrazione, ps4, None, "x", "",
                  corpo={"modo": "link", "giorni": 0}) or [0])[0])
    prova("sessantuno giorni e' un no", 400,
          (errore(SRV.apri_estrazione, ps4, None, "x", "",
                  corpo={"modo": "link", "giorni": 61}) or [0])[0])
    banco.come(111)
    prova("l'annuncio di un altro non si mette in palio", 400,
          (errore(SRV.apri_estrazione, ps4, None, "x", "",
                  corpo={"modo": "link", "giorni": 30}) or [0])[0])
    banco.come(222)
    no = errore(SRV.apri_estrazione, tre, None, "x", "",
                corpo={"modo": "link", "giorni": 30})
    prova("con tre pezzi si chiede di duplicare con quantita' 1", True,
          bool(no) and "pezzo solo" in no[1])
    esito = apri(ps4, {"modo": "link", "giorni": 30,
                       "regolamento": "spedisco io"})
    e = esito["estrazione"]
    codice = riga(e["id"])["codice"]
    prova("si apre, e il codice ha la sua forma", True,
          bool(SRV._FORMA_CODICE_ESTRAZIONE.fullmatch(codice or "")))
    prova("il link porta annuncio, codice d'invito e codice dell'estrazione",
          True, e.get("link", "").startswith(
              f"{SRV.URL_PUBBLICO}/annuncio/{ps4}?invito=")
          and e["link"].endswith(f"&estrazione={codice}"))
    prova("chiude fra trenta giorni", 30 * 86400,
          e["chiude_il"] - e["aperta_il"])
    banco.come(222)
    prova("una seconda estrazione viva sullo stesso annuncio e' un 409", 409,
          (errore(SRV.apri_estrazione, ps4, None, "x", "",
                  corpo={"modo": "inviti", "giorni": 3}) or [0])[0])

    # ---- 2) il nastro e le guardie ----------------------------------
    print("\n[in palio non si compra]")
    prova("il nastro: l'annuncio e' fra quelli in palio", {ps4},
          SRV._annunci_in_palio([ps4, tre]))
    con = _db()
    try:
        SRV.guardia_estrazione(con, ps4)
        detto = None
    except SRV.HTTPException as x:
        detto = (x.status_code, "in palio" in x.detail)
    prova("la guardia dice no all'acquisto", (400, True), detto)
    con = _db()
    SRV.guardia_estrazione(con, tre)        # nessun no: niente eccezione
    con.close()
    src = open("server.py", encoding="utf-8").read()
    for nome in ("async def compra(", "async def _compra_set(",
                 "async def preventivo_ordine(", "async def fai_offerta("):
        if nome not in src:
            continue
        i = src.index(nome)
        prova(f"{nome[10:-1]} chiama la guardia", True,
              "guardia_estrazione(con" in src[i:src.index("\n\n\n", i)])

    # ---- 3) il Partecipo --------------------------------------------
    print("\n[il Partecipo del link]")
    v = partecipa(codice, 111)["estrazione"]
    prova("il primo che entra ha il numero 1", 1, v["mio"]["numero"])
    v2 = partecipa(codice, 111)["estrazione"]
    prova("rientrare non da' un secondo biglietto", (1, v["mio"]["biglietto"]),
          (v2["mio"]["numero"], v2["mio"]["biglietto"]))
    prova("la seconda persona ha il 2", 2,
          partecipa(codice, 333)["estrazione"]["mio"]["numero"])
    # dalla pagina dell'annuncio, senza il codice (28 nov 2026: «tutti
    # possano partecipare»): la stessa estrazione, lo stesso biglietto
    banco.come(111)
    v3 = banco.chiama(SRV.partecipa_estrazione, None, "x", "",
                      corpo={"annuncio": ps4})["estrazione"]
    prova("dall'annuncio senza codice si entra (stesso biglietto)",
          (1, v["mio"]["biglietto"]),
          (v3["mio"]["numero"], v3["mio"]["biglietto"]))
    banco.come(222)
    no = errore(SRV.partecipa_estrazione, None, "x", "",
                corpo={"codice": codice})
    prova("chi regala non partecipa", True, bool(no) and no[0] == 400)
    banco.come(-5)
    no = errore(SRV.partecipa_estrazione, None, "x", "",
                corpo={"codice": codice})
    prova("un account Nostr non partecipa", True,
          bool(no) and "Telegram" in no[1])
    banco.come(111)
    prova("un codice storto non trova niente", 404,
          (errore(SRV.partecipa_estrazione, None, "x", "",
                  corpo={"codice": "ZZZZZZZZZZ"}) or [0])[0])

    # ---- 4) la vista ------------------------------------------------
    print("\n[la vista]")
    a_lui = vista(ps4, 111)
    prova("a chi partecipa: il suo numero, e nessun link", (1, None),
          (a_lui["mio"]["numero"], a_lui.get("link")))
    a_jj = vista(ps4, 222)
    prova("a chi regala: il link e il conto, mai chi", (True, 2, False),
          ("link" in a_jj, a_jj["partecipanti"], "Primo" in str(a_jj)))
    anonimo = vista(ps4, None)
    prova("a chi guarda senza entrare: il conto, niente biglietto suo", (2, None),
          (anonimo["partecipanti"], anonimo.get("mio")))
    # la lista pubblica dal primo biglietto (27 nov 2026): righe
    # «numero:biglietto» in ordine, e nessun id o nome dentro
    prova("la lista anonima si vede gia' a estrazione aperta",
          ["1:" + v["mio"]["biglietto"], 2],
          [anonimo["biglietti"][0], len(anonimo["biglietti"])])
    prova("...senza id ne' nomi", False,
          any(x in str(anonimo["biglietti"]) for x in ("111", "333", "Primo")))

    # ---- 5) l'annullo -----------------------------------------------
    print("\n[l'annullo]")
    banco.come(222)
    no = errore(SRV.annulla_estrazione, e["id"], "x", "")
    prova("con dei biglietti non si annulla", True,
          bool(no) and "partecipanti" in no[1])

    # ---- 6) la chiusura e il sorteggio ------------------------------
    print("\n[la chiusura]")
    con = _db()
    con.execute("UPDATE estrazioni SET chiude_il=? WHERE id=?",
                (int(time.time()) - 5, e["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV.giro_estrazioni())
    # lo stesso giro avvisa i biglietti nuovi e POI chiude la scaduta
    prova("chi entra col link riceve in chat la ricevuta del suo numero",
          True, any("Sei dentro" in t and "numero è <b>1</b>" in t
                    for t in detti_a(111)))
    r = riga(e["id"])
    prova("alla chiusura ognuno riceve in chat impronta e suo numero", True,
          all(any("🔒" in t and r["impronta"] in t and f"numero è <b>{k}</b>"
                  in t for t in detti_a(tg)) for tg, k in ((111, 1), (333, 2))))
    prova("...e chi regala l'impronta", True,
          any(r["impronta"] in t for t in detti_a(222)))
    prova("scaduta: la lista si ferma e aspetta il blocco dopo la cima",
          ("attesa_blocco", 2, int(time.time()) // 60 + 1),
          (r["stato"], r["n_partecipanti"], r["blocco_altezza"]))
    con = _db()
    righe = [(x["numero"], x["biglietto"]) for x in con.execute(
        "SELECT numero, biglietto FROM estrazioni_partecipanti WHERE "
        "estrazione_id=? ORDER BY numero", (e["id"],))]
    con.close()
    prova("...con l'impronta della lista vera", SRV.estrazione_impronta(righe),
          r["impronta"])
    banco.come(333)
    no = errore(SRV.partecipa_estrazione, None, "x", "",
                corpo={"codice": codice})
    prova("a lista ferma non si entra piu'", True,
          bool(no) and "chiusa" in no[1])
    prova("la vista mostra i biglietti e il blocco atteso", (2, r["blocco_altezza"]),
          (len(vista(ps4, None)["biglietti"]), vista(ps4, None)["blocco_altezza"]))
    # il blocco minato: si porta l'altezza attesa sotto la cima finta
    altezza = int(time.time()) // 60 - 1
    con = _db()
    con.execute("UPDATE estrazioni SET blocco_altezza=? WHERE id=?",
                (altezza, e["id"]))
    con.commit()
    con.close()
    asyncio.run(SRV.giro_estrazioni())
    r = riga(e["id"])
    h = hashlib.sha256(f"collaudo-blocco:{altezza}".encode()).hexdigest()
    atteso = SRV.estrazione_vincitore(h, 2)
    vincitore, perdente = (111, 333) if atteso == 1 else (333, 111)
    prova("estratta col numero che dice il blocco",
          ("estratta", h, atteso, vincitore),
          (r["stato"], r["blocco_hash"], r["vincitore_numero"],
           r["vincitore_id"]))
    prova("l'annuncio diventa esaurito", "venduto", stato_annuncio(ps4))
    prova("e il nastro se ne va", set(), SRV._annunci_in_palio([ps4]))
    prova("il vincitore sente che ha vinto, col contatto di chi regala",
          True, any("Hai vinto" in t and "@jj_regala" in t
                    for t in detti_a(vincitore)))
    contatto = "@primo_tg" if vincitore == 111 else "Seconda"
    prova("chi regala sente il numero e il contatto del vincitore", True,
          any(f"numero {atteso}" in t and contatto in t
              for t in detti_a(222)))
    prova("chi non ha vinto sente com'e' andata, col conto e l'hash", True,
          any("Non era il tuo" in t and h in t for t in detti_a(perdente)))
    vg = vista(ps4, None)
    prova("la scheda mostra il conto intero: hash, resto, biglietto vincente",
          (h, int(h, 16) % 2, atteso),
          (vg["blocco_hash"], vg["resto"], int(vg["vincitore_numero"])))
    prova("...e il biglietto vincente e' quello della sua riga", True,
          f"{atteso}:{vg['vincitore_biglietto']}" in vg["biglietti"])
    vv = vista(ps4, vincitore)
    prova("la scheda del vincitore: ha vinto, e il contatto di chi regala",
          (True, "jj_regala"), (vv["ho_vinto"], vv["contatto"]["username"]))
    prova("la scheda di chi ha perso: nessun contatto", None,
          vista(ps4, perdente).get("contatto"))
    asyncio.run(SRV.giro_estrazioni())
    prova("un giro dopo non si estrae una seconda volta", "estratta",
          riga(e["id"])["stato"])

    # ---- 7) il modo inviti ------------------------------------------
    print("\n[i miei invitati]")
    bici = annuncio("Bici")
    con = _db()
    # un collegamento di PRIMA dell'apertura: non conta
    persona(440, "Vecchio")
    con.execute("INSERT INTO inviti(invitato, invitante, creato, via) "
                "VALUES(440, 222, ?, 'link')", (int(time.time()) - 3600,))
    con.commit()
    con.close()
    ei = apri(bici, {"modo": "inviti", "giorni": 2})["estrazione"]
    prova("al modo inviti il link e' quello d'invito di sempre", True,
          ei["link"].startswith(f"{SRV.URL_PUBBLICO}/?invito="))
    persona(444, "Nuovo")
    persona(-9, "NostrNuovo")
    con = _db()
    adesso = int(time.time())
    con.execute("INSERT INTO inviti(invitato, invitante, creato, via) "
                "VALUES(444, 222, ?, 'link')", (adesso + 1,))
    con.execute("INSERT INTO inviti(invitato, invitante, creato, via) "
                "VALUES(-9, 222, ?, 'nostr')", (adesso + 2,))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV.giro_estrazioni())
    prova("entra solo chi si e' collegato dentro la finestra, ed e' "
          "Telegram", {444: 1}, {
              x["tg_id"]: x["numero"] for x in _db().execute(
                  "SELECT tg_id, numero FROM estrazioni_partecipanti WHERE "
                  "estrazione_id=?", (ei["id"],))})
    prova("...e sente che e' dentro, col suo numero", True,
          any("Sei dentro" in t and "<b>1</b>" in t for t in detti_a(444)))
    banco.DETTO.clear()
    asyncio.run(SRV.giro_estrazioni())
    prova("l'avviso parte una volta sola", [], detti_a(444))

    # ---- 8) lista vuota, annuncio sparito, annullo a lista vuota ---
    print("\n[le chiusure senza vincitore]")
    vaso = annuncio("Vaso")
    ev = apri(vaso, {"modo": "link", "giorni": 1})["estrazione"]
    con = _db()
    con.execute("UPDATE estrazioni SET chiude_il=? WHERE id=?",
                (int(time.time()) - 5, ev["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV.giro_estrazioni())
    prova("senza partecipanti: vuota, e l'annuncio resta in vendita",
          ("vuota", "attivo"), (riga(ev["id"])["stato"], stato_annuncio(vaso)))
    prova("...e chi regala lo sa", True,
          any("senza partecipanti" in t for t in detti_a(222)))
    ev2 = apri(vaso, {"modo": "link", "giorni": 1})["estrazione"]
    prova("chiusa la prima, se ne riapre un'altra", "aperta", ev2["stato"])
    partecipa(riga(ev2["id"])["codice"], 111)
    con = _db()
    con.execute("UPDATE annunci SET stato='rimosso' WHERE id=?", (vaso,))
    con.execute("UPDATE estrazioni SET chiude_il=? WHERE id=?",
                (int(time.time()) - 5, ev2["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV.giro_estrazioni())
    prova("annuncio sparito: annullata, e chi partecipava lo sa",
          ("annullata", True),
          (riga(ev2["id"])["stato"],
           any("annullata" in t for t in detti_a(111))))
    lampada = annuncio("Lampada")
    el = apri(lampada, {"modo": "link", "giorni": 5})["estrazione"]
    banco.come(222)
    banco.chiama(SRV.annulla_estrazione, el["id"], "x", "")
    prova("a lista vuota si annulla, e l'annuncio torna comprabile",
          ("annullata", set()),
          (riga(el["id"])["stato"], SRV._annunci_in_palio([lampada])))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
