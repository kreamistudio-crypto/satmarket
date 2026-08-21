# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CONSEGNA SULLA STRADA FIRMATA (ago 2026).

`prove.py` difende la FORMA — che la dichiarazione sia la PRESENZA
della chiave, che l'UPDATE sia condizionato, che le due tariffe che i
relay non sanno rileggere restino fuori — e fa girare il giro chiuso
`estrai_commercio(evento_annuncio_importato(...))`. Quello che non puo'
fare e' far girare i DUE ENDPOINT veri su un database vero: le sue
prove leggono il sorgente, non vedono cosa finisce in colonna.

Questo script chiude quel buco, ed e' il calco di
`collaudo_due_teste.py`. Il caso e' quello dal campo — sei importati
attivi senza consegna, e nessun modo di dichiararla — e chiede le sette
cose su cui il cantiere si regge:

  · IL GIRO VERO: fase 1 → firma Schnorr → fase 2, e la consegna
    finisce in colonna E nei tag dell'evento che va sui relay;
  · «CHIAVE ASSENTE = CONSERVA», che e' la riga da non ammorbidire: un
    client rimasto in cache manda le cinque chiavi di ieri e NON deve
    azzerare la consegna dei due importati digitali corretti a mano.
    E' la prova regina di questo file: se un domani qualcuno rende
    l'UPDATE incondizionato, questa riga MOSTRA il danno;
  · il digitale da questa porta non passa (400 esplicito);
  · le colonne che i relay non sanno rileggere restano INTATTE dopo
    una modifica firmata — tariffa punto, supplemento, taglia;
  · la zona CATALANA passa (esigi_luogo spenta), che e' il caso
    misurato dei sei: «baixllobregat» e «maresme» non sono comuni;
  · ...ma il ritiro senza zona no: quella meta' della guardia resta;
  · la quantita' assente conserva lo stock.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
rete: i relay sono di cartone e la moderazione AI e' spenta (chiave
segnaposto). Senza `coincurve` non si puo' firmare: si SALTA contando,
il patto di salta() in prove.py.

USO:  python collaudo_consegna_firmata.py
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = SALTATE = 0
SRV = None

VENDITORE = -777                         # nativo Nostr, id negativo
SEGRETO = "cc" * 32                      # la sua chiave privata
CHIAVE = NPUB = ""                       # pubkey hex e npub (in avvio)


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def salta(nome, perche):
    global SALTATE
    SALTATE += 1
    print(f"  ⊘ {nome} — SALTATA: {perche}")


def avvio():
    global SRV, CHIAVE, NPUB
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-firmata-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"      # moderazione AI spenta
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    if server.ChiavePubblicaNostr is None:
        return None
    from coincurve import PrivateKey
    CHIAVE = PrivateKey(bytes.fromhex(SEGRETO)).public_key.format()[1:].hex()
    NPUB = server.hex_to_npub(CHIAVE)

    async def muto(*a, **k):
        return None
    server.notifica = muto
    server.notifica_admin = muto
    # Il backstop verso i relay: nessuna rete, e si ricorda cosa gli e'
    # passato — l'evento che parte e' l'altra meta' della prova.
    server._spediti = []

    async def spedisci(ev, relays):
        server._spediti.append(ev)
    server._spedisci_ai_relay = spedisci
    server.verifica_utente = lambda *a, **k: {"id": VENDITORE,
                                              "first_name": "Nativo"}
    return db


def firma(evento):
    """La firma vera del venditore, com'e' quella del suo browser."""
    from coincurve import PrivateKey
    ev = SRV.evento_non_firmato(CHIAVE, evento["kind"], evento["tags"],
                                evento["content"], evento["created_at"])
    sig = PrivateKey(bytes.fromhex(SEGRETO)).sign_schnorr(
        bytes.fromhex(ev["id"])).hex()
    return ev["id"], sig


def chiama(fn, *args, corpo=None):
    """Una rotta vera, col suo corpo JSON (il patto di collaudo_pausa:
    si cede il controllo, o i create_task non partirebbero)."""
    async def leggi(_req):
        return corpo if corpo is not None else {}
    SRV.leggi_json = leggi

    async def giro():
        r = await fn(*args)
        await asyncio.sleep(0.02)
        return r
    return asyncio.run(giro())


def semina(con, **extra):
    """Un importato attivo del nostro venditore, com'e' in produzione:
    contatto_nostr pieno, coordinata registrata, consegna vuota."""
    campi = {"titolo": "Sacco di riso 4 kg", "descrizione": "Riso vero",
             "categoria": "Alimenti e bevande", "zona": "Verona",
             "prezzo_sats": 50000, "venditore_id": VENDITORE,
             "stato": "attivo", "contatto_nostr": NPUB,
             "nostr_origine_d": "riso-1", "consegna": "",
             "condizione": "", "quantita": 1, "quantita_max": 1,
             "spedizione_punto_sats": 300, "spedizione_punto_dichiarata": 1,
             "spedizione_extra_sats": 150, "taglia_pacco": "medio",
             "creato": int(time.time()), "foto": "[]"}
    campi.update(extra)
    coll = ", ".join(campi)
    seg = ", ".join("?" * len(campi))
    cur = con.execute(f"INSERT INTO annunci({coll}) VALUES({seg})",
                      tuple(campi.values()))
    con.commit()
    return cur.lastrowid


def riga(con, aid):
    return dict(con.execute("SELECT * FROM annunci WHERE id=?",
                            (aid,)).fetchone())


def modifica(aid, **extra):
    """Il giro completo: prepara → firma → consegna. Torna l'errore
    (codice, messaggio) se una delle due fasi rifiuta."""
    corpo = {"titolo": "Sacco di riso 4 kg", "prezzo_sats": 50000,
             "categoria": "Alimenti e bevande", "zona": "Verona",
             "descrizione": "Riso vero"}
    corpo.update(extra)
    try:
        d = chiama(SRV.modifica_firmata_prepara, aid, None, corpo=corpo)
    except Exception as e:
        return ("errore", getattr(e, "status_code", "?"), str(e))
    _id, sig = firma(d["evento"])
    try:
        chiama(SRV.modifica_firmata, aid, None,
               corpo={"biglietto": d["biglietto"], "pubkey": CHIAVE,
                      "sig": sig})
    except Exception as e:
        return ("errore", getattr(e, "status_code", "?"), str(e))
    return ("ok", d["evento"]["tags"], None)


def tag_delivery(tags):
    return [t for t in tags if t and t[0] == "delivery"]


def main():
    print("=" * 58)
    print("  LA CONSEGNA SULLA STRADA FIRMATA")
    print("=" * 58)
    db = avvio()
    if db is None:
        salta("tutto il collaudo", "manca coincurve: non si puo' firmare")
        print(f"\n  {PASSATE} passate, {FALLITE} fallite, {SALTATE} saltate")
        return 0
    con = SRV.db()
    con.execute("INSERT INTO utenti(tg_id, nome, username, npub, "
                "npub_verificata, npub_accesso) VALUES(?,?,?,?,1,?)",
                (VENDITORE, "Nativo", "", NPUB, NPUB))
    con.commit()

    # --- 1. IL GIRO VERO --------------------------------------------
    print("\n[il giro vero]")
    aid = semina(con)
    esito, tags, _ = modifica(aid, consegna="spedizione",
                              spedizione_sats=800, condizione="",
                              quantita=3)
    prova("la modifica firmata passa", "ok", esito)
    r = riga(con, aid)
    prova("la consegna finisce in colonna", "spedizione", r["consegna"])
    prova("...col suo costo", 800, r["spedizione_sats"])
    prova("...e la quantita' pure", 3, r["quantita"])
    prova("la memoria dei pezzi sale col MAX", 3, r["quantita_max"])
    prova("l'evento che va sui relay porta il tag delivery",
          [["delivery", "shipping", "800", "sats"]], tag_delivery(tags))
    prova("...ed e' l'evento che il backstop ha spedito", True,
          bool(SRV._spediti) and ["delivery", "shipping", "800", "sats"]
          in SRV._spediti[-1]["tags"])
    # La condizione: «Alimenti e bevande» e' senza_condizione, quindi
    # il giudice unico la azzera — e il tag non compare.
    prova("la condizione dove non vuol dire niente resta vuota", "",
          r["condizione"])

    # --- 2. LE COLONNE CHE NON SI TOCCANO ---------------------------
    print("\n[quel che i relay non sanno rileggere resta dov'e']")
    prova("la tariffa punto e' intatta", 300, r["spedizione_punto_sats"])
    prova("...e la sua dichiarazione", 1, r["spedizione_punto_dichiarata"])
    prova("il supplemento per pezzo e' intatto", 150,
          r["spedizione_extra_sats"])
    prova("la taglia del pacco e' intatta", "medio", r["taglia_pacco"])

    # --- 3. LA PROVA REGINA: il client di ieri non azzera niente -----
    print("\n[chiave assente = conserva]")
    # I due importati DIGITALI corretti a mano: la loro consegna non
    # vive sui relay, e un UPDATE incondizionato se la porterebbe via.
    dig = semina(con, titolo="Licenza Panda Dome", consegna="digitale",
                 categoria="Bitcoin", condizione="nuovo",
                 nostr_origine_d="panda-1", quantita=2, quantita_max=2)
    esito, _, _ = modifica(dig, titolo="Licenza Panda Dome",
                           categoria="Bitcoin")
    prova("il client di ieri salva lo stesso", "ok", esito)
    d = riga(con, dig)
    prova("...e la consegna digitale NON si azzera", "digitale",
          d["consegna"])
    prova("...ne' la condizione", "nuovo", d["condizione"])
    prova("...ne' la quantita'", 2, d["quantita"])
    prova("...ma il titolo si e' aggiornato davvero",
          "Licenza Panda Dome", d["titolo"])

    # --- 4. IL DIGITALE DA QUESTA PORTA NON PASSA -------------------
    print("\n[il codice online resta un gesto nostro]")
    esito, code, msg = modifica(dig, titolo="Licenza Panda Dome",
                                categoria="Bitcoin", consegna="digitale")
    prova("dichiarare il digitale da qui: 400", "errore", esito)
    prova("...col messaggio che dice cosa fare", True,
          "scrivici" in str(msg))
    prova("...e la riga non si e' mossa", "digitale",
          riga(con, dig)["consegna"])
    # La combo nemmeno: e' quella che si degraderebbe al primo import.
    esito, _, _ = modifica(dig, titolo="Licenza Panda Dome",
                           categoria="Bitcoin", consegna="spedizione",
                           anche_digitale=1)
    prova("la combo si puo' chiedere, ma il flag non passa", 0,
          riga(con, dig)["anche_digitale"])

    # --- 5. LA ZONA CHE PUO' ESSERE FUORI DALL'ITALIA ---------------
    print("\n[la zona la scrivono i relay]")
    cat = semina(con, titolo="Vino catalano", zona="baixllobregat",
                 categoria="Alimenti e bevande", nostr_origine_d="vino-1")
    esito, _, msg = modifica(cat, titolo="Vino catalano",
                             categoria="Alimenti e bevande",
                             zona="baixllobregat", consegna="spedizione",
                             spedizione_sats=500)
    prova("la comarca catalana non blocca la dichiarazione", "ok", esito)
    prova("...e la consegna e' passata", "spedizione",
          riga(con, cat)["consegna"])
    # ...ma il ritiro senza zona SI': chi viene a ritirare deve sapere
    # dove, e quella meta' della guardia non si e' spenta.
    esito, code, _ = modifica(cat, titolo="Vino catalano",
                              categoria="Alimenti e bevande", zona="",
                              consegna="ritiro")
    prova("il ritiro senza zona resta un 400", "errore", esito)

    # --- 6. LA QUANTITA' ASSENTE CONSERVA ---------------------------
    print("\n[lo stock, il patto di sempre]")
    q = semina(con, titolo="Miele", nostr_origine_d="miele-1",
               quantita=7, quantita_max=9, categoria="Alimenti e bevande")
    modifica(q, titolo="Miele", categoria="Alimenti e bevande",
             consegna="ritiro")
    rq = riga(con, q)
    prova("senza la chiave lo stock resta", 7, rq["quantita"])
    prova("...e la memoria dei pezzi non scende", 9, rq["quantita_max"])
    # LA CHIAVE PRESENTE MA VUOTA e' l'altro caso, e nessuno lo
    # esercitava: se_manca esiste per questo — un client che manda
    # `"quantita": null` non deve riportare lo stock a UNO. L'ha
    # scoperto la tortura (la mutazione che toglie se_manca
    # sopravviveva a tutto).
    modifica(q, titolo="Miele", categoria="Alimenti e bevande",
             consegna="ritiro", quantita=None)
    prova("la chiave VUOTA conserva anche lei", 7,
          riga(con, q)["quantita"])

    con.close()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite, {SALTATE} saltate")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
