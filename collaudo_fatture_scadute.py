# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE FATTURE SCADUTE (20 set 2026, ordine #152).

Il caso vero: il venditore incolla una fattura quando spedisce, il
payout parte alla consegna confermata QUATTRO GIORNI dopo, e la fattura
e' scaduta da quattro. LND la rifiuta prima di cercare una strada,
LNbits risponde 520, e noi dicevamo «LNbits ha risposto 520» a chi
modera e «la rete non ha trovato una strada» a chi vendeva.

`prove.py` fa girare le funzioni estratte in un mondo di cartone. Qui
gira il SERVER VERO — il modulo intero, col suo schema, le sue rotte e
le sue costanti — su un database usa-e-getta: e' il giro che si accorge
di una colonna che manca, di un nome definito dopo il suo uso, di una
rotta che non passa il campo giusto. Di finto c'e' SOLO il nodo, ed e'
quello di `collaudo_lnbits_muto.py` (una riga per payment hash, come
LNbits vero), con un modo in piu': il 520 che porta il suo perche'.

LE FATTURE SONO BOLT11 SINTATTICAMENTE VERE (`bolt11_finta` di
prove.py: bech32 col checksum, la scadenza nel campo `x`), perche' il
giudice della scadenza la legge DALLA FATTURA.

  1. la porta: PRIMA della conferma non si incolla niente (21 set
     2026) — rifiutata quella da un'ora e pure quella da 31 giorni;
  2. il #152: in colonna c'e' una fattura scaduta da quattro giorni, il
     compratore conferma → NESSUNA richiesta di pagamento, l'ordine va
     in 'confirmed', la fattura morta si toglie, al venditore si dice
     che e' scaduta e quando, ai moderatori «NON TENTATO»;
  3. la stessa fattura rincollata → rifiutata; una nuova → pagata, una
     volta sola;
  4. il 520 «invoice expired» su una fattura che per noi era viva: ai
     moderatori il perche' in parole, al venditore la frase giusta;
  5. il pannello 🧊: una riga congelata il cui hash e' `failed` su
     LNbits e la cui fattura e' scaduta → «Verifica e riprova» NON
     ripaga, toglie il fermo, e dice SCADUTA.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_fatture_scadute.py
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
    print("  LE FATTURE SCADUTE — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    a1, a2, a3, a4 = banco.semina()
    adesso = int(time.time())
    dovuti = 50_000
    un_ora = bolt11_finta(dovuti, 3600, adesso - 5)
    lunga = bolt11_finta(dovuti, 31 * GIORNO, adesso - 5)
    morta = bolt11_finta(dovuti, 3600, adesso - 4 * GIORNO - 3600)
    il_giorno = SRV.giorno_scadenza(morta)

    def rifiuto(fn, *args, corpo=None):
        try:
            return banco.chiama(fn, *args, corpo=corpo)
        except SRV.HTTPException as e:
            return e

    # ---- 1) la porta ---------------------------------------------
    print("\n[la porta: quando si incolla]")
    oid = banco.ordine_pagato(a1)
    banco.come(222)
    # DAL 21 SET 2026 la fattura si incolla SOLO all'incasso: prima della
    # conferma la porta e' chiusa a tutte, anche a quella da 31 giorni
    # che fino al 20 si salvava. Il metodo che si imposta prima e' uno
    # solo, l'address.
    for nome, fattura in (("da un'ora", un_ora), ("da 31 giorni", lunga)):
        e = rifiuto(SRV.deposita_invoice, oid, None,
                    corpo={"invoice": fattura})
        prova(f"prima della conferma, fattura {nome}: rifiutata", 400,
              getattr(e, "status_code", None))
        prova("...col perche', l'avviso che arrivera', e l'address", True,
              all(x in str(getattr(e, "detail", "")) for x in (
                  "solo al momento dell'incasso", "ti avvisiamo",
                  "Lightning address", "non scade")))
        prova("...e in colonna non e' entrato niente", "",
              banco.riga(oid)["invoice_venditore"] or "")

    # ---- 2) il #152 ----------------------------------------------
    print("\n[il #152: in colonna c'e' una fattura scaduta da 4 giorni]")
    con = SRV.db()
    con.execute("UPDATE ordini SET invoice_venditore=? WHERE id=?",
                (morta, oid))
    con.commit()
    con.close()
    banco.DETTO.clear(); banco.AVVISI.clear(); banco.USCITE.clear()
    banco.come(111)
    esito = banco.chiama(SRV.conferma_ricezione, oid, None)
    dopo = banco.riga(oid)
    prova("nessuna richiesta di pagamento parte", 0, len(banco.USCITE))
    prova("...e su LNbits non nasce nessuna riga", {}, banco.PAGAMENTI)
    prova("l'ordine va in 'confirmed', senza fermi",
          ("confirmed", ""), (dopo["stato"], dopo["payout_stato"]))
    prova("la fattura morta si toglie dalla colonna", "",
          dopo["invoice_venditore"])
    prova("il diario dice perche'", True,
          "scaduta" in (dopo["payout_errore"] or ""))
    prova("nessun hash resta sulla riga, ne' in memoria", ("", 0),
          (dopo["payout_hash"] or "",
           SRV.db().execute("SELECT COUNT(*) FROM payout_tentati WHERE "
                            "riga_id=?", (oid,)).fetchone()[0]))
    al_venditore = " ".join(t for chi, t in banco.DETTO if chi == 222)
    prova("al venditore: e' scaduta, e quando", True,
          f"è scaduta {il_giorno}" in al_venditore)
    prova("...cosa fare, e la cura che non scade", True,
          "fattura <b>nuova</b>" in al_venditore
          and "Lightning address" in al_venditore)
    prova("...e non che la rete non ha trovato una strada", False,
          "non ha trovato una strada" in al_venditore)
    prova("ai moderatori: NON TENTATO, col giorno", True,
          any("NON TENTATO" in x and il_giorno in x for x in banco.AVVISI))
    prova("...e nessun «FALLITO»", [],
          [x for x in banco.AVVISI if "FALLITO" in x])
    prova("chi ha confermato non vede un errore", "confirmed",
          esito.get("stato"))

    # ---- 3) la stessa, poi una nuova -----------------------------
    print("\n[il venditore rincolla]")
    banco.come(222)
    e = rifiuto(SRV.deposita_invoice, oid, None, corpo={"invoice": morta})
    prova("LA STESSA fattura: rifiutata alla porta, col giorno",
          (400, True),
          (getattr(e, "status_code", None),
           "già scaduta" in str(getattr(e, "detail", ""))
           and il_giorno in str(getattr(e, "detail", ""))))
    banco.USCITE.clear()
    e = rifiuto(SRV.deposita_invoice, oid, None, corpo={"invoice": un_ora})
    prova("una fattura NUOVA: pagata subito", "released",
          e.get("stato") if isinstance(e, dict) else e)
    prova("...una volta sola", 1, len(banco.USCITE))

    # ---- 4) il 520 col suo perche' -------------------------------
    print("\n[il 520 che dice «invoice expired»]")
    post_vero = banco._FintoHttpx.AsyncClient.post

    async def post_520(self, url, **kw):
        if "decode" in url:
            return await post_vero(self, url, **kw)
        banco.USCITE.append(url)
        h = banco._hash_di((kw.get("json") or {}).get("bolt11", ""))
        banco.PAGAMENTI[h] = "failed"
        return banco._Risposta(520, {
            "detail": "Payment failed: invoice expired. Valid until ieri"})
    banco._FintoHttpx.AsyncClient.post = post_520
    oid2 = banco.ordine_pagato(a2)
    con = SRV.db()
    altra = bolt11_finta(dovuti, 3600, adesso - 6)
    con.execute("UPDATE ordini SET invoice_venditore=? WHERE id=?",
                (altra, oid2))
    con.commit()
    con.close()
    banco.DETTO.clear(); banco.AVVISI.clear()
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid2, None)
    banco._FintoHttpx.AsyncClient.post = post_vero
    avviso = " ".join(banco.AVVISI)
    prova("ai moderatori: FALLITO, e il perche' in parole", True,
          "FALLITO" in avviso and "Perché:" in avviso
          and "<b>scaduta</b>" in avviso)
    prova("...col testo grezzo di LNbits, non il solo numero", True,
          "520: Payment failed: invoice expired" in avviso)
    prova("il diario della riga lo tiene", True,
          "invoice expired" in (banco.riga(oid2)["payout_errore"] or ""))
    al_venditore = " ".join(t for chi, t in banco.DETTO if chi == 222)
    prova("al venditore: scaduta, non «nessuna strada»", (True, False),
          ("è scaduta" in al_venditore,
           "non ha trovato una strada" in al_venditore))

    # ---- 5) il pannello 🧊 ----------------------------------------
    print("\n[🧊 Verifica e riprova su una fattura scaduta]")
    oid3 = banco.ordine_pagato(a3)
    morta3 = morta            # stessa forma: scaduta da quattro giorni
    h = banco._hash_di(morta3)
    banco.PAGAMENTI[h] = "failed"
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='delivered', invoice_venditore=?, "
                "payout_stato='incerto', payout_hash=?, "
                "payout_verso='venditore', payout_ultimo=?, "
                "payout_tentativi=1 WHERE id=?",
                (morta3, h, adesso - 4 * GIORNO, oid3))
    con.execute("INSERT INTO payout_tentati(tabella, riga_id, hash, quando, "
                "esito) VALUES('ordini',?,?,?,'')",
                (oid3, h, adesso - 4 * GIORNO))
    con.commit()
    con.close()
    banco.DETTO.clear(); banco.AVVISI.clear(); banco.USCITE.clear()
    banco.come(999, admin=True)
    r = rifiuto(SRV.decidi_pagamento, None,
                corpo={"tipo": "ordine", "id": oid3, "esito": "verifica"})
    prova("la decisione passa (LNbits dice failed, LND e' spento)", True,
          isinstance(r, dict) and r.get("esito") == "ritentato")
    prova("NON si ripaga la fattura morta", 0, len(banco.USCITE))
    prova("al moderatore: SCADUTA, e niente in volo", True,
          isinstance(r, dict) and "SCADUTA" in r.get("messaggio", "")
          and "niente in volo" in r.get("messaggio", ""))
    dopo = banco.riga(oid3)
    prova("il fermo e' tolto e si aspetta la fattura nuova",
          ("confirmed", "", ""),
          (dopo["stato"], dopo["payout_stato"], dopo["invoice_venditore"]))
    prova("al venditore: scaduta, e quando", True,
          any(f"è scaduta {il_giorno}" in t
              for chi, t in banco.DETTO if chi == 222))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
