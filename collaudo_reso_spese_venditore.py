# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL RESO A SPESE DEL VENDITORE (18 nov 2026, cantiere
«reso-spese-venditore», ok di Andrea).

IL CASO (dal campo): un compratore riceve un telefono bloccato (FRP)
e deve rispedirlo. Col reso di sempre l'etichetta la pagava lui, in
euro e coi suoi dati — ma l'oggetto difettoso e' colpa di chi vende.
Il quinto esito del moderatore, «Reso a spese del venditore», fa la
STESSA strada del reso (nessuno stato nuovo) e dice a chi vende di
mandare l'etichetta prepagata nella chat dell'ordine entro
GIORNI_ETICHETTA_RESO. Passati quelli, chi compra puo' avvisare i
moderatori, che decidono il «Rimborso»: niente scatta da solo.

Gira sul SERVER VERO con un database usa-e-getta e il nodo di cartone
del banco di casa (`collaudo_lnbits_muto`). Le domande:
  1. la decisione: 'return_pending', l'istante scritto, nessun sat
     mosso, e i due testi giusti (chi compra: «non pagare niente»;
     chi vende: «a tue spese», la chat, la scadenza);
  2. l'avviso prima del tempo si rifiuta, e lo rifiuta anche a chi
     vende e a un estraneo;
  3. passati i giorni l'avviso arriva ai moderatori UNA volta, e a
     chi vende; un secondo tocco non suona di nuovo;
  4. il moderatore rimborsa da un reso in corso: tutto il deposito a
     chi compra, una volta;
  5. il reso a spese del venditore fa la strada di sempre: spedito,
     ricevuto, rimborsato — e a reso spedito l'avviso non c'e' piu';
  6. il reso di sempre resta com'era: niente istante, niente avviso;
  7. le guardie del reso valgono anche qui: un pagamento in volo, e
     il moderatore che e' una delle parti.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete.

USO:  python collaudo_reso_spese_venditore.py
"""

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

FATTURE = {}
CHIESTE = []          # (a chi, sats, esito) di ogni richiesta di PAGAMENTO
_coniate = [0]


def fattura(chi, sats):
    _coniate[0] += 1
    b = bolt11_finta(sats, 3600, int(time.time()), phash=900 + _coniate[0])
    FATTURE[b] = {"chi": chi, "sats": sats}
    return b


def uscite():
    return [(c, s) for c, s, e in CHIESTE if e == "success"]


def alza(nome, fn, codice, dentro=""):
    try:
        fn()
    except Exception as e:
        cod = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        ok = cod == codice and ((not dentro) or dentro.lower() in testo.lower())
        prova(nome, (codice, True),
              (cod, (not dentro) or dentro.lower() in testo.lower()))
        if not ok:
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

    vero_post = banco._FintoHttpx.AsyncClient.post

    async def post(self, url, **kw):
        j = kw.get("json") or {}
        b = j.get("data") or j.get("bolt11") or ""
        if b in FATTURE:
            banco.NODO["sats"] = FATTURE[b]["sats"]
            banco.NODO["esito"] = "success"
            if "decode" not in url:
                CHIESTE.append((FATTURE[b]["chi"], FATTURE[b]["sats"],
                                "success"))
        return await vero_post(self, url, **kw)

    banco._FintoHttpx.AsyncClient.post = post


def db_esegui(sql, *args):
    con = SRV.db()
    con.execute(sql, args)
    con.commit()
    con.close()


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
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
        "valuta,condizione,spedizione_sats) VALUES(222,'Telefono','desc',?,"
        "'Altro','Torino (TO)','attivo',1,'spedizione',40,40,'sats',"
        "'buono',?)", (PREZZO, SPED))
    aid = cur.lastrowid
    con.commit()
    con.close()
    banco.NODO.update(codice=200, esito="success")
    return aid


def disputa(aid):
    """Un ordine pagato, spedito e finito in disputa, dai percorsi veri."""
    banco.come(111)
    corpo = {"consegna": "spedizione", "spedizione_via": "casa",
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


def decidi(oid, esito="reso_venditore", chi=999):
    banco.come(chi, admin=True)
    return banco.chiama(SRV.risolvi_disputa, oid, None, "", "",
                        corpo={"esito": esito})


def avvisa(oid, chi=111):
    banco.come(chi)
    return banco.chiama(SRV.reso_etichetta_mancante, oid, "", "")


def invecchia(oid, giorni):
    """La decisione presa `giorni` fa: si sposta l'istante, non l'orologio."""
    db_esegui("UPDATE ordini SET reso_venditore_il=reso_venditore_il-? "
              "WHERE id=?", int(giorni * 86400), oid)


def detti_a(chi):
    return " || ".join(t for c, t in banco.DETTO if c == chi)


# ---------------------------------------------------------------
def scena_decisione(aid):
    print("\n── 1. LA DECISIONE: il reso, e chi paga l'etichetta ──")
    oid = disputa(aid)
    prima = int(time.time())
    r = decidi(oid)
    o = banco.riga(oid)
    prova("la decisione torna 'return_pending' con l'istante",
          ("return_pending", True),
          (r.get("stato"), int(r.get("reso_venditore_il") or 0) >= prima))
    prova("l'ordine e' 'return_pending': nessuno stato nuovo",
          "return_pending", o["stato"])
    prova("...e porta l'istante della decisione", r.get("reso_venditore_il"),
          o["reso_venditore_il"])
    prova("...e nessun avviso dato", 0, o["etichetta_mancante_il"])
    prova("nessun sat si e' mosso", [], uscite())
    c, v = detti_a(111), detti_a(222)
    scade = SRV._data_etichetta_reso(o["reso_venditore_il"])
    prova("chi compra legge che il reso lo paga chi vende, e di non pagare",
          (True, True, True),
          ("reso a spese del venditore" in c, "Non pagare" in c,
           scade in c))
    prova("chi vende legge che e' a sue spese, la chat e la scadenza",
          (True, True, True),
          ("reso a tue spese" in v, "chat dell'ordine" in v, scade in v))
    prova("la scadenza e' fra GIORNI_ETICHETTA_RESO giorni (3)", 3,
          SRV.GIORNI_ETICHETTA_RESO)
    return oid


def scena_prima_del_tempo(oid):
    print("\n── 2. PRIMA DEL TEMPO L'AVVISO SI RIFIUTA ──")
    alza("chi compra, al primo giorno: rifiutato col perche'",
         lambda: avvisa(oid), 400, "puoi avvisare i moderatori dal")
    invecchia(oid, 3 - 1 / 24)
    alza("...e un'ora prima della scadenza ancora no",
         lambda: avvisa(oid), 400, "puoi avvisare")
    alza("chi vende non puo' avvisare al posto di chi compra",
         lambda: avvisa(oid, 222), 400, "non permessa")
    alza("...e nemmeno un estraneo", lambda: avvisa(oid, 333), 400,
         "non permessa")
    prova("nessun moderatore e' stato chiamato", [], banco.AVVISI)


def scena_avviso(oid):
    print("\n── 3. PASSATI I GIORNI: L'AVVISO, UNA VOLTA ──")
    invecchia(oid, 1 / 24 + 1 / 1440)
    banco.DETTO.clear()
    r = avvisa(oid)
    o = banco.riga(oid)
    prova("l'avviso riesce e resta scritto", (True, True),
          (r.get("ok"), o["etichetta_mancante_il"] > 0))
    prova("...l'ordine resta 'return_pending': niente si muove da solo",
          ("return_pending", []), (o["stato"], uscite()))
    prova("i moderatori lo leggono, col numero dell'ordine e il «Rimborso»",
          (1, True, True),
          (len(banco.AVVISI), f"#{oid}" in " ".join(banco.AVVISI),
           "Rimborso" in " ".join(banco.AVVISI)))
    prova("chi vende sa che l'acquirente ha avvisato i moderatori", True,
          "ha avvisato i moderatori" in detti_a(222))
    r2 = avvisa(oid)
    prova("un secondo tocco riesce ma non suona di nuovo", (True, True, 1),
          (r2.get("ok"), r2.get("gia"), len(banco.AVVISI)))
    prova("...e l'istante del primo avviso non cambia",
          o["etichetta_mancante_il"], banco.riga(oid)["etichetta_mancante_il"])


def scena_rimborso(oid):
    print("\n── 4. IL MODERATORE RIMBORSA DA UN RESO IN CORSO ──")
    r = decidi(oid, "rimborso")
    o = banco.riga(oid)
    prova("l'ordine e' rimborsato", ("refunded", "refunded"),
          (r.get("stato"), o["stato"]))
    prova("...tutto il deposito a chi compra, una volta",
          [("compratore", TOTALE)], uscite())
    alza("a ordine rimborsato l'avviso non c'e' piu'",
         lambda: avvisa(oid), 400, "non permessa")


def scena_strada_di_sempre(aid):
    print("\n── 5. LA STRADA DI SEMPRE: spedito, ricevuto, rimborsato ──")
    oid = disputa(aid)
    decidi(oid)
    banco.come(111)
    banco.chiama(SRV.reso_spedito, oid, None, "", "",
                 corpo={"corriere": "InPost", "tracking": "IP123"})
    prova("con l'etichetta del venditore chi compra segna il reso spedito",
          "return_shipped", banco.riga(oid)["stato"])
    invecchia(oid, 4)
    alza("a reso spedito l'avviso dell'etichetta non c'e' piu'",
         lambda: avvisa(oid), 400, "non permessa")
    banco.come(222)
    banco.chiama(SRV.reso_ricevuto, oid, "", "")
    o = banco.riga(oid)
    prova("chi vende lo riceve: rimborso integrale, una volta",
          ("refunded", [("compratore", TOTALE)]), (o["stato"], uscite()))
    prova("...e il segno del reso a spese del venditore resta nella storia",
          True, o["reso_venditore_il"] > 0)


def scena_reso_di_sempre(aid):
    print("\n── 6. IL RESO DI SEMPRE RESTA COM'ERA ──")
    oid = disputa(aid)
    r = decidi(oid, "reso")
    o = banco.riga(oid)
    prova("'return_pending', senza l'istante", ("return_pending", 0, False),
          (o["stato"], o["reso_venditore_il"], "reso_venditore_il" in r))
    c = detti_a(111)
    prova("chi compra legge il testo di sempre, non «non pagare»",
          (True, False),
          ("rimborso previa restituzione" in c, "Non pagare" in c))
    alza("l'avviso dell'etichetta non vale sul reso di sempre",
         lambda: avvisa(oid), 400, "non permessa")
    alza("su un reso gia' deciso non si decide un altro reso",
         lambda: decidi(oid), 400, "già in restituzione")


def scena_guardie(aid):
    print("\n── 7. LE GUARDIE DEL RESO VALGONO ANCHE QUI ──")
    oid = disputa(aid)
    db_esegui("UPDATE ordini SET payout_stato='in_volo' WHERE id=?", oid)
    alza("un pagamento in volo ferma il reso a spese del venditore",
         lambda: decidi(oid), 409, "non sappiamo ancora")
    db_esegui("UPDATE ordini SET payout_stato='' WHERE id=?", oid)
    vecchio = SRV.ADMIN_IDS
    SRV.ADMIN_IDS = [999, 222]
    try:
        alza("il moderatore che e' il venditore non lo decide",
             lambda: decidi(oid, chi=222), 403, "un altro moderatore")
    finally:
        SRV.ADMIN_IDS = vecchio
    alza("un esito inventato si rifiuta", lambda: decidi(oid, "reso_x"),
         400, "non valido")
    prova("...e l'ordine e' ancora in disputa, senza istante",
          ("dispute", 0), (banco.riga(oid)["stato"],
                           banco.riga(oid)["reso_venditore_il"]))


def main():
    print("=" * 66)
    print("  IL RESO A SPESE DEL VENDITORE — il giro vero")
    print("=" * 66)
    avvio()
    aid = semina()
    oid = scena_decisione(aid)
    scena_prima_del_tempo(oid)
    scena_avviso(oid)
    scena_rimborso(oid)
    scena_strada_di_sempre(aid)
    scena_reso_di_sempre(aid)
    scena_guardie(aid)
    print("\n" + "=" * 66)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 66)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
