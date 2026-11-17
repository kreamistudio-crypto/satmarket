"""IL GIRO VERO DEI REGALI PER LIVELLO (17 nov 2026, il merch «Un tempo
per te»).

Le sentinelle di `prove.py` (`prove_regali_livello`) dicono che i
giudici ci sono e che la forma e' giusta; qui il SERVER VERO gira su un
database usa-e-getta e si guarda cosa RISPONDE: chi sale di gradino
trova il regalo sbloccato e l'avviso, lo chiede col recapito UNA volta,
l'admin lo vede col recapito e lo segna spedito, la persona lo sa. Piu'
i rami che non devono passare: il gradino non raggiunto, il recapito
corto, la seconda richiesta, la leva spenta, l'account fantasma, e chi
era GIA' di un livello il giorno del deploy (nessuna riga scritta prima).

Il bot e' MUTO e registra: un collaudo non manda messaggi veri. Gli XP
non si toccano mai (il perimetro di «GLI XP»): qui si SCRIVONO utenti
coi loro xp e affari, come nel collaudo del banner.

    python collaudo_regali_livello.py
"""
import asyncio
import os
import sys
import tempfile

os.environ["PYTHONIOENCODING"] = "utf-8"

# --- il config di cartone, PRIMA dell'import del server -------------
# (o si aprirebbe il database di casa: il patto dei collaudi)
_tmp = tempfile.mkdtemp(prefix="collaudo_regali_")
_conf = os.path.join(_tmp, "config.py")
_DB = os.path.join(_tmp, "collaudo.db").replace("\\", "/")
_RIGHE = [
    "DB = r'" + _DB + "'",
    "BOT_TOKEN = 'finto'",
    "ANTHROPIC_API_KEY = ''",
    "LNBITS_URL = 'http://127.0.0.1:1'",
    # I DUE VALORI SONO IL SEGNAPOSTO DEL CONFIG D'ESEMPIO (vedi il
    # collaudo del banner): lo scanner dei segreti in CI ammette solo
    # quello, e qui LNbits non si tocca comunque.
    "LNBITS_INVOICE_KEY = 'INCOLLA_QUI'",
    "LNBITS_ADMIN_KEY = 'INCOLLA_QUI'",
    "ADMIN_IDS = [999]",
    "MODALITA_COLLAUDO = True",
    "COMMISSIONE_PERCENTO = 0",
    "ORE_CONFERMA = 72",
    "GIORNI_AUTO_SBLOCCO = 10",
    "MODELLO_RICERCA = 'claude-haiku-4-5-20251001'",
    # La leva NON si scrive: deve nascere accesa da sola (regola del 14
    # nov 2026), e il giro lo prova leggendola dal server.
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


# --- il bot di cartone: muto, ma con la memoria -----------------------
AVVISI = []          # (tg_id, testo) verso le persone
AVVISI_ADMIN = []    # i testi verso i moderatori


async def _registra(tg_id, testo, *a, **k):
    AVVISI.append((tg_id, testo))
    return ""


async def _registra_admin(testo, *a, **k):
    AVVISI_ADMIN.append(testo)


async def _muta(*a, **k):
    return None


server.notifica = _registra
server.notifica_admin = _registra_admin
server.bot_api = _muta
server._premia_distintivo = _muta      # niente relay, mai, in un collaudo


class Req:
    """La richiesta di cartone: la rotta legge il body con leggi_json."""

    def __init__(self, corpo=None):
        self._c = corpo or {}

    async def json(self):
        return self._c


def db():
    return server.db()


def utente(tg_id, xp=0, vendite=0, acquisti=0):
    con = db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, xp, vendite_ok, "
                "acquisti_ok) VALUES(?,?,?,?,?)",
                (tg_id, f"Tale {tg_id}", xp, vendite, acquisti))
    con.commit()
    con.close()


def righe(tg_id):
    con = db()
    out = [(r["livello"], r["stato"], r["recapito"]) for r in con.execute(
        "SELECT livello, stato, recapito FROM regali_livello WHERE tg_id=? "
        "ORDER BY id", (tg_id,))]
    con.close()
    return out


def come(n):
    server.verifica_utente = lambda h="", s="": {"id": n}


def chiedi(livello, recapito):
    """Torna 'ok' o il codice HTTP del rifiuto."""
    try:
        d = asyncio.run(server.richiedi_regalo_livello(
            livello, Req({"recapito": recapito}), "", ""))
        return "ok" if d.get("ok") else d
    except server.HTTPException as e:
        return e.status_code


def main():
    server.init_db()
    print("\n=== I REGALI PER LIVELLO ===\n")
    prova("la leva nasce ACCESA senza una riga nel config", True,
          server.REGALI_LIVELLO_ATTIVI)

    # 1 = nuovo arrivato, 2 = pratico (5000 xp, 9 vendite), 3 = tanti
    # xp ma zero affari (resta nuovo: le due chiavi), 4 = pratico senza
    # righe scritte (il giorno del deploy), 5 = per la leva spenta
    utente(1)
    utente(2, xp=5000, vendite=9)
    utente(3, xp=5000)
    utente(4, xp=300, vendite=4, acquisti=2)
    utente(5, xp=5000, vendite=9)
    utente(999)

    print("[il gancio: chi sale di gradino sblocca, e lo sa]")
    asyncio.run(server.premia_distintivi(2))
    prova("pratico: borsa e tazza sbloccate, nell'ordine della scala",
          [("avviato", "sbloccato", ""), ("pratico", "sbloccato", "")],
          righe(2))
    regali = [t for i, t in AVVISI if i == 2 and "regalo" in t]
    prova("...e due avvisi, uno per regalo, che dicono dove andare", 2,
          sum("Livello e titolo" in t for t in regali))
    prova("...col nome del regalo e del gradino", True,
          "borsa" in regali[0] and "Bottega avviata" in regali[0]
          and "tazza" in regali[1] and "Mercante pratico" in regali[1])
    n = len(AVVISI)
    asyncio.run(server.premia_distintivi(2))
    prova("al secondo giro niente di nuovo: ne' righe ne' avvisi",
          (2, n), (len(righe(2)), len(AVVISI)))
    asyncio.run(server.premia_distintivi(1))
    asyncio.run(server.premia_distintivi(3))
    prova("il nuovo arrivato non ha regali, e nemmeno chi ha solo xp",
          ([], []), (righe(1), righe(3)))
    con = db()
    prova("un account cancellato (fantasma) non riceve regali", [],
          server.sblocca_regali_livello(con, 2 ** 52 + 5))
    con.close()

    print("\n[/api/me: la scala e lo stato di chi legge]")
    come(2)
    me = asyncio.run(server.mio_profilo("", ""))
    prova("ogni gradino della scala porta il suo regalo (il primo no)",
          ["", "👜", "☕", "👕", "📓"],
          [g["regalo"][:1] for g in me["livelli_scala"]])
    prova("i regali con lo stato: due sbloccati, due da sbloccare",
          [("avviato", "sbloccato"), ("pratico", "sbloccato"),
           ("esperto", "da_sbloccare"), ("maestro", "da_sbloccare")],
          [(r["livello"], r["stato"]) for r in me["regali_livello"]])
    come(1)
    me1 = asyncio.run(server.mio_profilo("", ""))
    prova("il nuovo arrivato li vede tutti da sbloccare", ["da_sbloccare"] * 4,
          [r["stato"] for r in me1["regali_livello"]])

    print("\n[chiedere il regalo]")
    come(2)
    prova("un recapito corto non passa (400)", 400, chiedi("avviato", "Mario"))
    prova("il gradino che non esiste come regalo: 404", 404,
          chiedi("nuovo", "Mario Rossi, via Roma 1, 20100 Milano"))
    prova("un gradino non ancora raggiunto: 403", 403,
          chiedi("maestro", "Mario Rossi, via Roma 1, 20100 Milano"))
    n_admin = len(AVVISI_ADMIN)
    prova("la borsa si chiede, col recapito", "ok",
          chiedi("avviato", "  Mario   Rossi,\nvia Roma 1,  20100 Milano "))
    prova("...la riga passa a richiesto, col recapito ripulito",
          ("richiesto", "Mario Rossi, via Roma 1, 20100 Milano"),
          righe(2)[0][1:])
    prova("...e i moderatori lo sanno: cosa e a chi, MAI il recapito",
          (n_admin + 1, True, False),
          (len(AVVISI_ADMIN), "borsa" in AVVISI_ADMIN[-1]
           and "Tale 2" in AVVISI_ADMIN[-1],
           "via Roma" in AVVISI_ADMIN[-1]))
    prova("la seconda volta no: 409", 409,
          chiedi("avviato", "Mario Rossi, via Roma 1, 20100 Milano"))
    me = asyncio.run(server.mio_profilo("", ""))
    prova("/api/me ora dice richiesto", "richiesto",
          me["regali_livello"][0]["stato"])
    lungo = "x" * 700
    prova("un recapito lunghissimo si accorcia al tetto", "ok",
          chiedi("pratico", lungo))
    prova("...a 500 caratteri", 500, len(righe(2)[1][2]))

    print("\n[chi era gia' di un livello il giorno del deploy]")
    come(4)
    prova("nessuna riga scritta prima", [], righe(4))
    me4 = asyncio.run(server.mio_profilo("", ""))
    prova("...ma /api/me lo vede gia' sbloccato (la lettura non scrive)",
          (["sbloccato", "sbloccato", "da_sbloccare", "da_sbloccare"], []),
          ([r["stato"] for r in me4["regali_livello"]], righe(4)))
    prova("e la richiesta sblocca prima e passa", "ok",
          chiedi("pratico", "Punto Locker Stazione, via Verdi 2, Torino"))
    prova("...scrivendo ENTRAMBE le righe, la borsa resta da chiedere",
          [("avviato", "sbloccato"), ("pratico", "richiesto")],
          [r[:2] for r in righe(4)])

    print("\n[il pannello admin]")
    come(1)
    try:
        server.lista_regali_admin("", "")
        esito = "passato"
    except server.HTTPException as e:
        esito = e.status_code
    prova("la lista e' solo degli admin (403)", 403, esito)
    come(999)
    lista = server.lista_regali_admin("", "")
    prova("tre richieste in coda, dalla piu' vecchia, col recapito",
          [(2, "avviato", "richiesto", "Mario Rossi, via Roma 1, 20100 Milano"),
           (2, "pratico", "richiesto"),
           (4, "pratico", "richiesto")],
          [(lista[0]["tg_id"], lista[0]["livello"], lista[0]["stato"],
            lista[0]["recapito"])]
          + [(r["tg_id"], r["livello"], r["stato"]) for r in lista[1:]])
    prova("...col nome accanto", "Tale 2", lista[0]["nome"])
    rid = lista[0]["id"]
    n = len(AVVISI)
    come(1)
    try:
        asyncio.run(server.regalo_spedito_admin(rid, "", ""))
        esito = "passato"
    except server.HTTPException as e:
        esito = e.status_code
    prova("«spedito» non lo preme chi non e' admin (403)", 403, esito)
    come(999)
    d = asyncio.run(server.regalo_spedito_admin(rid, "", ""))
    prova("l'admin segna spedito", "spedito", d["stato"])
    prova("...e la persona riceve l'avviso del pacco", (n + 1, 2, True),
          (len(AVVISI), AVVISI[-1][0], "partito" in AVVISI[-1][1]
           and "borsa" in AVVISI[-1][1]))
    try:
        asyncio.run(server.regalo_spedito_admin(rid, "", ""))
        esito = "passato"
    except server.HTTPException as e:
        esito = e.status_code
    prova("una seconda volta no: 409", 409, esito)
    try:
        asyncio.run(server.regalo_spedito_admin(99999, "", ""))
        esito = "passato"
    except server.HTTPException as e:
        esito = e.status_code
    prova("un id che non esiste: 404", 404, esito)
    lista = server.lista_regali_admin("", "")
    prova("la lista mette lo spedito in fondo",
          ["richiesto", "richiesto", "spedito"], [r["stato"] for r in lista])
    come(2)
    me = asyncio.run(server.mio_profilo("", ""))
    prova("e /api/me di chi riceve dice spedito", "spedito",
          me["regali_livello"][0]["stato"])

    print("\n[la leva spenta]")
    server.REGALI_LIVELLO_ATTIVI = False
    try:
        asyncio.run(server.premia_distintivi(5))
        prova("nessuno sblocca", [], righe(5))
        come(5)
        me5 = asyncio.run(server.mio_profilo("", ""))
        prova("la scala non promette e la lista e' vuota",
              ([""] * 5, []),
              ([g["regalo"] for g in me5["livelli_scala"]],
               me5["regali_livello"]))
        prova("e chiedere risponde 404", 404,
              chiedi("avviato", "Mario Rossi, via Roma 1, 20100 Milano"))
        come(999)
        prova("le righe gia' scritte restano nel pannello", 3,
              len(server.lista_regali_admin("", "")))
    finally:
        server.REGALI_LIVELLO_ATTIVI = True

    print(f"\n=== {VERDI[0]} verdi, {ROSSE[0]} rotte ===")
    return 1 if ROSSE[0] else 0


if __name__ == "__main__":
    sys.exit(main())
