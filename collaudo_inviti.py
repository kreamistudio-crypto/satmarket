# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI CODICI INVITO (set 2026).

`prove.py` monta i pezzi estratti su un database di cartone; qui gira il
SERVER VERO su un database usa-e-getta, con lo SCHEMA VERO di `init_db`
— le due tabelle nuove col loro CHECK, la fusione con tutte le sue
tabelle, il campanello del bot attraverso la sua rotta. Di finto ci
sono soltanto Telegram (quel che il bot direbbe si registra) e il
config.

  1. il /start col codice, dalla ROTTA del campanello: chi arriva nuovo
     si collega da solo, il benvenuto resta UNO con la riga dell'invito
     in coda, e il lasciapassare della fusione prende ancora la sua
     strada;
  2. il campo a mano: il giro buono e tutti i no — la forma, il codice
     che non c'e', il proprio, il secondo invito, la finestra chiusa, il
     giro in tondo (anche lungo) — piu' il CHECK dello schema;
  3. il cassetto in /api/me: il codice, il link, due conti, e nessun
     nome di chi e' stato invitato;
  4. la quota a ogni accredito, dal gancio VERO (`premia_xp`): il tetto
     sui propri, il 5% per difetto, l'affare con chi ha invitato che non
     paga, il retry, niente catena, «a vita» — e il numero che resta UNO
     fra cache, riallineamento d'avvio, classifica e scomposizione, che
     sotto i tre invitati attivi non dice nessuna cifra;
  5. la fusione di due account: l'auto-invito, il giro in tondo e
     l'affare diventato «con chi ha invitato» che nascerebbero fondendo
     si sciolgono, e il CHECK non fa cadere la fusione;
  6. l'azzeramento degli XP, simulato come lo dice il codice: si
     cancellano le righe del perimetro, i collegamenti restano, e la
     regola riparte da zero da sola.

NON TOCCA NIENTE DI VERO: il `config` di cartone lo installa `avvio()`
del banco dei pagamenti, PRIMA dell'import del server. Nessuna rete: il
bot e il rinfresco della foto profilo sono doppi.

USO:  python collaudo_inviti.py
"""

import asyncio
import json
import sqlite3
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
BOT = []            # (metodo, dati) di ogni chiamata al bot


def _gancio_vero():
    """Il banco dei pagamenti sostituisce `premia_xp` con un doppio muto
    (li' non serviva): qui serve QUELLO VERO, perche' e' il punto da cui
    la quota nasce. Si rimonta dal sorgente dentro il modulo del server
    — la lezione di `reale` in prove.py: mai uno stub scritto a mano,
    che imiterebbe anche i difetti."""
    src = open("server.py", encoding="utf-8").read()
    i = src.index("async def premia_xp(")
    exec(src[i:src.index("\n\n\n", i)], banco.SRV.__dict__)


async def _bot_finto(metodo, dati):
    BOT.append((metodo, dati))
    return {"ok": True, "result": {"message_id": -1}}


async def _zitto(*a, **k):
    return None


def _db():
    return banco.SRV.db()


def persona(tg_id, nome, giorni_fa=0.0, registrato=None):
    """Una riga d'anagrafe iscritta `giorni_fa` giorni fa — o con un
    `registrato` esplicito: lo zero di chi c'era prima del timbro."""
    reg = (int(time.time() - giorni_fa * 86400) if registrato is None
           else registrato)
    con = _db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, negozio, "
                "registrato, avatar_aggiornato) VALUES(?,?,?,?,?)",
                (tg_id, nome, f"neg{abs(tg_id)}", reg, int(time.time())))
    con.commit()
    con.close()


def nostrano(tg_id, nome):
    """Un account nato su Nostr (tg_id negativo, chiave d'accesso): la
    meta' che muore in una fusione."""
    persona(tg_id, nome, 1)
    con = _db()
    finta = f"npub1collaudo{abs(tg_id)}"
    con.execute("UPDATE utenti SET npub=?, npub_accesso=? WHERE tg_id=?",
                (finta, finta, tg_id))
    con.commit()
    con.close()


def codice_di(tg_id):
    con = _db()
    c = banco.SRV.codice_invito(con, tg_id)
    con.commit()
    con.close()
    return c


def invitante_di(tg_id):
    con = _db()
    r = con.execute("SELECT invitante, via FROM inviti WHERE invitato=?",
                    (tg_id,)).fetchone()
    con.close()
    return (r["invitante"], r["via"]) if r else None


def collega_a_mano(invitato, invitante):
    """Un collegamento scritto DIRETTO nella tabella, senza il giudice:
    serve solo a mettere in scena chi e' iscritto da un pezzo."""
    con = _db()
    con.execute("INSERT INTO inviti(invitato, invitante, creato, via) "
                "VALUES(?,?,?,'banco')", (invitato, invitante,
                                          int(time.time())))
    con.commit()
    con.close()


def xp_di(tg_id):
    con = _db()
    r = con.execute("SELECT xp FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    con.close()
    return r["xp"] if r else None


def quote_di(tg_id):
    con = _db()
    rr = [(r["punti"], r["riferimento"]) for r in con.execute(
        "SELECT punti, riferimento FROM xp_eventi WHERE tg_id=? "
        "AND tipo=? ORDER BY id", (tg_id, banco.SRV.XP_INVITO))]
    con.close()
    return rr


def ordine(venditore, compratore):
    """Un affare concluso: basta la riga, perche' la quota chiede solo
    CHI stava nell'affare."""
    adesso = int(time.time())
    con = _db()
    oid = con.execute(
        "INSERT INTO ordini(annuncio_id, compratore_id, venditore_id, "
        "prezzo_sats, stato, creato, aggiornato) "
        "VALUES(0,?,?,1000,'released',?,?)",
        (compratore, venditore, adesso, adesso)).lastrowid
    con.commit()
    con.close()
    return oid


def accredita(tg_id, punti, oid, ruolo):
    """Il gancio VERO, con il riferimento nella forma di `_sblocca_sats`."""
    return asyncio.run(banco.SRV.premia_xp(
        tg_id, "ordine", punti, f"ordine:{oid}:{ruolo}"))


def start(client, tg_id, nome, carico):
    """Un /start dalla rotta del campanello, come lo manda Telegram."""
    BOT.clear()
    r = client.post(
        "/api/telegram/aggiornamenti",
        headers={"x-telegram-bot-api-secret-token": "collaudo"},
        json={"update_id": abs(tg_id), "message": {
            "message_id": 1, "text": f"/start {carico}".strip(),
            "from": {"id": tg_id, "first_name": nome, "is_bot": False},
            "chat": {"id": tg_id, "type": "private"}}})
    return r.status_code, [d.get("text", "") for m, d in BOT
                           if m == "sendMessage"]


def a_mano(tg_id, codice):
    """Il campo a mano del Profilo: None se passa, la frase del 400 se
    no."""
    banco.come(tg_id)
    try:
        banco.chiama(banco.SRV.inserisci_invito, None,
                     corpo={"codice": codice})
        return None
    except banco.SRV.HTTPException as e:
        return e.detail


def profilo(tg_id):
    banco.come(tg_id)
    return banco.chiama(banco.SRV.mio_profilo)


def main():
    print("=" * 58)
    print("  I CODICI INVITO — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    _gancio_vero()
    SRV.bot_api = _bot_finto
    SRV.aggiorna_profilo_social = _zitto
    from fastapi.testclient import TestClient
    client = TestClient(SRV.app)

    # ---- 1) il /start col codice, dalla rotta del campanello --------
    print("\n[il link del bot]")
    persona(222, "Ermenegildo", 400)       # chi invita: iscritto da un pezzo
    persona(223, "Altobello", 400)
    persona(111, "Terzo", 400)
    c222, c223 = codice_di(222), codice_di(223)
    prova("il codice ha la sua forma canonica", c222,
          SRV.normalizza_codice_invito(c222))
    prova("...ed e' fermo: chiederlo di nuovo da' lo stesso", c222,
          codice_di(222))
    stato, testi = start(client, 333, "Zefirina", c222)
    prova("il campanello risponde 200", 200, stato)
    prova("chi arriva dal link e' collegato da solo", (222, "link"),
          invitante_di(333))
    con = _db()
    reg = con.execute("SELECT registrato FROM utenti WHERE tg_id=333"
                      ).fetchone()["registrato"]
    con.close()
    prova("...ed e' in anagrafe da adesso (e' l'iscrizione)", True,
          abs(time.time() - reg) < 120)
    prova("il benvenuto resta UNO", 1, len(testi))
    prova("...e porta la riga dell'invito IN CODA", True,
          bool(testi) and testi[0].startswith("🫙")
          and "Sei arrivato con un invito" in testi[0])
    prova("...senza nominare chi ha invitato", True,
          bool(testi) and "Ermenegildo" not in testi[0])
    stato, testi = start(client, 333, "Zefirina", c223)
    prova("un secondo link non cambia chi ha invitato", (222, "link"),
          invitante_di(333))
    prova("...e lo dice", True, bool(testi) and "una volta sola" in testi[0])
    ricopiato = c222[:3].lower() + "-" + c222[3:].lower()
    start(client, 334, "Quintiliana", ricopiato)
    prova("minuscole e un trattino in mezzo valgono lo stesso",
          (222, "link"), invitante_di(334))
    stato, testi = start(client, 335, "Fusione", "ab" * 16)
    prova("un esadecimale da 32 va alla fusione, non agli inviti", None,
          invitante_di(335))
    prova("...e riceve la risposta della fusione", True,
          bool(testi) and "scaduto" in testi[0])
    stato, testi = start(client, 336, "Nuda", "")
    prova("il /start nudo e' il benvenuto di sempre", True,
          bool(testi) and "invito" not in testi[0].lower())
    persona(337, "Veterano", 30)
    stato, testi = start(client, 337, "Veterano", c222)
    prova("chi e' iscritto da un mese il link non lo collega", None,
          invitante_di(337))
    prova("...e sente perche'", True, bool(testi) and "7 giorni" in testi[0])
    stato, testi = start(client, 222, "Ermenegildo", c222)
    prova("il proprio link non collega", None, invitante_di(222))
    prova("...e lo dice", True, bool(testi) and "tuo codice" in testi[0])

    # ---- 2) il campo a mano -----------------------------------------
    print("\n[il campo a mano]")
    persona(340, "Anselma", 2)
    prova("il campo collega", None, a_mano(340, c222))
    prova("...dalla sua porta", (222, "codice"), invitante_di(340))
    prova("...UNA volta sola", True,
          "una volta sola" in (a_mano(340, c223) or ""))
    prova("...e il primo resta", (222, "codice"), invitante_di(340))
    persona(341, "Bartolomea", 8)
    prova("otto giorni dopo l'iscrizione il campo e' chiuso", True,
          "7 giorni" in (a_mano(341, c222) or ""))
    persona(342, "Cesira", 6.9)
    prova("...a sei giorni e ventun ore e' ancora aperto", None,
          a_mano(342, c222))
    persona(343, "Pioniera", registrato=0)
    prova("chi c'era prima del timbro dell'iscrizione non ha finestra",
          True, "7 giorni" in (a_mano(343, c222) or ""))
    persona(344, "Domitilla", 1)
    prova("un codice di forma sbagliata si dice", True,
          "caratteri" in (a_mano(344, "ciao!") or ""))
    con = _db()
    preso = con.execute("SELECT 1 FROM inviti_codici WHERE codice='BBBBBB'"
                        ).fetchone()
    con.close()
    if not preso:
        prova("...e uno che non esiste anche", True,
              "Non trovo" in (a_mano(344, "BBBBBB") or ""))
    prova("il proprio codice non vale", True,
          "tuo codice" in (a_mano(344, codice_di(344)) or ""))
    prova("...e chi ci ha provato resta libero", None, invitante_di(344))
    persona(345, "Elio", 1)
    persona(346, "Filiberta", 1)
    persona(347, "Gualtiero", 1)
    prova("Filiberta entra col codice di Elio", None,
          a_mano(346, codice_di(345)))
    prova("A invita B: B non puo' invitare A", True,
          "in tondo" in (a_mano(345, codice_di(346)) or ""))
    prova("Gualtiero entra col codice di Filiberta", None,
          a_mano(347, codice_di(346)))
    prova("...e il giro LUNGO e' chiuso lo stesso", True,
          "in tondo" in (a_mano(345, codice_di(347)) or ""))
    prova("...ma Elio resta libero di entrare con un altro codice", None,
          a_mano(345, c222))
    con = _db()
    try:
        con.execute("INSERT INTO inviti(invitato, invitante, creato, via) "
                    "VALUES(348, 348, 0, 'a mano')")
        passato = True
    except sqlite3.IntegrityError:
        passato = False
    con.rollback()
    con.close()
    prova("lo SCHEMA stesso rifiuta l'auto-invito (il CHECK)", False,
          passato)

    # ---- 3) il cassetto in /api/me ----------------------------------
    print("\n[il cassetto del Profilo]")
    me = profilo(222)
    inv = me.get("inviti") or {}
    prova("il cassetto ha il codice", c222, inv.get("codice"))
    prova("...e il link del bot con lo start", f"{SRV.LINK_BOT}?start={c222}",
          inv.get("link"))
    prova("...e QUANTE persone (Zefirina, Quintiliana, Anselma, Cesira, "
          "Elio)", 5, inv.get("persone"))
    prova("...e la percentuale viene dal server", 5, inv.get("percento"))
    tutto = json.dumps(me, ensure_ascii=False)
    prova("nessun nome di chi e' stato invitato esce", [],
          [n for n in ("Zefirina", "Quintiliana", "Anselma", "Cesira")
           if n in tutto])
    me = profilo(340)
    prova("l'invitata sa di essere arrivata con un invito", True,
          me["inviti"]["invitato"])
    prova("...il suo campo e' chiuso", 0, me["inviti"]["campo_fino"])
    prova("...e il nome di chi l'ha invitata non esce", False,
          "Ermenegildo" in json.dumps(me, ensure_ascii=False))
    me = profilo(344)
    prova("chi e' appena arrivato senza invito vede il campo", True,
          me["inviti"]["campo_fino"] > time.time())
    me = profilo(341)
    prova("...e chi e' arrivato da otto giorni no", 0,
          me["inviti"]["campo_fino"])

    # ---- 4) la quota, dal gancio vero -------------------------------
    print("\n[la quota a ogni accredito]")
    # IL NONNO: chi ha invitato Ermenegildo. Serve a vedere che la quota
    # non fa catena, e che gli XP PROPRI di Ermenegildo invece la fanno.
    persona(350, "Nonno", 400)
    accredita(350, 1000, ordine(350, 111), "venditore")
    collega_a_mano(222, 350)
    o = ordine(111, 333)
    accredita(333, 100, o, "compratore")
    prova("con zero XP propri chi invita non prende niente (il tetto)",
          [], quote_di(222))
    prova("...ma l'invitata i suoi li ha tutti", 100, xp_di(333))
    accredita(222, 100, ordine(222, 111), "venditore")
    prova("gli XP PROPRI di chi invita pagano chi l'ha invitato", [5],
          [q[0] for q in quote_di(350)])
    o = ordine(111, 333)
    accredita(333, 100, o, "compratore")
    prova("il 5% di 100 e' 5, col riferimento che porta l'accredito",
          [(5, f"invito:333:ordine:{o}:compratore")], quote_di(222))
    prova("...e chi invita ha 100 propri + 5", 105, xp_di(222))
    prova("NIENTE CATENA: la quota di Ermenegildo non paga il Nonno", [5],
          [q[0] for q in quote_di(350)])
    accredita(333, 2000, ordine(111, 333), "compratore")
    prova("il tetto taglia allo spazio che resta: 100 teorici, ne "
          "entrano 95", 95, quote_di(222)[-1][0])
    prova("...e il numero e' il doppio dei propri, non di piu'", 200,
          xp_di(222))
    accredita(333, 2000, ordine(111, 333), "compratore")
    prova("a tetto pieno non entra piu' niente", 2, len(quote_di(222)))
    o6 = ordine(222, 333)                  # Zefirina compra DA Ermenegildo
    accredita(222, 50, o6, "venditore")    # lo spazio si riapre: 150 propri
    accredita(333, 60, o6, "compratore")
    prova("un affare con chi ha invitato NON paga quota (lo spazio c'era)",
          2, len(quote_di(222)))
    o7 = ordine(111, 340)
    accredita(340, 39, o7, "compratore")
    prova("il 5% si arrotonda per difetto: 39 -> 1", 1, quote_di(222)[-1][0])
    accredita(340, 19, ordine(111, 340), "compratore")
    prova("...e 19 -> niente", 3, len(quote_di(222)))
    prova("il retry non paga due volte", 0, accredita(340, 39, o7,
                                                      "compratore"))
    prova("...ne' l'accredito ne' la quota", 3, len(quote_di(222)))
    con = _db()
    con.execute("UPDATE inviti SET creato=creato-3*365*86400")
    con.commit()
    con.close()
    accredita(340, 100, ordine(111, 340), "compratore")
    prova("A VITA: tre anni dopo il collegamento la quota paga ancora", 4,
          len(quote_di(222)))

    # IL NUMERO E' UNO SOLO, da quattro strade
    con = _db()
    prova("il riallineamento d'avvio non trova niente da correggere", 0,
          SRV.riallinea_xp_commercio(con))
    _v, _c, xp_rank, _a = SRV._dati_classifica(con)
    con.close()
    prova("il Profilo e il rank dicono lo stesso numero, quote comprese",
          xp_di(222), xp_rank.get(222))
    me = profilo(222)
    # LA SOGLIA DEGLI INVITATI ATTIVI (set 2026, ritocchi piccoli): qui
    # Ermenegildo ne ha DUE, Zefirina e Anselma, e sotto la soglia il
    # server non dice nessuna cifra — ne' la scomposizione ne' il
    # cassetto. Poi compra Cesira, e dalla terza le cifre tornano: le tre
    # prove di sotto, EMENDATE, guardano quel momento (prima l'ultima
    # passava per la ragione sbagliata, None contro None).
    prova("con due invitati attivi la scomposizione accorpa: nessuna "
          "cifra", {"accorpati": True, "attivi_min": 3}, me.get("xp_ruoli"))
    prova("...e il cassetto non la dice nemmeno lui", None,
          (me.get("inviti") or {}).get("xp"))
    accredita(342, 100, ordine(111, 342), "compratore")
    me = profilo(222)
    ruoli = me.get("xp_ruoli") or {}
    prova("la scomposizione ha il terzo lato, e fa il totale", me["xp"],
          sum(ruoli.values()))
    prova("...il terzo lato e' quello degli inviti", 5 + 95 + 1 + 5 + 5,
          ruoli.get("inviti"))
    prova("...e il cassetto dice gli stessi punti", ruoli.get("inviti"),
          (me.get("inviti") or {}).get("xp"))

    # ---- 5) la fusione di due account -------------------------------
    print("\n[la fusione]")
    # A) L'AUTO-INVITO: la meta' Telegram ha invitato la sua meta' Nostr.
    persona(600, "Telegramma", 3)
    nostrano(-601, "Chiave")
    collega_a_mano(-601, 600)
    accredita(600, 100, ordine(600, 111), "venditore")
    accredita(-601, 100, ordine(111, -601), "compratore")
    prova("prima della fusione la meta' Telegram ha la quota della sua "
          "meta' Nostr", [5], [q[0] for q in quote_di(600)])
    esito = SRV.esegui_fusione(600, -601)
    prova("la fusione passa, e il CHECK non la fa cadere", True,
          isinstance(esito, dict))
    prova("l'invito fra le due meta' se ne va", (None, None),
          (invitante_di(-601), invitante_di(600)))
    prova("...e la quota nata dalla meta' fusa pure", [], quote_di(600))
    prova("...il numero si rifa' dal registro: 100 + 100 propri", 200,
          xp_di(600))
    # B) IL GIRO IN TONDO nato fondendo: X invitata da N, P invitato da X.
    persona(610, "Pafnuzio", 3)
    nostrano(-611, "Nostromo")
    persona(612, "Xenia", 3)
    c610, c611 = codice_di(610), codice_di(-611)
    collega_a_mano(612, -611)
    collega_a_mano(610, 612)
    esito = SRV.esegui_fusione(610, -611)
    prova("B) la fusione passa", True, isinstance(esito, dict))
    prova("chi era invitata dalla meta' che muore passa a quella che "
          "resta", 610, (invitante_di(612) or (0,))[0])
    prova("...e il giro in tondo che ne nasceva si spezza", None,
          invitante_di(610))
    con = _db()
    codici = [r[0] for r in con.execute(
        "SELECT codice FROM inviti_codici WHERE tg_id IN (610, -611)")]
    con.close()
    prova("il codice che resta e' quello della meta' Telegram", [c610],
          codici)
    persona(613, "Ultima", 1)
    prova("...e il codice della meta' che muore si spegne", True,
          "Non trovo" in (a_mano(613, c611) or ""))
    # C) L'AFFARE DIVENTATO «CON CHI HA INVITATO»: Ylenia (Telegram) ha
    # invitato Zita, e Zita ha comprato dalla meta' Nostr di Ylenia.
    persona(620, "Ylenia", 3)
    nostrano(-621, "Nostra")
    persona(622, "Zita", 3)
    collega_a_mano(622, 620)
    accredita(620, 100, ordine(620, 111), "venditore")
    oc = ordine(-621, 622)
    accredita(622, 100, oc, "compratore")
    prova("prima della fusione la quota c'e' (l'affare era con un altro "
          "account)", [5], [q[0] for q in quote_di(620)])
    esito = SRV.esegui_fusione(620, -621)
    prova("C) la fusione passa", True, isinstance(esito, dict))
    prova("...e la quota di un affare diventato con chi ha invitato se "
          "ne va", [], quote_di(620))
    prova("...mentre il collegamento resta", (620, "banco"),
          invitante_di(622))
    # D) IL VERSO OPPOSTO: la meta' Telegram era stata invitata dalla sua
    # meta' Nostr. Qui a salvare la fusione e' SOLO il DELETE che viene
    # prima: l'UPDATE degli invitanti riscriverebbe la riga in un
    # auto-invito, e il CHECK farebbe cadere la fusione intera. E la
    # meta' Telegram, che un codice non l'aveva, eredita quello della
    # meta' Nostr: i link che quella aveva gia' condiviso restano vivi.
    persona(630, "Telesforo", 3)
    nostrano(-631, "Nostrana")
    c631 = codice_di(-631)
    collega_a_mano(630, -631)
    esito = SRV.esegui_fusione(630, -631)
    prova("D) la fusione passa anche nel verso opposto", True,
          isinstance(esito, dict))
    prova("...e l'auto-invito non c'e'", None, invitante_di(630))
    con = _db()
    rimasto = con.execute("SELECT codice FROM inviti_codici WHERE "
                          "tg_id=630").fetchone()
    con.close()
    prova("chi non aveva un codice eredita quello della meta' che muore",
          c631, rimasto["codice"] if rimasto else None)

    # ---- 6) l'azzeramento, simulato come lo dice il codice ----------
    print("\n[l'azzeramento degli XP]")
    con = _db()
    collegamenti = con.execute("SELECT COUNT(*) FROM inviti").fetchone()[0]
    dove, par = SRV.sql_xp_commercio()
    con.execute(f"DELETE FROM xp_eventi WHERE {dove}", par)
    SRV.riallinea_xp_commercio(con)
    con.commit()
    dopo = con.execute("SELECT COUNT(*) FROM inviti").fetchone()[0]
    somma = con.execute("SELECT COALESCE(SUM(xp),0) FROM utenti"
                        ).fetchone()[0]
    con.close()
    prova("azzerati gli XP, i collegamenti restano tutti", collegamenti,
          dopo)
    prova("...e i numeri sono tutti a zero", 0, somma)
    accredita(333, 100, ordine(111, 333), "compratore")
    prova("la regola riparte da zero: chi invita, senza XP propri, non "
          "prende", [], quote_di(222))
    accredita(222, 10, ordine(222, 111), "venditore")
    accredita(333, 100, ordine(111, 333), "compratore")
    prova("...e riprende appena guadagna in proprio", [5],
          [q[0] for q in quote_di(222)])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
