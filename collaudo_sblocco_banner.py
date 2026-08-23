"""IL GIRO VERO DELLO SBLOCCO A PAGAMENTO DEL BANNER (ago 2026).

Le sentinelle di `prove.py` dicono che le guardie ci sono e che la
forma e' giusta; qui il SERVER VERO gira su un database usa-e-getta e
si guarda cosa RISPONDE — che e' un'altra domanda, e su un cantiere
che incassa sats e' quella che conta.

Il giro: porta chiusa -> fattura -> pagata -> porta aperta -> banner
chiesto e approvato. Piu' i due rami dell'orologio, la fusione che si
porta dietro la porta, e la regressione che chi ha il LIVELLO non
cambia di un byte.

LNBITS E' SIMULATO, sempre: un collaudo non conia fatture vere senza
che nessuno l'abbia chiesto (la lezione del 12 ago 2026). Qui in piu'
non servirebbe a niente — quel che si prova e' la macchina nostra.

    python collaudo_sblocco_banner.py
"""
import asyncio
import os
import sys
import tempfile

os.environ["PYTHONIOENCODING"] = "utf-8"

# --- il config di cartone, PRIMA dell'import del server -------------
# (o si aprirebbe il database di casa: il patto dei collaudi)
_tmp = tempfile.mkdtemp(prefix="collaudo_sblocco_")
_conf = os.path.join(_tmp, "config.py")
_DB = os.path.join(_tmp, "collaudo.db").replace("\\", "/")
_RIGHE = [
    "DB = r'" + _DB + "'",
    "BOT_TOKEN = 'finto'",
    "ANTHROPIC_API_KEY = ''",
    "LNBITS_URL = 'http://127.0.0.1:1'",
    # I DUE VALORI SONO IL SEGNAPOSTO DEL CONFIG D'ESEMPIO, e non un
    # 'finta' qualunque: lo scanner dei segreti in CI ancora la sua
    # regola al NOME della variabile con un valore non vuoto, e
    # `INCOLLA_QUI` e' l'unica eccezione che ammette. Un valore
    # inventato qui fa diventare rosso il job dei segreti — successo
    # davvero — e la cura giusta non e' allargare la guardia per un
    # file di prova: e' cosi' che le regole muoiono. Qui il valore
    # non conta comunque: LNbits e' simulato.
    "LNBITS_INVOICE_KEY = 'INCOLLA_QUI'",
    "LNBITS_ADMIN_KEY = 'INCOLLA_QUI'",
    "ADMIN_IDS = [999]",
    "MODALITA_COLLAUDO = True",
    "COMMISSIONE_PERCENTO = 0",
    "ORE_CONFERMA = 72",
    "GIORNI_AUTO_SBLOCCO = 10",
    "MODELLO_RICERCA = 'claude-haiku-4-5-20251001'",
    "BANNER_NEGOZIO_ATTIVO = True",
    "BANNER_PREZZO_SATS = 10000",
]
with open(_conf, "w", encoding="utf-8") as f:
    f.write(chr(10).join(_RIGHE) + chr(10))
sys.path.insert(0, _tmp)

import server  # noqa: E402

VERDI = [0]
ROSSE = [0]


def prova(che, atteso, avuto):
    ok = atteso == avuto
    VERDI[0] += ok
    ROSSE[0] += not ok
    print(("  OK   " if ok else "  ROTTO ") + che)
    if not ok:
        print(f"       atteso: {atteso!r}")
        print(f"       avuto:  {avuto!r}")


# --- LNbits di cartone ----------------------------------------------
FATTURE = {}        # payment_hash -> {"sats", "memo", "pagata"}
USCITE = []         # le bolt11 che avremmo pagato


async def _finta_invoice(sats, memo, expiry=900):
    h = f"hash{len(FATTURE) + 1}"
    FATTURE[h] = {"sats": sats, "memo": memo, "pagata": False}
    return {"payment_hash": h, "payment_request": f"lnbc{h}"}


async def _finta_pagata(payment_hash):
    return FATTURE.get(payment_hash, {}).get("pagata", False)


async def _muta(*a, **k):
    return None


server.crea_invoice_escrow = _finta_invoice
server.invoice_pagata = _finta_pagata
server.notifica = _muta
server.notifica_admin = _muta
server.avvisa_banner = _muta
server.bot_api = _muta


def paga(payment_hash):
    FATTURE[payment_hash]["pagata"] = True


class Req:
    """La richiesta di cartone: `salva_banner_negozio` legge il body
    PRIMA di guardare la porta, quindi senza un corpo vero il 400 che
    torna e' «Richiesta malformata» — cioe' il banco boccerebbe per la
    ragione sbagliata."""

    def __init__(self, corpo=None):
        self._c = corpo or {}

    async def json(self):
        return self._c


def db():
    return server.db()


def utente(tg_id, negozio, xp=0, vendite=0):
    con = db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, negozio, xp, "
                "vendite_ok, acquisti_ok) VALUES(?,?,?,?,?,0)",
                (tg_id, f"Tale {tg_id}", negozio, xp, vendite))
    con.commit()
    con.close()


def campo(tg_id, nome):
    con = db()
    r = con.execute(f"SELECT {nome} AS v FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    con.close()
    return (r["v"] if r else None)


def main():
    server.init_db()
    print("\n=== LO SBLOCCO A PAGAMENTO DEL BANNER ===\n")

    # 1 = paga, 2 = ce l'ha col livello, 3 = paghera' e poi si fonde
    utente(1, "aa11")
    utente(2, "bb22", xp=5000, vendite=9)
    utente(3, "cc33")

    def come(n):
        server.verifica_utente = lambda h="", s="": {"id": n}

    print("[la porta, prima]")
    come(1)
    d = asyncio.run(server.mio_profilo("", ""))  # /api/me
    prova("chi e' nudo trova la porta chiusa", False,
          d["banner_leve"]["porta_aperta"])
    prova("...e il prezzo per aprirla arriva dal server", 10000,
          d["banner_leve"]["prezzo_sats"])
    prova("...col motivo gia' scritto", True,
          "si sblocca col livello" in d["banner_leve"]["motivo"])
    come(2)
    d2 = asyncio.run(server.mio_profilo("", ""))
    prova("chi ha il livello ce l'ha aperta, e senza pagare", (True, 0),
          (d2["banner_leve"]["porta_aperta"],
           d2["banner_leve"]["sbloccato_il"]))

    print("\n[chiedere il banner a porta chiusa]")
    come(1)
    try:
        asyncio.run(server.salva_banner_negozio(Req({"link": "https://x.it", "foto": ""}), "", ""))
        esito = "passato"
    except server.HTTPException as e:
        esito = str(e.detail)
    prova("il banner non si chiede: il 400 dice quale chiave manca",
          True, "si sblocca col livello" in esito)

    print("\n[la fattura]")
    r = asyncio.run(server.sblocca_banner(None, "", ""))
    pid = r["pagamento_id"]
    prova("la fattura chiede il prezzo della leva", 10000, r["importo_sats"])
    prova("...e nel registro LNbits si riconosce", True,
          "sblocco banner" in FATTURE[r["payment_hash"]]["memo"])
    prova("la riga nasce 'creato'", "creato",
          db().execute("SELECT stato FROM pagamenti WHERE id=?",
                       (pid,)).fetchone()["stato"])
    prova("...e la porta e' ancora chiusa", 0, campo(1, "banner_sbloccato_il"))

    print("\n[la ripresa: chi ritocca il bottone]")
    r2 = asyncio.run(server.sblocca_banner(None, "", ""))
    prova("si rivede LA SUA fattura", (pid, True),
          (r2["pagamento_id"], bool(r2.get("ripresa"))))
    prova("...e non se ne conia una seconda", 1, len(FATTURE))

    print("\n[il poll, prima del pagamento]")
    d3 = asyncio.run(server.verifica_pagamento_sblocco(pid, "", ""))
    prova("in attesa", "in_attesa", d3["stato"])
    prova("...e nessuno ha aperto niente", 0, campo(1, "banner_sbloccato_il"))

    print("\n[pagata]")
    paga(r["payment_hash"])
    d4 = asyncio.run(server.verifica_pagamento_sblocco(pid, "", ""))
    prova("il pagamento si registra", "pagato", d4["stato"])
    prova("...e la porta si apre nello stesso giro", True,
          (campo(1, "banner_sbloccato_il") or 0) > 0)
    quando = campo(1, "banner_sbloccato_il")
    d5 = asyncio.run(server.verifica_pagamento_sblocco(pid, "", ""))
    prova("il secondo poll non fa niente", "pagato", d5["stato"])
    prova("...e non sposta la data del primo sblocco", quando,
          campo(1, "banner_sbloccato_il"))

    print("\n[e adesso il banner si chiede]")
    d6 = asyncio.run(server.mio_profilo("", ""))
    prova("la porta risulta aperta", True, d6["banner_leve"]["porta_aperta"])
    prova("...e il cassetto non ha piu' un motivo da dire", "",
          d6["banner_leve"]["motivo"])
    try:
        asyncio.run(server.sblocca_banner(None, "", ""))
        due = "passato"
    except server.HTTPException as e:
        due = str(e.detail)
    prova("chi ha pagato non puo' ripagare", True, "già aperta" in due)
    prova("...e la fattura resta una sola", 1, len(FATTURE))

    print("\n[l'orologio: chi paga e sparisce]")
    come(3)
    r3 = asyncio.run(server.sblocca_banner(None, "", ""))
    con = db()
    con.execute("UPDATE pagamenti SET creato=creato-99999 WHERE id=?",
                (r3["pagamento_id"],))
    con.commit()
    con.close()
    paga(r3["payment_hash"])
    asyncio.run(server.controlla_abbandonati())
    prova("l'ultimo sguardo lo riacciuffa", "pagato",
          db().execute("SELECT stato FROM pagamenti WHERE id=?",
                       (r3["pagamento_id"],)).fetchone()["stato"])
    prova("...e gli apre la porta", True,
          (campo(3, "banner_sbloccato_il") or 0) > 0)

    print("\n[l'orologio: chi non paga]")
    utente(4, "dd44")
    come(4)
    r4 = asyncio.run(server.sblocca_banner(None, "", ""))
    con = db()
    con.execute("UPDATE pagamenti SET creato=creato-99999 WHERE id=?",
                (r4["pagamento_id"],))
    con.commit()
    con.close()
    asyncio.run(server.controlla_abbandonati())
    prova("la fattura morta diventa una LAPIDE", "annullato",
          db().execute("SELECT stato FROM pagamenti WHERE id=?",
                       (r4["pagamento_id"],)).fetchone()["stato"])
    prova("...e la porta resta chiusa", 0, campo(4, "banner_sbloccato_il"))
    # LA LAPIDE NON SI CANCELLA MAI: e' il filo verso quel pagamento,
    # ed e' la ragione per cui qui NON esiste una purga.
    prova("la riga resta, che e' il registro contabile", 1,
          db().execute("SELECT COUNT(*) AS n FROM pagamenti WHERE id=?",
                       (r4["pagamento_id"],)).fetchone()["n"])

    print("\n[l'orologio: il pentito che paga lo stesso]")
    # IL CASO VERO: chi annulla col suo bottone e paga lo stesso. La
    # lapide dev'essere FRESCA — `controlla_annullati` guarda i 30
    # minuti, la stessa finestra degli ordini — e quella fabbricata
    # dall'ultimo sguardo su una riga vecchia di ore e' gia' fuori:
    # e' il comportamento degli ordini, ereditato, non un caso nuovo.
    utente(5, "ee77")
    come(5)
    r5 = asyncio.run(server.sblocca_banner(None, "", ""))
    asyncio.run(server.annulla_pagamento_sblocco(r5["pagamento_id"], "", ""))
    prova("annullato: la riga diventa una lapide", "annullato",
          db().execute("SELECT stato FROM pagamenti WHERE id=?",
                       (r5["pagamento_id"],)).fetchone()["stato"])
    paga(r5["payment_hash"])
    asyncio.run(server.controlla_annullati())
    prova("il riacciuffo lo trova", "pagato",
          db().execute("SELECT stato FROM pagamenti WHERE id=?",
                       (r5["pagamento_id"],)).fetchone()["stato"])
    prova("...e gli apre la porta lo stesso", True,
          (campo(5, "banner_sbloccato_il") or 0) > 0)

    print("\n[la ronda del libro mastro]")
    rotti = []
    for nome, perche, sql in server.CONTROLLI_LIBRO_MASTRO:
        con = db()
        try:
            if con.execute(sql).fetchall():
                rotti.append(nome)
        except Exception as e:
            rotti.append(f"{nome} (esplosa: {e})")
        con.close()
    prova("a database sano la ronda TACE", [], rotti)

    print("\n[la porta segue chi fonde i suoi due account]")
    # il nativo Nostr ha pagato (tg_id negativo), poi collega Telegram
    utente(-77, "ee55")
    utente(88, "ff66")
    # la fusione esige che il nativo abbia una chiave d'accesso vera:
    # e' la prima guardia di `_guardie_fusione`
    con = db()
    con.execute("UPDATE utenti SET npub_accesso='npub1finta' WHERE tg_id=-77")
    con.commit()
    con.close()
    come(-77)
    r6 = asyncio.run(server.sblocca_banner(None, "", ""))
    paga(r6["payment_hash"])
    asyncio.run(server.verifica_pagamento_sblocco(r6["pagamento_id"], "", ""))
    prova("il nativo ha la sua porta", True,
          (campo(-77, "banner_sbloccato_il") or 0) > 0)
    # IL BANCO NON DEVE MENTIRE: se la fusione si rifiuta, ritorna la
    # frase gentile invece del riepilogo — e le prove dopo passerebbero
    # o fallirebbero per la ragione sbagliata (la lezione del venditore
    # che aveva gia' il wallet, in collaudo_feedback_confermato).
    esito = server.esegui_fusione(88, -77)
    prova("la fusione avviene davvero", True, isinstance(esito, dict))
    prova("dopo la fusione la porta e' di chi resta", True,
          (campo(88, "banner_sbloccato_il") or 0) > 0)
    prova("...e il pagamento l'ha seguito", 88,
          db().execute("SELECT tg_id FROM pagamenti WHERE id=?",
                       (r6["pagamento_id"],)).fetchone()["tg_id"])
    rotti2 = []
    for nome, perche, sql in server.CONTROLLI_LIBRO_MASTRO:
        con = db()
        if con.execute(sql).fetchall():
            rotti2.append(nome)
        con.close()
    prova("...e la ronda tace anche dopo la fusione", [], rotti2)

    print("\n[la regressione: chi ha il livello]")
    come(2)
    prova("non gli si offre di pagare", 0,
          db().execute("SELECT COUNT(*) AS n FROM pagamenti WHERE tg_id=2",
                       ).fetchone()["n"])
    prova("...e la sua porta non e' mai stata sbloccata a pagamento", 0,
          campo(2, "banner_sbloccato_il"))
    prova("nessun sat e' uscito da nessuna parte", [], USCITE)

    print(f"\n=== {VERDI[0]} verdi, {ROSSE[0]} rotte ===")
    return 1 if ROSSE[0] else 0


if __name__ == "__main__":
    sys.exit(main())
