# -*- coding: utf-8 -*-
"""
IMPORTA DA NOSTR — prende gli annunci di un venditore Nostr
(con il suo consenso!) e li inserisce nel database di SatMarket.

Supporta entrambi i formati:
  - kind 30402 (NIP-99, annunci "classified")
  - kind 30018 (NIP-15, prodotti dei negozi tipo Shopstr/Plebeian)

I prezzi in EUR/USD vengono convertiti in sats col cambio attuale.

COME SI USA:
  1. Compila NPUB_VENDITORE qui sotto con la npub del tuo amico
  2. (Meglio a server spento) nella cartella MERCATINO:
       python importa_nostr.py
  3. Riavvia il server: gli annunci sono in vetrina, intestati
     al "Venditore" del collaudo (che li gestisce dalla Mini App)

Da lug 2026 il server rifa' questo import DA SOLO ogni ora (vedi
l'orologio in server.py, che importa questo modulo): lo script
manuale resta per il primo giro e per le prove.

E DA LI' NON E' PIU' UN VENDITORE SOLO: col server, l'import gira su
tutti i venditori Nostr conosciuti, e gli eventi passano prima dal
VAGLIO (firma verificata davvero, lingua italiana, moderazione
completa) — vedi `importa_venditore(..., vaglio)`. Lanciato a mano,
questo file si comporta come e' sempre stato: nessun vaglio, e la
fiducia sta tutta nella npub che scrivi nel config. Va bene per un
amico, non per uno sconosciuto.

REQUISITI: pip install websocket-client   (gia' installato)
"""

import ipaddress
import json
import os
import sqlite3
import ssl
import time
import urllib.request
from urllib.parse import urlparse

from websocket import create_connection

# I CERTIFICATI DEI RELAY SI VERIFICANO (20 ott 2026, cantiere
# certificati-relay, decisione di Andrea): sul nome del relay, con le CA
# del sistema, come nel server (`SSLOPT_RELAY` di server.py, col perche').
# Un certificato non valido e' un relay irraggiungibile; mai CERT_NONE.
SSLOPT_RELAY = {"cert_reqs": ssl.CERT_REQUIRED}

# il giudice del titolo e' uno solo per tutti gli import (8 ott 2026):
# vive nel modulo dei negozi collegati, che non importa nessuno
from importa_negozio import spoglia_titolo

# ======================= CONFIGURAZIONE =======================
# La npub del venditore e l'id a cui intestare gli annunci vivono
# in config.py (insieme alle chiavi del server), cosi' questo script
# si aggiorna senza mai dover ricopiare nulla.
# Nel tuo config.py devono esserci queste due righe:
#   NPUB_VENDITORE = "npub1..."   # la chiave pubblica Nostr del venditore
#   VENDITORE_ID = 222            # 222 nel collaudo; al lancio il suo
#                                 # VERO user id Telegram (da @userinfobot)

# Il modulo deve restare IMPORTABILE dal server (import periodico):
# se config.py o le sue righe mancano, qui entrano segnaposto vuoti
# e a fermarsi (con la guida di sempre) e' solo main().
try:
    from config import NPUB_VENDITORE, VENDITORE_ID
except ImportError:
    NPUB_VENDITORE, VENDITORE_ID = "", 0

DB = "satmarket.db"
FOTO_DIR = "foto"                    # stessa cartella degli annunci normali
MAX_FOTO_BYTES = 3_000_000           # oltre ~3 MB la foto resta un URL

# I RELAY SONO UNA LEVA (ago 2026), e qui sono DUE liste per un
# motivo: `RELAY_NOSTR` sono quelli dove Barattolo scrive e legge —
# gli stessi del server, cosi' un relay aggiunto la' vale anche qui
# per costruzione — e `RELAY_NOSTR_IMPORT` quelli che si interrogano
# in PIU', i relay personali dei venditori, dove i loro annunci
# vivono e i grossi non arrivano. La' si pubblica, qui si legge e
# basta: tenerli separati e' quel che permette di aggiungere il relay
# di un venditore senza mandargli anche i nostri eventi.
# Il config e' il VALORE DI PARTENZA: senza quelle righe valgono i
# relay di serie, gli stessi del server (la lista del 15 ott 2026: il
# perche' sta accanto a quella di server.py).
# ⚠️ IL CONFIG SI LEGGE DENTRO UN try, come NPUB_VENDITORE qui sopra:
# questo modulo dev'essere lanciabile a mano su un Barattolo piu'
# VECCHIO, dove quelle righe non ci sono (la lezione di
# ricategorizza.py, che chiudeva la CI in faccia a chi lo importava).
# ⚠️ IL NOME E' LO STESSO DEL SERVER (`RELAY_DI_SERIE`) apposta: e'
# la stessa lista con lo stesso mestiere, e chi la cerca in un file
# la trova nell'altro. Sta in una costante e non ripetuta due volte
# — nel default e nel fail-safe — perche' due copie divergono al
# primo ritocco, che e' il difetto che questo cantiere toglie.
RELAY_DI_SERIE = [
    "wss://relay.primal.net",
    "wss://relay.nostr.net",
    "wss://nostr.oxtr.dev",
    "wss://nos.lol",
    "wss://relay.mostro.network",
    "wss://relay.barattolo.store",
]
try:
    from config import RELAY_NOSTR
except ImportError:
    RELAY_NOSTR = list(RELAY_DI_SERIE)
try:
    from config import RELAY_NOSTR_IMPORT
except ImportError:
    RELAY_NOSTR_IMPORT = [
        "wss://21milionidinostr.duckdns.org",   # il relay di un venditore
    ]

# I doppioni si tolgono, e non e' cosmesi: interrogare due volte lo
# stesso relay raddoppia i suoi eventi nel giro e — sull'altra strada,
# quella della pubblicazione — falserebbe il conto degli OK, che e' il
# giudice di «l'evento e' arrivato da qualche parte». L'ordine e'
# quello scritto: prima i nostri, poi gli extra.
RELAYS = list(dict.fromkeys(
    [str(r) for r in list(RELAY_NOSTR) + list(RELAY_NOSTR_IMPORT)
     if str(r).strip()]))
if not RELAYS:                    # il fail-safe del server, qui uguale
    RELAYS = list(RELAY_DI_SERIE)


def _di_casa(relay: str) -> bool:
    """PURA: il relay sta su questa macchina (loopback)? Il gemello di
    `relay_di_casa` del server, che da qui non si importa."""
    try:
        host = (urlparse(str(relay or "").strip()).hostname or "").lower()
    except ValueError:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


# IL RECINTO DELL'ISTANZA DI PROVA (20 ott 2026, vedi `fuori_dal_recinto`
# nel server): con PROVA_SOLO_IDS nel config, qualunque cosa ci sia
# scritta, l'import legge SOLO dai relay di casa, e senza il ripiego sui
# relay di serie qui sopra.
try:
    from config import PROVA_SOLO_IDS as _PROVA_SOLO_IDS
except ImportError:
    _PROVA_SOLO_IDS = []
if _PROVA_SOLO_IDS:
    RELAYS = [r for r in RELAYS if _di_casa(r)]

# Quanti eventi chiedere a ogni relay, SEPARATAMENTE per gli annunci e
# per le cancellazioni (vedi interroga: un tetto solo per tutti e due
# affamava gli annunci). Molti relay non superano comunque i 500.
LIMITE_ANNUNCI = 500
LIMITE_CANCELLAZIONI = 500

# Il tetto sui pezzi in stock: la stessa leva del server, letta anche
# qui perche' l'import scrive dritto nel database e non passa dai
# giudici dei payload. Se il config non c'e' (script lanciato altrove)
# vale il default di server.py.
try:
    from config import MAX_QUANTITA_ANNUNCIO
except ImportError:
    MAX_QUANTITA_ANNUNCIO = 999999

# ==============================================================

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"   # alfabeto bech32


def npub_to_hex(npub: str) -> str:
    """Converte la npub (bech32) nella chiave esadecimale dei relay."""
    npub = npub.strip().lower()
    if len(npub) == 64 and all(c in "0123456789abcdef" for c in npub):
        return npub                      # e' gia' in esadecimale
    if not npub.startswith("npub1"):
        raise ValueError("La chiave deve iniziare con 'npub1' (o essere hex)")
    dati = [CHARSET.find(c) for c in npub[5:]]
    if -1 in dati:
        raise ValueError("npub non valida: carattere sconosciuto")
    dati = dati[:-6]                     # togli il checksum
    bits, val, out = 0, 0, []
    for d in dati:                       # da gruppi di 5 bit a byte
        val = (val << 5) | d
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((val >> bits) & 0xFF)
    hexkey = bytes(out).hex()
    if len(hexkey) != 64:
        raise ValueError("npub non valida: lunghezza sbagliata")
    return hexkey


def _bech32_polymod(valori: list) -> int:
    """Il cuore del checksum bech32 (BIP-173) — specchio di server.py."""
    gen = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)
    chk = 1
    for v in valori:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= gen[i]
    return chk


def hex_to_npub(hexkey: str) -> str:
    """Gemella speculare di npub_to_hex (specchio di server.py): serve
    a scrivere il badge del venditore nella forma canonica npub1…"""
    dati, bits, val = [], 0, 0
    for byte in bytes.fromhex(hexkey):   # da byte a gruppi di 5 bit
        val = (val << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            dati.append((val >> bits) & 31)
    if bits:
        dati.append((val << (5 - bits)) & 31)
    # hrp "npub" espansa come vuole lo standard: bit alti, zero, bit bassi
    hrp = [ord(c) >> 5 for c in "npub"] + [0] + [ord(c) & 31 for c in "npub"]
    polymod = _bech32_polymod(hrp + dati + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return "npub1" + "".join(CHARSET[d] for d in dati + checksum)


def tag(e, nome):
    for t in e.get("tags", []):
        if t and t[0] == nome and len(t) > 1:
            return t
    return None


def interroga(relay, hexkey):
    """Chiede a UN relay gli annunci del venditore e le sue
    cancellazioni NIP-09, in DUE richieste separate.

    Separate e non una sola, perche' il "limit" vale per l'intera
    richiesta e i relay servono i piu' recenti per primi: un
    venditore che cancella molte note si spingeva fuori dalla
    finestra i propri annunci. Visto dal vivo su una chiave con 206
    cancellazioni — dei 200 eventi che tornavano, 197 erano kind 5
    e solo 3 erano annunci, su 17 che ne aveva.
    """
    eventi = []
    # Anche i kind 5 (NIP-09): le cancellazioni del venditore vanno
    # lette e rispettate, non solo i suoi annunci.
    richieste = {
        "ann": {"kinds": [30402, 30018, 30017], "authors": [hexkey],
                "limit": LIMITE_ANNUNCI},
        "canc": {"kinds": [5], "authors": [hexkey],
                 "limit": LIMITE_CANCELLAZIONI},
    }
    try:
        ws = create_connection(relay, timeout=10,
                               sslopt=SSLOPT_RELAY)
        for sub, filtro in richieste.items():
            ws.send(json.dumps(["REQ", sub, filtro]))
        # Si aspettano ENTRAMBI gli EOSE, non il primo che arriva
        # (col vecchio break sul primo si perdeva l'altra meta').
        aperte = set(richieste)
        inizio = time.time()
        while aperte and time.time() - inizio < 25:
            try:
                msg = json.loads(ws.recv())
            except Exception:
                break
            if msg[0] == "EVENT" and msg[1] in aperte:
                eventi.append(msg[2])
            # CLOSED = il relay ha chiuso lui la sottoscrizione: senza
            # questo ramo si resterebbe ad aspettare un EOSE mai dovuto
            elif msg[0] in ("EOSE", "CLOSED") and msg[1] in aperte:
                aperte.discard(msg[1])
        ws.close()
        print(f"  ✓ {relay}: {len(eventi)} eventi")
    except Exception as err:
        print(f"  ✗ {relay}: non raggiungibile ({err})")
    return eventi


def interroga_aperto(relay, limite=500):
    """La spazzata della SCOPERTA: gli annunci di CHIUNQUE, non di un
    autore solo. Serve a trovare venditori nuovi, non a importarli —
    quello che torna qui e' per forza un campione recente (i relay
    servono i piu' nuovi), e infatti a prendere davvero tutti gli
    annunci di uno e' poi interroga(), chiave per chiave."""
    eventi = []
    try:
        ws = create_connection(relay, timeout=10,
                               sslopt=SSLOPT_RELAY)
        ws.send(json.dumps(["REQ", "scoperta",
                            {"kinds": [30402, 30018], "limit": limite}]))
        inizio = time.time()
        while time.time() - inizio < 25:
            try:
                msg = json.loads(ws.recv())
            except Exception:
                break
            if msg[0] == "EVENT" and msg[1] == "scoperta":
                eventi.append(msg[2])
            elif msg[0] in ("EOSE", "CLOSED") and msg[1] == "scoperta":
                break
        ws.close()
        print(f"  ✓ {relay}: {len(eventi)} eventi in spazzata")
    except Exception as err:
        print(f"  ✗ {relay}: non raggiungibile ({err})")
    return eventi


# Il messaggio vive in un posto solo: lo dicono sia la lettura fallita
# dello script a mano, sia il cambio VUOTO che il server puo' passare —
# e sono la stessa notizia per chi legge il journal.
MSG_CAMBIO_MANCANTE = ("⚠️  Cambio BTC non disponibile: gli annunci in "
                       "EUR/USD verranno saltati.")


def cambio_btc():
    """Prezzo del Bitcoin in EUR e USD (per convertire i prezzi in sats).

    E' la strada dello SCRIPT A MANO. Quando l'import gira dal server
    non si chiama nessuno: il cambio arriva gia' pronto dalla cache del
    server (vedi `importa_venditore`), che e' la stessa fonte delle
    invoice — una verita' sola, e un giro d'import che non bussa a
    CoinGecko una volta per venditore."""
    try:
        with urllib.request.urlopen(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin&vs_currencies=eur,usd", timeout=15) as r:
            d = json.loads(r.read())["bitcoin"]
            return {"EUR": d["eur"], "USD": d["usd"]}
    except Exception as err:
        # Il PERCHE' serve: «non disponibile» puo' essere una rete giu'
        # o un 429 di CoinGecko, e sono due problemi diversi.
        print(f"{MSG_CAMBIO_MANCANTE} ({type(err).__name__}: {err})")
        return {}


def in_sats(importo: float, valuta: str, cambio: dict):
    valuta = (valuta or "").upper()
    if valuta in ("SAT", "SATS"):
        return int(importo)
    if valuta == "BTC":
        return int(importo * 100_000_000)
    if valuta in cambio:                       # EUR / USD
        return int(importo / cambio[valuta] * 100_000_000)
    return None


def scarica_foto(url: str, annuncio_id: int, indice: int, scarica=None,
                 pulisci=None):
    """Scarica una foto esterna e la salva in foto/ con lo stesso
    schema nomi degli annunci normali (a{id}_{indice}.ext).
    Ritorna il nome del file locale, o None se qualcosa va storto.

    `scarica` e' lo scaricatore che il SERVER passa (ago 2026, audit):
    ha le guardie anti-SSRF e ricontrolla ogni salto dei redirect.
    Vive li' e non qui per lo stesso motivo del `vaglio`. Senza —
    script lanciato a mano, con la npub fidata scritta nel config —
    si scarica come si e' sempre fatto.

    `pulisci` e' `spoglia_metadati` del server (set 2026, la QUARTA
    porta che il cantiere «niente GPS» aveva lasciato aperta): questa
    era l'unica strada per cui una foto arrivava sul disco senza mai
    passare da li', GPS compreso se il venditore Nostr lo portava. A
    differenza di `normalizza_foto_import` (che serve la filiera del
    CSV e forza sempre il JPEG) preserva il formato — qui l'estensione
    la decide gia' il Content-Type, e deve restare quella vera. Se non
    sa pulirla la foto NON si scrive in locale: resta l'URL, la stessa
    cintura della foto troppo grande — mai un file sporco sul disco."""
    try:
        if scarica is not None:
            esito = scarica(url)
            if not esito:
                return None
            raw, ctype = esito
            if len(raw) > MAX_FOTO_BYTES:
                print(f"    ⚠️  foto troppo grande, tengo l'URL: {url[:60]}")
                return None
        else:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Barattolo/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read(MAX_FOTO_BYTES + 1)
                if len(raw) > MAX_FOTO_BYTES:
                    print(f"    ⚠️  foto troppo grande, tengo l'URL: {url[:60]}")
                    return None
                ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
        if pulisci is not None:
            pulito = pulisci(raw)
            if pulito is None:
                print(f"    ⚠️  foto non ripulibile dai metadati, tengo "
                      f"l'URL: {url[:60]}")
                return None
            raw = pulito
        est = {"image/png": "png", "image/webp": "webp",
               "image/gif": "gif"}.get(ctype, "jpg")
        nome = f"a{annuncio_id}_{indice}.{est}"
        percorso = os.path.join(FOTO_DIR, nome)
        # Sentinella qualita' (lug 2026): se stiamo SOSTITUENDO un file
        # locale con uno molto piu' leggero, quasi sempre e' il client
        # del venditore che ha ricompresso le foto ripubblicando
        # (successo con Primal: originali nitidi rimpiazzati da
        # 1024px a bassa qualita'). I relay restano la fonte di
        # verita', quindi non blocchiamo — ma non deve MAI succedere
        # in silenzio: una riga forte nel journal.
        try:
            vecchio = os.path.getsize(percorso)
            if len(raw) < vecchio * 0.6:
                print(f"    📉 ATTENZIONE {nome}: la nuova foto pesa "
                      f"{len(raw)//1024}KB contro i {vecchio//1024}KB di "
                      f"quella locale — il client del venditore l'ha "
                      f"ricompressa? La vecchia versione viene sovrascritta.")
        except OSError:
            pass
        with open(percorso, "wb") as out:
            out.write(raw)
        # La miniatura gemella ora e' VECCHIA: via, cosi' la card
        # ripiega sul file pieno e il backfill del server ne fara'
        # una fresca al prossimo avvio (senza questo, card e
        # dettaglio mostrerebbero due foto diverse).
        try:
            os.remove(os.path.join(FOTO_DIR,
                                   nome[:nome.rfind(".")] + "_min.jpg"))
        except OSError:
            pass
        return nome
    except Exception as err:
        print(f"    ⚠️  foto non scaricata ({err}), tengo l'URL: {url[:60]}")
        return None


def localizza_foto(annuncio_id: int, foto_json: str, scarica=None,
                   pulisci=None) -> str:
    """Prende la lista foto (JSON) e scarica in locale gli URL esterni.
    Se un download fallisce, l'URL resta com'e' (meglio di niente)."""
    try:
        lista = json.loads(foto_json or "[]")
    except Exception:
        return foto_json
    nuove = []
    for i, f in enumerate(lista):
        if not isinstance(f, str):
            continue                           # non e' ne' nome ne' URL
        if not f.startswith("http"):
            # gia' un file locale: SOLO un nome nudo, mai un percorso
            # (la cintura di `foto_evento`: vedi la sua voce)
            if f and f == os.path.basename(f) and not f.startswith("."):
                nuove.append(f)
            continue
        nome = scarica_foto(f, annuncio_id, i, scarica, pulisci)
        nuove.append(nome or f)
    return json.dumps(nuove) if nuove else ""


# categoria_automatica NON esiste piu' (lug 2026): indovinare la
# categoria dal titolo sbagliava in silenzio e nessuno se ne
# accorgeva. Gli annunci importati nascono in «Altro» e a
# collocarli e' il venditore, dal form.

# --- I metadati di commercio, dai tag ---------------------------------
# Il gemello in lettura di tag_commercio (server.py). Si parlano DUE
# dialetti, perche' la spec NIP-99 non dice nulla di spedizione,
# condizione e quantita' e quindi ognuno se li e' inventati:
#
#   il nostro   ["delivery","shipping","5.00","EUR"] · ["condition",…]
#               ["delivery","pickup"] · ["delivery","digital"] · ["stock",n]
#   Shopstr     ["shipping","Added Cost","5.00","EUR"] (enum chiuso)
#               ["condition",…] · ["quantity",n] · ["pickup_location",…]
#
# Leggere anche il loro non costa quasi nulla ed e' la differenza tra
# capirsi col mercatino Nostr piu' grosso e ignorarlo.
#
# ATTENZIONE al tag "weight": NON si legge come peso. Per Shopstr e'
# una VARIANTE di prodotto col suo prezzo (["weight","500g","12.00"]),
# stessa arita' del peso di spedizione e significato opposto: chi lo
# scambia scrive un peso che non esiste. Finche' non c'e' una regola
# condivisa, meglio nessun dato che uno sbagliato.

CONDIZIONE_DA_NIP99 = {
    "new": "nuovo",
    "like-new": "come_nuovo", "likenew": "come_nuovo",
    "good": "buono",
    "fair": "accettabile",
    "poor": "da_sistemare", "for-parts": "da_sistemare",
}

# I valori dell'enum Shopstr che implicano una spedizione a pagamento
# o gratuita, e quelli che implicano il ritiro.
SHOPSTR_SPEDISCE = {"free", "added cost", "free/pickup"}
SHOPSTR_RITIRA = {"pickup", "free/pickup"}


def estrai_commercio(e):
    """Legge consegna, costo, condizione e quantita' dai tag.
    Ritorna un dict con le SOLE chiavi davvero presenti: cio' che il
    venditore non dichiara non si inventa, e a valle un campo assente
    lascia intatto quello che c'e' gia' su Barattolo."""
    fuori = {}
    spedisce = ritira = digitale = False
    costo, valuta_costo = 0.0, ""
    for t in e.get("tags", []):
        if not t or len(t) < 2:
            continue
        nome, val = t[0], (t[1] or "").strip()
        if nome == "delivery":
            modo = val.lower()
            if modo == "shipping":
                spedisce = True
                # 4 elementi = costo dichiarato; 2 = «spedisco, il
                # prezzo lo concordiamo», che NON e' gratis
                if len(t) >= 4:
                    try:
                        costo, valuta_costo = float(t[2]), (t[3] or "").upper()
                    except ValueError:
                        pass
            elif modo == "pickup":
                ritira = True
            elif modo == "digital":
                digitale = True
        elif nome == "shipping" and len(t) == 4:      # dialetto Shopstr
            modo = val.lower()
            if modo in SHOPSTR_SPEDISCE:
                spedisce = True
                if modo != "free":
                    try:
                        costo, valuta_costo = float(t[2]), (t[3] or "").upper()
                    except ValueError:
                        pass
            if modo in SHOPSTR_RITIRA:
                ritira = True
        elif nome == "pickup_location":
            ritira = True
        elif nome == "condition":
            nostra = CONDIZIONE_DA_NIP99.get(val.lower())
            if nostra:
                fuori["condizione"] = nostra
        elif nome in ("stock", "quantity"):
            if val.lower() == "unlimited":
                continue                  # non lo sappiamo rappresentare
            try:
                n = int(float(val))
            except ValueError:
                continue
            if n > 0:
                # Il tetto vale anche qui. Le guardie di Barattolo
                # stanno nel form e nel giudice del payload, ma questa
                # strada scrive DRITTA nel database e le scavalcherebbe
                # tutte: uno ["stock","999999"] su un relay non deve
                # poter fare quello che il form non lascia fare. Si
                # lima invece di scartare, come quantita_tollerante
                # del CSV: la merce c'e' davvero, e' il numero a essere
                # fuori scala.
                fuori["quantita"] = min(n, MAX_QUANTITA_ANNUNCIO)
    # LA CONSEGNA DIGITALE NON ARRIVA DAI RELAY (lug 2026). Il codice
    # di un buono passa DENTRO Barattolo — c'e' l'endpoint che lo
    # consegna, la rivelazione che fa da ricevuta, le finestre corte
    # di 24/48 ore — e tutto questo chiede che il venditore sia QUI a
    # premere un bottone. Un venditore che sta solo su Nostr non ce
    # l'ha, quel bottone: promettere una consegna immediata che
    # nessuno puo' fare sarebbe una bugia scritta in vetrina, e il
    # compratore la scoprirebbe a sats gia' in cassaforte.
    # Il tag non si ignora per sfiducia: se il venditore entra su
    # Barattolo con la sua chiave, la consegna digitale la dichiara
    # dal form come tutti — dove la guardia sulle vendite minime
    # (DIGITALE_MIN_VENDITE) puo' dire la sua.
    # (`digitale` si legge ma non si usa: serve a NON confonderlo con
    # un tag sconosciuto, e il giorno che i codici si potranno
    # consegnare da fuori bastera' rimettere in piedi il ramo.)
    if spedisce or ritira:
        fuori["consegna"] = ("entrambe" if (spedisce and ritira)
                             else "spedizione" if spedisce else "ritiro")
        fuori["anche_digitale"] = 0
        if spedisce:
            # L'euro resta ancorato all'euro (e' la semantica che
            # Barattolo da' a spedizione_eur); ogni altra valuta
            # diventa il numero in sats che ci hanno detto.
            if valuta_costo == "EUR":
                fuori["spedizione_eur"] = round(costo, 2)
                fuori["spedizione_sats"] = 0
            elif valuta_costo:
                fuori["spedizione_sats"] = int(costo)
                fuori["spedizione_eur"] = 0
    return fuori


# IL TETTO DELLA DESCRIZIONE IMPORTATA (23 ott 2026, cantiere adozione-
# titolo, decisione di Andrea). Erano 1.500 caratteri, e il form di
# Barattolo non ne ha nessuno: un annuncio nato qui con una descrizione
# lunga, firmato dal venditore col BIVIO e riletto dai relay, tornava
# TAGLIATO A META' (il «Turtle», 23 ott 2026: footer di Barattolo
# compreso nei 1.500). Non si toglie: un evento altrui sconosciuto non
# deve poter riempire il database. Diecimila caratteri stanno larghi in
# qualunque descrizione vera e ben dentro il tetto degli eventi dei
# relay (64 KiB di serie su strfry): un evento che li supera i relay non
# lo tengono nemmeno. Lo legge anche il server per giudicare «il testo e'
# cambiato?» — e' per questo che vive in un posto solo.
DESCRIZIONE_IMPORT_MAX = 10000


def testo_evento(e):
    """Titolo e descrizione di un evento, TRONCATI esattamente come
    finiranno nel database. Cuore condiviso: lo usa estrai_annuncio
    per scrivere e il server per capire se l'evento e' cambiato
    davvero da quando l'ha giudicato la moderazione. Se i due
    divergessero, un annuncio identico sembrerebbe cambiato a ogni
    giro (o, peggio, uno cambiato sembrerebbe fermo)."""
    if e.get("kind") == 30402:                 # NIP-99 classified
        t = tag(e, "title")
        titolo = t[1] if t else ""
        s = tag(e, "summary")
        desc = e.get("content", "") or (s[1] if s else "")
    else:                                      # NIP-15 prodotto (30018)
        try:
            c = json.loads(e.get("content", "{}"))
        except Exception:
            return "", ""
        titolo = c.get("name", "") or ""
        desc = c.get("description", "") or ""
    # il titolo senza HTML ne' entita' (8 ott 2026), come per i negozi
    # collegati: spogliato PRIMA di troncare
    return (spoglia_titolo(titolo)[:120],
            (desc or "—").strip()[:DESCRIZIONE_IMPORT_MAX])


def foto_evento(e) -> list:
    """Gli URL delle foto che l'evento dichiara, al massimo cinque: i
    tag `image` del NIP-99, la lista `images` del NIP-15. E' la stessa
    lettura di `estrai_annuncio`, messa in un posto solo l'11 ott 2026
    (cantiere foto-obbligatorie) perche' adesso la fanno in due: chi
    scrive l'annuncio e chi decide se un evento mai visto puo' nascere
    (qui in `importa_venditore`, e nel server prima di pagare l'AI).
    SOLO INDIRIZZI http(s) (14 nov 2026, cantiere audit-chiusure, dal
    primo audit di sicurezza): quei valori li scrive chi firma
    l'evento, e uno che non e' un indirizzo — `../config.py`, un
    percorso assoluto — passava per «un file nostro» ed entrava in
    colonna cosi' com'era. Una foto che non e' un URL non e' una foto:
    l'evento che ha solo quelle e' un evento SENZA foto."""
    def _url_di_foto(u) -> bool:
        return isinstance(u, str) and u.startswith(("http://", "https://"))

    if e.get("kind") == 30402:                 # NIP-99 classified
        return [t[1] for t in e.get("tags", [])
                if t and t[0] == "image" and len(t) > 1
                and _url_di_foto(t[1])][:5]
    try:                                       # NIP-15 prodotto (30018)
        c = json.loads(e.get("content", "{}"))
    except Exception:
        return []
    if not isinstance(c, dict):
        return []
    return [u for u in (c.get("images") or []) if _url_di_foto(u)][:5]


def estrai_annuncio(e, valute_stall, cambio):
    """Trasforma un evento Nostr in un annuncio SatMarket (o None)."""
    titolo, descrizione = testo_evento(e)
    if e["kind"] == 30402:                     # NIP-99 classified
        # (lo "status sold" non si salta piu' qui: lo gestisce il
        # giro principale, che puo' spegnere la riga locale)
        loc = tag(e, "location")
        zona = loc[1] if loc else ""
        p = tag(e, "price")
        if not p or len(p) < 3:
            return None
        importo, valuta = float(p[1]), p[2]
        sats = in_sats(importo, valuta, cambio)
        foto = foto_evento(e)
        # Le coordinate dell'evento origine: il tag "d" (serve alla
        # modifica firmata da Barattolo per SOSTITUIRE l'evento sui
        # relay) e gli URL originali delle foto (per non riscriverli
        # con URL nostri quando l'evento si ricostruisce).
        d = tag(e, "d")
        origine_d = d[1] if d else ""
        origine_foto = json.dumps(foto) if foto else ""
    else:                                      # NIP-15 prodotto (30018)
        try:
            c = json.loads(e.get("content", "{}"))
        except Exception:
            return None
        zona = ""
        valuta = c.get("currency") or valute_stall.get(c.get("stall_id"), "")
        if c.get("price") is None:
            return None
        importo = float(c["price"])
        sats = in_sats(importo, valuta, cambio)
        foto = foto_evento(e)
        origine_d, origine_foto = "", ""       # la modifica firmata (v1)
                                               # parla solo NIP-99

    if not titolo or not sats or sats <= 0:
        return None
    return {"titolo": titolo,
            "descrizione": descrizione,
            "zona": zona.strip()[:60],
            "prezzo_sats": sats,
            "foto": json.dumps(foto) if foto else "",
            # NIENTE categoria indovinata (lug 2026, decisione di
            # Andrea): un evento NIP-99 non dichiara una categoria, e
            # tirarla a indovinare dal titolo sbagliava in silenzio —
            # lo «Sparkling Sake» giapponese finiva fra gli arredi
            # perche' quella categoria pesca «cucina». Nasce in
            # «Altro» e a metterlo al suo posto e' il VENDITORE, che
            # e' l'unico a saperlo davvero. L'import non ricopre mai
            # una categoria gia' scelta, quindi la sua resta per
            # sempre.
            "categoria": "Altro",
            "origine_d": origine_d,
            "origine_foto": origine_foto,
            # l'id dell'evento importato: serve alle cancellazioni
            # NIP-09 che puntano per tag "e" invece che per coordinata
            "origine_id": e.get("id", ""),
            # la coppia del tag price: se il listino nasce in EUR la
            # vetrina deve dirlo (valuta/prezzo_eur), non solo i sats
            "valuta_orig": (valuta or "").upper(),
            "importo_orig": importo,
            # la data dell'EVENTO (created_at): per un replaceable e' la
            # data di pubblicazione vera — finisce in annunci.modificato
            # e il dettaglio la mostra come «pubblicato N giorni fa»
            # (annunci.creato resta l'ora dell'import, che ordina la
            # vetrina e non va toccata)
            "evento_ts": e.get("created_at", 0),
            # spedizione/condizione/quantita' dai tag, se ci sono:
            # solo le chiavi davvero dichiarate (vedi estrai_commercio)
            "commercio": estrai_commercio(e) if e["kind"] == 30402 else {}}


def scrivi_commercio(con, annuncio_id: int, dati: dict):
    """Scrive le SOLE colonne di commercio che l'evento dichiara.
    Colonne che potrebbero non esistere (database di un Barattolo piu'
    vecchio): l'UPDATE si prova e, se la colonna manca, si lascia
    perdere in silenzio — questo file deve poter girare anche da solo,
    senza le migrazioni del server."""
    if not dati:
        return
    for colonna, valore in dati.items():
        try:
            con.execute(f"UPDATE annunci SET {colonna}=? WHERE id=?",
                        (valore, annuncio_id))
        except sqlite3.OperationalError:
            pass


def spegni_annuncio(con, annuncio_id: int, stato: str = "rimosso"):
    """Spegne una riga locale (l'evento e' stato cancellato o segnato
    venduto sui relay) e annulla gli ordini mai pagati, come fa la
    rimozione dalla Mini App. I sats in escrow non c'entrano mai:
    un annuncio con un affare in corso non e' piu' 'attivo'."""
    con.execute("UPDATE annunci SET stato=? WHERE id=?",
                (stato, annuncio_id))
    con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                "WHERE annuncio_id=? AND stato='creato'",
                (int(time.time()), annuncio_id))
    try:
        # Anche i SET 'creato' che contengono il pezzo (lug 2026).
        # Fail-open sul DB di ieri senza la tabella: la crea il
        # server al riavvio, e un set non ancora pagato scade da solo.
        con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                    "WHERE stato='creato' AND id IN (SELECT ordine_id "
                    "FROM ordine_righe WHERE annuncio_id=?)",
                    (int(time.time()), annuncio_id))
    except sqlite3.OperationalError:
        pass


# --- IL RIFLESSO NON E' UNA FONTE (ago 2026) -------------------------
# Un evento che abbiamo composto NOI e fatto firmare al venditore (IL
# BIVIO di annuncio_su_nostr: chi ha una chiave provata pubblica sul
# SUO account, e a firmare e' il suo browser) e' lo SPECCHIO di una
# riga nata su Barattolo, non un annuncio da importare.
#
# Senza questo filtro il match per TITOLO qui sotto «adottava» la riga
# nativa — la clausola ammette `nostr_origine_d=''` e il venditore_id
# e' il suo — scrivendole addosso `contatto_nostr` e la coordinata. Da
# li' l'annuncio nato qui diventava a tutti gli effetti un IMPORTATO:
# il venditore non poteva piu' modificarlo dal form, l'import gli
# riscriveva testo e prezzo dai relay (footer promozionale compreso) e
# una sua NIP-09 da un client qualunque lo spegneva su Barattolo.
#
# E' il gemello di `chiave_di_casa` un piano piu' in basso, ma il
# marchio non puo' essere lo stesso: li' la chiave e' la NOSTRA, qui e'
# la SUA. Quindi il riconoscimento e' una domanda al DATABASE e non al
# testo dell'evento, e sta in TRE condizioni insieme — il `d` e' una
# coordinata nostra, la riga che nomina e' NATIVA, e quella riga
# l'abbiamo fatta firmare proprio a quella chiave. Col solo prefisso
# `barattolo-` ci si affiderebbe a una convenzione di stringa che
# chiunque puo' scrivere; con tutte e tre, a mentire dovrebbe essere il
# nostro stesso database.
def id_riflesso(d: str) -> int:
    """L'id della riga locale di cui questo tag `d` e' la coordinata
    (0 = non e' un evento composto da noi). Prima condizione."""
    if not d or not d.startswith("barattolo-"):
        return 0
    coda = d[len("barattolo-"):]
    return int(coda) if coda.isdigit() else 0


def e_riflesso(riga, pubkey: str) -> bool:
    """Le altre DUE condizioni, sulla riga che la coordinata nomina:
    `riga` e' la coppia (contatto_nostr, nostr_autore) — o None se
    quella riga non esiste piu'.

    Nativa (`contatto_nostr` vuoto: se fosse piena l'annuncio verrebbe
    davvero dai relay e l'import e' a casa sua) e firmata proprio da
    QUELLA chiave. `nostr_autore` vuoto non basta mai: vuol dire riga
    mai firmata da nessuno, e due vuoti che si somigliano non sono una
    prova."""
    if not riga:
        return False
    contatto, autore = (riga[0] or ""), (riga[1] or "").lower()
    return not contatto and bool(autore) and autore == (pubkey or "").lower()


def importa_venditore(npub_venditore: str, venditore_id: int,
                      db: str = DB, vaglio=None, scarica=None,
                      cambio=None, pulisci=None, relays=None, firma=None):
    """Il cuore dell'import, in forma riusabile: lo chiama lo script
    manuale (main, qui sotto) e ogni ora l'orologio del server.
    Ritorna la terna (importati, aggiornati, saltati).

    `vaglio` e' il filtro che il SERVER mette prima della scrittura:
    riceve la lista degli eventi e restituisce quelli ammessi (firma
    verificata, lingua italiana, moderazione superata). Vive li' e
    non qui perche' ha bisogno dell'AI e delle chiavi, che stanno nel
    server; senza (script manuale) l'import si comporta come sempre.

    Il vaglio puo' anche MARCHIARE un evento invece di scartarlo,
    posandogli addosso la chiave `_revisione`: l'annuncio si scrive
    lo stesso, ma nasce (o torna) in stato 'revisione', fuori dalla
    vetrina, in attesa che un moderatore decida. Qui si legge solo il
    marchio — il perche' lo sa il server.

    `cambio` e' lo stesso patto del vaglio, per i soldi: {'EUR': x,
    'USD': y} letto UNA volta dal server per tutto il giro e passato a
    tutti. Senza (script a mano) ci si legge il proprio, come sempre.
    Serve perche' questa funzione la chiama il server una volta PER
    VENDITORE: la lettura che stava qui dentro diventava una raffica di
    chiamate a CoinGecko a ogni giro — e una conversione diversa per
    ogni venditore dello stesso giro, cioe' la seconda verita' che il
    cantiere del cambio doveva togliere di mezzo.
    Un dizionario VUOTO passato apposta vuol dire «non ce l'ho»: gli
    annunci in EUR/USD si saltano e lo si dice, come quando falliva la
    lettura di qui.

    `pulisci` e' `spoglia_metadati` del server — vedi il docstring di
    `scarica_foto`, dove finisce per davvero. Senza (script a mano) le
    foto scaricate portano i metadati che il venditore ci ha messo,
    come sempre: la fiducia sta tutta nella npub scritta a mano nel
    config, non in uno sconosciuto sui relay.

    `relays` (23 set 2026) e' la lista da cui leggere, quando il
    chiamante ne ha una sua: il SERVER la passa gia' filtrata — in
    collaudo i soli relay di casa, vedi `lettura_simulata` in
    server.py. Senza (script a mano) valgono i RELAYS di qui, come
    sempre: e lo script a mano NON e' per i collaudi, legge dai relay
    veri qualunque cosa dica il config.

    `firma` (14 nov 2026, secondo audit di sicurezza) e' il giudice
    della firma del server (`verifica_firma_nostr`): se c'e', OGNI
    evento passa da lui prima di tutto il resto — anche le cancellazioni
    (kind 5) e gli «status sold», che il vaglio non vede. Senza (script
    a mano) come sempre.
    """
    hexkey = npub_to_hex(npub_venditore)
    os.makedirs(FOTO_DIR, exist_ok=True)
    print(f"Cerco gli annunci di {npub_venditore[:20]}… sui relay:\n")
    eventi = []
    for r in (RELAYS if relays is None else relays):
        eventi += interroga(r, hexkey)

    # CHI HA FIRMATO DAVVERO (lug 2026). Fin qui si e' creduto sulla
    # parola al filtro `authors` della REQ: se il relay dice che sono
    # suoi, sono suoi. Con UN venditore fidato era un rischio teorico;
    # da quando l'import e' aperto no — l'autore di un evento decide
    # A CHI VANNO I SATS di chi lo compra, e un relay distratto (o
    # bugiardo) basterebbe a intestare la merce di uno alla cassa di
    # un altro.
    # La firma la si controlla gia' altrove (il vaglio del server), ma
    # controlla una cosa DIVERSA: che l'evento sia firmato dalla
    # chiave che DICHIARA — non che quella chiave sia il venditore che
    # abbiamo chiesto. Le due domande insieme chiudono il buco; una
    # sola, nessuna delle due.
    # Vale anche per i kind 5: una cancellazione altrui, col tag `e`
    # giusto, spegnerebbe l'annuncio di un altro.
    estranei = [e for e in eventi
                if (e.get("pubkey") or "").lower() != hexkey]
    if estranei:
        print(f"  ⚠️ {len(estranei)} eventi NON firmati da questa chiave: "
              f"scartati (il relay ha ignorato il filtro authors)")
        eventi = [e for e in eventi
                  if (e.get("pubkey") or "").lower() == hexkey]

    # ...E FIRMATI DAVVERO, TUTTI (14 nov 2026, cantiere
    # audit-pagamenti-2, dal secondo audit di sicurezza). La `pubkey`
    # qui sopra e' una stringa che chiunque puo' scrivere: la firma la
    # guardava solo il vaglio del server, e il vaglio riceve i soli
    # annunci da scrivere — non le cancellazioni (kind 5) ne' gli
    # «status sold», che spengono una riga e la seppelliscono per
    # sempre (lapide). Un relay qualunque poteva spegnere gli annunci
    # importati di un altro. Ora, col giudice del server, ogni evento
    # passa dalla firma PRIMA del dedup: anche una versione «piu'
    # recente» falsa non nasconde piu' quella vera.
    if firma is not None:
        firmati = [e for e in eventi if firma(e)]
        if len(firmati) < len(eventi):
            print(f"  ✍️ {len(eventi) - len(firmati)} eventi con firma non "
                  f"verificabile: scartati (cancellazioni comprese)")
        eventi = firmati

    # dedup: tieni la versione piu' recente di ogni annuncio
    unici = {}
    for e in eventi:
        d = tag(e, "d")
        chiave = (e["kind"], d[1] if d else e["id"])
        if chiave not in unici or e["created_at"] > unici[chiave]["created_at"]:
            unici[chiave] = e

    # valute dei negozi NIP-15 (stall, kind 30017)
    valute_stall = {}
    for e in unici.values():
        if e["kind"] == 30017:
            try:
                c = json.loads(e["content"])
                valute_stall[c.get("id")] = c.get("currency", "")
            except Exception:
                pass

    # --- Cancellazioni NIP-09 (kind 5) del venditore ---
    # Tag "a" = coordinata kind:pubkey:d (la via giusta per i
    # replaceable, solo i kind che importiamo e solo la SUA chiave),
    # tag "e" = id di un evento preciso. Qui arrivano solo eventi la
    # cui `pubkey` E' questa chiave (il filtro qui sopra), quindi una
    # cancellazione non puo' piu' spegnere l'annuncio di un altro —
    # che col solo tag "e", che non nomina l'autore, sarebbe bastato.
    canc_coord, canc_id = set(), set()
    for e in eventi:
        if e.get("kind") != 5:
            continue
        for t in e.get("tags", []):
            if not t or len(t) < 2 or not t[1]:
                continue
            if t[0] == "a":
                parti = t[1].split(":", 2)
                if (len(parti) == 3 and parti[0] in ("30402", "30018")
                        and parti[1].lower() == hexkey):
                    canc_coord.add(parti[2])       # il tag d
            elif t[0] == "e":
                canc_id.add(t[1])

    prodotti = [e for e in unici.values() if e["kind"] in (30402, 30018)]
    print(f"\nTrovati {len(prodotti)} annunci unici. Converto e importo…\n")
    if not prodotti and not canc_coord and not canc_id:
        print("Nessun annuncio trovato: controlla la npub, o prova ad "
              "aggiungere ai RELAYS quello usato dal tuo amico.")
        # NIENTE return secco: le lapidi dei giri passati vanno fatte
        # rispettare comunque (un rimborso puo' aver riacceso una
        # riga il cui evento non esiste piu' da nessuna parte).

    # il cambio serve solo se c'e' qualcosa da importare
    if not prodotti:
        cambio = {}
    elif cambio is None:            # script a mano: ce lo leggiamo noi
        cambio = cambio_btc()       # (che se non ce la fa lo dice da se')
    elif not cambio:                # il server ce l'ha passato VUOTO:
        print(MSG_CAMBIO_MANCANTE)  # la stessa notizia, mai in silenzio
    # timeout generoso: quando gira dal server il database e' conteso
    con = sqlite3.connect(db, timeout=15)
    # Assicura che il database abbia le colonne nuove (foto, nostr).
    # Le due "origine" ricordano le coordinate dell'evento Nostr
    # (tag d e URL foto originali): servono alla modifica firmata.
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''",
                    "nostr_origine_d TEXT DEFAULT ''",
                    "nostr_origine_foto TEXT DEFAULT ''",
                    "nostr_origine_id TEXT DEFAULT ''",
                    # la chiave che ha FIRMATO l'evento di una riga nata
                    # qui: e' il marchio del riflesso (v. e_riflesso).
                    # Senza la colonna il filtro non scatterebbe e
                    # l'adozione tornerebbe in silenzio.
                    "nostr_autore TEXT DEFAULT ''",
                    "valuta TEXT DEFAULT 'sats'",
                    "prezzo_eur REAL DEFAULT 0",
                    "modificato INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE annunci ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome, username) "
                "VALUES(?, 'Venditore', 'venditore')", (venditore_id,))

    # Il badge del venditore: gli eventi importati sono firmati dalla
    # sua chiave, il possesso e' dimostrato. Se il profilo non dichiara
    # ancora una npub gliela scriviamo gia' verificata (cosi' il login
    # Nostr lo riconosce); una npub DIVERSA gia' presente non si tocca.
    for colonna in ("npub TEXT DEFAULT ''",
                    "npub_verificata INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE utenti ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    npub_bech = hex_to_npub(hexkey)        # forma canonica del badge
    u = con.execute("SELECT npub, npub_verificata FROM utenti "
                    "WHERE tg_id=?", (venditore_id,)).fetchone()
    if u:
        attuale = (u[0] or "").strip()
        if not attuale:
            con.execute("UPDATE utenti SET npub=?, npub_verificata=1 "
                        "WHERE tg_id=?", (npub_bech, venditore_id))
            print("  🟣 Profilo venditore: npub scritta, badge verificato")
        elif attuale == npub_bech and not u[1]:
            con.execute("UPDATE utenti SET npub_verificata=1 "
                        "WHERE tg_id=?", (venditore_id,))
            print("  🟣 Profilo venditore: npub gia' dichiarata, "
                  "badge ora verificato")

    npub = npub_venditore.strip()

    # LAPIDE PERSISTENTE (tappa 2 del cantiere cancellazioni): una
    # cancellazione vista su QUALUNQUE relay si ricorda per sempre,
    # perche' i relay possono scordare il kind 5 prima dell'evento —
    # e senza memoria l'annuncio tornerebbe al giro dopo.
    con.execute("CREATE TABLE IF NOT EXISTS nostr_lapidi("
                "hexkey TEXT NOT NULL, d TEXT NOT NULL DEFAULT '', "
                "event_id TEXT NOT NULL DEFAULT '', "
                "visto INTEGER NOT NULL DEFAULT 0, "
                "PRIMARY KEY(hexkey, d, event_id))")
    adesso = int(time.time())
    # Un tag "e" nudo punta a un id: se quell'evento e' tra i letti
    # ne ricaviamo la coordinata d, che e' stabile nel tempo.
    for e in prodotti:
        if e.get("id") in canc_id:
            dt = tag(e, "d")
            if dt:
                canc_coord.add(dt[1])
    for d in canc_coord:
        con.execute("INSERT OR IGNORE INTO nostr_lapidi(hexkey, d, "
                    "event_id, visto) VALUES(?, ?, '', ?)",
                    (hexkey, d, adesso))
    for eid in canc_id:
        con.execute("INSERT OR IGNORE INTO nostr_lapidi(hexkey, d, "
                    "event_id, visto) VALUES(?, '', ?, ?)",
                    (hexkey, eid, adesso))
    # ...e si rilegge TUTTA: contano anche le lapidi dei giri passati.
    for r in con.execute("SELECT d, event_id FROM nostr_lapidi "
                         "WHERE hexkey=?", (hexkey,)).fetchall():
        if r[0]:
            canc_coord.add(r[0])
        if r[1]:
            canc_id.add(r[1])

    # Le righe locali sotto lapide si SPENGONO: prima restavano
    # attive e COMPRABILI per sempre (il buco vero del cantiere).
    da_spegnere = {}
    for d in canc_coord:
        for r in con.execute(
                "SELECT id, titolo FROM annunci WHERE nostr_origine_d=? "
                "AND stato='attivo' AND (venditore_id=? OR contatto_nostr=?)",
                (d, venditore_id, npub)).fetchall():
            da_spegnere[r[0]] = r[1]
    for eid in canc_id:
        for r in con.execute(
                "SELECT id, titolo FROM annunci WHERE nostr_origine_id=? "
                "AND stato='attivo' AND (venditore_id=? OR contatto_nostr=?)",
                (eid, venditore_id, npub)).fetchall():
            da_spegnere[r[0]] = r[1]
    for aid, titolo in da_spegnere.items():
        spegni_annuncio(con, aid)
        print(f"  🪦 cancellato sui relay: spento «{titolo[:50]}»")

    # E gli eventi sotto lapide non si importano MAI piu' — nemmeno
    # se il venditore ripubblicasse con lo stesso d (imperfezione
    # dichiarata: lapide e' lapide, per tornare serve un d nuovo).
    vivi = []
    for e in prodotti:
        dt = tag(e, "d")
        if e.get("id") in canc_id or (dt and dt[1] in canc_coord):
            continue
        vivi.append(e)
    if len(vivi) < len(prodotti):
        print(f"  🪦 {len(prodotti) - len(vivi)} eventi sotto lapide: "
              f"ignorati")
    prodotti = vivi

    # E i RIFLESSI di Barattolo non si importano MAI: un evento che
    # abbiamo composto noi e fatto firmare al venditore e' lo specchio
    # di una riga nata qui (v. id_riflesso / e_riflesso qui sopra). Si
    # filtra PRIMA del vaglio: cosi' non si paga l'AI per giudicare un
    # testo che la moderazione ha gia' approvato quando l'annuncio e'
    # nato — e soprattutto un «dubbio» non puo' rimandare in revisione
    # un annuncio vivo e in vetrina.
    vivi, riflessi = [], 0
    for e in prodotti:
        dt = tag(e, "d")
        aid = id_riflesso(dt[1] if dt else "")
        if aid:
            riga = con.execute("SELECT contatto_nostr, nostr_autore "
                               "FROM annunci WHERE id=?", (aid,)).fetchone()
            if e_riflesso(riga, e.get("pubkey") or ""):
                riflessi += 1
                continue
        vivi.append(e)
    if riflessi:
        print(f"  🪞 {riflessi} riflessi di Barattolo (annunci nati qui e "
              f"firmati dal venditore): ignorati")
    prodotti = vivi

    # Il vaglio del server (firma, lingua, moderazione) decide cosa
    # ENTRA, mai cosa si spegne: gli eventi con status 'sold' gli si
    # fanno scavalcare apposta, altrimenti una vendita vista sui
    # relay smetterebbe di spegnere la riga locale — che e' proprio
    # il buco chiuso dal cantiere cancellazioni. Si vaglia dopo le
    # lapidi: sugli eventi gia' morti l'AI non si paga.
    if vaglio:
        def e_venduto(e):
            st = tag(e, "status") if e["kind"] == 30402 else None
            return bool(st and st[1] == "sold")
        venduti = [e for e in prodotti if e_venduto(e)]
        prodotti = venduti + list(vaglio([e for e in prodotti
                                          if not e_venduto(e)]))

    importati, aggiornati, saltati = 0, 0, 0
    for e in prodotti:
        # "status sold" sui relay: la riga locale si spegne come
        # 'venduto' (tappa 3: prima l'evento si saltava e l'annuncio
        # restava attivo e COMPRABILE qui). Niente lapide: venduto
        # non e' cancellato — ma lo scudo anti-resurrezione lo tiene
        # spento anche se lo status tornasse active (dichiarato:
        # stesso rimedio, un tag d nuovo).
        st = tag(e, "status") if e["kind"] == 30402 else None
        if st and st[1] == "sold":
            saltati += 1
            dt = tag(e, "d")
            tt = tag(e, "title")
            morto = None
            if dt:
                morto = con.execute(
                    "SELECT id, titolo, modificato FROM annunci "
                    "WHERE nostr_origine_d=? AND stato='attivo' "
                    "AND (venditore_id=? OR contatto_nostr=?)",
                    (dt[1], venditore_id, npub)).fetchone()
            if not morto and tt:
                # La clausola del gemello qui sotto, per la stessa
                # ragione (ago 2026, il tappo delle «due teste»): una
                # riga NATIVA con una testa sua non e' la riga di
                # QUESTO evento, e spegnerla come «venduto» perche' un
                # ALTRO annuncio del venditore e' stato venduto sui
                # relay le toglie la vetrina — e al riavvio dopo la
                # riparazione dell'invariante le azzera pure lo stock
                # (`quantita=0 WHERE stato='venduto'`).
                # Il match per `d` qui sopra resta senza guardia, ed e'
                # giusto: quella E' la riga di questo evento.
                # ...E MAI UNA RIGA NATIVA (23 ott 2026, adozione-titolo,
                # decisione di Andrea): `contatto_nostr<>''`. Una riga
                # nata qui, anche senza testa (la firma del BIVIO che
                # non e' mai arrivata), non e' la riga di un evento dei
                # relay: un omonimo venduto sui relay non la spegne.
                morto = con.execute(
                    "SELECT id, titolo, modificato FROM annunci WHERE titolo=? "
                    "AND stato='attivo' AND contatto_nostr<>'' "
                    "AND (venditore_id=? OR contatto_nostr=?) "
                    "AND (nostr_origine_d='' OR nostr_origine_d IS NULL "
                    "     OR nostr_origine_d=?) "
                    "AND (nostr_event_id='' OR nostr_event_id IS NULL)",
                    (tt[1].strip()[:120], venditore_id, npub,
                     dt[1] if dt else "")).fetchone()
            # UN EVENTO PIU' VECCHIO DELLA RIGA NON LA TOCCA (23 ott 2026,
            # adozione-titolo): la riga e' gia' stata scritta da qualcosa
            # di piu' recente, e un relay rimasto indietro non la spegne
            if morto and e.get("created_at") and (morto[2] or 0) \
                    and e["created_at"] < morto[2]:
                print(f"  ⏮️ «venduto» piu' vecchio della riga: lasciato "
                      f"«{morto[1][:50]}»")
                morto = None
            if morto:
                spegni_annuncio(con, morto[0], "venduto")
                print(f"  🏷️ venduto sui relay: spento «{morto[1][:50]}»")
            continue
        a = estrai_annuncio(e, valute_stall, cambio)
        if not a:
            saltati += 1
            continue
        # Se il listino Nostr parla EUR la vetrina lo dice (doppia
        # valuta); tutte le altre valute restano un listino in sats.
        if a["valuta_orig"] == "EUR":
            valuta, prezzo_eur = "eur", round(a["importo_orig"], 2)
        else:
            valuta, prezzo_eur = "sats", 0
        # Ritrova l'annuncio: PRIMA per tag "d" (la coordinata stabile
        # dell'evento: sopravvive a un cambio di titolo), poi per
        # titolo come una volta — ma senza toccare le righe gia'
        # "battezzate" con un d diverso, che appartengono a un ALTRO
        # evento omonimo.
        gia = None
        if a["origine_d"]:
            gia = con.execute(
                "SELECT id, foto, nostr_origine_foto, modificato, titolo "
                "FROM annunci "
                "WHERE nostr_origine_d=? AND stato='attivo' "
                "AND (venditore_id=? OR contatto_nostr=?)",
                (a["origine_d"], venditore_id, npub)).fetchone()
        if not gia:
            # ...e MAI su una riga che ha gia' una TESTA sua (ago 2026,
            # dal campo: gli annunci 208 e 209). La WHERE qui sotto
            # ammette `venditore_id=?`, quindi fra i candidati per
            # titolo ci sono anche le righe NATIVE di quel venditore —
            # e l'UPDATE piu' sotto scrive `contatto_nostr` senza
            # azzerare `nostr_event_id`, che non nomina proprio. Una
            # riga cosi' dice due cose incompatibili («la fonte e' sui
            # relay» e «di questa riga esiste un evento che comandiamo
            # noi») e il venditore perde Modifica, il rifornimento e
            # perfino «ritira il doppione». Saltandola, l'import gli
            # crea una riga NUOVA: le due restano DUE, e la deduplica —
            # che esiste apposta per la coppia (importato, nativo) e ha
            # il suo bottone — torna a vederle.
            #
            # SOLO QUI, ed e' la riga da non ammorbidire. Il match per
            # `d` qui sopra NON si guarda: una riga nativa non ha mai
            # `nostr_origine_d` (lo scrive solo l'import), quindi da li'
            # le due teste non possono nascere — mentre guardarlo
            # smetterebbe di ritrovare le righe gia' adottate e ne
            # creerebbe copie nuove. Stessa ragione per lo scudo
            # anti-resurrezione qui sotto, dove trasformerebbe uno
            # «skip» in un INSERT.
            #
            # `IS NULL` e non `nostr_event_id=''` secco: chi non ha una
            # testa DEVE restare adottabile — e' il caso legacy per cui
            # questo match per titolo esiste.
            #
            # ...MA SOLO UNA RIGA GIA' IMPORTATA (23 ott 2026, cantiere
            # adozione-titolo, decisione di Andrea): `contatto_nostr<>''`.
            # Il caso legacy sono le righe importate prima del tag `d`,
            # che `contatto_nostr` ce l'hanno. Una riga NATIVA senza testa
            # — l'annuncio rifatto da Telegram che aspetta una firma che
            # non arriva — veniva adottata dal vecchio 30402 omonimo: il
            # testo nuovo ricoperto da quello vecchio (tagliato), il 🟣, e
            # la Modifica che chiede la firma (il «Turtle», 23 ott 2026).
            # Non adottandola nasce una riga nuova, e la deduplica vede
            # la coppia come per le righe con la testa.
            gia = con.execute(
                "SELECT id, foto, nostr_origine_foto, modificato, titolo "
                "FROM annunci "
                "WHERE titolo=? AND stato='attivo' AND contatto_nostr<>'' "
                "AND (venditore_id=? OR contatto_nostr=?) "
                "AND (nostr_origine_d='' OR nostr_origine_d IS NULL "
                "     OR nostr_origine_d=?) "
                "AND (nostr_event_id='' OR nostr_event_id IS NULL)",
                (a["titolo"], venditore_id, npub, a["origine_d"])).fetchone()
        if not gia:
            # SCUDO ANTI-RESURREZIONE (lug 2026, da un bug vissuto):
            # se la stessa coordinata (tag d) o lo stesso titolo esiste
            # gia' nel database ma NON e' piu' attivo — rimosso dal
            # venditore, da un admin, o venduto — l'annuncio NON si
            # ricrea. Prima di questo scudo il match cercava solo tra
            # gli attivi: un annuncio rimosso su Barattolo, col suo
            # evento ancora vivo su un relay, tornava in vetrina a
            # ogni giro d'import.
            spento = None
            if a["origine_d"]:
                spento = con.execute(
                    "SELECT id, stato FROM annunci "
                    "WHERE nostr_origine_d=? AND stato!='attivo' "
                    "AND (venditore_id=? OR contatto_nostr=?)",
                    (a["origine_d"], venditore_id, npub)).fetchone()
            if not spento:
                spento = con.execute(
                    "SELECT id, stato FROM annunci "
                    "WHERE titolo=? AND stato!='attivo' "
                    "AND (venditore_id=? OR contatto_nostr=?) "
                    "AND (nostr_origine_d='' OR nostr_origine_d IS NULL "
                    "     OR nostr_origine_d=?)",
                    (a["titolo"], venditore_id, npub,
                     a["origine_d"])).fetchone()
            if spento:
                saltati += 1
                print(f"  ⛔ non risuscitato (qui e' '{spento[1]}'): "
                      f"{a['titolo'][:50]}")
                continue
        # UN EVENTO PIU' VECCHIO DELLA RIGA NON LA RICOPRE MAI (23 ott
        # 2026, cantiere adozione-titolo, decisione di Andrea): `modificato`
        # e' la data dell'ultimo contenuto scritto (l'evento importato, o
        # la modifica firmata), e un relay rimasto indietro con la
        # versione di prima non deve riportarla in vetrina.
        if gia and a.get("evento_ts") and (gia[3] or 0) \
                and a["evento_ts"] < gia[3]:
            saltati += 1
            print(f"  ⏮️ evento piu' vecchio della riga: lasciata "
                  f"«{(gia[4] or '')[:50]}»")
            continue
        if gia:
            # Gia' presente: aggiorna TUTTO il contenuto (l'evento sui
            # relay e' la fonte di verita', anche dopo una modifica
            # firmata da Barattolo) e il PROPRIETARIO (utile al lancio).
            # La categoria invece resta: categoria_automatica
            # ricoprirebbe ogni ora una scelta fatta a mano dal form.
            if a["origine_foto"] and a["origine_foto"] == gia[2]:
                foto_loc = gia[1]      # stesse foto: niente ri-download
            else:
                foto_loc = localizza_foto(gia[0], a["foto"], scarica, pulisci)
            con.execute(
                "UPDATE annunci SET titolo=?, descrizione=?, zona=?, "
                "foto=?, contatto_nostr=?, prezzo_sats=?, valuta=?, "
                "prezzo_eur=?, venditore_id=?, nostr_origine_d=?, "
                "nostr_origine_foto=?, nostr_origine_id=?, modificato=? "
                "WHERE id=?",
                (a["titolo"], a["descrizione"], a["zona"], foto_loc, npub,
                 a["prezzo_sats"], valuta, prezzo_eur, venditore_id,
                 a["origine_d"], a["origine_foto"], a["origine_id"],
                 a["evento_ts"], gia[0]))
            # I metadati di commercio si scrivono SOLO se l'evento li
            # dichiara: un tag assente lascia intatto quello che c'e'
            # gia' qui. E' la regola della categoria — cio' che il
            # venditore ha messo a mano su Barattolo non deve essere
            # ricoperto ogni ora dal silenzio dei relay.
            scrivi_commercio(con, gia[0], a["commercio"])
            # Il marchio del vaglio (v. importa_venditore): un annuncio
            # gia' in vetrina il cui TESTO e' cambiato e che adesso il
            # moderatore automatico non sa piu' approvare torna in
            # attesa, come una modifica fatta dal form. Sparisce dalla
            # vetrina finche' un umano non dice la sua.
            if e.get("_revisione"):
                con.execute("UPDATE annunci SET stato='revisione' "
                            "WHERE id=? AND stato='attivo'", (gia[0],))
                print(f"  ⏳ rimesso in revisione: {a['titolo'][:50]}")
            aggiornati += 1
            print(f"  ↻ aggiornato: {a['titolo'][:50]}")
            continue
        # ALMENO UNA FOTO PER ENTRARE (11 ott 2026, cantiere
        # foto-obbligatorie, decisione di Andrea): la regola del foglio
        # «Pubblica» vale anche per chi arriva dai relay. A chi scrive
        # con un altro client non si puo' imporre niente — si puo' solo
        # non far NASCERE qui l'annuncio che non ne ha: al giro in cui
        # l'evento ne porta una e' un evento mai visto come gli altri,
        # ed entra. SOLO LA NASCITA: chi e' gia' in vetrina si aggiorna
        # come sempre qui sopra, anche se sui relay la foto e' sparita
        # (gli annunci gia' online restano com'erano, e spegnerli da
        # qui sarebbe togliere merce a un venditore senza dirglielo).
        if not a["foto"]:
            saltati += 1
            print(f"  📷 senza foto, non entra: {a['titolo'][:50]}")
            continue
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
            "prezzo_sats,zona,foto,contatto_nostr,valuta,prezzo_eur,"
            "nostr_origine_d,nostr_origine_foto,nostr_origine_id,creato,"
            "modificato,stato) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (venditore_id, a["titolo"], a["descrizione"], a["categoria"],
             a["prezzo_sats"], a["zona"], a["foto"], npub, valuta,
             prezzo_eur, a["origine_d"], a["origine_foto"],
             a["origine_id"], int(time.time()), a["evento_ts"],
             "revisione" if e.get("_revisione") else "attivo"))
        scrivi_commercio(con, cur.lastrowid, a["commercio"])
        # Le foto si scaricano DOPO l'insert: il nome file vuole l'id
        foto_loc = localizza_foto(cur.lastrowid, a["foto"], scarica, pulisci)
        if foto_loc != a["foto"]:
            con.execute("UPDATE annunci SET foto=? WHERE id=?",
                        (foto_loc, cur.lastrowid))
        importati += 1
        n_foto = len(json.loads(foto_loc)) if foto_loc else 0
        print(f"  ⚡ {a['titolo'][:50]} — {a['prezzo_sats']} sats "
              f"[{a['categoria']}] {'📷x'+str(n_foto) if n_foto else ''}")

    con.commit()
    con.close()
    return importati, aggiornati, saltati


def main():
    if not NPUB_VENDITORE or not VENDITORE_ID:
        raise SystemExit(
            "\n⚠️  Manca config.py (o le righe NPUB_VENDITORE e VENDITORE_ID"
            "\n   al suo interno). Aggiungile e rilancia. Esempio:\n"
            '\n   NPUB_VENDITORE = "npub1..."'
            "\n   VENDITORE_ID = 222\n")
    importati, aggiornati, saltati = importa_venditore(
        NPUB_VENDITORE, VENDITORE_ID)
    print(f"\nFATTO: {importati} importati, {aggiornati} aggiornati, "
          f"{saltati} saltati (venduti o senza prezzo).")
    print("Riavvia il server e guardali in vetrina nella Mini App!")


if __name__ == "__main__":
    main()
