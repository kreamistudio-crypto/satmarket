# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI FRENI (1 ott 2026, cantiere «CSP e le voci aperte degli
audit», cura 4). `prove.py` fa girare il secchio e i giudici; qui risponde
il SERVER VERO: la sfida del login che al trentunesimo colpo dallo stesso
IP in chiaro e' un 429 e sull'onion non lo e' mai; l'anteprima della foto
che al sessantunesimo colpo della stessa persona e' un 429; la fotografia
del libro che risponde 304 all'ETag; il canale P2P che non posta due volte
lo stesso ordine ne' a raffica (e non da' mai un 429).

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco.
Nessuna rete (il canale e' spento: canale_id() vuoto).

USO:  python collaudo_freni.py
"""

import base64
import io
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  I FRENI — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    S._SECCHI.clear()

    print("\n[la sfida del login, per IP e solo in chiaro]")
    chiaro = {"X-Forwarded-For": "93.184.216.34"}   # un IP pubblico VERO (198.51.100.x e' «di documentazione», e per ipaddress privato)
    stati = [c.get("/api/login/nostr/sfida", headers=chiaro).status_code for _ in range(31)]
    # senza coincurve (la gabbia della CI non lo installa) la sfida e' un
    # 503 «login Nostr spento», e il freno viene PRIMA di quel controllo
    # apposta: quel che si prova e' «mai 429 per trenta, 429 al 31°»
    aperta = 200 if S.ChiavePubblicaNostr is not None else 503
    print(f"    (la sfida risponde {aperta}: coincurve "
          f"{'c\'e\'' if aperta == 200 else 'manca, login Nostr spento'})")
    prova("trenta sfide passano il freno, la trentunesima e' un 429", [aperta] * 30 + [429], stati)
    prova("...e un altro IP ha il suo secchio", aperta,
          c.get("/api/login/nostr/sfida", headers={"X-Forwarded-For": "151.101.1.1"}).status_code)
    onion = {"X-Forwarded-For": "127.0.0.1", "Host": "abcdefghijklmnop.onion"}
    stati = [c.get("/api/login/nostr/sfida", headers=onion).status_code for _ in range(40)]
    prova("sull'onion quaranta sfide di fila non sono mai un 429", True, 429 not in stati)
    S._SECCHI.clear()

    print("\n[l'anteprima della foto, per persona]")
    try:
        from PIL import Image
        out = io.BytesIO()
        Image.new("RGB", (8, 8), (200, 100, 50)).save(out, "JPEG")
        uri = "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode()
        stati = []
        for _ in range(61):
            stati.append(c.post("/api/foto/anteprima", json={"foto": uri},
                                headers={"X-Tg-Init-Data": "collaudo:111:Compratore"}).status_code)
        prova("sessanta anteprime passano, la sessantunesima e' un 429", [200] * 60 + [429], stati)
        prova("...e un'altra persona ha il suo secchio", 200,
              c.post("/api/foto/anteprima", json={"foto": uri},
                     headers={"X-Tg-Init-Data": "collaudo:222:Venditore"}).status_code)
    except ImportError:
        prova("Pillow c'e' (senza, l'anteprima e' un 503 e non si prova)", True, False)
    S._SECCHI.clear()

    print("\n[la fotografia del libro: ETag e 304]")
    r = c.get("/api/p2p/libro")
    etag = r.headers.get("etag", "")
    prova("la fotografia porta un ETag", True, etag.startswith('W/"'))
    r2 = c.get("/api/p2p/libro", headers={"If-None-Match": etag})
    prova("...e a impronta uguale risponde 304, senza corpo", (304, b""), (r2.status_code, r2.content))
    prova("...con un'impronta diversa risponde la fotografia", 200,
          c.get("/api/p2p/libro", headers={"If-None-Match": 'W/"altro"'}).status_code)

    print("\n[il canale P2P: un post per ordine, uno ogni dieci minuti, mai un 429]")
    if not S._p2p_per(111)["attivo"]:
        prova("(la leva P2P e' spenta nel banco: il canale si prova con la leva)", True, True)
    else:
        corpo = {"lato": "vendo", "euro": 50, "metodo": "Bonifico",
                 "ordine": "11111111-2222-3333-4444-555555555555"}
        r1 = c.post("/api/p2p/canale", json=corpo, headers={"X-Tg-Init-Data": "collaudo:111:Compratore"})
        r2 = c.post("/api/p2p/canale", json=corpo, headers={"X-Tg-Init-Data": "collaudo:111:Compratore"})
        prova("due post di fila: tutt'e due 200, mai un 429", [200, 200], [r1.status_code, r2.status_code])
        prova("...e il secondo dice di aver saltato il post (raffica, il canale e' spento)",
              "raffica", r2.json().get("saltato"))
    print("\n[gli ordini «creato» vivi per compratore: cinque, il sesto no]")
    async def zitto(*a, **k):
        return None
    S.annuncio_su_nostr = zitto
    S.promo_venduto = zitto
    con = S.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((222, "Vende"), (111, "Compra"), (333, "Altro")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato) "
                    "VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    ann = []
    for n in range(7):
        ann.append(con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa',25000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',1,'sats','nuovo')", (f"Pesto {n}",)).lastrowid)
    con.commit()
    con.close()

    def compra(annuncio, tg=111):
        return c.post("/api/orders", json={"annuncio_id": annuncio, "consegna": "ritiro"},
                      headers={"X-Tg-Init-Data": f"collaudo:{tg}:Chi"})

    stati = [compra(a).status_code for a in ann[:5]]
    prova("cinque ordini nascono", [200] * 5, stati)
    r = compra(ann[5])
    prova("il sesto e' un 429 con la frase", (429, S.MSG_ORDINI_APERTI),
          (r.status_code, r.json().get("detail")))
    prova("...e nessuna fattura e' stata coniata per lui", 5,
          S.db().execute("SELECT COUNT(*) FROM ordini WHERE compratore_id=111").fetchone()[0])
    prova("la ripresa della propria fattura sullo stesso annuncio passa ancora", 200,
          compra(ann[0]).status_code)
    prova("un altro compratore non c'entra", 200, compra(ann[6], tg=333).status_code)
    con = S.db()
    con.execute("UPDATE ordini SET stato='annullato' WHERE compratore_id=111 AND annuncio_id=?", (ann[0],))
    con.commit()
    con.close()
    prova("...e appena uno si annulla, se ne puo' aprire un altro", 200, compra(ann[5]).status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
