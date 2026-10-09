# -*- coding: utf-8 -*-
"""
LA CAMPAGNA P2P A TUTTI, SUL SERVER VERO (9 ott 2026, la vigilia del
lancio, richiesta di Andrea).

Il giorno che il P2P si apre partono due campagne una-tantum: quella di
sempre a chi aveva premuto «Avvisami» (`avvisa_interessi_p2p`) e quella
nuova a TUTTI gli altri iscritti (`avvisa_tutti_p2p`, leva
P2P_CAMPAGNA_TUTTI). Qui si guarda cosa parte davvero, RIAVVIO DOPO
RIAVVIO: ogni avvio e' un PROCESSO NUOVO col server importato da capo
(globali azzerati, come dopo un `systemctl restart`), sullo STESSO
database usa-e-getta — quel che resta fra un avvio e l'altro e' solo
quel che sta su disco, cioe' il timbro.

I quattro avvii, in fila:
  0. FASE CHIUSA (un id in P2P_PROVA_IDS) e leva accesa: non parte
     niente, e nessun timbro si brucia;
  1. P2P APERTO e leva SPENTA: parte solo la campagna di «Avvisami»
     (a 111 e alla nativa Nostr -7); quella a tutti tace e non timbra;
  2. P2P aperto e leva ACCESA: parte una volta sola, a tutti TRANNE chi
     ha premuto «Avvisami» — Telegram a 222 e 555 (che aveva votato le
     ASTE, non il P2P), il DM Nostr a -5, il 403 di 333 (bot bloccato)
     si salta e si dice; la riga finale del journal col totale;
  3. RIAVVIO con la leva ancora accesa: non riparte niente.
Alla fine: OGNUNO HA RICEVUTO UN MESSAGGIO SOLO, in tutto.

IL FINTO TELEGRAM: `_manda_telegram` sostituito da uno che segna il
messaggio e risponde come Telegram (ok col numero, o il 403 di chi ha
bloccato il bot); `_dm_nostr_con_ripiego` segna il DM. A scegliere il
canale e' la `notifica()` VERA.

NON TOCCA NIENTE DI VERO: il `config` di cartone si installa PRIMA
dell'import di server, il database e' usa-e-getta, i relay sono quello
morto (ws://127.0.0.1:9), niente rete, niente Telegram.

USO:  python collaudo_campagna_p2p_tutti.py
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0

# chi c'e': (tg_id, nome, npub d'accesso o None)
UTENTI = [(111, "Avvisami", None), (222, "Compra", None),
          (333, "Bloccato", None), (555, "Aste", None),
          (-5, "Nativa", "npub1collaudonativa5"),
          (-7, "NativaAvvisami", "npub1collaudonativa7")]
# chi ha premuto «Avvisami» sul P2P, e chi sulle aste
INTERESSI = [(111, "p2p"), (-7, "p2p"), (555, "aste")]
BLOCCATO = 333
MOSTRO_NPUB = ("npub14l3aax4gv9khctnzavek6wsj0nua42d5fq4tr6fkr4wpwhfm3n"
               "eswg6lg0")
SEGNO = "ESITO-CAMPAGNA:"


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# ------------------------- IL FIGLIO: UN AVVIO -------------------------

def avvio(percorso_db, leva, prova_ids, semina):
    """Un avvio del server: config di cartone, import, le due campagne
    nell'ordine dell'orologio, e un JSON con quel che e' partito."""
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: il config va "
                         "installato PRIMA.")
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
    cfg.DB = percorso_db
    # il P2P acceso, col relay MORTO: la regola dei giri dal vivo
    cfg.P2P_ATTIVO = True
    cfg.MOSTRO_NPUB = MOSTRO_NPUB
    cfg.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    cfg.MOSTRO_RELAY_SPECCHIO = []
    cfg.NOSTR_NSEC_PIATTAFORMA = "INCOLLA_QUI"
    cfg.P2P_PROVA_IDS = list(prova_ids)
    cfg.P2P_CAMPAGNA_TUTTI = leva
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server

    via = []          # (canale, destinatario, testo)

    async def telegram_finto(tg_id, testo):
        via.append(("telegram", tg_id, testo))
        if tg_id == BLOCCATO:
            return "telegram 403: non ha avviato il bot, o l'ha bloccato"
        return f"telegram ok (messaggio {len(via)})"

    async def dm_finto(npub, testo, ripiego):
        via.append(("nostr", npub, testo))

    server._manda_telegram = telegram_finto
    server._dm_nostr_con_ripiego = dm_finto

    if semina:
        con = server.db()
        for tg_id, nome, npub in UTENTI:
            con.execute("INSERT INTO utenti(tg_id, nome, negozio, registrato) "
                        "VALUES(?,?,?,?)",
                        (tg_id, nome, f"neg{abs(tg_id)}", 1_700_000_000))
            if npub:
                con.execute("UPDATE utenti SET npub=?, npub_accesso=?, "
                            "npub_verificata=1 WHERE tg_id=?",
                            (npub, npub, tg_id))
        for tg_id, funzione in INTERESSI:
            con.execute("INSERT INTO interessi(tg_id, funzione) VALUES(?,?)",
                        (tg_id, funzione))
        con.commit()
        con.close()

    async def giro():
        # l'ordine dell'orologio: prima «Avvisami», poi il lancio a tutti
        await server.avvisa_interessi_p2p()
        server.avvia_campagna_p2p_tutti()
        compito = server._TASK_CAMPAGNA_P2P_TUTTI
        if compito is not None:
            await compito
        return compito is not None

    lanciata = asyncio.run(giro())
    print(SEGNO + json.dumps({
        "via": via, "lanciata": lanciata,
        "timbro_tutti": server.timbro_letto("campagna_p2p_tutti"),
        "timbro_avvisami": server.timbro_letto("campagna_p2p_acceso"),
        "leva": server.P2P_CAMPAGNA_TUTTI}, ensure_ascii=False))


# ------------------------- IL PADRE: I QUATTRO AVVII -------------------

def un_avvio(percorso_db, leva, prova_ids, semina):
    amb = dict(os.environ)
    amb["PYTHONUTF8"] = "1"
    amb["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--avvio", percorso_db,
         json.dumps({"leva": leva, "prova_ids": prova_ids, "semina": semina})],
        cwd=QUI, env=amb, capture_output=True, encoding="utf-8",
        errors="replace", timeout=180)
    righe = r.stdout.splitlines()
    esiti = [x for x in righe if x.startswith(SEGNO)]
    if r.returncode != 0 or not esiti:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("⛔ l'avvio e' caduto")
    esito = json.loads(esiti[-1][len(SEGNO):])
    esito["journal"] = [x for x in righe if "Campagna" in x]
    return esito


def destinatari(esito):
    return sorted(str(d) for _c, d, _t in esito["via"])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 58)
    print("  LA CAMPAGNA P2P A TUTTI — riavvio dopo riavvio")
    print("=" * 58)
    tmp = tempfile.mkdtemp(prefix="barattolo-campagna-tutti-")
    percorso_db = os.path.join(tmp, "usa-e-getta.db")

    print("\n[avvio 0: fase chiusa, leva accesa]")
    e0 = un_avvio(percorso_db, True, [111], semina=True)
    prova("non parte niente", [], e0["via"])
    prova("...e nessun timbro si brucia", ("", ""),
          (e0["timbro_tutti"], e0["timbro_avvisami"]))
    prova("...il task nasce e tace subito", True,
          e0["lanciata"])

    print("\n[avvio 1: P2P aperto, leva SPENTA]")
    e1 = un_avvio(percorso_db, False, [], semina=False)
    prova("parte solo «Avvisami»: 111 su Telegram e -7 col DM",
          ["111", "npub1collaudonativa7"], destinatari(e1))
    prova("...col testo di «Avvisami»", True,
          all("Avevi chiesto di essere avvisato" in t for _c, _d, t in e1["via"]))
    prova("la campagna a tutti non e' nemmeno lanciata", False,
          e1["lanciata"])
    prova("...e il suo timbro e' intatto", "", e1["timbro_tutti"])
    prova("il journal non la nomina", [],
          [x for x in e1["journal"] if "a tutti" in x])

    print("\n[avvio 2: P2P aperto, leva ACCESA]")
    e2 = un_avvio(percorso_db, True, [], semina=False)
    prova("parte a tutti TRANNE chi ha premuto «Avvisami»",
          ["222", "333", "555", "npub1collaudonativa5"], destinatari(e2))
    prova("...la nativa Nostr col DM, gli altri su Telegram",
          {"222": "telegram", "333": "telegram", "555": "telegram",
           "npub1collaudonativa5": "nostr"},
          {str(d): c for c, d, _t in e2["via"]})
    testo = ("🔄 Su Barattolo è arrivato lo scambio P2P in euro!\n"
             "Da oggi puoi comprare e vendere bitcoin direttamente con "
             "altre persone, pagando con SEPA, Revolut e altri metodi.\n"
             "Apri Barattolo → P2P e prova 🫙")
    prova("...col testo deciso, lettera per lettera", True,
          all(t == testo for _c, _d, t in e2["via"]))
    prova("«Avvisami» non riparte", "fatto", e2["timbro_avvisami"])
    prova("il timbro della campagna a tutti e' scritto", "fatto",
          e2["timbro_tutti"])
    prova("il journal dice la partenza", True,
          any("parte verso 4 iscritti" in x for x in e2["journal"]))
    prova("...il saltato col perche'", True,
          any("saltato 333" in x and "403" in x for x in e2["journal"]))
    prova("...e il totale finale", True,
          any("inviati 3, saltati 1" in x for x in e2["journal"]))

    print("\n[avvio 3: riavvio, leva ancora accesa]")
    e3 = un_avvio(percorso_db, True, [], semina=False)
    prova("non riparte niente", [], e3["via"])
    prova("...e il journal tace", [], e3["journal"])

    print("\n[in tutto]")
    tutti = destinatari(e0) + destinatari(e1) + destinatari(e2) + destinatari(e3)
    prova("ognuno ha ricevuto UN messaggio solo", True,
          len(tutti) == len(set(tutti)))
    prova("...e tutti gli iscritti ne hanno ricevuto uno", 6, len(set(tutti)))

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--avvio":
        sys.stdout.reconfigure(encoding="utf-8")
        p = json.loads(sys.argv[3])
        avvio(sys.argv[2], p["leva"], p["prova_ids"], p["semina"])
    else:
        sys.exit(main())
