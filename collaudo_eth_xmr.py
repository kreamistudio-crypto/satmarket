# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI ETH E XMR NEL P2P (13 nov 2026, cantiere eth-xmr,
richiesta di AndreAI: «in collaudo aggiungi nel P2P anche Ethereum e
Monero come altre coin»).

`prove.py` (`prove_eth_xmr`) prova i giudici del telefono e i pezzi puri;
qui risponde il SERVER VERO:
  - a lista della prova vuota (la produzione) /api/me dice `p2p_coin`
    falso a chiunque, e /api/cambio non porta `cambio_coin`;
  - sull'istanza di prova chi ha il P2P lo vede, e /api/cambio porta il
    cambio di ETH e XMR dalla cache (0 finche' non c'e', mai inventato);
  - la lettura del cambio prende ETH e XMR da una risposta di CoinGecko,
    non bussa due volte nello stesso minuto, e una risposta storta non
    cancella il cambio di prima;
  - col P2P spento, anche sulla prova, nessuno.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco
(MODALITA_COLLAUDO), i relay del coordinator sono quello morto
(ws://127.0.0.1:9), e CoinGecko e' un cartone. Nessuna rete.

USO:  python collaudo_eth_xmr.py
"""

import asyncio
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


class _Risposta:
    def __init__(self, dati):
        self._dati = dati

    def raise_for_status(self):
        return None

    def json(self):
        return self._dati


class _CoinGeckoDiCartone:
    """httpx.AsyncClient per la sola domanda del cambio: conta le
    chiamate e risponde con quel che il banco gli mette in mano."""
    chiamate = []
    risposta = {}

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, params=None, **k):
        _CoinGeckoDiCartone.chiamate.append((url, dict(params or {})))
        return _Risposta(_CoinGeckoDiCartone.risposta)


class _HttpxFinto:
    AsyncClient = _CoinGeckoDiCartone


def main():
    print("=" * 58)
    print("  ETH E XMR NEL P2P — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    # il P2P acceso, verso il relay morto: niente esce di qui
    S.P2P_ATTIVO = True
    S.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    S.MOSTRO_HEX = "ab" * 32
    S.PROVA_APERTA = True        # le porte della prova aperte: qui si prova il cancello
    httpx_prima = S.httpx
    con = S.db()
    con.execute("INSERT INTO utenti(tg_id, nome, registrato) VALUES(?,?,?)",
                (111, "Compratore", 1_700_000_000))
    con.commit()
    con.close()
    try:
        print("\n[in produzione: la lista della prova e' vuota]")
        S.PROVA_SOLO_IDS = set()
        banco.come(111)
        me = c.get("/api/me").json()
        prova("/api/me dice p2p_coin falso", False, me.get("p2p_coin"))
        cam = c.get("/api/cambio").json()
        prova("/api/cambio non porta il cambio di ETH e XMR", False, "cambio_coin" in cam)

        print("\n[sull'istanza di prova]")
        S.PROVA_SOLO_IDS = {111, 222, 999}
        banco.come(111)
        prova("/api/me dice p2p_coin a chi ha il P2P", True, c.get("/api/me").json().get("p2p_coin"))
        prova("...prima della prima lettura il cambio e' 0, non inventato",
              {"eth": 0.0, "xmr": 0.0}, c.get("/api/cambio").json().get("cambio_coin"))

        S.httpx = _HttpxFinto
        _CoinGeckoDiCartone.risposta = {"ethereum": {"eur": 2834.5}, "monero": {"eur": 301.2}}
        letto = asyncio.run(S._rileggi_cambio_coin())
        prova("la lettura chiede ethereum e monero in euro, e va", (True, {"ids": "ethereum,monero", "vs_currencies": "eur"}),
              (letto, _CoinGeckoDiCartone.chiamate[-1][1]))
        prova("/api/cambio adesso porta i due cambi", {"eth": 2834.5, "xmr": 301.2},
              c.get("/api/cambio").json().get("cambio_coin"))
        n = len(_CoinGeckoDiCartone.chiamate)
        prova("nello stesso minuto non si ribussa", (False, n),
              (asyncio.run(S._rileggi_cambio_coin()), len(_CoinGeckoDiCartone.chiamate)))
        S._cambio_coin_cache["tentato"] = 0
        _CoinGeckoDiCartone.risposta = {"ethereum": {"eur": 0}, "monero": {}}
        prova("una risposta vuota non va, e non cancella il cambio di prima",
              (False, {"eth": 2834.5, "xmr": 301.2}),
              (asyncio.run(S._rileggi_cambio_coin()), c.get("/api/cambio").json().get("cambio_coin")))
        S._cambio_coin_cache["tentato"] = 0
        _CoinGeckoDiCartone.risposta = {"ethereum": {"eur": 2900}}
        asyncio.run(S._rileggi_cambio_coin())
        prova("...una moneta sola aggiorna quella e lascia l'altra",
              {"eth": 2900.0, "xmr": 301.2}, c.get("/api/cambio").json().get("cambio_coin"))
        S._cambio_coin_cache["quando"] -= S.CAMBIO_COIN_VALIDO_S + 1
        prova("...e oltre un quarto d'ora il cambio tace", {"eth": 0.0, "xmr": 0.0},
              c.get("/api/cambio").json().get("cambio_coin"))

        print("\n[sulla prova col P2P spento]")
        S.P2P_ATTIVO = False
        prova("/api/me dice p2p_coin falso", False, c.get("/api/me").json().get("p2p_coin"))
        prova("...e /api/cambio non lo porta", False, "cambio_coin" in c.get("/api/cambio").json())
    finally:
        S.httpx = httpx_prima
        S.PROVA_SOLO_IDS = set()
        S.PROVA_APERTA = False

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
