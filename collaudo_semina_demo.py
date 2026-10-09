# -*- coding: utf-8 -*-
"""
🌱 LA SEMINA DELLA DEMO, SUL SERVER VERO (9 ott 2026).

`prove.py` gira `semina_demo.py` su un database in memoria con le sole
colonne che lo script dichiara di volere. Qui si fa la domanda che solo
il server VERO risponde: su uno schema nato da `init_db` e dalle sue
migrazioni, la semina scrive righe che le ROTTE leggono davvero — il
negozio si apre per codice e per link, l'annuncio esce in ricerca e in
vetrina, le foto rispondono dalla whitelist, l'ordine «creato» sta in
«Ordini» del cliente e il mietitore lo lascia in pace.

IL GIRO:
  - prima della semina: /api/negozio/<codice del client> risponde 404
    (il buco del 9 ott: la card «Consigliati» portava al vuoto);
  - senza un cambio nel database la semina si ferma e dice --cambio-usd;
  - col cambio scritto da «CoinGecko» (la riga di cambio_noto): negozio,
    annuncio a 4.800 sats = 4,80 $, cliente — e le rotte lo vedono;
  - rilanciata: niente doppioni; col cambio cambiato: il prezzo si ritara;
  - `ordine`: in «Ordini» di 111 come «creato», senza fattura; il
    mietitore (`controlla_abbandonati`) con l'ordine invecchiato di
    un'ora NON lo annulla; `ordine` di nuovo non duplica, `--nuovo` si';
  - col config di produzione (MODALITA_COLLAUDO False) non scrive.

Niente parla con Telegram, coi relay o con LNbits: il `config` finto lo
installa `avvio()` del banco PRIMA dell'import di server, e in CI c'e'
la gabbia senza rete di `collaudi_ci.py`. Le foto vanno in una cartella
usa-e-getta (`SEMINA_CARTELLA_FOTO`, e `FOTO_DIR` del server girato li'):
la `foto/` del repo non si tocca.

USO:  python collaudo_semina_demo.py
"""

import asyncio
import io
import os
import re
import shutil
import sys
import tempfile
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}


def main():
    print("=" * 58)
    print("  🌱 LA SEMINA DELLA DEMO — il giro vero")
    print("=" * 58)
    db = banco.avvio()
    from fastapi.testclient import TestClient
    import semina_demo as sd

    SRV = banco.SRV
    c = TestClient(SRV.app)
    cartella = tempfile.mkdtemp(prefix="semina-collaudo-")
    SRV.FOTO_DIR = cartella
    os.environ["SEMINA_CARTELLA_FOTO"] = cartella
    try:
        giro(c, SRV, sd, db, cartella)
    finally:
        os.environ.pop("SEMINA_CARTELLA_FOTO", None)
        shutil.rmtree(cartella, ignore_errors=True)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


def comando(sd, args):
    """`semina_demo.main` col config del banco (gia' in sys.modules),
    uscita catturata: (codice, testo)."""
    uscita, fuori = io.StringIO(), sys.stdout
    sys.stdout = uscita
    try:
        rc = sd.main(args)
    finally:
        sys.stdout = fuori
    return rc, uscita.getvalue()


def giro(c, SRV, sd, db, cartella):
    codice = sd.codice_negozio_del_client(
        open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read())
    prova("il codice negozio della card «Consigliati» del client ha la forma",
          True, bool(re.fullmatch(r"[0-9a-f]{8}", codice)))

    def negozio(chi):
        r = c.get(f"/api/negozio/{chi}?limit=12")
        return r.status_code, (r.json() if r.status_code == 200 else None)

    def ricerca(q):
        d = c.get(f"/api/listings?q={q}").json()
        lista = d if isinstance(d, list) else d.get("annunci") or d.get("listings") or []
        return [(a["id"], a["prezzo_sats"]) for a in lista]

    def ordini():
        d = c.get("/api/orders", headers=COMPRATORE).json()
        lista = d if isinstance(d, list) else d.get("ordini") or []
        return [(o["id"], o["stato"], o["prezzo_sats"], o.get("invoice", ""))
                for o in lista]

    print("\n[prima della semina: il buco del 9 ott]")
    prova("il negozio del client non c'e' (404)", 404, negozio(codice)[0])
    prova("...e «Mooon» non trova niente", [], ricerca("Mooon"))

    print("\n[la semina]")
    rc, out = comando(sd, [])
    prova("senza un cambio nel database si ferma e dice --cambio-usd",
          (1, True), (rc, "--cambio-usd" in out))
    con = SRV.db()
    adesso = int(time.time())
    con.execute("INSERT OR REPLACE INTO cambio_noto(valuta, valore, quando) "
                "VALUES('eur', 90000, ?), ('usd', 100000, ?)", (adesso, adesso))
    con.commit()
    con.close()
    rc, out = comando(sd, [])
    prova("col cambio del server: verde, 4.800 sats = 4,80 $", (0, True),
          (rc, "4.800 sats = 4,80 $ al cambio di 100.000 $/BTC letto dal server" in out))
    s, d = negozio(codice)
    v = (d or {}).get("venditore") or {}
    prova("il negozio si apre per codice: nome, npub, avatar",
          (200, "To The Mooon", sd.NPUB_NEGOZIO, f"av_{codice}_1.jpg"),
          (s, v.get("nome"), v.get("npub"), v.get("avatar")))
    annunci = (d or {}).get("annunci") or []
    prova("...con l'annuncio in vetrina a 4.800 sats, ritiro, due foto",
          (1, 4800, "ritiro", 2),
          (len(annunci), annunci[0]["prezzo_sats"] if annunci else 0,
           annunci[0].get("consegna") if annunci else "",
           len(__import__("json").loads(annunci[0]["foto"])) if annunci else 0))
    aid = annunci[0]["id"] if annunci else 0
    s2, d2 = negozio("tothemooon")
    prova("...e per link a scelta /negozio/tothemooon, lo stesso negozio",
          (200, v.get("negozio")), (s2, ((d2 or {}).get("venditore") or {}).get("negozio")))
    prova("le pagine HTML del negozio rispondono", (200, 200),
          (c.get(f"/negozio/{codice}").status_code, c.get("/negozio/tothemooon").status_code))
    prova("l'avatar e le foto escono dalla whitelist della rotta /foto",
          ("image/jpeg", "image/webp", "image/webp"),
          tuple(c.get(f"/foto/{n}").headers.get("content-type", "").split(";")[0]
                for n in (f"av_{codice}_1.jpg", f"a{aid}_0.webp", f"a{aid}_1.webp")))
    prova("«Mooon» lo trova (l'indice si rifa' alla ricerca)", [(aid, 4800)],
          ricerca("Mooon"))
    prova("il cliente 111 esiste", 1, SRV.db().execute(
        "SELECT COUNT(*) FROM utenti WHERE tg_id=111").fetchone()[0])

    print("\n[l'insegna]")
    prova("senza link e con la leva spenta il negozio non ha banner", None,
          negozio(codice)[1]["venditore"].get("banner"))
    SRV.BANNER_NEGOZIO_ATTIVO = True
    sys.modules["config"].BANNER_NEGOZIO_ATTIVO = True   # la semina legge la leva dal config
    rc, out = comando(sd, ["--insegna-link", "https://esempio.test/gioco"])
    prova("col link e la leva: ✓ insegna", (0, True),
          (rc, "✓ insegna ban_" in out and "link https://esempio.test/gioco" in out))
    prova("...e il negozio porta banner {foto, link, dominio}",
          {"foto": f"ban_{codice}_1.jpg", "link": "https://esempio.test/gioco",
           "dominio": "esempio.test"},
          negozio(codice)[1]["venditore"].get("banner"))
    prova("...l'insegna esce dalla rotta /foto come JPEG", "image/jpeg",
          c.get(f"/foto/ban_{codice}_1.jpg").headers.get("content-type", "").split(";")[0])

    print("\n[rilanciata: niente doppioni, prezzo ritarato]")
    rc, out = comando(sd, [])
    prova("la seconda semina: verde, «c’era», niente da ritoccare, il link resta", (0, True),
          (rc, out.count("c’era") == 3 and "niente da ritoccare" in out
           and "link https://esempio.test/gioco" in out))
    con = SRV.db()
    conti = tuple(con.execute(q).fetchone()[0] for q in (
        "SELECT COUNT(*) FROM utenti WHERE tg_id=444",
        "SELECT COUNT(*) FROM annunci WHERE venditore_id=444",
        "SELECT COUNT(*) FROM utenti WHERE tg_id=111"))
    con.execute("UPDATE cambio_noto SET valore=120000 WHERE valuta='usd'")
    con.commit()
    con.close()
    prova("un negozio, un annuncio, un cliente", (1, 1, 1), conti)
    rc, out = comando(sd, [])
    prova("col cambio a 120.000: ritoccato 4.800 → 4.000 sats", (0, True),
          (rc, "ritoccato: prezzo 4.800 → 4.000 sats" in out))
    prova("...e la vetrina lo dice", 4000, (negozio(codice)[1]["annunci"][0]["prezzo_sats"]))

    print("\n[l'ordine della mattina]")
    prova("prima: nessun ordine di 111", [], ordini())
    rc, out = comando(sd, ["ordine"])
    m = re.search(r"Ordine #(\d+) creato", out)
    oid = int(m.group(1)) if m else 0
    prova("`ordine`: verde, creato, non pagato", (0, True, True),
          (rc, bool(m), "non pagato" in out))
    prova("in «Ordini» di 111: creato, 4.000 sats, senza fattura",
          [(oid, "creato", 4000, "")], ordini())
    rc, out = comando(sd, ["ordine"])
    prova("`ordine` di nuovo: c'e' gia', non duplica", (0, True, 1),
          (rc, "c'è già" in out, len(ordini())))
    con = SRV.db()
    con.execute("UPDATE ordini SET creato=creato-3600, aggiornato=aggiornato-3600 "
                "WHERE id=?", (oid,))
    con.commit()
    con.close()
    asyncio.run(SRV.controlla_abbandonati())
    asyncio.run(SRV.controlla_annullati())
    prova("il mietitore, un'ora dopo, lo lascia «creato»",
          [(oid, "creato", 4000, "")], ordini())
    r = c.post(f"/api/orders/{oid}/verifica-pagamento", headers=COMPRATORE)
    prova("la verifica del pagamento non lo tocca (non c'e' niente da verificare)",
          "creato", ordini()[0][1])
    rc, out = comando(sd, ["ordine", "--nuovo"])
    prova("`ordine --nuovo`: il secondo ordine, due in tutto", (0, 2),
          (rc, len(ordini())))
    rc, out = comando(sd, ["stato"])
    prova("`stato`: verde e racconta", (0, True),
          (rc, "negozio To The Mooon" in out and "ordine" in out))

    print("\n[la guardia]")
    cfg = sys.modules["config"]
    cfg.MODALITA_COLLAUDO = False
    try:
        rc, out = comando(sd, [])
    finally:
        cfg.MODALITA_COLLAUDO = True
    prova("col config di produzione il comando si ferma", (1, True),
          (rc, "MODALITA_COLLAUDO" in out))
    prova("...e nel database non e' cambiato niente", (1, 1, 2), tuple(
        SRV.db().execute(q).fetchone()[0] for q in (
            "SELECT COUNT(*) FROM utenti WHERE tg_id=444",
            "SELECT COUNT(*) FROM annunci WHERE venditore_id=444",
            "SELECT COUNT(*) FROM ordini WHERE compratore_id=111")))
    prova("le foto stanno nella cartella usa-e-getta, non nella foto/ del repo",
          True, os.path.exists(os.path.join(cartella, f"av_{codice}_1.jpg")))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
