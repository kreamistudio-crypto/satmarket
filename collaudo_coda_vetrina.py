# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CODA DEL CANALE (ott 2026, decisione di Andrea).

«Un articolo a settimana per persona, ma se pubblica altri articoli
entrano in una coda schedulata per la settimana dopo, in automatico.»
Qui gira il drenatore VERO e l'orologio VERO della coda, con Telegram di
cartone (si contano i post) e il tempo spostato a mano nel database:

  1. ritmo «settimana»: il venditore pubblica tre annunci → UN post
     subito (il piu' recente, come sempre), gli altri due in coda;
  2. il battito dell'orologio a turno preso non richiama nessuno;
  3. passata la settimana: torna in fila il PIU' VECCHIO, esce il suo
     post, e il terzo aspetta la settimana dopo;
  4. un annuncio pubblicato a turno preso entra in coda e non esce;
  5. il venduto esce dalla coda per sempre, il negozio in ferie aspetta;
  6. due venditori non si rubano il turno;
  7. a ritmo «tutto» la coda si svuota al primo battito;
  8. il giudice puro `_chi_esce_dalla_coda` sui casi di bordo.

NON TOCCA NIENTE DI VERO: config finto prima dell'import di server,
database usa-e-getta, bot_api sostituito.

USO:  python collaudo_coda_vetrina.py
"""

import asyncio
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
POST = []           # (canale, testo) di ogni post uscito


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
        raise SystemExit("⚠️  server e' gia' importato")
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
    cfg.DB = os.path.join(tempfile.mkdtemp(prefix="barattolo-coda-"),
                          "usa-e-getta.db")
    cfg.POST_AUTOMATICI = True
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    server.ATTESA_RAGGRUPPO = 0
    server.PAUSA_TRA_PROMO = 0
    server._NOSTR = None

    async def bot_finto(metodo, dati, *a, **k):
        if metodo in ("sendPhoto", "sendMessage"):
            POST.append((dati.get("chat_id"),
                         dati.get("caption") or dati.get("text") or ""))
            return {"ok": True, "result": {"message_id": len(POST)}}
        return {"ok": True, "result": {}}

    async def cambio_finto():
        return 100_000.0

    server.bot_api = bot_finto
    server.cambio_btc_eur = cambio_finto
    server.imposta_canale("@canale_di_cartone")
    server.imposta_ritmo("settimana")


def sql(q, par=()):
    con = SRV.db()
    r = con.execute(q, par).fetchall()
    con.commit()
    con.close()
    return r


def venditore(tg, nome):
    sql("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato) "
        "VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))


def annuncio(tg, titolo, creato):
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(?,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',?,"
        "'spedizione',1,'sats','nuovo')", (tg, titolo, creato))
    con.commit()
    con.close()
    return cur.lastrowid


async def _pubblica(ids):
    for i in ids:
        SRV.accoda_promo(i)
    await _finisci()


async def _finisci():
    # il drenatore e' un task: si aspetta che abbia finito
    for _ in range(200):
        await asyncio.sleep(0.01)
        if not SRV._drenatore_promo_avviato and not SRV.CODA_PROMO:
            attesa = [t for t in asyncio.all_tasks()
                      if t is not asyncio.current_task()]
            if not attesa:
                return
            await asyncio.gather(*attesa, return_exceptions=True)
            return


def pubblica(*ids):
    asyncio.run(_pubblica(list(ids)))


async def _battito():
    await SRV.richiama_coda_vetrina()
    await _finisci()


def battito():
    asyncio.run(_battito())


def in_coda():
    return [r[0] for r in sql("SELECT annuncio_id FROM coda_vetrina "
                              "ORDER BY annuncio_id")]


TITOLI = ("Lampada", "Sedia", "Tavolo", "Vaso", "Quadro", "Bici", "Radio",
          "Libro")


def titoli_usciti(da=0):
    """Di chi parla ogni post: il titolo che compare PER PRIMO — sotto,
    il post elenca anche gli altri annunci del venditore."""
    def primo(testo):
        presenti = [(testo.find(t), t) for t in TITOLI if t in testo]
        return min(presenti)[1] if presenti else "?"
    return [primo(testo) for _, testo in POST[da:]]


def indietro_di(tg, giorni):
    """Il turno del venditore e' stato preso `giorni` fa."""
    sql("UPDATE utenti SET promo_canale_il=? WHERE tg_id=?",
        (int(time.time()) - giorni * 86400, tg))


def main():
    print("=" * 60)
    print("  LA CODA DEL CANALE")
    print("=" * 60)
    avvio()
    venditore(222, "Vende")
    venditore(333, "Altro")
    t0 = int(time.time()) - 100

    # ---- 1. tre annunci in una settimana --------------------------------
    print("\n[1. ritmo «settimana», tre annunci insieme]")
    lamp = annuncio(222, "Lampada", t0)
    sedia = annuncio(222, "Sedia", t0 + 1)
    tav = annuncio(222, "Tavolo", t0 + 2)
    pubblica(lamp, sedia, tav)
    prova("un post solo, subito", 1, len(POST))
    prova("...il piu' recente, come sempre", ["Tavolo"], titoli_usciti())
    prova("gli altri due in coda, non persi", sorted([lamp, sedia]), in_coda())

    # ---- 2. turno preso -------------------------------------------------
    print("\n[2. il battito a turno preso]")
    battito()
    prova("nessun post nuovo", 1, len(POST))
    prova("la coda resta com'era", sorted([lamp, sedia]), in_coda())

    # ---- 3. passata la settimana ---------------------------------------
    print("\n[3. passata la settimana]")
    indietro_di(222, 8)
    battito()
    prova("esce UN post", 2, len(POST))
    prova("...ed e' il piu' vecchio della coda", ["Lampada"], titoli_usciti(1))
    prova("il terzo aspetta la settimana dopo", [sedia], in_coda())
    battito()
    prova("un secondo battito non ne fa uscire un altro", 2, len(POST))
    indietro_di(222, 8)
    battito()
    prova("la settimana dopo esce anche lui", ["Sedia"], titoli_usciti(2))
    prova("e la coda e' vuota", [], in_coda())

    # ---- 4. pubblicato a turno preso ------------------------------------
    print("\n[4. un annuncio nuovo a turno preso]")
    vaso = annuncio(222, "Vaso", t0 + 10)
    pubblica(vaso)
    prova("non esce", 3, len(POST))
    prova("entra in coda", [vaso], in_coda())

    # ---- 5. venduto e ferie --------------------------------------------
    print("\n[5. il venduto se ne va, le ferie aspettano]")
    sql("UPDATE annunci SET stato='venduto' WHERE id=?", (vaso,))
    quadro = annuncio(222, "Quadro", t0 + 11)
    pubblica(quadro)
    prova("(il quadro e' in coda col vaso)", sorted([vaso, quadro]), in_coda())
    indietro_di(222, 8)
    sql("UPDATE utenti SET ferie_fino=? WHERE tg_id=222",
        (int(time.time()) + 86400,))
    battito()
    prova("in ferie non esce niente", 3, len(POST))
    prova("...il venduto e' uscito dalla coda, il quadro aspetta",
          [quadro], in_coda())
    sql("UPDATE utenti SET ferie_fino=0 WHERE tg_id=222")
    battito()
    prova("tornato dalle ferie, il quadro esce", ["Quadro"], titoli_usciti(3))
    prova("coda vuota", [], in_coda())

    # ---- 6. due venditori ----------------------------------------------
    print("\n[6. due venditori non si rubano il turno]")
    bici = annuncio(333, "Bici", t0 + 20)
    radio = annuncio(333, "Radio", t0 + 21)
    libro = annuncio(222, "Libro", t0 + 22)
    da = len(POST)
    pubblica(bici, radio, libro)
    prova("esce la radio di 333, il libro di 222 va in coda",
          ["Radio"], titoli_usciti(da))
    prova("in coda la bici e il libro", sorted([bici, libro]), in_coda())
    indietro_di(333, 8)
    battito()
    prova("col turno di 333 libero esce solo la bici", ["Radio", "Bici"],
          titoli_usciti(da))
    prova("il libro di 222 aspetta il SUO turno", [libro], in_coda())

    # ---- 7. ritmo «tutto» ----------------------------------------------
    print("\n[7. a ritmo «tutto» la coda si svuota]")
    SRV.imposta_ritmo("tutto")
    battito()
    prova("il libro esce", "Libro", titoli_usciti()[-1])
    prova("coda vuota", [], in_coda())
    SRV.imposta_ritmo("settimana")

    # ---- 8. il giudice puro --------------------------------------------
    print("\n[8. _chi_esce_dalla_coda]")
    ad = 10_000_000
    r = lambda i, v, **k: dict({"annuncio_id": i, "venditore_id": v,
                                "stato": "attivo", "creato": i,
                                "promo_canale_il": 0, "ferie_fino": 0,
                                "origine": ""}, **k)
    giudice = SRV._chi_esce_dalla_coda
    prova("annuncio sparito, venduto, rimosso, importato: via",
          ([], [1, 2, 3, 4]),
          giudice([r(1, 1, stato=None), r(2, 1, stato="venduto"),
                   r(3, 1, stato="rimosso"), r(4, 1, origine="nostr")], 7, ad))
    prova("in revisione aspetta, non va via", ([], []),
          giudice([r(5, 1, stato="revisione")], 7, ad))
    prova("uno per venditore, il piu' vecchio per creato",
          ([7, 9], []), giudice([r(8, 1), r(7, 1), r(9, 2)], 7, ad))
    prova("a pari creato vince l'id piu' basso", ([3], []),
          giudice([r(4, 1, creato=1), r(3, 1, creato=1)], 7, ad))
    prova("turno preso sei giorni fa: aspetta", ([], []),
          giudice([r(1, 1, promo_canale_il=ad - 6 * 86400)], 7, ad))
    prova("turno preso otto giorni fa: esce", ([1], []),
          giudice([r(1, 1, promo_canale_il=ad - 8 * 86400)], 7, ad))
    prova("a freno spento escono tutti", ([1, 2, 3], []),
          giudice([r(1, 1), r(2, 1), r(3, 1, promo_canale_il=ad)], 0, ad))

    print(f"\n{'=' * 60}\n  {PASSATE} passate, {FALLITE} fallite\n{'=' * 60}")
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
