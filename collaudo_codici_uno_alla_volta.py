# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «UN CODICE ALLA VOLTA» (16 nov 2026, cantiere
codici-uno-alla-volta, idea e ok di Andrea).

IL CASO: dieci buoni da 50 € in un ordine solo erano UN campo di testo,
rivelato tutto insieme. Chi compra poteva usarli tutti e poi dire «non
funzionano»: in ballo c'erano 500 €. Adesso, da due pezzi in su, chi
vende scrive un codice per riquadro, e chi compra vede il successivo
solo dopo aver detto che il precedente funziona. I sats restano nel
deposito e partono in un pagamento solo; si dividono solo in disputa, e
la divisione la fanno i contatori.

Gira la STORIA sul SERVER VERO con un database usa-e-getta e il nodo di
cartone del banco di casa (`collaudo_lnbits_muto`): compra, incasso,
consegna, lettura, «Funziona», disputa, decisione, orologio, giro dei
pagamenti e ronda del libro mastro sono tutti quelli veri.

Le domande a cui risponde:
  1. la consegna a riquadri: il campo unico, l'immagine, un riquadro
     vuoto, due codici uguali si rifiutano; tre codici entrano;
  2. la lettura: chi vende li vede tutti, chi compra apre SOLO il primo
     (ed e' la ricevuta), una seconda lettura non apre niente;
  3. la correzione: un codice mai aperto si corregge, uno aperto no;
  4. «Funziona»: conferma il codice di turno e apre il successivo, un
     tocco doppio o fuori turno si rifiuta;
  5. la disputa sul codice 2, decisa «rimborso»: il codice 1 e' pagato
     a chi vende, il 2 e il 3 tornano a chi compra, e le due uscite
     fanno il deposito; lo stock risale di due;
  6. la stessa disputa decisa «sats al venditore»: due codici a lui;
  7. la disputa sul codice 1 decisa «rimborso» e' il rimborso integrale
     di sempre;
  8. l'ultimo «Funziona» conclude: un pagamento solo, e chi compra vede
     tutti i codici;
  9. l'orologio: 24 ore per il codice di turno, 48 in piu' per aprire il
     successivo; passate le 24 la disputa non si apre;
 10. a leva spenta, o con un pezzo solo, il campo unico di sempre;
 11. il libro mastro resta sano.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete,
nessuna chiave.

USO:  python collaudo_codici_uno_alla_volta.py
"""

import asyncio
import time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
SRV = None

PREZZO = 50_000            # un buono, in sats
A_COMPRA, A_VENDE = "compra@wallet.tld", "vende@wallet.tld"
# un PNG vero da un pixel: il vaglio della busta lo lascia passare,
# e a rifiutarlo dev'essere la regola dei riquadri
PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC"
CODICI = ["ZAL-1111-AAAA", "ZAL-2222-BBBB", "ZAL-3333-CCCC"]

FATTURE = {}
CHIESTE = []          # (a chi, sats, esito) di ogni richiesta di PAGAMENTO
_coniate = [0]


def fattura(chi, sats):
    _coniate[0] += 1
    b = bolt11_finta(sats, 3600, int(time.time()), phash=700 + _coniate[0])
    FATTURE[b] = {"chi": chi, "sats": sats}
    return b


def uscite():
    return sorted((c, s) for c, s, e in CHIESTE if e == "success")


def alza(nome, fn, codice, dentro=""):
    try:
        fn()
    except Exception as e:
        cod = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        dice = (not dentro) or dentro.lower() in testo.lower()
        prova(nome, (codice, True), (cod, dice))
        if not (cod == codice and dice):
            print(f"      testo: {testo!r}")
        return
    prova(nome, codice, "nessun rifiuto")


def avvio():
    global SRV
    banco.avvio()
    SRV = banco.SRV
    # una commissione vera, cosi' la quota di chi vende si vede netta
    SRV.COMMISSIONE_PERCENTO = 10

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


def db_uno(sql, *args):
    con = SRV.db()
    r = con.execute(sql, args).fetchone()
    con.close()
    return r


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci", "rimborsi_asta",
              "payout_passi", "payout_tentati", "codici_digitali"):
        try:
            con.execute(f"DELETE FROM {t}")
        except Exception:
            pass
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(222,'Vende','neg22222',1,?)", (A_VENDE,))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,?)", (A_COMPRA,))
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
        "valuta,condizione) VALUES(222,'Buono Zalando 50 euro','desc',?,"
        "'Buoni ed esperienze','Torino (TO)','attivo',1,'digitale',40,40,"
        "'sats','nuovo')", (PREZZO,))
    aid = cur.lastrowid
    con.commit()
    con.close()
    return aid


def pulisci_giro():
    FATTURE.clear()
    CHIESTE.clear()
    banco.PAGAMENTI.clear()
    banco.USCITE.clear()
    banco.NODO.update(codice=200, esito="success")
    banco.DETTO.clear()
    banco.AVVISI.clear()


def compra(aid, pezzi=3):
    """Un ordine pagato e pronto da consegnare, dai percorsi veri."""
    banco.come(111)
    c = banco.chiama(SRV.compra, None,
                     corpo={"annuncio_id": aid, "quantita": pezzi,
                            "consegna": "digitale"})
    oid = c["ordine_id"]
    banco.chiama(SRV._incassa_ordine, oid)
    pulisci_giro()
    return oid


def consegna(oid, corpo):
    banco.come(222)
    return banco.chiama(SRV.consegna_digitale, oid, None, "", "", corpo=corpo)


def leggi(oid, chi, admin=False, req=None):
    banco.come(chi, admin=admin)
    return banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", req)


def funziona(oid, k):
    banco.come(111)
    return banco.chiama(SRV.codice_funziona, oid, None, "", "",
                        corpo={"n": k})


def disputa(oid):
    banco.come(111)
    return banco.chiama(SRV.apri_disputa, oid, "", "")


def decidi(oid, esito):
    banco.come(999, admin=True)
    return banco.chiama(SRV.risolvi_disputa, oid, None, "", "",
                        corpo={"esito": esito})


def pronto(aid, pezzi=3):
    """Ordine consegnato a riquadri e codice 1 aperto."""
    oid = compra(aid, pezzi)
    consegna(oid, {"codici": CODICI[:pezzi], "contenuto": "Su zalando.it"})
    leggi(oid, 111)
    pulisci_giro()
    return oid


def testi(d):
    return [c["testo"] for c in d["codici"]]


def detti_a(chi):
    return " || ".join(t for c, t in banco.DETTO if c == chi)


def stock(aid):
    return db_uno("SELECT quantita FROM annunci WHERE id=?", aid)[0]


def ronda():
    db_esegui("DELETE FROM timbri WHERE nome=?", SRV.TIMBRO_LIBRO_MASTRO)
    banco.AVVISI.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    return " || ".join(banco.AVVISI)


class _Link:
    """Una richiesta che il browser dichiara NAVIGAZIONE: un link."""
    headers = {"sec-fetch-mode": "navigate"}


# ---------------------------------------------------------------
def scena_consegna(aid):
    print("\n── 1. LA CONSEGNA A RIQUADRI ──")
    oid = compra(aid)
    o = banco.riga(oid)
    prova("l'ordine da tre pezzi nasce da consegnare a riquadri",
          (True, 0), (SRV.codici_uno_alla_volta(o), o["codici_n"]))
    alza("il campo unico si rifiuta, e dice dei riquadri",
         lambda: consegna(oid, {"contenuto": " ".join(CODICI)}),
         400, "un codice per riquadro")
    alza("l'immagine si rifiuta", lambda: consegna(
        oid, {"codici": CODICI, "file": PNG}),
        400, "immagine")
    alza("un riquadro vuoto si rifiuta, col suo numero",
         lambda: consegna(oid, {"codici": [CODICI[0], "", CODICI[2]]}),
         400, "riquadro 2")
    alza("due codici uguali si rifiutano",
         lambda: consegna(oid, {"codici": [CODICI[0], CODICI[1], CODICI[0]]}),
         400, "uguale al codice 1")
    alza("due codici per tre pezzi si rifiutano",
         lambda: consegna(oid, {"codici": CODICI[:2]}), 400, "esattamente 3")
    prova("...e nessun rifiuto ha scritto niente", (0, "locked", 0),
          (banco.riga(oid)["codici_n"], banco.riga(oid)["stato"],
           db_uno("SELECT COUNT(*) FROM codici_digitali WHERE ordine_id=?",
                  oid)[0]))
    r = consegna(oid, {"codici": CODICI, "contenuto": "Si riscattano su "
                                                      "zalando.it"})
    o = banco.riga(oid)
    prova("tre codici entrano: 'shipped', tre riquadri",
          (True, "shipped", 3, 3), (r["ok"], o["stato"], o["codici_n"],
                                    r["codici_n"]))
    cif = [x[0] for x in SRV.db().execute(
        "SELECT contenuto FROM codici_digitali WHERE ordine_id=? ORDER BY n",
        (oid,)).fetchall()]
    prova("in tabella i codici portano il prefisso della cifratura",
          True, all(c.startswith(("plain:", "f2:")) for c in cif))
    prova("chi compra sa che si aprono uno alla volta", True,
          "uno alla" in detti_a(111) and "3 codici" in detti_a(111))
    return oid


def scena_lettura(oid):
    print("\n── 2. LA LETTURA ──")
    v = leggi(oid, 222)
    prova("chi vende li rilegge tutti, senza effetti",
          (CODICI, "shipped", 0),
          (testi(v), banco.riga(oid)["stato"], banco.riga(oid)["codici_aperti"]))
    alza("chi compra non apre da un link", lambda: leggi(oid, 111, req=_Link()),
         400, "Rivela")
    c = leggi(oid, 111)
    o = banco.riga(oid)
    prova("la prima lettura di chi compra apre SOLO il codice 1",
          ([CODICI[0], None, None], "delivered", 1),
          (testi(c), o["stato"], o["codici_aperti"]))
    prova("...ed e' la ricevuta (consegnato) e l'ancora del codice di turno",
          (True, True), (o["consegnato"] > 0, o["codice_aperto_il"] > 0))
    prova("...e le istruzioni comuni arrivano con lui",
          "Si riscattano su zalando.it", c["contenuto"])
    c2 = leggi(oid, 111)
    prova("una seconda lettura non apre niente", ([CODICI[0], None, None], 1),
          (testi(c2), banco.riga(oid)["codici_aperti"]))
    alza("un estraneo non legge", lambda: leggi(oid, 333), 400, "non permessa")
    banco.come(111)
    righe = {r["id"]: r for r in SRV.miei_ordini(0, "", "")}
    r = righe[oid]
    prova("la lista ordini dice i contatori e mai i codici",
          (3, 1, 0, False),
          (r.get("codici_n"), r.get("codici_aperti"),
           r.get("codici_confermati"),
           any(x in str(r) for x in CODICI)))


def scena_correzione(oid):
    print("\n── 3. LA CORREZIONE ──")
    r = consegna(oid, {"codici": ["CAMBIATO-1", CODICI[1], "ZAL-3333-NUOVO"],
                       "contenuto": "istruzioni nuove"})
    v = testi(leggi(oid, 222))
    prova("il codice 3, mai aperto, si corregge; l'1, aperto, resta",
          [CODICI[0], CODICI[1], "ZAL-3333-NUOVO"], v)
    prova("...le istruzioni, gia' viste, restano", "Si riscattano su "
          "zalando.it", leggi(oid, 222)["contenuto"])
    prova("...e la correzione e' contata, col riquadro giusto",
          ([3], 1), (r.get("corretti"), banco.riga(oid)["contenuto_correzioni"]))
    alza("un riquadro corretto uguale a un altro si rifiuta",
         lambda: consegna(oid, {"codici": CODICI[:2] + [CODICI[1]]}),
         400, "uguale")
    CODICI[2] = "ZAL-3333-NUOVO"


def scena_funziona(oid):
    print("\n── 4. «FUNZIONA» ──")
    alza("fuori turno si rifiuta", lambda: funziona(oid, 2), 409, "turno")
    r = funziona(oid, 1)
    o = banco.riga(oid)
    prova("il codice 1 confermato apre il 2, col suo testo",
          (2, CODICI[1], 1, 2), (r["aperto"], r["testo"],
                                 o["codici_confermati"], o["codici_aperti"]))
    alza("il tocco doppio si rifiuta", lambda: funziona(oid, 1), 409, "turno")
    prova("chi compra ora vede l'1 e il 2", [CODICI[0], CODICI[1], None],
          testi(leggi(oid, 111)))
    prova("...e nessun sat si e' mosso", [], uscite())


def scena_disputa_rimborso(aid, oid):
    print("\n── 5. DISPUTA SUL CODICE 2, DECISA «RIMBORSO» ──")
    s0 = stock(aid)
    disputa(oid)
    o = banco.riga(oid)
    prova("la disputa e' sul codice 2", ("dispute", 2),
          (o["stato"], o["codice_disputa"]))
    nota = " || ".join(banco.AVVISI)
    prova("il moderatore legge i contatori e cosa vuol dire decidere",
          True, "contestato il codice 2" in nota and "Decidi solo" in nota)
    a = leggi(oid, 999, admin=True)
    prova("il moderatore vede l'1 e il 2, mai il 3",
          [CODICI[0], CODICI[1], None], testi(a))
    prova("chi compra in disputa non apre il 3", [CODICI[0], CODICI[1], None],
          testi(leggi(oid, 111)))
    pulisci_giro()
    r = decidi(oid, "rimborso")
    o = banco.riga(oid)
    tot = o["prezzo_sats"]
    quota = SRV.quota_codici_venditore(o, 1)
    prova("un codice a chi vende, netto della commissione",
          SRV.netto_venditore(PREZZO), quota)
    prova("la decisione divide: un codice pagato, il resto torna",
          (True, 1, "refunded"),
          (r.get("meno_spese"), r.get("codici_venditore"), o["stato"]))
    prova("le uscite sono DUE e non superano il deposito",
          ([("compratore", tot - quota), ("venditore", quota)], True),
          (uscite(), sum(s for _, s in uscite()) <= tot))
    prova("...anzi lo fanno esattamente", tot, sum(s for _, s in uscite()))
    prova("lo stock risale dei due codici mai pagati", s0 + 2, stock(aid))
    c, v = detti_a(111), detti_a(222)
    prova("chi compra legge «sui codici», mai «spese di spedizione»",
          (True, False), ("sui codici" in c, "spedizione" in c))
    prova("chi vende legge i suoi codici e l'incasso dei codici",
          (True, True, False), ("Ti è pagato 1 codice su 3" in v,
                                "Codici incassati" in v, "spedizione" in v))
    prova("chi compra continua a non vedere il codice 3",
          [CODICI[0], CODICI[1], None], testi(leggi(oid, 111)))
    prova("il libro mastro e' sano", "", ronda())
    alza("la decisione e' definitiva", lambda: decidi(oid, "venditore"),
         400, "")


def scena_disputa_venditore(aid):
    print("\n── 6. DISPUTA SUL CODICE 2, DECISA «SATS AL VENDITORE» ──")
    oid = pronto(aid)
    funziona(oid, 1)
    disputa(oid)
    pulisci_giro()
    r = decidi(oid, "venditore")
    o = banco.riga(oid)
    quota = SRV.quota_codici_venditore(o, 2)
    prova("due codici a chi vende, il terzo torna a chi compra",
          (2, [("compratore", o["prezzo_sats"] - quota), ("venditore", quota)]),
          (r.get("codici_venditore"), uscite()))
    prova("il libro mastro e' sano", "", ronda())


def scena_disputa_primo(aid):
    print("\n── 7. DISPUTA SUL CODICE 1, «RIMBORSO» = INTEGRALE ──")
    oid = pronto(aid)
    s0 = stock(aid)
    disputa(oid)
    pulisci_giro()
    r = decidi(oid, "rimborso")
    o = banco.riga(oid)
    prova("nessun codice a chi vende: il rimborso integrale di sempre",
          ("refunded", 0, 0, [("compratore", o["prezzo_sats"])]),
          (o["stato"], o["spese_rese_sats"], o["codici_venditore"], uscite()))
    prova("lo stock risale di tutti e tre", s0 + 3, stock(aid))


def scena_tutti(aid):
    print("\n── 8. L'ULTIMO «FUNZIONA» CONCLUDE ──")
    oid = pronto(aid)
    funziona(oid, 1)
    funziona(oid, 2)
    pulisci_giro()
    r = funziona(oid, 3)
    o = banco.riga(oid)
    prova("tutti confermati: un pagamento solo, il netto intero",
          (True, "released", [("venditore", SRV.netto_venditore(
              o["prezzo_sats"] - o["protezione_sats"]))]),
          (r.get("tutti"), o["stato"], uscite()))
    prova("a ordine concluso chi compra vede tutti i codici", CODICI,
          testi(leggi(oid, 111)))


def scena_orologio(aid):
    print("\n── 9. L'OROLOGIO ──")
    ora = int(time.time())
    # codice 1 di 3 aperto da 25 ore: conta come buono, ma l'ordine no
    oid = pronto(aid)
    db_esegui("UPDATE ordini SET codice_aperto_il=? WHERE id=?",
              ora - 25 * 3600, oid)
    alza("passate le 24 ore la disputa non si apre", lambda: disputa(oid),
         400, "conta come buono")
    asyncio.run(SRV.controlla_scadenze())
    prova("a 25 ore, con altri codici da aprire, l'ordine resta aperto",
          "delivered", banco.riga(oid)["stato"])
    r = funziona(oid, 1)
    prova("...e chi compra apre ancora il successivo", 2, r["aperto"])
    db_esegui("UPDATE ordini SET codice_aperto_il=? WHERE id=?",
              ora - 73 * 3600, oid)
    pulisci_giro()
    asyncio.run(SRV.controlla_scadenze())
    prova("a 73 ore senza aprire il successivo, i sats vanno a chi vende",
          "released", banco.riga(oid)["stato"])
    # l'ultimo codice: bastano le sue 24 ore
    oid = pronto(aid, pezzi=2)
    funziona(oid, 1)
    db_esegui("UPDATE ordini SET codice_aperto_il=? WHERE id=?",
              ora - 23 * 3600, oid)
    asyncio.run(SRV.controlla_scadenze())
    prova("l'ultimo codice a 23 ore: ancora aperto", "delivered",
          banco.riga(oid)["stato"])
    db_esegui("UPDATE ordini SET codice_aperto_il=? WHERE id=?",
              ora - 25 * 3600, oid)
    asyncio.run(SRV.controlla_scadenze())
    prova("...a 25 ore si sblocca", "released", banco.riga(oid)["stato"])


def scena_campo_unico(aid):
    print("\n── 10. IL CAMPO UNICO DI SEMPRE ──")
    oid = compra(aid, pezzi=1)
    prova("un pezzo solo: campo unico", False,
          SRV.codici_uno_alla_volta(banco.riga(oid)))
    consegna(oid, {"contenuto": "ZAL-9999"})
    prova("...che si consegna e si rivela come ieri",
          ("ZAL-9999", "delivered", 0),
          (leggi(oid, 111)["contenuto"], banco.riga(oid)["stato"],
           banco.riga(oid)["codici_n"]))
    SRV.CODICI_UNO_ALLA_VOLTA = False
    try:
        oid = compra(aid, pezzi=3)
        prova("a leva spenta tre pezzi tornano al campo unico", False,
              SRV.codici_uno_alla_volta(banco.riga(oid)))
        consegna(oid, {"contenuto": "tre codici insieme"})
        prova("...e si consegnano come ieri", "shipped",
              banco.riga(oid)["stato"])
    finally:
        SRV.CODICI_UNO_ALLA_VOLTA = True
    prova("riaccesa la leva, l'ordine gia' consegnato al campo unico resta "
          "com'e'", False, SRV.codici_uno_alla_volta(banco.riga(oid)))


def main():
    print("=" * 66)
    print("  UN CODICE ALLA VOLTA — il giro vero")
    print("=" * 66)
    avvio()
    aid = semina()
    oid = scena_consegna(aid)
    scena_lettura(oid)
    scena_correzione(oid)
    scena_funziona(oid)
    scena_disputa_rimborso(aid, oid)
    scena_disputa_venditore(aid)
    scena_disputa_primo(aid)
    scena_tutti(aid)
    scena_orologio(aid)
    scena_campo_unico(aid)
    print("\n" + "=" * 66)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 66)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
