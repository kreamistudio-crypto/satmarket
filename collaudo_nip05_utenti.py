# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI NOMI NIP-05 DEGLI UTENTI (17 nov 2026, cantiere
nip05-utenti; Andrea: «attivare verifica NIP-05, gratis per utenti da
lv2 in su»).

Chi ha una chiave Nostr PROVATA e almeno il livello «avviato» (il
gradino 2) sceglie gratis nome@barattolo.store, e /.well-known/nostr.json
lo conferma ai client Nostr. Qui il server VERO, per HTTP con la
TestClient e l'identita' di collaudo nell'header:
  1) la migrazione: un database di ieri si apre con la colonna nuova, e
     la leva e' accesa di serie;
  2) le tre porte: senza chiave provata, sotto il livello, e la npub
     solo DICHIARATA (non firmata) non prendono il nome;
  3) chi ha tutto lo prende: /api/me lo dice, la rotta pubblica risponde
     la chiave in esadecimale, e senza `?name=` gli utenti NON escono;
  4) la forma e i doppioni: maiuscole, segni, nomi riservati e di casa,
     il nome di un altro, lo username Telegram di un altro;
  5) il nome si spegne DA SOLO quando la chiave sparisce o il livello
     non c'e' piu', e si puo' sempre lasciare;
  6) la scala dei livelli e il pannello delle leve lo dicono;
  7) la fusione (la funzione vera) lo porta, la cancellazione lo libera;
  8) a leva spenta: niente chiave in /api/me, la rotta risponde 404 e
     nostr.json torna ai soli nomi di casa.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, nessuna rete.

USO:  python collaudo_nip05_utenti.py
"""

import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None

ANNA, BRUNO, CARLA, DARIO = 111, 222, 333, 444
NOSTR = -4243       # un account entrato con Nostr, da fondere in CARLA
# chiavi PUBBLICHE di cartone, una per persona (mai una nsec qui)
HEX = {ANNA: "a1" * 32, BRUNO: "b2" * 32, CARLA: "c3" * 32,
       DARIO: "d4" * 32, NOSTR: "e5" * 32}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il database di IERI prima dell'import: un file con una tabella
    qualunque, l'avvio del server fa nascere la sua anagrafe con la
    colonna nuova."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-nip05-"),
                      "usa-e-getta.db")
    vecchio = sqlite3.connect(db)
    vecchio.execute("CREATE TABLE segnaposto(x INTEGER)")
    vecchio.commit()
    vecchio.close()
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def zitto(*a, **k):
        return None

    for nome in ("notifica", "notifica_admin", "annuncio_su_nostr",
                 "premia_distintivi", "premia_xp", "aggiorna_profilo_social"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    return db


def chi(tg_id):
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:Utente{tg_id}"}


def scrivi(sql, *arg):
    con = SRV.db()
    con.execute(sql, arg)
    con.commit()
    con.close()


def leggi(sql, *arg):
    con = SRV.db()
    r = con.execute(sql, arg).fetchone()
    con.close()
    return tuple(r) if r else None


def da_livello_2(tg_id):
    """50 XP e un affare: il gradino «avviato»."""
    scrivi("UPDATE utenti SET xp=50, vendite_ok=1 WHERE tg_id=?", tg_id)


def con_chiave(tg_id, come="accesso"):
    npub = SRV.hex_to_npub(HEX[tg_id])
    if come == "accesso":
        scrivi("UPDATE utenti SET npub=?, npub_verificata=1, npub_accesso=? "
               "WHERE tg_id=?", npub, npub, tg_id)
    elif come == "badge":
        scrivi("UPDATE utenti SET npub=?, npub_verificata=1, npub_accesso='' "
               "WHERE tg_id=?", npub, tg_id)
    else:                                    # solo dichiarata
        scrivi("UPDATE utenti SET npub=?, npub_verificata=0, npub_accesso='' "
               "WHERE tg_id=?", npub, tg_id)


def main():
    db = avvio()
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    me = lambda t: c.get("/api/me", headers=chi(t)).json()
    scegli = lambda t, nome: c.post("/api/me/nip05", headers=chi(t),
                                    json={"nome": nome})
    nj = lambda nome=None: c.get(
        "/.well-known/nostr.json", params={"name": nome} if nome else None)

    # ------------------------------------------------------------------
    print("\n[1) la migrazione e la leva]")
    for t in (ANNA, BRUNO, CARLA, DARIO):
        me(t)                                   # la prima apertura li crea
    con = sqlite3.connect(db)
    colonne = [r[1] for r in con.execute("PRAGMA table_info(utenti)")]
    con.close()
    prova("la colonna nip05_nome e' nata all'avvio", True,
          "nip05_nome" in colonne)
    prova("la leva e' accesa di serie, gratis dal livello «avviato»",
          (True, "avviato"), (SRV.NIP05_UTENTI_ATTIVO, SRV.NIP05_UTENTI_LIVELLO))
    s = me(ANNA)["nip05"]
    prova("/api/me di chi non ha niente: nessun nome, nessuna chiave, "
          "livello non raggiunto", ("", False, False, False, "Bottega avviata"),
          (s["nome"], s["chiave"], s["sblocca"], s["attivo"], s["livello_nome"]))

    # ------------------------------------------------------------------
    print("\n[2) le tre porte]")
    da_livello_2(ANNA)
    r = scegli(ANNA, "anna")
    prova("livello si', chiave no: 400 e lo dice", (400, True),
          (r.status_code, "chiave Nostr" in r.json().get("detail", "")))
    con_chiave(BRUNO)
    r = scegli(BRUNO, "bruno")
    prova("chiave si', livello no: 400 e dice da quale livello", (400, True),
          (r.status_code, "Bottega avviata" in r.json().get("detail", "")))
    con_chiave(ANNA, "dichiarata")
    r = scegli(ANNA, "anna")
    prova("una npub solo DICHIARATA non basta (400)", 400, r.status_code)
    prova("...e nessun nome e' stato scritto", ("",),
          leggi("SELECT nip05_nome FROM utenti WHERE tg_id=?", ANNA))
    prova("senza identita' non si passa", True,
          c.post("/api/me/nip05", json={"nome": "x"}).status_code in (401, 403))
    prova("in GET la rotta non c'e' (scrive: e' una POST)", 405,
          c.get("/api/me/nip05", headers=chi(ANNA)).status_code)

    # ------------------------------------------------------------------
    print("\n[3) chi ha tutto lo prende]")
    con_chiave(ANNA, "badge")                   # il badge verificato basta
    r = scegli(ANNA, "  Anna@barattolo.store ")
    prova("livello 2 e badge verificato: 200, il nome tenuto minuscolo e "
          "senza dominio", (200, "anna", True),
          (r.status_code, r.json()["nip05"]["nome"], r.json()["nip05"]["attivo"]))
    s = me(ANNA)["nip05"]
    prova("/api/me lo dice, col dominio", ("anna", True, "barattolo.store"),
          (s["nome"], s["attivo"], s["dominio"]))
    r = nj("anna")
    prova("nostr.json?name=anna risponde la chiave in esadecimale",
          {"names": {"anna": HEX[ANNA]}}, r.json())
    prova("...con CORS aperto", "*", r.headers.get("access-control-allow-origin"))
    prova("un nome che non c'e': «qui nessuno», non 404",
          (200, {"names": {}}), (nj("nessuno").status_code, nj("nessuno").json()))
    tutti = nj().json()["names"]
    prova("senza ?name= escono i soli nomi di casa, mai gli utenti",
          (False, True), ("anna" in tutti, "_" in tutti))
    prova("i nomi di casa rispondono come prima",
          SRV.NIP05_DI_CASA["_"], nj("_").json()["names"].get("_"))
    con_chiave(DARIO)
    da_livello_2(DARIO)
    r = scegli(DARIO, "dario.bottega")
    prova("con la chiave d'accesso (login Nostr) va lo stesso",
          (200, {"names": {"dario.bottega": HEX[DARIO]}}),
          (r.status_code, nj("dario.bottega").json()))
    r = scegli(DARIO, "dario")
    prova("cambiare nome: il vecchio non risponde piu', il nuovo si'",
          ({"names": {}}, {"names": {"dario": HEX[DARIO]}}),
          (nj("dario.bottega").json(), nj("dario").json()))

    # ------------------------------------------------------------------
    print("\n[4) la forma e i doppioni]")
    for nome, pezzo in (("ab", "fra 3 e 30"), ("a" * 31, "fra 3 e 30"),
                        ("an na", "Solo lettere"), ("anna!", "Solo lettere"),
                        ("ànna", "Solo lettere"), (".anna", "segni"),
                        ("anna-", "segni"), ("an..na", "segni"),
                        ("admin", "riservato"), ("tappo", "riservato"),
                        ("barattolo", "riservato"), ("_", "fra 3 e 30")):
        r = scegli(ANNA, nome)
        prova(f"«{nome}» non passa", (400, True),
              (r.status_code, pezzo in r.json().get("detail", "")))
    SRV.NIP05_NOMI["casetta"] = "f6" * 32
    r = scegli(ANNA, "casetta")
    prova("un nome di casa scritto nel config non si prende", 400, r.status_code)
    del SRV.NIP05_NOMI["casetta"]
    r = scegli(ANNA, "dario")
    prova("il nome di un altro e' preso", (400, True),
          (r.status_code, "già preso" in r.json().get("detail", "")))
    scrivi("UPDATE utenti SET username='BrunoBotteghe' WHERE tg_id=?", BRUNO)
    r = scegli(ANNA, "brunobotteghe")
    prova("...e anche lo username Telegram di un altro", 400, r.status_code)
    prova("dopo i rifiuti Anna tiene il suo", {"names": {"anna": HEX[ANNA]}},
          nj("anna").json())

    # ------------------------------------------------------------------
    print("\n[5) si spegne da solo, e si lascia sempre]")
    scrivi("UPDATE utenti SET npub_verificata=0 WHERE tg_id=?", ANNA)
    s = me(ANNA)["nip05"]
    prova("chiave non piu' provata: la rotta tace, il nome resta salvato",
          ({"names": {}}, "anna", False),
          (nj("anna").json(), s["nome"], s["attivo"]))
    scrivi("UPDATE utenti SET npub_verificata=1 WHERE tg_id=?", ANNA)
    prova("...riprovata, torna da sola", {"names": {"anna": HEX[ANNA]}},
          nj("anna").json())
    scrivi("UPDATE utenti SET xp=10 WHERE tg_id=?", ANNA)
    prova("sotto il livello: la rotta tace", {"names": {}}, nj("anna").json())
    r = scegli(ANNA, "")
    prova("...e lasciarlo si puo' anche senza livello", (200, ""),
          (r.status_code, r.json()["nip05"]["nome"]))
    da_livello_2(ANNA)
    prova("un nome lasciato non torna col livello", {"names": {}},
          nj("anna").json())
    proposta = me(BRUNO)["nip05"]["proposta"]      # /api/me riscrive lo username
    prova("la proposta per chi non ha un nome: il suo username, se ha la forma",
          (leggi("SELECT lower(username) FROM utenti WHERE tg_id=?", BRUNO)[0],
           True), (proposta, bool(proposta)))

    # ------------------------------------------------------------------
    print("\n[6) la scala dei livelli e il pannello]")
    scala = me(ANNA)["livelli_scala"]
    prova("la scala: dal gradino 2 in su il nome verificato e' un vantaggio",
          [False, True, True, True, True], [g["nip05"] for g in scala])
    voci = [v for g in SRV._leve_stato() for v in g.get("voci", [])]
    chiavi = {v["chiave"]: v["valore"] for v in voci}
    prova("il pannello delle leve mostra la leva e il livello",
          (True, "avviato"),
          (chiavi.get("NIP05_UTENTI_ATTIVO"), chiavi.get("NIP05_UTENTI_LIVELLO")))

    # ------------------------------------------------------------------
    print("\n[7) la fusione e la cancellazione, con le funzioni vere]")
    scrivi("INSERT INTO utenti(tg_id, nome, negozio, registrato, "
           "npub_accesso, npub, npub_verificata, nip05_nome) "
           "VALUES(?, 'Nostr', 'negnostr', 1, ?, ?, 1, 'carla')",
           NOSTR, SRV.hex_to_npub(HEX[NOSTR]), SRV.hex_to_npub(HEX[NOSTR]))
    esito = SRV.esegui_fusione(CARLA, NOSTR)
    prova("la fusione va in porto", False, isinstance(esito, str))
    prova("il nome della meta' Nostr passa a Carla", ("carla",),
          leggi("SELECT nip05_nome FROM utenti WHERE tg_id=?", CARLA))
    SRV.esegui_cancellazione(DARIO)
    prova("l'account cancellato libera il suo nome", (None, {"names": {}}),
          (leggi("SELECT tg_id FROM utenti WHERE nip05_nome='dario'"),
           nj("dario").json()))

    # ------------------------------------------------------------------
    print("\n[8) a leva spenta]")
    r = scegli(ANNA, "anna")
    prova("(Anna riprende il suo nome)", 200, r.status_code)
    SRV.NIP05_UTENTI_ATTIVO = False
    prova("/api/me non manda lo stato", None, me(ANNA).get("nip05"))
    prova("la rotta risponde 404", 404, scegli(ANNA, "anna2").status_code)
    prova("nostr.json torna ai soli nomi di casa",
          ({"names": {}}, True), (nj("anna").json(), "_" in nj().json()["names"]))
    prova("la scala non promette il vantaggio",
          [False] * 5, [g["nip05"] for g in me(ANNA)["livelli_scala"]])
    SRV.NIP05_UTENTI_ATTIVO = True
    prova("riaccesa, il nome salvato risponde di nuovo",
          {"names": {"anna": HEX[ANNA]}}, nj("anna").json())

    # un database che non risponde vale «qui nessuno», mai un 500
    buono = SRV.db

    def rotto(*a, **k):
        raise sqlite3.OperationalError("database rotto apposta")

    SRV.db = rotto
    r = nj("anna")
    prova("col database che esplode nostr.json risponde 200, vuoto",
          (200, {"names": {}}), (r.status_code, r.json()))
    SRV.db = buono

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
