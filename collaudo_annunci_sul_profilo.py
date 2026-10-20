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
(coincurve), come le farebbe il suo firmatario.

NESSUNA RETE.

USO:  python collaudo_annunci_sul_profilo.py
"""

import asyncio
import hashlib
import json
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
LUI = 4242
SPEDITI = []          # gli eventi che sarebbero andati ai relay


def firma_sua(sk, ev):
    """Firma l'evento preparato dal server con la chiave dell'utente,
    come farebbe il suo firmatario (NIP-01: id ricalcolato, Schnorr)."""
    pub = sk.public_key.format()[1:].hex()
    serial = json.dumps([0, pub, ev["created_at"], ev["kind"], ev["tags"],
                         ev["content"]], separators=(",", ":"),
                        ensure_ascii=False)
    ev_id = hashlib.sha256(serial.encode("utf-8")).hexdigest()
    return pub, ev_id, sk.sign_schnorr(bytes.fromhex(ev_id)).hex()


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
    from coincurve import PrivateKey
    piattaforma = PrivateKey()
    S._NOSTR = (piattaforma, piattaforma.public_key.format()[1:].hex())
    nostra = S._NOSTR[1]

    async def spedisci_finto(evento, relays=None):
        SPEDITI.append(evento)
        return 1
    S._spedisci_ai_relay = spedisci_finto

    sk = PrivateKey()
    sua = sk.public_key.format()[1:].hex()
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
    con.execute("INSERT INTO firme_nostr(annuncio_id, tg_id, azione, creato) "
                "VALUES(?,?,?,?)", (a4, LUI, "ritira", int(time.time())))
    con.commit()
    con.close()
    await json_di({"si": True})
    r = await S.scegli_annunci_sul_profilo(None, "", "")
    prova("una cancellazione non firmata su un annuncio vivo si butta, e "
          "i nostri quattro eventi si accodano per la sua firma",
          (True, [(a1, "pubblica"), (a2, "pubblica"), (a3, "pubblica"),
                  (a4, "pubblica")]),
          (r["si"], coda(S)))


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
