# -*- coding: utf-8 -*-
"""
BARATTOZON FRA I METODI DEGLI AVVISI (19 nov 2026, cantiere avvisi-bz-lato).

Andrea: «Mi piacerebbe poter avere le notifiche solo per ordini barattozon
di tipo compra btc e non di tipo vendi btc», e la scelta «Barattozon fra i
metodi». `prove.py` fa girare i giudici puri (la traduzione delle righe di
ieri, il lato di un ordine Barattozon); qui risponde la ROTTA VERA
`/api/me/avvisi-nuovi-p2p` su un database usa-e-getta (fastapi c'e' solo
nei collaudi): il telefono di oggi (`v: 2`) salva i due lati e Barattozon
fra i metodi; un telefono di ieri, coi tre tipi, viene tradotto prima di
scrivere; e quel che si scrive si rilegge uguale.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete.

USO:  python collaudo_avvisi_bz_metodo.py
"""

import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
BZ = "Contanti al tabacchino"


def main():
    print("=" * 58)
    print("  BARATTOZON FRA I METODI DEGLI AVVISI")
    print("=" * 58)
    banco.avvio()
    S = banco.SRV
    S.P2P_AVVISI_NUOVI_ORDINI = True
    S._p2p_per = lambda tg: {"attivo": True}
    con = S.db()
    con.execute("INSERT INTO utenti(tg_id, nome, username, registrato, negozio) "
                "VALUES(111, 'Compratore', 'c111', ?, '')", (int(time.time()),))
    con.commit()
    con.close()
    banco.come(111)

    def salva(corpo):
        return banco.chiama(S.scegli_avvisi_nuovi_p2p, None, "", "", corpo=corpo)["avvisi_nuovi_p2p"]

    def scritto():
        con = S.db()
        try:
            r = con.execute("SELECT avvisi_nuovi_tipi, avvisi_nuovi_metodi FROM utenti "
                            "WHERE tg_id=111").fetchone()
            return [r[0], r[1]]
        finally:
            con.close()

    def riletto():
        con = S.db()
        try:
            r = con.execute("SELECT * FROM utenti WHERE tg_id=111").fetchone()
            p = S._pref_avvisi_nuovi_p2p(r)
            return [p["tipi"], p["metodi"]]
        finally:
            con.close()

    print("\n[il telefono di oggi]")
    p = salva({"v": 2, "attivo": True, "tipi": ["vendita"], "soglia": "", "metodi": [BZ]})
    prova("solo «Compra BTC» col solo Barattozon: torna cosi'", [["vendita"], [BZ]],
          [p["tipi"], p["metodi"]])
    prova("...si scrive col segno della forma nuova", ["|vendita|v2|", f"|{BZ}|"], scritto())
    prova("...e si rilegge uguale", [["vendita"], [BZ]], riletto())
    prova("il tipo «barattozon» dal telefono di oggi non esiste piu': almeno un lato",
          400, _errore(lambda: salva({"v": 2, "attivo": True, "tipi": ["barattozon"]})))

    print("\n[il telefono di ieri]")
    p = salva({"attivo": True, "tipi": ["vendita", "barattozon"], "soglia": "", "metodi": []})
    prova("Vendita + Barattozon coi metodi «tutti»: «Compra BTC» coi metodi «tutti»",
          [["vendita"], []], [p["tipi"], p["metodi"]])
    p = salva({"attivo": True, "tipi": ["barattozon"], "soglia": ""})
    prova("solo Barattozon: i due lati col solo metodo Barattozon (i metodi gia' scritti, "
          "che il telefono di ieri non manda, si traducono anche loro)",
          [["vendita", "acquisto"], [BZ]], [p["tipi"], p["metodi"]])
    p = salva({"attivo": True, "tipi": ["vendita", "acquisto"], "soglia": "", "metodi": ["SEPA"]})
    prova("Barattozon spento coi metodi scelti: quei metodi, senza Barattozon",
          [["vendita", "acquisto"], ["SEPA"]], [p["tipi"], p["metodi"]])
    prova("...e si rilegge uguale", [["vendita", "acquisto"], ["SEPA"]], riletto())

    print("\n[la riga di ieri, mai risalvata]")
    con = S.db()
    con.execute("UPDATE utenti SET avvisi_nuovi_tipi='|acquisto|barattozon|', "
                "avvisi_nuovi_metodi='|Revolut|' WHERE tg_id=111")
    con.commit()
    con.close()
    prova("si rilegge tradotta: il lato scritto, e Barattozon davanti ai metodi",
          [["acquisto"], [BZ, "Revolut"]], riletto())

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


def _errore(fn):
    try:
        fn()
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)
    return 200


if __name__ == "__main__":
    sys.exit(main())
