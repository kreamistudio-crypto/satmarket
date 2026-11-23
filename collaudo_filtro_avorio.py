# -*- coding: utf-8 -*-
"""
L'AVORIO CHE NON E' UNA ZANNA, SUL SERVER VERO (25 ott 2026, cantiere
filtro-animali-falso-positivo, richiesta di Andrea).

Il caso vero: una collezione d'arte sacra in edizione di lusso fermata
due volte dal filtro parole come «animali protetti». `prove.py` gira il
giudice estratto; qui si chiamano le ROTTE vere, su un database
usa-e-getta, e si guarda quel che vede chi vende e quel che resta scritto:
  1. il libro (carta avorio, pagine color avorio) si PUBBLICA, e nel
     registro non resta nessun blocco dello strato 1; e cosi' la collana
     beige e avorio del 19 nov 2026 (i colori in fila, le perline);
  2. la statuetta in avorio resta FERMA: 400, col divieto, la PAROLA che
     l'ha fermata e lo «scrivici» con la chat privata — anche con
     BANNER_TEST_LINK assente dal config, che e' il caso di questo banco;
     il registro dice «animali protetti: avorio», e cosi' l'avviso ai
     moderatori;
  3. la MODIFICA che infila una zanna nel libro pubblicato e' ferma allo
     stesso modo, col numero dell'annuncio nel registro.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, niente rete (l'AI
non si chiama: lo strato 2 e' di cartone e dice «ok»), niente Telegram.

USO:  python collaudo_filtro_avorio.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
AVVISI = []       # i testi che sarebbero andati ai moderatori

VENDE = 222
PORTA = "https://t.me/barattolostore?direct"


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
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa. BANNER_TEST_LINK NON c'e', apposta."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-filtro-avorio-")
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
    # la foto di cartone: senza almeno una foto non si pubblica, e
    # questo collaudo non parla di foto
    # (23 nov 2026, foto-varianti) `indici` dice quale posizione e'
    # entrata: qui entra sempre la prima, l'unica che si salva
    server.salva_foto = lambda aid, foto, versione="", indici=None: (
        indici.append(0) if indici is not None else None,
        ([f"a{aid}_0.jpg"], []))[1]

    async def zitto(*a, **k):
        return None

    async def cambio_finto():
        return 100_000.0

    async def avvisa_finto(testo, *a, **k):
        AVVISI.append(testo)

    server.cambio_btc_eur = cambio_finto
    server.notifica_admin = avvisa_finto
    # lo strato 2 dice «ok»: qui si guarda lo strato 1, e un «ok»
    # dell'AI e' proprio il caso in cui il filtro parole decide da solo
    server.moderazione_ai = zitto
    for nome in ("annuncio_su_nostr", "premia_distintivi",
                 "avvisa_contatto_mancante", "premia_xp", "notifica"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    server.accoda_promo = lambda *a, **k: None
    server.FRENI["annunci"] = (1000, 3600)
    return tmp


async def _rotta(rotta, corpo, args):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    try:
        return await rotta(*args, None,
                           x_tg_init_data=f"collaudo:{VENDE}:Vende")
    except SRV.HTTPException as e:
        return {"errore": e.status_code, "detail": e.detail}


def chiama(rotta, corpo, *args):
    async def giro():
        r = await _rotta(rotta, corpo, args)
        io = asyncio.current_task()
        altri = [x for x in asyncio.all_tasks() if x is not io]
        if altri:
            await asyncio.wait(altri, timeout=10)
        return r
    return asyncio.run(giro())


def corpo(titolo, descrizione):
    return {"titolo": titolo, "prezzo_sats": 30000,
            "categoria": "Libri e riviste", "zona": "Torino (TO)",
            "descrizione": descrizione, "consegna": "ritiro",
            "quantita": 1, "condizione": "buono",
            "foto": ["foto-di-cartone"]}


def registro():
    con = SRV.db()
    righe = [dict(r) for r in con.execute(
        "SELECT annuncio_id, strato, esito, motivo, venditore_id "
        "FROM moderazione_log WHERE strato='parole' ORDER BY id")]
    con.close()
    return righe


def main():
    tmp = avvio()
    prova("il banco non ha BANNER_TEST_LINK, apposta", "",
          SRV.BANNER_TEST_LINK)

    print("\n[1) il libro con la carta avorio si pubblica]")
    libro = chiama(SRV.pubblica, corpo(
        "Collezione d'Arte Religiosa SAIE – Società San Paolo "
        "(1978-1981) Edizioni di lusso",
        "Volumi rilegati, carta avorio, pagine color avorio. "
        "Rilegatura avorio, copertina avorio, tela avorio sul dorso."))
    prova("nasce, con un numero", True, bool(libro.get("id")))
    con = SRV.db()
    stato = con.execute("SELECT stato FROM annunci WHERE id=?",
                        (libro.get("id"),)).fetchone()
    con.close()
    prova("...ed e' in vetrina", "attivo", stato and stato["stato"])
    prova("...e il filtro parole non ha scritto niente", [], registro())
    prova("...ne' avvisato i moderatori di un blocco", 0,
          len([t for t in AVVISI if "bloccat" in t]))

    print("\n[1-bis) la collana beige e avorio si pubblica (19 nov 2026)]")
    collana = chiama(SRV.pubblica, corpo(
        "Collana Beige",
        "Fatta a mano, colori beige e avorio. Perline avorio e "
        "cordino beige, filo avorio."))
    prova("nasce, con un numero", True, bool(collana.get("id")))
    prova("...e il filtro parole non ha scritto niente", [], registro())

    print("\n[2) la statuetta in avorio resta ferma]")
    r = chiama(SRV.pubblica, corpo("Statuetta in avorio",
                                   "Intagliata a mano, fine '800."))
    prova("400", 400, r.get("errore"))
    detto = str(r.get("detail"))
    prova("...dice il divieto", True, "animali protetti" in detto)
    prova("...dice la parola che l'ha fermata", True,
          "A fermarlo è stata la parola «avorio»." in detto)
    prova("...dice che si puo' riscrivere", True, "ripubblica" in detto)
    prova("...e a chi scrivere, senza nessun canale nel config", True,
          detto.endswith("scrivici: " + PORTA))
    prova("il registro dice categoria e parola",
          [{"annuncio_id": 0, "strato": "parole", "esito": "vietato",
            "motivo": "animali protetti: avorio", "venditore_id": VENDE}],
          registro())
    prova("...e cosi' l'avviso ai moderatori", 1,
          len([t for t in AVVISI if "Annuncio bloccato dal filtro" in t
               and "(animali protetti: avorio)" in t]))

    print("\n[3) la modifica che infila una zanna e' ferma uguale]")
    r = chiama(SRV.modifica_annuncio, corpo(
        "Collezione d'Arte Religiosa SAIE",
        "Carta avorio. In regalo una zanna d'avorio."), libro.get("id"))
    prova("400", 400, r.get("errore"))
    prova("...con la parola e la porta", True,
          "«avorio»" in str(r.get("detail"))
          and str(r.get("detail")).endswith("scrivici: " + PORTA))
    ultima = registro()[-1]
    prova("il registro tiene il numero dell'annuncio e la parola",
          (libro.get("id"), "animali protetti: avorio"),
          (ultima["annuncio_id"], ultima["motivo"]))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
