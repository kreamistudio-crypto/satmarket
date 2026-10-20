# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ISTANZA DI PROVA (19-20 ott 2026, cantiere «collaudo-vm»,
richieste di Andrea; il disegno e' docs/STUDIO-ISTANZA-PROVA-2026-10-08.md).

`prove.py` prova i giudici puri (la lista, il cookie, il guscio, le
righe della pagina) e le leve lette dal config; qui risponde il SERVER
VERO, col middleware davanti a tutte le rotte:
  - a lista vuota (la produzione) tutto e' come prima: la vetrina si
    legge senza identita', nessun cookie nuovo, la pagina e' quella di
    sempre;
  - a lista accesa chi non e' ammesso non vede NIENTE: ogni rotta GET
    del server, chiesta da anonimo, risponde 403/401 o torna a `/`, e il
    titolo dell'annuncio seminato non esce da nessuna parte; il guscio
    (la pagina vuota e i suoi file) si apre, e porta la copertina;
  - chi e' in lista entra, riceve il cookie d'ammissione, e con quello
    passano anche le chiamate senza identita'; vale per un id Telegram e
    per una chiave Nostr (npub) in lista;
  - la salute, il campanello del bot e il login restano aperti; il bot
    non risponde a chi non e' in lista;
  - la pagina porta il bot e il dominio della prova, e il pannello le
    leve.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco
(MODALITA_COLLAUDO, le identita' «collaudo:<id>:<nome>»). Le leve si
girano sul modulo gia' importato: il middleware le legge a ogni
richiesta, la pagina a ogni rilettura. Nessuna rete.

USO:  python collaudo_istanza_prova.py
"""

import re
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova
SEGRETO = "Barattolo segreto del collaudo Q7"
NPUB = "npub10elfcs4fr0l0r8af98jlmgdh9c8tcxjvz9qkw038js35mp4dma8qzvjptg"


def chi(n, nome="Prova"):
    return {"X-Tg-Init-Data": f"collaudo:{n}:{nome}"}


def semina(S):
    con = S.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(222,'Vende','neg22222',1,'')")
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(222,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
        "'ritiro',5,'sats','nuovo')", (SEGRETO,))
    con.commit()
    con.close()
    return cur.lastrowid


def rotte_get(S):
    """Ogni rotta GET del server, coi parametri riempiti a caso."""
    fuori = []
    for r in S.app.routes:
        metodi = getattr(r, "methods", None) or set()
        percorso = getattr(r, "path", "")
        if "GET" in metodi and percorso:
            fuori.append(re.sub(r"\{[^}]+\}", "1", percorso))
    return sorted(set(fuori))


def main():
    print("=" * 58)
    print("  L'ISTANZA DI PROVA — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    PRIVATA = {"detail": S.MSG_PROVA_PRIVATA}
    aid = semina(S)

    print("\n[a lista vuota: la produzione, identica]")
    prova("la leva nasce vuota (il config finto non la dichiara)", set(),
          S.PROVA_SOLO_IDS)
    r = c.get("/api/listings")
    prova("la vetrina si legge senza identita', annuncio compreso",
          (200, True), (r.status_code, SEGRETO in r.text))
    r = c.get("/api/me", headers=chi(222, "Venditore"))
    prova("chiunque si riconosca entra (222), e nessun cookie d'ammissione nasce",
          (200, False), (r.status_code, S.PROVA_COOKIE in r.headers.get("set-cookie", "")))
    spento_post = c.post("/api/orders", json={})
    prova("un gesto senza identita' non e' il 403 della prova (e' quello di sempre)",
          False, spento_post.json() == PRIVATA)
    S._PAGINA_CACHE["timbro"] = False
    pagina_serie = c.get("/").text
    prova("la pagina: la copertina resta spenta", (1, 0),
          (pagina_serie.count("const ISTANZA_PRIVATA = false;"),
           pagina_serie.count("const ISTANZA_PRIVATA = true;")))
    prova("un annuncio si apre a chiunque", 200, c.get(f"/annuncio/{aid}").status_code)
    webhook_spento = c.post("/api/telegram/aggiornamenti", json={})
    sfida_spenta = c.get("/api/login/nostr/sfida").status_code
    token_222 = S.crea_sessione(222)

    print("\n[a lista accesa: solo 111 e la chiave Nostr del tester]")
    # l'esadecimale dalla npub (64 cifre scritte nel repo farebbero
    # scattare lo scanner delle chiavi private)
    PK = S._npub_in_hex(NPUB)
    nativo = S.crea_utente_nostr(PK, NPUB)
    prova("l'account nativo della npub ha l'id che la lista calcola", nativo,
          S._id_nativo_nostr(S._npub_in_hex(NPUB)))
    S.PROVA_SOLO_IDS = S._prova_lista([111, NPUB])
    S._PAGINA_CACHE["timbro"] = False
    a = TestClient(S.app)                     # il telefono di Andrea
    r = a.get("/api/me", headers=chi(111, "Compratore"))
    prova("111 entra, e riceve il cookie d'ammissione", (200, True),
          (r.status_code, S.PROVA_COOKIE in r.headers.get("set-cookie", "")))
    prova("...poi le chiamate SENZA identita' passano col cookie: la vetrina, il cartello",
          (200, True, 200), (a.get("/api/listings").status_code,
                             SEGRETO in a.get("/api/listings").text,
                             a.get("/api/banner-test").status_code))
    prova("...e la pagina di un annuncio si apre", 200, a.get(f"/annuncio/{aid}").status_code)
    falso = TestClient(S.app)
    # l'ultimo carattere cambia SEMPRE: con un '0' fisso, una volta su
    # sedici la firma finiva gia' in '0' e il cookie restava buono
    vero = a.cookies.get(S.PROVA_COOKIE)
    falso.cookies.set(S.PROVA_COOKIE, vero[:-1] + ("0" if vero[-1] != "0" else "1"))
    prova("un cookie toccato a mano non apre niente", 403, falso.get("/api/listings").status_code)
    n = TestClient(S.app)
    n.cookies.set("barattolo_sessione", S.crea_sessione(nativo))
    r = n.get("/api/me")
    prova("il tester entrato con la sua chiave Nostr (sessione web) entra", (200, nativo),
          (r.status_code, r.json().get("tg_id")))

    print("\n[chi si riconosce ma non e' in lista: niente]")
    r = c.get("/api/me", headers=chi(222, "Venditore"))
    prova("222 col suo initData: 403 col suo perche'", (403, PRIVATA), (r.status_code, r.json()))
    prova("...anche per un gesto", 403, c.post("/api/orders", json={}, headers=chi(222)).status_code)
    s222 = TestClient(S.app)
    s222.cookies.set("barattolo_sessione", token_222)
    prova("...col solo cookie del login web: le API 403", 403, s222.get("/api/me").status_code)
    r = s222.get(f"/annuncio/{aid}", follow_redirects=False)
    prova("...e le pagine tornano a / (la copertina)", (303, "/"),
          (r.status_code, r.headers.get("location")))
    con = S.db()
    try:
        prima = con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id=333").fetchone()[0]
    finally:
        con.close()
    prova("333 non c'e' nel database", 0, prima)
    prova("333 bussa: 403", 403, c.get("/api/me", headers=chi(333)).status_code)
    con = S.db()
    try:
        dopo = con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id=333").fetchone()[0]
    finally:
        con.close()
    prova("...e NON e' stato scritto: il middleware gira prima della rotta", 0, dopo)
    r = c.get("/api/me", headers={"X-Tg-Init-Data": "rotta"})
    prova("un initData rotto o scaduto: 401 (il client sa dire «sessione scaduta»)",
          401, r.status_code)

    print("\n[chi non si fa riconoscere: NIENTE, su ogni rotta]")
    anonimo = TestClient(S.app)
    fughe, porte_sbagliate, guscio = [], [], []
    for via in rotte_get(S):
        r = anonimo.get(via, follow_redirects=False)
        if SEGRETO in r.text:
            fughe.append(via)
        if S._prova_esente(via):
            continue
        if S._prova_guscio(via):
            guscio.append((via, r.status_code))
            continue
        atteso = (403,) if via.startswith("/api/") else (303,)
        if r.status_code not in atteso:
            porte_sbagliate.append((via, r.status_code))
    prova("il titolo dell'annuncio non esce da NESSUNA rotta GET del server", [], fughe)
    prova("...ogni rotta fuori dal guscio: 403 se e' un'API, altrimenti torna a /",
          [], porte_sbagliate)
    prova("...e le rotte censite sono tante (la prova guarda davvero)", True,
          len(rotte_get(S)) > 100)
    p = anonimo.get("/").text
    prova("il guscio: / si apre vuoto, con la copertina accesa e senza annunci",
          (True, False), ("const ISTANZA_PRIVATA = true;" in p, SEGRETO in p))
    prova("...un gesto si ferma", (403, PRIVATA),
          (anonimo.post("/api/orders", json={}).status_code,
           anonimo.post("/api/orders", json={}).json()))
    prova("...e nessun cookie d'ammissione nasce a chi non e' entrato", None,
          anonimo.cookies.get(S.PROVA_COOKIE))

    print("\n[le porte che restano aperte]")
    prova("la salute risponde anche a chi non e' in lista", 200,
          c.get("/api/salute", headers=chi(222)).status_code)
    w = c.post("/api/telegram/aggiornamenti", json={})
    prova("il campanello del bot risponde come a lista vuota",
          (webhook_spento.status_code, webhook_spento.json()), (w.status_code, w.json()))
    prova("...e il login pure", sfida_spenta,
          anonimo.get("/api/login/nostr/sfida").status_code)
    r = anonimo.get("/api/login/nostr/relay")
    prova("...e la porta del login da' i relay del bunker a chi deve ancora entrare",
          (200, list(S.RELAYS_NIP46)), (r.status_code, r.json().get("relay_nip46")))

    print("\n[la leva storta e' chiusa a tutti]")
    S.PROVA_SOLO_IDS = {0}
    prova("con {0} nemmeno 111 entra", 403,
          c.get("/api/me", headers=chi(111)).status_code)
    S.PROVA_SOLO_IDS = set()
    prova("rimessa vuota, 222 rientra", 200,
          c.get("/api/me", headers=chi(222)).status_code)
    S._PAGINA_CACHE["timbro"] = False
    prova("...e la pagina torna quella di sempre, byte per byte", pagina_serie, c.get("/").text)

    print("\n[il bot nella pagina]")
    riga_serie = "const BOT_TG = 'ilbarattolobot';"
    S._PAGINA_CACHE["timbro"] = False
    pagina = c.get("/").text
    prova("col bot di serie la riga resta quella del file", 1, pagina.count(riga_serie))
    S.BOT_NOME = "barattolo_prova_bot"
    S._PAGINA_CACHE["timbro"] = False
    for via in ("/", "/miniapp.html"):
        p = c.get(via).text
        prova(f"{via}: col bot di prova la riga porta il suo nome",
              (1, 0), (p.count("const BOT_TG = 'barattolo_prova_bot';"),
                       p.count("ilbarattolobot")))
    S.BOT_NOME = "ilbarattolobot"
    S._PAGINA_CACHE["timbro"] = False
    prova("rimesso il bot di serie, la pagina torna identica a prima",
          pagina, c.get("/").text)

    print("\n[il bot di prova non risponde a chi non e' in lista]")
    gestiti = []

    async def gestisci_finto(aggiornamento):
        gestiti.append(aggiornamento["message"]["from"]["id"])
    vero = S.gestisci_update
    S.gestisci_update = gestisci_finto
    campanello = {"X-Telegram-Bot-Api-Secret-Token": "collaudo"}   # il segreto del collaudo

    def start(n):
        return c.post("/api/telegram/aggiornamenti", headers=campanello,
                      json={"update_id": n, "message": {"from": {"id": n},
                                                        "chat": {"id": n}, "text": "/start"}})
    try:
        r = start(222)
        prova("a lista vuota il /start di 222 arriva al bot (la produzione)",
              (200, [222]), (r.status_code, gestiti[:]))
        S.PROVA_SOLO_IDS = {111}
        gestiti.clear()
        r = start(222)
        prova("a lista accesa il /start di 222 non arriva al bot...",
              (200, {"ok": True}, []), (r.status_code, r.json(), gestiti[:]))
        start(111)
        prova("...e quello di 111 si'", [111], gestiti[:])
    finally:
        S.gestisci_update = vero
        S.PROVA_SOLO_IDS = set()

    print("\n[il dominio nei testi della pagina]")
    S._PAGINA_CACHE["timbro"] = False
    prova("col dominio di serie la riga resta quella del file", 1,
          c.get("/").text.count("const DOMINIO_SITO = 'barattolo.store';"))
    S.DOMINIO_PUBBLICO = "collaudo.barattolo.store"
    S._PAGINA_CACHE["timbro"] = False
    p = c.get("/").text
    prova("col dominio della prova la riga porta il suo", (1, 0),
          (p.count("const DOMINIO_SITO = 'collaudo.barattolo.store';"),
           p.count("const DOMINIO_SITO = 'barattolo.store';")))
    S.DOMINIO_PUBBLICO = "barattolo.store"
    S._PAGINA_CACHE["timbro"] = False
    prova("rimesso quello di serie, la pagina torna identica", pagina, c.get("/").text)

    print("\n[il pannello «Stato delle leve»]")
    def righe_leve():
        g = c.get("/api/admin/leve", headers=chi(999, "Admin")).json()["gruppi"]
        return {v["chiave"]: v for gr in g for v in gr["voci"]}
    v = righe_leve()
    prova("l'indirizzo, il bot e la lista ci sono, la lista come numero",
          ["https://barattolo.store", "https://t.me/ilbarattolobot", 0],
          [v["URL_PUBBLICO"]["valore"], v["LINK_BOT"]["valore"], v["PROVA_SOLO_IDS"]["valore"]])
    S.PROVA_SOLO_IDS = {111, 999}
    v = righe_leve()
    prova("a lista accesa dice QUANTI, e nessuno dei due id compare", (2, False),
          (v["PROVA_SOLO_IDS"]["valore"], "111" in str(v["PROVA_SOLO_IDS"])))
    S.PROVA_SOLO_IDS = set()
    S.URL_PUBBLICO = "https://collaudo.barattolo.store"
    prova("un indirizzo di prova senza lista suona l'allarme", True,
          righe_leve()["URL_PUBBLICO"].get("allarme", False))
    S.URL_PUBBLICO = S.URL_PUBBLICO_DI_SERIE

    print("\n[il recinto dei relay: chi bussa, e dove]")
    bussati = []

    def connessione_finta(relay, **kw):
        bussati.append(relay)
        raise OSError("nessuna rete nel collaudo")
    vera_conn, vera_posta = S.create_connection, S._posta_per
    S.create_connection = connessione_finta
    S._posta_per = lambda relay: None
    evento = {"id": "e" * 64, "kind": 1, "content": "prova"}
    try:
        S.PROVA_SOLO_IDS = set()
        S.invia_evento_relay("wss://relay.barattolo.store", evento)
        prova("a lista vuota (la produzione) la scrittura bussa al nostro relay come sempre",
              ["wss://relay.barattolo.store"], bussati[:])
        S.PROVA_SOLO_IDS = {111}
        bussati.clear()
        esiti = [S.invia_evento_relay(r, evento) for r in
                 ("wss://relay.barattolo.store", "wss://nos.lol", "wss://relay.primal.net")]
        prova("sull'istanza di prova la scrittura non bussa a NESSUN relay vero",
              ([False] * 3, []), (esiti, bussati[:]))
        S.invia_evento_relay("ws://127.0.0.1:7777", evento)
        prova("...e bussa al relay di prova di casa", ["ws://127.0.0.1:7777"], bussati[:])
        bussati.clear()
        # in collaudo `lettura_simulata` ferma gia' ogni lettura da un
        # relay vero: per QUESTA riga la si spegne (la connessione e'
        # finta, la rete non esce) e si guarda il solo recinto
        S.MODALITA_COLLAUDO = False
        S.info_libro_da_relay("wss://relay.mostro.network", S.MOSTRO_NPUB)
        S.MODALITA_COLLAUDO = True
        prova("...mentre il P2P parla coi relay di Mostro", ["wss://relay.mostro.network"],
              bussati[:])
    finally:
        S.create_connection, S._posta_per = vera_conn, vera_posta
        S.PROVA_SOLO_IDS = set()
        S.MODALITA_COLLAUDO = True

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
