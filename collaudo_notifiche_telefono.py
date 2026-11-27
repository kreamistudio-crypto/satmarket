# -*- coding: utf-8 -*-
"""
LE NOTIFICHE SUL TELEFONO, SUL SERVER VERO (14 nov 2026, cantiere
web-push, Andrea: «si puo' fare: notifiche web app» — l'app di Zapstore,
il sito sulla Home, il browser del PC).

`prove.py` (prove_notifiche_telefono) fa girare i pezzi uno per uno: la
cifratura col vettore dell'RFC, il timbro, la lista dei servizi, il
carico. Qui gira il SERVER VERO su un database usa-e-getta, con un
TELEFONO DI CARTONE che ha le sue chiavi vere, e si guarda che:

  1. IL TIMBRO nasce da solo nel database al primo /api/me, UNA volta, e
     /api/me ne da' la chiave pubblica (mai la privata);
  2. ISCRIVERSI: un servizio vero e due chiavi buone entrano; un
     indirizzo fuori lista o chiavi storte no (400); a leva spenta 503 e
     /api/me dice «niente tasto»;
  3. LA NOTIFICA VERA: la `notifica()` del server, quella che chiamano
     ordini e scambi, in collaudo locale simula e non spedisce; fuori
     dal collaudo spedisce al servizio (di cartone) un corpo che SOLO il
     telefono decifra, col titolo e il percorso giusti, timbrato con la
     chiave che /api/me ha dato; un 410 toglie l'iscrizione;
  4. LA PROVA DAL CASSETTO: senza telefoni 409, poi parte, e la seconda
     subito dopo e' 429;
  5. TOGLIERSI: un altro account non toglie il telefono di nessuno;
  6. FUSIONE E CANCELLAZIONE: i telefoni passano alla meta' viva, e con
     l'account cancellato se ne vanno;
  7. IL PANNELLO: la leva e' nel censimento, e si cambia da li'.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, e non esce niente: il
servizio push e' un cliente httpx di cartone che mette i corpi in una
lista.

USO:  python collaudo_notifiche_telefono.py
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
import time
import types

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
RIGHE = []        # quel che il server ha stampato
SPEDITI = []      # (url, intestazioni, corpo) al servizio push di cartone
TG, NOSTR, ALTRO = 111, -601, 222


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def avvio():
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-push-")
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
    cfg.URL_PUBBLICO = "https://barattolo.store"
    cfg.DB = os.path.join(tmp, "usa-e-getta.db")
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    def stampa(*a, **k):
        RIGHE.append(" ".join(str(x) for x in a))
        print(*a, **k)
    server.print = stampa

    async def telegram_finto(tg_id, testo, bottone=None):
        return "telegram ok (cartone)"
    server._manda_telegram = telegram_finto

    async def dm_finto(*a, **k):
        return None
    server._dm_nostr_con_ripiego = dm_finto
    return tmp


class _Risp:
    def __init__(self, codice):
        self.status_code, self.text = codice, ""


class _ServizioDiCartone:
    """Il servizio push: mette il corpo in SPEDITI e risponde 201, o 410
    per gli indirizzi che finiscono con «morto»."""

    def __init__(self, *a, **k):
        self.k = k

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, content=None, headers=None):
        SPEDITI.append((url, headers, content))
        return _Risp(410 if url.endswith("morto") else 201)


class _Telefono:
    """Un telefono di cartone con le chiavi VERE: quelle che il browser
    genera all'iscrizione, e con cui si decifra cio' che arriva."""

    def __init__(self, nome):
        self.priv = ec.generate_private_key(ec.SECP256R1())
        self.pub = self.priv.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        self.auth = os.urandom(16)
        self.endpoint = f"https://fcm.googleapis.com/fcm/send/{nome}"

    def iscrizione(self):
        return {"endpoint": self.endpoint, "p256dh": b64e(self.pub),
                "auth": b64e(self.auth)}

    def decifra(self, c):
        sale, idlen = c[:16], c[20]
        as_pub = c[21:21 + idlen]
        com = self.priv.exchange(ec.ECDH(), ec.EllipticCurvePublicKey
                                 .from_encoded_point(ec.SECP256R1(), as_pub))

        def hk(s, k, i, n):
            return HKDF(hashes.SHA256(), n, s, i).derive(k)
        ikm = hk(self.auth, com, b"WebPush: info\x00" + self.pub + as_pub, 32)
        testo = AESGCM(hk(sale, ikm, b"Content-Encoding: aes128gcm\x00", 16)).decrypt(
            hk(sale, ikm, b"Content-Encoding: nonce\x00", 12), c[21 + idlen:], None)
        return json.loads(testo.rstrip(b"\x02"))


class _Richiesta:
    def __init__(self, dati):
        self.dati = dati

    async def json(self):
        return self.dati


def come(tg_id):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": False}


async def lascia_finire():
    """I lavori in sottofondo del server (il push, l'avviso in app)
    finiscono prima che il loop si chiuda."""
    for _ in range(300):
        altri = [t for t in asyncio.all_tasks()
                 if t is not asyncio.current_task() and not t.done()]
        if not altri:
            return
        await asyncio.sleep(0.02)


def rifiuto(coro):
    """Il codice HTTP con cui la rotta rifiuta, o 200."""
    try:
        asyncio.run(coro)
        return 200
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)


def telefoni_di(tg):
    con = SRV.db()
    r = [x[0] for x in con.execute(
        "SELECT endpoint FROM push_iscrizioni WHERE tg_id=? ORDER BY id", (tg,))]
    con.close()
    return r


def main():
    print("=" * 58)
    print("  LE NOTIFICHE SUL TELEFONO — il giro vero")
    print("=" * 58)
    tmp = avvio()
    con = SRV.db()
    adesso = int(time.time())
    for tg, nome in ((TG, "Telegrammo"), (ALTRO, "Altro")):
        con.execute("INSERT INTO utenti(tg_id, nome, registrato) VALUES(?,?,?)",
                    (tg, nome, adesso))
    # chi entra da Nostr ha la sua chiave d'accesso (la fusione la vuole)
    con.execute("INSERT INTO utenti(tg_id, nome, registrato, npub_accesso) "
                "VALUES(?,?,?,?)", (NOSTR, "Nostrino", adesso,
                                    SRV.hex_to_npub("a7" * 32)))
    con.commit()
    con.close()

    async def profilo():
        p = await SRV.mio_profilo()
        await lascia_finire()
        return p

    # ---- 1) IL TIMBRO --------------------------------------------------
    print("\n[1) il timbro nasce da solo, una volta]")
    come(NOSTR)
    p1 = asyncio.run(profilo())
    SRV._PUSH_TIMBRO.update(chiave=None, pubblica="")   # come un riavvio
    p2 = asyncio.run(profilo())
    con = SRV.db()
    righe_timbro = con.execute("SELECT COUNT(*) FROM push_timbro").fetchone()[0]
    con.close()
    chiave = (p1.get("web_push") or {}).get("chiave", "")
    prova("/api/me: tasto acceso e la chiave pubblica (65 byte, 0x04); il "
          "timbro e' UNA riga e dopo un riavvio e' lo stesso",
          [True, 65, 4, 1, chiave],
          [(p1.get("web_push") or {}).get("attivo"), len(b64d(chiave)) if chiave else 0,
           b64d(chiave)[0] if chiave else 0, righe_timbro,
           (p2.get("web_push") or {}).get("chiave")])
    prova("la privata non esce mai da /api/me; chi non le ha mai accese "
          "non le ha «volute» (27 nov 2026, push-rientro)", [True, False],
          [set((p1.get("web_push") or {})) == {"attivo", "chiave", "voluto"},
           (p1.get("web_push") or {}).get("voluto")])
    prova("il journal dice che il timbro e' nato, una volta", 1,
          sum("timbro VAPID creato" in r for r in RIGHE))

    # ---- 2) ISCRIVERSI -------------------------------------------------
    print("\n[2) iscriversi: servizio vero e chiavi buone, il resto no]")
    tel = _Telefono("nostrino-1")
    morto = _Telefono("nostrino-morto")
    r = asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione())))
    asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(morto.iscrizione())))
    prova("un telefono vero entra (e poi il secondo)", [{"ok": True, "telefoni": 1},
          [tel.endpoint, morto.endpoint]], [r, telefoni_di(NOSTR)])
    prova("un indirizzo fuori lista, chiavi storte: 400; niente scritto",
          [400, 400, 400, 2],
          [rifiuto(SRV.push_iscrivi_rotta(_Richiesta(
               dict(tel.iscrizione(), endpoint="https://127.0.0.1/x")))),
           rifiuto(SRV.push_iscrivi_rotta(_Richiesta(
               dict(tel.iscrizione(), endpoint="http://fcm.googleapis.com/x")))),
           rifiuto(SRV.push_iscrivi_rotta(_Richiesta(
               dict(tel.iscrizione(), p256dh=b64e(b"\x04" + b"\0" * 64))))),
           len(telefoni_di(NOSTR))])
    SRV.WEB_PUSH_ATTIVO = False
    prova("a leva spenta: iscriversi 503, la prova 503, /api/me senza tasto",
          [503, 503, {"attivo": False}],
          [rifiuto(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione()))),
           rifiuto(SRV.push_prova_rotta()), asyncio.run(profilo()).get("web_push")])
    SRV.WEB_PUSH_ATTIVO = True

    # ---- 3) LA NOTIFICA VERA ------------------------------------------
    print("\n[3) la notifica() del server arriva al telefono]")
    vero_httpx = SRV.httpx
    SRV.httpx = types.SimpleNamespace(AsyncClient=_ServizioDiCartone)
    try:
        async def avvisa():
            await SRV.notifica(NOSTR, "📦 <b>Ordine #7 spedito</b>\nIl venditore "
                               "ha spedito &amp; ti avvisa.",
                               ("📦 Apri l'ordine", "https://barattolo.store/?ordine=7"))
            await lascia_finire()
        asyncio.run(avvisa())
        prova("in collaudo locale si simula e non parte niente",
              [[], True], [SPEDITI[:], any(r.startswith("📲 [push simulato per utente -601")
                                            for r in RIGHE)])
        SRV.MODALITA_COLLAUDO = False
        asyncio.run(avvisa())
        al_vivo = [s for s in SPEDITI if s[0] == tel.endpoint]
        url, h, corpo = al_vivo[0] if al_vivo else ("", {}, b"")
        letto = tel.decifra(corpo) if corpo else None
        t, k = h.get("Authorization", "vapid t=a.b.c, k=").split("t=", 1)[1].split(", k=")
        testa, corpo_jwt, firma = t.split(".")
        rs = b64d(firma)
        try:
            ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), b64d(k)).verify(
                encode_dss_signature(int.from_bytes(rs[:32], "big"),
                                     int.from_bytes(rs[32:], "big")),
                f"{testa}.{corpo_jwt}".encode(), ec.ECDSA(hashes.SHA256()))
            firmato = True
        except Exception:
            firmato = False
        prova("fuori dal collaudo: al telefono un corpo che SOLO lui decifra, "
              "titolo e testo spogli, il tocco sull'ordine DI QUELL'ACCOUNT "
              "(`conto`, 19 nov 2026: la pagina passa a lui da sola)",
              {"titolo": "📦 Ordine #7 spedito",
               "testo": "Il venditore ha spedito & ti avvisa.",
               "url": "/?ordine=7&conto=-601"},
              letto)
        prova("...timbrato con la chiave che /api/me ha dato, firma valida, "
              "per l'origine del servizio", [chiave, True, "https://fcm.googleapis.com",
                                             "https://barattolo.store"],
              [k, firmato, json.loads(b64d(corpo_jwt))["aud"],
               json.loads(b64d(corpo_jwt))["sub"]])
        prova("il 410 del servizio toglie l'iscrizione morta, il vivo resta",
              [tel.endpoint], telefoni_di(NOSTR))

        # ---- 4) LA PROVA DAL CASSETTO -----------------------------------
        print("\n[4) «Mandami una notifica di prova»]")
        come(ALTRO)
        prova("senza telefoni: 409", 409, rifiuto(SRV.push_prova_rotta()))
        come(NOSTR)
        del SPEDITI[:]
        r = asyncio.run(SRV.push_prova_rotta())
        prova("parte, e arriva al telefono", ["push: 1 consegnati",
                                              "🫙 Le notifiche funzionano"],
              [r.get("esito"), tel.decifra(SPEDITI[0][2])["titolo"] if SPEDITI else None])
        prova("la seconda subito dopo: 429", 429, rifiuto(SRV.push_prova_rotta()))
    finally:
        SRV.httpx = vero_httpx
        SRV.MODALITA_COLLAUDO = True

    # ---- 4b) DI CHI E' IL TELEFONO (19 nov 2026, cantiere push-attive) ----
    print("\n[4b) la riga del Profilo: il telefono suona per me?]")
    stato = lambda e: asyncio.run(SRV.push_stato_rotta(_Richiesta({"endpoint": e})))
    come(NOSTR)
    suo = stato(tel.endpoint)
    come(ALTRO)
    d_altro = stato(tel.endpoint)
    prova("chi l'ha iscritto: mio; l'altro account aperto sullo stesso "
          "telefono: non mio (prima la riga diceva «Attive» a tutti e due); "
          "un indirizzo sconosciuto: non mio; e la domanda non scrive niente",
          [{"ok": True, "mio": True, "libero": False},
           {"ok": True, "mio": False, "libero": False},
           {"ok": True, "mio": False, "libero": True}, [tel.endpoint]],
          [suo, d_altro, stato("https://fcm.googleapis.com/fcm/send/nessuno"),
           telefoni_di(NOSTR)])
    asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione())))
    prova("«Attiva qui» dall'altro account: il telefono passa a lui, e per "
          "il primo non e' piu' suo (un account alla volta)",
          [{"ok": True, "mio": True, "libero": False}, []],
          [stato(tel.endpoint), telefoni_di(NOSTR)])
    come(NOSTR)
    asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione())))

    # ---- 5) TOGLIERSI ----------------------------------------------------
    print("\n[5) togliersi: solo il proprio telefono]")
    come(ALTRO)
    prova("un altro account non toglie niente", [{"ok": True, "tolti": 0}, [tel.endpoint]],
          [asyncio.run(SRV.push_togli_rotta(_Richiesta({"endpoint": tel.endpoint}))),
           telefoni_di(NOSTR)])
    come(NOSTR)
    SRV.WEB_PUSH_ATTIVO = False
    prova("il proprio si', anche a leva spenta", [{"ok": True, "tolti": 1}, []],
          [asyncio.run(SRV.push_togli_rotta(_Richiesta({"endpoint": tel.endpoint}))),
           telefoni_di(NOSTR)])
    SRV.WEB_PUSH_ATTIVO = True

    # ---- 5b) AL RIENTRO TORNANO DA SOLE (27 nov 2026, push-rientro) -------
    print("\n[5b) il ricordo «le aveva accese»: chi esce lo tiene, chi spegne no]")
    voluto = lambda: (asyncio.run(profilo()).get("web_push") or {}).get("voluto")
    v_uscito = voluto()
    stato_dopo = stato(tel.endpoint)
    asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione())))
    come(ALTRO)
    altro_spegne = asyncio.run(SRV.push_togli_rotta(
        _Richiesta({"endpoint": tel.endpoint, "spento": True})))
    v_altro = voluto()
    come(NOSTR)
    v_dopo_altro = voluto()
    spento_testo = asyncio.run(SRV.push_togli_rotta(
        _Richiesta({"endpoint": tel.endpoint, "spento": "si"})))
    v_testo = voluto()
    asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione())))
    asyncio.run(SRV.push_togli_rotta(_Richiesta({"endpoint": tel.endpoint, "spento": True})))
    prova("uscito (iscrizione tolta senza «spento»): /api/me dice ancora "
          "«voluto» e l'indirizzo e' libero, cosi' il browser col permesso le "
          "rifa' al rientro; un altro account che spegne tocca solo il suo "
          "ricordo; «spento» vale solo se e' proprio true; il bottone le "
          "spegne davvero e il ricordo se ne va",
          [True, {"ok": True, "mio": False, "libero": True},
           {"ok": True, "tolti": 0}, False, True, {"ok": True, "tolti": 1},
           True, False, []],
          [v_uscito, stato_dopo, altro_spegne, v_altro, v_dopo_altro,
           spento_testo, v_testo, voluto(), telefoni_di(NOSTR)])

    # ---- 6) FUSIONE E CANCELLAZIONE ---------------------------------------
    print("\n[6) fusione e cancellazione]")
    asyncio.run(SRV.push_iscrivi_rotta(_Richiesta(tel.iscrizione())))
    esito = SRV.esegui_fusione(TG, NOSTR)
    voluti = lambda: [x[0] for x in SRV.db().execute(
        "SELECT tg_id FROM push_voluti ORDER BY tg_id")]
    prova("nella fusione il telefono passa alla meta' viva, e con lui il "
          "ricordo «le aveva accese»", [True, [tel.endpoint], [], [TG]],
          [not isinstance(esito, str), telefoni_di(TG), telefoni_di(NOSTR),
           [t for t in voluti() if t in (TG, NOSTR)]])
    SRV.esegui_cancellazione(TG)
    prova("con l'account cancellato i telefoni se ne vanno, e il ricordo pure",
          [[], False], [telefoni_di(TG), TG in voluti()])

    # ---- 7) IL PANNELLO -------------------------------------------------
    print("\n[7) la leva nel pannello]")
    voci = [v for g in SRV._leve_stato() for v in g["voci"]
            if v.get("chiave") == "WEB_PUSH_ATTIVO"]
    prova("la leva e' nel censimento, accesa, e si cambia da li' (si'/no)",
          [1, True, "si_no"],
          [len(voci), voci[0]["valore"] if voci else None,
           (SRV._leva_generica(voci[0]) or {}).get("tipo") if voci else None])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
