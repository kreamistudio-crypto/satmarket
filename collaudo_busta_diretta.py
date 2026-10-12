# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA BUSTA DIRETTA (ago 2026, cantiere 45).

Quando il venditore spedisce a un locker puo' mettere l'email del
COMPRATORE come destinatario: il codice di ritiro arriva a lui
direttamente dal corriere, senza passare da Barattolo. `prove.py`
difende la FORMA (la clausola nella WHERE, il deposito che azzera, la
guardia nell'endpoint); questo script CAMMINA il giro — server vero su
un database usa-e-getta, LNbits finto:

  1. ordine via punto, spedito CON la spunta: la dichiarazione si
     timbra e la notifica dice «te lo manda direttamente il corriere»,
     mai «ti avviseremo»;
  2. il gemello SENZA spunta resta il mondo di ieri: «ti avviseremo»,
     e a 4 giorni il sollecito squilla — col testo che NOMINA la porta
     tardiva, che e' come i distratti la scoprono;
  3. sull'ordine dichiarato il sollecito TACE, e tace anche il 🧊 al
     tetto (stessa query);
  4. la PORTA TARDIVA coi suoi rifiuti (il compratore, l'estraneo
     indistinguibile dall'inesistente, l'ordine non spedito, la busta
     gia' depositata), il timbro senza muovere le ancore, il doppio
     tocco idempotente senza seconda notifica;
  5. il DEPOSITO che azzera la dichiarazione (l'annulla naturale), col
     «ti aspetta» di sempre;
  6. la disputa sul dichiarato: la nota al moderatore dice la
     dichiarazione con la data, ETICHETTATA di parte — mai piu' il
     falso «MAI depositate»;
  7. la ronda del libro mastro che TACE sul sano e trova la riga rotta
     («dichiarata fuori dalla via punto») col suo id.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. LNbits non viene mai chiamato: gira senza rete
e senza chiavi.

USO:  python collaudo_busta_diretta.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
DETTO = []          # (destinatario, testo) di ogni notifica
ADMIN = []          # i testi arrivati ai moderatori


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  [ok] {nome}")
    else:
        FALLITE += 1
        print(f"  [KO] {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server (la liturgia di
    collaudo_punto_concordato). Le leve restano quelle di produzione:
    il tempo si fa passare RETRODATANDO l'ordine."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("[!] server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-diretta-"),
                      "usa-e-getta.db")
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
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        return {"payment_hash": f"hash{int(time.time()*1000000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    # DUE REGISTRI, DUE MESTIERI (12 ott 2026, cantiere punti-ritiro):
    # dal gruppo degli admin la nota della DISPUTA non e' piu' un ciclo
    # di `notifica()` su ADMIN_IDS — passa da `notifica_admin` con
    # l'argomento «dispute» — e questo finto la buttava fra i testi
    # della ronda, dove la sezione della disputa non guarda: rossa su
    # main da quel giorno, e nessuno lo vedeva perche' questo collaudo
    # non era fra quelli della CI (adesso c'e'). La nota al moderatore
    # torna fra i DETTI a 999, l'unico admin di questo config; il resto
    # e' della ronda. E' il calco di collaudo_punti_barattolo.
    async def admin_finto(testo, *a, **k):
        if k.get("argomento") == "dispute":
            DETTO.append((999, testo))
            return
        ADMIN.append(testo)

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.notifica_admin = admin_finto
    server.polso_ordini_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": admin}


def chiama(fn, *args, corpo=None):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def rifiuto(fn, *args, corpo=None):
    """Torna (codice, messaggio) invece di far esplodere il collaudo."""
    try:
        chiama(fn, *args, corpo=corpo)
        return 0, ""
    except SRV.HTTPException as e:
        return e.status_code, str(e.detail)


def riga(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return dict(o)


def tocca(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET "
                + ", ".join(f"{k}=?" for k in campi)
                + " WHERE id=?", tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address,spedizionieri,spedizioniere) "
                "VALUES(222,'Vende','neg22222',1,'','|InPost|','InPost')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(111,'Compra','neg11111',1,"
                "'compra@wallet.tld')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(333,'Estraneo','neg33333',1,'')")
    ids = []
    for n in range(6):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "spedizione_sats) VALUES(222,?,'una cosa vera',50000,'Altro',"
            "'Pavia (PV)','attivo',1,'spedizione',9,'sats','nuovo',1000)",
            (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_al_punto(annuncio_id, punto="Locker InPost Via Verdi 3"):
    """Compra via punto e porta l'ordine a 'locked' coi percorsi veri:
    il pagamento e' l'unico pezzo simulato."""
    come(111)
    c = chiama(SRV.compra, None, corpo={
        "annuncio_id": annuncio_id, "consegna": "spedizione",
        "spedizione_via": "punto", "punto_ritiro": punto,
        "tipo_punto": "locker"})
    oid = c["ordine_id"]
    tocca(oid, stato="locked")
    return oid


def spedisci(oid, diretta=False):
    come(222)
    corpo = {"corriere": "InPost", "tracking": "616555400308780213"}
    if diretta:
        corpo["busta_diretta"] = True
    return chiama(SRV.segna_spedito, oid, None, corpo=corpo)


def giro_buste():
    DETTO.clear()
    ADMIN.clear()
    asyncio.run(SRV.sollecita_buste_ferme())
    return list(DETTO), list(ADMIN)


def giro_diretti():
    """La TERZA SORELLA (ago 2026): il promemoria di chi aspetta un
    codice che non passa da qui."""
    DETTO.clear()
    ADMIN.clear()
    asyncio.run(SRV.sollecita_codici_diretti())
    return list(DETTO), list(ADMIN)


def main():
    G = 86400
    ora = int(time.time())
    print("=" * 60)
    print("  LA BUSTA DIRETTA — il giro vero")
    print("=" * 60)
    avvio()
    a1, a2, a3, a4, a5, a6 = semina()

    # ---- 1) la spunta alla spedizione ------------------------------
    print("\n[1] la spunta alla spedizione")
    o_dir = ordine_al_punto(a1)
    DETTO.clear()
    spedisci(o_dir, diretta=True)
    o = riga(o_dir)
    prova("l'ordine e' spedito e la dichiarazione e' timbrata", True,
          o["stato"] == "shipped" and o["busta_diretta_il"] > 0)
    testo = DETTO[-1][1] if DETTO else ""
    prova("la notifica dice il corriere, mai «ti avviseremo»", True,
          "direttamente il corriere" in testo
          and "Ti avviseremo" not in testo)

    # ---- 2) il gemello senza spunta: il mondo di ieri --------------
    print("\n[2] il gemello senza spunta")
    o_ieri = ordine_al_punto(a2)
    DETTO.clear()
    spedisci(o_ieri)
    o = riga(o_ieri)
    prova("senza spunta niente timbro, e la riga di sempre", True,
          o["busta_diretta_il"] == 0
          and "Ti avviseremo" in (DETTO[-1][1] if DETTO else ""))
    # a 4 giorni il sollecito squilla, e NOMINA la porta tardiva
    tocca(o_ieri, spedito_il=ora - 4 * G)
    detto, ghiaccio = giro_buste()
    prova("a 4 giorni il sollecito squilla al venditore", [222],
          [chi for chi, _ in detto])
    prova("...e nomina la porta tardiva («dillo dall'ordine»)", True,
          bool(detto) and "dillo dall'ordine" in detto[0][1])

    # ---- 3) sull'ordine dichiarato il sollecito tace ---------------
    print("\n[3] il silenzio del dichiarato")
    tocca(o_dir, spedito_il=ora - 4 * G)
    # il gemello ha appena ricevuto il suo squillo: azzerarlo isola
    # la domanda («squilla il SOLO non dichiarato?») dal calendario
    tocca(o_ieri, sollecito_busta_il=0, solleciti_busta=0)
    detto, ghiaccio = giro_buste()
    # il sollecito porta il TITOLO, non il numero: si distingue da li'
    # (o_ieri viene da «Cosa 1», il dichiarato o_dir da «Cosa 0»)
    testi = " || ".join(t for _, t in detto)
    prova("squilla il solo ordine NON dichiarato", True,
          len(detto) == 1 and "Cosa 1" in testi and "Cosa 0" not in testi)
    # ...e al tetto il 🧊 tace sul dichiarato (stessa query)
    tocca(o_dir, solleciti_busta=SRV.PROMEMORIA_CONFERMA_MAX,
          sollecito_busta_il=ora - 9 * G)
    detto, ghiaccio = giro_buste()
    prova("al tetto il 🧊 del dichiarato NON parte", [], ghiaccio)

    # ---- 4) la porta tardiva ---------------------------------------
    print("\n[4] la porta tardiva")
    o_tardi = o_ieri          # spedito senza spunta: il distratto
    come(111)
    prova("il compratore non dichiara", (400, "Operazione non permessa"),
          rifiuto(SRV.dichiara_busta_diretta, o_tardi))
    come(333)
    estraneo = rifiuto(SRV.dichiara_busta_diretta, o_tardi)
    come(222)
    inesistente = rifiuto(SRV.dichiara_busta_diretta, 777777)
    prova("l'estraneo e l'inesistente rispondono IDENTICO (anti-oracolo)",
          estraneo, inesistente)
    o_locked = ordine_al_punto(a3)
    come(222)
    prova("su un ordine non ancora spedito la porta non c'e'",
          (400, "Operazione non permessa"),
          rifiuto(SRV.dichiara_busta_diretta, o_locked))
    # la busta depositata chiude la porta
    come(222)
    chiama(SRV.deposita_busta_ritiro, o_dir, None,
           corpo={"nome": "Mario Rossi", "codice": "PIN 4321"})
    cod, msg = rifiuto(SRV.dichiara_busta_diretta, o_dir)
    prova("con la busta depositata la porta e' chiusa", True,
          cod == 400 and msg.startswith("Le istruzioni"))
    # ...e il deposito ha azzerato la dichiarazione (l'annulla naturale)
    prova("il deposito ha azzerato la dichiarazione", 0,
          riga(o_dir)["busta_diretta_il"])
    # il gesto vero, sul distratto
    prima = riga(o_tardi)
    DETTO.clear()
    r = chiama(SRV.dichiara_busta_diretta, o_tardi)
    dopo = riga(o_tardi)
    prova("la dichiarazione tardiva timbra", True,
          r["ok"] and dopo["busta_diretta_il"] > 0)
    prova("...senza muovere ancore ne' stato",
          (prima["spedito_il"], prima["aggiornato"], prima["stato"]),
          (dopo["spedito_il"], dopo["aggiornato"], dopo["stato"]))
    prova("...e avvisa il compratore", True,
          len(DETTO) == 1 and DETTO[0][0] == 111
          and "direttamente dal corriere" in DETTO[0][1])
    DETTO.clear()
    r2 = chiama(SRV.dichiara_busta_diretta, o_tardi)
    prova("il doppio tocco: ok idempotente, nessuna seconda notifica",
          True, r2["ok"] and DETTO == [])
    # e da li' il sollecito tace anche per lui
    tocca(o_tardi, sollecito_busta_il=0, solleciti_busta=0)
    detto, ghiaccio = giro_buste()
    prova("dopo la dichiarazione il sollecito tace", ([], []),
          (detto, ghiaccio))

    # ---- 5) il deposito sul dichiarato: il «ti aspetta» ------------
    print("\n[5] il deposito che supersede")
    DETTO.clear()
    come(222)
    chiama(SRV.deposita_busta_ritiro, o_tardi, None,
           corpo={"nome": "Rita Verdi", "codice": "PIN 9999"})
    o = riga(o_tardi)
    prova("busta depositata e dichiarazione azzerata insieme", True,
          o["busta_il"] > 0 and o["busta_diretta_il"] == 0)
    prova("...col «ti aspetta» di sempre", True,
          len(DETTO) == 1 and "ti aspetta" in DETTO[0][1])

    # ---- 6) la disputa sul dichiarato ------------------------------
    print("\n[6] la disputa")
    o_disp = ordine_al_punto(a4)
    spedisci(o_disp, diretta=True)
    DETTO.clear()
    come(111)
    chiama(SRV.apri_disputa, o_disp)
    # la nota ai moderatori viaggia con notifica_admin(), argomento
    # «dispute»: il finto dell'avvio la registra fra i DETTI a 999
    nota = " || ".join(t for chi, t in DETTO if chi == 999)
    prova("la nota dice la dichiarazione, con l'etichetta di parte",
          True, "ha DICHIARATO" in nota
          and "dichiarazione di parte" in nota)
    prova("...e non piu' il falso «MAI depositate»", False,
          "MAI depositate" in nota)

    # ---- 7) la ronda -----------------------------------------------
    print("\n[7] la ronda del libro mastro")

    def ronda():
        con = SRV.db()
        con.execute("DELETE FROM timbri WHERE nome=?",
                    (SRV.TIMBRO_LIBRO_MASTRO,))
        con.commit()
        con.close()
        ADMIN.clear()
        asyncio.run(SRV.controlla_libro_mastro())
        return list(ADMIN)

    # Sul sano si chiede il silenzio del NOSTRO controllo, non della
    # ronda intera: i controlli degli altri cantieri sono loro — uno
    # che esplodeva qui («righe d'offerta orfane» su una colonna che
    # il DDL vero non ha) l'ha trovato proprio questo collaudo, ed e'
    # il genere di bug che i cartoni di prove.py non possono vedere.
    # Curato dal suo cantiere; il perimetro stretto resta, cosi' un
    # controllo altrui rotto non tinge di rosso la busta diretta.
    sano = ronda()
    prova("sul sano il controllo della busta TACE", False,
          any("busta fuori contratto" in t for t in sano))
    # la riga rotta: dichiarata fuori dalla via punto
    tocca(o_disp, via_punto=0)
    ghiaccio = ronda()
    prova("la riga rotta si trova, col suo controllo e il suo id", True,
          any("busta fuori contratto" in t and str(o_disp) in t
              for t in ghiaccio))
    tocca(o_disp, via_punto=1)

    # ---- 8) il silenzio rotto (tappa A) ----------------------------
    # Fino a ieri un ordine dichiarato diretto era MUTO: tre gate lo
    # zittivano, e il primo squillo cadeva al giorno 10 (da
    # `sollecita_conferme_ferme`) mentre la giacenza al punto dura ~3
    # giorni — quando qualcuno bussava, il pacco era gia' tornato
    # indietro. Le sezioni 3 e 4 restano vere e restano giuste: a
    # tacere e' il sollecito DELLA BUSTA, che chiede al venditore una
    # cosa che li' non puo' fare. A parlare adesso e' un'altra
    # funzione, con un altro destinatario.
    print("\n[8] il silenzio rotto: il promemoria di chi aspetta")
    o_att = ordine_al_punto(a5)
    spedisci(o_att, diretta=True)
    tocca(o_att, spedito_il=ora - 2 * G)
    detto, ghiaccio = giro_diretti()
    prova("a 2 giorni squilla il SOLO compratore", [111],
          [chi for chi, _ in detto])
    testo = detto[0][1] if detto else ""
    # LA RIGA CHE IL CORRIERE NON MANDA MAI, ed e' la ragione per cui
    # questa funzione puo' esistere accanto alle altre due
    prova("...e gli dice di guardare anche nello spam", True,
          "spam" in testo)
    # l'ancora e' la SPEDIZIONE e non l'arrivo, che non sappiamo
    prova("...senza promettere un arrivo che non possiamo sapere",
          False, "ti aspetta" in testo or "è arrivato al punto" in testo)
    prova("...e ai moderatori non si scrive mai", [], ghiaccio)
    # i contatori sono SUOI: se leggesse quelli della sorella,
    # l'ordine che passa di la' (il venditore deposita dopo la
    # segnalazione) arriverebbe al tetto senza aver mai sentito
    # «vai a ritirare»
    o = riga(o_att)
    prova("il contatore e' il SUO", (1, 0, 0),
          (o["solleciti_diretti"], o["solleciti_punto"],
           o["solleciti_busta"]))
    # il non dichiarato resta della sorella, e il depositato di
    # nessuno dei due
    o_no = ordine_al_punto(a6)
    spedisci(o_no)
    tocca(o_no, spedito_il=ora - 5 * G)
    detto, _ = giro_diretti()
    prova("il NON dichiarato non entra in questo giro", [], detto)
    # LO SHIPPED STORICO con `spedito_il=0`: senza la guardia l'ancora
    # varrebbe zero e al primo giro partirebbe una raffica su tutta
    # quella popolazione. E' l'unico caso in cui quella riga morde —
    # col timbro valorizzato la mutazione che la toglie sopravvive.
    tocca(o_no, busta_diretta_il=ora - 5 * G, spedito_il=0)
    detto, _ = giro_diretti()
    prova("...e lo shipped storico senza data non riceve la raffica",
          [], detto)
    tocca(o_no, busta_diretta_il=0, spedito_il=ora - 5 * G)
    come(222)
    chiama(SRV.deposita_busta_ritiro, o_att, None,
           corpo={"nome": "Lia Neri", "codice": "PIN 1122"})
    tocca(o_att, sollecito_diretto_il=0, solleciti_diretti=0)
    detto, _ = giro_diretti()
    prova("...e col codice depositato non squilla piu'", [], detto)
    # LA CINTURA VUOLE UNO STATO CHE IL DEPOSITO NON PRODUCE, ed e' la
    # ragione per cui il caso qui sopra non basta: quel gesto AZZERA
    # la dichiarazione nello stesso UPDATE (l'annulla naturale), quindi
    # a escludere la riga e' gia' il primo gate e `busta_il=0` non
    # morde. Si rimette la dichiarazione a mano — lo stato impossibile
    # per costruzione, che e' precisamente cio' da cui una cintura
    # difende — o la mutazione che la toglie resta viva (l'ha detto la
    # tortura del banco, non la rilettura).
    tocca(o_att, busta_diretta_il=ora - 2 * G)
    detto, _ = giro_diretti()
    prova("...e con TUTTI E DUE la cintura chiude lo stesso", [], detto)
    tocca(o_att, busta_diretta_il=0)

    # LA VIA D'USCITA: il bottone a comando, che fino a ieri il gate
    # `busta_diretta_il=0` teneva fuori — e li' non c'era niente da
    # dire, perche' il codice era andato al compratore. Adesso c'e',
    # ma con un altro mestiere: RIFERISCE un fatto che solo chi compra
    # puo' sapere, e il testo non accusa mai il venditore di aver
    # sbagliato l'indirizzo.
    print("\n[8b] la via d'uscita a comando")
    o_out = ordine_al_punto(a1)
    spedisci(o_out, diretta=True)
    tocca(o_out, spedito_il=ora - 2 * G)
    DETTO.clear()
    come(111)
    r = chiama(SRV.sollecita_venditore, o_out)
    prova("il compratore puo' segnalare che non e' arrivato niente",
          True, bool(r.get("ok")))
    msg = " || ".join(t for chi, t in DETTO if chi == 222)
    prova("...e al venditore arriva il FATTO", True,
          "non ha ricevuto il codice di ritiro" in msg)
    prova("...con la via d'uscita dentro", True,
          "deposita il nome" in msg)
    prova("...e senza accusarlo di aver sbagliato l'indirizzo", False,
          "sbagliato" in msg)
    # il gesto passa dai contatori della busta e non da quelli
    # dell'automatico: bussare a mano non sposta il 🧊 di un minuto
    o = riga(o_out)
    prova("il gesto usa i contatori della busta", (1, 0),
          (o["solleciti_manuali_busta"], o["solleciti_diretti"]))
    come(111)
    cod, _ = rifiuto(SRV.sollecita_venditore, o_out)
    prova("...e la pausa di famiglia regge", 400, cod)

    print("\n" + "=" * 60)
    print(f"  {PASSATE} verdi, {FALLITE} rosse")
    print("=" * 60)
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
