# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI PIONIERI CONGELATI (26 set 2026).

Il distintivo 🫙 Pioniere si ricalcolava sulla POSIZIONE, la coorte
«pioniere» era congelata alla prima scrittura: dopo una fusione
Telegram↔Nostr la riga Nostr cancellata faceva avanzare di uno tutti
quelli dietro, e il 101° si prendeva il distintivo senza la coorte —
cioe' senza lo sconto. Sul VPS e' successo a due persone, allineate a
mano da Andrea il 26 set 2026.

`prove.py` monta i pezzi su un database di cartone; qui gira il SERVER
VERO su un database usa-e-getta, con lo schema vero di `init_db`:

  1. il RIAVVIO: la passata dei distintivi da' il 🫙 ai soli pionieri
     di coorte, una riga d'anagrafe senza coorte in testa alla fila
     prende i «primi giorni» e non il pioniere, e il journal dice il
     conto — e nomina per tg_id chi ha il distintivo senza la coorte;
  2. la FUSIONE con la meta' Nostr pioniera: l'account che resta
     diventa pioniere (coorte, distintivo, titolo, sconto P2P) e il
     101°, che adesso sta al centesimo posto, NON avanza — ne' al
     primo sguardo al Profilo ne' al riavvio dopo;
  3. le altre tre fusioni: pioniera la meta' Telegram, pionieri tutt'e
     due (i pionieri scendono di uno e nessuno prende il posto), nessuno
     dei due (niente da portare).

NON TOCCA NIENTE DI VERO: il `config` di cartone lo installa `avvio()`
del banco dei pagamenti, PRIMA dell'import del server. Nessuna rete.

USO:  python collaudo_pionieri.py
"""

import contextlib
import io
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def _db():
    return banco.SRV.db()


def persona(tg_id, registrato, coorte):
    con = _db()
    con.execute("INSERT INTO utenti(tg_id, nome, negozio, registrato, "
                "coorte, avatar_aggiornato) VALUES(?,?,?,?,?,?)",
                (tg_id, f"U{tg_id}", f"neg{abs(tg_id)}", registrato, coorte,
                 int(time.time())))
    if tg_id < 0:
        finta = f"npub1collaudo{abs(tg_id)}"
        con.execute("UPDATE utenti SET npub=?, npub_accesso=? "
                    "WHERE tg_id=?", (finta, finta, tg_id))
    con.commit()
    con.close()


def coorte_di(tg_id):
    con = _db()
    r = con.execute("SELECT coorte FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    con.close()
    return r["coorte"] if r else None


def ha_distintivo(tg_id):
    con = _db()
    r = con.execute("SELECT 1 FROM badge_utente WHERE tg_id=? "
                    "AND badge_id='pioniere'", (tg_id,)).fetchone()
    con.close()
    return bool(r)


def pionieri():
    con = _db()
    n = con.execute("SELECT COUNT(*) FROM utenti "
                    "WHERE coorte='pioniere'").fetchone()[0]
    con.close()
    return n


def posizione(tg_id):
    con = _db()
    u = con.execute("SELECT registrato FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    n = con.execute("SELECT COUNT(*) FROM utenti WHERE registrato<? "
                    "OR (registrato=? AND tg_id<=?)",
                    (u["registrato"], u["registrato"], tg_id)).fetchone()[0]
    con.close()
    return n


def riavvio():
    """init_db come all'avvio del servizio, col journal catturato: le
    sole righe del controllo dei pionieri."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        banco.SRV.init_db()
    righe = out.getvalue().splitlines()
    return [r for i, r in enumerate(righe)
            if "Pionieri:" in r or (r.startswith("   tg_id ")
                                    and any("Pionieri:" in x
                                            for x in righe[:i]))]


def profilo(tg_id):
    """Il primo sguardo al Profilo: /api/me, che passa i distintivi e
    assegna la coorte a chi non ce l'ha."""
    banco.come(tg_id)
    return banco.chiama(banco.SRV.mio_profilo)


def main():
    print("=" * 58)
    print("  I PIONIERI CONGELATI — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV

    # LA FILA, come sul VPS: cento pionieri di coorte in ordine
    # d'iscrizione, poi i primi giorni. Al secondo posto c'e' la meta'
    # Nostr (-500) di qualcuno che su Telegram (1110) e' arrivato tardi;
    # al terzo un'altra meta' Nostr pioniera (-501) la cui meta'
    # Telegram (1005) e' pioniera anche lei.
    for k in range(1, 101):
        tg = {2: -500, 3: -501}.get(k, 1000 + k)
        persona(tg, 1_700_000_000 + k, "pioniere")
    for k in range(101, 109):
        persona(1000 + k, 1_700_000_000 + k, "primi_giorni")
    persona(-502, 1_700_000_000 + 109, "primi_giorni")   # Nostr, tardi
    persona(1110, 1_700_000_000 + 110, "primi_giorni")   # Telegram di -500
    # IL PREGRESSO: una riga senza coorte che per la sua data starebbe
    # in testa alla fila (registrato=0: chi c'era prima della colonna)
    persona(1200, 0, "")
    # LO STORTO di prima della cura: il distintivo senza la coorte
    con = _db()
    con.execute("INSERT INTO badge_utente(tg_id, badge_id, ottenuto_il) "
                "VALUES(1108,'pioniere',0)")
    con.commit()
    con.close()

    print("\n[il riavvio]")
    detto = riavvio()
    prova("la riga senza coorte in testa alla fila prende i primi giorni",
          ("primi_giorni", 1), (coorte_di(1200), posizione(1200)))
    prova("...e il distintivo NO, per quanto sia la prima", False,
          ha_distintivo(1200))
    prova("i cento pionieri di coorte hanno il distintivo", 100,
          sum(ha_distintivo({2: -500, 3: -501}.get(k, 1000 + k))
              for k in range(1, 101)))
    prova("il 101° e i dietro no", [False] * 7,
          [ha_distintivo(1000 + k) for k in range(101, 108)])
    prova("il journal dice il conto e nomina lo storto per tg_id",
          ["⚠️  Pionieri: 100 di coorte, 1 storti fra coorte e distintivo:",
           "   tg_id 1108: distintivo sì, coorte 'primi_giorni'"], detto)
    prova("...e non lo ripara: il distintivo resta, la coorte pure",
          (True, "primi_giorni"), (ha_distintivo(1108), coorte_di(1108)))
    # si torna al pulito, per leggere le righe dopo
    con = _db()
    con.execute("DELETE FROM badge_utente WHERE tg_id=1108")
    con.commit()
    con.close()
    prova("tutto a posto: una riga sola, col conto",
          ["🫙 Pionieri: 100, coorte e distintivo combaciano"], riavvio())
    # La riga del pregresso ha fatto il suo mestiere e se ne va: in testa
    # alla fila spingerebbe il 101° al 102° posto, e la fusione qui
    # sotto non lo porterebbe al centesimo — cioe' «non avanza» sarebbe
    # vero per la ragione sbagliata.
    con = _db()
    con.execute("DELETE FROM utenti WHERE tg_id=1200")
    con.commit()
    con.close()

    print("\n[la fusione con la meta' Nostr pioniera]")
    # Lo sconto P2P acceso come sul VPS (0,5 punti): a leva spenta non e'
    # attivo per nessuno, e la domanda qui sotto risponderebbe da sola.
    SRV.P2P_SCONTO_FEDELTA_PERCENTO = 0.5
    prova("il 101° sta al 101° posto", 101, posizione(1101))
    esito = SRV.esegui_fusione(1110, -500)
    prova("la fusione passa", True, isinstance(esito, dict))
    prova("l'account che resta e' pioniere: coorte e distintivo",
          ("pioniere", True), (coorte_di(1110), ha_distintivo(1110)))
    prova("...e il titolo 🌱 gli e' disponibile", True,
          "coorte_pioniere" in SRV.titoli_disponibili(_db(), 1110))
    con = _db()
    prova("...lo sconto P2P lo vede pioniere", "pioniere",
          SRV._sconto_p2p(con, 1110)["motivo"])
    prova("...e anche lo sconto fedelta' del mercatino", (True, False),
          SRV._fedelta_lato(con, 1110))
    con.close()
    prova("i pionieri restano cento", 100, pionieri())
    prova("il 101° adesso sta al CENTESIMO posto", 100, posizione(1101))
    me = profilo(1101)
    prova("...ma al primo sguardo al Profilo NON avanza",
          ("primi_giorni", False), (coorte_di(1101), ha_distintivo(1101)))
    prova("...e il suo profilo non gli promette lo sconto da pioniere",
          {"attivo": False, "motivo": "", "punti": 0.5},
          me.get("p2p_sconto"))
    prova("...ne' al riavvio dopo",
          (["🫙 Pionieri: 100, coorte e distintivo combaciano"],
           "primi_giorni", False),
          (riavvio(), coorte_di(1101), ha_distintivo(1101)))

    print("\n[le altre fusioni]")
    # pionieri tutt'e due: se ne perde uno, e nessuno prende il posto
    esito = SRV.esegui_fusione(1005, -501)
    prova("pionieri tutt'e due: resta pioniere", ("pioniere", True),
          (coorte_di(1005), ha_distintivo(1005)))
    profilo(1102)
    prova("...i pionieri scendono a 99 e nessuno avanza, nemmeno chi e' "
          "salito a 99 e 100",
          (99, 99, 100, "primi_giorni", "primi_giorni", False, False),
          (pionieri(), posizione(1101), posizione(1102), coorte_di(1101),
           coorte_di(1102), ha_distintivo(1101), ha_distintivo(1102)))
    # nessuno dei due: niente da portare
    esito = SRV.esegui_fusione(1107, -502)
    prova("nessuno dei due pioniere: resta dei primi giorni",
          ("primi_giorni", False), (coorte_di(1107), ha_distintivo(1107)))
    # pioniera la sola meta' Telegram: la coorte e' gia' sua
    persona(-503, 1_700_000_000 + 200, "primi_giorni")
    esito = SRV.esegui_fusione(1004, -503)
    prova("pioniera la sola meta' Telegram: resta pioniere",
          ("pioniere", True), (coorte_di(1004), ha_distintivo(1004)))
    prova("il riavvio finale: 99 pionieri, coorte e distintivo combaciano",
          ["🫙 Pionieri: 99, coorte e distintivo combaciano"], riavvio())
    prova("...e nessuno oltre i cento di ieri e' diventato pioniere", [],
          [tg for tg in range(1101, 1109)
           if coorte_di(tg) == "pioniere" or ha_distintivo(tg)])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
