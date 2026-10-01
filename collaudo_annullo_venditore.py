# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ANNULLO DEL VENDITORE (1 ott 2026).

Caso vero dal campo: un venditore aveva finito l'oggetto senza togliere
l'annuncio, piu' persone l'hanno comprato e pagato, e lui doveva
avvisarle a mano una per una perche' da chi vende un ordine non si
poteva annullare. Da oggi puo', finche' non ha spedito: i sats tornano
per intero al compratore per la strada dei rimborsi di sempre, lui
riceve subito un avviso col motivo, e con «esaurito» l'annuncio va in
pausa da solo.

`prove.py` fa girare la rotta e il rimborso in un mondo di cartone. Qui
gira il SERVER VERO — il modulo intero, lo schema di `init_db` con le
quattro colonne nuove, la cassa vera (`compra`), la rotta vera, il
rimborso vero con `paga_venditore` e la fattura dal Lightning address, la
lista vera di /api/orders — su un database usa-e-getta. Di finto c'e'
SOLO la cassaforte (il LNbits di cartone di `collaudo_lnbits_muto`, che
tiene una riga per payment hash come quello vero), la fattura coniata
dal Lightning address, e le due piazze (Nostr e il canale), che qui non
hanno niente da dire.

  1. il mono ESAURITO, compratore col Lightning address: refunded
     subito, per intero; l'annuncio in pausa (0, 'venduto'); l'avviso
     col motivo, poi quello del rimborso; il polso col conto;
  2. «NON POSSO SPEDIRE», compratore SENZA metodo: 'refund' e un solo
     avviso; poi incolla la fattura e il rimborso parte, con l'annuncio
     tornato in vetrina UNA volta sola;
  3. l'ordine NON PAGATO: lapide 'annullato', nessun sat, «non pagare»;
  4. i RIFIUTI: spedito, il compratore, «altro» senza nota — e niente
     si muove;
  5. il TERZO annullo pagato in trenta giorni: l'allarme ai moderatori;
  6. /api/orders porta i campi nuovi a tutt'e due le parti.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_annullo_venditore.py
"""

import time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova


def main():
    print("=" * 58)
    print("  L'ANNULLO DEL VENDITORE — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV

    coniate = [0]

    async def fattura_da_address(addr, sats):
        # un hash NUOVO a ogni fattura: il LNbits di cartone tiene una
        # riga per hash, come quello vero, e due fatture uguali sarebbero
        # un solo pagamento
        coniate[0] += 1
        return bolt11_finta(sats, 3600, int(time.time()), phash=100 + coniate[0])

    async def zitto(*a, **k):
        return None

    SRV.invoice_da_ln_address = fattura_da_address
    SRV.annuncio_su_nostr = zitto
    SRV.promo_venduto = zitto
    # il polso dei moderatori: il banco di casa lo zittisce, qui si
    # ascolta — la riga finisce fra gli avvisi, come dal vero
    async def polso(riga):
        banco.AVVISI.append(riga)

    SRV.polso_ordini_admin = polso
    ids = banco.semina()
    con = SRV.db()
    con.execute("UPDATE annunci SET quantita_max=5")   # il MAX di sempre
    con.commit()
    con.close()

    def pagato(annuncio_id):
        """Un ordine fino a 'locked' passando dal CUORE VERO del pagamento
        (`_incassa_ordine`: CAS, stock scalato, offerte, avvisi) — il
        banco di casa salta lo stock, e qui lo stock e' la cosa da
        guardare. Le parole dell'incasso si buttano: non sono di questo
        collaudo."""
        banco.come(111)
        c = banco.chiama(SRV.compra, None, corpo={"annuncio_id": annuncio_id,
                                                  "consegna": "ritiro"})
        banco.chiama(SRV._incassa_ordine, c["ordine_id"])
        banco.DETTO.clear()
        banco.AVVISI.clear()
        return c["ordine_id"]

    def annulla(oid, corpo, chi=222):
        banco.come(chi)
        try:
            return banco.chiama(SRV.annulla_vendita, oid, None, corpo=corpo)
        except SRV.HTTPException as e:
            return e

    def annuncio(aid):
        con = SRV.db()
        a = con.execute("SELECT stato, quantita, quantita_max FROM annunci "
                        "WHERE id=?", (aid,)).fetchone()
        con.close()
        return (a["stato"], a["quantita"], a["quantita_max"])

    def ln_address(tg_id, valore):
        con = SRV.db()
        con.execute("UPDATE utenti SET ln_address=? WHERE tg_id=?",
                    (valore, tg_id))
        con.commit()
        con.close()

    def pulisci():
        banco.DETTO.clear()
        banco.AVVISI.clear()
        banco.USCITE.clear()

    def detti_a(chi):
        return [t for d, t in banco.DETTO if d == chi]

    # ============ 1. IL MONO ESAURITO ==================================
    print("\n[1. esaurito, col Lightning address]")
    pulisci()
    oid = pagato(ids[0])
    prova("l'ordine parte da 'locked', 50.000 sats, un pezzo scalato (4 su 5)",
          ("locked", 50000, ("attivo", 4, 5)),
          (banco.riga(oid)["stato"], banco.riga(oid)["prezzo_sats"],
           annuncio(ids[0])))
    r = annulla(oid, {"motivo": "esaurito"})
    o = banco.riga(oid)
    prova("annullato e rimborsato SUBITO, dal LNbits vero di cartone",
          (True, "refunded", "refunded", "uscito", 1),
          (r.get("ok"), r.get("stato"), o["stato"], o["payout_stato"],
           len(banco.USCITE)))
    prova("...la riga porta il timbro, il motivo e l'esaurito",
          (True, "esaurito", str(ids[0])),
          (o["annullato_venditore_il"] > 0, o["motivo_annullo"],
           o["esauriti_annullo"]))
    prova("...l'annuncio e' in PAUSA: 0 pezzi, 'venduto', il MAX intatto",
          ("venduto", 0, 5), annuncio(ids[0]))
    al_compratore = detti_a(111)
    prova("...al compratore due avvisi: l'annullo col motivo, poi i sats",
          (2, True, True, True),
          (len(al_compratore),
           "Il venditore ha annullato" in al_compratore[0]
           and "Oggetto esaurito" in al_compratore[0]
           and "per intero" in al_compratore[0],
           "Rimborso dell'ordine annullato" in al_compratore[1],
           not any("isputa" in t for t in al_compratore)))
    prova("...a chi vende la ricevuta del rimborso", True,
          any("sats sono tornati per intero" in t for t in detti_a(222)))
    prova("...il polso ai moderatori: l'annullo (1°), e nessun allarme",
          (True, False),
          (any("Ordine annullato dal venditore" in a and "È il 1° annullo" in a
               for a in banco.AVVISI),
           any("⚠️" in a and "ha annullato" in a for a in banco.AVVISI)))

    # ============ 2. NON POSSO SPEDIRE, SENZA METODO ===================
    print("\n[2. non posso spedire, senza Lightning address]")
    pulisci()
    ln_address(111, "")
    oid = pagato(ids[1])
    r = annulla(oid, {"motivo": "spedizione"})
    o = banco.riga(oid)
    prova("senza metodo l'ordine resta 'refund', nessun sat uscito",
          (True, "refund", "refund", 0),
          (r.get("ok"), r.get("stato"), o["stato"], len(banco.USCITE)))
    prova("...l'annuncio e' GIA' tornato in vetrina (5 su 5)",
          ("attivo", 5, 5), annuncio(ids[1]))
    prova("...al compratore UN avviso solo, che dice come riceverli",
          (1, True), (len(detti_a(111)),
                      "scegli come riceverli" in detti_a(111)[0]))
    # giorni dopo incolla la fattura
    banco.come(111)
    r = banco.chiama(SRV.deposita_invoice, oid, None,
                     corpo={"invoice": bolt11_finta(50000, 3600,
                                                    int(time.time()), phash=2)})
    o = banco.riga(oid)
    prova("la fattura incollata paga: refunded, un'uscita", (True, "refunded", 1),
          (r.get("ok"), o["stato"], len(banco.USCITE)))
    prova("...e lo stock NON si conta due volte: ancora 5 su 5",
          ("attivo", 5, 5), annuncio(ids[1]))
    prova("...le parole sono quelle dell'annullo", True,
          any("Rimborso dell'ordine annullato" in t for t in detti_a(111)))

    # ============ 3. L'ORDINE NON PAGATO ===============================
    print("\n[3. non pagato: la lapide]")
    pulisci()
    banco.come(111)
    c = banco.chiama(SRV.compra, None, corpo={"annuncio_id": ids[2],
                                              "consegna": "ritiro"})
    oid = c["ordine_id"]
    r = annulla(oid, {"motivo": "altro", "nota": "mi sono trasferito"})
    o = banco.riga(oid)
    prova("'creato': lapide 'annullato', nessun sat, la nota scritta",
          ("annullato", "annullato", 0, "mi sono trasferito"),
          (r.get("stato"), o["stato"], len(banco.USCITE), o["nota_annullo"]))
    prova("...al compratore: non pagare, col motivo", True,
          "Non pagare la fattura" in detti_a(111)[0]
          and "Altro: mi sono trasferito" in detti_a(111)[0])
    prova("...nessun polso: non c'erano sats", False,
          any("annullato dal venditore" in a for a in banco.AVVISI))
    banco.come(222)
    prova("...la lapide esce in lista come 'annullato' (il client la nasconde)",
          "annullato", {x["id"]: x["stato"]
                        for x in SRV.miei_ordini(0)}.get(oid))

    # ============ 4. I RIFIUTI ========================================
    print("\n[4. i rifiuti]")
    pulisci()
    oid = pagato(ids[3])
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='shipped' WHERE id=?", (oid,))
    con.commit()
    con.close()
    r = annulla(oid, {"motivo": "spedizione"})
    prova("spedito: 400, con le parole giuste",
          (400, True), (r.status_code, "già spedito" in r.detail))
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (oid,))
    con.commit()
    con.close()
    prova("il compratore non puo' (400)", 400,
          annulla(oid, {"motivo": "spedizione"}, chi=111).status_code)
    prova("«altro» senza nota: 400", 400,
          annulla(oid, {"motivo": "altro"}).status_code)
    prova("motivo sconosciuto: 400", 400,
          annulla(oid, {"motivo": "boh"}).status_code)
    prova("...e niente si e' mosso: locked, 4 su 5, nessun avviso",
          ("locked", ("attivo", 4, 5), 0, 0),
          (banco.riga(oid)["stato"], annuncio(ids[3]), len(banco.DETTO),
           len(banco.USCITE)))

    # ============ 5. IL TERZO ANNULLO: L'ALLARME ======================
    print("\n[5. il terzo annullo pagato in trenta giorni]")
    pulisci()
    ln_address(111, "compra@wallet.tld")
    r = annulla(oid, {"motivo": "spedizione"})
    prova("il terzo annullo pagato: refunded, il polso dice 3°, l'allarme parte",
          ("refunded", True, True),
          (r.get("stato"),
           any("È il 3° annullo" in a for a in banco.AVVISI),
           any("ha annullato 3 ordini pagati in 30 giorni" in a
               for a in banco.AVVISI)))

    # ============ 6. LA LISTA DEGLI ORDINI ============================
    print("\n[6. /api/orders]")
    banco.come(222)
    miei = {x["id"]: x for x in SRV.miei_ordini(0)}
    o = miei[oid]
    prova("chi vende legge il timbro e il motivo nella sua lista",
          (True, "spedizione", "refunded"),
          (o["annullato_venditore_il"] > 0, o["motivo_annullo"], o["stato"]))
    banco.come(111)
    suoi = {x["id"]: x for x in SRV.miei_ordini(0)}
    prova("...e chi compra pure", ("spedizione", "refunded"),
          (suoi[oid]["motivo_annullo"], suoi[oid]["stato"]))
    prova("gli annulli pagati del venditore, contati dal giudice", 3,
          SRV._conta_annulli_venditore(SRV.db(), 222))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
