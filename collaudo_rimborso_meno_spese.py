# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL RIMBORSO MENO LE SPESE DI SPEDIZIONE (13 ott 2026,
cantiere «indirizzo-giusto», secondo push).

IL CASO: chi compra sbaglia l'indirizzo — o il punto di ritiro — e il
pacco torna indietro. Fin qui il moderatore poteva solo rimborsare
tutto, rimborsare dopo il reso o dare tutto a chi vende: le spese di
spedizione restavano sempre a chi aveva spedito. Il quarto esito le
rende a lui e rimborsa il resto a chi ha comprato.

SONO DUE PAGAMENTI DALLO STESSO DEPOSITO, e fino a ieri un ordine ne
aveva uno solo. `prove.py` difende la forma; qui gira la STORIA, sul
SERVER VERO con un database usa-e-getta e il nodo di cartone del banco
di casa (`collaudo_lnbits_muto`): `paga_venditore`, la decodifica, le
uscite, il giro dei pagamenti sospesi e la ronda del libro mastro sono
TUTTI quelli veri — di finto c'e' solo il nodo, che qui in piu' sa
rispondere in modo diverso a chi compra e a chi vende.

Le domande a cui risponde:
  1. tutto bene: due uscite, e sommate fanno ESATTAMENTE il deposito;
  2. chi vende non ha un metodo d'incasso: chi compra e' rimborsato lo
     stesso, la quota resta «da riscuotere» e si incassa con una
     fattura (dell'importo giusto, non del totale);
  3. chi compra non ha un metodo: chi vende incassa lo stesso, e la
     fattura del TOTALE viene rifiutata col numero giusto;
  4. il nodo rifiuta UNO dei due pagamenti: l'altro parte, e nessuno
     viene pagato due volte quando si riprova;
  5. il nodo e' muto: nessun sat si muove, nessuno riceve una bugia, e
     quando torna il giro dei pagamenti li fa partire tutti e due;
  6. IL SERVER CADE A META' — dopo la decisione e prima dei pagamenti,
     e fra il primo e il secondo — e RIPARTE: le due righe ci sono
     gia', il giro riprende quella che mancava, e le uscite restano
     due;
  7. la decisione e' DEFINITIVA: dopo, nessun esito si puo' piu'
     prendere (o uscirebbe piu' del deposito);
  8. dove il bottone non vale: spedizione inclusa o gratuita, spese
     uguali o piu' grandi del totale, ritiro in zona, un caso gia'
     deciso e incagliato; e dove vale: il punto di ritiro, il reso;
  9. NESSUNA LOGICA D'ASTA scatta su queste righe: «Le mie aste», il
     pallino del profilo, i solleciti, gli avvisi ai moderatori;
 10. la reputazione: non e' una disputa persa per nessuno dei due;
 11. IL LIBRO MASTRO torna sul sano, e parla su ogni riga rotta.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete,
nessuna chiave.

USO:  python collaudo_rimborso_meno_spese.py
"""

import asyncio
import time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
SRV = None

PREZZO, SPED = 30_000, 6_000
TOTALE = PREZZO + SPED
CASA = {"nome": "Mario Rossi", "via": "Via Garibaldi 17", "cap": "27100",
        "citta": "Pavia", "provincia": "PV", "telefono": "3330000000"}
A_COMPRA, A_VENDE = "compra@wallet.tld", "vende@wallet.tld"

# le fatture di cartone: bolt11 -> a chi e per quanto. Il nodo del
# banco risponde la stessa cifra e lo stesso esito a tutti; qui serve
# che sappia distinguere i due destinatari, ed e' l'unica cosa aggiunta
FATTURE = {}
ESITO = {}            # "compratore"/"venditore" -> come finisce il pagamento
CHIESTE = []          # (a chi, sats, esito) di ogni richiesta di PAGAMENTO
_coniate = [0]


class Caduta(BaseException):
    """Il processo che muore: NON e' una Exception, cosi' passa
    attraverso ogni `except Exception` come farebbe un kill."""


def fattura(chi, sats):
    _coniate[0] += 1
    b = bolt11_finta(sats, 3600, int(time.time()), phash=500 + _coniate[0])
    FATTURE[b] = {"chi": chi, "sats": sats}
    return b


def uscite():
    """Le uscite RIUSCITE: (a chi, sats)."""
    return [(c, s) for c, s, e in CHIESTE if e == "success"]


def somma_uscite():
    return sum(s for _, s in uscite())


def alza(nome, fn, codice, dentro=""):
    try:
        fn()
    except Exception as e:
        cod = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        prova(nome, (codice, True),
              (cod, (not dentro) or dentro.lower() in testo.lower()))
        if not (cod == codice and ((not dentro)
                                   or dentro.lower() in testo.lower())):
            print(f"      testo: {testo!r}")
        return
    prova(nome, codice, "nessun rifiuto")


def avvio():
    global SRV
    banco.avvio()
    SRV = banco.SRV

    async def fattura_da_address(addr, sats):
        return fattura("compratore" if addr == A_COMPRA else "venditore",
                       sats)

    async def zitto(*a, **k):
        return None

    SRV.invoice_da_ln_address = fattura_da_address
    SRV.annuncio_su_nostr = zitto
    SRV.promo_venduto = zitto

    # il nodo di cartone impara a distinguere i destinatari
    vero_post = banco._FintoHttpx.AsyncClient.post

    async def post(self, url, **kw):
        j = kw.get("json") or {}
        b = j.get("data") or j.get("bolt11") or ""
        if b in FATTURE:
            banco.NODO["sats"] = FATTURE[b]["sats"]
            banco.NODO["esito"] = ESITO.get(FATTURE[b]["chi"], "success")
            if "decode" not in url:
                CHIESTE.append((FATTURE[b]["chi"], FATTURE[b]["sats"],
                                banco.NODO["esito"]))
        return await vero_post(self, url, **kw)

    banco._FintoHttpx.AsyncClient.post = post


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


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci", "rimborsi_asta",
              "payout_passi", "payout_tentati"):
        try:
            con.execute(f"DELETE FROM {t}")
        except Exception:
            pass
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address,spedizionieri,spedizioniere) VALUES(222,'Vende',"
                "'neg22222',1,?,'|InPost|','InPost')", (A_VENDE,))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,?)", (A_COMPRA,))
    ids = []
    for titolo, consegna in (("Atlante", "spedizione"),
                             ("A mano", "entrambe")):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
            "valuta,condizione,spedizione_sats) VALUES(222,?,'desc',?,"
            "'Altro','Torino (TO)','attivo',1,?,40,40,'sats','buono',?)",
            (titolo, PREZZO, consegna, SPED))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    FATTURE.clear()
    CHIESTE.clear()
    ESITO.clear()
    banco.PAGAMENTI.clear()
    banco.USCITE.clear()
    banco.NODO.update(codice=200, esito="success")
    return ids


def metodi(compratore=A_COMPRA, venditore=A_VENDE):
    db_esegui("UPDATE utenti SET ln_address=? WHERE tg_id=111", compratore)
    db_esegui("UPDATE utenti SET ln_address=? WHERE tg_id=222", venditore)


def disputa(aid, corpo=None):
    """Un ordine pagato, spedito e finito in disputa, dai percorsi
    veri: l'acquisto, l'incasso (`_incassa_ordine`, che scala lo
    stock), e la disputa aperta da chi ha comprato."""
    banco.come(111)
    corpo = corpo or {"consegna": "spedizione", "spedizione_via": "casa",
                      "indirizzo": dict(CASA), "indirizzo_confermato": True}
    c = banco.chiama(SRV.compra, None,
                     corpo=dict(corpo, annuncio_id=aid, quantita=1))
    oid = c["ordine_id"]
    banco.chiama(SRV._incassa_ordine, oid)
    db_esegui("UPDATE ordini SET stato='shipped', corriere='BRT', "
              "tracking='BRT001', spedito_il=? WHERE id=?",
              int(time.time()) - 5 * 86400, oid)
    banco.come(111)
    banco.chiama(SRV.apri_disputa, oid, "", "")
    banco.DETTO.clear()
    banco.AVVISI.clear()
    CHIESTE.clear()
    return oid


def decidi(oid, esito="meno_spese"):
    banco.come(999, admin=True)
    return banco.chiama(SRV.risolvi_disputa, oid, None, "", "",
                        corpo={"esito": esito})


def ordine(oid):
    return banco.riga(oid)


def riga_spese(oid):
    r = db_uno("SELECT * FROM rimborsi_asta WHERE ordine_id=? AND "
               "motivo='spese_spedizione'", oid)
    return dict(r) if r else None


def n_righe_spese(oid):
    return db_uno("SELECT COUNT(*) FROM rimborsi_asta WHERE ordine_id=?",
                  oid)[0]


def detti_a(chi):
    return " || ".join(t for c, t in banco.DETTO if c == chi)


def ronda():
    db_esegui("DELETE FROM timbri WHERE nome=?", SRV.TIMBRO_LIBRO_MASTRO)
    banco.AVVISI.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    return " || ".join(banco.AVVISI)


def giro_sospesi():
    banco._passa_un_minuto()
    db_esegui("UPDATE ordini SET payout_ultimo=0")
    db_esegui("UPDATE rimborsi_asta SET payout_ultimo=0")
    asyncio.run(SRV.riprova_pagamenti_sospesi())


# ---------------------------------------------------------------
def scena_tutto_bene(aid):
    print("\n── 1. TUTTO BENE: due uscite, e fanno il deposito ──")
    oid = disputa(aid)
    stock_prima = db_uno("SELECT quantita FROM annunci WHERE id=?", aid)[0]
    r = decidi(oid)
    o, s = ordine(oid), riga_spese(oid)
    prova("la decisione torna «meno le spese», a ordine rimborsato",
          (True, "refunded", SPED),
          (r.get("meno_spese"), r.get("stato"), r.get("spese_sats")))
    prova("l'ordine porta la cifra trattenuta", SPED, o["spese_rese_sats"])
    prova("...ed e' 'refunded': nessuno stato nuovo", "refunded", o["stato"])
    prova("la quota di chi vende e' una riga «da riscuotere», riscossa",
          (222, SPED, "riscosso", 0, 0),
          (s["tg_id"], s["importo_sats"], s["stato"], s["annuncio_id"],
           s["puntata_id"]))
    prova("le uscite sono DUE: il resto a chi compra, le spese a chi vende",
          [("compratore", TOTALE - SPED), ("venditore", SPED)],
          sorted(uscite()))
    prova("...e sommate fanno ESATTAMENTE il deposito", TOTALE,
          somma_uscite())
    prova("l'oggetto e' tornato in vetrina", stock_prima + 1,
          db_uno("SELECT quantita FROM annunci WHERE id=?", aid)[0])
    c, v = detti_a(111), detti_a(222)
    prova("chi compra legge la cifra che arriva e quella che resta", True,
          "rimborso meno le spese di spedizione" in c
          and SRV._fmt_sats(TOTALE - SPED) in c and SRV._fmt_sats(SPED) in c)
    prova("...e NON «a tuo favore», NE' «rimborso integrale»",
          (False, False), ("a tuo favore" in c, "integrale" in c))
    prova("chi vende legge che le spese sono sue, e che le ha incassate",
          True, "rimborso meno le spese di spedizione" in v
          and "Spese di spedizione incassate" in v)
    prova("...e non gli si parla di aste ne' di «rimborsi in arrivo»",
          (False, False), ("asta" in v.lower(), "Rimborso in arrivo" in v))
    return oid


def scena_definitiva(oid):
    print("\n── 7. A ORDINE CHIUSO NON SI RIDECIDE ──")
    # qui l'ordine e' gia' 'refunded': non e' piu' una disputa, e la
    # rotta risponde come per ogni ordine chiuso. Il caso che conta —
    # la decisione presa e un pagamento ancora da fare — sta nella
    # scena 3, dove l'ordine e' in 'refund' e la rotta di prima lo
    # avrebbe riaperto.
    prima = len(CHIESTE)
    for esito in ("meno_spese", "rimborso", "venditore", "reso"):
        alza(f"a ordine rimborsato, «{esito}» si rifiuta",
             lambda e=esito: decidi(oid, e), 400, "già chiusa")
    prova("...e nessun pagamento e' ripartito", prima, len(CHIESTE))
    prova("...e la riga di chi vende e' rimasta UNA", 1, n_righe_spese(oid))


def scena_venditore_senza_metodo(aid):
    print("\n── 2. CHI VENDE NON HA UN METODO D'INCASSO ──")
    metodi(venditore="")
    oid = disputa(aid)
    r = decidi(oid)
    o, s = ordine(oid), riga_spese(oid)
    prova("chi compra e' rimborsato lo stesso", ("refunded", True),
          (o["stato"], r.get("compratore_pagato")))
    prova("...della cifra ridotta, e basta",
          [("compratore", TOTALE - SPED)], uscite())
    prova("la quota di chi vende resta «da riscuotere», ferma",
          ("da_riscuotere", ""), (s["stato"], s["payout_stato"] or ""))
    v = detti_a(222)
    prova("...e glielo si dice: sono spese di spedizione, sull'ordine",
          True, "spese di spedizione" in v and f"#{oid}" in v
          and "da incassare" in v)
    # NIENTE LOGICA D'ASTA SU QUESTA RIGA
    banco.come(222)
    mie = SRV.mie_puntate("", "")
    prova("«Le mie aste» NON la elenca fra i rimborsi da riscuotere", [],
          mie.get("da_riscuotere"))
    me = asyncio.run(SRV.mio_profilo("", ""))
    prova("...e il pallino delle aste su cui agire resta a zero", 0,
          me.get("aste_da_agire"))
    # il sollecito: stesse leve, altre parole
    banco.DETTO.clear()
    banco.AVVISI.clear()
    vecchio = int(time.time()) - 400 * 86400
    db_esegui("UPDATE rimborsi_asta SET aggiornato=?, sollecito_il=0 "
              "WHERE id=?", vecchio, s["id"])
    asyncio.run(SRV.sollecita_rimborsi_puntate())
    sol = detti_a(222)
    prova("il sollecito arriva, e parla di spese di spedizione", True,
          "spese di spedizione da incassare" in sol and f"#{oid}" in sol)
    prova("...mai di un'asta", False, "asta" in sol.lower())
    db_esegui("UPDATE rimborsi_asta SET aggiornato=?, sollecito_il=0, "
              "solleciti=? WHERE id=?", vecchio, SRV.SOLLECITO_INCASSO_MAX,
              s["id"])
    banco.AVVISI.clear()
    asyncio.run(SRV.sollecita_rimborsi_puntate())
    adm = " || ".join(banco.AVVISI)
    prova("ignorati i solleciti, ai moderatori si dice «spese di "
          "spedizione ferme», non «rimborso d'asta»", (True, False),
          ("Spese di spedizione ferme" in adm and f"#{oid}" in adm,
           "asta" in adm.lower()))
    # l'incasso a mano: la fattura dell'importo giusto
    banco.come(222)
    alza("una fattura del TOTALE si rifiuta, col numero giusto",
         lambda: banco.chiama(SRV.deposita_invoice_rimborso, s["id"], None,
                              "", "", corpo={"invoice": fattura("venditore",
                                                                TOTALE)}),
         400, f"{SRV._fmt_sats(SPED)} sats (le spese di spedizione)")
    banco.come(111)
    alza("...e chi ha comprato non puo' incassarla al suo posto",
         lambda: banco.chiama(SRV.deposita_invoice_rimborso, s["id"], None,
                              "", "", corpo={"invoice": fattura("compratore",
                                                                SPED)}),
         400, "non permessa")
    banco.come(222)
    banco.chiama(SRV.deposita_invoice_rimborso, s["id"], None, "", "",
                 corpo={"invoice": fattura("venditore", SPED)})
    prova("con la fattura giusta la quota parte", "riscosso",
          riga_spese(oid)["stato"])
    prova("...e le uscite tornano a fare il deposito", TOTALE,
          somma_uscite())
    metodi()


def scena_compratore_senza_metodo(aid):
    print("\n── 3. CHI COMPRA NON HA UN METODO ──")
    metodi(compratore="")
    oid = disputa(aid)
    r = decidi(oid)
    o, s = ordine(oid), riga_spese(oid)
    prova("chi vende incassa lo stesso la sua quota",
          ("riscosso", [("venditore", SPED)]), (s["stato"], uscite()))
    prova("l'ordine resta in 'refund', come un rimborso senza metodo",
          ("refund", False), (o["stato"], r.get("compratore_pagato")))
    c = detti_a(111)
    prova("a chi compra si chiede una fattura della cifra RIDOTTA", True,
          "rimborso meno le spese di spedizione" in c
          and SRV._fmt_sats(TOTALE - SPED) in c)
    # LA DECISIONE E' DEFINITIVA, ed e' QUI che conta: l'ordine e' in
    # 'refund' con la disputa segnata, cioe' la forma che la rotta
    # RIAPRE per far ridecidere un rimborso non riuscito. Ma chi vende
    # ha gia' incassato le spese: un «rimborso integrale» adesso
    # farebbe uscire piu' sats di quanti ne sono entrati.
    prima = len(CHIESTE)
    for esito in ("rimborso", "venditore", "reso", "meno_spese"):
        alza(f"a decisione presa e rimborso da fare, «{esito}» si "
             f"rifiuta: e' definitiva",
             lambda e=esito: decidi(oid, e), 400, "definitiva")
    prova("...l'ordine NON e' stato riaperto, e non e' partito niente",
          ("refund", SPED, prima),
          (ordine(oid)["stato"], ordine(oid)["spese_rese_sats"],
           len(CHIESTE)))
    banco.come(111)
    alza("la fattura del TOTALE si rifiuta, e dice quanto e perche'",
         lambda: banco.chiama(SRV.deposita_invoice, oid, None, "", "",
                              corpo={"invoice": fattura("compratore",
                                                        TOTALE)}),
         400, f"{SRV._fmt_sats(TOTALE - SPED)} sats (rimborso meno le spese")
    prova("...senza muovere un sat", [("venditore", SPED)], uscite())
    banco.chiama(SRV.deposita_invoice, oid, None, "", "",
                 corpo={"invoice": fattura("compratore", TOTALE - SPED)})
    prova("con la fattura giusta il rimborso parte", "refunded",
          ordine(oid)["stato"])
    prova("...e le uscite fanno il deposito, non un sat di piu'", TOTALE,
          somma_uscite())
    metodi()


def scena_nodo_rifiuta_uno(aid):
    print("\n── 4. IL NODO RIFIUTA UNO DEI DUE PAGAMENTI ──")
    ESITO["compratore"] = "failed"
    oid = disputa(aid)
    r = decidi(oid)
    o, s = ordine(oid), riga_spese(oid)
    prova("il pagamento a chi vende parte lo stesso", "riscosso", s["stato"])
    prova("...quello a chi compra NO: l'ordine non e' chiuso", True,
          o["stato"] != "refunded" and not r.get("compratore_pagato"))
    prova("...ed e' uscita la sola quota di chi vende", SPED, somma_uscite())
    prova("l'ordine resta in 'refund', col rimborso in attesa del giro "
          "dei pagamenti", ("refund", "da_riprovare", "compratore"),
          (o["stato"], o["payout_stato"], o["payout_verso"]))
    c = detti_a(111)
    prova("...e a chi compra si dice la cifra RIDOTTA, e che ci "
          "riproviamo noi", (True, False, True),
          (SRV._fmt_sats(TOTALE - SPED) in c, SRV._fmt_sats(TOTALE) in c,
           "ci riproviamo noi" in c))
    alza("...e nel frattempo la decisione non si cambia",
         lambda: decidi(oid, "rimborso"), 400, "definitiva")
    ESITO.clear()
    # nessuno tocca niente: e' il giro dei pagamenti a riprovare, con
    # una fattura nuova chiesta al wallet di chi compra
    giro_sospesi()
    prova("al giro dopo, chi compra viene rimborsato", "refunded",
          ordine(oid)["stato"])
    prova("...e chi vende NON e' stato pagato una seconda volta",
          [("compratore", TOTALE - SPED), ("venditore", SPED)],
          sorted(uscite()))


def scena_nodo_rifiuta_chi_vende(aid):
    print("\n── 4b. IL NODO RIFIUTA LA META' DI CHI VENDE ──")
    ESITO["venditore"] = "failed"
    oid = disputa(aid)
    r = decidi(oid)
    o, s = ordine(oid), riga_spese(oid)
    prova("chi compra e' rimborsato lo stesso, della cifra ridotta",
          ("refunded", [("compratore", TOTALE - SPED)]),
          (o["stato"], uscite()))
    prova("la meta' di chi vende NON e' uscita, e la rotta lo dice",
          ("da_riscuotere", False),
          (s["stato"], r.get("venditore_pagato")))
    ESITO.clear()
    banco.come(222)
    banco.chiama(SRV.deposita_invoice_rimborso, s["id"], None, "", "",
                 corpo={"invoice": fattura("venditore", SPED)})
    prova("con una fattura sua, chi vende la incassa", "riscosso",
          riga_spese(oid)["stato"])
    prova("...e chi compra NON e' stato rimborsato una seconda volta",
          [("compratore", TOTALE - SPED), ("venditore", SPED)],
          sorted(uscite()))


def scena_indirizzo_salvato_dopo(aid):
    print("\n── 4c. CHI VENDE SALVA L'INDIRIZZO LIGHTNING DOPO ──")
    metodi(venditore="")
    oid = disputa(aid)
    decidi(oid)
    prova("senza un metodo la sua meta' aspetta", "da_riscuotere",
          riga_spese(oid)["stato"])
    banco.DETTO.clear()
    banco.come(222)
    r = banco.chiama(SRV.salva_ln_address, None, "", "",
                     corpo={"ln_address": A_VENDE})
    prova("salvato l'indirizzo dal Profilo, le spese partono da sole",
          ("riscosso", 1),
          (riga_spese(oid)["stato"], r.get("incassi_sbloccati")))
    v = detti_a(222)
    prova("...e gli si dice che sono spese di spedizione, non il "
          "rimborso di un'asta", (True, False),
          ("Spese di spedizione incassate" in v, "asta" in v.lower()))
    prova("...e le uscite fanno il deposito",
          [("compratore", TOTALE - SPED), ("venditore", SPED)],
          sorted(uscite()))
    metodi()


def scena_corse(aid):
    print("\n── 4d. LE CORSE: DUE GESTI NELLO STESSO ISTANTE ──")
    # (a) UN RIMBORSO PIENO E' GIA' PARTITO (un «reso ricevuto», un
    # altro moderatore) e si e' fermato a chiedere la fattura al wallet
    # di chi compra: ha gia' letto la cifra, il TOTALE. La decisione
    # «meno le spese» arriva adesso: deve ASPETTARE che quel giro
    # finisca, e poi rifiutarsi — o uscirebbero il totale E le spese.
    oid = disputa(aid)
    vera = SRV.invoice_da_ln_address

    async def corsa():
        via = asyncio.Event()

        async def lenta(addr, sats):
            await via.wait()
            return await vera(addr, sats)

        SRV.invoice_da_ln_address = lenta
        try:
            t1 = asyncio.ensure_future(SRV._rimborsa_compratore(oid))
            for _ in range(5):
                await asyncio.sleep(0)
            t2 = asyncio.ensure_future(SRV._rimborsa_meno_spese(oid))
            await asyncio.sleep(0.2)
            fermo = not t2.done()
            via.set()
            r1 = await t1
            try:
                r2 = await t2
            except SRV.HTTPException as e:
                r2 = e.status_code
            return fermo, r1.get("stato"), r2
        finally:
            SRV.invoice_da_ln_address = vera

    fermo, s1, r2 = asyncio.run(corsa())
    prova("la decisione ASPETTA il rimborso pieno gia' partito", True,
          fermo)
    prova("...che finisce: chi compra ha il TOTALE", ("refunded", TOTALE),
          (s1, somma_uscite()))
    prova("...e la decisione arrivata dopo si rifiuta (409), senza "
          "scrivere niente", (409, 0, 0),
          (r2, ordine(oid)["spese_rese_sats"] or 0, n_righe_spese(oid)))
    prova("...una sola uscita, a chi compra: mai piu' del deposito",
          [("compratore", TOTALE)], uscite())

    # (b) LA CINTURA: a decisione presa e pagamenti ancora fermi (nodo
    # muto) l'ordine e' ancora 'dispute'. Chi provasse a dare il netto
    # al venditore — un altro moderatore che aveva la riga di prima —
    # non deve far uscire niente.
    oid = disputa(aid)
    banco.NODO["codice"] = 520
    decidi(oid)
    banco.NODO["codice"] = 200
    prima = len(CHIESTE)
    r = asyncio.run(SRV._sblocca_sats(oid))
    prova("a decisione presa, il netto intero al venditore NON parte",
          (False, True, prima),
          (r.get("ok"), r.get("meno_spese"), len(CHIESTE)))
    prova("...e l'ordine non si e' mosso", "released" != ordine(oid)["stato"],
          True)
    giro_sospesi()
    giro_sospesi()
    prova("poi il giro dei pagamenti fa uscire le due meta', e basta",
          ("refunded", "riscosso",
           [("compratore", TOTALE - SPED), ("venditore", SPED)]),
          (ordine(oid)["stato"], riga_spese(oid)["stato"], sorted(uscite())))


def scena_nodo_muto(aid):
    print("\n── 5. IL NODO E' MUTO ──")
    oid = disputa(aid)
    banco.NODO["codice"] = 520
    r = decidi(oid)
    o, s = ordine(oid), riga_spese(oid)
    prova("nessun sat si e' mosso", [], CHIESTE)
    prova("la decisione pero' E' scritta: cifra e riga ci sono",
          (SPED, SPED), (o["spese_rese_sats"], s["importo_sats"]))
    prova("...tutt'e due in attesa del giro, ognuna col suo verso",
          ("da_riprovare", "compratore", "da_riprovare", "da_riscuotere"),
          (o["payout_stato"], o["payout_verso"], s["payout_stato"],
           s["stato"]))
    prova("...e l'ordine non e' stato chiuso a parole", True,
          o["stato"] in ("dispute", "refund"))
    prova("nessuno ha ricevuto un «sono in arrivo»", False,
          "in arrivo" in detti_a(111) + detti_a(222)
          or "incassate" in detti_a(222))
    alza("...e a decisione presa non si ridecide, nemmeno a nodo muto",
         lambda: decidi(oid, "rimborso"), 400, "definitiva")
    banco.NODO["codice"] = 200
    giro_sospesi()
    giro_sospesi()
    o, s = ordine(oid), riga_spese(oid)
    prova("tornato il nodo, il giro dei pagamenti li fa partire tutti e "
          "due", ("refunded", "riscosso"), (o["stato"], s["stato"]))
    prova("...una volta sola ciascuno, e fanno il deposito",
          [("compratore", TOTALE - SPED), ("venditore", SPED)],
          sorted(uscite()))


def scena_caduta(aid):
    print("\n── 6. IL SERVER CADE A META', E RIPARTE ──")
    vero_c, vero_v = SRV._rimborsa_compratore, SRV._paga_rimborso

    async def muore(*a, **k):
        raise Caduta()

    # (a) cade DOPO la decisione e PRIMA di ogni pagamento
    oid = disputa(aid)
    SRV._rimborsa_compratore = muore
    try:
        decidi(oid)
        caduto = False
    except Caduta:
        caduto = True
    SRV._rimborsa_compratore = vero_c
    o, s = ordine(oid), riga_spese(oid)
    prova("il processo e' morto a meta' della decisione", True, caduto)
    prova("...ma la decisione era GIA' scritta, tutta insieme",
          (SPED, SPED, "da_riscuotere"),
          (o["spese_rese_sats"], (s or {}).get("importo_sats"),
           (s or {}).get("stato")))
    prova("...e nessun sat era partito", [], CHIESTE)
    prova("...con tutt'e due le uscite timbrate «da riprovare»",
          ("da_riprovare", "da_riprovare"),
          (o["payout_stato"], (s or {}).get("payout_stato")))
    giro_sospesi()
    giro_sospesi()
    o, s = ordine(oid), riga_spese(oid)
    prova("AL RIAVVIO il giro dei pagamenti riprende tutt'e due",
          ("refunded", "riscosso"), (o["stato"], s["stato"]))
    prova("...due uscite, il deposito, non un sat di piu'",
          ([("compratore", TOTALE - SPED), ("venditore", SPED)], TOTALE),
          (sorted(uscite()), somma_uscite()))

    # (b) cade FRA il primo pagamento e il secondo
    oid = disputa(aid)
    SRV._paga_rimborso = muore
    try:
        decidi(oid)
        caduto = False
    except Caduta:
        caduto = True
    SRV._paga_rimborso = vero_v
    prova("caduto fra i due: chi compra era gia' stato pagato",
          (True, [("compratore", TOTALE - SPED)], "refunded"),
          (caduto, uscite(), ordine(oid)["stato"]))
    giro_sospesi()
    giro_sospesi()
    prova("al riavvio parte la SOLA quota che mancava",
          ("riscosso", [("compratore", TOTALE - SPED), ("venditore", SPED)]),
          (riga_spese(oid)["stato"], sorted(uscite())))

    # (c) una meta' che ESPLODE (un errore, non una caduta) non ferma
    # l'altra
    oid = disputa(aid)

    async def esplode(*a, **k):
        raise RuntimeError("guasto di cartone")

    SRV._rimborsa_compratore = esplode
    r = decidi(oid)
    SRV._rimborsa_compratore = vero_c
    prova("una meta' che esplode NON ferma l'altra: chi vende incassa",
          ("riscosso", [("venditore", SPED)], False),
          (riga_spese(oid)["stato"], uscite(), r.get("compratore_pagato")))
    giro_sospesi()
    giro_sospesi()
    prova("...e quella esplosa la riprende il giro", ("refunded", TOTALE),
          (ordine(oid)["stato"], somma_uscite()))


def scena_dove_vale(aid, aid_mano):
    print("\n── 8. DOVE IL BOTTONE VALE, E DOVE NO ──")
    # spedizione inclusa nel prezzo (o gratuita): niente da trattenere
    oid = disputa(aid)
    db_esegui("UPDATE ordini SET spedizione_sats=0 WHERE id=?", oid)
    alza("spedizione inclusa o gratuita: si rifiuta",
         lambda: decidi(oid), 400, "non c'è una spesa di spedizione")
    prova("...e non si scrive niente", (0, 0),
          (ordine(oid)["spese_rese_sats"], n_righe_spese(oid)))
    # spese uguali o piu' grandi del totale: niente rimborso a zero
    for sped, come in ((TOTALE, "UGUALI al totale"),
                       (TOTALE + 1, "PIU' GRANDI del totale")):
        db_esegui("UPDATE ordini SET spedizione_sats=? WHERE id=?", sped, oid)
        alza(f"spese {come}: si rifiuta (niente rimborso a zero o "
             f"negativo)", lambda: decidi(oid), 400,
             "non c'è una spesa di spedizione")
    prova("...senza muovere un sat ne' scrivere una riga", ([], 0),
          (CHIESTE, n_righe_spese(oid)))
    db_esegui("UPDATE ordini SET spedizione_sats=? WHERE id=?",
              TOTALE - 1, oid)
    r = decidi(oid)
    prova("...mentre un sat sotto il totale passa: a chi compra torna 1 "
          "sat", [("compratore", 1), ("venditore", TOTALE - 1)],
          sorted(uscite()))
    # il ritiro in zona non ha una spedizione
    banco.come(111)
    c = banco.chiama(SRV.compra, None, corpo={"annuncio_id": aid_mano,
                                              "quantita": 1,
                                              "consegna": "ritiro"})
    oid_r = c["ordine_id"]
    banco.chiama(SRV._incassa_ordine, oid_r)
    banco.come(111)
    banco.chiama(SRV.apri_disputa, oid_r, "", "")
    alza("ritiro in zona: si rifiuta", lambda: decidi(oid_r), 400,
         "non c'è una spesa di spedizione")
    # il punto di ritiro: vale (e' il caso dell'ordine 213)
    oid_p = disputa(aid, {"consegna": "spedizione", "spedizione_via": "punto",
                          "tipo_punto": "locker",
                          "punto_ritiro": "Locker InPost Via Verdi 3"})
    decidi(oid_p)
    prova("verso un punto di ritiro VALE (il punto sbagliato, il 213)",
          ("refunded", 1, TOTALE),
          (ordine(oid_p)["stato"], ordine(oid_p)["via_punto"],
           somma_uscite()))
    # il reso in corso: vale
    oid_x = disputa(aid)
    decidi(oid_x, "reso")
    prova("(il reso e' deciso: l'ordine aspetta il pacco di ritorno)",
          "return_pending", ordine(oid_x)["stato"])
    CHIESTE.clear()
    decidi(oid_x)
    prova("dal reso incagliato VALE", ("refunded", TOTALE),
          (ordine(oid_x)["stato"], somma_uscite()))
    # un caso gia' deciso e incagliato: no
    oid_c = disputa(aid)
    db_esegui("UPDATE ordini SET stato='confirmed' WHERE id=?", oid_c)
    alza("da un caso gia' deciso e incagliato NON vale",
         lambda: decidi(oid_c), 400, "disputa aperta o su un reso")
    prova("...e l'ordine non e' stato riaperto per provarci",
          ("confirmed", 0),
          (ordine(oid_c)["stato"], ordine(oid_c)["spese_rese_sats"]))
    # un esito che non esiste
    alza("un esito inventato si rifiuta", lambda: decidi(oid_c, "meta'"),
         400, "non valido")
    # e chi non modera non decide
    banco.come(222)
    try:
        banco.chiama(SRV.risolvi_disputa, oid_c, None, "", "",
                     corpo={"esito": "meno_spese"})
        cod = 200
    except Exception as e:
        cod = getattr(e, "status_code", None)
    prova("chi non e' moderatore non decide", 403, cod)


def scena_reputazione(aid):
    print("\n── 10. LA REPUTAZIONE ──")

    def perse(tg):
        con = SRV.db()
        d = SRV._dati_distintivi(con, tg)
        con.close()
        return d["dispute_perse"]

    prima_v, prima_c = perse(222), perse(111)
    oid = disputa(aid)
    decidi(oid)
    prova("«meno le spese» non e' una disputa persa per chi vende",
          prima_v, perse(222))
    prova("...ne' per chi compra", prima_c, perse(111))
    oid2 = disputa(aid)
    decidi(oid2, "rimborso")
    prova("(il controllo: il rimborso INTEGRALE invece si conta, per chi "
          "vende)", prima_v + 1, perse(222))


def scena_libro_mastro(aid):
    print("\n── 11. IL LIBRO MASTRO ──")
    oid = disputa(aid)
    decidi(oid)
    NOMI = ("spese rese senza la loro riga",
            "riga di spese senza il suo ordine", "spese rese fuori scala",
            "cinture d'idempotenza cadute", "cassa dell'asta chiusa",
            "puntata chiusa senza rimborso", "doppio rimborso da ritiro")

    def parlano(testo):
        return [n for n in NOMI if n in testo]

    prova("sul sano, dopo tutte le scene, i controlli del cantiere "
          "TACCIONO — e quelli delle aste pure", [], parlano(ronda()))
    s = riga_spese(oid)
    db_esegui("UPDATE rimborsi_asta SET importo_sats=importo_sats+1 "
              "WHERE id=?", s["id"])
    prova("la riga con una cifra diversa dall'ordine: parlano tutt'e due "
          "i versi", ["spese rese senza la loro riga",
                      "riga di spese senza il suo ordine"],
          parlano(ronda()))
    db_esegui("UPDATE rimborsi_asta SET importo_sats=? WHERE id=?",
              SPED, s["id"])
    db_esegui("DELETE FROM rimborsi_asta WHERE id=?", s["id"])
    prova("la riga sparita: i sats di chi vende sarebbero fermi e "
          "invisibili", ["spese rese senza la loro riga"], parlano(ronda()))
    con = SRV.db()
    con.execute(
        "INSERT INTO rimborsi_asta(annuncio_id, tg_id, puntata_id, "
        "importo_sats, motivo, stato, ordine_id, cassaforte, creato, "
        "aggiornato) VALUES(0,222,0,?,'spese_spedizione','riscosso',?,"
        "?,1,1)", (SPED, oid, s["cassaforte"]))
    con.commit()
    con.close()
    prova("(rimessa la riga, torna il silenzio)", [], parlano(ronda()))
    db_esegui("UPDATE ordini SET spese_rese_sats=prezzo_sats WHERE id=?", oid)
    prova("spese uguali al totale: fuori scala (e la riga non combacia "
          "piu')", True, "spese rese fuori scala" in parlano(ronda()))
    db_esegui("UPDATE ordini SET spese_rese_sats=? WHERE id=?", SPED, oid)
    db_esegui("UPDATE ordini SET stato='released' WHERE id=?", oid)
    prova("spese trattenute su un ordine chiuso a favore di chi vende: "
          "fuori scala", ["spese rese fuori scala"], parlano(ronda()))
    db_esegui("UPDATE ordini SET stato='refunded' WHERE id=?", oid)
    # la cintura: due righe di spese per lo stesso ordine non entrano
    try:
        db_esegui(
            "INSERT INTO rimborsi_asta(annuncio_id, tg_id, puntata_id, "
            "importo_sats, motivo, stato, ordine_id, creato, aggiornato) "
            "VALUES(0,222,0,?,'spese_spedizione','da_riscuotere',?,1,1)",
            SPED, oid)
        doppia = True
    except Exception:
        doppia = False
    prova("una SECONDA riga di spese sullo stesso ordine non entra (la "
          "cintura)", False, doppia)
    # e gli hash dei rimborsi non contano la quota di chi vende
    con = SRV.db()
    hs = SRV.hash_rimborsi(con)
    spese_h = {str(r[0]).lower() for r in con.execute(
        "SELECT t.hash FROM payout_tentati t JOIN rimborsi_asta x ON "
        "x.id=t.riga_id WHERE t.tabella='rimborsi_asta' AND "
        "x.motivo='spese_spedizione' AND t.hash!=''")}
    con.close()
    prova("fra gli hash dei RIMBORSI la quota di chi vende non c'e' (e' "
          "un incasso)", (True, set()), (bool(spese_h), hs & spese_h))


def scena_lista_ordini(aid):
    print("\n── COSA ARRIVA ALLA PAGINA ──")
    metodi(venditore="")
    oid = disputa(aid)
    decidi(oid)
    rid = riga_spese(oid)["id"]

    def mio(tg, admin=False):
        banco.come(tg, admin=admin)
        return {r["id"]: r for r in SRV.miei_ordini(0, "", "")}.get(oid, {})

    v = mio(222)
    prova("chi vende riceve la sua riga, col suo id e il suo stato",
          (SPED, rid, "da_riscuotere"),
          (v.get("spese_rese_sats"), v.get("spese_riga_id"),
           v.get("spese_riga_stato")))
    c = mio(111)
    prova("chi compra riceve la cifra trattenuta, ma non la riga",
          (SPED, False, False),
          (c.get("spese_rese_sats"), "spese_riga_id" in c,
           "spese_riga_stato" in c))
    a = db_uno("SELECT stato FROM ordini WHERE id=?", oid)["stato"]
    prova("(l'ordine e' chiuso: il moderatore lo vede finche' e' suo)",
          "refunded", a)
    metodi()


def main():
    print("=" * 66)
    print("  IL RIMBORSO MENO LE SPESE DI SPEDIZIONE — il giro vero")
    print("=" * 66)
    avvio()
    aid, aid_mano = semina()
    oid = scena_tutto_bene(aid)
    scena_definitiva(oid)
    scena_venditore_senza_metodo(aid)
    scena_compratore_senza_metodo(aid)
    scena_nodo_rifiuta_uno(aid)
    scena_nodo_rifiuta_chi_vende(aid)
    scena_indirizzo_salvato_dopo(aid)
    scena_corse(aid)
    scena_nodo_muto(aid)
    scena_caduta(aid)
    scena_dove_vale(aid, aid_mano)
    scena_lista_ordini(aid)
    scena_reputazione(aid)
    scena_libro_mastro(aid)
    print("\n" + "=" * 66)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 66)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
