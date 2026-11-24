"""IL GIRO VERO DELLE PROMOZIONI A PAGAMENTO (23 nov 2026).

Le sentinelle di `prove.py` dicono che i pezzi ci sono; qui il SERVER
VERO gira su un database usa-e-getta e si guarda cosa RISPONDE e cosa
resta SCRITTO dopo — su una cassa che incassa sats e' la domanda che
conta.

Il giro, per le tre promozioni («⬆️ In cima», «⭐ In evidenza», «🏪 il
negozio in Da scoprire»): il listino, le guardie prima della fattura,
la fattura, la ripresa, il poll, l'incasso che applica, la busta della
home che lo mostra, i posti pieni, l'orologio che riacciuffa chi paga a
telefono chiuso, il rimborso del moderatore che disfa, il libro mastro
che non suona per chi ricompra, e `/promossi`.

LNBITS E' SIMULATO, sempre: un collaudo non conia fatture vere (la
lezione del 12 ago 2026). Telegram pure: nessun post esce davvero.

    python collaudo_promozioni.py
"""
import asyncio
import os
import sys
import tempfile
import time

os.environ["PYTHONIOENCODING"] = "utf-8"

# --- il config di cartone, PRIMA dell'import del server -------------
_tmp = tempfile.mkdtemp(prefix="collaudo_promozioni_")
_conf = os.path.join(_tmp, "config.py")
_DB = os.path.join(_tmp, "collaudo.db").replace("\\", "/")
_RIGHE = [
    "DB = r'" + _DB + "'",
    "BOT_TOKEN = 'finto'",
    "ANTHROPIC_API_KEY = ''",
    "LNBITS_URL = 'http://127.0.0.1:1'",
    # il segnaposto del config d'esempio: vedi collaudo_sblocco_banner
    "LNBITS_INVOICE_KEY = 'INCOLLA_QUI'",
    "LNBITS_ADMIN_KEY = 'INCOLLA_QUI'",
    "ADMIN_IDS = [999]",
    "MODALITA_COLLAUDO = True",
    "COMMISSIONE_PERCENTO = 0",
    "ORE_CONFERMA = 72",
    "GIORNI_AUTO_SBLOCCO = 10",
    "MODELLO_RICERCA = 'claude-haiku-4-5-20251001'",
    "MOSTRO_RELAY = 'ws://127.0.0.1:9'",
    "MOSTRO_RELAY_SPECCHIO = 'ws://127.0.0.1:9'",
    # due posti soli, per vedere la fila piena senza otto annunci
    "PROMO_EVIDENZA_POSTI = 2",
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


# --- LNbits e Telegram di cartone -----------------------------------
FATTURE = {}        # payment_hash -> {"sats", "memo", "pagata"}
USCITE = []         # le bolt11 che avremmo pagato
POST = []           # i post che sarebbero usciti nel canale
TOLTI = []          # i post vecchi cancellati
AVVISI = []         # (tg, testo) agli utenti
BOTTONI = []        # (tg, bottone) degli stessi avvisi
ADMIN = []          # (testo, argomento) ai moderatori
ESITO = ["pagato"]


async def _finta_invoice(sats, memo, expiry=900, cassaforte=""):
    h = f"hash{len(FATTURE) + 1}"
    FATTURE[h] = {"sats": sats, "memo": memo, "pagata": False}
    return {"payment_hash": h, "payment_request": f"lnbc{h}"}


async def _finta_pagata(payment_hash, _cassaforte=""):
    return FATTURE.get(payment_hash, {}).get("pagata", False)


async def _muta(*a, **k):
    return None


async def _avviso(tg, testo, *a, **k):
    AVVISI.append((tg, testo))
    BOTTONI.append((tg, a[0] if a else k.get("bottone")))


async def _admin(testo, *a, **k):
    ADMIN.append((testo, k.get("argomento", "")))


async def _finta_uscita(bolt11, atteso_sats, diario=None, *, cassaforte,
                        riga=()):
    USCITE.append((bolt11, atteso_sats))
    if diario is not None:
        diario["hash"] = "hash-di-cartone"
        diario["tentato"] = True
    return ESITO[0]


async def _finto_address(indirizzo, sats):
    return f"lnbc-da-{indirizzo}-{sats}"


async def _finto_post(dove, caption, foto):
    POST.append((dove, caption))
    return 7000 + len(POST)


async def _finto_bot(metodo, dati=None, *a, **k):
    if metodo == "deleteMessage":
        TOLTI.append((dati or {}).get("message_id"))
    if metodo == "sendMessage":
        AVVISI.append(((dati or {}).get("chat_id"), (dati or {}).get("text")))
    return {"ok": True}


async def _cambio():
    return 60_000.0


server.paga_venditore = _finta_uscita
server.invoice_da_ln_address = _finto_address
server.crea_invoice_escrow = _finta_invoice
server.invoice_pagata = _finta_pagata
server.notifica = _avviso
server.notifica_admin = _admin
server.bot_api = _finto_bot
server._manda_post_canale = _finto_post
server.cambio_btc_eur = _cambio
server.canale_id = lambda: "-100123"
server.POST_AUTOMATICI = True
server.ESITO_PAGATO = server.PAGATO
ESITO[0] = server.PAGATO


def paga(payment_hash):
    FATTURE[payment_hash]["pagata"] = True


class Req:
    def __init__(self, corpo=None):
        self._c = corpo or {}

    async def json(self):
        return self._c


def db():
    return server.db()


def uno(sql, par=()):
    con = db()
    r = con.execute(sql, par).fetchone()
    con.close()
    return r


def scrivi(sql, par=()):
    con = db()
    con.execute(sql, par)
    con.commit()
    con.close()


def utente(tg_id, negozio):
    scrivi("INSERT OR REPLACE INTO utenti(tg_id, nome, negozio, xp, "
           "vendite_ok, acquisti_ok, registrato) VALUES(?,?,?,0,0,0,1)",
           (tg_id, f"Bottega {tg_id}", negozio))


def annuncio(tg, titolo, creato):
    con = db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(?,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',?,"
        "'spedizione',1,'sats','nuovo')", (tg, titolo, creato))
    con.commit()
    con.close()
    return cur.lastrowid


def come(n):
    server.verifica_utente = lambda h="", s="": {"id": n}
    server.utente_se_autenticato = lambda h="", s="": {"id": n}


def compra(corpo):
    try:
        return asyncio.run(server.compra_promo(Req(corpo), "", "")), ""
    except server.HTTPException as e:
        return None, (e.status_code, str(e.detail))


def verifica(pid):
    async def _giro():
        r = await server.verifica_pagamento_sblocco(pid, "", "")
        # il post del canale parte in un task: gli si lascia il tempo
        await asyncio.sleep(0.05)
        return r
    return asyncio.run(_giro())


def busta():
    come(0)
    server.utente_se_autenticato = lambda h="", s="": None
    return asyncio.run(server.lista_annunci(limit=24))


def main():
    server.init_db()
    print("\n=== LE PROMOZIONI A PAGAMENTO ===\n")
    adesso = int(time.time())

    utente(1, "aa11")          # vende, promuove
    utente(2, "bb22")          # un altro venditore
    utente(3, "cc33")          # il negozio col banner
    utente(4, "dd44")          # il terzo dell'evidenza
    vecchio = annuncio(1, "Lampada vecchia", adesso - 5 * 86400)
    recente = annuncio(2, "Sedia recente", adesso - 3600)
    di_altro = annuncio(2, "Tavolo di altri", adesso - 7200)
    terzo = annuncio(4, "Quadro", adesso - 9000)
    scrivi("UPDATE annunci SET post_canale_id=555 WHERE id=?", (vecchio,))

    # ---------------------------------------------------------------
    print("[il listino]")
    come(1)
    li = asyncio.run(server.listino_promo(vecchio, "", ""))
    prova("le promozioni sono accese di serie", True, li["attive"])
    prova("In cima costa la leva, e si puo' subito (vecchio di 5 giorni)",
          (5000, 0), (li["cima"]["sats"], li["cima"]["da"]))
    prova("In evidenza: le due durate coi loro prezzi",
          [{"giorni": 7, "sats": 15000}, {"giorni": 15, "sats": 25000}],
          li["evidenza"]["durate"])
    prova("...coi posti dalla leva, liberi", (2, 0, 0),
          (li["evidenza"]["posti"], li["evidenza"]["occupati"],
           li["evidenza"]["libero_da"]))
    try:
        asyncio.run(server.listino_promo(di_altro, "", ""))
        esito = "passato"
    except server.HTTPException as e:
        esito = str(e.detail)
    prova("il listino di un annuncio altrui non si legge",
          "Annuncio non trovato", esito)
    ln = asyncio.run(server.listino_promo(0, "", ""))
    prova("senza annuncio: la voce del negozio, 50.000 per 30 giorni",
          (50000, 30, False), (ln["scoprire"]["sats"],
                               ln["scoprire"]["giorni"],
                               ln["scoprire"]["banner"]))

    # ---------------------------------------------------------------
    print("\n[le guardie prima della fattura]")
    r, no = compra({"tipo": "cima", "annuncio_id": di_altro})
    prova("l'annuncio di un altro non si promuove", (400, "Annuncio non "
          "trovato"), no)
    r, no = compra({"tipo": "evidenza:3", "annuncio_id": vecchio})
    prova("una durata che non e' in listino non si compra", 400, no[0])
    r, no = compra({"tipo": "boh", "annuncio_id": vecchio})
    prova("un tipo inventato non si compra", 400, no[0])
    come(2)
    r, no = compra({"tipo": "cima", "annuncio_id": recente})
    prova("un annuncio di un'ora fa e' gia' fra i primi: In cima no",
          True, bool(no) and "già fra i primi" in no[1])
    come(3)
    r, no = compra({"tipo": "scoprire"})
    prova("il negozio senza banner approvato non si mette in Da scoprire",
          True, bool(no) and "banner" in no[1])
    server.PROMOZIONI_ATTIVE = False
    come(1)
    r, no = compra({"tipo": "cima", "annuncio_id": vecchio})
    prova("a leva spenta la cassa e' chiusa", (400, server.MSG_PROMO_SPENTE),
          no)
    server.PROMOZIONI_ATTIVE = True
    prova("...e in tutte queste nessuna fattura e' stata coniata", 0,
          len(FATTURE))

    # ---------------------------------------------------------------
    print("\n[In cima: fattura, ripresa, poll, incasso]")
    r, no = compra({"tipo": "cima", "annuncio_id": vecchio})
    pid = r["pagamento_id"]
    prova("la fattura chiede 5.000 sats", 5000,
          FATTURE[r["payment_hash"]]["sats"])
    prova("...e nel registro LNbits si riconosce", True,
          "promozione" in FATTURE[r["payment_hash"]]["memo"])
    r2, _ = compra({"tipo": "cima", "annuncio_id": vecchio})
    prova("chi ritocca il bottone rivede LA SUA fattura", (pid, True),
          (r2["pagamento_id"], bool(r2.get("ripresa"))))
    prova("in attesa finche' non paga", "in_attesa", verifica(pid)["stato"])
    prova("...e l'annuncio non si e' mosso", adesso - 5 * 86400,
          uno("SELECT creato FROM annunci WHERE id=?", (vecchio,))["creato"])
    paga(r["payment_hash"])
    d = verifica(pid)
    prova("pagata: il pagamento si registra e si applica",
          ("pagato", True), (d["stato"], d.get("applicata")))
    prova("l'annuncio ha la data di adesso", True,
          uno("SELECT creato FROM annunci WHERE id=?",
              (vecchio,))["creato"] >= adesso)
    b = busta()
    prova("...ed e' il primo dei Più recenti", vecchio, b["annunci"][0]["id"])
    prova("il post vecchio nel canale si toglie", [555], TOLTI)
    prova("...e ne esce uno nuovo, nel NOSTRO canale", ["-100123"],
          [p[0] for p in POST])
    prova("...e la colonna tiene l'id del nuovo", 7001,
          uno("SELECT post_canale_id FROM annunci WHERE id=?",
              (vecchio,))["post_canale_id"])
    prova("chi ha pagato riceve il «Fatto!»", True,
          any(tg == 1 and "tornato in cima" in t for tg, t in AVVISI))
    come(1)
    r3, no = compra({"tipo": "cima", "annuncio_id": vecchio})
    prova("subito dopo, In cima non si ricompra (una volta ogni 24 ore)",
          True, bool(no) and "già fra i primi" in no[1])

    # ---------------------------------------------------------------
    print("\n[In evidenza: la fila e i posti]")
    come(2)
    r, no = compra({"tipo": "evidenza:7", "annuncio_id": di_altro})
    prova("7 giorni chiedono 15.000 sats", 15000,
          FATTURE[r["payment_hash"]]["sats"])
    # CHI CAMBIA IDEA: 15 giorni invece di 7 chiude la fattura vecchia
    rb, _ = compra({"tipo": "evidenza:15", "annuncio_id": di_altro})
    prova("chi cambia durata ha una fattura nuova da 25.000", 25000,
          FATTURE[rb["payment_hash"]]["sats"])
    prova("...e la vecchia diventa una lapide", "annullato",
          uno("SELECT stato FROM pagamenti WHERE id=?",
              (r["pagamento_id"],))["stato"])
    paga(rb["payment_hash"])
    d = verifica(rb["pagamento_id"])
    fino = uno("SELECT evidenza_fino FROM annunci WHERE id=?",
               (di_altro,))["evidenza_fino"]
    prova("pagata: in evidenza per 15 giorni", True,
          abs(fino - (adesso + 15 * 86400)) < 60)
    prova("...e il primo giorno anche in cima", True,
          uno("SELECT creato FROM annunci WHERE id=?",
              (di_altro,))["creato"] >= adesso)
    b = busta()
    prova("la busta della home porta la fila In evidenza", [di_altro],
          [a["id"] for a in b.get("in_evidenza", [])])
    prova("...e la card sa fino a quando", fino,
          b["in_evidenza"][0].get("evidenza_fino"))
    come(1)
    r, _ = compra({"tipo": "evidenza:7", "annuncio_id": vecchio})
    paga(r["payment_hash"])
    verifica(r["pagamento_id"])
    come(4)
    r, no = compra({"tipo": "evidenza:7", "annuncio_id": terzo})
    prova("con i due posti presi, il terzo non conia fattura", 409,
          no[0] if no else None)
    prova("...e gli si dice da quando si libera un posto", True,
          "si libera il" in (no[1] if no else ""))
    li4 = asyncio.run(server.listino_promo(terzo, "", ""))
    prova("il listino dice i posti pieni e la data", (2, True),
          (li4["evidenza"]["occupati"], li4["evidenza"]["libero_da"] > 0))
    # CHI ALLUNGA LA SUA non conta come un posto in piu'
    come(2)
    r, no = compra({"tipo": "evidenza:7", "annuncio_id": di_altro})
    prova("chi e' gia' in fila puo' allungare anche a posti pieni", "",
          no)
    paga(r["payment_hash"])
    verifica(r["pagamento_id"])
    fino2 = uno("SELECT evidenza_fino FROM annunci WHERE id=?",
                (di_altro,))["evidenza_fino"]
    prova("...e i giorni si SOMMANO alla scadenza, non ad adesso",
          fino + 7 * 86400, fino2)

    # ---------------------------------------------------------------
    print("\n[il negozio in Da scoprire]")
    scrivi("UPDATE utenti SET banner_stato='attivo', banner_foto="
           "'ban_cc33.jpg', avatar='av_cc33.jpg' WHERE tg_id=3")
    come(3)
    # LA PAGINA DEDICATA (23 nov 2026) si chiede in Assistenza: accesa qui
    server.ASSISTENZA_ATTIVA = True
    AVVISI.clear(); BOTTONI.clear(); ADMIN.clear()
    r, no = compra({"tipo": "scoprire"})
    prova("col banner approvato la fattura chiede 50.000", 50000,
          FATTURE[r["payment_hash"]]["sats"])
    # PAGA E CHIUDE L'APP: l'orologio lo riacciuffa
    scrivi("UPDATE pagamenti SET creato=creato-99999 WHERE id=?",
           (r["pagamento_id"],))
    paga(r["payment_hash"])
    asyncio.run(server.controlla_abbandonati())
    prova("chi paga a telefono chiuso viene incassato dall'orologio",
          "pagato", uno("SELECT stato FROM pagamenti WHERE id=?",
                        (r["pagamento_id"],))["stato"])
    u = uno("SELECT promo_scoprire_fino, promo_consigliato FROM utenti "
            "WHERE tg_id=3")
    prova("...e il negozio e' in Da scoprire per 30 giorni, poi Consigliato",
          (True, 1), (abs(u["promo_scoprire_fino"] - (adesso + 30 * 86400))
                      < 120, u["promo_consigliato"]))
    a = uno("SELECT autore, admin, testo FROM assistenza WHERE utente=3")
    prova("alla prima entrata il negozio trova in Assistenza la richiesta "
          "di foto e testo, scritta da Barattolo (autore 0)",
          (0, 1, server.PROMO_PAGINA_ASSISTENZA),
          tuple(a) if a else None)
    prova("...il «Fatto!» del bot gliela indica, col tasto dell'assistenza",
          (True, ("💬 Apri l'assistenza", f"{server.URL_PUBBLICO}/?assistenza=mia")),
          (any(tg == 3 and "Per la pagina dedicata del tuo negozio" in t
               for tg, t in AVVISI),
           next((b for tg, b in BOTTONI if tg == 3 and b), None)))
    prova("...e ai moderatori arriva «Da preparare la pagina di…»",
          [("🏪 Da preparare la pagina di <b>Bottega 3</b>: gli abbiamo "
            "chiesto foto e testo in Assistenza.", "moderazione")],
          [x for x in ADMIN if "Da preparare" in x[0]])
    # CHI E' GIA' CONSIGLIATO (rinnovo, o pagina gia' fatta) non riceve
    # di nuovo la richiesta: il negozio 4, gia' fra i Consigliati
    scrivi("UPDATE utenti SET banner_stato='attivo', banner_foto="
           "'ban_dd44.jpg', promo_consigliato=1 WHERE tg_id=4")
    come(4)
    AVVISI.clear(); BOTTONI.clear(); ADMIN.clear()
    r4, _ = compra({"tipo": "scoprire"})
    paga(r4["payment_hash"])
    verifica(r4["pagamento_id"])
    prova("chi e' gia' fra i Consigliati non riceve di nuovo la richiesta",
          (0, False, [None], []),
          (uno("SELECT COUNT(*) FROM assistenza WHERE utente=4")[0],
           any("pagina dedicata" in t for _, t in AVVISI),
           [b for tg, b in BOTTONI if tg == 4],
           [x for x in ADMIN if "Da preparare" in x[0]]))
    # via le tracce del negozio 4: il resto del giro guarda il 3
    scrivi("UPDATE utenti SET banner_stato='', promo_consigliato=0, "
           "promo_scoprire_fino=0 WHERE tg_id=4")
    scrivi("UPDATE pagamenti SET stato='annullato' WHERE id=?",
           (r4["pagamento_id"],))
    server.ASSISTENZA_ATTIVA = False
    come(3)
    b = busta()
    prova("la busta porta il negozio: codice, banner, logo, mai il tg_id",
          [{"negozio": "cc33", "nome": "Bottega 3", "banner": "ban_cc33.jpg",
            "logo": "av_cc33.jpg", "scoprire": True, "consigliato": True}],
          b.get("negozi_promossi"))
    # DOPO I 30 GIORNI resta fra i Consigliati
    scrivi("UPDATE utenti SET promo_scoprire_fino=? WHERE tg_id=3",
           (adesso - 10,))
    b = busta()
    prova("scaduti i 30 giorni, esce da Da scoprire ma resta Consigliato",
          [(False, True)], [(n["scoprire"], n["consigliato"])
                            for n in b.get("negozi_promossi", [])])
    # IL BANNER SPENTO DAL MODERATORE spegne anche la card
    scrivi("UPDATE utenti SET banner_stato='sospeso' WHERE tg_id=3")
    prova("un banner spento toglie il negozio dalla busta", [],
          busta().get("negozi_promossi"))
    scrivi("UPDATE utenti SET banner_stato='attivo' WHERE tg_id=3")

    # ---------------------------------------------------------------
    print("\n[il libro mastro]")
    con = db()
    rotti = {}
    for nome, _perche, sql in server.CONTROLLI_LIBRO_MASTRO:
        try:
            if con.execute(sql).fetchall():
                rotti[nome] = True
        except Exception:
            pass
    con.close()
    prova("chi ricompra In evidenza non suona come «pagato due volte»",
          False, "sblocco pagato due volte" in rotti)
    prova("i motivi delle promozioni hanno la loro cassa", False,
          "pagamento con un motivo che nessuno sa incassare" in rotti)

    # ---------------------------------------------------------------
    print("\n[il rimborso del moderatore disfa]")
    pid_ev = uno("SELECT id FROM pagamenti WHERE motivo='promo_evidenza' "
                 "AND stato='pagato' AND tg_id=1")["id"]
    scrivi("UPDATE utenti SET ln_address='chi@wallet.it' WHERE tg_id IN (1,3)")
    esito = asyncio.run(server._rimborsa_sblocco(pid_ev, 999))
    prova("il rimborso di In evidenza riesce", True, esito["ok"])
    prova("...paga ESATTAMENTE quel che ha incassato", 15000, USCITE[-1][1])
    prova("...e l'annuncio esce dalla fila", 0,
          uno("SELECT evidenza_fino FROM annunci WHERE id=?",
              (vecchio,))["evidenza_fino"])
    pid_sc = uno("SELECT id FROM pagamenti WHERE motivo='promo_scoprire' "
                 "AND stato='pagato'")["id"]
    esito = asyncio.run(server._rimborsa_sblocco(pid_sc, 999))
    prova("il rimborso del negozio toglie Da scoprire E Consigliati",
          (True, 0, 0), (esito["ok"],) + tuple(uno(
              "SELECT promo_scoprire_fino, promo_consigliato FROM utenti "
              "WHERE tg_id=3")))

    # ---------------------------------------------------------------
    print("\n[/promossi, il moderatore]")
    scrivi("UPDATE utenti SET promo_consigliato=1 WHERE tg_id=3")
    AVVISI.clear()
    asyncio.run(server.comando_promossi({"id": 999}, "/promossi"))
    testo = AVVISI[-1][1] if AVVISI else ""
    prova("l'elenco mostra il negozio e l'annuncio in evidenza", True,
          "cc33" in testo and f"#{di_altro}" in testo)
    asyncio.run(server.comando_promossi({"id": 999},
                                        "/promossi negozio cc33"))
    prova("«/promossi negozio cc33» lo toglie dai Consigliati", 0,
          uno("SELECT promo_consigliato FROM utenti WHERE tg_id=3")[0])
    asyncio.run(server.comando_promossi({"id": 999},
                                        f"/promossi annuncio {di_altro}"))
    prova("«/promossi annuncio ID» lo toglie da In evidenza", 0,
          uno("SELECT evidenza_fino FROM annunci WHERE id=?",
              (di_altro,))["evidenza_fino"])
    scrivi("UPDATE annunci SET evidenza_fino=? WHERE id=?",
           (adesso + 86400, di_altro))
    asyncio.run(server.comando_promossi({"id": 1},
                                        f"/promossi annuncio {di_altro}"))
    prova("chi non e' admin non toglie niente", True,
          uno("SELECT evidenza_fino FROM annunci WHERE id=?",
              (di_altro,))["evidenza_fino"] > 0)

    # L'EVIDENZA REGALATA (24 nov 2026): la stessa della pagata, senza
    # fattura, dal link che il moderatore ha in mano
    print("\n[/promossi evidenza, il regalo del moderatore]")
    regalo = annuncio(3, "Crema spalmabile", adesso - 3 * 86400)
    POST.clear(); ADMIN.clear()
    pagamenti = uno("SELECT COUNT(*) FROM pagamenti")[0]

    async def _regala(chi, testo):
        await server.comando_promossi({"id": chi}, testo)
        await asyncio.sleep(0.05)      # il post del canale e' un task
    asyncio.run(_regala(999, "/promossi evidenza https://barattolo.store/"
                        f"annuncio/{regalo}-crema-spalmabile 7"))
    a = uno("SELECT evidenza_fino, creato FROM annunci WHERE id=?", (regalo,))
    prova("dal link: in evidenza 7 giorni e oggi in cima, senza fattura",
          (True, True, pagamenti),
          (abs(a["evidenza_fino"] - (adesso + 7 * 86400)) < 120,
           a["creato"] >= adesso, uno("SELECT COUNT(*) FROM pagamenti")[0]))
    prova("...esce di nuovo nel canale, e i moderatori lo sanno", (1, True),
          (len(POST), any(f"/promossi evidenza {regalo} 7" in x[0]
                          for x in ADMIN)))
    prova("...e la busta lo porta nella fila", True,
          regalo in [x["id"] for x in busta().get("in_evidenza", [])])
    asyncio.run(_regala(999, f"/promossi evidenza {regalo} 3"))
    prova("ridato a chi ce l'ha, i giorni si sommano", True,
          abs(uno("SELECT evidenza_fino FROM annunci WHERE id=?",
                  (regalo,))[0] - (adesso + 10 * 86400)) < 120)
    asyncio.run(_regala(999, f"/promossi evidenza {regalo}"))
    prova("senza giorni sono 7", True,
          abs(uno("SELECT evidenza_fino FROM annunci WHERE id=?",
                  (regalo,))[0] - (adesso + 17 * 86400)) < 120)
    server.PROMO_EVIDENZA_POSTI = 2
    AVVISI.clear()
    asyncio.run(_regala(999, f"/promossi evidenza {vecchio} 7"))
    prova("a fila piena non scavalca: dice quando si libera il posto",
          (0, True), (uno("SELECT evidenza_fino FROM annunci WHERE id=?",
                          (vecchio,))[0],
                      "sono tutti presi" in (AVVISI[-1][1] if AVVISI else "")))
    server.PROMO_EVIDENZA_POSTI = 8
    for testo in (f"/promossi evidenza {vecchio} 0",
                  f"/promossi evidenza {vecchio} 91"):
        asyncio.run(_regala(999, testo))
    asyncio.run(_regala(1, f"/promossi evidenza {vecchio} 7"))
    scrivi("UPDATE annunci SET stato='venduto' WHERE id=?", (regalo,))
    asyncio.run(_regala(999, f"/promossi evidenza {regalo} 7"))
    prova("giorni fuori misura, chi non e' admin, un annuncio venduto: "
          "niente", (0, True),
          (uno("SELECT evidenza_fino FROM annunci WHERE id=?", (vecchio,))[0],
           abs(uno("SELECT evidenza_fino FROM annunci WHERE id=?",
                   (regalo,))[0] - (adesso + 17 * 86400)) < 120))

    print(f"\n=== {VERDI[0]} verdi, {ROSSE[0]} rotte ===")
    return 1 if ROSSE[0] else 0


if __name__ == "__main__":
    sys.exit(main())
