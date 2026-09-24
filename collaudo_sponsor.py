# -*- coding: utf-8 -*-
"""
PIU' NEGOZI SPONSORIZZATI IN «DA SCOPRIRE», SUL SERVER VERO (24 set 2026).

Lo spazio in vetrina reggeva un negozio alla volta, e solo quelli del
catalogo del client (To The Mooon). Da questo cantiere ogni negozio ha il
SUO spazio — acceso, spento, la sua scadenza — le card stanno in fila
nell'ordine deciso da noi, e anche le pagine del server (`racconti.py`)
si possono accendere: la loro card compare solo a pagina PUBBLICATA.
`prove.py` gira i giudici estratti con un'impostazione di cartone; qui si
fa la domanda che solo il server VERO risponde — cosa esce DAVVERO dalla
busta di prima pagina che riceve chiunque apra la home, dopo i gesti
veri: il comando del bot, la pubblicazione dal pannello, l'orologio.

IL GIRO, nell'ordine in cui lo farebbe Andrea:
  - `/sponsor` nudo, da admin: lo stato di tutti gli spazi, e a chi non
    e' admin la risposta di un messaggio qualunque;
  - accende To The Mooon e Un tempo per te — che e' ancora IN BOZZA:
    nella busta resta solo To The Mooon, e il bot l'ha detto;
  - il moderatore pubblica la pagina: due card, prima Un tempo per te e
    poi To The Mooon, col codice del negozio risolto e mai il tg_id; il
    banner si serve;
  - `/sponsor ordine` rovescia la fila;
  - la scadenza di uno non tocca l'altro, nei due versi;
  - `/sponsor <slug> spento` spegne quello solo, `/sponsor spento` tutti;
  - il preavviso: uno per spazio, e una volta sola per scadenza;
  - le aperture si contano per spazio, e solo se QUELLO e' acceso;
  - la riga di ieri (`sponsor_slug` + `sponsor_fino`) tiene acceso lo
    spazio acceso prima del deploy;
  - rimessa in bozza, la card sparisce subito.

IL VENDITORE DELLA PAGINA E' QUELLO DI COLLAUDO (222), non quello vero
del catalogo: il legame si riscrive in memoria per il giro e si rimette
com'era alla fine — un tg_id vero non deve finire nemmeno in un database
usa-e-getta. Niente parla con Telegram: il `config` finto e il nodo finto
li installa `avvio()` del banco PRIMA dell'import di server, il bot e le
notifiche li raccoglie il banco, e in CI c'e' la gabbia senza rete di
`collaudi_ci.py`.

USO:  python collaudo_sponsor.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
ANONIMO = {}
MODERATORE = {"X-Tg-Init-Data": "collaudo:999:Admin"}
VENDITORE = {"X-Tg-Init-Data": "collaudo:222:Venditore"}
PAGINA = "un-tempo-per-te"
CASA = "to-the-moon"
BOT = []            # quel che il bot ha risposto, un testo per messaggio


def main():
    print("=" * 58)
    print("  PIU' NEGOZI SPONSORIZZATI — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    SRV = banco.SRV

    async def bot_finto(metodo, dati, *a, **k):
        BOT.append(dati.get("text", ""))
        return {"ok": True}

    SRV.bot_api = bot_finto
    c = TestClient(SRV.app)
    cat = SRV.RACCONTI_NEGOZI[PAGINA]
    salvato = {k: cat.get(k) for k in ("negozio", "venditore_tg")}
    cat["negozio"], cat["venditore_tg"] = "", 222
    try:
        giro(c, SRV, cat)
    finally:
        for k, v in salvato.items():
            if v is None:
                cat.pop(k, None)
            else:
                cat[k] = v

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


def giro(c, SRV, cat):
    def bot(testo, chi=999, username=""):
        BOT.clear()
        asyncio.run(SRV.comando_sponsor(
            {"id": chi, "username": username}, testo))
        return " ".join(BOT)

    def busta():
        """la fila come la riceve chiunque apra la home: la busta di prima
        pagina, da anonimo, col `limit` che il client manda sempre"""
        r = c.get("/api/listings?limit=12", headers=ANONIMO)
        return r.json().get("sponsorizzati"), r.text

    def slug_in(fila):
        return [x.get("slug") for x in (fila or [])]

    def scadenza(slug, quando):
        """l'orologio che passa: la riga si riscrive come la scriverebbe il
        tempo, e la cache si rilegge a freddo"""
        SRV.scrivi_impostazione(f"sponsor_fino:{slug}", str(int(quando)))
        SRV._SPONSOR = None

    print("\n[il vocabolario e lo stato]")
    prova("il vocabolario: prima la pagina del server, poi To The Mooon",
          (PAGINA, CASA), SRV.slug_sponsorizzabili())
    fila, _ = busta()
    prova("a spazi spenti la busta porta una fila vuota", [], fila)
    t = bot("/sponsor")
    prova("/sponsor nudo dice lo stato di tutti, nell'ordine", True,
          t.index(PAGINA) < t.index(CASA) and t.count("spento") >= 2)
    prova("...e dice che la pagina e' in bozza", True,
          "pagina in bozza" in t)
    prova("...e insegna i gesti nuovi: uno, tutti, l'ordine", True,
          all(x in t for x in (f"/sponsor {PAGINA} 30",
                               f"/sponsor {PAGINA} spento",
                               "/sponsor spento", "/sponsor ordine")))
    t = bot("/sponsor", chi=111)
    prova("a chi non e' admin il comando non esiste", False,
          "Spazi in vetrina" in t)

    print("\n[accesi tutt'e due, la pagina in bozza]")
    t = bot(f"/sponsor {CASA} 30")
    prova("To The Mooon si accende per 30 giorni", True,
          CASA in t and "30" in t and "in vetrina" in t)
    t = bot(f"/sponsor {PAGINA} 30")
    prova("Un tempo per te si accende anche in bozza...", True,
          PAGINA in t and "in vetrina" in t)
    prova("...e il bot dice che la card compare solo pubblicata", True,
          "IN BOZZA" in t and "scadenza corre" in t)
    prova("i due spazi sono accesi, nell'ordine di partenza", [PAGINA, CASA],
          SRV.sponsor_accesi())
    fila, testo = busta()
    prova("in bozza la busta porta solo To The Mooon", [{"slug": CASA}], fila)
    prova("...e il banner della bozza non si serve", 404,
          c.get(f"/assets/scoprire/{PAGINA}.webp").status_code)

    print("\n[pubblicata: due card]")
    # il venditore di collaudo nasce qui, col suo codice
    c.get("/api/me/racconti", headers=VENDITORE)
    con = SRV.db()
    codice = con.execute("SELECT negozio FROM utenti WHERE tg_id=222"
                         ).fetchone()["negozio"]
    con.close()
    r = c.post(f"/api/admin/racconti/{PAGINA}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("il moderatore pubblica la pagina", (200, "pubblicato"),
          (r.status_code, r.json().get("stato")))
    fila, testo = busta()
    prova("due card, prima Un tempo per te e poi To The Mooon, col codice "
          "risolto", [{"slug": PAGINA, "titolo": cat["titolo"],
                       "emoji": cat["emoji"], "negozio": codice},
                      {"slug": CASA}], fila)
    prova("...e il tg_id del venditore non viaggia", False,
          '"venditore_tg"' in testo)
    r = c.get(f"/assets/scoprire/{PAGINA}.webp")
    prova("il banner della pagina pubblicata si serve, WebP", (200, True),
          (r.status_code, r.headers.get("content-type", "").startswith(
              "image/webp")))
    r = c.get(f"/assets/scoprire/{CASA}.webp")
    prova("...e quello di To The Mooon pure", 200, r.status_code)
    t = bot("/sponsor")
    prova("/sponsor nudo li dice accesi tutt'e due, con la data", 2,
          t.count("in vetrina fino al"))
    prova("...e la bozza non la dice piu'", False, "pagina in bozza" in t)

    print("\n[l'ordine]")
    t = bot(f"/sponsor ordine {CASA} {PAGINA}")
    prova("/sponsor ordine rovescia la fila", [CASA, PAGINA],
          slug_in(busta()[0]))
    prova("...e il bot la ridice", True,
          "1. <b>" + CASA in t and "2. <b>" + PAGINA in t)
    t = bot(f"/sponsor ordine {PAGINA} mai-visto")
    prova("un nome inventato nell'ordine non cambia niente", (True,
          [CASA, PAGINA]), ("mai-visto" in t, slug_in(busta()[0])))
    t = bot("/sponsor ordine")
    prova("...e un ordine vuoto nemmeno, e il bot fa l'esempio", (True,
          [CASA, PAGINA]), ("/sponsor ordine" in t, slug_in(busta()[0])))
    bot(f"/sponsor ordine {PAGINA}")
    prova("nominarne uno lo mette in testa, gli altri seguono",
          [PAGINA, CASA], slug_in(busta()[0]))

    print("\n[la scadenza di uno non tocca l'altro]")
    ora = int(time.time())
    fino_casa = SRV.sponsor_fino(CASA)
    scadenza(CASA, ora - 1)
    prova("scaduto To The Mooon, resta Un tempo per te", [PAGINA],
          slug_in(busta()[0]))
    scadenza(CASA, fino_casa)
    fino_pag = SRV.sponsor_fino(PAGINA)
    scadenza(PAGINA, ora - 1)
    prova("scaduto Un tempo per te, resta To The Mooon", [CASA],
          slug_in(busta()[0]))
    scadenza(PAGINA, fino_pag)
    prova("...e rinnovati tornano tutt'e due", [PAGINA, CASA],
          slug_in(busta()[0]))

    print("\n[le aperture, per spazio]")
    prima = SRV.aperture_sponsor(PAGINA)
    c.get(f"/api/negozio/{codice}?limit=12&da=sponsor:{PAGINA}")
    prova("un'apertura dalla card si conta sul suo spazio", prima + 1,
          SRV.aperture_sponsor(PAGINA))
    c.get(f"/api/negozio/{codice}?limit=12&da=sponsor:mai-visto")
    c.get(f"/api/negozio/{codice}?limit=12&da=sponsor")
    prova("...e uno slug inventato o il «sponsor» di ieri non contano",
          (prima + 1, 0), (SRV.aperture_sponsor(PAGINA),
                           SRV.aperture_sponsor("mai-visto")))

    print("\n[il preavviso: uno per spazio]")
    banco.AVVISI.clear()
    scadenza(CASA, ora + 3600)
    scadenza(PAGINA, ora + 7200)
    asyncio.run(SRV.avvisa_scadenza_sponsor())
    prova("due spazi in scadenza: due preavvisi, uno per spazio",
          [True, True], [any(s in a for a in banco.AVVISI)
                         for s in (f"di {CASA} scade", f"di {PAGINA} scade")])
    prova("...e ognuno dice come rinnovare il suo", True,
          all(f"/sponsor {s} 30" in " ".join(banco.AVVISI)
              for s in (CASA, PAGINA)))
    banco.AVVISI.clear()
    asyncio.run(SRV.avvisa_scadenza_sponsor())
    prova("...e una volta sola per scadenza", [], banco.AVVISI)
    scadenza(CASA, ora + 3000)
    asyncio.run(SRV.avvisa_scadenza_sponsor())
    prova("un rinnovo (scadenza nuova) risuona solo per il suo", 1,
          len(banco.AVVISI))
    prova("...ed e' quello giusto", True, f"di {CASA} scade" in
          " ".join(banco.AVVISI))
    scadenza(CASA, fino_casa)
    scadenza(PAGINA, fino_pag)

    print("\n[spegnere: uno, poi tutti]")
    t = bot(f"/sponsor {CASA} spento")
    prova("/sponsor <slug> spento spegne quello solo", [PAGINA],
          slug_in(busta()[0]))
    prova("...e il bot dice che gli altri restano", True,
          "gli altri spazi restano" in t)
    bot(f"/sponsor {CASA} 30")
    prova("riacceso torna al suo posto nell'ordine", [PAGINA, CASA],
          slug_in(busta()[0]))
    t = bot("/sponsor spento")
    prova("/sponsor spento li spegne tutti", ([], True),
          (busta()[0], "Tolti tutti" in t))
    t = bot("/sponsor mai-visto 30")
    prova("uno slug inventato: il bot dice di no e nomina quelli veri",
          (True, True, []), ("Non conosco" in t, PAGINA in t and CASA in t,
                             busta()[0]))
    t = bot(f"/sponsor {PAGINA} 999")
    prova("...e i giorni fuori tetto pure", (True, []),
          ("I giorni vanno da 1" in t, busta()[0]))

    print("\n[la riga di ieri]")
    con = SRV.db()
    con.execute("DELETE FROM impostazioni WHERE chiave LIKE 'sponsor_fino:%'")
    con.commit()
    con.close()
    SRV.scrivi_impostazione("sponsor_slug", CASA)
    SRV.scrivi_impostazione("sponsor_fino", str(ora + 86400))
    SRV._SPONSOR = None
    prova("lo spazio acceso prima del deploy resta acceso", [{"slug": CASA}],
          busta()[0])
    bot(f"/sponsor {CASA} spento")
    prova("...e il gesto nuovo lo spegne davvero", [], busta()[0])

    print("\n[rimessa in bozza]")
    bot(f"/sponsor {PAGINA} 30")
    prova("la pagina pubblicata e accesa ha la sua card", [PAGINA],
          slug_in(busta()[0]))
    r = c.post(f"/api/admin/racconti/{PAGINA}", headers=MODERATORE,
               json={"esito": "bozza"})
    prova("il moderatore la rimette in bozza", (200, "bozza"),
          (r.status_code, r.json().get("stato")))
    prova("...e la card sparisce subito, con lo spazio ancora acceso",
          ([], [PAGINA]), (busta()[0], SRV.sponsor_accesi()))
    bot("/sponsor spento")


if __name__ == "__main__":
    sys.exit(main())
