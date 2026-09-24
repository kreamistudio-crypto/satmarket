# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CHIUSURA DELLA CASSAFORTE SAAS (24 set 2026).

Sul LNbits ospitato restano sei ordini e un pagamento appeso «pending»
per sempre (il #152). Il giudice M1 e' giusto — per una macchina un
«pending» sul SaaS e' vivo — e a chiuderlo e' UNA PERSONA con due gesti
dal pannello 🧊: «dichiara morto il pagamento appeso» e «sposta sulla
cassaforte nodo». Motivo scritto, registro nel database, riga nel
journal, doppia conferma dal client.

`prove.py` fa girare le funzioni estratte in un mondo di cartone. Qui
gira il SERVER VERO — il modulo intero, lo schema di `init_db` (la
tabella del registro nasce da sola), le rotte vere, la coda vera del
pannello, la vista vera, il libro mastro vero — su un database
usa-e-getta. Di finto ci sono SOLO le due LNbits (distinte dall'URL,
come in produzione), LND e l'orologio, che qui si sposta: 24 ore non si
aspettano.

  1. lo schema: `gesti_cassaforte` nasce da `init_db`;
  2. IL #152 PER INTERO: appeso sul SaaS → 🧊 → «presto» (scaduta da
     poco) → scaduta da 25 ore → dichiarato morto (motivo, conferma,
     registro, journal, credito) → chi vende sente «tocca a te» → incolla
     la fattura nuova → PAGATO DAL NODO da solo → il credito rientra col
     promemoria del Debit quando LNbits dice «failed»;
  3. SPOSTA: un ordine 'locked' del SaaS spostato sul nodo → l'acquirente
     conferma → l'incasso esce DAL NODO; un secondo, spostato e poi
     rimborsato da una disputa → il rimborso esce DAL NODO;
  4. i rifiuti: pagamento in corso, ordine del nodo, non moderatore;
  5. la vista «Cassaforte SaaS» e il libro mastro, che non grida.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_chiusura_saas.py
"""

import asyncio
import sys
import time as _time

import collaudo_lnbits_muto as banco
from collaudo_altra_cassaforte import (BANCHE, LND, POSTE, Orologio,
                                       _DueLnbits)
from prove import bolt11_finta

prova = banco.prova
MINUTI, ORE = 60, 3600
MOTIVO = "il SaaS chiude: pending dal 20 set, nessuna preimage"


def h(n):
    return f"{n:064x}"


def main():
    print("=" * 58)
    print("  LA CHIUSURA DELLA CASSAFORTE SAAS — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    SRV.httpx = _DueLnbits
    orologio = Orologio()
    SRV.time = orologio
    for nome, valore in {
            "LNBITS_URL": "http://saas.finto",
            "LNBITS_INVOICE_KEY": "lettura-saas",
            "LNBITS_ADMIN_KEY": "paga-saas",
            "LNBITS_NODO_URL": "http://nodo.finto",
            "LNBITS_NODO_INVOICE_KEY": "lettura-nodo",
            "LNBITS_NODO_ADMIN_KEY": "paga-nodo"}.items():
        setattr(SRV, nome, valore)

    async def lnd_finto(payment_hash):
        return LND.get(payment_hash, SRV.LND_ASSENTE)

    SRV._chiedi_lnd = lnd_finto
    a1, a2, a3, a4 = banco.semina()

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

    def fattura(n, vita=3600):
        return bolt11_finta(50_000, vita, int(orologio.time()), phash=n)

    def moderatore():
        banco.come(999, admin=True)

    def posso_morto(oid):
        moderatore()
        return asyncio.run(SRV.posso_dichiarare_morto("ordine", oid, "", ""))

    def morto(oid, **k):
        moderatore()
        return rifiuto(SRV.dichiara_morto, None, "", "",
                       corpo={"tipo": "ordine", "id": oid, **k})

    def posso_sposta(oid):
        moderatore()
        return SRV.posso_spostare_nodo("ordine", oid, "", "")

    def sposta(oid, **k):
        moderatore()
        return rifiuto(SRV.sposta_nodo, None, "", "",
                       corpo={"tipo": "ordine", "id": oid, **k})

    def vista():
        moderatore()
        return SRV.vista_cassaforte_saas("", "")

    def coda(oid):
        moderatore()
        return next((r for r in SRV.coda_pagamenti("", "")
                     if r["tipo"] == "ordine" and r["id"] == oid), {})

    def codice(e):
        return getattr(e, "status_code", None)

    def campo(r, chiave):
        # su un rifiuto (HTTPException) risponde None: la prova diventa
        # rossa col suo nome, il collaudo non cade
        return r.get(chiave) if isinstance(r, dict) else None

    def gesti():
        return leggi("SELECT riga_id, gesto, da, a, sats, deciso_da, motivo "
                     "FROM gesti_cassaforte ORDER BY id")

    # ---- 1) lo schema ---------------------------------------------
    print("\n[lo schema]")
    colonne = lambda t: {r[1] for r in leggi(f"PRAGMA table_info({t})")}
    prova("init_db: il registro dei gesti nasce da solo, con le sue colonne",
          True, {"gesto", "da", "a", "hash", "sats", "motivo", "deciso_da",
                 "deciso_il"} <= colonne("gesti_cassaforte"))

    # ---- 2) il #152, per intero ------------------------------------
    print("\n[il #152: appeso sul SaaS, dichiarato morto, pagato dal nodo]")
    F1 = fattura(1)
    oid = banco.ordine_pagato(a1)
    banco.fattura_di_ieri(oid, F1)
    prova("l'ordine nasce sul SaaS", "saas", banco.riga(oid)["cassaforte"])
    banco.DETTO.clear(); banco.AVVISI.clear()
    banco.come(111)
    rifiuto(SRV.conferma_ricezione, oid, None)
    prova("confermato: il payout parte dal SaaS e resta appeso",
          ("in_volo", [("saas", h(1))]),
          (banco.riga(oid)["payout_stato"], POSTE))
    orologio.avanti = 40 * MINUTI
    asyncio.run(SRV.risolvi_pagamenti_in_volo())
    prova("dopo mezz'ora: 🧊", "incerto", banco.riga(oid)["payout_stato"])
    c = coda(oid)
    prova("la coda vera porta il quarto bottone, SPENTO (non sono passate "
          "24 ore dalla scadenza)",
          ("saas", False), (campo(c, "cassaforte"), (campo(c, "morto") or {}).get("forse")))
    r = posso_morto(oid)
    prova("scaduta da poco: «presto»", (False, "presto"),
          (campo(r, "ok"), campo(r, "codice")))
    prova("...e la rotta rifiuta: 409, niente mosso", (409, 1),
          (codice(morto(oid, motivo=MOTIVO, conferma=True)), len(POSTE)))
    orologio.avanti = 60 * MINUTI + 25 * ORE
    c = coda(oid)
    prova("scaduta da 25 ore: il bottone si accende", True,
          (campo(c, "morto") or {}).get("forse"))
    r = posso_morto(oid)
    prova("...e il «posso?» dice si': hash, cifra, fattura vecchia",
          (True, [h(1)], 50_000, True),
          (campo(r, "ok"), [a["hash"] for a in campo(r, "appesi") or []],
           campo(r, "sats"), campo(r, "fattura_vecchia")))
    v = vista()
    prova("la vista VERA: un ordine che esce ancora dal SaaS, col pagamento "
          "appeso, il gesto acceso e i doveri contati",
          (1, 1, 0, 50_000, 1, True, False, True),
          (v["totali"]["aperti"], v["totali"]["dal_saas"],
           v["totali"]["sul_nodo"], v["totali"]["sats_dal_saas"],
           len(v["ordini"][0]["appesi"]), v["ordini"][0]["morto"],
           v["ordini"][0]["sposta"],
           all(d["n"] is not None for d in v["doveri"])))
    prova("...«ordini aperti» del SaaS ne conta uno", [1],
          [d["n"] for d in v["doveri"] if d["nome"] == "ordini aperti"])
    prova("senza motivo: 400; senza conferma: 400", (400, 400),
          (codice(morto(oid, conferma=True)), codice(morto(oid, motivo=MOTIVO))))
    banco.come(222)
    prova("chi non modera: 403", 403, codice(rifiuto(
        SRV.dichiara_morto, None, "", "",
        corpo={"tipo": "ordine", "id": oid, "motivo": MOTIVO, "conferma": True})))
    banco.DETTO.clear(); banco.AVVISI.clear()
    r = morto(oid, motivo=MOTIVO, conferma=True)
    prova("DICHIARATO MORTO", ("morto", True), (campo(r, "esito"), campo(r, "ok")))
    o = banco.riga(oid)
    prova("...l'ordine e' libero, 'confirmed', esce dal nodo, `cassaforte` "
          "resta saas, la fattura vecchia e' via",
          ("confirmed", "", "saas", "nodo", ""),
          (o["stato"], o["payout_stato"], o["cassaforte"],
           o["cassaforte_payout"], o["invoice_venditore"]))
    prova("...l'hash appeso e' «deviato» sul saas", [("deviato", "saas")],
          leggi("SELECT esito, cassaforte FROM payout_tentati WHERE hash=?", h(1)))
    prova("...il credito e' aperto sul saas", [("saas", h(1), 50_000, "nodo", "aperto")],
          leggi("SELECT cassaforte, hash, sats, pagato_da, stato FROM "
                "crediti_cassaforte"))
    prova("...il registro dice tutto", [(oid, "dichiara_morto", "saas", "nodo",
                                        50_000, 999, MOTIVO)], gesti())
    prova("...chi vende sente il solito «tocca a te»", 1, sum(
        1 for chi, t in banco.DETTO if chi == 222 and "Tocca a te" in t))
    prova("...i moderatori leggono il verbale col Debit", 1, sum(
        1 for a in banco.AVVISI if "💀" in a and "Debit" in a))
    prova("...e dal nodo non e' partito niente", [("saas", h(1))], POSTE)
    prova("una volta sola: 409", 409,
          codice(morto(oid, motivo=MOTIVO, conferma=True)))
    F2 = fattura(2)
    banco.come(222)
    banco.DETTO.clear()
    r = rifiuto(SRV.deposita_invoice, oid, None, "", "",
                corpo={"invoice": F2})
    prova("chi vende incolla la fattura nuova: PAGATO DAL NODO, da solo",
          (True, "released", [("saas", h(1)), ("nodo", h(2))]),
          (campo(r, "ok"), campo(r, "stato"), POSTE))
    o = banco.riga(oid)
    prova("...la riga: released, uscito, hash nuovo, saas → nodo",
          ("released", "uscito", h(2), "saas", "nodo"),
          (o["stato"], o["payout_stato"], o["payout_hash"], o["cassaforte"],
           o["cassaforte_payout"]))
    prova("...«Arrivati ✓»", 1, sum(
        1 for chi, t in banco.DETTO if chi == 222 and "Arrivati ✓" in t))
    banco.AVVISI.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    prova("il libro mastro VERO grida il credito e non la deviazione",
          (True, False),
          ("credito da recuperare su un'altra cassaforte" in " ".join(banco.AVVISI),
           "incasso deviato senza verbale" in " ".join(banco.AVVISI)))
    BANCHE["saas"][h(1)] = "failed"
    banco.AVVISI.clear()
    orologio.avanti += ORE
    asyncio.run(SRV.sorveglia_crediti())
    prova("LNbits dice «failed»: il credito rientra, e l'avviso ricorda il Debit",
          ("rientrato", 1),
          (leggi("SELECT stato FROM crediti_cassaforte")[0][0],
           sum(1 for a in banco.AVVISI if "Credito rientrato" in a and "Debit" in a)))
    prova("...e la vista non ha piu' niente", (0, 0),
          (vista()["totali"]["aperti"], vista()["crediti"]["n"]))

    # ---- 3) sposta, poi l'incasso e il rimborso escono dal nodo ----
    print("\n[sposta sulla cassaforte nodo]")
    orologio.avanti = 0
    oid2 = banco.ordine_pagato(a2)
    r = posso_sposta(oid2)
    prova("un ordine 'locked' del SaaS: si puo' spostare", (True, "saas", "nodo"),
          (campo(r, "ok"), campo(r, "origine"), campo(r, "destinazione")))
    prova("senza motivo: 400", 400, codice(sposta(oid2, conferma=True)))
    banco.DETTO.clear(); banco.AVVISI.clear()
    r = sposta(oid2, motivo=MOTIVO, conferma=True)
    o = banco.riga(oid2)
    prova("SPOSTATO: la riga promette il nodo, niente si muove",
          ("spostato", "locked", "saas", "nodo", 2),
          (campo(r, "esito"), o["stato"], o["cassaforte"], o["cassaforte_payout"],
           len(POSTE)))
    prova("...la nota e il registro", (True, 2),
          ("spostato sulla cassaforte nodo" in o["payout_nota"], len(gesti())))
    prova("...i moderatori lo sanno, il libro mastro tace", (1, False),
          (sum(1 for a in banco.AVVISI if "➡️" in a),
           (lambda: (banco.AVVISI.clear(), asyncio.run(SRV.controlla_libro_mastro()),
                     "incasso deviato senza verbale" in " ".join(banco.AVVISI))[2])()))
    prova("due volte: 409", 409, codice(sposta(oid2, motivo=MOTIVO, conferma=True)))
    v = vista()
    prova("la vista lo conta fra gli spostati", (0, 1, 50_000),
          (v["totali"]["dal_saas"], v["totali"]["sul_nodo"],
           v["totali"]["sats_sul_nodo"]))
    banco.fattura_di_ieri(oid2, fattura(3))
    banco.come(111)
    rifiuto(SRV.conferma_ricezione, oid2, None)
    o = banco.riga(oid2)
    prova("l'acquirente conferma: l'incasso esce DAL NODO",
          ("released", "uscito", ("nodo", h(3))),
          (o["stato"], o["payout_stato"], POSTE[-1]))
    # il rimborso
    oid3 = banco.ordine_pagato(a3)
    sposta(oid3, motivo=MOTIVO, conferma=True)
    esegui("UPDATE ordini SET stato='dispute', disputata=1, invoice_rimborso=? "
           "WHERE id=?", fattura(4), oid3)
    try:
        r = asyncio.run(SRV._rimborsa_compratore(oid3))
    except Exception as e:
        r = e
    o = banco.riga(oid3)
    prova("spostato e poi rimborsato: il RIMBORSO esce dal NODO",
          (True, "refunded", ("nodo", h(4)), "saas"),
          (campo(r, "ok"), o["stato"], POSTE[-1], o["cassaforte"]))

    # ---- 4) i rifiuti -----------------------------------------------
    print("\n[i rifiuti]")
    oid4 = banco.ordine_pagato(a4)
    banco.fattura_di_ieri(oid4, fattura(5))
    banco.come(111)
    rifiuto(SRV.conferma_ricezione, oid4, None)
    orologio.avanti = 40 * MINUTI
    asyncio.run(SRV.risolvi_pagamenti_in_volo())
    prova("un pagamento congelato non si sposta: «in_corso», 409",
          ("incerto", "in_corso", 409),
          (banco.riga(oid4)["payout_stato"], campo(posso_sposta(oid4), "codice"),
           codice(sposta(oid4, motivo=MOTIVO, conferma=True))))
    BANCHE["saas"][h(5)] = "failed"
    prova("...e «dichiara morto» su un «failed» dice di usare «Verifica e riprova»",
          "non_pending", campo(posso_morto(oid4), "codice"))
    esegui("UPDATE ordini SET cassaforte='nodo' WHERE id=?", oid4)
    prova("un ordine del nodo: «non_saas» e «gia_nodo»", ("non_saas", "gia_nodo"),
          (campo(posso_morto(oid4), "codice"), campo(posso_sposta(oid4), "codice")))
    banco.come(222)
    prova("chi non modera non sposta e non vede la vista: 403, 403", (403, 403),
          (codice(rifiuto(SRV.sposta_nodo, None, "", "",
                          corpo={"tipo": "ordine", "id": oid2, "motivo": MOTIVO,
                                 "conferma": True})),
           codice(rifiuto(SRV.vista_cassaforte_saas, "", ""))))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
