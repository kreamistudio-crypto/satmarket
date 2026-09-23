# -*- coding: utf-8 -*-
"""
LA PAGINA IN BOZZA, SUL SERVER VERO (23 set 2026).

Le pagine dei negozi consigliati nascono in BOZZA: le vedono i
moderatori e nessun altro, fuori da vetrina, ricerca, link condivisi e
anteprime finche' un moderatore non le pubblica. `prove.py` guarda i
pezzi estratti e il renderer; qui si fa la domanda che solo il server
VERO risponde — cosa esce DAVVERO dalle rotte, a chi, e quando.

LA SONDA E' IL TESTO, non una chiave: le frasi della bozza si prendono
dal catalogo VERO (`racconti.py`) e si cercano nella risposta INTERA di
ogni porta — il JSON del negozio, la pagina coi meta delle anteprime,
la home col link della leva, la mappa del sito. Una chiave assente
direbbe «qui non c'e' il campo»; una frase assente dice «qui la bozza
non c'e'», che e' la promessa.

LE PORTE CHE SI BUSSANO, e il verso di ognuna:
  - la rotta admin: 401 all'anonimo, 403 a chi non e' moderatore,
    il testo intero al moderatore;
  - `/api/negozio`: MAI la bozza, a nessuno — nemmeno al moderatore
    che bussa col suo initData, nemmeno al venditore del negozio;
  - la pagina `/negozio/{codice}` e la home con `?bozza=`: niente, ne'
    prima ne' dopo la pubblicazione (l'anteprima social di un negozio
    resta quella del brand, la scelta gia' fatta per To The Mooon);
  - il gesto: pubblicare chiede un venditore vero, e dopo il racconto
    esce a chiunque apra QUEL negozio e a nessun altro; tornare in
    bozza lo toglie di nuovo.

IL CATALOGO SI COLLEGA IN MEMORIA, e non e' un trucco: nel repo il
codice del venditore e' vuoto (va collegato quando si sa di chi e'), e
la prima meta' del giro prova proprio quello stato — pubblicare si
rifiuta. Poi il codice si scrive nel dizionario gia' importato dal
server, lo stesso oggetto che le rotte leggono.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete: le notifiche ai
moderatori le raccoglie il banco.

USO:  python collaudo_racconti_bozza.py
"""

import sys

import collaudo_lnbits_muto as banco

prova = banco.prova
SLUG = "una-garlanda"
ANONIMO = {}
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
MODERATORE = {"X-Tg-Init-Data": "collaudo:999:Admin"}
VENDITORE = {"X-Tg-Init-Data": "collaudo:222:Manuele"}


def main():
    print("=" * 58)
    print("  LA PAGINA IN BOZZA — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    SRV = banco.SRV
    c = TestClient(SRV.app)
    cat = SRV.RACCONTI_NEGOZI[SLUG]
    # LE SPIE, dal catalogo vero: il sottotitolo (il titolo che si
    # legge), un pezzo dell'apertura e la firma in fondo
    firma = next(b for b in cat["blocchi"] if b["t"] == "firma")
    spie = [cat["sottotitolo"], cat["intro"][:60], firma["p"]]

    def trovate(testo):
        return [s for s in spie if s in testo]

    def racconto_di(chi, h):
        r = c.get(f"/api/negozio/{chi}?limit=12", headers=h)
        return r.status_code, r.json()["venditore"].get("racconto"), r.text

    print("\n[la porta admin: chi la puo' aprire]")
    prova("l'anonimo prende 401", 401,
          c.get("/api/admin/racconti", headers=ANONIMO).status_code)
    prova("chi non e' moderatore prende 403", 403,
          c.get("/api/admin/racconti", headers=COMPRATORE).status_code)
    r = c.get("/api/admin/racconti", headers=MODERATORE)
    prova("il moderatore la apre", 200, r.status_code)
    lista = {x["slug"]: x for x in r.json()["racconti"]}
    d = lista.get(SLUG) or {}
    prova("...e ci trova la pagina, in bozza", "bozza", d.get("stato"))
    prova("...col testo intero, preso dal catalogo",
          (cat["sottotitolo"], len(cat["blocchi"])),
          (d.get("sottotitolo"), len(d.get("blocchi") or [])))
    prova("...e col venditore ancora da collegare", ("", None),
          (d.get("negozio"), d.get("venditore")))
    prova("il gesto di chi non e' moderatore prende 403, prima del body",
          403, c.post(f"/api/admin/racconti/{SLUG}", headers=COMPRATORE,
                      content=b"non e' nemmeno json").status_code)
    prova("un esito inventato e' un 400", 400,
          c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
                 json={"esito": "boh"}).status_code)
    prova("...e una pagina che non esiste un 404", 404,
          c.post("/api/admin/racconti/mai-vista", headers=MODERATORE,
                 json={"esito": "pubblica"}).status_code)

    print("\n[senza venditore non si pubblica]")
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("pubblicare si rifiuta (409)", 409, r.status_code)
    prova("...e dice perche'", True, "venditore" in r.json().get("detail", ""))
    prova("...e la pagina resta in bozza", "bozza",
          SRV.racconto_stato(SLUG))

    print("\n[il venditore collegato, la pagina ancora in bozza]")
    # il venditore nasce dalla porta di sempre: la sua prima richiesta
    c.get("/api/me", headers=VENDITORE)
    con = SRV.db()
    codice = con.execute("SELECT negozio FROM utenti WHERE tg_id=222"
                         ).fetchone()["negozio"]
    con.close()
    prova("il venditore di prova ha il suo codice", 8, len(codice or ""))
    cat["negozio"] = codice
    for nome, h in (("all'anonimo", ANONIMO), ("a chi compra", COMPRATORE),
                    ("al moderatore che bussa col suo initData", MODERATORE),
                    ("al venditore stesso", VENDITORE)):
        st, rac, testo = racconto_di(codice, h)
        prova(f"il negozio {nome} risponde senza la bozza",
              (200, None, []), (st, rac, trovate(testo)))
    r = c.get(f"/negozio/{codice}")
    prova("la pagina del negozio (i meta delle anteprime) non la nomina",
          (200, []), (r.status_code, trovate(r.text)))
    r = c.get(f"/?bozza={SLUG}")
    prova("la home col link della leva nemmeno", (200, []),
          (r.status_code, trovate(r.text)))
    r = c.get("/sitemap.xml")
    prova("...e nemmeno la mappa del sito", [], trovate(r.text))
    d = {x["slug"]: x for x in c.get("/api/admin/racconti",
         headers=MODERATORE).json()["racconti"]}[SLUG]
    prova("il pannello riconosce il venditore collegato",
          {"trovato": True, "nome": "Manuele"}, d.get("venditore"))

    print("\n[il gesto: pubblica]")
    prima = len(banco.AVVISI)
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("il moderatore pubblica", (200, "pubblicato"),
          (r.status_code, r.json().get("stato")))
    prova("...e gli altri moderatori lo sanno", True,
          any("pubblicata" in a for a in banco.AVVISI[prima:]))
    st, rac, _ = racconto_di(codice, ANONIMO)
    prova("adesso il negozio la mostra a chiunque", True, bool(rac))
    rac = rac or {}
    prova("...col testo del catalogo e lo slug delle foto",
          (SLUG, cat["sottotitolo"], len(cat["blocchi"]), cat["emoji"]),
          (rac.get("slug"), rac.get("sottotitolo"),
           len(rac.get("blocchi") or []), rac.get("emoji")))
    prova("...e nient'altro che le chiavi dichiarate",
          sorted(SRV.CAMPI_RACCONTO + ("slug",)), sorted(rac))
    _, rac_u, _ = racconto_di("manuele", ANONIMO)
    prova("...anche arrivando dallo username", SLUG,
          (rac_u or {}).get("slug"))
    c.get("/api/me", headers=COMPRATORE)
    con = SRV.db()
    altro = con.execute("SELECT negozio FROM utenti WHERE tg_id=111"
                        ).fetchone()["negozio"]
    con.close()
    _, rac_a, testo_a = racconto_di(altro, ANONIMO)
    prova("...e su un altro negozio no", (None, []),
          (rac_a, trovate(testo_a)))
    r = c.get(f"/negozio/{codice}")
    prova("l'anteprima social del negozio resta quella del brand", [],
          trovate(r.text))

    print("\n[il gesto: rimetti in bozza]")
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "bozza"})
    prova("il moderatore la rimette in bozza", (200, "bozza"),
          (r.status_code, r.json().get("stato")))
    st, rac, testo = racconto_di(codice, ANONIMO)
    prova("...e dal negozio sparisce subito", (None, []),
          (rac, trovate(testo)))
    prova("...mentre il moderatore la ritrova nella sua porta", "bozza",
          {x["slug"]: x for x in c.get("/api/admin/racconti",
           headers=MODERATORE).json()["racconti"]}[SLUG].get("stato"))

    print("\n[un codice che non e' di nessuno]")
    cat["negozio"] = "00000000"
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("pubblicare si rifiuta anche li' (409)", 409, r.status_code)
    d = {x["slug"]: x for x in c.get("/api/admin/racconti",
         headers=MODERATORE).json()["racconti"]}[SLUG]
    prova("...e il pannello lo dice prima del tocco",
          {"trovato": False, "nome": ""}, d.get("venditore"))
    cat["negozio"] = ""

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
