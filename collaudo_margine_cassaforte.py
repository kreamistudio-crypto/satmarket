# -*- coding: utf-8 -*-
"""
IL MARGINE DELLA CASSAFORTE (27 ott 2026, cantiere margine-cassaforte,
decisione di Andrea coi numeri veri del VPS).

LNbits non paga se nel wallet, oltre al pagamento, non resta la sua
riserva per le commissioni di rete (l'1 %, minimo 2 sats): rifiuta con un
520 PRIMA di toccare LND. Sul regtest (26 ott) quel 520 passava per
«ignoto» e «fattura bruciata», e chi vende si sentiva chiedere una
fattura nuova per un guasto NOSTRO. Da oggi la domanda la fa il server,
prima di prendere la mano, con la sola chiave di lettura.

Qui gira il SERVER VERO su un database usa-e-getta, col LNbits di cartone
del banco dei pagamenti (`collaudo_lnbits_muto`), che da oggi dichiara
anche il SALDO del wallet. Le scene:
  1. il saldo copre il pagamento ma non la riserva: NON CHIESTO col motivo
     «riserva», la riga «da riprovare», la fattura al suo posto, nessun
     sat uscito, UN avviso ai moderatori «manca margine nella cassaforte»;
  2. un secondo incasso fermo sullo stesso wallet: nessun secondo avviso
     (uno per cassaforte ogni sei ore);
  3. il giro dei sospesi a saldo ancora corto: niente parte, la riga
     resta, e lo stadio dice «un problema del nostro nodo» (nostro,
     col prossimo tentativo scritto);
  4. il margine rimesso: il giro paga DA SOLO, con la stessa fattura;
  5. il limite al sat: saldo = importo + riserva passa, un sat sotto no;
  6. il wallet che non risponde alla domanda del saldo: si paga come
     ieri (fail-open dichiarato: un LNbits muto lo ferma la chiamata che
     paga);
  7. passate le sei ore, l'avviso torna;
  8. la sesta domanda della guardia (`_voci_margine`) sul server vero:
     una voce per cassaforte configurata, buona/cattiva/non misurata,
     con gli incassi in attesa letti dal database; e la sua frase dentro
     l'avviso della guardia;
  9. il trasloco del SaaS (29 ott 2026): l'ordine spostato sul nodo
     conta sul nodo, e la cassaforte senza doveri che non riceve il
     denaro nuovo non si giudica (niente «⚠️» ne' «❔» sul SaaS chiuso).

NON TOCCA NIENTE DI VERO: il config finto si installa PRIMA dell'import
di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_margine_cassaforte.py
"""
import asyncio
import io
import sqlite3
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
SRV = None


class _Tee(io.TextIOBase):
    def __init__(self, vero):
        self.vero, self.righe = vero, []

    def write(self, s):
        self.righe.append(s)
        return self.vero.write(s)

    def flush(self):
        self.vero.flush()


def passa(secondi: int):
    """Il tempo passa per il ritentativo: la linea del tempo e la riga
    invecchiano di `secondi`."""
    con = SRV.db()
    con.execute("UPDATE payout_passi SET quando=quando-?, ultimo=ultimo-?",
                (secondi, secondi))
    con.execute("UPDATE ordini SET payout_ultimo=payout_ultimo-? "
                "WHERE payout_ultimo>0", (secondi,))
    con.commit()
    con.close()


def stadio(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    r = dict(con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone())
    s = SRV._stadi_ordini(con, [r]).get(oid) or {}
    con.close()
    return {"passo": s.get("passo"), "motivo": s.get("motivo"),
            "nostro": s.get("nostro"), "prossimo": bool(s.get("prossimo"))}


def ordine_confermato(annuncio_id):
    """Un ordine pagato, con la fattura di chi vende gia' in colonna, e la
    conferma di chi compra: da qui il pagamento parte subito."""
    oid = banco.ordine_pagato(annuncio_id)
    banco.fattura_di_ieri(oid, f"lnbc-fattura-{oid}")
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid)
    return oid


def avvisi_margine():
    return [a for a in banco.AVVISI if "Manca margine nella cassaforte" in a]


def primo_avviso():
    """Il primo avviso del margine, o '' se non c'e': un banco che esplode
    su una lista vuota non e' un rosso, e' un buco (la tortura lo sa)."""
    return avvisi_margine()[0] if avvisi_margine() else ""


def main():
    global SRV
    print("=" * 58)
    print("  💧 IL MARGINE DELLA CASSAFORTE")
    print("=" * 58)
    tee = _Tee(sys.stdout)
    sys.stdout = tee
    banco.avvio()
    SRV = banco.SRV
    ids = banco.semina()
    con = SRV.db()
    for n in range(4):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',5,'sats','nuovo')", (f"Cosa in piu' {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    riserva = SRV._riserva_lnbits(50_000)

    print("\n[1. il saldo copre il pagamento ma non la riserva]")
    banco.NODO["saldo"] = 50_000
    o1 = ordine_confermato(ids[0])
    r = banco.riga(o1)
    prova("la riserva che LNbits vuole su 50.000: 500 sats", 500, riserva)
    prova("NON CHIESTO: niente uscito, la riga «da riprovare», la fattura "
          "al suo posto, lo stato di prima (i sats non sono arrivati)",
          ([], "da_riprovare", "lnbc-fattura-1", "locked"),
          (banco.USCITE, r["payout_stato"], r["invoice_venditore"], r["stato"]))
    prova("...il journal lo dice col motivo", True,
          any("manca il margine" in x and f"ordini#{o1}" in x
              for x in "".join(tee.righe).splitlines()))
    prova("...UN avviso ai moderatori: la cassaforte, il saldo, quanto serve",
          (1, True, True, True),
          (len(avvisi_margine()),
           "cassaforte saas" in primo_avviso(),
           "<b>50.000 sats</b>" in primo_avviso(),
           "<b>50.500</b>" in primo_avviso()))
    prova("...e lo stadio: un problema nostro, col prossimo tentativo",
          {"passo": "riparte", "motivo": "riserva", "nostro": True,
           "prossimo": True}, stadio(o1))
    prova("...a chi vende nessuna richiesta di fattura nuova", False,
          any(chi == 222 and "fattura" in t.lower() and "nuova" in t.lower()
              for chi, t in banco.DETTO))

    print("\n[2. un secondo incasso fermo sullo stesso wallet]")
    o2 = ordine_confermato(ids[1])
    prova("niente uscito, riga da riprovare, e NESSUN secondo avviso",
          ([], "da_riprovare", 1),
          (banco.USCITE, banco.riga(o2)["payout_stato"], len(avvisi_margine())))

    print("\n[3. il giro dei sospesi a saldo ancora corto]")
    passa(61)
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    prova("il giro ribussa, il saldo e' ancora corto: niente parte",
          ([], "da_riprovare", "da_riprovare", 1),
          (banco.USCITE, banco.riga(o1)["payout_stato"],
           banco.riga(o2)["payout_stato"], len(avvisi_margine())))

    print("\n[4. il margine rimesso: il giro paga da solo]")
    banco.NODO["saldo"] = 50_000 + riserva
    passa(301)
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    prova("al limite esatto (importo + riserva) si paga: tutt'e due, con la "
          "fattura di sempre",
          (2, "released", "released", "uscito"),
          (len(banco.USCITE), banco.riga(o1)["stato"], banco.riga(o2)["stato"],
           banco.riga(o1)["payout_stato"]))

    print("\n[5. il limite al sat]")
    banco.NODO["saldo"] = 50_000 + riserva - 1
    o3 = ordine_confermato(ids[2])
    prova("un sat sotto il limite: non chiesto", (2, "da_riprovare"),
          (len(banco.USCITE), banco.riga(o3)["payout_stato"]))

    print("\n[6. il wallet che non risponde alla domanda del saldo]")
    banco.NODO["saldo"] = None
    passa(61)
    asyncio.run(SRV.riprova_pagamenti_sospesi())
    prova("saldo non leggibile: si paga come ieri (fail-open dichiarato)",
          (3, "released"), (len(banco.USCITE), banco.riga(o3)["stato"]))

    print("\n[7. passate le sei ore, l'avviso torna]")
    SRV.timbro_scrivi(f"{SRV.TIMBRO_MARGINE}_saas",
                      str(int(time.time()) - SRV.MARGINE_AVVISO_PAUSA_S - 1))
    banco.NODO["saldo"] = 10
    o4 = ordine_confermato(ids[3])
    prova("un nuovo avviso, uno", (2, "da_riprovare"),
          (len(avvisi_margine()), banco.riga(o4)["payout_stato"]))
    prova("...e il pagamento del wallet che risponde 0 non parte", 3,
          len(banco.USCITE))

    print("\n[8. la sesta domanda della guardia, sul server vero]")
    # la cassaforte del banco ha la chiave segnaposto: per la guardia non
    # e' «configurata». Qui il LNbits e' di cartone e la chiave non conta.
    voci0 = asyncio.run(SRV._voci_margine())
    SRV.LNBITS_INVOICE_KEY = "collaudo-usa-e-getta"
    con = SRV.db()
    attese = SRV._incassi_in_attesa(con)
    con.close()
    # in attesa: il #4 (50.000, confermato, fermo); i tre pagati no
    prova("gli incassi in attesa, per cassaforte: un ordine da 50.000 sul saas",
          {"saas": {"n": 1, "sats": 50_000}}, attese)
    prova("...prima, con la chiave segnaposto, la cassaforte non si "
          "contava: nessuna voce", [], voci0)
    soglia = 50_000 * 1 // 100 + 10_000
    banco.NODO["saldo"] = 50_000 + soglia
    voci = asyncio.run(SRV._voci_margine())
    prova("una voce per cassaforte configurata (solo il saas qui), buona al "
          "limite: 500 + 10.000 di soglia",
          [("margine_saas", True)], [(k, e) for k, e, _ in voci])
    prova("...con le parole giuste", True,
          "✅ Margine saas: 10.500 sats (saldo 60.500, 50.000 sats in attesa "
          "su 1 ordine; la soglia è 10.500)." == voci[0][2])
    banco.NODO["saldo"] = 50_000 + soglia - 1
    voci = asyncio.run(SRV._voci_margine())
    prova("un sat sotto: cattiva, e dice cosa fare", (False, True),
          (voci[0][1], "Aggiungi margine alla cassaforte" in voci[0][2]))
    banco.NODO["saldo"] = None
    voci = asyncio.run(SRV._voci_margine())
    prova("saldo non letto: non misurata, ne' allarma ne' rassicura",
          (None, True), (voci[0][1], "non si è potuto leggere" in voci[0][2]))
    banco.NODO["saldo"] = 50_000 + soglia - 1
    voci = asyncio.run(SRV._voci_margine())
    azione, dopo = SRV._liquidita_passo({}, {k for k, e, _ in voci if e is False},
                                        set(), time.time())
    testo = SRV._testo_liquidita(azione, voci, [], {}, time.time())
    prova("nella guardia: la voce cattiva fa l'allarme, e l'avviso la porta",
          ("allarme", ["margine_saas"], True),
          (azione, dopo.get("chiavi"), "⚠️ Margine saas: solo 10.499 sats" in testo))
    SRV.LIQUIDITA_MARGINE_PERCENTO, SRV.LIQUIDITA_MARGINE_MIN_SATS = 0, 0
    prova("con le due leve a 0 la domanda e' spenta", [],
          asyncio.run(SRV._voci_margine()))

    print("\n[9. il trasloco del SaaS: l'ordine spostato conta sul nodo]")
    # (29 ott 2026) le due casseforti configurate, il denaro nuovo sul
    # nodo, e il #4 nato sul saas spostato sul nodo col gesto vero
    # della riga (`cassaforte_payout`): il saas resta senza doveri.
    SRV.LIQUIDITA_MARGINE_PERCENTO, SRV.LIQUIDITA_MARGINE_MIN_SATS = 1, 10_000
    SRV.LNBITS_NODO_URL = SRV.LNBITS_URL
    # le chiavi di cartone nella forma che il controllo dei segreti
    # riconosce («collaudo-usa-e-getta»): scritte «collaudo-nodo-…» la
    # CI le ha prese per chiavi vere (2 nov 2026, promozione rossa)
    SRV.LNBITS_NODO_INVOICE_KEY = "collaudo-usa-e-getta-nodo-lettura"
    SRV.LNBITS_NODO_ADMIN_KEY = "collaudo-usa-e-getta-nodo-paga"
    SRV.CASSAFORTE_NUOVA = True
    banco.NODO["saldo"] = 50_000 + soglia
    voci = asyncio.run(SRV._voci_margine())
    prova("prima dello spostamento: il saas ha il #4 e si giudica, il nodo "
          "riceve il denaro nuovo e si giudica anche senza doveri",
          [("margine_saas", True), ("margine_nodo", True)],
          [(k, e) for k, e, _ in voci])
    con = SRV.db()
    con.execute("UPDATE ordini SET cassaforte_payout='nodo' WHERE id=?", (o4,))
    con.commit()
    attese = SRV._incassi_in_attesa(con)
    con.close()
    prova("dopo: gli incassi in attesa contano il #4 sul nodo, da dove "
          "uscira'", {"nodo": {"n": 1, "sats": 50_000}}, attese)
    banco.NODO["saldo"] = 117
    voci = asyncio.run(SRV._voci_margine())
    prova("...e il saas svuotato (117 sats) non da' piu' «⚠️ Margine saas»: "
          "una voce sola, quella del nodo", ["margine_nodo"],
          [k for k, _, _ in voci])
    banco.NODO["saldo"] = None
    voci = asyncio.run(SRV._voci_margine())
    prova("...ne' «❔» col saas chiuso che non risponde: resta il nodo",
          [("margine_nodo", None)], [(k, e) for k, e, _ in voci])
    SRV.CASSAFORTE_NUOVA = False
    banco.NODO["saldo"] = 50_000 + soglia
    voci = asyncio.run(SRV._voci_margine())
    prova("con la leva girata il saas torna la cassaforte del denaro "
          "nuovo e si giudica di nuovo, anche senza doveri",
          [("margine_saas", True), ("margine_nodo", True)],
          [(k, e) for k, e, _ in voci])

    sys.stdout = tee.vero
    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
