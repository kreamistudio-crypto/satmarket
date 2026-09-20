# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLO STADIO «IN PAGAMENTO» (set 2026).

Fra la conferma di chi compra e i sats arrivati a chi vende c'e' un
tempo che non vedeva nessuno: l'ordine restava 'shipped' e poi saltava a
'released'. In mezzo, un guasto NOSTRO (LNbits muta, il ponte giu', il
nodo giu') sembrava colpa loro — e chi aveva gia' confermato aveva
ancora davanti «libera i sats» e «apri disputa».

`prove.py` fa girare le funzioni estratte in un mondo di cartone. Qui
gira il SERVER VERO — il modulo intero, col suo schema (la tabella
`payout_passi` nasce da `init_db`, non da un DDL ricopiato), le sue
rotte e i suoi due giri dell'orologio — su un database usa-e-getta. Di
finto c'e' SOLO il nodo, quello di `collaudo_lnbits_muto.py`.

  1. il pagamento resta IN VOLO: la lista degli ordini porta lo stadio a
     tutt'e due le parti, la conferma non si ripete, la disputa non si
     apre, il sollecito non parte; saldato, la ronda chiude e la linea
     del tempo resta come storia;
  2. IL NODO GIU' PER UN'ORA: la conferma passa, LNbits non sente
     niente, la fattura incollata resta buona; in un'ora si ribussa a
     1, 6, 21 e 51 minuti, a compratore e venditore non arriva una
     parola in piu'; tornato il nodo, il payout parte DA SOLO con la
     stessa fattura;
  3. il battito corto: a mercatino tranquillo non fa niente, con una
     riga di turno la riprende da solo;
  4. chi modera vede LO STESSO stadio nella coda dei 🧊;
  5. il promemoria degli incassi tace mentre la palla e' nostra;
  6. il TIMER non ripassa su un ordine gia' confermato da una persona
     (e sul gemello mai confermato scatta: la prova non e' vuota).

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_in_pagamento.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
GIORNO = 86400


def main():
    print("=" * 58)
    print("  LO STADIO «IN PAGAMENTO» — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    a1, a2, a3, a4 = banco.semina()
    adesso = int(time.time())
    dovuti = 50_000

    def rifiuto(fn, *args, corpo=None):
        try:
            return banco.chiama(fn, *args, corpo=corpo)
        except SRV.HTTPException as e:
            return e

    def esegui(sql, *par):
        con = SRV.db()
        con.execute(sql, par)
        con.commit()
        con.close()

    def leggi(sql, *par):
        con = SRV.db()
        r = con.execute(sql, par).fetchall()
        con.close()
        return [tuple(x) for x in r]

    def passa_il_tempo(secondi):
        esegui("UPDATE payout_passi SET quando=quando-?, ultimo=ultimo-?",
               secondi, secondi)
        esegui("UPDATE payout_tentati SET quando=quando-?", secondi)
        esegui("UPDATE ordini SET payout_ultimo=payout_ultimo-? "
               "WHERE payout_ultimo>0", secondi)

    def stadio(oid, chi):
        banco.come(chi)
        for o in SRV.miei_ordini(0, "", ""):
            if o["id"] == oid:
                return o.get("pagamento")
        return None

    def passi(oid):
        return leggi("SELECT passo, motivo, volte FROM payout_passi WHERE "
                     "tabella='ordini' AND riga_id=? ORDER BY id", oid)

    def fattura(secondi_fa=5):
        return bolt11_finta(dovuti, 31 * GIORNO, adesso - secondi_fa)

    def ordine_con_fattura(annuncio, bolt11):
        oid = banco.ordine_pagato(annuncio)
        banco.come(222)
        banco.chiama(SRV.deposita_invoice, oid, None,
                     corpo={"invoice": bolt11})
        return oid

    # ---- 0) lo schema vero ---------------------------------------
    print("\n[lo schema]")
    prova("la tabella dei passi nasce da init_db", 1, len(leggi(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND "
        "name='payout_passi'")))

    # ---- 1) in volo: lo stadio, e la conferma definitiva ----------
    print("\n[il pagamento resta in volo]")
    f1 = fattura()
    oid = ordine_con_fattura(a1, f1)
    prova("prima della conferma non c'e' nessuno stadio", (None, None),
          (stadio(oid, 111), stadio(oid, 222)))
    banco.NODO["esito"] = "pending"
    banco.DETTO.clear(); banco.AVVISI.clear(); banco.USCITE.clear()
    banco.come(111)
    esito = banco.chiama(SRV.conferma_ricezione, oid, None)
    dopo = banco.riga(oid)
    prova("confermato, e il payout resta in volo: lo stato NON cambia",
          ("locked", "in_volo", "venditore"),
          (dopo["stato"], dopo["payout_stato"], dopo["payout_verso"]))
    prova("la risposta dice al client di rileggere", True,
          bool(esito.get("in_volo")))
    for chi, nome in ((111, "chi compra"), (222, "chi vende")):
        s = stadio(oid, chi) or {}
        prova(f"{nome} legge lo stadio: in volo, via lightning",
              ("in_volo", "lightning", "conferma", False, False),
              (s.get("passo"), s.get("via"), s.get("deciso_da"),
               s.get("gesto_venditore"), s.get("lungo")))
        prova("...con la linea del tempo: deciso, partito, in volo",
              ["deciso", "partito", "in_volo"],
              [x["passo"] for x in s.get("linea", [])])
        prova("...e quanti sats stanno arrivando", dovuti, s.get("sats"))
    prova("a chi compra: «ci pensa Barattolo», una volta", 1, sum(
        1 for c, t in banco.DETTO if c == 111 and "ci pensa Barattolo" in t))
    prova("a chi vende: «sono in arrivo», una volta", 1, sum(
        1 for c, t in banco.DETTO if c == 222 and "sono in arrivo.</b>" in t))
    banco.come(111)
    e = rifiuto(SRV.conferma_ricezione, oid, None)
    prova("la conferma non si ripete: 409", 409,
          getattr(e, "status_code", None))
    e = rifiuto(SRV.apri_disputa, oid, None)
    prova("...e non si annulla con una disputa: 409, con le sue parole",
          (409, True),
          (getattr(e, "status_code", None),
           "la conferma è definitiva" in str(getattr(e, "detail", ""))))
    prova("...l'ordine non e' andato in disputa", "locked",
          banco.riga(oid)["stato"])
    prova("un solo pagamento e' partito", 1, len(banco.USCITE))
    # il nodo salda: la ronda chiude da sola
    banco.PAGAMENTI[banco._hash_di(f1)] = "success"
    banco.NODO["esito"] = "success"
    asyncio.run(SRV.risolvi_pagamenti_in_volo(solo_in_volo=True))
    prova("saldato: il battito corto chiude da solo", "released",
          banco.riga(oid)["stato"])
    prova("chi vende sente «Arrivati ✓»", 1, sum(
        1 for c, t in banco.DETTO if c == 222 and "Arrivati ✓" in t))
    s = stadio(oid, 222) or {}
    prova("lo stadio resta come storia",
          ("arrivato", ["deciso", "partito", "in_volo", "arrivato"]),
          (s.get("passo"), [x["passo"] for x in s.get("linea", [])]))

    # ---- 2) il nodo giu' per un'ora --------------------------------
    print("\n[il nodo giu' per un'ora]")
    # la cassaforte del nodo esiste solo con le sue tre righe: si
    # montano a mano sul modulo, di cartone (nessuna chiave in un file)
    for nome, valore in (("LNBITS_NODO_URL", "http://127.0.0.1:2"),
                         ("LNBITS_NODO_INVOICE_KEY", "cartone-che-legge"),
                         ("LNBITS_NODO_ADMIN_KEY", "cartone-che-paga")):
        setattr(SRV, nome, valore)
    f2 = fattura(6)
    oid2 = ordine_con_fattura(a2, f2)
    esegui("UPDATE ordini SET cassaforte='nodo' WHERE id=?", oid2)
    SRV._ponte["stato"] = "giu"
    banco.DETTO.clear(); banco.AVVISI.clear(); banco.USCITE.clear()
    banco.PAGAMENTI.clear()
    banco.come(111)
    esito = banco.chiama(SRV.conferma_ricezione, oid2, None)
    dopo = banco.riga(oid2)
    prova("ponte giu': la conferma passa, e a LNbits non si chiede di pagare",
          (True, 0, {}),
          (bool(esito.get("non_chiesto")), len(banco.USCITE),
           banco.PAGAMENTI))
    prova("...la fattura incollata resta al suo posto",
          (f2, "da_riprovare", ""),
          (dopo["invoice_venditore"], dopo["payout_stato"],
           dopo["payout_hash"] or ""))
    prova("...e le due parti sentono solo che ci pensiamo noi", 2,
          len(banco.DETTO))
    s = stadio(oid2, 222) or {}
    prova("chi vende legge: riparte da solo, guasto NOSTRO, nessun gesto",
          ("riparte", "ponte", True, False),
          (s.get("passo"), s.get("motivo"), s.get("nostro"),
           s.get("gesto_venditore")))
    bussate = []
    for minuto in range(1, 61):
        passa_il_tempo(60)
        prima = passi(oid2)[-1][2]
        asyncio.run(SRV.riprova_pagamenti_sospesi())
        if passi(oid2)[-1][2] > prima:
            bussate.append(minuto)
    prova("in un'ora si ribussa a 1, 6, 21 e 51 minuti", [1, 6, 21, 51],
          bussate)
    prova("...LNbits non ha sentito niente, la fattura e' ancora buona",
          (0, {}), (len(banco.USCITE), banco.PAGAMENTI))
    prova("...e a compratore e venditore nemmeno una parola in piu'", 2,
          len(banco.DETTO))
    prova("...un'ora di guasto e' UNA riga: «5 volte»",
          [("deciso", "conferma", 1), ("guasto_nostro", "ponte", 5)],
          passi(oid2))
    prova("dopo un'ora: «ci stiamo lavorando»", True,
          (stadio(oid2, 111) or {}).get("lungo"))
    SRV._ponte["stato"] = "ok"
    passa_il_tempo(3600)
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    dopo = banco.riga(oid2)
    prova("tornato il nodo, il payout parte DA SOLO e arriva",
          ("released", "uscito", 1),
          (dopo["stato"], dopo["payout_stato"], len(banco.USCITE)))
    prova("...con la stessa fattura di un'ora prima", "success",
          banco.PAGAMENTI.get(banco._hash_di(f2)))
    prova("...e chi vende sente «Arrivati ✓»: il suo secondo messaggio",
          (1, 2), (sum(1 for c, t in banco.DETTO
                       if c == 222 and "Arrivati ✓" in t),
                   sum(1 for c, _ in banco.DETTO if c == 222)))

    # ---- 3) il battito corto ---------------------------------------
    print("\n[il battito da un minuto]")
    prova("a mercatino tranquillo non c'e' niente da guardare", False,
          SRV._pagamenti_da_guardare())
    f3 = fattura(7)
    oid3 = ordine_con_fattura(a3, f3)
    banco.NODO["codice"] = 520          # LNbits muta: non si puo' chiedere
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid3, None)
    banco.NODO["codice"] = 200
    prova("LNbits muta: sospeso, e il battito ha qualcosa da guardare",
          ("da_riprovare", True),
          (banco.riga(oid3)["payout_stato"], SRV._pagamenti_da_guardare()))
    prova("...il passo dice di chi e' il guasto",
          ("guasto_nostro", "lnbits_muto", 1), passi(oid3)[-1])
    passa_il_tempo(61)
    SRV.BATTITO_PAGAMENTI_S = 0

    async def un_battito():
        try:
            await asyncio.wait_for(SRV.orologio_pagamenti(), timeout=1.5)
        except asyncio.TimeoutError:
            pass
    asyncio.run(un_battito())
    prova("un minuto dopo il battito corto la riprende DA SOLO", "released",
          banco.riga(oid3)["stato"])

    # ---- 4) chi modera vede lo stesso stadio -----------------------
    print("\n[il pannello dei moderatori]")
    f4 = fattura(8)
    oid4 = ordine_con_fattura(a4, f4)
    banco.NODO["esito"] = "pending"
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid4, None)
    passa_il_tempo(SRV.IN_VOLO_LIMITE_S + 60)
    banco.AVVISI.clear()
    asyncio.run(SRV.risolvi_pagamenti_in_volo())
    prova("mezz'ora in volo: 'incerto', e il 🧊 di sempre — UNO",
          ("incerto", 1),
          (banco.riga(oid4)["payout_stato"],
           sum(1 for x in banco.AVVISI if "verificare a mano" in x)))
    banco.come(999, admin=True)
    coda = [r for r in SRV.coda_pagamenti("", "") if r["id"] == oid4]
    s = (coda[0].get("pagamento") if coda else None) or {}
    prova("la coda dei 🧊 porta lo STESSO stadio: in verifica, lungo",
          ("in_verifica", True, "in_verifica"),
          (s.get("passo"), s.get("lungo"),
           (s.get("linea") or [{}])[-1].get("passo")))
    prova("...ed e' quello che leggono le due parti", s.get("passo"),
          (stadio(oid4, 111) or {}).get("passo"))
    banco.NODO["esito"] = "success"

    # ---- 5) il promemoria degli incassi tace ------------------------
    print("\n[il promemoria degli incassi]")
    vecchio = adesso - 30 * GIORNO
    esegui("UPDATE ordini SET stato='confirmed', payout_stato='da_riprovare',"
           " payout_verso='venditore', aggiornato=?, sollecito_incasso_il=0, "
           "solleciti_incasso=0 WHERE id=?", vecchio, oid4)
    banco.DETTO.clear()
    asyncio.run(SRV.sollecita_incassi())
    prova("mentre ci riproviamo noi, a chi vende NON si dice «imposta il "
          "tuo address»", 0, len(banco.DETTO))
    esegui("UPDATE ordini SET payout_stato='' WHERE id=?", oid4)
    asyncio.run(SRV.sollecita_incassi())
    prova("...quando la palla e' sua, il promemoria torna", 1, sum(
        1 for c, t in banco.DETTO if c == 222 and "da incassare" in t))

    # ---- 6) il timer non ripassa ---------------------------------
    print("\n[il timer e un ordine gia' in pagamento]")
    un_mese_fa = adesso - 30 * GIORNO
    coppia = []
    for n in (9, 10):
        o = ordine_con_fattura(a1, fattura(n))
        esegui("UPDATE ordini SET stato='delivered', "
               "consegna_scelta='digitale', consegnato=?, spedito_il=? "
               "WHERE id=?", un_mese_fa, un_mese_fa, o)
        coppia.append(o)
    confermato, mai_confermato = coppia
    banco.NODO["codice"] = 520            # LNbits muta: resta sospeso
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, confermato, None)
    banco.NODO["codice"] = 200
    banco.USCITE.clear(); banco.DETTO.clear()
    asyncio.run(SRV.controlla_scadenze())
    uno, due = banco.riga(confermato), banco.riga(mai_confermato)
    prova("il gemello MAI confermato il timer lo chiude (la prova non e' "
          "vuota)", ("released", True),
          (due["stato"], due["sbloccato_auto_il"] > 0))
    prova("l'ordine confermato da una PERSONA il timer non lo tocca",
          ("delivered", "da_riprovare", 0),
          (uno["stato"], uno["payout_stato"], uno["sbloccato_auto_il"]))
    prova("...e non scavalca l'orologio dei ritentativi: un solo pagamento, "
          "quello del gemello", 1, len(banco.USCITE))
    prova("...ne' dice a chi vende che «il tempo è scaduto»", [],
          [t for c, t in banco.DETTO if c == 222 and "scaduto" in t
           and f"#{confermato}" in t])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
