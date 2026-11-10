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
    print("\n[il canale P2P: la convenienza nel post, e Subito Crypto solo da Telegram]")
    # (10 nov 2026, richiesta di Andrea) due canali finti, la fabbrica dei
    # post che ANNOTA invece di spedire, e tre persone: Telegram con
    # @username, Telegram senza, e un nativo Nostr (tg_id < 0)
    mandati = []

    async def annota(dove, caption, foto):
        mandati.append((dove, caption))
        return 1
    prima = (S._manda_post_canale, S.canale_id, S.canale_vetrina,
             S.verifica_utente, S._p2p_per, S._foto_subito_p2p,
             S.canale_bitcoin_podcast)
    # (10 nov 2026, poi) BitcoinPodcast, la terza porta: entra TUTTO
    S.canale_bitcoin_podcast = lambda: "@podcast"
    S._manda_post_canale = annota
    S.canale_id = lambda: "@casa"
    S.canale_vetrina = lambda: "@subito_crypto_vetrina"
    S._p2p_per = lambda tg: {"attivo": True}
    S._foto_subito_p2p = lambda *a: None
    con = S.db()
    for tg, nome, username in ((4401, "Tele", "tele"), (4402, "Muto", ""),
                               (-4403, "Nostrano", "")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,registrato) "
                    "VALUES(?,?,?,?,1)", (tg, nome, username, f"neg{abs(tg)}"))
    con.commit()
    con.close()

    def posta(tg, corpo):
        mandati.clear()
        S._SECCHI.clear()
        S._CANALE_POSTATI.clear()
        S.verifica_utente = lambda *a, **k: {"id": tg}
        r = c.post("/api/p2p/canale", json=corpo)
        return r.status_code, r.json().get("postato"), [d for d, _ in mandati], \
            (mandati[0][1] if mandati else "")
    try:
        st, ok, dove, cap = posta(4401, {"lato": "vendo", "euro": 50,
                                         "metodo": "Revolut", "premio": 3})
        prova("Telegram con @username: il post esce in casa, su Subito Crypto e su BitcoinPodcast, uguale",
              (200, True, ["@casa", "@subito_crypto_vetrina", "@podcast"]), (st, ok, dove))
        prova("...con la convenienza dal lato di chi guarda (vende a +3: 3% meno conveniente)",
              True, "🏷️ 3% meno conveniente" in cap
              and mandati[0][1] == mandati[1][1] == mandati[2][1])
        st, ok, dove, cap = posta(4401, {"lato": "compro", "euro": 50,
                                         "metodo": "Revolut", "premio": 4})
        prova("...e chi compra a +4 e' 4% più conveniente per chi legge", True,
              "🏷️ 4% più conveniente" in cap)
        st, ok, dove, cap = posta(4401, {"lato": "vendo", "euro": 50,
                                         "metodo": "SEPA", "premio": -150})
        prova("...a sats fissi la convenienza passa il 20 (−150: 150% più conveniente)", True,
              "🏷️ 150% più conveniente" in cap)
        st, ok, dove, cap = posta(4401, {"lato": "vendo", "euro": 50,
                                         "metodo": "SEPA", "premio": 0})
        prova("...a zero «al prezzo di mercato»", True, "🏷️ al prezzo di mercato" in cap)
        esiti = []
        for storto in ("3", 2.5, True, 5000, None):
            corpo = {"lato": "vendo", "euro": 50, "metodo": "SEPA"}
            if storto is not None:
                corpo["premio"] = storto
            st, ok, dove, cap = posta(4401, corpo)
            esiti.append((st, "🏷️" in cap))
        prova("...una convenienza storta o assente non e' un 400: il post esce senza la riga",
              [(200, False)] * 5, esiti)
        st, ok, dove, cap = posta(4401, {"lato": "vendo", "euro": 50,
                                         "metodo": "Contanti al tabacchino", "premio": 25})
        prova("...mentre il Barattozon tiene il suo 400 fuori scala", 400, st)
        st, ok, dove, cap = posta(4402, {"lato": "vendo", "euro": 50, "metodo": "SEPA"})
        prova("Telegram senza @username: in casa e su BitcoinPodcast, non su Subito Crypto",
              (200, True, ["@casa", "@podcast"]), (st, ok, dove))
        st, ok, dove, cap = posta(-4403, {"lato": "vendo", "euro": 50, "metodo": "SEPA"})
        prova("chi entra da Nostr: in casa e su BitcoinPodcast, mai su Subito Crypto",
              (200, True, ["@casa", "@podcast"]), (st, ok, dove))
        S.canale_bitcoin_podcast = lambda: ""
        S.canale_id = lambda: ""
        st, ok, dove, cap = posta(4401, {"lato": "vendo", "euro": 50, "metodo": "SEPA"})
        prova("a canale di casa spento Subito Crypto va lo stesso, per conto suo",
              (200, True, ["@subito_crypto_vetrina"]), (st, ok, dove))
        S.canale_id = lambda: "@casa"
        S.canale_vetrina = lambda: ""
        st, ok, dove, cap = posta(4401, {"lato": "vendo", "euro": 50, "metodo": "SEPA"})
        prova("...e a Subito Crypto spento resta solo casa", ["@casa"], dove)
    finally:
        (S._manda_post_canale, S.canale_id, S.canale_vetrina,
         S.verifica_utente, S._p2p_per, S._foto_subito_p2p,
         S.canale_bitcoin_podcast) = prima
        S._SECCHI.clear()
        S._CANALE_POSTATI.clear()

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
