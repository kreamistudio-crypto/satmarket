# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL «TURTLE»: l'adozione per titolo, ricostruita (23 ott 2026,
cantiere adozione-titolo, decisione di Andrea).

Dal campo: un venditore con la npub collegata rifà da Telegram il suo
annuncio «Turtle (marrone)» con la descrizione lunga. L'annuncio nasce
qui senza evento — col BIVIO aspetta la SUA firma, che dal telefono non
arriva — e sui relay c'e' ancora un suo vecchio 30402 con lo stesso
titolo. Al giro d'import dopo (ogni ora) l'import, non trovandolo per
`d`, lo cercava per TITOLO e si prendeva la riga nativa: testo vecchio
al posto del nuovo, tagliato a 1.500 caratteri, il pallino 🟣, e la
Modifica che da li' in poi chiede la firma.

QUI GIRA L'IMPORT VERO (`importa_venditore`) su un database usa-e-getta,
col calco di `collaudo_due_teste`: config finto PRIMA dell'import del
server, relay di cartone, nessuna foto scaricata, il cambio a mano.
Le domande:
  · la riga nativa senza evento non si adotta, ne' per l'aggiornamento
    ne' per il ramo «venduto»: testo, stato e proprietario restano suoi;
  · se l'importato vecchio e' stato cancellato, l'evento non risorge; se
    non c'e', nasce una riga importata NUOVA accanto (le due restano due);
  · un evento piu' vecchio della riga non la ricopre (e non la spegne);
  · la descrizione importata non si taglia piu' a 1.500 caratteri, e ha
    ancora un tetto;
  · la moderazione non ripaga l'AI ogni ora per l'evento che lo scudo
    salta (`_da_giudicare` guarda prima la riga importata).

NESSUNA RETE.

USO:  python collaudo_turtle.py
"""

import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = IMP = None

VENDITORE = 7340001
CHIAVE = "c3" * 32                       # la sua, in esadecimale
NPUB = ""
TITOLO = "Turtle (marrone)"
LUNGA = ("Tartaruga di peluche marrone, cucita a mano. " * 70).strip()   # ~3.100
VECCHIA = ("Tartaruga marrone, come nuova. " * 90).strip()               # ~2.800


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
    global SRV, IMP, NPUB
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-turtle-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    for nome, val in (("BOT_TOKEN", "0:collaudo"),
                      ("ANTHROPIC_API_KEY", "INCOLLA_QUI"),
                      ("LNBITS_URL", "http://127.0.0.1:1"),
                      ("LNBITS_INVOICE_KEY", "INCOLLA_QUI"),
                      ("LNBITS_ADMIN_KEY", "INCOLLA_QUI"),
                      ("ADMIN_IDS", [999]), ("MODALITA_COLLAUDO", True),
                      ("COMMISSIONE_PERCENTO", 0), ("ORE_CONFERMA", 72),
                      ("GIORNI_AUTO_SBLOCCO", 10),
                      ("MODELLO_RICERCA", "claude-haiku-4-5-20251001"),
                      ("DB", db)):
        setattr(cfg, nome, val)
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    import importa_nostr
    SRV, IMP = server, importa_nostr
    NPUB = server.hex_to_npub(CHIAVE)
    IMP.RELAYS = ["wss://finto"]
    IMP.DB = db


def evento(d, titolo=TITOLO, testo=VECCHIA, quando=None, venduto=False,
           eid=None):
    """Un suo 30402: la sua chiave, una coordinata, una foto (un mai
    visto senza foto non nasce). Il contenuto ha il footer di Barattolo,
    com'e' un evento composto qui e firmato col BIVIO."""
    tags = [["d", d], ["title", titolo], ["price", "21000", "SAT"],
            ["location", "Torino"], ["image", f"https://foto.test/{d}.jpg"]]
    if venduto:
        tags.append(["status", "sold"])
    contenuto = (testo + "\n\nPrezzo: 21000 sats — zona: Torino\n\n🫙⚡ In "
                 "vendita su Barattolo, il mercatino in sats con escrow "
                 "Lightning: https://barattolo.store")
    return {"id": eid or ("ab" * 32), "pubkey": CHIAVE, "kind": 30402,
            "created_at": int(quando or time.time()), "content": contenuto,
            "tags": tags}


def importa(eventi):
    IMP.interroga = lambda relay, hexkey: list(eventi)
    return IMP.importa_venditore(NPUB, VENDITORE, db=SRV.DB,
                                 cambio={"EUR": 60_000.0, "USD": 65_000.0},
                                 scarica=lambda url: None)


def semina(con_importato_cancellato=False):
    """Il campo: lui (npub collegata), e il Turtle rifatto da Telegram —
    riga NATIVA, descrizione lunga, nessun evento (la firma aspetta)."""
    con = SRV.db()
    con.execute("DELETE FROM annunci")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,npub,"
                "npub_verificata,npub_accesso,registrato) "
                "VALUES(?,?,?,?,?,?)", (VENDITORE, "Lui", NPUB, 1, NPUB, 1))
    adesso = int(time.time())
    con.execute(
        "INSERT INTO annunci(id,venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,foto,contatto_nostr,nostr_event_id,nostr_autore,"
        "nostr_origine_d,stato,creato) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (300, VENDITORE, TITOLO, LUNGA, "Giocattoli", 21000, "Torino", "[]",
         "", "", "", "", "attivo", adesso))
    if con_importato_cancellato:
        # l'importato di ieri, che lui ha cancellato dall'app
        con.execute(
            "INSERT INTO annunci(id,venditore_id,titolo,descrizione,"
            "categoria,prezzo_sats,zona,foto,contatto_nostr,"
            "nostr_origine_d,stato,creato,modificato) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (310, VENDITORE, TITOLO, VECCHIA[:1500], "Giocattoli", 21000,
             "Torino", "[]", NPUB, "barattolo-250", "rimosso",
             adesso - 86400, adesso - 2 * 86400))
    con.commit()
    con.close()


def riga(aid):
    con = SRV.db()
    r = con.execute("SELECT stato, contatto_nostr, length(descrizione) AS n, "
                    "descrizione, nostr_origine_d, modificato FROM annunci "
                    "WHERE id=?", (aid,)).fetchone()
    con.close()
    return r


def importati():
    con = SRV.db()
    r = [tuple(x) for x in con.execute(
        "SELECT id, stato, length(descrizione) FROM annunci "
        "WHERE contatto_nostr<>'' AND id<>310 ORDER BY id").fetchall()]
    con.close()
    return r


def main():
    print("=" * 58)
    print("  IL «TURTLE» — l'adozione per titolo, ricostruita")
    print("=" * 58)
    avvio()
    ieri = time.time() - 86400

    print("\n[il vecchio evento non si prende la riga nativa]")
    for d, come in (("barattolo-250", "la coordinata di una riga che "
                     "non c'e' piu'"), ("turtle-1", "un d del suo client")):
        semina()
        importa([evento(d, quando=ieri)])
        r = riga(300)
        prova(f"{come}: la riga nativa resta sua (niente 🟣)", "",
              r["contatto_nostr"])
        prova("...col SUO testo lungo, intero", (len(LUNGA), LUNGA),
              (r["n"], r["descrizione"]))
        prova("...attiva, e senza coordinata d'import", ("attivo", ""),
              (r["stato"], r["nostr_origine_d"] or ""))
        nuove = importati()
        prova("...e l'evento nasce come riga importata NUOVA accanto "
              "(le due restano due, la deduplica le vede)", 1, len(nuove))

    print("\n[l'importato di ieri cancellato: l'evento non risorge]")
    semina(con_importato_cancellato=True)
    importa([evento("barattolo-250", quando=ieri)])
    prova("la riga nativa resta sua e lunga", ("", len(LUNGA), "attivo"),
          (riga(300)["contatto_nostr"], riga(300)["n"], riga(300)["stato"]))
    prova("...e non nasce nessun importato nuovo (lo scudo)", [], importati())
    prova("...e quello cancellato resta cancellato", "rimosso",
          riga(310)["stato"])

    print("\n[il ramo «venduto» non spegne una riga nativa omonima]")
    semina()
    importa([evento("turtle-vecchio", quando=ieri, venduto=True)])
    prova("un omonimo venduto sui relay: la riga nativa resta in vetrina",
          "attivo", riga(300)["stato"])

    print("\n[un evento piu' vecchio della riga non la ricopre]")
    semina()
    importa([evento("turtle-1", testo="Versione di oggi.", quando=time.time())])
    imp = importati()[0][0]
    oggi = riga(imp)
    prova("l'evento di oggi nasce importato col suo testo",
          True, oggi["descrizione"].startswith("Versione di oggi."))
    importa([evento("turtle-1", testo="Versione di ieri.", quando=ieri,
                    eid="cd" * 32)])
    prova("la versione di IERI (un relay rimasto indietro) non la ricopre",
          True, riga(imp)["descrizione"].startswith("Versione di oggi."))
    importa([evento("turtle-1", testo="Versione di domani.",
                    quando=time.time() + 60, eid="ef" * 32)])
    prova("...una versione piu' nuova si'", True,
          riga(imp)["descrizione"].startswith("Versione di domani."))
    importa([evento("turtle-1", quando=ieri, venduto=True, eid="aa" * 32)])
    prova("...e un «venduto» piu' vecchio della riga non la spegne",
          "attivo", riga(imp)["stato"])

    print("\n[il tetto della descrizione importata]")
    prova("il tetto e' uno, e non e' piu' 1.500", 10000,
          IMP.DESCRIZIONE_IMPORT_MAX)
    _, d = IMP.testo_evento(evento("x", testo=LUNGA))
    prova("una descrizione lunga come quella del Turtle entra intera",
          True, d.startswith(LUNGA) and len(d) > 1500)
    _, d = IMP.testo_evento(evento("x", testo="z" * 15000))
    prova("...e un testo enorme si ferma al tetto", 10000, len(d))

    print("\n[la moderazione guarda prima la riga importata]")
    semina(con_importato_cancellato=True)
    nuovi, noti = SRV._da_giudicare([evento("barattolo-999", quando=ieri)],
                                    NPUB, VENDITORE)
    prova("con l'importato cancellato l'evento e' «gia' deciso»: niente AI "
          "a ogni giro per un annuncio che lo scudo salta", (0, 1),
          (len(nuovi), len(noti)))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
