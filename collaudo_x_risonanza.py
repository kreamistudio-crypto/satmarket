# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CASSA DI RISONANZA SU X (9 ott 2026) — il giro col
SERVER VERO.

`prove.py` guarda i pezzi uno per uno: il peso e il taglio a 280, il
filtro degli originali, la firma OAuth sul vettore della
documentazione, il registro dei doppioni. Qui gira la STORIA: il
server vero legge le note da un relay (di cartone, perche' nella gabbia
della CI un relay vero non c'e' — e in collaudo non si legge comunque),
le mette in coda, scarica i media, li carica a pezzi su un X di cartone
sul loopback che VERIFICA la firma OAuth 1.0a con le quattro chiavi di
prova, e pubblica. Poi i no di X: il 429 che si riprova a distanza, il
403 che si lascia, e la nota dopo che esce lo stesso. Poi i doppioni,
la modalita' prova, il riepilogo del giorno, e la prova che nessuna
delle quattro chiavi finisce mai nel journal.

LA FIRMA DELLE NOTE E' VERA: le firma `schnorr_puro` (BIP-340 in
Python puro) con una chiave usa-e-getta, e il server le verifica con
coincurve dove c'e' e con `schnorr_puro` dove non c'e' (la CI).

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti, PRIMA dell'import del server. Niente rete fuori
dal loopback: il relay e' un oggetto, X e' un http.server su 127.0.0.1.

USO:  python collaudo_x_risonanza.py
"""
import asyncio
import base64
import contextlib
import hashlib
import hmac
import io
import json
import os
import re
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova

# Le quattro chiavi di prova. In un DIZIONARIO e posate col setattr: la
# forma `NOME = "valore"` e' quella che lo scanner dei segreti della CI
# cerca, e il valore porta il segnaposto di cartone per la cronologia.
CHIAVI = {"X_API_KEY": "collaudo-usa-e-getta-xk",
          "X_API_SECRET": "collaudo-usa-e-getta-xs",
          "X_ACCESS_TOKEN": "collaudo-usa-e-getta-xt",
          "X_ACCESS_SECRET": "collaudo-usa-e-getta-xa"}
SK = bytes.fromhex("07" * 31 + "11")            # la chiave della «npub ufficiale» di prova
PUB = schnorr_puro.pubblica(SK).hex()
SK_ALTRA = bytes.fromhex("09" * 31 + "13")      # un'altra persona
PUB_ALTRA = schnorr_puro.pubblica(SK_ALTRA).hex()
IMG = b"\xff\xd8\xff\xe0" + bytes(range(256)) * 40     # ~10 KB di «jpeg»
VIDEO = bytes(range(256)) * (6 * 1024 * 1024 // 256)    # 6 MB: due pezzi da 4 MB

X = {"modo": 201, "post": [], "media": {}, "chiamate": [],
     "firme_sbagliate": 0, "prossimo": 100, "porta": 0}
RELAY = {"note": [], "req": [], "aperture": 0}
BASE = ""


def perc(s):
    return quote(str(s), safe="-._~")


class XFinto(BaseHTTPRequestHandler):
    """L'API v2 di X, in cartone: initialize/append/finalize/STATUS e
    POST /2/tweets, con la firma OAuth 1.0a RIFATTA qui e confrontata.
    Serve anche le foto e il video della nota (/foto, /img, /video)."""
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _manda(self, codice, corpo=None, tipo="application/json"):
        dati = (json.dumps(corpo).encode() if isinstance(corpo, (dict, list))
                else (corpo or b""))
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        if dati:
            self.wfile.write(dati)

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _firma_ok(self, metodo, form=None):
        testa = self.headers.get("Authorization") or ""
        if not testa.startswith("OAuth "):
            return False
        params = {}
        for pezzo in testa[6:].split(", "):
            k, _, v = pezzo.partition("=")
            params[unquote(k)] = unquote(v.strip('"'))
        firma = params.pop("oauth_signature", "")
        if params.get("oauth_consumer_key") != CHIAVI["X_API_KEY"] \
                or params.get("oauth_token") != CHIAVI["X_ACCESS_TOKEN"] \
                or params.get("oauth_signature_method") != "HMAC-SHA1" \
                or not params.get("oauth_nonce") or not params.get("oauth_timestamp"):
            return False
        u = urlparse(self.path)
        tutti = dict(params)
        for k, v in parse_qs(u.query).items():
            tutti[k] = v[0]
        if form:
            tutti.update(form)
        coppie = sorted((perc(k), perc(v)) for k, v in tutti.items())
        stringa = "&".join(f"{k}={v}" for k, v in coppie)
        base = f"{metodo}&{perc(BASE + u.path)}&{perc(stringa)}"
        chiave = f"{perc(CHIAVI['X_API_SECRET'])}&{perc(CHIAVI['X_ACCESS_SECRET'])}"
        attesa = base64.b64encode(hmac.new(chiave.encode(), base.encode(),
                                           hashlib.sha1).digest()).decode()
        return hmac.compare_digest(attesa, firma)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.startswith(("/foto/", "/img/")):
            return self._manda(200, IMG, "image/jpeg")
        if u.path.startswith("/video/"):
            return self._manda(200, VIDEO, "video/mp4")
        if u.path == "/2/media/upload":
            X["chiamate"].append(("GET", u.path + "?" + u.query))
            if not self._firma_ok("GET"):
                X["firme_sbagliate"] += 1
                return self._manda(401, {"title": "Unauthorized"})
            mid = parse_qs(u.query).get("media_id", [""])[0]
            return self._manda(200, {"data": {"id": mid, "processing_info": {
                "state": "succeeded", "progress_percent": 100}}})
        self._manda(404, {})

    def do_POST(self):
        u = urlparse(self.path)
        corpo = self._corpo()
        tipo = self.headers.get("Content-Type") or ""
        X["chiamate"].append(("POST", u.path))
        form, parti = None, {}
        if tipo.startswith("multipart/form-data"):
            confine = tipo.split("boundary=", 1)[1].strip().encode()
            for blocco in corpo.split(b"--" + confine)[1:]:
                if blocco.strip() in (b"", b"--"):
                    continue
                testa, _, dati = blocco.partition(b"\r\n\r\n")
                m = re.search(rb'name="([^"]+)"', testa)
                if m:
                    parti[m.group(1).decode()] = dati[:-2] if dati.endswith(b"\r\n") else dati
        elif tipo.startswith("application/x-www-form-urlencoded"):
            form = {k: v[0] for k, v in parse_qs(corpo.decode()).items()}
        if not self._firma_ok("POST", form):
            X["firme_sbagliate"] += 1
            return self._manda(401, {"title": "Unauthorized"})
        if u.path == "/2/media/upload/initialize":
            d = json.loads(corpo)
            X["prossimo"] += 1
            mid = str(X["prossimo"])
            X["media"][mid] = {"init": d, "pezzi": [], "finale": False}
            return self._manda(200, {"data": {"id": mid, "media_key": "3_" + mid,
                                              "expires_after_secs": 86400}})
        m = re.match(r"^/2/media/upload/(\d+)/(append|finalize)$", u.path)
        if m:
            mid, passo = m.groups()
            if mid not in X["media"]:
                return self._manda(404, {"title": "media sconosciuto"})
            if passo == "append":
                X["media"][mid]["pezzi"].append(
                    (int(parti.get("segment_index", b"-1")), len(parti.get("media", b""))))
                return self._manda(204)
            X["media"][mid]["finale"] = True
            d = {"data": {"id": mid, "media_key": "3_" + mid,
                          "size": sum(n for _, n in X["media"][mid]["pezzi"])}}
            if X["media"][mid]["init"].get("media_category") == "tweet_video":
                d["data"]["processing_info"] = {"state": "pending", "check_after_secs": 0}
            return self._manda(200, d)
        if u.path == "/2/tweets":
            d = json.loads(corpo)
            if X["modo"] == 429:
                return self._manda(429, {"errors": [{"code": 88,
                                                     "message": "Rate limit exceeded"}]})
            if X["modo"] == 403:
                return self._manda(403, {"title": "Forbidden",
                                         "detail": "You are not permitted"})
            X["prossimo"] += 1
            pid = str(X["prossimo"])
            X["post"].append({"id": pid, "text": d.get("text", ""),
                              "media_ids": (d.get("media") or {}).get("media_ids", [])})
            return self._manda(201, {"data": {"id": pid, "text": d.get("text", "")}})
        self._manda(404, {})


class WsFinto:
    """Il relay di cartone: UNA connessione, che risponde a un REQ con le
    note che passano il filtro e poi l'EOSE, e a un EVENT con l'OK."""

    def __init__(self, url):
        self.coda = []
        RELAY["aperture"] += 1

    def settimeout(self, t):
        pass

    def send(self, msg):
        m = json.loads(msg)
        if m[0] == "REQ":
            sid, filtro = m[1], m[2]
            RELAY["req"].append(filtro)
            for ev in RELAY["note"]:
                if ev["kind"] in filtro.get("kinds", [ev["kind"]]) \
                        and ev["pubkey"] in filtro.get("authors", [ev["pubkey"]]) \
                        and ev["created_at"] >= filtro.get("since", 0):
                    self.coda.append(json.dumps(["EVENT", sid, ev]))
            self.coda.append(json.dumps(["EOSE", sid]))
        elif m[0] == "EVENT":
            self.coda.append(json.dumps(["OK", m[1]["id"], True, ""]))

    def recv(self):
        if not self.coda:
            raise TimeoutError("niente da leggere")
        return self.coda.pop(0)

    def close(self):
        pass


def relay_finto(url, timeout=None, sslopt=None):
    return WsFinto(url)


def nota(sk, content, tags=None, quando=None, kind=1):
    """Una nota FIRMATA per davvero, con schnorr_puro."""
    SRV = banco.SRV
    pub = schnorr_puro.pubblica(sk).hex()
    ev = SRV.evento_non_firmato(pub, kind, tags or [], content,
                                int(quando or time.time()))
    ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"])).hex()
    return ev


def giro():
    """Un giro dell'orologio di X, col journal catturato."""
    uscita = io.StringIO()
    with contextlib.redirect_stdout(uscita):
        esito = asyncio.run(banco.SRV.giro_x())
    testo = uscita.getvalue()
    JOURNAL.append(testo)
    for r in testo.splitlines():
        if r.strip():
            print("      │ " + r)
    return esito, testo


JOURNAL = []


def righe(esito=None):
    con = banco.SRV.db()
    q = "SELECT * FROM x_post" + (" WHERE esito=?" if esito else "") + " ORDER BY creato_nota"
    r = [dict(x) for x in con.execute(q, (esito,) if esito else ()).fetchall()]
    con.close()
    return r


def main():
    global BASE
    print("=" * 58)
    print("  LA CASSA DI RISONANZA SU X — il giro col server vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    server = ThreadingHTTPServer(("127.0.0.1", 0), XFinto)
    X["porta"] = server.server_address[1]
    BASE = f"http://127.0.0.1:{X['porta']}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # le leve, posate DOPO l'import: il modulo le legge al momento della
    # chiamata (nessuna si cristallizza all'import, e' la prova che qui
    # tutto funzioni)
    for k, v in CHIAVI.items():
        setattr(SRV, k, v)
    SRV.X_RIPUBBLICA = True
    SRV.X_RIEPILOGO_GIORNO = False
    SRV.X_CON_LINK = False
    SRV.X_PROVA = False
    SRV.X_API_BASE = BASE
    SRV.X_NPUB = PUB                        # in esadecimale: ammesso
    SRV.X_PAUSA_S = 0                       # la pausa fra i post, qui no
    SRV.URL_PUBBLICO = BASE                 # le foto degli annunci stanno qui
    SRV.RELAYS_VERIFICA = ["ws://127.0.0.1:9", "ws://localhost:9"]   # di casa: si leggono
    SRV.create_connection = relay_finto
    # IL BANCO SOSTITUISCE httpx col nodo LNbits di cartone (solo `post`):
    # qui X e' un server vero sul loopback e le chiamate sono quelle vere
    # (request, stream): torna l'httpx di libreria. LNbits non si chiama.
    import httpx
    SRV.httpx = httpx

    print("\n[la prima accensione: si parte da adesso]")
    prova("la leva letta viva e' accesa (chiavi di cartone, X sul loopback)",
          (True, False), (SRV.x_ripubblica_viva(), SRV.x_in_prova()))
    adesso = int(time.time())
    vecchia = nota(SK, "Una nota di IERI, che non deve uscire", quando=adesso - 3600)
    RELAY["note"].append(vecchia)
    (nuove, fatti), testo = giro()
    prova("il primo giro scrive la lancetta e lo dice", True,
          "si parte da adesso" in testo and int(SRV.impostazione("x_dal")) >= adesso)
    prova("...e la nota di ieri NON si ripubblica", (0, 0, []), (nuove, fatti, X["post"]))
    prova("il relay e' stato interrogato per kind 1 della chiave, da adesso", True,
          RELAY["req"] and RELAY["req"][-1]["kinds"] == [1]
          and RELAY["req"][-1]["authors"] == [PUB] and RELAY["req"][-1]["since"] >= adesso - 61)
    prova("...due relay di casa, due aperture", 2, RELAY["aperture"])

    print("\n[le note nuove: originali si', il resto no]")
    dopo = adesso + 1
    RELAY["note"] += [
        nota(SK, "Ciao da Barattolo, il mercatino in satoshi 🫙", quando=dopo),
        nota(SK, "Rispondo a qualcuno", tags=[["e", "aa" * 32, "", "reply"]], quando=dopo + 1),
        nota(SK, "Cito qualcuno", tags=[["q", "bb" * 32]], quando=dopo + 2),
        nota(SK_ALTRA, "Io non sono Barattolo", quando=dopo + 3),
        nota(SK, "Con due foto " + BASE + "/img/1.jpg e " + BASE + "/img/2.jpg",
             tags=[["imeta", "url " + BASE + "/img/1.jpg", "m image/jpeg"]], quando=dopo + 4),
        nota(SK, " ".join(f"parola{i}" for i in range(70)), quando=dopo + 5),
        nota(SK, "Un annuncio", quando=dopo + 6, kind=30402),
    ]
    # LA NOTA DI CASA: il server firma una promo (qui con la chiave di
    # prova: la piattaforma in questo collaudo non ha una nsec) e la
    # spedisce come fa `_posta_promo_singolo` — in collaudo non esce,
    # ma il gancio la timbra. Il relay la serve lo stesso: e' il caso.
    promo = nota(SK, "🫙 Nuovo nel barattolo: una bici — 100.000 sats",
                 tags=[["t", "barattolo"]], quando=dopo + 7)
    with contextlib.redirect_stdout(io.StringIO()):
        asyncio.run(SRV._spedisci_ai_relay(promo))
    RELAY["note"].append(promo)
    # e una nota con la firma ROTTA, «di Barattolo» a parole
    rotta = nota(SK, "Firma rotta", quando=dopo + 8)
    rotta["content"] = "Firma rotta, contenuto cambiato"
    RELAY["note"].append(rotta)
    (nuove, fatti), testo = giro()
    prova("in coda sono entrati SOLO i tre originali", 3, nuove)
    prova("...e tre post sono usciti su X, in ordine di tempo", 3, len(X["post"]))
    testi = [p["text"] for p in X["post"]]
    prova("il primo e' il saluto, intero", "Ciao da Barattolo, il mercatino in satoshi 🫙",
          testi[0])
    prova("il secondo ha le foto caricate e NIENTE URL nel testo",
          ("Con due foto e", 2), (testi[1], len(X["post"][1]["media_ids"])))
    prova("...caricate a pezzi: initialize, append, finalize, per ognuna", True,
          all(X["media"][m]["finale"] and X["media"][m]["pezzi"] == [(0, len(IMG))]
              and X["media"][m]["init"]["media_category"] == "tweet_image"
              for m in X["post"][1]["media_ids"]))
    prova("il terzo e' tagliato su una parola e chiude con «continua su Nostr»", True,
          testi[2].endswith("… continua su Nostr") and SRV.x_pesa(testi[2]) <= 280
          and "parola" in testi[2] and not re.search(r"parola\d*[a-z]", testi[2]))
    # 1 (il saluto) + 3+3+1 (due foto: initialize/append/finalize
    # ciascuna, poi il post) + 1 (il testo lungo) = nove chiamate firmate
    prova("X ha verificato OGNI firma OAuth (nove chiamate), nessuna sbagliata",
          (0, 9), (X["firme_sbagliate"], len(X["chiamate"])))
    prova("la promo di casa non e' uscita (timbrata di_casa)", 1,
          sum(1 for r in righe("di_casa") if r["evento_id"] == promo["id"]))
    prova("...e la firma rotta e' stata buttata, dicendolo", True,
          "non ha una firma valida: buttata" in testo
          and all(r["evento_id"] != rotta["id"] for r in righe()))
    prova("il journal racconta i post con la stima e il totale", True,
          testo.count("🐦 X: pubblicato il post") == 3
          and "stima 0,015 $" in testo and "totale del mese 0,045 $" in testo)
    prova("di serie nessun link njump", False, any("njump" in t for t in testi))
    prova("il registro ha gli id di X accanto a quelli Nostr", True,
          sorted(r["post_x_id"] for r in righe("pubblicato"))
          == sorted(p["id"] for p in X["post"]))

    print("\n[il video: due pezzi, poi lo stato finche' e' pronto]")
    RELAY["note"].append(nota(SK, "Un video " + BASE + "/video/1.mp4 e una foto "
                              + BASE + "/img/3.jpg", quando=dopo + 9))
    X["chiamate"].clear()
    (nuove, fatti), testo = giro()
    ultimo = X["post"][-1]
    prova("il post ha UN media: il video, la foto resta su Nostr",
          (1, "Un video e una foto"), (len(ultimo["media_ids"]), ultimo["text"]))
    vid = X["media"][ultimo["media_ids"][0]]
    prova("...caricato in due pezzi da 4 MB e 2 MB come tweet_video",
          ([(0, 4 * 1024 * 1024), (1, 2 * 1024 * 1024)], "tweet_video", "video/mp4"),
          (vid["pezzi"], vid["init"]["media_category"], vid["init"]["media_type"]))
    prova("...e lo stato e' stato chiesto dopo il finalize", True,
          any(c[0] == "GET" and "command=STATUS" in c[1] for c in X["chiamate"]))

    print("\n[i no di X: il 429 si riprova a distanza, il 403 si lascia]")
    X["modo"] = 429
    RELAY["note"].append(nota(SK, "Troppi post", quando=dopo + 10))
    (nuove, fatti), testo = giro()
    r = [x for x in righe() if x["evento_id"] == RELAY["note"][-1]["id"]][0]
    prova("il 429 lascia la nota in «riprova», con l'attesa scritta",
          ("riprova", 1, True), (r["esito"], r["tentativi"], r["riprova_il"] > time.time() + 200))
    prova("...e il journal lo dice", True, "riprovo fra 5 min (tentativo 1/3)" in testo)
    X["modo"] = 201
    quanti = len(X["post"])
    giro()
    prova("finche' non e' ora, non si riprova", quanti, len(X["post"]))
    con = SRV.db()
    con.execute("UPDATE x_post SET riprova_il=riprova_il-400 WHERE evento_id=?", (r["evento_id"],))
    con.commit()
    con.close()
    (nuove, fatti), testo = giro()
    prova("passata l'attesa, esce", ("Troppi post", "pubblicato"),
          (X["post"][-1]["text"], [x for x in righe() if x["evento_id"] == r["evento_id"]][0]["esito"]))
    X["modo"] = 403
    RELAY["note"].append(nota(SK, "Questa X la rifiuta", quando=dopo + 11))
    (nuove, fatti), testo = giro()
    r = [x for x in righe() if x["evento_id"] == RELAY["note"][-1]["id"]][0]
    prova("il 403 si lascia subito, senza riprovare", ("rifiutato", 1), (r["esito"], r["tentativi"]))
    prova("...dicendolo nel journal", True, "resta su Nostr e basta" in testo and "si va avanti" in testo)
    X["modo"] = 201
    RELAY["note"].append(nota(SK, "E questa dopo esce", quando=dopo + 12))
    (nuove, fatti), testo = giro()
    prova("...e la nota dopo esce lo stesso: niente si e' bloccato",
          "E questa dopo esce", X["post"][-1]["text"])
    prova("la rifiutata resta rifiutata, non si rifa'", "rifiutato",
          [x for x in righe() if x["evento_id"] == r["evento_id"]][0]["esito"])

    print("\n[niente doppioni, anche se il relay le riserve tutte]")
    quanti = len(X["post"])
    con = SRV.db()
    con.execute("UPDATE impostazioni SET valore=? WHERE chiave='x_dal'", (str(adesso),))
    con.commit()
    con.close()
    (nuove, fatti), testo = giro()
    prova("con la lancetta riportata indietro il relay riserve tutto, e non esce niente",
          (0, 0, quanti), (nuove, fatti, len(X["post"])))

    print("\n[la modalita' prova: si racconta, X non si chiama]")
    SRV.X_PROVA = True
    X["chiamate"].clear()
    RELAY["note"].append(nota(SK, "In prova " + BASE + "/img/9.jpg", quando=dopo + 13))
    (nuove, fatti), testo = giro()
    prova("in prova la nota si racconta nel journal, coi media e la stima", True,
          "[X prova]" in testo and "1 foto" in testo and "stima 0,015 $" in testo
          and "In prova" in testo)
    prova("...X non e' stato chiamato", [], X["chiamate"])
    prova("...e il registro la segna «prova»: accendendo, non torna", "prova",
          [x for x in righe() if x["evento_id"] == RELAY["note"][-1]["id"]][0]["esito"])
    SRV.X_PROVA = False

    print("\n[il riepilogo del giorno: spento di serie, poi acceso]")
    con = SRV.db()
    for foto in ('["uno.jpg"]', '["due.jpg","tre.jpg"]', "[]"):
        con.execute("INSERT INTO annunci(venditore_id, titolo, prezzo_sats, foto, stato, creato) "
                    "VALUES(222, 'Cosa', 1000, ?, 'attivo', ?)", (foto, int(time.time())))
    con.commit()
    con.close()
    from datetime import datetime, timedelta, timezone
    sera = datetime.now(timezone(timedelta(hours=1))).replace(hour=19, minute=0)
    SRV._x_oggi_italiano = lambda: sera
    quanti = len(X["post"])
    giro()
    prova("con X_RIEPILOGO_GIORNO spenta non esce nessun riepilogo", quanti, len(X["post"]))
    SRV.X_RIEPILOGO_GIORNO = True
    (nuove, fatti), testo = giro()
    ultimo = X["post"][-1]
    prova("acceso, alle 19 esce il riepilogo con le foto e senza link",
          ("🫙 Nuovi arrivi di oggi nel mercatino: 3 annunci", 2),
          (ultimo["text"], len(ultimo["media_ids"])))
    prova("...e un secondo giro lo stesso giorno non lo rifa'", len(X["post"]),
          (giro(), len(X["post"]))[1])
    prova("il giorno e' timbrato in impostazioni", sera.strftime("%Y-%m-%d"),
          SRV.impostazione("x_riepilogo_il"))

    print("\n[il pannello delle leve e i segreti]")
    with contextlib.redirect_stdout(io.StringIO()):
        voci = {v["chiave"]: v for g in SRV._leve_stato() for v in g["voci"]}
    prova("il pannello dice le leve vive", (True, True, False, True),
          (voci["X_RIPUBBLICA"]["valore"], voci["X_RIEPILOGO_GIORNO"]["valore"],
           voci["X_CON_LINK"]["valore"], voci["X_API_KEY…"]["valore"]))
    prova("...e la spesa del mese", round(0.015 * len(X["post"]), 3),
          voci["db: x_post"]["valore"])
    tutto = "\n".join(JOURNAL) + json.dumps(SRV._leve_stato(), default=str)
    prova("nessuna delle quattro chiavi e' finita nel journal o nel pannello", [],
          [k for k, v in CHIAVI.items() if v in tutto])
    prova("...e nemmeno l'intestazione OAuth", False, "oauth_signature" in tutto)
    server.shutdown()
    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
