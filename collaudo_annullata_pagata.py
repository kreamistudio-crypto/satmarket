# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA FATTURA ANNULLATA E PAGATA (13 ott 2026).

Il caso, verificato con una sonda il 13 ott: Anna compra l'ultimo pezzo
e annulla; il pezzo torna libero ma la sua fattura e' ancora viva nel
wallet. Bruno compra e paga. Poi Anna paga la fattura annullata — e il
riacciuffo portava anche il SUO ordine a 'locked' senza guardare se il
pezzo c'era ancora: due ordini pagati per un oggetto solo, «Hai
venduto!» due volte. Da oggi quel saldo NON diventa una vendita: chi
vende non riceve niente, chi ha pagato viene avvisato e rimborsato, i
moderatori lo sanno. E se ad annullare era stato chi vende, si rimborsa
SEMPRE, anche col pezzo ancora in vetrina.

Qui gira il SERVER VERO — il modulo intero, lo schema di `init_db` con
la colonna nuova, la cassa vera (`compra`), l'annullo vero, il
riacciuffo vero (`controlla_annullati`), il rimborso vero con
`paga_venditore`, il giro dei pagamenti sospesi, la lista vera di
/api/orders, la ronda del libro mastro e la riconciliazione — su un
database usa-e-getta. Di finto c'e' SOLO il nodo (il LNbits di cartone
di `collaudo_lnbits_muto`, che tiene una riga per payment hash come
quello vero), la fattura coniata dal Lightning address e le due piazze
(Nostr e il canale), che qui si CONTANO.

   1. Anna e Bruno: nessuna seconda vendita, rimborso intero, parole sue;
   2. due passaggi dell'orologio di fila: un rimborso solo;
   3. il pezzo c'e' ancora: chi paga ha comprato, come ieri;
   4. il pezzo e' PRENOTATO da un altro (fattura viva): rimborso, e
      l'altro poi compra davvero;
   5. la SUA stessa fattura nuova non le nega il pezzo;
   6. senza Lightning address: 'refund', poi incolla la fattura;
   7. il nodo muto: 'da_riprovare', e riparte da solo;
   8. il server che cade a meta': al riavvio finisce il lavoro, una
      volta sola;
   9. l'annullo del VENDITORE pagato dopo: rimborso sempre;
  10. il set con UN pezzo che manca: torna tutto;
  11. l'annuncio rimosso nel frattempo;
  12. chi vende non vede niente e i conti non si muovono;
  13. il libro mastro e la riconciliazione tacciono (e sanno parlare).

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_annullata_pagata.py
"""

import asyncio
import sys
import time
import traceback

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
SRV = None
ANNA, BRUNO, VENDE, ADMIN = 111, 333, 222, 999

CONIATE = []        # (address, sats) di ogni fattura chiesta a un address
FATTURE = {}        # payment_hash -> sats della fattura d'ingresso
PIAZZE = []         # ("nostr"|"canale", annuncio_id, ...) di ogni avviso
XP = []             # ogni premio di XP o distintivo tentato


# ------------------------------------------------------------ attrezzi
def db_esegui(sql, *args):
    con = SRV.db()
    con.execute(sql, args)
    con.commit()
    con.close()


def db_uno(sql, *args):
    con = SRV.db()
    r = con.execute(sql, args).fetchone()
    con.close()
    return r


def pulisci():
    banco.DETTO.clear()
    banco.AVVISI.clear()
    banco.USCITE.clear()
    CONIATE.clear()
    PIAZZE.clear()
    XP.clear()


def detti_a(chi):
    return [t for d, t in banco.DETTO if d == chi]


def nuovo_annuncio(titolo, quantita=1):
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,quantita_max,valuta,"
        "condizione) VALUES(?,?,'una cosa',50000,'Altro','Pavia (PV)',"
        "'attivo',1,'ritiro',?,?,'sats','nuovo')",
        (VENDE, titolo, quantita, quantita))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def annuncio(aid):
    a = db_uno("SELECT stato, quantita FROM annunci WHERE id=?", aid)
    return (a["stato"], a["quantita"])


def compra(chi, aid):
    banco.come(chi)
    return banco.chiama(SRV.compra, None,
                        corpo={"annuncio_id": aid,
                               "consegna": "ritiro"})["ordine_id"]


def compra_set(chi, aids):
    banco.come(chi)
    return banco.chiama(
        SRV.compra, None,
        corpo={"righe": [{"annuncio_id": a, "quantita": 1} for a in aids],
               "consegna": "ritiro"})["ordine_id"]


def annulla(chi, oid):
    banco.come(chi)
    return banco.chiama(SRV.annulla_ordine, oid)


def paga(oid):
    """I sats arrivano sul nodo di cartone: la fattura di quest'ordine
    risulta pagata a chiunque lo chieda (`invoice_pagata`, per hash)."""
    banco.PAGAMENTI[banco.riga(oid)["payment_hash"]] = "success"


def verifica(chi, oid):
    """Il poll del telefono: la strada vera di chi paga e resta li'."""
    banco.come(chi)
    return banco.chiama(SRV.verifica_pagamento, oid)


def orologio():
    asyncio.run(SRV.controlla_annullati())


def giro_sospesi():
    # il ritentativo per cause nostre aspetta 1, 5, 15, 30 minuti e poi
    # un'ora: invece di fermare l'orologio si INVECCHIA di piu' di
    # un'ora la linea del tempo, cosi' la riga e' di turno a ogni giro
    db_esegui("UPDATE payout_passi SET quando=quando-3700, "
              "ultimo=ultimo-3700")
    db_esegui("UPDATE ordini SET payout_ultimo=0")
    asyncio.run(SRV.riprova_pagamenti_sospesi())


def miei(chi, admin=False):
    banco.come(chi, admin)
    return {r["id"]: r for r in SRV.miei_ordini(0, "", "")}


def ln_address(tg_id, valore):
    db_esegui("UPDATE utenti SET ln_address=? WHERE tg_id=?", valore, tg_id)


def stato(oid):
    o = banco.riga(oid)
    return (o["stato"], o["payout_stato"] or "")


def timbro(oid):
    return int(banco.riga(oid).get("pagata_da_annullata_il") or 0) > 0


def annullata_e_pagata(aid, chi=ANNA):
    """Il gesto di Anna fino al saldo: compra, annulla, paga lo stesso.
    Torna l'ordine; il riacciuffo lo fa chi chiama."""
    oid = compra(chi, aid)
    annulla(chi, oid)
    paga(oid)
    return oid


def scena(nome, fn):
    """Una scena che ESPLODE e' una scena rossa, non un collaudo morto:
    sul codice di prima meta' di queste funzioni non esiste nemmeno."""
    print(f"\n[{nome}]")
    pulisci()
    banco.NODO.update(codice=200, sats=50_000, esito="success")
    ln_address(ANNA, "anna@wallet.tld")
    try:
        fn()
    except Exception as e:
        traceback.print_exc()
        prova(f"la scena «{nome}» arriva in fondo", "senza eccezioni",
              f"{type(e).__name__}: {e}")


# -------------------------------------------------------------- scene
def scena_anna_e_bruno():
    aid = nuovo_annuncio("Radio a valvole")
    o_anna = compra(ANNA, aid)
    banco.come(BRUNO)
    try:
        banco.chiama(SRV.compra, None, corpo={"annuncio_id": aid,
                                              "consegna": "ritiro"})
        rifiuto = "comprato"
    except SRV.HTTPException as e:
        rifiuto = (e.status_code, "sta già pagando" in str(e.detail))
    prova("finche' Anna ha la fattura viva, Bruno non puo' comprare",
          (409, True), rifiuto)
    annulla(ANNA, o_anna)
    prova("Anna annulla: lapide, e il pezzo e' di nuovo libero",
          ("annullato", ("attivo", 1)),
          (banco.riga(o_anna)["stato"], annuncio(aid)))
    o_bruno = compra(BRUNO, aid)
    paga(o_bruno)
    verifica(BRUNO, o_bruno)
    prova("Bruno compra e paga: il SUO ordine e' nel deposito, "
          "l'annuncio venduto", ("locked", ("venduto", 0)),
          (banco.riga(o_bruno)["stato"], annuncio(aid)))
    prova("...a chi vende UN «Hai venduto!»", 1,
          sum("Hai venduto" in t for t in detti_a(VENDE)))
    venduto_prima = [p for p in PIAZZE if p[1] == aid]
    pulisci()

    # ---- Anna paga la fattura annullata ------------------------------
    paga(o_anna)
    orologio()
    o = banco.riga(o_anna)
    prova("la fattura annullata e pagata NON diventa una vendita: "
          "rimborsata, col timbro, senza disputa",
          ("refunded", "uscito", True, 0),
          (o["stato"], o["payout_stato"], timbro(o_anna), o["disputata"]))
    prova("...UN'uscita sola, dell'importo della fattura: mai piu' del "
          "deposito", (1, [("anna@wallet.tld", 50_000)], 50_000, 50_000),
          (len(banco.USCITE), CONIATE, o["prezzo_sats"],
           FATTURE[o["payment_hash"]]))
    prova("...l'ordine di Bruno non si e' mosso", "locked",
          banco.riga(o_bruno)["stato"])
    prova("...lo stock e l'annuncio nemmeno: venduto, 0 pezzi",
          ("venduto", 0), annuncio(aid))
    prova("...a chi vende NIENTE: nessun avviso, nessun «Hai venduto!»",
          [], detti_a(VENDE))
    prova("...Nostr e il canale non sentono niente (ne' «venduto» ne' "
          "«di nuovo disponibile»)", (2, []),
          (len(venduto_prima), PIAZZE))
    prova("...nessun XP e nessun distintivo", [], XP)
    ad_anna = detti_a(ANNA)
    prova("Anna legge DUE avvisi: il fatto, poi i sats", 2, len(ad_anna))
    prova("...il primo con parole sue: fattura annullata, oggetto non "
          "piu' disponibile, i sats tornano per intero",
          (True, True, True, True),
          ("Hai pagato una fattura annullata" in ad_anna[0],
           "«Radio a valvole» nel frattempo non è più disponibile"
           in ad_anna[0],
           "50.000 sats</b> tornano per intero" in ad_anna[0],
           "Arrivano da soli sul tuo Lightning address" in ad_anna[0]))
    prova("...il secondo dice che sono partiti", True,
          "Rimborso della fattura annullata" in ad_anna[-1]
          and "50.000 sats" in ad_anna[-1])
    tutto = " ".join(ad_anna).lower()
    prova("...mai «disputa», mai «il venditore ha annullato», mai "
          "«Ordine pagato!», mai l'invito al feedback", [],
          [p for p in ("disputa", "venditore", "ordine pagato", "feedback")
           if p in tutto])
    avviso = [a for a in banco.AVVISI if "Fattura annullata pagata" in a
              and "nessuna vendita" in a]
    prova("ai moderatori UN avviso chiaro: ordine, cifra, perche', e il "
          "rimborso gia' uscito", (1, True, True, True, True, True),
          (len(avviso),
           f"Ordine #{o_anna}" in avviso[0] if avviso else False,
           "50.000 sats" in avviso[0] if avviso else False,
           "l'oggetto non era più disponibile" in avviso[0]
           if avviso else False,
           "✅ uscito" in avviso[0] if avviso else False,
           "Al venditore non è arrivato nessun avviso" in avviso[0]
           if avviso else False))
    prova("...e non piu' l'avviso generico «portato avanti come un "
          "ordine normale»", [],
          [a for a in banco.AVVISI if "ordine normale" in a])
    return aid, o_anna, o_bruno


def scena_due_passaggi(o_anna):
    orologio()
    orologio()
    prova("due passaggi dell'orologio di fila: nessuna uscita in piu', "
          "nessun avviso in piu'", (0, [], []),
          (len(banco.USCITE), banco.DETTO, banco.AVVISI))
    prova("...e la riga e' quella di prima", ("refunded", "uscito"),
          stato(o_anna))


def scena_pezzo_disponibile():
    aid = nuovo_annuncio("Lampada", quantita=3)
    oid = annullata_e_pagata(aid)
    orologio()
    o = banco.riga(oid)
    prova("il pezzo c'e' ancora: chi paga ha comprato — 'locked', "
          "NESSUN timbro, lo stock scalato",
          ("locked", False, ("attivo", 2)),
          (o["stato"], timbro(oid), annuncio(aid)))
    prova("...«Hai venduto!» a chi vende e «Ordine pagato!» a chi compra",
          (1, 1), (sum("Hai venduto" in t for t in detti_a(VENDE)),
                   sum("Ordine pagato" in t for t in detti_a(ANNA))))
    prova("...nessun rimborso, nessuna fattura chiesta", (0, []),
          (len(banco.USCITE), CONIATE))
    prova("...e ai moderatori l'avviso del riacciuffo di sempre",
          (1, 0),
          (sum("ordine annullato" in a and "riacciuffato" in a
               for a in banco.AVVISI),
           sum("nessuna vendita" in a for a in banco.AVVISI)))


def scena_prenotato_da_un_altro():
    aid = nuovo_annuncio("Bicicletta")
    o_anna = compra(ANNA, aid)
    annulla(ANNA, o_anna)
    o_bruno = compra(BRUNO, aid)          # fattura VIVA, non ancora pagata
    paga(o_anna)
    orologio()
    prova("l'ultimo pezzo e' prenotato da Bruno (fattura viva): la "
          "fattura annullata di Anna si rimborsa, il pezzo resta suo",
          (("refunded", "uscito"), True, "creato", ("attivo", 1)),
          (stato(o_anna), timbro(o_anna), banco.riga(o_bruno)["stato"],
           annuncio(aid)))
    paga(o_bruno)
    verifica(BRUNO, o_bruno)
    prova("...poi Bruno paga: UNA vendita, UN «Hai venduto!»",
          ("locked", ("venduto", 0), 1),
          (banco.riga(o_bruno)["stato"], annuncio(aid),
           sum("Hai venduto" in t for t in detti_a(VENDE))))


def scena_la_sua_fattura_nuova():
    aid = nuovo_annuncio("Tappeto")
    vecchio = compra(ANNA, aid)
    annulla(ANNA, vecchio)
    nuovo = compra(ANNA, aid)             # ci ripensa: fattura nuova, SUA
    paga(vecchio)
    orologio()
    prova("la prenotazione che le si oppone e' la SUA: paga la vecchia "
          "e ha comprato ('locked', nessun timbro, nessun rimborso)",
          ("locked", False, 0),
          (banco.riga(vecchio)["stato"], timbro(vecchio),
           len(banco.USCITE)))
    prova("...la nuova resta la fattura viva di prima", "creato",
          banco.riga(nuovo)["stato"])


def scena_senza_metodo():
    aid, o_anna, o_bruno = _anna_e_bruno_fino_al_saldo("Orologio")
    ln_address(ANNA, "")
    pulisci()
    orologio()
    prova("senza Lightning address: 'refund' col timbro, nessun sat "
          "uscito, niente timbro di ritentativo",
          (("refund", ""), True, 0),
          (stato(o_anna), timbro(o_anna), len(banco.USCITE)))
    ad_anna = detti_a(ANNA)
    prova("...UN avviso solo, che dice come riaverli",
          (1, True, True),
          (len(ad_anna),
           "Hai pagato una fattura annullata" in (ad_anna or [""])[0],
           "Apri l'ordine nella Mini App e scegli come riceverli"
           in (ad_anna or [""])[0]))
    prova("...ai moderatori: il rimborso ASPETTA chi ha pagato", True,
          any("nessuna vendita" in a and "⏳ in attesa: chi ha pagato deve "
              "indicare come riceverlo" in a for a in banco.AVVISI))
    prova("...a chi vende niente, e lo stock fermo", ([], ("venduto", 0)),
          (detti_a(VENDE), annuncio(aid)))
    prova("...e l'annuncio NON risulta con un affare in corso in piu': "
          "conta solo l'ordine di Bruno", 1, _affari_in_corso(aid))
    # giorni dopo incolla la fattura
    pulisci()
    banco.come(ANNA)
    r = banco.chiama(SRV.deposita_invoice, o_anna, None,
                     corpo={"invoice": bolt11_finta(
                         50000, 3600, int(time.time()), phash=61)})
    prova("incolla la fattura: il rimborso parte, UN'uscita",
          (True, ("refunded", "uscito"), 1),
          (r.get("ok"), stato(o_anna), len(banco.USCITE)))
    prova("...con le parole della fattura annullata, e niente a chi vende",
          (True, [], []),
          (any("Rimborso della fattura annullata" in t
               for t in detti_a(ANNA)),
           [t for t in detti_a(ANNA) if "isputa" in t], detti_a(VENDE)))
    prova("...lo stock NON risale: l'oggetto e' di Bruno",
          (("venduto", 0), "locked", []),
          (annuncio(aid), banco.riga(o_bruno)["stato"], PIAZZE))


def scena_nodo_muto():
    aid, o_anna, o_bruno = _anna_e_bruno_fino_al_saldo("Vaso")
    pulisci()
    banco.NODO["codice"] = 520           # il nodo non risponde
    orologio()
    prova("nodo muto: la decisione e' presa ('refund', timbro) e il "
          "rimborso aspetta 'da_riprovare' — nessun sat mosso",
          (("refund", "da_riprovare"), True, 0),
          (stato(o_anna), timbro(o_anna), len(banco.USCITE)))
    prova("...Anna sa gia' che i sats tornano, e nessuno le dice che "
          "e' colpa sua", (True, []),
          (any("Hai pagato una fattura annullata" in t
               for t in detti_a(ANNA)),
           [t for t in detti_a(ANNA) if "non è partito" in t]))
    prova("...ai moderatori: non e' partito, ci riproviamo da soli", True,
          any("nessuna vendita" in a and "⏳ in attesa: non è partito, ci "
              "riproviamo da soli" in a for a in banco.AVVISI))
    orologio()
    giro_sospesi()
    prova("...finche' tace, il giro dei pagamenti non muove niente",
          (("refund", "da_riprovare"), 0),
          (stato(o_anna), len(banco.USCITE)))
    banco.NODO["codice"] = 200           # torna su
    giro_sospesi()
    prova("il nodo torna: il rimborso riparte DA SOLO, un'uscita",
          (("refunded", "uscito"), 1),
          (stato(o_anna), len(banco.USCITE)))
    giro_sospesi()
    orologio()
    prova("...e non riparte una seconda volta", 1, len(banco.USCITE))
    prova("...ad Anna in tutto: il fatto una volta, i sats una volta",
          (1, 1),
          (sum("Hai pagato una fattura annullata" in t
               for t in detti_a(ANNA)),
           sum("Rimborso della fattura annullata" in t
               for t in detti_a(ANNA))))
    prova("...ai moderatori un solo ⚠️ in tutto", 1,
          sum("nessuna vendita" in a for a in banco.AVVISI))


def scena_server_che_cade():
    aid, o_anna, o_bruno = _anna_e_bruno_fino_al_saldo("Quadro")
    pulisci()
    # LA CADUTA: la decisione e' scritta, e poi il processo muore — prima
    # di ogni avviso e prima di toccare il nodo
    esito = SRV._decidi_annullata_pagata(o_anna)
    prova("la decisione sta in UNA scrittura: stato, timbro e rimborso "
          "da riprovare verso chi ha pagato",
          ("esaurito", ("refund", "da_riprovare"), True, "compratore"),
          (esito, stato(o_anna), timbro(o_anna),
           banco.riga(o_anna)["payout_verso"]))
    prova("...e a quel punto nessuno ha ancora saputo niente", ([], [], 0),
          (banco.DETTO, banco.AVVISI, len(banco.USCITE)))
    # IL RIAVVIO: init_db gira all'import, col suo backfill di `disputata`
    SRV.init_db()
    prova("al riavvio il backfill NON la marca disputa", 0,
          banco.riga(o_anna)["disputata"])
    orologio()
    prova("il primo giro dell'orologio finisce gli avvisi: Anna e i "
          "moderatori, una volta ciascuno", (1, 1),
          (sum("Hai pagato una fattura annullata" in t
               for t in detti_a(ANNA)),
           sum("nessuna vendita" in a for a in banco.AVVISI)))
    giro_sospesi()
    prova("...e il giro dei pagamenti fa uscire il rimborso",
          (("refunded", "uscito"), 1),
          (stato(o_anna), len(banco.USCITE)))
    orologio()
    giro_sospesi()
    orologio()
    prova("altri giri: niente di piu' — un rimborso, un avviso a testa",
          (1, 1, 1, []),
          (len(banco.USCITE),
           sum("Hai pagato una fattura annullata" in t
               for t in detti_a(ANNA)),
           sum("nessuna vendita" in a for a in banco.AVVISI),
           detti_a(VENDE)))
    # LA SECONDA CADUTA: dopo il rimborso, prima dell'avviso ai moderatori
    aid, o_anna, o_bruno = _anna_e_bruno_fino_al_saldo("Cornice")
    pulisci()
    SRV._decidi_annullata_pagata(o_anna)
    asyncio.run(SRV._avvisi_annullata_pagata(o_anna, "compratore"))
    asyncio.run(SRV._rimborsa_compratore(o_anna))
    prova("caduta DOPO il rimborso: i sats sono usciti, i moderatori "
          "non sanno ancora niente", (("refunded", "uscito"), 0),
          (stato(o_anna), sum("nessuna vendita" in a
                              for a in banco.AVVISI)))
    orologio()
    orologio()
    prova("...il giro dopo li avvisa UNA volta, col rimborso gia' uscito, "
          "e ad Anna non ripete niente", (1, True, 1),
          (sum("nessuna vendita" in a for a in banco.AVVISI),
           any("✅ uscito" in a for a in banco.AVVISI),
           sum("Hai pagato una fattura annullata" in t
               for t in detti_a(ANNA))))


def scena_annullo_del_venditore():
    aid = nuovo_annuncio("Sedia", quantita=3)
    oid = compra(ANNA, aid)
    banco.come(VENDE)
    r = banco.chiama(SRV.annulla_vendita, oid, None,
                     corpo={"motivo": "spedizione"})
    prova("chi vende annulla l'ordine NON pagato («non posso spedire»): "
          "lapide, e ad Anna si dice che se paga i sats tornano",
          ("annullato", True, False),
          (r.get("stato"),
           any("i sats ti tornano per intero" in t for t in detti_a(ANNA)),
           any("riparte da solo" in t for t in detti_a(ANNA))))
    pulisci()
    paga(oid)
    orologio()
    o = banco.riga(oid)
    prova("Anna paga lo stesso, e il pezzo C'E' ANCORA (3 su 3): si "
          "rimborsa comunque — il no di chi vende resta un no",
          (("refunded", "uscito"), True, 0, ("attivo", 3), 1),
          (stato(oid), timbro(oid), o["disputata"], annuncio(aid),
           len(banco.USCITE)))
    prova("...nessuna vendita: niente «Hai venduto!», niente a chi vende",
          [], detti_a(VENDE))
    ad_anna = detti_a(ANNA)
    prova("...Anna legge parole sue: il venditore AVEVA annullato, i "
          "sats tornano per intero", (True, True, True),
          ("Hai pagato una fattura annullata" in (ad_anna or [""])[0],
           "Il venditore aveva annullato l'ordine «Sedia»"
           in (ad_anna or [""])[0],
           "50.000 sats</b> tornano per intero" in (ad_anna or [""])[0]))
    prova("...mai «disputa», mai «Ordine pagato!», mai il feedback", [],
          [p for p in ("disputa", "ordine pagato", "feedback")
           if p in " ".join(ad_anna).lower()])
    prova("...ai moderatori il motivo GIUSTO", (1, True, False),
          (sum("nessuna vendita" in a for a in banco.AVVISI),
           any("il venditore aveva annullato l'ordine" in a
               for a in banco.AVVISI),
           any("non era più disponibile" in a for a in banco.AVVISI)))
    con = SRV.db()
    n = SRV._conta_annulli_venditore(con, VENDE)
    con.close()
    prova("...e non e' un «annullo di un ordine pagato» nel conto di chi "
          "vende", 0, n)
    prova("...nella lista di Anna c'e', in quella di chi vende no",
          (True, False), (oid in miei(ANNA), oid in miei(VENDE)))
    # e con l'«esaurito», che mette l'annuncio in pausa
    aid2 = nuovo_annuncio("Sgabello")
    oid2 = compra(ANNA, aid2)
    banco.come(VENDE)
    banco.chiama(SRV.annulla_vendita, oid2, None,
                 corpo={"motivo": "esaurito"})
    pulisci()
    paga(oid2)
    orologio()
    prova("annullo per «esaurito» pagato dopo: stesso rimborso, e "
          "l'annuncio resta in pausa", (("refunded", "uscito"),
                                        ("venduto", 0), []),
          (stato(oid2), annuncio(aid2), detti_a(VENDE)))


def scena_set():
    a, b = nuovo_annuncio("Tazza"), nuovo_annuncio("Piattino")
    banco.NODO["sats"] = 100_000
    oid = compra_set(ANNA, [a, b])
    annulla(ANNA, oid)
    o_bruno = compra(BRUNO, b)            # si porta via UN pezzo del set
    paga(o_bruno)
    banco.NODO["sats"] = 50_000
    verifica(BRUNO, o_bruno)
    pulisci()
    banco.NODO["sats"] = 100_000
    paga(oid)
    orologio()
    o = banco.riga(oid)
    prova("set di due, ne manca UNO: nessuna vendita a meta' — torna "
          "tutto l'ordine, in un'uscita sola",
          (("refunded", "uscito"), True, 1, [("anna@wallet.tld", 100_000)],
           100_000),
          (stato(oid), timbro(oid), len(banco.USCITE), CONIATE,
           o["prezzo_sats"]))
    prova("...il pezzo che C'ERA resta in vetrina, intatto; l'altro e' "
          "di Bruno", (("attivo", 1), ("venduto", 0), "locked"),
          (annuncio(a), annuncio(b), banco.riga(o_bruno)["stato"]))
    prova("...a chi vende niente, alle piazze niente", ([], []),
          (detti_a(VENDE), PIAZZE))
    prova("...ad Anna il titolo del set", True,
          any("Hai pagato una fattura annullata" in t and "Tazza" in t
              for t in detti_a(ANNA)))


def scena_annuncio_rimosso():
    aid = nuovo_annuncio("Poster", quantita=4)
    oid = compra(ANNA, aid)
    # la rimozione: l'annuncio esce di scena e l'ordine mai pagato
    # diventa una lapide (la scrittura di `rimuovi_annuncio`)
    db_esegui("UPDATE annunci SET stato='rimosso' WHERE id=?", aid)
    db_esegui("UPDATE ordini SET stato='annullato', aggiornato=? WHERE id=?",
              int(time.time()), oid)
    paga(oid)
    orologio()
    prova("annuncio rimosso nel frattempo: niente piu' «serve un occhio "
          "umano» — si rimborsa, e l'annuncio resta rimosso",
          (("refunded", "uscito"), True, ("rimosso", 4), []),
          (stato(oid), timbro(oid), annuncio(aid), detti_a(VENDE)))


def scena_chi_vende_non_vede(aid, o_anna, o_bruno):
    la, lv, lm = miei(ANNA), miei(VENDE), miei(ADMIN, admin=True)
    prova("la lista di Anna porta l'ordine col suo timbro; quella di "
          "chi vende NO; quella di Bruno non c'entra",
          (True, True, False, False),
          (o_anna in la,
           bool(la.get(o_anna, {}).get("pagata_da_annullata_il")),
           o_anna in lv, o_anna in miei(BRUNO)))
    prova("...chi vende continua a vedere l'ordine vero, quello di Bruno",
          True, o_bruno in lv)
    aperto = [oid for oid, r in miei(ANNA).items()
              if r.get("pagata_da_annullata_il") and r["stato"] == "refund"]
    prova("...i moderatori vedono quelli ancora da rimborsare (la coda "
          "di sempre), mai di meno", True,
          all(oid in lm for oid in aperto))
    banco.come(ANNA)
    try:
        banco.chiama(SRV.lascia_feedback, o_anna, None,
                     corpo={"voto": 1, "commento": "mai arrivato"})
        fb = "accettato"
    except SRV.HTTPException as e:
        fb = (e.status_code, str(e.detail))
    prova("nessun feedback su quell'ordine: non c'e' stato un affare",
          (400, "Il feedback si lascia a affare concluso"), fb)
    prova("...e chi vende non ne ha ricevuti", 0,
          db_uno("SELECT COUNT(*) FROM feedback WHERE ordine_id=?",
                 o_anna)[0])
    prova("l'annuncio ha UN affare in corso: quello di Bruno", 1,
          _affari_in_corso(aid))
    v = db_uno("SELECT COALESCE(xp,0) AS xp FROM utenti WHERE tg_id=?",
               VENDE)
    prova("gli XP di chi vende non si sono mossi", 0, v["xp"])
    tardive = db_uno(
        "SELECT COUNT(*) FROM ordini WHERE pagata_da_annullata_il>0")[0]
    prova("nessuna delle fatture annullate e pagate e' marcata disputa, "
          "nemmeno dopo un riavvio", (True, 0),
          (tardive >= 6,
           (SRV.init_db(), db_uno(
               "SELECT COUNT(*) FROM ordini WHERE pagata_da_annullata_il>0 "
               "AND disputata<>0")[0])[1]))
    banco.come(ADMIN, True)
    conclusi = db_uno("SELECT COUNT(*) FROM ordini WHERE stato IN "
                      "('released','refunded') AND "
                      + SRV.SQL_NON_ANNULLATA_PAGATA)[0]
    prova("gli «affari conclusi» non le contano: nessun affare si e' "
          "concluso in questo collaudo", 0, conclusi)


def scena_libro_mastro(o_anna):
    SRV.CONTROLLO_LIBRO_MASTRO = True
    SRV.RICONCILIA_PAYOUT = True

    def ronda():
        db_esegui("DELETE FROM timbri WHERE nome=?", SRV.TIMBRO_LIBRO_MASTRO)
        banco.AVVISI.clear()
        asyncio.run(SRV.controlla_libro_mastro())
        return list(banco.AVVISI)

    def riconcilia():
        db_esegui("DELETE FROM timbri WHERE nome=?", SRV.TIMBRO_RICONCILIA)
        db_esegui("UPDATE ordini SET payout_verificato=0")
        banco.AVVISI.clear()
        asyncio.run(SRV.riconcilia_payout())
        return list(banco.AVVISI)

    prova("dopo tutte le scene il libro mastro TACE", [], ronda())
    prova("...e la riconciliazione dei pagamenti pure", [], riconcilia())
    # LE CONTROPROVE: le due ronde hanno guardato davvero queste righe
    h = banco.riga(o_anna)["payout_hash"]
    prova("il rimborso di Anna ha lasciato il suo hash sulla riga", True,
          bool(h) and h in banco.PAGAMENTI)
    banco.PAGAMENTI[h] = "failed"
    parla = riconcilia()
    prova("controprova: se il nodo dice che quel rimborso e' fallito, "
          "la riconciliazione NOMINA l'ordine", True,
          any(f"#{o_anna}" in a or f" {o_anna}" in a for a in parla))
    banco.PAGAMENTI[h] = "success"
    db_esegui("UPDATE ordini SET payout_stato='boh' WHERE id=?", o_anna)
    prova("controprova: un timbro fuori contratto su quella riga fa "
          "parlare il libro mastro", True,
          any("payout fuori contratto" in a for a in ronda()))
    db_esegui("UPDATE ordini SET payout_stato='uscito' WHERE id=?", o_anna)
    prova("...rimessa a posto, tace di nuovo", [], ronda())


# ------------------------------------------------------------ aiutanti
def _anna_e_bruno_fino_al_saldo(titolo):
    """Anna compra e annulla, Bruno compra e paga, Anna paga la fattura
    annullata. Il riacciuffo NON e' ancora passato."""
    aid = nuovo_annuncio(titolo)
    o_anna = compra(ANNA, aid)
    annulla(ANNA, o_anna)
    o_bruno = compra(BRUNO, aid)
    paga(o_bruno)
    verifica(BRUNO, o_bruno)
    paga(o_anna)
    return aid, o_anna, o_bruno


def _affari_in_corso(aid):
    con = SRV.db()
    n = SRV._ordini_vivi_annuncio(
        con, aid, ("released", "refunded", "annullato"), esclusi=True)
    con.close()
    return n


def main():
    global SRV
    print("=" * 58)
    print("  LA FATTURA ANNULLATA E PAGATA — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV

    async def fattura_da_address(addr, sats):
        # un hash NUOVO a ogni fattura: il LNbits di cartone tiene una
        # riga per hash, come quello vero
        CONIATE.append((addr, sats))
        return bolt11_finta(sats, 3600, int(time.time()),
                            phash=1000 + len(banco.PAGAMENTI))

    vera_invoice = SRV.crea_invoice_escrow

    async def invoice_contata(sats, memo, *a, **k):
        inv = await vera_invoice(sats, memo, *a, **k)
        # un hash che non si ripete nemmeno a due fatture nello stesso
        # microsecondo
        inv["payment_hash"] = f"{inv['payment_hash']}-{len(FATTURE)}"
        FATTURE[inv["payment_hash"]] = sats
        return inv

    async def nostr(annuncio_id, *a, **k):
        PIAZZE.append(("nostr", annuncio_id) + a)

    async def canale(annuncio_id, *a, **k):
        PIAZZE.append(("canale", annuncio_id, k.get("venduto", True)))

    async def polso(riga):
        banco.AVVISI.append(riga)

    async def premio(*a, **k):
        XP.append(a)

    SRV.invoice_da_ln_address = fattura_da_address
    SRV.crea_invoice_escrow = invoice_contata
    SRV.annuncio_su_nostr = nostr
    SRV.promo_venduto = canale
    SRV.polso_ordini_admin = polso
    SRV.premia_xp = premio
    SRV.premia_distintivi = premio
    # il freno del poll (un tot di verifiche al minuto per persona) qui
    # non e' in prova: le scene ne fanno una dozzina di fila
    SRV._frena = lambda *a, **k: None
    banco.semina()
    db_esegui("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
              "ln_address) VALUES(?,'Bruno','neg33333',1,'bruno@wallet.tld')",
              BRUNO)

    tenuti = {}

    def _prima():
        tenuti["abc"] = scena_anna_e_bruno()

    scena("1. Anna e Bruno", _prima)
    aid, o_anna, o_bruno = tenuti.get("abc", (0, 0, 0))
    scena("2. due passaggi dell'orologio",
          lambda: scena_due_passaggi(o_anna))
    scena("3. il pezzo c'e' ancora", scena_pezzo_disponibile)
    scena("4. prenotato da un altro", scena_prenotato_da_un_altro)
    scena("5. la sua fattura nuova", scena_la_sua_fattura_nuova)
    scena("6. senza Lightning address", scena_senza_metodo)
    scena("7. il nodo muto", scena_nodo_muto)
    scena("8. il server che cade a meta'", scena_server_che_cade)
    scena("9. l'annullo del venditore pagato dopo",
          scena_annullo_del_venditore)
    scena("10. il set con un pezzo che manca", scena_set)
    scena("11. l'annuncio rimosso", scena_annuncio_rimosso)
    scena("12. chi vende non vede, i conti non si muovono",
          lambda: scena_chi_vende_non_vede(aid, o_anna, o_bruno))
    scena("13. il libro mastro e la riconciliazione",
          lambda: scena_libro_mastro(o_anna))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    sys.exit(1 if banco.FALLITE else 0)


if __name__ == "__main__":
    main()
