# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI PAGAMENTI CHE NON ARRIVANO (5 ott 2026).

Il caso vero: un acquisto da Phoenix da 56.459 sats e' fallito perche'
l'entrata dei canali ACINQ era scesa a ~29.000, e nessuno ci ha avvisati:
il pagamento muore PRIMA del nostro nodo. Da Barattolo si vede solo la
fattura che scade. Due nella stessa ora = un avviso ai moderatori,
«pagamenti non arrivati, controllare la liquidità», poi sei ore di pausa.

`prove.py` fa girare i pezzi estratti. Qui gira il SERVER VERO — lo
schema con la tabella nuova, il reaper vero dell'orologio
(`controlla_abbandonati`) e la rotta vera degli eventi di mostrod
(`evento_p2p`, col suo segreto) — su un database usa-e-getta. Di finto
c'e' solo LNbits (che dice «non pagata») e Telegram.

  1. mercatino: una fattura morta non avvisa; la seconda nella stessa
     ora si'; la terza no (pausa); un ordine annullato dal compratore
     non conta;
  2. P2P: la garanzia chiesta e mai pagata, poi `expired`, conta; la
     garanzia pagata e poi scaduta no; il ritiro (`canceled`) no; il
     retry di mostrod non conta due volte; un mercatino + un P2P nella
     stessa ora fanno l'avviso;
  3. fail-open: col registro rotto il reaper mette lo stesso le sue
     lapidi e la rotta risponde lo stesso, e le parti sono avvisate.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete, nessuna chiave.

USO:  python collaudo_pagamenti_non_arrivati.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
SEGRETO = "segreto-di-cartone"
CHIAVE_VENDE = "a1" * 32
CHIAVE_COMPRA = "b2" * 32


class Richiesta:
    """La richiesta di mostrod: l'intestazione col segreto e il corpo."""

    def __init__(self, corpo, segreto=SEGRETO):
        self.corpo = corpo
        self.headers = {"authorization": "Bearer " + segreto}

    async def json(self):
        return self.corpo


def main():
    print("=" * 58)
    print("  I PAGAMENTI CHE NON ARRIVANO — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    SRV.P2P_EVENTI_SEGRETO = SEGRETO       # la porta degli eventi aperta

    async def mai_pagata(h, cassaforte=""):
        return False
    SRV.invoice_pagata = mai_pagata

    def con():
        return SRV.db()

    def nuovo_ordine(sats, stato="creato", eta=2000):
        c = con()
        oid = c.execute(
            "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
            "prezzo_sats,stato,payment_hash,invoice,creato,aggiornato,"
            "cassaforte) VALUES(1,111,222,?,?,?,'lnbc1collaudo',?,?,'nodo')",
            (sats, stato, f"hash-{sats}-{time.time()}",
             int(time.time()) - eta, int(time.time()) - eta)).lastrowid
        c.commit()
        c.close()
        return oid

    def stato(oid):
        c = con()
        s = c.execute("SELECT stato FROM ordini WHERE id=?", (oid,)).fetchone()[0]
        c.close()
        return s

    def registro():
        c = con()
        r = [tuple(x) for x in c.execute(
            "SELECT fonte, rif, sats FROM fatture_scadute ORDER BY quando, rif")]
        c.close()
        return r

    def azzera():
        c = con()
        c.execute("DELETE FROM fatture_scadute")
        c.execute("DELETE FROM timbri WHERE nome=?", (SRV.TIMBRO_FATTURE_SCADUTE,))
        c.commit()
        c.close()
        banco.AVVISI.clear()

    def orologio():
        asyncio.run(SRV.controlla_abbandonati())

    # ---- 1) il mercatino -------------------------------------------
    print("\n[1) il mercatino: l'orologio vero]")
    prova("lo schema vero ha la tabella del registro", [],
          registro())
    primo = nuovo_ordine(56459)
    orologio()
    prova("la prima fattura morta: lapide, e al registro coi suoi sats",
          ("annullato", [("mercatino", str(primo), 56459)]),
          (stato(primo), registro()))
    prova("...una sola: nessun avviso", [], banco.AVVISI)
    annullato = nuovo_ordine(30000, stato="annullato")
    viva = nuovo_ordine(40000, eta=60)
    secondo = nuovo_ordine(25000)
    orologio()
    prova("la seconda nella stessa ora: UN avviso ai moderatori", 1,
          len(banco.AVVISI))
    testo = banco.AVVISI[0] if banco.AVVISI else ""
    prova("...con la frase chiesta e i due ordini", True,
          "Pagamenti non arrivati, controllare la liquidità" in testo
          and f"• ordine #{primo}, 56.459 sats" in testo
          and f"• ordine #{secondo}, 25.000 sats" in testo)
    prova("l'ordine annullato dal compratore e quello con la fattura viva "
          "non contano", (False, False, "creato"),
          (f"#{annullato}" in testo, f"#{viva}" in testo, stato(viva)))
    terzo = nuovo_ordine(12000)
    orologio()
    prova("la terza dentro la pausa: registrata, nessun secondo avviso",
          (3, 1), (len(registro()), len(banco.AVVISI)))
    c = con()
    t = c.execute("SELECT quando FROM timbri WHERE nome=?",
                  (SRV.TIMBRO_FATTURE_SCADUTE,)).fetchone()
    c.close()
    prova("il timbro della pausa sta nel database (sopravvive al deploy)",
          True, t is not None and abs(int(t[0]) - time.time()) < 60)
    prova("lapidi come sempre", "annullato", stato(terzo))

    # ---- 2) il P2P: la rotta vera degli eventi ----------------------
    print("\n[2) il P2P: la garanzia chiesta e mai pagata]")
    azzera()

    def evento(ordine, azione, ts, attore="mostro", dettaglio=None,
               segreto=SEGRETO):
        corpo = {"v": 1, "order": ordine, "action": azione, "ts": ts,
                 "buyer": CHIAVE_COMPRA, "seller": CHIAVE_VENDE,
                 "actor": attore, "detail": dettaglio}

        async def giro():
            r = await SRV.evento_p2p(Richiesta(corpo, segreto))
            # la rotta lancia i suoi avvisi in task: si aspettano qui,
            # o asyncio.run li cancellerebbe uscendo
            await asyncio.gather(*list(SRV._TASK_EVENTI_P2P),
                                 return_exceptions=True)
            return r
        try:
            r = asyncio.run(giro())
        except Exception as e:
            return getattr(e, "status_code", type(e).__name__)
        import json
        return json.loads(r.body)

    t0 = int(time.time()) - 600
    MORTA = "5a1e0000-1111-4a2b-9c3d-000000000001"
    PAGATA = "5a1e0000-2222-4a2b-9c3d-000000000002"
    RITIRATA = "5a1e0000-3333-4a2b-9c3d-000000000003"
    c = con()
    c.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
              "sats) VALUES(?,111,?,'in-progress','sell',1,7300)", (MORTA, t0))
    # le due parti, cosi' la rotta ha qualcuno da avvisare (il punto 3)
    for chiave, tg in ((CHIAVE_VENDE, 222), (CHIAVE_COMPRA, 111)):
        c.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                  "VALUES(?,?,?)", (chiave, tg, t0))
    c.commit()
    c.close()

    evento(MORTA, "taken", t0, attore="buyer")
    evento(MORTA, "hold-invoice-requested", t0 + 5)
    r = evento(MORTA, "expired", t0 + 900, dettaglio="maker-timeout")
    prova("la garanzia mai pagata, poi expired: la rotta risponde come sempre",
          {"ok": True, "nuovo": True}, r)
    prova("...e la fattura va al registro col suo giro e i sats del libro",
          [("p2p", MORTA + ":1", 7300)], registro())
    prova("...una sola: nessun avviso", [], banco.AVVISI)
    prova("il retry di mostrod: «ripetuto», e non conta due volte",
          ({"ok": True, "nuovo": False}, 1),
          (evento(MORTA, "expired", t0 + 900, dettaglio="maker-timeout"),
           len(registro())))
    evento(PAGATA, "taken", t0, attore="buyer")
    evento(PAGATA, "hold-invoice-requested", t0 + 5)
    evento(PAGATA, "hold-invoice-paid", t0 + 30, attore="seller")
    evento(PAGATA, "expired", t0 + 900, dettaglio="escrow-deadline")
    evento(RITIRATA, "taken", t0, attore="buyer")
    evento(RITIRATA, "hold-invoice-requested", t0 + 5)
    evento(RITIRATA, "canceled", t0 + 100, attore="seller")
    prova("garanzia PAGATA e poi scaduta, e il RITIRO: non contano",
          (1, []), (len(registro()), banco.AVVISI))
    prova("un segreto sbagliato resta un 403", 403,
          evento(MORTA, "expired", t0 + 901, segreto="sbagliato"))
    # la stessa MORTA ripresa: un giro nuovo, un'altra fattura
    evento(MORTA, "taken", t0 + 920, attore="buyer")
    evento(MORTA, "hold-invoice-requested", t0 + 925)
    evento(MORTA, "expired", t0 + 1100, dettaglio="taker-timeout")
    prova("ripresa e di nuovo morta: e' un'altra fattura, e fa l'avviso",
          ([MORTA + ":1", MORTA + ":2"], 1),
          ([r[1] for r in registro()], len(banco.AVVISI)))
    prova("...che dice lo scambio P2P e la garanzia", True,
          bool(banco.AVVISI) and "• scambio P2P 5a1e0000 (garanzia), 7.300 sats"
          in banco.AVVISI[0])
    azzera()
    m = nuovo_ordine(56459)
    orologio()
    evento("5a1e0000-4444-4a2b-9c3d-000000000004", "taken", t0, attore="buyer")
    evento("5a1e0000-4444-4a2b-9c3d-000000000004", "hold-invoice-requested", t0 + 5)
    evento("5a1e0000-4444-4a2b-9c3d-000000000004", "expired", t0 + 900,
           dettaglio="maker-timeout")
    prova("un mercatino e un P2P nella stessa ora: l'avviso, con tutt'e due",
          (1, True), (len(banco.AVVISI), bool(banco.AVVISI)
                      and f"#{m}," in banco.AVVISI[0]
                      and "scambio P2P 5a1e0000" in banco.AVVISI[0]))

    # ---- 3) fail-open ------------------------------------------------
    print("\n[3) fail-open: il registro rotto non ferma niente]")
    azzera()
    c = con()
    c.execute("DROP TABLE fatture_scadute")
    c.commit()
    c.close()
    rotto = nuovo_ordine(9000)
    orologio()
    prova("registro rotto: il reaper mette lo stesso la lapide", "annullato",
          stato(rotto))
    MUTA = "5a1e0000-5555-4a2b-9c3d-000000000005"
    evento(MUTA, "taken", t0, attore="buyer")
    evento(MUTA, "hold-invoice-requested", t0 + 5)
    prima = len(banco.DETTO)
    prova("registro rotto: la rotta risponde lo stesso",
          {"ok": True, "nuovo": True},
          evento(MUTA, "expired", t0 + 900, dettaglio="maker-timeout"))
    prova("...le parti sono avvisate dello scaduto come sempre", True,
          len(banco.DETTO) > prima)
    prova("...e nessun avviso ai moderatori", [], banco.AVVISI)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
