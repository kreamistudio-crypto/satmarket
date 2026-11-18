# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA FOTOGRAFIA DELL'ANNUNCIO (18 nov 2026, cantiere
«fotografia-annuncio», ok di Andrea: «se non occupa uno spazio
esagerato e se non rallenta il sito, facciamolo»).

`prove.py` difende la forma, i giudici puri e la pagina. Qui gira il
SERVER VERO su un database usa-e-getta — compra, il pagamento, la
modifica e la rotta del moderatore — e si chiedono le cose che solo la
filiera intera puo' dire:
  1. al pagamento l'ordine si tiene l'annuncio com'era (testo, prezzo,
     consegna, foto), e il moderatore lo legge: nessuna differenza;
  2. l'annuncio cambia sotto (il sync di un negozio, un moderatore):
     la rotta dice cosa, e com'era — la fotografia non si muove;
  3. la modifica del venditore resta FERMA ad affare aperto (la guardia
     di sempre, che la fotografia non sostituisce);
  4. LA CORSA: l'ordine si paga MENTRE la modifica e' in volo (fra la
     guardia e la scrittura ci sono la moderazione e le foto): le foto
     vecchie, nominate dalla fotografia, restano sul disco;
  5. senza ordini aperti la modifica cancella le foto vecchie come ieri;
  6. la rotta e' dei moderatori; un ordine di prima ha la lista vuota;
  7. a leva spenta il pagamento non fotografa, e l'incasso va lo stesso.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco), foto in una cartella
usa-e-getta, AI e notifiche di cartone. Nessuna rete.

USO:  python collaudo_fotografia_annuncio.py
"""

import asyncio
import base64
import io
import json
import os
import tempfile

import collaudo_lnbits_muto as banco

prova = banco.prova
SRV = None
FOTO = ""
IN_VOLO = []          # gli annunci da comprare a meta' della prossima modifica
PAGATI = []           # gli ordini nati e pagati in quella corsa


def jpeg_vero(seme=0):
    """Una foto che non e' una tinta unita (il server scarta le vuote)."""
    from PIL import Image
    img = Image.new("RGB", (240, 180))
    px = img.load()
    for y in range(180):
        for x in range(240):
            px[x, y] = ((x * 7 + seme) % 256, (y * 5) % 256,
                        (x + y + seme) % 256)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(
        out.getvalue()).decode()


def avvio():
    global SRV, FOTO
    banco.avvio()
    SRV = banco.SRV
    FOTO = tempfile.mkdtemp(prefix="barattolo-fotografia-")
    SRV.FOTO_DIR = FOTO

    async def zitto(*a, **k):
        return None

    async def ai_finta(titolo, descrizione=""):
        # LA CORSA: qualcuno compra e paga QUI, fra la guardia
        # dell'affare in corso (che un ordine anche solo creato
        # fermerebbe) e la scrittura della modifica
        while IN_VOLO:
            aid = IN_VOLO.pop()
            leggi_prima, chi_prima = SRV.leggi_json, SRV.verifica_utente

            async def leggi(_req):
                return {"annuncio_id": aid, "quantita": 1,
                        "consegna": "ritiro"}
            SRV.leggi_json = leggi
            come(111)
            try:
                r = await SRV.compra(None)
                PAGATI.append(r["ordine_id"])
                await SRV._incassa_ordine(r["ordine_id"])
            finally:
                SRV.leggi_json, SRV.verifica_utente = leggi_prima, chi_prima
        return None

    SRV.moderazione_ai = ai_finta
    for nome in ("annuncio_su_nostr", "promo_venduto",
                 "avvisa_contatto_mancante", "avvisa_revisione"):
        setattr(SRV, nome, zitto)
    SRV.accoda_promo = lambda *a, **k: None
    SRV.accoda_match = lambda *a, **k: None


def come(tg_id, admin=False):
    """Il `come` del banco, col nome di battesimo che pubblica() mette
    nell'avviso ai moderatori."""
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": admin}


def chiama(rotta, corpo, *argomenti):
    """La rotta VERA: torna (200, risposta) o (codice, detail)."""
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi

    async def giro():
        try:
            r = await rotta(*argomenti)
            await asyncio.sleep(0.05)      # i create_task in coda
            return 200, r
        except SRV.HTTPException as e:
            return e.status_code, e.detail
    return asyncio.run(giro())


def db_esegui(sql, *args):
    con = SRV.db()
    con.execute(sql, args)
    con.commit()
    con.close()


def colonna(sql, *args):
    con = SRV.db()
    r = con.execute(sql, args).fetchone()
    con.close()
    return r[0] if r else None


def semina():
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(222,'Vende','neg22222',1)")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    con.commit()
    con.close()


BASE = {"prezzo_sats": 30000, "categoria": "Elettronica",
        "zona": "Torino (TO)", "descrizione": "Come nuovo, sbloccato",
        "consegna": "ritiro", "condizione": "buono", "quantita": 5}


def pubblica(titolo, **extra):
    come(222)
    return chiama(SRV.pubblica, {**BASE, "titolo": titolo,
                                 "foto": [jpeg_vero(len(titolo))], **extra},
                  None)


def modifica(aid, **extra):
    come(222)
    corpo = {**BASE, "titolo": colonna("SELECT titolo FROM annunci WHERE "
                                       "id=?", aid), **extra}
    return chiama(SRV.modifica_annuncio, corpo, aid, None)


def foto_di(aid):
    return json.loads(colonna("SELECT foto FROM annunci WHERE id=?", aid)
                      or "[]")


def sul_disco(nomi):
    return [os.path.exists(os.path.join(FOTO, n)) for n in nomi]


def ordine(aid):
    """Un ordine CREATO dai percorsi veri (non ancora pagato)."""
    come(111)
    c, r = chiama(SRV.compra, {"annuncio_id": aid, "quantita": 1,
                               "consegna": "ritiro"}, None)
    if c != 200:
        raise SystemExit(f"⚠️  compra non e' partita: {c} {r}")
    return r["ordine_id"]


def paga(oid):
    return asyncio.run(SRV._incassa_ordine(oid))


def fotografia(oid, chi=999):
    come(chi, admin=(chi == 999))
    return chiama(SRV.fotografia_ordine, None, oid, "", "")


def scena_pagamento():
    print("\n[1) al pagamento l'ordine si tiene l'annuncio com'era]")
    prova("la leva nasce accesa senza riga nel config", True,
          SRV.ORDINE_FOTOGRAFIA_ATTIVA)
    c, r = pubblica("Telefono Android")
    prova("si pubblica", 200, c)
    aid = r["id"]
    prima = foto_di(aid)
    oid = ordine(aid)
    prova("...l'ordine creato e non pagato non ha ancora fotografie", 0,
          colonna("SELECT COUNT(*) FROM ordine_fotografie WHERE ordine_id=?",
                  oid))
    prova("si paga: locked", "locked", paga(oid).get("stato"))
    c, d = fotografia(oid)
    f = (d.get("fotografie") or [{}])[0] if c == 200 else {}
    allora = f.get("allora") or {}
    prova("il moderatore la legge: una fotografia, quella dell'annuncio",
          (200, 1, aid), (c, len(d.get("fotografie") or []) if c == 200
                          else 0, f.get("annuncio_id")))
    prova("...titolo, descrizione, prezzo, consegna, condizione, foto",
          ("Telefono Android", "Come nuovo, sbloccato", 30000, "ritiro",
           "buono", prima),
          tuple(allora.get(k) for k in ("titolo", "descrizione",
                                        "prezzo_sats", "consegna",
                                        "condizione", "foto")))
    prova("...e oggi e' uguale: nessuna differenza", [], f.get("diversi"))
    prova("...la quantita' (che e' scesa col pagamento) non c'e' nemmeno",
          False, "quantita" in allora)
    peso = len(colonna("SELECT dati FROM ordine_fotografie WHERE "
                       "ordine_id=?", oid).encode())
    prova(f"...e pesa poco ({peso} byte)", True, peso < 6000)
    paga(oid)
    prova("un secondo passaggio non scrive una seconda riga", 1,
          colonna("SELECT COUNT(*) FROM ordine_fotografie WHERE ordine_id=?",
                  oid))
    return aid, oid


def scena_annuncio_cambiato(aid, oid):
    print("\n[2) l'annuncio cambia sotto: la rotta dice cosa]")
    db_esegui("UPDATE annunci SET titolo='Telefono Android (bloccato FRP)', "
              "descrizione='Venduto con blocco Google, lo sapevi', "
              "modificato=12345 WHERE id=?", aid)
    c, d = fotografia(oid)
    f = (d.get("fotografie") or [{}])[0] if c == 200 else {}
    prova("le differenze: titolo e descrizione, non la data del ritocco",
          ["titolo", "descrizione"], f.get("diversi"))
    prova("...com'era e com'e'", ("Telefono Android",
                                  "Telefono Android (bloccato FRP)"),
          ((f.get("allora") or {}).get("titolo"),
           (f.get("oggi") or {}).get("titolo")))


def scena_guardia(aid):
    print("\n[3) ad affare aperto la modifica resta ferma]")
    c, detail = modifica(aid, descrizione="Altro testo",
                         foto=[jpeg_vero(77)])
    prova("400 «affare in corso», e le foto non cambiano", (400, True),
          (c, "affare in corso" in str(detail)))


def scena_corsa():
    print("\n[4) la corsa: pagato mentre la modifica e' in volo]")
    c, r = pubblica("Tablet dieci pollici")
    aid = r["id"]
    vecchie = foto_di(aid)
    prova("le foto di partenza sono sul disco", [True], sul_disco(vecchie))
    IN_VOLO.append(aid)
    c, _ = modifica(aid, foto=[jpeg_vero(91)])
    prova("la modifica passa (la guardia era prima dell'acquisto)", 200, c)
    oid = PAGATI[-1] if PAGATI else 0
    prova("...l'ordine e' stato pagato in mezzo, con la fotografia",
          ("locked", 1),
          (banco.riga(oid)["stato"],
           colonna("SELECT COUNT(*) FROM ordine_fotografie WHERE "
                   "ordine_id=?", oid)))
    nuove = foto_di(aid)
    prova("...l'annuncio ha le foto nuove", True,
          bool(nuove) and nuove != vecchie)
    prova("...e le VECCHIE restano sul disco: le nomina la fotografia",
          [True], sul_disco(vecchie))
    c, d = fotografia(oid)
    f = (d.get("fotografie") or [{}])[0] if c == 200 else {}
    prova("il moderatore vede le foto cambiate dopo l'acquisto",
          (["foto"], vecchie), (f.get("diversi"), (f.get("allora") or {})
                                .get("foto")))
    return aid, oid


def scena_senza_ordini():
    print("\n[5) senza ordini aperti la modifica cancella come ieri]")
    c, r = pubblica("Cuffie senza fili")
    aid = r["id"]
    vecchie = foto_di(aid)
    c, _ = modifica(aid, foto=[jpeg_vero(55)])
    prova("modifica con foto nuove: 200, le vecchie via dal disco",
          (200, [False]), (c, sul_disco(vecchie)))


def scena_rotta(oid):
    print("\n[6) la rotta: dei moderatori, e gli ordini di prima]")
    c, _ = fotografia(oid, chi=111)
    prova("chi compra: 403", 403, c)
    c, _ = fotografia(oid, chi=222)
    prova("chi vende: 403", 403, c)
    c, _ = fotografia(987654)
    prova("un ordine che non c'e': 404", 404, c)
    db_esegui("DELETE FROM ordine_fotografie WHERE ordine_id=?", oid)
    c, d = fotografia(oid)
    prova("un ordine pagato prima del cantiere: lista vuota, mai un errore",
          (200, []), (c, d.get("fotografie") if c == 200 else d))


def scena_leva_spenta():
    print("\n[7) la leva spenta]")
    c, r = pubblica("Mouse da gioco")
    aid = r["id"]
    oid = ordine(aid)
    SRV.ORDINE_FOTOGRAFIA_ATTIVA = False
    try:
        prova("spenta: il pagamento va lo stesso", "locked",
              paga(oid).get("stato"))
        prova("...senza fotografia", 0,
              colonna("SELECT COUNT(*) FROM ordine_fotografie WHERE "
                      "ordine_id=?", oid))
        c, d = fotografia(oid)
        prova("...e la rotta lo dice", (200, False, []),
              (c, d.get("attiva"), d.get("fotografie")))
    finally:
        SRV.ORDINE_FOTOGRAFIA_ATTIVA = True


def scena_guasto():
    print("\n[8) un guasto della fotografia non ferma l'incasso]")
    c, r = pubblica("Caricatore rapido")
    aid = r["id"]
    oid = ordine(aid)
    vera = SRV._fotografa_annunci

    def rotta(*a, **k):
        raise RuntimeError("disco pieno, per finta")
    SRV._fotografa_annunci = rotta
    try:
        prova("la fotografia esplode: l'ordine passa a locked lo stesso",
              "locked", paga(oid).get("stato"))
    finally:
        SRV._fotografa_annunci = vera


def main():
    print("=" * 66)
    print("  LA FOTOGRAFIA DELL'ANNUNCIO — il giro vero")
    print("=" * 66)
    avvio()
    semina()
    aid, oid = scena_pagamento()
    scena_annuncio_cambiato(aid, oid)
    scena_guardia(aid)
    _, oid2 = scena_corsa()
    scena_senza_ordini()
    scena_rotta(oid2)
    scena_leva_spenta()
    scena_guasto()
    print("\n" + "=" * 66)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 66)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
