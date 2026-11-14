# -*- coding: utf-8 -*-
"""
L'INVITO DEL CODICE SCONTO AI CLIENTI, SUL SERVER VERO (14 nov 2026,
cantiere invito-codice-sconto, richiesta di un venditore via Andrea).

Vende (333) ha un codice «AMICI15» da 30 giorni e cinque persone intorno:
  · Fedele (222): due ordini PAGATI da Vende → cliente;
  · Abbandona (444): un ordine mai pagato ('creato') e uno 'annullato' →
    NON e' cliente;
  · Altrove (555): ha comprato solo da un ALTRO negozio → non compare;
  · Zitto (666): cliente, ma ha spento «🎟️ Offerte dei negozi» → non
    compare nemmeno;
  · Nativa (-5): cliente che entra con Nostr → riceve il DM cifrato.
Si guarda:
  1. il FOGLIO: solo i clienti veri, col numero d'ordine come maniglia e
     MAI un tg_id; il codice di un altro e' un 404;
  2. L'INVIO: il messaggio parte con codice, cifra, scadenza, negozio e
     la riga per dire basta, sulla strada che il cliente ha scelto
     (`notifica()` vera, trasporti di cartone);
  3. UNA VOLTA PER CODICE: il secondo «Invia» non manda niente;
  4. LA CINTURA DEI GIORNI: un secondo codice dentro la settimana
     salta, passata la settimana parte;
  5. I NUMERI INVENTATI: un numero d'ordine altrui non porta a nessuno;
  6. IL CODICE MORTO: in pausa non si condivide (409), e una riga in
     coda si consuma senza messaggio se il codice muore prima;
  7. IL NO DEL CLIENTE: «🔕» su un negozio lo toglie dal foglio e dalla
     coda; l'interruttore generale pure; il numero altrui e' un 404;
  8. IL TETTO PER VOLTA: oltre CODICI_SCONTO_INVITI_MAX restano i
     `rimasti`;
  9. la leva spenta chiude le rotte (409) ma dire basta funziona.

NON TOCCA NIENTE DI VERO: config finto PRIMA dell'import di server,
database usa-e-getta, niente rete, niente Telegram, niente relay.

USO:  python collaudo_invito_codice.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
VIA = []          # (canale, destinatario, testo)

FEDELE, VENDE, ABBANDONA, ALTROVE, ZITTO, NATIVA, ALTRO_NEGOZIO = (
    222, 333, 444, 555, 666, -5, 777)
NOMI = {FEDELE: "Fedele", VENDE: "Vende", ABBANDONA: "Abbandona",
        ALTROVE: "Altrove", ZITTO: "Zitto", NATIVA: "Nativa",
        ALTRO_NEGOZIO: "Altro Negozio"}


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
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-invito-codice-")
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
    cfg.DB = os.path.join(tmp, "usa-e-getta.db")
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def telegram_finto(tg_id, testo, *a, **k):
        VIA.append(("telegram", tg_id, testo))
        return "ok"

    async def dm_finto(npub, testo, ripiego, *a, **k):
        VIA.append(("nostr", npub, testo))

    async def zitto(*a, **k):
        return None

    server._manda_telegram = telegram_finto
    server._dm_nostr_con_ripiego = dm_finto
    server._avviso_in_app_sottofondo = zitto
    server.PAUSA_INVITI = 0
    return tmp


def testata(tg_id):
    return f"collaudo:{tg_id}:{NOMI.get(tg_id, 'Utente')}"


async def lascia_finire():
    io = asyncio.current_task()
    fine = asyncio.get_running_loop().time() + 30
    while True:
        altri = [x for x in asyncio.all_tasks() if x is not io and not x.done()]
        if not altri or asyncio.get_running_loop().time() > fine:
            return not altri
        await asyncio.wait(altri, timeout=1)


def chiama(rotta, corpo, tg_id, *args):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi

    async def giro():
        try:
            if corpo is None:
                r = await rotta(*args, x_tg_init_data=testata(tg_id))
            else:
                r = await rotta(*args, None, x_tg_init_data=testata(tg_id))
        except SRV.HTTPException as e:
            r = {"errore": e.status_code, "detail": e.detail}
        await lascia_finire()
        return r
    return asyncio.run(giro())


def semina():
    con = SRV.db()
    for tg_id, nome in NOMI.items():
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg_id, nome, f"neg{abs(tg_id)}"))
    con.execute("UPDATE utenti SET npub_accesso='npub1nativa' WHERE tg_id=?", (NATIVA,))
    con.execute("UPDATE utenti SET offerte_negozi=0 WHERE tg_id=?", (ZITTO,))
    ordini = [(FEDELE, VENDE, "released", 100), (FEDELE, VENDE, "shipped", 200),
              (ABBANDONA, VENDE, "creato", 300), (ABBANDONA, VENDE, "annullato", 400),
              (ALTROVE, ALTRO_NEGOZIO, "released", 500),
              (ZITTO, VENDE, "confirmed", 600), (NATIVA, VENDE, "locked", 700)]
    for comp, vend, stato, quando in ordini:
        con.execute("INSERT INTO ordini(annuncio_id, compratore_id, venditore_id, "
                    "stato, creato, aggiornato) VALUES(1,?,?,?,?,?)",
                    (comp, vend, stato, quando, quando))
    con.commit()
    righe = {r["compratore_id"]: r["id"] for r in con.execute(
        "SELECT compratore_id, MAX(id) AS id FROM ordini GROUP BY compratore_id")}
    con.close()
    return righe


def crea_codice(nome, tg_id=VENDE, giorni=30):
    r = chiama(SRV.salva_codice_sconto, {"codice": nome, "tipo": "percento",
                                         "percento": 15, "giorni": giorni}, tg_id)
    return r["codice"]["id"]


def foglio(cid, tg_id=VENDE):
    return chiama(SRV.clienti_codice_sconto, None, tg_id, cid)


def invita(cid, ordini, tg_id=VENDE):
    return chiama(SRV.invita_codice_sconto, {"ordini": ordini}, tg_id, cid)


def a_chi():
    return sorted(str(chi) for _, chi, _ in VIA)


def main():
    tmp = avvio()
    ultimo = semina()

    print("\n[1) il foglio: solo i clienti veri, mai un tg_id]")
    cid = crea_codice("AMICI15")
    f = foglio(cid)
    nomi = [c["nome"] for c in f["clienti"]]
    prova("compaiono Nativa e Fedele, dal piu' recente; non Abbandona, Altrove, Zitto",
          ["Nativa", "Fedele"], nomi)
    prova("la maniglia e' il numero dell'ultimo ordine",
          [ultimo[NATIVA], ultimo[FEDELE]], [c["ordine"] for c in f["clienti"]])
    prova("nessun tg_id, username o npub esce verso il venditore", True,
          all(set(c) == {"ordine", "nome", "ultimo", "ordini", "stato", "invitato_il"}
              for c in f["clienti"]))
    prova("Fedele ha due ordini", 2, [c["ordini"] for c in f["clienti"] if c["nome"] == "Fedele"][0])
    prova("il codice vale e la leva arriva al client", (True, True, 7, 200),
          (f["vale"], f["inviti"], f["inviti_giorni"], f["inviti_max"]))
    prova("il codice di un altro e' un 404", 404, foglio(cid, ALTRO_NEGOZIO).get("errore"))
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(VENDE)))
    prova("/api/me porta la leva nella busta dei codici", True,
          me["codici_sconto_leve"]["inviti"])

    print("\n[2) l'invio, sulla strada del cliente]")
    VIA.clear()
    r = invita(cid, [ultimo[FEDELE], ultimo[NATIVA]])
    prova("due in coda, nessuno saltato", (2, 0, 0),
          (r.get("accodati"), r.get("saltati"), r.get("rimasti")))
    prova("Fedele sul bot, Nativa col DM", ["222", "npub1nativa"], a_chi())
    testo = VIA[0][2] if VIA else ""
    prova("il messaggio dice chi, il codice, la cifra, la scadenza, il negozio e come dire basta",
          True, all(p in testo for p in ("<b>Vende</b>", "<code>AMICI15</code>",
                                          "−15%", "Valido fino al", "/negozio/neg333",
                                          "Profilo → «🔔 Avvisi»")))
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(FEDELE)))
    prova("nel cassetto di Fedele c'e' il negozio che gli ha scritto", ["Vende"],
          [n["nome"] for n in me["offerte_negozi_lista"]])

    print("\n[3) una volta per codice]")
    VIA.clear()
    r = invita(cid, [ultimo[FEDELE], ultimo[NATIVA]])
    prova("il secondo Invia non accoda niente e conta due saltati", (0, 2), (r["accodati"], r["saltati"]))
    prova("...e non parte niente", 0, len(VIA))
    prova("il foglio dice «gia' invitato»", {"gia_invitato"},
          {c["stato"] for c in foglio(cid)["clienti"]})

    print("\n[4) la cintura dei giorni]")
    cid2 = crea_codice("NATALE10")
    prova("un altro codice dentro la settimana: «da_poco»", {"da_poco"},
          {c["stato"] for c in foglio(cid2)["clienti"]})
    VIA.clear()
    r = invita(cid2, [ultimo[FEDELE]])
    prova("...e l'Invia lo salta", (0, 1, 0), (r["accodati"], r["saltati"], len(VIA)))
    con = SRV.db()
    con.execute("UPDATE inviti_codice SET accodato=accodato-8*86400")
    con.commit()
    con.close()
    r = invita(cid2, [ultimo[FEDELE]])
    prova("passati otto giorni parte", (1, ["222"]), (r["accodati"], a_chi()))

    print("\n[5) i numeri inventati]")
    cid3 = crea_codice("PROVA5")
    con = SRV.db()
    con.execute("UPDATE inviti_codice SET accodato=accodato-30*86400")
    con.commit()
    con.close()
    VIA.clear()
    r = invita(cid3, [ultimo[ALTROVE], ultimo[ABBANDONA], 999999])
    prova("ordini di altri negozi, non pagati o inventati: nessuno parte", (0, 3, 0),
          (r["accodati"], r["saltati"], len(VIA)))
    prova("una lista vuota e' un 400", 400, invita(cid3, []).get("errore"))
    prova("un numero storto e' un 400", 400, invita(cid3, ["abc"]).get("errore"))

    print("\n[6) il codice morto]")
    chiama(SRV.pausa_codice_sconto, None, VENDE, cid3)
    prova("in pausa non si condivide", 409, invita(cid3, [ultimo[FEDELE]]).get("errore"))
    prova("...e il foglio lo dice", False, foglio(cid3)["vale"])
    chiama(SRV.pausa_codice_sconto, None, VENDE, cid3)
    con = SRV.db()
    con.execute("INSERT INTO inviti_codice(codice_id, venditore_id, tg_id, accodato, mandato) "
                "VALUES(?,?,?,?,0)", (cid3, VENDE, FEDELE, 1))
    con.execute("UPDATE codici_sconto SET attivo=0 WHERE id=?", (cid3,))
    con.commit()
    con.close()
    VIA.clear()
    asyncio.run(SRV._giro_inviti_codice())
    con = SRV.db()
    m = con.execute("SELECT mandato FROM inviti_codice WHERE codice_id=? AND tg_id=?",
                    (cid3, FEDELE)).fetchone()["mandato"]
    con.execute("UPDATE codici_sconto SET attivo=1 WHERE id=?", (cid3,))
    con.commit()
    con.close()
    prova("una riga in coda di un codice morto si consuma senza messaggio", (1, 0), (m, len(VIA)))

    print("\n[7) il no del cliente]")
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(NATIVA)))
    inv = me["offerte_negozi_lista"][0]["invito"]
    r = chiama(SRV.scegli_offerte_negozi, {"invito": inv, "zitto": True}, NATIVA)
    prova("🔕 su Vende: la lista lo dice zitto", True, r["offerte_negozi_lista"][0]["zitto"])
    cid4 = crea_codice("ZITTI20")
    prova("...e Nativa sparisce dal foglio di Vende", ["Fedele"],
          [c["nome"] for c in foglio(cid4)["clienti"]])
    con = SRV.db()
    con.execute("INSERT INTO inviti_codice(codice_id, venditore_id, tg_id, accodato, mandato) "
                "VALUES(?,?,?,?,0)", (cid4, VENDE, NATIVA, 1))
    con.commit()
    con.close()
    VIA.clear()
    asyncio.run(SRV._giro_inviti_codice())
    prova("una riga gia' in coda verso chi ha detto basta non parte", 0, len(VIA))
    r = chiama(SRV.scegli_offerte_negozi, {"invito": inv, "zitto": False}, NATIVA)
    prova("riaccendere toglie lo zitto", False, r["offerte_negozi_lista"][0]["zitto"])
    r = chiama(SRV.scegli_offerte_negozi, {"attive": False}, FEDELE)
    prova("l'interruttore generale si spegne", False, r["offerte_negozi"])
    prova("...e Fedele sparisce dal foglio", ["Nativa"], [c["nome"] for c in foglio(cid4)["clienti"]])
    chiama(SRV.scegli_offerte_negozi, {"attive": True}, FEDELE)
    prova("il numero d'invito di un altro e' un 404", 404,
          chiama(SRV.scegli_offerte_negozi, {"invito": inv, "zitto": True}, ALTROVE).get("errore"))

    print("\n[8) il tetto per volta]")
    con = SRV.db()
    con.execute("UPDATE inviti_codice SET accodato=accodato-30*86400")
    con.commit()
    con.close()
    SRV.CODICI_SCONTO_INVITI_MAX = 1
    VIA.clear()
    cid5 = crea_codice("UNO1")
    r = invita(cid5, [ultimo[FEDELE], ultimo[NATIVA]])
    prova("con tetto 1: uno parte, uno resta per il giro dopo", (1, 0, 1, 1),
          (r["accodati"], r["saltati"], r["rimasti"], len(VIA)))
    SRV.CODICI_SCONTO_INVITI_MAX = 200

    print("\n[9) la leva spenta]")
    SRV.CODICI_SCONTO_INVITI = False
    prova("foglio e Invia rispondono 409", (409, 409),
          (foglio(cid5).get("errore"), invita(cid5, [ultimo[FEDELE]]).get("errore")))
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(VENDE)))
    prova("/api/me lo dice al client (niente tasto)", False, me["codici_sconto_leve"]["inviti"])
    r = chiama(SRV.scegli_offerte_negozi, {"attive": False}, FEDELE)
    prova("...ma dire basta funziona lo stesso", False, r.get("offerte_negozi"))
    SRV.CODICI_SCONTO_INVITI = True

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
