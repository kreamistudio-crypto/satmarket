# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA SERIE DEI GIORNI 🔥 (17 nov 2026, cantiere
serie-giorni).

Nel Profilo ognuno vede quanti giorni DI FILA ha aperto Barattolo, e il
suo record. Non da' XP ne' premi; gli altri la vedono solo nella
classifica dei giorni di fila (punto 8), mai sul profilo pubblico. Qui il
server VERO, per HTTP con la TestClient e l'identita' di collaudo
nell'header, e un orologio finto che il collaudo sposta:
  1) la migrazione: un database di ieri, senza la tabella, si apre e la
     prima apertura conta 1;
  2) /api/me timbra una volta al giorno: la seconda apertura non e'
     «nuova», il giorno dopo si sale, un giorno saltato riparte da 1 col
     record che resta;
  3) il giorno e' quello ITALIANO: mezz'ora dopo la mezzanotte di Roma
     conta gia', anche se a Greenwich e' ancora ieri;
  4) la rotta del ritorno in primo piano (`POST /api/me/serie`): lo
     stesso giudice, e non si lascia dire il giorno dal client;
  5) e' SOLO di chi la fa: il negozio pubblico non la porta, e la serie
     di uno non tocca quella di un altro;
  6) la fusione di due account (la funzione vera, `esegui_fusione`) e la
     cancellazione dell'account (`esegui_cancellazione`);
  7) a leva spenta: niente chiave, niente timbro, la rotta risponde 404;
  8) LA CLASSIFICA (17 nov sera, cantiere serie-classifica): `GET
     /api/serie/classifica` vuole l'identita', mette in fila le serie
     VIVE dal secondo giorno, non timbra, non manda id, e chi accende
     «Non mostrarmi in classifica» (la rotta vera) ne esce subito.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, nessuna rete.

USO:  python collaudo_serie_giorni.py
"""

import calendar
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
OROLOGIO = [0]      # l'istante (epoch UTC) che il timbro crede sia adesso
TIMBRI = []         # ogni chiamata al timbro vero: (tg_id, istante)

ANNA, BRUNO, CARLA = 111, 222, 333
NOSTR = -4242       # un account entrato con Nostr, da fondere in CARLA


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alle(giorno, ora=12, minuti=0, mese=11):
    """Sposta l'orologio a un istante UTC del 2026."""
    OROLOGIO[0] = calendar.timegm((2026, mese, giorno, ora, minuti, 0))


def avvio():
    """Il database di IERI prima dell'import: l'anagrafe com'e' in
    produzione oggi non ha `serie_giorni`. Qui basta un file vuoto con
    una tabella qualunque: l'avvio del server deve far nascere la sua."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-serie-"),
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
                 "premia_distintivi", "premia_xp", "aggiorna_profilo_social",
                 "premia_reputazione_nostr"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    # L'OROLOGIO FINTO: il timbro vero, con l'istante che dice il
    # collaudo. Le due porte (/api/me e la rotta del ritorno) lo chiamano
    # per nome, quindi basta cambiare il nome nel modulo.
    vero = server.timbra_serie

    def timbro_con_orologio(con, tg_id, adesso=None):
        TIMBRI.append((tg_id, OROLOGIO[0]))
        return vero(con, tg_id, OROLOGIO[0])

    server.timbra_serie = timbro_con_orologio
    # ...e la classifica guarda lo stesso orologio
    vera = server.serie_classifica
    server.serie_classifica = lambda con, io, adesso=None: vera(con, io, OROLOGIO[0])
    return db


def chi(tg_id):
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:Utente{tg_id}"}


def riga(tg_id):
    con = SRV.db()
    r = con.execute("SELECT giorni, record, ultimo FROM serie_giorni "
                    "WHERE tg_id=?", (tg_id,)).fetchone()
    con.close()
    return tuple(r) if r else None


def main():
    db = avvio()
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    me = lambda t: c.get("/api/me", headers=chi(t)).json()
    serie = lambda t: me(t).get("serie")
    corta = lambda s: (s["giorni"], s["record"], s["nuova"]) if s else None

    # ------------------------------------------------------------------
    print("\n[1) la migrazione: il database di ieri]")
    con = sqlite3.connect(db)
    prova("la tabella e' nata all'avvio, vuota", 0,
          con.execute("SELECT COUNT(*) FROM serie_giorni").fetchone()[0])
    con.close()
    prova("la leva e' accesa di serie (il config non la nomina)", True,
          SRV.SERIE_GIORNI_ATTIVA)

    # ------------------------------------------------------------------
    print("\n[2) /api/me timbra una volta al giorno]")
    alle(16)                         # lunedi' 16 nov 2026, mezzogiorno UTC
    me(ANNA)                         # la prima apertura crea l'utente
    s = serie(ANNA)
    prova("dopo la prima apertura: 1 giorno, record 1", (1, 1),
          (s["giorni"], s["record"]))
    prova("la busta dice il giorno italiano, che e' lunedi', e le tappe",
          ("2026-11-16", 0, [7, 30, 100, 365], True),
          (s["oggi"], s["feriale"], s["tappe"], s["oggi_contato"]))
    prova("un'altra apertura lo stesso giorno non e' nuova e non sale",
          (1, 1, False), corta(serie(ANNA)))
    prova("la riga in tabella: una, col giorno italiano", (1, 1, "2026-11-16"),
          riga(ANNA))
    alle(17)
    prova("il giorno dopo: 2 di fila, ed e' nuova UNA volta",
          [(2, 2, True), (2, 2, False)], [corta(serie(ANNA)), corta(serie(ANNA))])
    for g in (18, 19, 20):
        alle(g)
        me(ANNA)
    prova("cinque giorni di fila", (5, 5, "2026-11-20"), riga(ANNA))
    alle(23)
    prova("due giorni senza aprire: riparte da 1, IL RECORD RESTA 5",
          (1, 5, True), corta(serie(ANNA)))
    alle(24)
    prova("...e da li' si risale, sotto il record", (2, 5, True),
          corta(serie(ANNA)))

    # ------------------------------------------------------------------
    print("\n[3) il giorno e' quello italiano]")
    alle(24, 22, 59)                 # le 23:59 a Roma
    prova("alle 23:59 di Roma e' ancora martedi' 24", (2, 5, False),
          corta(serie(ANNA)))
    alle(24, 23, 30)                 # le 00:30 a Roma, ancora il 24 a Greenwich
    s = serie(ANNA)
    prova("alle 00:30 di Roma e' gia' mercoledi' 25: conta",
          (3, True, "2026-11-25", 2),
          (s["giorni"], s["nuova"], s["oggi"], s["feriale"]))
    alle(25, 22, 0)
    prova("...e per tutto il 25 italiano non conta di nuovo", (3, 5, False),
          corta(serie(ANNA)))
    # l'estate: due ore avanti. Bruno apre il 10 luglio alle 21:30 UTC
    # (le 23:30 a Roma) e poi alle 22:30 UTC (le 00:30 dell'11)
    alle(10, 21, 30, mese=7)
    me(BRUNO)
    prova("d'estate, alle 23:30 di Roma: 1", (1, 1), corta(serie(BRUNO))[:2])
    alle(10, 22, 30, mese=7)
    prova("...e un'ora dopo e' gia' l'11 luglio: 2 di fila", (2, 2, True),
          corta(serie(BRUNO)))

    # ------------------------------------------------------------------
    print("\n[4) la rotta del ritorno in primo piano]")
    alle(26)
    r = c.post("/api/me/serie", headers=chi(ANNA))
    prova("a giorno cambiato conta, con la stessa busta di /api/me",
          (200, (4, 5, True), "2026-11-26"),
          (r.status_code, corta(r.json().get("serie")),
           r.json().get("serie", {}).get("oggi")))
    prova("...bussare ancora non conta due volte", (4, 5, False),
          corta(c.post("/api/me/serie", headers=chi(ANNA)).json()["serie"]))
    r = c.post("/api/me/serie", headers=chi(ANNA),
               json={"giorni": 999, "record": 999, "oggi": "2030-01-01",
                     "adesso": 9999999999})
    prova("...e quel che dichiara il client non conta niente", (4, 5, False),
          corta(r.json()["serie"]))
    prova("senza identita' non si passa", True,
          c.post("/api/me/serie").status_code in (401, 403))
    prova("in GET la rotta non c'e' (scrive: e' una POST)", 405,
          c.get("/api/me/serie", headers=chi(ANNA)).status_code)

    # ------------------------------------------------------------------
    print("\n[5) e' solo di chi la fa]")
    prova("la serie di Anna non ha toccato quella di Bruno", (2, 2, "2026-07-11"),
          riga(BRUNO))
    con = SRV.db()
    negozio = con.execute("SELECT negozio FROM utenti WHERE tg_id=?",
                          (ANNA,)).fetchone()[0]
    con.close()
    pubblico = c.get(f"/api/negozio/{negozio}", headers=chi(BRUNO))
    prova("il negozio pubblico di Anna risponde...", 200, pubblico.status_code)
    prova("...e della serie non dice niente", False,
          "serie" in pubblico.text or "record" in pubblico.text)

    # ------------------------------------------------------------------
    print("\n[6) la fusione e la cancellazione, con le funzioni vere]")
    alle(26)
    me(CARLA)                                    # Carla: 1 giorno, oggi
    con = SRV.db()
    con.execute("INSERT INTO utenti(tg_id, nome, negozio, registrato, "
                "npub_accesso, npub) VALUES(?, 'Nostr', 'negnostr', 1, ?, ?)",
                (NOSTR, "npub1collaudo", "npub1collaudo"))
    con.execute("INSERT INTO serie_giorni VALUES(?, 8, 21, '2026-11-26')",
                (NOSTR,))
    con.commit()
    con.close()
    esito = SRV.esegui_fusione(CARLA, NOSTR)
    prova("la fusione va in porto", False, isinstance(esito, str))
    prova("resta UNA riga: la serie piu' lunga delle due e il record piu' alto",
          [(8, 21, "2026-11-26"), None], [riga(CARLA), riga(NOSTR)])
    prova("...e il Profilo di Carla la mostra", (8, 21, False),
          corta(serie(CARLA)))
    SRV.esegui_cancellazione(BRUNO)
    prova("l'account cancellato porta via la sua riga", None, riga(BRUNO))

    # ------------------------------------------------------------------
    print("\n[8) la classifica dei giorni di fila]")
    DINO = 444
    alle(26)
    timbri, righe_prima = len(TIMBRI), (riga(ANNA), riga(CARLA))
    cl = lambda t: c.get("/api/serie/classifica", headers=chi(t))
    r = cl(ANNA)
    d = r.json()
    prova("risponde a chi e' entrato: Carla (8) prima, Anna (4) seconda e "
          "segnata come «io»",
          (200, [(1, 8, False), (2, 4, True)], 2, None, False, 2),
          (r.status_code,
           [(v["posizione"], v["giorni"], v["io"]) for v in d["voci"]],
           d["totale"], d["mia"], d["nascosto"], d["minimo"]))
    prova("i campi di una riga sono cinque: l'id non esce",
          {"posizione", "nome", "avatar", "giorni", "io"}, set(d["voci"][0]))
    prova("il nome e' quello dell'anagrafe", True,
          all(isinstance(v["nome"], str) and v["nome"] for v in d["voci"]))
    prova("senza identita' non si guarda", True,
          c.get("/api/serie/classifica").status_code in (401, 403))
    r = cl(DINO)
    prova("chi non ha ancora una serie guarda lo stesso, e guardare NON "
          "timbra: nessuna riga per lui, nessun timbro in piu', le altre ferme",
          (200, None, timbri, righe_prima, False),
          (r.status_code, riga(DINO), len(TIMBRI), (riga(ANNA), riga(CARLA)),
           any(v["io"] for v in r.json()["voci"])))
    # Carla accende «Non mostrarmi in classifica», dalla rotta vera
    r = c.post("/api/me/classifica-nascosta", headers=chi(CARLA),
               json={"nascosta": True})
    prova("Carla accende «Non mostrarmi in classifica»", (200, True),
          (r.status_code, r.json().get("nascosta")))
    d = cl(ANNA).json()
    prova("...e sparisce SUBITO: Anna sale al primo posto, in gara resta lei",
          ([(1, 4, True)], 1),
          ([(v["posizione"], v["giorni"], v["io"]) for v in d["voci"]], d["totale"]))
    d = cl(CARLA).json()
    prova("...a Carla si dice che non compare, e la sua riga non c'e'",
          (True, None, False),
          (d["nascosto"], d["mia"], any(v["io"] for v in d["voci"])))
    prova("...ma la sua serie nel Profilo resta la sua", (8, 21, False),
          corta(serie(CARLA)))
    c.post("/api/me/classifica-nascosta", headers=chi(CARLA),
           json={"nascosta": False})
    prova("spento l'interruttore, torna in testa", [(1, 8), (2, 4)],
          [(v["posizione"], v["giorni"]) for v in cl(ANNA).json()["voci"]])
    alle(27)
    prova("il giorno dopo, senza che nessuno apra, le file sono ancora in "
          "piedi (ieri vale)", 2, cl(DINO).json()["totale"])
    alle(28)
    prova("due giorni dopo non c'e' piu' nessuno: una fila finita non si "
          "mostra", ([], 0), (lambda x: (x["voci"], x["totale"]))(cl(DINO).json()))

    # ------------------------------------------------------------------
    print("\n[7) a leva spenta]")
    SRV.SERIE_GIORNI_ATTIVA = False
    alle(27)
    prima = len(TIMBRI)
    prova("/api/me non manda la chiave", None, serie(ANNA))
    prova("...e risponde lo stesso, col resto del profilo", ANNA,
          me(ANNA).get("tg_id"))
    prova("...il timbro non gira e la riga resta com'era",
          (prima, (4, 5, "2026-11-26")), (len(TIMBRI), riga(ANNA)))
    prova("la rotta del ritorno risponde 404", 404,
          c.post("/api/me/serie", headers=chi(ANNA)).status_code)
    prova("...e la classifica pure", 404,
          c.get("/api/serie/classifica", headers=chi(ANNA)).status_code)
    SRV.SERIE_GIORNI_ATTIVA = True
    alle(29)
    prova("riaccesa dopo due giorni di buio: riparte da 1, il record resta",
          (1, 5, True), corta(serie(ANNA)))

    # un errore nel contatore non costa il profilo (fail-open)
    buono = SRV.timbra_serie

    def rotto(*a, **k):
        raise RuntimeError("contatore rotto apposta")

    SRV.timbra_serie = rotto
    r = c.get("/api/me", headers=chi(ANNA))
    prova("col timbro che esplode /api/me risponde 200, senza la chiave",
          (200, None), (r.status_code, r.json().get("serie")))
    SRV.timbra_serie = buono

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
