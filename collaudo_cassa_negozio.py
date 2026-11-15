# -*- coding: utf-8 -*-
"""LA CASSA IN NEGOZIO, fatta girare per davvero (15 nov 2026, cantiere
cassa-negozio).

Gira la STORIA sulle rotte vere del server, su un database usa-e-getta:

  · la cassa si apre: cosa puo' incassare chi vende, i suoi annunci col
    prezzo in sats di adesso (anche quelli a listino in euro), il conto
    di oggi;
  · un conto battuto: il totale lo fa il server (articoli + importo
    libero in sats o in euro), e la fattura la conia il wallet di chi
    vende dal suo Lightning address (il wallet di cartone della mancia);
  · ⚡ pagato: LUD-21 lo vede, la vendita si chiude, lo stock scala UNA
    volta, l'esaurito diventa venduto (e Nostr e il canale lo sanno);
  · ⛓️: l'indirizzo e' il prossimo `/0/i` della xpub di chi vende, la
    fila e' condivisa con gli ordini, mai lo stesso indirizzo due volte;
    visto in mempool = in arrivo, una conferma = pagata;
  · l'indirizzo FISSO: una transazione non paga due vendite, e una
    vecchia non paga una nuova;
  · il «✓ Ricevuto» a mano, l'annullo, lo storico, i no (lo stock, un
    annuncio altrui, la cifra vuota, la leva spenta, chi non ha dove
    ricevere), e nessuno legge le vendite di un altro.

NON TOCCA NIENTE DI VERO: config di cartone prima dell'import di server
(lo prepara `collaudo_mancia.avvio`), httpx e mempool di cartone,
nessun avviso spedito, nessun relay.

USO:  python collaudo_cassa_negozio.py
"""

import asyncio
import sqlite3
import sys

import collaudo_mancia as banco

PASSATE = FALLITE = 0
VENDE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}
ALTRO = {"id": 333, "nome": "Altro", "username": "altro", "admin": False}
TXS = {}             # indirizzo -> transazioni come le dice mempool
NOSTR = []           # (annuncio, stato) mandati alla piazza
CANALE = []          # annunci col ✅ sul canale


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def rifiuto(nome, codice, fn, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        c = getattr(e, "status_code", None)
        t = str(getattr(e, "detail", e))
        if c == codice and (not dentro or dentro.lower() in t.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso {codice} {dentro!r}\n      avuto:  {c} {t!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def main():
    print("=" * 58)
    print("  LA CASSA IN NEGOZIO — il giro vero")
    print("=" * 58)
    db = banco.avvio()
    SRV = banco.SRV
    from embit import bip32, bip39, script
    from embit.networks import NETWORKS
    N = NETWORKS["signet"]
    parole = bip39.mnemonic_from_bytes(bytes(16))
    radice = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(parole))
    vpub = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(parole),
                                 version=b"\x04\x5f\x18\xbc").derive(
        "m/84h/1h/0h").to_public().to_base58()

    def dal_wallet(i):
        k = radice.derive(f"m/84h/1h/0h/0/{i}")
        return script.p2wpkh(k.key.get_public_key()).address(N)

    async def cambio():
        return 100_000.0            # 1 € = 1.000 sats, conti tondi
    DEST = {222: {"tipo": "xpub", "valore": vpub}}

    async def txs_finte(indirizzo):
        return list(TXS.get(indirizzo, []))

    async def nostr_finto(aid, stato, **k):
        NOSTR.append((aid, stato))

    async def canale_finto(aid, venduto=True):
        CANALE.append(aid)

    SRV.cambio_btc_eur = cambio
    SRV._cassa_dest_onchain = lambda con, tg: DEST.get(int(tg))
    SRV._cassa_mempool_txs = txs_finte
    SRV.annuncio_su_nostr = nostr_finto
    SRV.promo_venduto = canale_finto
    SRV.CASSA_SECONDI_TRA_CONTROLLI = 0

    con = sqlite3.connect(db)
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,ln_address) "
                "VALUES(222,'Vende','vende','vende@wallet.esempio')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username) "
                "VALUES(333,'Altro','altro')")
    for aid, tit, vend, sats, eur, valuta, q in (
            (1, "Caffè in grani", 222, 5000, 0, "sats", 3),
            (2, "Tazza", 222, 0, 4.5, "eur", 1),
            (3, "Di un altro", 333, 9000, 0, "sats", 1)):
        con.execute("INSERT OR REPLACE INTO annunci(id,titolo,descrizione,"
                    "prezzo_sats,prezzo_eur,valuta,venditore_id,stato,categoria,"
                    "quantita,consegna,zona) VALUES(?,?,'x',?,?,?,?,'attivo',"
                    "'Altro',?,'mano','Pavia (PV)')",
                    (aid, tit, sats, eur, valuta, vend, q))
    con.execute("INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
                "importo_sats,stato,creato,aggiornato) VALUES(2,111,222,4000,"
                "'proposta',1,1)")
    con.commit()
    vero = con
    vero.row_factory = sqlite3.Row

    def chi(u):
        SRV.verifica_utente = lambda *a, **k: u

    def chiama(fn, *args, corpo=None):
        async def leggi(_req):
            return corpo or {}
        SRV.leggi_json = leggi
        return asyncio.run(fn(*args))

    def nuova(corpo):
        return chiama(SRV.cassa_nuova, None, "", "", corpo=corpo)

    def guarda(vid):
        return chiama(SRV.cassa_guarda, vid, "", "")

    def quantita(aid):
        return vero.execute("SELECT quantita, stato FROM annunci WHERE id=?",
                            (aid,)).fetchone()

    print("\n[la cassa si apre]")
    chi(VENDE)
    c = chiama(SRV.cassa_apri, "", "")
    prova("Lightning: c'e' l'indirizzo", True, c["ln"])
    prova("on-chain: c'e' la destinazione", True, c["onchain"])
    prova("i suoi due annunci, non quello altrui", [2, 1],
          [a["id"] for a in c["annunci"]])
    prova("la tazza in euro: 4,50 € = 4.500 sats", 4500,
          next(a for a in c["annunci"] if a["id"] == 2)["sats"])
    prova("oggi nessuna vendita", {"n": 0, "sats": 0}, c["oggi"])
    prova("/api/me dice la leva", True, "profilo[\"cassa_attiva\"]" in
          open(SRV.__file__, encoding="utf-8").read())

    print("\n[un conto in Lightning, pagato e visto da LUD-21]")
    v = nuova({"righe": [{"id": 1, "q": 2}], "extra_euro": 1.2,
               "nota": "tavolo 4", "metodo": "ln"})
    prova("totale: 2 × 5.000 + 1,20 € = 11.200", 11200, v["sats"])
    prova("la fattura e' del wallet di chi vende, della cifra giusta", 11200,
          SRV.zap_leggi_bolt11(v["ln"]["invoice"])["msat"] // 1000)
    prova("verificabile (LUD-21)", True, v["ln"]["verificabile"])
    prova("niente indirizzo on-chain finche' non serve", None, v["onchain"])
    prova("in attesa", "attesa", v["stato"])
    prova("lo stock non scala prima del pagamento", 3, quantita(1)["quantita"])
    prova("ancora in attesa al battito", "attesa", guarda(v["id"])["stato"])
    h = vero.execute("SELECT ln_hash FROM cassa_vendite WHERE id=?",
                     (v["id"],)).fetchone()["ln_hash"]
    banco.WALLET["pagate"].add(h)
    g = guarda(v["id"])
    prova("pagata appena il wallet lo dice", ("pagata", "lud21"),
          (g["stato"], g["come"]))
    w = chiama(SRV.cassa_metodo, v["id"], None, "", "", corpo={"metodo": "onchain"})
    prova("a vendita pagata il tocco ⛓️ non conia niente", None, w["onchain"])
    prova("lo stock scala di 2", 1, quantita(1)["quantita"])
    guarda(v["id"])
    chiama(SRV.cassa_chiudi_a_mano, v["id"], "", "")
    prova("...e non due volte", 1, quantita(1)["quantita"])
    prova("nessun esaurito, niente Nostr", [], NOSTR)

    print("\n[on-chain: la xpub di chi vende, mai due volte lo stesso indirizzo]")
    v2 = nuova({"righe": [{"id": 2, "q": 1}], "metodo": "onchain"})
    prova("indirizzo /0/0 del wallet di chi vende", dal_wallet(0),
          v2["onchain"]["indirizzo"])
    prova("il QR porta la cifra in BTC", True,
          v2["onchain"]["uri"].startswith(f"bitcoin:{dal_wallet(0)}?amount=0.000045"))
    v3 = nuova({"extra_sats": 2000, "metodo": "onchain"})
    prova("il conto dopo prende /0/1", dal_wallet(1), v3["onchain"]["indirizzo"])
    prova("la fila degli ordini conta la cassa", 2,
          SRV._onchain_prossimo_esterno(vero, 222, vpub))
    TXS[dal_wallet(0)] = [{"txid": "aa" * 32, "status": {"confirmed": False},
                           "vout": [{"scriptpubkey_address": dal_wallet(0),
                                     "value": 4500}]}]
    g = guarda(v2["id"])
    prova("visto in mempool: in arrivo", "in_arrivo", g["stato"])
    prova("col txid", "aa" * 32, g["onchain"]["txid"])
    prova("lo stock non scala in mempool", 1, quantita(2)["quantita"])
    TXS[dal_wallet(0)][0]["status"] = {"confirmed": True, "block_time": 2**31}
    g = guarda(v2["id"])
    prova("una conferma: pagata", ("pagata", "blocco"), (g["stato"], g["come"]))
    prova("l'ultima tazza: esaurita, venduto", (0, "venduto"),
          tuple(quantita(2)))
    prova("Nostr e il canale sanno che e' venduta", ([(2, "sold")], [2]),
          (NOSTR, CANALE))
    prova("l'offerta viva decade", "decaduta",
          vero.execute("SELECT stato FROM offerte WHERE annuncio_id=2").fetchone()[0])

    print("\n[il ⚡/⛓️ sullo stesso conto, e il «✓ Ricevuto» a mano]")
    banco.WALLET["verify"] = ""
    w = chiama(SRV.cassa_metodo, v3["id"], None, "", "", corpo={"metodo": "ln"})
    prova("il tocco ⚡ conia la fattura", True, bool(w["ln"]))
    prova("...e l'indirizzo di prima resta", dal_wallet(1), w["onchain"]["indirizzo"])
    prova("senza LUD-21: non verificabile", False, w["ln"]["verificabile"])
    r = chiama(SRV.cassa_chiudi_a_mano, v3["id"], "", "")
    prova("«✓ Ricevuto»: pagata a mano", ("pagata", "a_mano"), (r["stato"], r["come"]))

    print("\n[pagato col QR di prima: lo storico dice il metodo vero]")
    banco.WALLET["verify"] = "https://wallet.esempio/verify/{h}"
    p1 = nuova({"extra_sats": 3000, "metodo": "ln"})
    p1 = chiama(SRV.cassa_metodo, p1["id"], None, "", "", corpo={"metodo": "onchain"})
    prova("passata a ⛓️", "onchain", p1["metodo"])
    h1 = vero.execute("SELECT ln_hash FROM cassa_vendite WHERE id=?",
                      (p1["id"],)).fetchone()["ln_hash"]
    banco.WALLET["pagate"].add(h1)
    g = guarda(p1["id"])
    prova("pagata col ⚡ di prima: metodo ln", ("pagata", "ln"),
          (g["stato"], g["metodo"]))
    banco.WALLET["verify"] = ""

    print("\n[l'indirizzo fisso: una transazione paga una vendita sola]")
    DEST[222] = {"tipo": "indirizzo", "valore": dal_wallet(50)}
    f1 = nuova({"extra_sats": 1000, "metodo": "onchain"})
    f2 = nuova({"extra_sats": 1000, "metodo": "onchain"})
    prova("stesso indirizzo per le due", f1["onchain"]["indirizzo"],
          f2["onchain"]["indirizzo"])
    TXS[dal_wallet(50)] = [
        {"txid": "bb" * 32, "status": {"confirmed": True, "block_time": 1000},
         "vout": [{"scriptpubkey_address": dal_wallet(50), "value": 5000}]},
        {"txid": "cc" * 32, "status": {"confirmed": True, "block_time": 2**31},
         "vout": [{"scriptpubkey_address": dal_wallet(50), "value": 1000}]}]
    prova("la prima prende la nuova, non quella vecchia", ("pagata", "cc" * 32),
          (guarda(f1["id"])["stato"], guarda(f1["id"])["onchain"]["txid"]))
    prova("la seconda non si paga con la stessa", "attesa",
          guarda(f2["id"])["stato"])
    a = chiama(SRV.cassa_annulla, f2["id"], "", "")
    prova("annullata", "annullata", a["stato"])

    print("\n[i no]")
    rifiuto("piu' pezzi di quelli in vetrina", 400,
            lambda: nuova({"righe": [{"id": 1, "q": 5}]}), "ne restano")
    rifiuto("l'annuncio di un altro", 400,
            lambda: nuova({"righe": [{"id": 3, "q": 1}]}), "non è più in vetrina")
    rifiuto("un annuncio esaurito", 400,
            lambda: nuova({"righe": [{"id": 2, "q": 1}]}))
    rifiuto("niente da incassare", 400, lambda: nuova({}), "importo")
    rifiuto("importo negativo", 400, lambda: nuova({"extra_sats": -5}))
    rifiuto("on-chain sotto la polvere", 400,
            lambda: nuova({"extra_sats": 100, "metodo": "onchain"}), "546")
    SRV.CASSA_MAX_SATS = 5000
    rifiuto("sopra il tetto della leva", 400,
            lambda: nuova({"extra_sats": 6000}), "massimo")
    SRV.CASSA_MAX_SATS = 0
    chi(ALTRO)
    rifiuto("senza Lightning address, niente fattura", 400,
            lambda: nuova({"extra_sats": 1000}), "Lightning address")
    rifiuto("le vendite di un altro non si leggono", 404,
            lambda: guarda(v["id"]))
    rifiuto("...ne' si chiudono", 404,
            lambda: chiama(SRV.cassa_chiudi_a_mano, f2["id"], "", ""))
    prova("a lui la cassa dice che non ha dove ricevere", (False, False),
          (lambda c: (c["ln"], c["onchain"]))(chiama(SRV.cassa_apri, "", "")))
    SRV.CASSA_ATTIVA = False
    rifiuto("leva spenta: la cassa non c'e'", 404,
            lambda: chiama(SRV.cassa_apri, "", ""))
    SRV.CASSA_ATTIVA = True

    print("\n[lo storico e il conto di oggi]")
    chi(VENDE)
    s = chiama(SRV.cassa_storico, "", "")
    prova("cinque vendite pagate, la piu' recente prima",
          [f1["id"], p1["id"], v3["id"], v2["id"], v["id"]],
          [x["id"] for x in s["vendite"]])
    prova("oggi: 5 vendite, 11.200 + 4.500 + 2.000 + 3.000 + 1.000", (5, 21700),
          (s["oggi"]["n"], s["oggi"]["sats"]))
    prova("la nota resta", "tavolo 4", s["vendite"][-1]["nota"])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
