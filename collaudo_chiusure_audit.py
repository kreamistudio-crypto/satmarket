# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE PICCOLE CHIUSURE DEL PRIMO AUDIT (14 nov 2026,
cantiere audit-chiusure, dal primo audit di sicurezza).

`prove.py` (`prove_chiusure_audit`) prova i pezzi estratti; qui girano
le ROTTE VERE sul server vero, con un database usa-e-getta e il banco
della porta del timer: quattro storie, e nessuna cambia un gesto di chi
usa l'app.

  1. IL CONTENUTO DIGITALE NON SI RIVELA DA UN LINK. Chi compra, col
     codice consegnato e non ancora rivelato, segue un link che punta
     alla lettura: 400, l'ordine resta 'shipped', nessuna ricevuta,
     chi vende non sente niente. Poi rivela dall'ordine, com'e' sempre
     stato: 'delivered', la ricevuta, l'avviso a chi vende.
  2. OGNI LETTURA DI CHI COMPRA LASCIA LA RICEVUTA. Disputa aperta
     PRIMA di rivelare, poi il codice letto: lo stato non si muove, ma
     la ricevuta si scrive e i moderatori lo sanno. La seconda lettura
     non scrive piu' niente. Chi vende e il moderatore rileggono senza
     lasciare tracce, come ieri.
  3. IL COMMENTO DI UN FEEDBACK ESCE SCAPPATO nell'avviso all'altra
     parte: un `<a href>` resta testo.
  4. LE TRE LEVE CHE RESTANO SUL VPS: la porta di scrittura risponde
     404 a un admin, e nel database non entra niente.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete,
nessuna chiave.

USO:  python collaudo_chiusure_audit.py
"""

import types

import collaudo_porta_timer as banco

prova = banco.prova
SRV = None
AGLI_ADMIN = []     # (argomento, testo) di ogni avviso ai moderatori

LINK = types.SimpleNamespace(headers={
    "sec-fetch-mode": "navigate", "sec-fetch-site": "cross-site",
    "accept": "text/html,application/xhtml+xml"})
PAGINA = types.SimpleNamespace(headers={
    "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
    "accept": "*/*"})


def tenta(fn, *args, corpo=None):
    """Una rotta che rifiuta torna come (codice, parole)."""
    try:
        return banco.chiama(fn, *args, corpo=corpo)
    except SRV.HTTPException as e:
        return (e.status_code, str(e.detail))


def consegnato_non_rivelato(annuncio_id):
    """Compra, incassa (l'unico pezzo simulato, come nel banco) e chi
    vende consegna il codice: l'ordine e' 'shipped', mai rivelato."""
    banco.come(111)
    c = banco.chiama(SRV.compra, None, corpo={"annuncio_id": annuncio_id,
                                              "consegna": "digitale"})
    oid = c["ordine_id"]
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (oid,))
    con.commit()
    con.close()
    banco.come(222)
    banco.chiama(SRV.consegna_digitale, oid, None,
                 corpo={"contenuto": "ABCD-1234-EFGH"})
    return oid


def due(oid):
    o = banco.riga(oid)
    return (o["stato"], bool(o["consegnato"]))


def detti_a(chi):
    return " | ".join(t for c, t in banco.DETTO if c == chi)


def scena_link(aid):
    print("\n── 1. LA RIVELAZIONE NON LA FA UN LINK ──")
    oid = consegnato_non_rivelato(aid)
    banco.DETTO.clear()
    banco.come(111)
    r = tenta(SRV.leggi_contenuto_digitale, oid, "", "", LINK)
    prova("chi compra segue un link verso la lettura: 400, con le sue "
          "parole", (400, True),
          (r[0], "si rivela dall'ordine" in str(r[1])) if isinstance(r, tuple)
          else ("letto", r))
    prova("...l'ordine resta com'era: 'shipped', nessuna ricevuta",
          ("shipped", False), due(oid))
    prova("...e chi vende non ha sentito parlare di rivelazione", False,
          "rivelato" in detti_a(222))
    r = banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", PAGINA)
    prova("dall'ordine, col suo bottone, si rivela come sempre",
          ("ABCD-1234-EFGH", ("delivered", True)),
          (r.get("contenuto"), due(oid)))
    prova("...e chi vende lo sa", True,
          "rivelato il contenuto" in detti_a(222))
    r = tenta(SRV.leggi_contenuto_digitale, oid, "", "", LINK)
    prova("a rivelazione fatta rileggere non cambia niente, nemmeno da "
          "un link (non c'e' piu' nessuna ricevuta da scrivere)",
          "ABCD-1234-EFGH", r.get("contenuto") if isinstance(r, dict) else r)


def scena_lettura_tarda(aid):
    print("\n── 2. DISPUTA PRIMA DI RIVELARE, POI IL CODICE LETTO ──")
    oid = consegnato_non_rivelato(aid)
    banco.come(111)
    banco.chiama(SRV.apri_disputa, oid)
    prova("la disputa si apre senza aver rivelato", ("dispute", False),
          due(oid))
    AGLI_ADMIN.clear()
    banco.DETTO.clear()
    banco.come(222)
    banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", PAGINA)
    banco.come(999, admin=True)
    banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", PAGINA)
    prova("chi vende e il moderatore rileggono senza lasciare tracce",
          (("dispute", False), []), (due(oid), list(AGLI_ADMIN)))
    banco.come(111)
    r = tenta(SRV.leggi_contenuto_digitale, oid, "", "", LINK)
    prova("da un link nemmeno questa lettura parte", (400, ("dispute", False)),
          (r[0] if isinstance(r, tuple) else "letto", due(oid)))
    r = banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", PAGINA)
    prova("chi compra legge il codice in disputa: lo riceve, lo stato non "
          "si muove, e la RICEVUTA si scrive",
          ("ABCD-1234-EFGH", ("dispute", True), True),
          (r.get("contenuto"), due(oid), bool(r.get("rivelato"))))
    prova("...e i moderatori lo sanno, nell'argomento delle dispute",
          (1, "dispute", True),
          (len(AGLI_ADMIN), AGLI_ADMIN[0][0] if AGLI_ADMIN else "",
           f"#{oid}" in (AGLI_ADMIN[0][1] if AGLI_ADMIN else "")))
    timbro = banco.riga(oid)["consegnato"]
    AGLI_ADMIN.clear()
    banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", PAGINA)
    prova("la seconda lettura non e' una seconda ricevuta ne' un secondo "
          "avviso", (timbro, []),
          (banco.riga(oid)["consegnato"], list(AGLI_ADMIN)))


def scena_commento(aid):
    print("\n── 3. IL COMMENTO DI UN FEEDBACK NELL'AVVISO ──")
    oid = banco.ordine_digitale(aid)
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='released' WHERE id=?", (oid,))
    con.commit()
    con.close()
    banco.DETTO.clear()
    banco.come(111)
    COMMENTO = '<a href="https://example.invalid/">clicca qui</a> & co'
    banco.chiama(SRV.lascia_feedback, oid, None,
                 corpo={"voto": 5, "commento": COMMENTO})
    avviso = detti_a(222)
    prova("l'avviso all'altra parte arriva", True,
          "Hai ricevuto un feedback" in avviso)
    prova("...col commento come TESTO: nessun link vero dentro",
          (False, True, True),
          ("<a href" in avviso, "&lt;a href=" in avviso, "&amp; co" in avviso))
    prova("...e chi lo legge senza HTML (DM Nostr, campanella) vede "
          "quello che e' stato scritto", True,
          COMMENTO in SRV.spoglia_html(avviso))
    con = SRV.db()
    salvato = con.execute("SELECT commento FROM feedback WHERE ordine_id=?",
                          (oid,)).fetchone()[0]
    con.close()
    prova("...nel database il commento resta com'e' stato scritto",
          COMMENTO, salvato)


def scena_leve():
    print("\n── 4. LE TRE LEVE CHE RESTANO SUL VPS ──")
    banco.come(999, admin=True)
    esiti = [tenta(SRV.leva_admin_cambia, k, None, corpo={"valore": v})
             for k, v in (("GUARDIANO_PONTE_AVVISA", [424242]),
                          ("BLOSSOM_SERVER", "http://127.0.0.1:9"),
                          ("LND_PONTE_CERT", "/non-esiste"))]
    prova("un admin prova a scriverle dalla porta del pannello: 404, "
          "«solo dal VPS»", [(404, True)] * 3,
          [(e[0], "solo dal VPS" in str(e[1])) if isinstance(e, tuple)
           else ("scritta", e) for e in esiti])
    con = SRV.db()
    try:
        n = con.execute(
            "SELECT COUNT(*) FROM leve_pannello WHERE chiave IN "
            "('GUARDIANO_PONTE_AVVISA','BLOSSOM_SERVER','LND_PONTE_CERT')"
        ).fetchone()[0]
    except Exception:
        n = 0                       # la tabella non e' nemmeno nata
    con.close()
    prova("...e nel database non e' entrato niente", 0, n)
    prova("...i valori vivi sono quelli del config", ([], True),
          (SRV.GUARDIANO_PONTE_AVVISA,
           SRV.BLOSSOM_SERVER.startswith("https://")))


def main():
    global SRV
    print("=" * 66)
    print("  LE PICCOLE CHIUSURE DEL PRIMO AUDIT — il giro vero")
    print("=" * 66)
    banco.avvio()
    SRV = banco.SRV

    async def agli_admin(testo, bottone=None, argomento=""):
        AGLI_ADMIN.append((argomento, testo))
    SRV.notifica_admin = agli_admin
    a1, a2 = banco.semina()
    scena_link(a1)
    scena_lettura_tarda(a2)
    scena_commento(a1)
    scena_leve()
    print("\n" + "=" * 66)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 66)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
