# -*- coding: utf-8 -*-
"""
LA PAGINA IN BOZZA, SUL SERVER VERO (23 set 2026).

Le pagine dei negozi consigliati nascono in BOZZA: le vedono i
moderatori e il VENDITORE della pagina — lui sul suo negozio — e
nessun altro, fuori da vetrina, ricerca, link condivisi e anteprime
finche' un moderatore non le pubblica. `prove.py` guarda i pezzi
estratti e il renderer; qui si fa la domanda che solo il server VERO
risponde — cosa esce DAVVERO dalle rotte, a chi, e quando.

LA SONDA E' IL TESTO, non una chiave: le frasi della bozza si prendono
dal catalogo VERO (`racconti.py`) e si cercano nella risposta INTERA di
ogni porta — il JSON del negozio, la pagina coi meta delle anteprime,
la home col link della leva, la mappa del sito. Una chiave assente
direbbe «qui non c'e' il campo»; una frase assente dice «qui la bozza
non c'e'», che e' la promessa. E la stessa sonda cerca il tg_id del
venditore, che il catalogo porta e che NESSUNA risposta deve portare.

LE PORTE CHE SI BUSSANO, e il verso di ognuna:
  - la porta admin: 401 all'anonimo, 403 a chi non e' moderatore (il
    venditore compreso), il testo intero al moderatore;
  - la porta del venditore (`/api/me/racconti`): 401 all'anonimo, una
    lista VUOTA a un altro utente, la bozza al venditore della pagina;
  - `/api/negozio`: MAI la bozza, a nessuno — nemmeno al moderatore e
    nemmeno al venditore, che la bozza sul suo negozio la riceve dalla
    porta sua;
  - la pagina `/negozio/{codice}`, la home con `?bozza=` e la mappa del
    sito: niente, ne' prima ne' dopo la pubblicazione (l'anteprima
    social di un negozio resta quella del brand, la scelta gia' fatta
    per To The Mooon);
  - il gesto: pubblicare lo fa solo il moderatore e chiede un venditore
    vero; dopo, il racconto esce a chiunque apra QUEL negozio e a
    nessun altro; tornare in bozza lo toglie di nuovo;
  - I CONSIGLIATI (set 2026): la busta di prima pagina — quella che
    riceve chiunque apra la home — porta la pagina solo PUBBLICATA e col
    LOGO nel catalogo, col codice del negozio risolto e mai il tg_id;
    in bozza no, nemmeno col logo; e la rotta del logo di una bozza
    risponde 404. La pagina /consigliati risponde coi suoi meta, senza
    indicizzarsi e fuori dalla mappa del sito.

IL VENDITORE E' QUELLO VERO DEL CATALOGO, legato col tg_id: l'utente
nasce qui, sul database usa-e-getta, alla sua prima richiesta, con
l'identita' di collaudo di quel tg_id. Niente parla con Telegram: il
`config` finto e il nodo finto li installa `avvio()` del banco, PRIMA
dell'import di server, e le notifiche le raccoglie il banco — in CI,
in piu', c'e' la gabbia senza rete di `collaudi_ci.py`.

USO:  python collaudo_racconti_bozza.py
"""

import sys

import collaudo_lnbits_muto as banco

prova = banco.prova
SLUG = "una-garlanda"
ANONIMO = {}
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
MODERATORE = {"X-Tg-Init-Data": "collaudo:999:Admin"}


def main():
    print("=" * 58)
    print("  LA PAGINA IN BOZZA — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    SRV = banco.SRV
    c = TestClient(SRV.app)
    cat = SRV.RACCONTI_NEGOZI[SLUG]
    TG = int(cat["venditore_tg"])
    VENDITORE = {"X-Tg-Init-Data": f"collaudo:{TG}:Manuele"}
    # LE SPIE, dal catalogo vero: il sottotitolo (il titolo che si
    # legge), un pezzo dell'apertura, la firma in fondo — e il tg_id
    firma = next(b for b in cat["blocchi"] if b["t"] == "firma")
    spie = [cat["sottotitolo"], cat["intro"][:60], firma["p"]]

    def trovate(testo):
        return [s for s in spie if s in testo]

    def racconto_di(chi, h):
        r = c.get(f"/api/negozio/{chi}?limit=12", headers=h)
        return r.status_code, r.json()["venditore"].get("racconto"), r.text

    def elenco_admin():
        r = c.get("/api/admin/racconti", headers=MODERATORE)
        return {x["slug"]: x for x in r.json()["racconti"]}, r.text

    def consigliati():
        """la lista dei Consigliati come la riceve chiunque apra la home:
        la busta di prima pagina, da anonimo, col `limit` che il client
        manda sempre (senza, la rotta risponde la lista nuda dei client
        di ieri, e la busta non c'e'); le sole voci di QUESTA pagina, e
        il testo intero della risposta per le spie"""
        r = c.get("/api/listings?limit=12", headers=ANONIMO)
        lista = r.json().get("consigliati")
        return (r.status_code, isinstance(lista, list),
                [x for x in (lista or []) if x.get("slug") == SLUG], r.text)

    logo_salvato = cat.get("logo")

    print("\n[la porta admin: chi la puo' aprire]")
    prova("l'anonimo prende 401", 401,
          c.get("/api/admin/racconti", headers=ANONIMO).status_code)
    prova("chi non e' moderatore prende 403", 403,
          c.get("/api/admin/racconti", headers=COMPRATORE).status_code)
    prova("...e il venditore pure: la sua porta e' un'altra", 403,
          c.get("/api/admin/racconti", headers=VENDITORE).status_code)
    lista, testo = elenco_admin()
    d = lista.get(SLUG) or {}
    prova("il moderatore la apre, in bozza", "bozza", d.get("stato"))
    prova("...col testo intero, preso dal catalogo",
          (cat["sottotitolo"], len(cat["blocchi"])),
          (d.get("sottotitolo"), len(d.get("blocchi") or [])))
    prova("...e il tg_id del venditore non esce nemmeno da li'", False,
          str(TG) in testo)
    prova("il gesto di chi non e' moderatore prende 403, prima del body",
          403, c.post(f"/api/admin/racconti/{SLUG}", headers=COMPRATORE,
                      content=b"non e' nemmeno json").status_code)
    prova("...e quello del venditore pure: pubblica solo il moderatore",
          403, c.post(f"/api/admin/racconti/{SLUG}", headers=VENDITORE,
                      json={"esito": "pubblica"}).status_code)
    prova("un esito inventato e' un 400", 400,
          c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
                 json={"esito": "boh"}).status_code)
    prova("...e una pagina che non esiste un 404", 404,
          c.post("/api/admin/racconti/mai-vista", headers=MODERATORE,
                 json={"esito": "pubblica"}).status_code)

    print("\n[un venditore scritto nel catalogo che non ha un negozio]")
    # Il 403 del venditore, qui sopra, e' passato da `verifica_utente`,
    # che l'ha gia' fatto nascere: si toglie la riga per provare il caso
    # di un tg_id scritto per una persona che su Barattolo non c'e'.
    con = SRV.db()
    con.execute("DELETE FROM utenti WHERE tg_id=?", (TG,))
    con.commit()
    con.close()
    lista, _ = elenco_admin()
    prova("il pannello lo dice prima del tocco", ("", {"trovato": False,
          "nome": ""}), (lista[SLUG].get("negozio"),
                        lista[SLUG].get("venditore")))
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("pubblicare si rifiuta (409)", 409, r.status_code)
    prova("...e dice perche'", True, "venditore" in r.json().get("detail", ""))
    salvato = cat.pop("venditore_tg")
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("...e senza nessun venditore scritto anche (409)", 409,
          r.status_code)
    cat["venditore_tg"] = salvato
    prova("...e la pagina resta in bozza", "bozza",
          SRV.racconto_stato(SLUG))

    print("\n[il venditore: la sua porta]")
    prova("la porta del venditore all'anonimo: 401", 401,
          c.get("/api/me/racconti", headers=ANONIMO).status_code)
    r = c.get("/api/me/racconti", headers=COMPRATORE)
    prova("...a un altro utente: una lista vuota, e nessuna frase", (200, [], []),
          (r.status_code, r.json().get("racconti"), trovate(r.text)))
    # la prima richiesta del venditore lo fa nascere (col suo codice)
    r = c.get("/api/me/racconti", headers=VENDITORE)
    mie = r.json().get("racconti") or []
    con = SRV.db()
    codice = con.execute("SELECT negozio FROM utenti WHERE tg_id=?",
                         (TG,)).fetchone()["negozio"]
    con.close()
    prova("il venditore del catalogo ha il suo negozio", 8, len(codice or ""))
    prova("...e dalla sua porta riceve la SUA bozza, col codice risolto",
          [(SLUG, "bozza", codice, cat["sottotitolo"])],
          [(x.get("slug"), x.get("stato"), x.get("negozio"),
            x.get("sottotitolo")) for x in mie])
    prova("...e il tg_id non viaggia", (False, False),
          (str(TG) in r.text, any("venditore_tg" in x for x in mie)))

    print("\n[la bozza non esce da nessun'altra parte]")
    for nome, h in (("all'anonimo", ANONIMO), ("a chi compra", COMPRATORE),
                    ("al moderatore che bussa col suo initData", MODERATORE),
                    ("al venditore stesso: la riceve dalla porta sua",
                     VENDITORE)):
        st, rac, testo = racconto_di(codice, h)
        prova(f"il negozio {nome} risponde senza la bozza",
              (200, None, [], False),
              (st, rac, trovate(testo), str(TG) in testo))
    r = c.get(f"/negozio/{codice}")
    prova("la pagina del negozio (i meta delle anteprime) non la nomina",
          (200, []), (r.status_code, trovate(r.text)))
    r = c.get(f"/?bozza={SLUG}")
    prova("la home col link della leva nemmeno", (200, []),
          (r.status_code, trovate(r.text)))
    r = c.get("/sitemap.xml")
    prova("...e nemmeno la mappa del sito", [], trovate(r.text))
    lista, testo = elenco_admin()
    prova("il pannello riconosce il venditore, col codice risolto",
          (codice, {"trovato": True, "nome": "Manuele"}),
          (lista[SLUG].get("negozio"), lista[SLUG].get("venditore")))

    print("\n[fra i Consigliati: la bozza no]")
    st, e_lista, mia, testo = consigliati()
    prova("la busta di prima pagina porta la lista dei Consigliati, e la "
          "bozza non c'e'", (200, True, [], []),
          (st, e_lista, mia, trovate(testo)))
    # IL CASO CHE CONTA: la bozza col suo LOGO gia' nel catalogo — cioe'
    # pronta in tutto tranne che nella pubblicazione. Resta fuori.
    cat["logo"] = True
    st, e_lista, mia, testo = consigliati()
    prova("...nemmeno col logo nel catalogo: in bozza non entra", ([], []),
          (mia, trovate(testo)))
    prova("...e il suo logo non si serve a nessuno", 404,
          c.get(f"/assets/consigliati/{SLUG}.webp").status_code)
    cat["logo"] = logo_salvato
    r = c.get("/assets/consigliati/to-the-moon.webp")
    prova("il logo dello spazio in vetrina si serve, WebP", (200, True),
          (r.status_code, r.headers.get("content-type", "").startswith(
              "image/webp")))
    prova("...e un nome fuori forma o inventato no", [404, 404],
          [c.get(f"/assets/consigliati/{n}").status_code
           for n in ("to-the-moon.png", "mai-visto.webp")])
    r = c.get("/consigliati")
    prova("la pagina /consigliati risponde coi suoi meta, e non si "
          "indicizza", (200, True, True, []),
          (r.status_code, "Consigliati — Barattolo" in r.text,
           'content="noindex,follow"' in r.text, trovate(r.text)))
    prova("...e sta fuori dalla mappa del sito", False,
          "/consigliati" in c.get("/sitemap.xml").text)

    print("\n[il gesto: pubblica]")
    prima = len(banco.AVVISI)
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "pubblica"})
    prova("il moderatore pubblica", (200, "pubblicato"),
          (r.status_code, r.json().get("stato")))
    prova("...e gli altri moderatori lo sanno", True,
          any("pubblicata" in a for a in banco.AVVISI[prima:]))
    st, rac, testo = racconto_di(codice, ANONIMO)
    rac = rac or {}
    prova("adesso il negozio la mostra a chiunque, col suo codice",
          (SLUG, codice, cat["sottotitolo"], len(cat["blocchi"])),
          (rac.get("slug"), rac.get("negozio"), rac.get("sottotitolo"),
           len(rac.get("blocchi") or [])))
    prova("...con le sole chiavi dichiarate, e il tg_id a casa",
          (sorted(SRV.CAMPI_RACCONTO + ("slug",)), False),
          (sorted(rac), str(TG) in testo))
    _, rac_u, _ = racconto_di("manuele", ANONIMO)
    prova("...anche arrivando dallo username", SLUG,
          (rac_u or {}).get("slug"))
    c.get("/api/me/racconti", headers=COMPRATORE)
    con = SRV.db()
    altro = con.execute("SELECT negozio FROM utenti WHERE tg_id=111"
                        ).fetchone()["negozio"]
    con.close()
    _, rac_a, testo_a = racconto_di(altro, ANONIMO)
    prova("...e sul negozio di un altro no", (None, []),
          (rac_a, trovate(testo_a)))
    r = c.get("/api/me/racconti", headers=VENDITORE)
    prova("la porta del venditore la dice pubblicata", ["pubblicato"],
          [x.get("stato") for x in r.json().get("racconti") or []])
    r = c.get(f"/negozio/{codice}")
    prova("l'anteprima social del negozio resta quella del brand", [],
          trovate(r.text))

    print("\n[fra i Consigliati: pubblicata, e col logo]")
    st, e_lista, mia, testo = consigliati()
    prova("pubblicata ma SENZA logo, fra i Consigliati non entra", [], mia)
    cat["logo"] = True
    # IL RITOCCO DEL LOGO VIAGGIA CON LUI (set 2026): un valore diverso
    # dallo zero del catalogo, o la prova non saprebbe dire se esce
    giu_salvato = cat.get("logo_giu", 0)
    cat["logo_giu"] = 3
    st, e_lista, mia, testo = consigliati()
    prova("...col logo si': col codice del negozio risolto, il nome, "
          "l'emoji e il ritocco del logo",
          [{"slug": SLUG, "titolo": cat["titolo"], "emoji": cat["emoji"],
            "negozio": codice, "logo_giu": 3}], mia)
    cat["logo_giu"] = giu_salvato
    prova("...e ne' il tg_id ne' il testo della storia viaggiano", (False, []),
          (str(TG) in testo, trovate(testo)))

    print("\n[il gesto: rimetti in bozza]")
    r = c.post(f"/api/admin/racconti/{SLUG}", headers=MODERATORE,
               json={"esito": "bozza"})
    prova("il moderatore la rimette in bozza", (200, "bozza"),
          (r.status_code, r.json().get("stato")))
    st, rac, testo = racconto_di(codice, ANONIMO)
    prova("...e dal negozio sparisce subito", (None, []),
          (rac, trovate(testo)))
    r = c.get("/api/me/racconti", headers=VENDITORE)
    prova("...mentre il venditore la ritrova in bozza dalla sua porta",
          ["bozza"], [x.get("stato") for x in r.json().get("racconti") or []])
    st, e_lista, mia, testo = consigliati()
    prova("...e dai Consigliati esce subito, anche col logo", [], mia)
    cat["logo"] = logo_salvato

    print("\n[la precedenza: col codice nel catalogo il tg_id non conta]")
    cat["negozio"] = "00000000"
    r = c.get("/api/me/racconti", headers=VENDITORE)
    prova("un codice di nessuno scritto accanto: il venditore non la vede "
          "piu'", [], r.json().get("racconti"))
    lista, _ = elenco_admin()
    prova("...e il pannello dice che quel venditore non ha un negozio",
          {"trovato": False, "nome": ""}, lista[SLUG].get("venditore"))
    cat["negozio"] = codice
    r = c.get("/api/me/racconti", headers=VENDITORE)
    prova("col SUO codice scritto nel catalogo, la vede di nuovo",
          [SLUG], [x.get("slug") for x in r.json().get("racconti") or []])
    cat["negozio"] = ""

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
