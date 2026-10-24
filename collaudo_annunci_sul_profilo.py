# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «PUBBLICA I MIEI ANNUNCI ANCHE SUL MIO PROFILO NOSTR»
(20 ott 2026, cantiere nostr-da-telefono, decisione di Andrea).

Dal campo: un utente con Primal vende su Barattolo e non vuole che gli
annunci compaiano sul suo account Nostr. Il BIVIO di agosto li metteva
sempre li' (li firmava lui, dalla coda delle firme). Ora e' una scelta:

  · di serie SI': il bivio di sempre, l'annuncio si accoda per la SUA
    firma e nasce sul suo profilo;
  · con NO: quel che e' gia' sul suo profilo si accoda per la
    cancellazione NIP-09 — UN kind 5 solo per tutti, una firma — e
    firmata quella torna in piazza col nome di Barattolo; quel che
    aspettava di nascere a nome suo nasce col nostro, subito;
  · l'evento col nome di Barattolo non porta NIENTE che arrivi alla sua
    npub: ne' tag p, e, a, ne' la npub o la chiave, ne' il nome, lo
    username o un link al profilo (la prova chiesta da Andrea);
  · finche' la sua cancellazione non e' firmata non nasce un nostro
    evento accanto al suo (due teste);
  · tornando a SI' le cancellazioni non firmate sugli annunci vivi si
    buttano, e il trasloco riporta a nome suo quel che e' nostro.

QUI GIRA IL SERVER VERO col banco di `collaudo_lnbits_muto` (config
finto, database usa-e-getta, MODALITA_COLLAUDO), con una chiave di
piattaforma usa-e-getta e i relay di cartone: `_spedisci_ai_relay`
tiene gli eventi invece di spedirli. Le firme dell'utente sono VERE
(`schnorr_puro`, la ricetta BIP-340 del repo), come le farebbe il suo
firmatario. Il server le verifica col suo giudice vero: coincurve dove
c'e', e in CI, dove non c'e', `schnorr_puro.ChiaveXOnly` montato al
posto di `ChiavePubblicaNostr` — solo dopo aver visto che il server,
da solo, non ci crede (24 ott 2026, cantiere collaudi-senza-coincurve,
come `collaudo_fusione_da_telegram`). La chiave della piattaforma e'
quella di coincurve dove c'e', se no un calco che firma con schnorr_puro.

NESSUNA RETE.

USO:  python collaudo_annunci_sul_profilo.py
"""

import asyncio
import hashlib
import json
import os
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova
LUI = 4242
SPEDITI = []          # gli eventi che sarebbero andati ai relay


def nuova_chiave() -> bytes:
    """Una chiave usa-e-getta, 32 byte nella misura del BIP-340."""
    while True:
        sk = os.urandom(32)
        if 1 <= int.from_bytes(sk, "big") < schnorr_puro.N:
            return sk


class ChiaveDiCalco:
    """La chiave della piattaforma dove coincurve non c'e': quel che il
    server le chiede, `secret` e `sign_schnorr`, fatto con schnorr_puro
    (lo stesso calco di `collaudo_avviso_dm_nostr`)."""

    def __init__(self, sk: bytes):
        self.secret = sk

    def sign_schnorr(self, msg: bytes) -> bytes:
        return schnorr_puro.firma(self.secret, msg, os.urandom(32))


def firma_sua(sk, ev):
    """Firma l'evento preparato dal server con la chiave dell'utente,
    come farebbe il suo firmatario (NIP-01: id ricalcolato, Schnorr)."""
    pub = schnorr_puro.pubblica(sk).hex()
    serial = json.dumps([0, pub, ev["created_at"], ev["kind"], ev["tags"],
                         ev["content"]], separators=(",", ":"),
                        ensure_ascii=False)
    ev_id = hashlib.sha256(serial.encode("utf-8")).hexdigest()
    return pub, ev_id, schnorr_puro.firma(sk, bytes.fromhex(ev_id),
                                          os.urandom(32)).hex()


def annuncio(S, titolo, stato="attivo"):
    con = S.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id, titolo, descrizione, categoria, "
        "prezzo_sats, zona, stato, creato) VALUES(?,?,?,?,?,?,?,?)",
        (LUI, titolo, f"{titolo}, come nuovo", "Casa e giardino", 21000,
         "Torino", stato, int(time.time())))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def riga(S, aid):
    con = S.db()
    r = con.execute("SELECT nostr_event_id, nostr_autore FROM annunci "
                    "WHERE id=?", (aid,)).fetchone()
    con.close()
    return (r["nostr_event_id"], r["nostr_autore"])


def coda(S):
    con = S.db()
    r = [tuple(x) for x in con.execute(
        "SELECT annuncio_id, azione FROM firme_nostr WHERE tg_id=? "
        "ORDER BY annuncio_id", (LUI,)).fetchall()]
    con.close()
    return r


async def scenario():
    S = banco.SRV
    sk_noi = nuova_chiave()
    if S.ChiavePrivataNostr is not None:
        piattaforma = S.ChiavePrivataNostr(sk_noi)
    else:
        piattaforma = ChiaveDiCalco(sk_noi)
    S._NOSTR = (piattaforma, schnorr_puro.pubblica(sk_noi).hex())
    nostra = S._NOSTR[1]

    print("\n[le firme: il patto del server, e il calco dove coincurve non c'e']")
    if S.ChiavePubblicaNostr is None:
        sk0 = nuova_chiave()
        ev0 = S.evento_non_firmato(schnorr_puro.pubblica(sk0).hex(), 1, [],
                                   "prova", int(time.time()))
        ev0["sig"] = schnorr_puro.firma(sk0, bytes.fromhex(ev0["id"]),
                                        os.urandom(32)).hex()
        prova("senza coincurve il server non crede a nessuna firma, nemmeno "
              "a una giusta", False, S.verifica_firma_nostr(ev0))
        S.ChiavePubblicaNostr = schnorr_puro.ChiaveXOnly
        print("   (coincurve assente: monto schnorr_puro.ChiaveXOnly, come in CI)")
    else:
        print("   (coincurve presente: il server verifica con libsecp256k1)")

    async def spedisci_finto(evento, relays=None):
        SPEDITI.append(evento)
        return 1
    S._spedisci_ai_relay = spedisci_finto

    sk = nuova_chiave()
    sua = schnorr_puro.pubblica(sk).hex()
    npub = S.hex_to_npub(sua)
    con = S.db()
    con.execute("INSERT INTO utenti(tg_id, nome, username, npub, "
                "npub_verificata, npub_accesso, registrato) "
                "VALUES(?,?,?,?,?,?,?)",
                (LUI, "Mario Lunghi", "mariolunghi", npub, 1, npub,
                 int(time.time())))
    con.commit()
    con.close()
    banco.come(LUI)

    async def json_di(corpo):
        async def leggi(_req):
            return corpo
        S.leggi_json = leggi

    async def firma_la_coda():
        """Il giro del browser: GET della coda, firma, POST di ognuna."""
        d = await S.firme_nostr_da_fare("", "")
        for voce in d["firme"]:
            pub, ev_id, sig = firma_sua(sk, voce["evento"])
            await json_di({"biglietto": voce["biglietto"], "pubkey": pub,
                           "sig": sig})
            await S.firma_nostr_fatta(None, "", "")
        await asyncio.sleep(0.2)      # i ganci in sottofondo finiscono
        return d

    print("\n[di serie SI': il bivio di sempre]")
    prova("la colonna nasce a 1 per chi c'e' gia'", True,
          S.annunci_sul_suo_profilo(S.db(), LUI))
    a1, a2 = annuncio(S, "Lampada"), annuncio(S, "Sedia")
    await S.annuncio_su_nostr(a1, "active")
    await S.annuncio_su_nostr(a2, "active")
    prova("i due annunci si accodano per la SUA firma, nessuno parte col "
          "nostro nome", ([(a1, "pubblica"), (a2, "pubblica")], 0),
          (coda(S), len(SPEDITI)))
    d = await firma_la_coda()
    SUO = d["firme"][0]["evento"] if d["firme"] else {}
    prova("firmati da lui: sono suoi in piazza", (sua, sua),
          (riga(S, a1)[1], riga(S, a2)[1]))
    prova("...e la coda e' vuota", [], coda(S))

    print("\n[con NO: una cancellazione sola, poi il nome di Barattolo]")
    a3 = annuncio(S, "Bicicletta")
    await S.annuncio_su_nostr(a3, "active")
    prova("un terzo annuncio aspetta di nascere a nome suo", [(a3, "pubblica")],
          coda(S))
    await json_di({"si": False})
    r = await S.scegli_annunci_sul_profilo(None, "", "")
    await asyncio.sleep(0.2)
    prova("la scelta si salva e dice quanti sono da cancellare",
          (False, False, 2), (S.annunci_sul_suo_profilo(S.db(), LUI),
                               r["si"], r["da_ritirare"]))
    prova("i suoi due eventi si accodano per la cancellazione, la "
          "pubblicazione a nome suo esce dalla coda",
          [(a1, "ritira"), (a2, "ritira")], coda(S))
    nati = [e for e in SPEDITI if e["kind"] == 30402]
    prova("quello che aspettava di nascere nasce SUBITO col nostro nome",
          (1, nostra, f"barattolo-{a3}"),
          (len(nati), nati[0]["pubkey"] if nati else None,
           next((t[1] for t in nati[0]["tags"] if t[0] == "d"), None)
           if nati else None))
    await S.annuncio_su_nostr(a1, "sold")
    prova("finche' la sua cancellazione aspetta, un aggiornamento non fa "
          "nascere un NOSTRO evento accanto al suo (due teste)",
          (1, sua), (len([e for e in SPEDITI if e["kind"] == 30402]),
                     riga(S, a1)[1]))
    d = await S.firme_nostr_da_fare("", "")
    cinque = [v for v in d["firme"] if v["evento"]["kind"] == 5]
    prova("la coda chiede UNA firma sola, un kind 5 con tutti e due",
          (1, 1, 2), (len(d["firme"]), len(cinque),
                      cinque[0].get("quanti") if cinque else None))
    tags = cinque[0]["evento"]["tags"] if cinque else []
    prova("...con un `e` e un `a` per annuncio, e il `k`",
          (sorted([riga(S, a1)[0], riga(S, a2)[0]]),
           sorted([f"30402:{sua}:barattolo-{a1}", f"30402:{sua}:barattolo-{a2}"]),
           [["k", "30402"]]),
          (sorted(t[1] for t in tags if t[0] == "e"),
           sorted(t[1] for t in tags if t[0] == "a"),
           [t for t in tags if t[0] == "k"]))
    SPEDITI.clear()
    await firma_la_coda()
    prova("firmata la cancellazione, i suoi eventi non sono piu' suoi",
          (True, True),
          (riga(S, a1)[1] == "", riga(S, a2)[1] == ""))
    nati = [e for e in SPEDITI if e["kind"] == 30402]
    prova("...e tornano in piazza col nome di Barattolo, tutti e due",
          ({nostra}, sorted([f"barattolo-{a1}", f"barattolo-{a2}"])),
          ({e["pubkey"] for e in nati},
           sorted(next(t[1] for t in e["tags"] if t[0] == "d") for e in nati)))
    prova("...con lo stato della riga di adesso (attivi)", True,
          all(["status", "active"] in e["tags"] for e in nati))
    prova("...e la riga tiene il nostro evento", (True, True),
          (riga(S, a1)[0] != "" and riga(S, a1)[1] == "",
           riga(S, a2)[0] != "" and riga(S, a2)[1] == ""))

    print("\n[la prova di Andrea: niente che porti alla sua npub]")
    prova("CONTROLLO DEL SETACCIO: sull'evento firmato da lui la sua chiave "
          "si vede (se qui non si vedesse, le righe sotto non proverebbero "
          "niente)", True, sua in json.dumps(SUO).lower())
    for e in nati:
        testo = json.dumps(e, ensure_ascii=False).lower()
        prova(f"#{next(t[1] for t in e['tags'] if t[0] == 'd')}: nessun tag "
              "p, e, a", [], [t for t in e["tags"] if t[0] in ("p", "e", "a")])
        prova("...ne' la npub ne' la chiave, il nome, lo username, un nip05 "
              "o un link al profilo", [],
              [x for x in (npub, sua, "mario lunghi", "mariolunghi", "nip05",
                           "/u/", "/negozio/", "/venditore/", "nostr:npub",
                           "nprofile") if x in testo])
        prova("...e la firma e' la nostra", nostra, e["pubkey"])

    print("\n[di nuovo SI': il trasloco riporta a nome suo]")
    a4 = annuncio(S, "Tavolo")
    await S.annuncio_su_nostr(a4, "active")
    con = S.db()
    # una cancellazione NATA DAL «NO» e non ancora firmata: in coda e
    # nell'elenco del «no», come la scrive scegli_annunci_sul_profilo
    con.execute("INSERT INTO firme_nostr(annuncio_id, tg_id, azione, creato) "
                "VALUES(?,?,?,?)", (a4, LUI, "ritira", int(time.time())))
    con.execute("INSERT INTO ritiri_per_scelta(annuncio_id, creato) "
                "VALUES(?,?)", (a4, int(time.time())))
    con.commit()
    con.close()
    await json_di({"si": True})
    r = await S.scegli_annunci_sul_profilo(None, "", "")
    prova("una cancellazione del «no» non firmata si butta, e "
          "i nostri quattro eventi si accodano per la sua firma",
          (True, [(a1, "pubblica"), (a2, "pubblica"), (a3, "pubblica"),
                  (a4, "pubblica")]),
          (r["si"], coda(S)))

    print("\n[il doppione ritirato col «si'» non rinasce dopo un «no»]")
    # IL CASO RARO (23 ott 2026, cantiere firme-giuste, decisione di
    # Andrea): col «si'» il venditore ritira a mano un doppione — e' suo,
    # quindi la cancellazione aspetta la sua firma. Poi sceglie «no». La
    # cancellazione del doppione non e' del «no»: firmata, il doppione
    # deve restare FUORI dalla piazza, non tornarci col nome di Barattolo.
    await firma_la_coda()
    prova("firmati: i quattro sono di nuovo suoi in piazza",
          [sua] * 4, [riga(S, a)[1] for a in (a1, a2, a3, a4)])
    await S.ritira_da_nostr(a4)            # la strada vera del doppione
    prova("il doppione si accoda per la SUA cancellazione",
          [(a4, "ritira")], coda(S))
    d = await S.firme_nostr_da_fare("", "")
    prova("la coda conta le cancellazioni a parte: zero annunci da "
          "pubblicare, una cancellazione", (0, 1),
          (d.get("totale"), d.get("ritiri")))
    await json_di({"si": False})
    r = await S.scegli_annunci_sul_profilo(None, "", "")
    con = S.db()
    segnati = sorted(x[0] for x in con.execute(
        "SELECT annuncio_id FROM ritiri_per_scelta").fetchall())
    con.close()
    prova("il «no» accoda le altre tre e le segna come sue; il doppione "
          "resta da cancellare ma NON e' del «no»",
          (4, sorted([a1, a2, a3]), [(a, "ritira") for a in (a1, a2, a3, a4)]),
          (r["da_ritirare"], segnati, coda(S)))
    await json_di({"si": True})
    await S.scegli_annunci_sul_profilo(None, "", "")
    prova("un «si'» prima di firmare butta solo le cancellazioni del «no»: "
          "quella del doppione resta", [(a4, "ritira")], coda(S))
    await json_di({"si": False})
    await S.scegli_annunci_sul_profilo(None, "", "")
    d = await S.firme_nostr_da_fare("", "")
    prova("di nuovo «no»: una firma sola per le quattro cancellazioni, e "
          "nessun annuncio da pubblicare", (0, 4, 1),
          (d.get("totale"), d.get("ritiri"), len(d["firme"])))
    SPEDITI.clear()
    await firma_la_coda()
    nati = sorted(next(t[1] for t in e["tags"] if t[0] == "d")
                  for e in SPEDITI if e["kind"] == 30402)
    prova("firmata: le tre del «no» tornano col nome di Barattolo, il "
          "doppione NO", sorted(f"barattolo-{a}" for a in (a1, a2, a3)), nati)
    prova("...il doppione resta fuori dalla piazza", ("", ""), riga(S, a4))
    con = S.db()
    resti = con.execute("SELECT COUNT(*) FROM ritiri_per_scelta").fetchone()[0]
    con.close()
    prova("...e l'elenco del «no» si e' consumato", 0, resti)

    print("\n[il promemoria settimanale dice il vero]")
    # LA STESSA CORREZIONE DELLA RIGA DEL PROFILO (23 ott 2026, cantiere
    # promemoria-firme, decisione di Andrea): sollecita_firme_nostr VERO,
    # con le notifiche di cartone del banco. Prima diceva a tutti «per
    # finire su Nostr a nome TUO», contando anche le cancellazioni.
    S.SOLLECITO_FIRME_GIORNI = 1
    vecchio = int(time.time()) - 3 * 86400
    con = S.db()
    con.execute("UPDATE utenti SET suggerimenti_annunci=1, "
                "sollecito_firme_il=0, solleciti_firme=0 WHERE tg_id=?",
                (LUI,))
    con.execute("UPDATE annunci SET nostr_event_id=?, nostr_autore=? "
                "WHERE id IN (?,?)", ("ee" * 32, sua, a1, a2))
    con.execute("DELETE FROM firme_nostr")
    con.executemany("INSERT INTO firme_nostr(annuncio_id, tg_id, azione, "
                    "creato) VALUES(?,?,?,?)",
                    [(a1, LUI, "ritira", vecchio), (a2, LUI, "ritira", vecchio)])
    con.commit()
    con.close()
    banco.DETTO.clear()
    await S.sollecita_firme_nostr()
    detto = [t for chi, t in banco.DETTO if chi == LUI]
    prova("col «no» e due cancellazioni: UN promemoria, che le chiama "
          "per nome e dice la frase dei separati",
          (1, True, True, False),
          (len(detto), bool(detto) and "2 tuoi annunci sono ancora" in detto[0],
           bool(detto) and "tenerli separati" in detto[0],
           bool(detto) and "a nome TUO" in detto[0]))
    con = S.db()
    con.execute("UPDATE utenti SET annunci_su_profilo_nostr=1, "
                "sollecito_firme_il=0, solleciti_firme=0 WHERE tg_id=?",
                (LUI,))
    con.execute("INSERT INTO firme_nostr(annuncio_id, tg_id, azione, creato) "
                "VALUES(?,?,?,?)", (a3, LUI, "pubblica", vecchio))
    con.commit()
    con.close()
    banco.DETTO.clear()
    await S.sollecita_firme_nostr()
    detto = [t for chi, t in banco.DETTO if chi == LUI]
    prova("col «si'», una pubblicazione e due cancellazioni: si contano le "
          "pubblicazioni, e le cancellazioni hanno la loro riga",
          (1, True, True, False),
          (len(detto), bool(detto) and "Un tuo annuncio aspetta" in detto[0],
           bool(detto) and "2 tuoi annunci sono ancora sul tuo profilo "
                           "Nostr da togliere" in detto[0],
           bool(detto) and "3 tuoi annunci" in detto[0]))


def main():
    print("=" * 58)
    print("  I MIEI ANNUNCI SUL MIO PROFILO NOSTR — il giro vero")
    print("=" * 58)
    banco.avvio()
    asyncio.run(scenario())
    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
