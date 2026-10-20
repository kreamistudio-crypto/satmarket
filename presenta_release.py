"""Presenta la npub delle release al mondo Nostr. Rito una tantum.

Due gesti, entrambi firmati dalla chiave della PIATTAFORMA (che vive
solo nel config del server: la nsec non passa mai di qui):

  1. FOLLOW (kind 3): la piattaforma segue la npub dedicata alle
     release. ATTENZIONE al vetro sottile: il kind 3 e' un evento
     SOSTITUIBILE — chi lo ripubblica cancella la lista precedente.
     Percio' qui si LEGGE prima la lista esistente dai relay e si
     AGGIUNGE il follow, mai si riparte da zero (a meno che una lista
     non esista proprio, e in quel caso lo si dice forte).
  2. NOTA DI PRESENTAZIONE (kind 1): un post pubblico che dichiara
     quale chiave firma le release dell'app Android — cosi' chi apre
     il profilo su Zapstore o njump trova un legame verificabile con
     la piattaforma, non una npub muta.

Perche' serve: il popup «Trust this app?» di Zapstore resta appeso
sullo spinner se la npub del publisher non ha un profilo kind-0 sui
relay social, e senza follower il web-of-trust (Vertex) non ha nulla
da dire. Il kind-0 lo pubblica Andrea con la chiave fredda; questo
script cuce il resto: un follow da un profilo con storia e una nota
che spiega chi e' quella chiave.

Uso (sul VPS, col python dell'ambiente del servizio):
    python presenta_release.py

E' IDEMPOTENTE: se il follow c'e' gia' non ripubblica la lista, se la
nota di presentazione esiste gia' sui relay non la duplica. In
MODALITA_COLLAUDO legge davvero ma pubblica per finta (stampa).
Dipendenze: coincurve e websocket-client (gia' nell'ambiente del
servizio, sono quelle di server.py).
"""

import json
import ssl
import time
import hashlib

from websocket import create_connection

# I CERTIFICATI DEI RELAY SI VERIFICANO (20 ott 2026, cantiere
# certificati-relay, decisione di Andrea): sul nome del relay, con le CA
# del sistema, come nel server (`SSLOPT_RELAY` di server.py, col perche').
# Un certificato non valido e' un relay irraggiungibile; mai CERT_NONE.
SSLOPT_RELAY = {"cert_reqs": ssl.CERT_REQUIRED}
from coincurve import PrivateKey

from config import NOSTR_NSEC_PIATTAFORMA, MODALITA_COLLAUDO

# La npub DEDICATA alle release (la stessa del campo pubkey in
# zapstore.yaml su kreamistudio-crypto/barattolo-releases).
NPUB_RELEASE = ("npub1yjkuma9cenrzde7duj222gp44r"
                "aqa88uj352z0akrtw0mvvfrhhsx8g68u")

# Gli stessi 4 relay di server.py (RELAYS_VERIFICA): dentro ci sono
# damus, primal e nos.lol — esattamente i relay "social" da cui
# Zapstore precarica i profili e le liste follow.
RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://nostr.mom",
]

URL_PUBBLICO = "https://barattolo.store"
URL_RELEASES = "https://github.com/kreamistudio-crypto/barattolo-releases"

CHARSET_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_a_bytes(parola: str, prefisso: str) -> bytes:
    """Decodifica npub/nsec bech32 nei 32 byte nudi (checksum via)."""
    if not parola.startswith(prefisso + "1"):
        raise ValueError(f"deve iniziare con {prefisso}1")
    dati = [CHARSET_BECH32.find(c) for c in parola[len(prefisso) + 1:]]
    if -1 in dati:
        raise ValueError("carattere sconosciuto")
    dati = dati[:-6]                     # togli il checksum
    bits, val, out = 0, 0, []
    for d in dati:                       # da gruppi di 5 bit a byte
        val = (val << 5) | d
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((val >> bits) & 0xFF)
    if len(out) != 32:
        raise ValueError("lunghezza sbagliata")
    return bytes(out)


def firma_evento(sk, pubkey: str, kind: int, tags: list,
                 content: str) -> dict:
    """Evento NIP-01 canonico firmato Schnorr (come in server.py)."""
    creato = int(time.time())
    serial = json.dumps([0, pubkey, creato, kind, tags, content],
                        separators=(",", ":"), ensure_ascii=False)
    ev_id = hashlib.sha256(serial.encode("utf-8")).hexdigest()
    return {"id": ev_id, "pubkey": pubkey, "created_at": creato,
            "kind": kind, "tags": tags, "content": content,
            "sig": sk.sign_schnorr(bytes.fromhex(ev_id)).hex()}


def chiedi_eventi(relay: str, filtro: dict) -> list:
    """Fa una REQ a UN relay e raccoglie gli EVENT fino a EOSE."""
    eventi = []
    try:
        ws = create_connection(relay, timeout=5,
                               sslopt=SSLOPT_RELAY)
        ws.send(json.dumps(["REQ", "presenta", filtro]))
        inizio = time.time()
        while time.time() - inizio < 6:
            msg = json.loads(ws.recv())
            if msg[0] == "EVENT":
                eventi.append(msg[2])
            elif msg[0] == "EOSE":
                break
        ws.close()
    except ssl.SSLCertVerificationError as e:
        # (certificati-relay) l'unico silenzio che non si tiene: un
        # certificato rifiutato si dice
        print(f"   🔐 {relay}: certificato non valido "
              f"({getattr(e, 'verify_message', '') or e}), non lo uso")
    except Exception:
        pass                  # relay muto o irraggiungibile: pazienza
    return eventi


def spedisci(evento: dict) -> int:
    """Consegna l'evento a tutti i relay, conta gli OK. In collaudo
    non esce nulla dal computer: si stampa e basta."""
    if MODALITA_COLLAUDO:
        print(f"🟣 [nostr simulato] "
              f"{json.dumps(evento, ensure_ascii=False)[:300]}…")
        return len(RELAYS)
    ok = 0
    for relay in RELAYS:
        try:
            ws = create_connection(relay, timeout=5,
                                   sslopt=SSLOPT_RELAY)
            ws.send(json.dumps(["EVENT", evento]))
            inizio = time.time()
            while time.time() - inizio < 6:
                msg = json.loads(ws.recv())
                if msg[0] == "OK" and msg[1] == evento["id"]:
                    accettato = bool(msg[2])
                    print(f"   {'✅' if accettato else '❌'} {relay}"
                          + ("" if accettato else f" — {msg[3] if len(msg) > 3 else '?'}"))
                    ok += accettato
                    break
            ws.close()
        except Exception as e:
            print(f"   ❌ {relay} — {e}")
    return ok


def main():
    if (not NOSTR_NSEC_PIATTAFORMA
            or NOSTR_NSEC_PIATTAFORMA.startswith("INCOLLA")):
        print("⚠️ NOSTR_NSEC_PIATTAFORMA e' il segnaposto: niente da fare.")
        return

    sk = PrivateKey(_bech32_a_bytes(NOSTR_NSEC_PIATTAFORMA, "nsec"))
    pubkey = sk.public_key.format()[1:].hex()   # x-only, come server.py
    hex_release = _bech32_a_bytes(NPUB_RELEASE, "npub").hex()
    print(f"🫙 Piattaforma {pubkey[:16]}… presenta la npub release "
          f"{hex_release[:16]}…")

    # ---- 1. FOLLOW: leggi la lista esistente, aggiungi, ripubblica ----
    # Si interroga OGNI relay e vince la lista piu' recente: il kind 3
    # e' sostituibile, e ripartire da una copia vecchia (o peggio da
    # zero) butterebbe via i follow gia' fatti.
    liste = []
    for relay in RELAYS:
        liste += chiedi_eventi(relay, {"authors": [pubkey],
                                       "kinds": [3], "limit": 3})
    lista = max(liste, key=lambda e: e.get("created_at", 0)) if liste else None

    if lista:
        tags = lista.get("tags", [])
        content = lista.get("content", "")
        seguiti = {t[1] for t in tags if len(t) > 1 and t[0] == "p"}
        print(f"📖 Lista follow trovata: {len(seguiti)} seguiti "
              f"(del {time.strftime('%Y-%m-%d', time.localtime(lista['created_at']))})")
    else:
        tags, content, seguiti = [], "", set()
        print("📖 Nessuna lista follow sui relay: ne nasce una nuova "
              "(primo follow della piattaforma).")

    if hex_release in seguiti:
        print("✅ Il follow c'e' gia': lista non toccata.")
    else:
        ev3 = firma_evento(sk, pubkey, 3,
                           tags + [["p", hex_release]], content)
        ok = spedisci(ev3)
        print(f"🤝 Follow pubblicato: {ok}/{len(RELAYS)} relay OK.")
        if not ok:
            print("⚠️ Nessun relay ha accettato: riprovare piu' tardi.")
            return

    # ---- 2. NOTA DI PRESENTAZIONE (solo se non c'e' gia') ----
    esistenti = []
    for relay in RELAYS:
        esistenti += chiedi_eventi(relay, {"authors": [pubkey],
                                           "kinds": [1],
                                           "#p": [hex_release],
                                           "limit": 1})
        if esistenti:
            break
    if esistenti:
        print("✅ Nota di presentazione gia' sui relay: non si duplica.")
        return

    content = (
        "🫙⚡ Barattolo ora si installa anche da Zapstore!\n\n"
        "Le release ufficiali dell'app Android sono firmate dalla "
        f"nostra chiave dedicata nostr:{NPUB_RELEASE} — se installi "
        "da Zapstore, il publisher e' quello (e solo quello).\n\n"
        f"APK, hash e note di rilascio: {URL_RELEASES}\n"
        f"Il mercatino in sats con escrow Lightning: {URL_PUBBLICO}\n\n"
        "#barattolo #zapstore"
    )
    ev1 = firma_evento(sk, pubkey, 1,
                       [["p", hex_release],
                        ["t", "barattolo"], ["t", "zapstore"]],
                       content)
    ok = spedisci(ev1)
    print(f"📣 Nota di presentazione pubblicata: {ok}/{len(RELAYS)} relay OK.")


if __name__ == "__main__":
    main()
