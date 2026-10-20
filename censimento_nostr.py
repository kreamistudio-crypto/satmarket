# -*- coding: utf-8 -*-
"""
CENSIMENTO NOSTR — quanti annunci di vendita ci sono davvero,
e quanti sembrano italiani?

Interroga i principali relay Nostr per gli eventi:
  - kind 30402 (NIP-99: annunci "classified", tipo Subito)
  - kind 30018 (NIP-15: prodotti dei negozi, tipo Shopstr/Plebeian)
poi conta tutto e segnala quelli con indizi italiani (località,
lingua, parole tipiche).

REQUISITI:  pip install websocket-client
USO:        python censimento_nostr.py
Durata: ~1-2 minuti (dipende dai relay).
"""

import json
import ssl
import time

from websocket import create_connection

# I CERTIFICATI DEI RELAY SI VERIFICANO (20 ott 2026, cantiere
# certificati-relay, decisione di Andrea): sul nome del relay, con le CA
# del sistema, come nel server (`SSLOPT_RELAY` di server.py, col perche').
# Un certificato non valido e' un relay irraggiungibile; mai CERT_NONE.
SSLOPT_RELAY = {"cert_reqs": ssl.CERT_REQUIRED}

RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.nostr.band",
    "wss://relay.primal.net",
    "wss://relay.snort.social",
    "wss://nostr.mom",
]

# Quanti eventi chiedere per kind a ogni relay (molti relay
# comunque non superano i 500)
LIMITE = 500

# Indizi che un annuncio sia italiano
CITTA = ["italia", "italy", "milano", "roma", "torino", "napoli", "bologna",
         "firenze", "genova", "palermo", "venezia", "verona", "padova",
         "brescia", "bergamo", "pavia", "monza", "como", "varese", "bari",
         "catania", "cagliari", "trento", "trieste", "parma", "modena",
         "lombardia", "piemonte", "veneto", "toscana", "lazio", "sicilia",
         "sardegna", "emilia", "liguria", "puglia", "campania"]
PAROLE_IT = ["vendo", "vendesi", "spedizione", "spedisco", "usato", "nuovo",
             "ottime condizioni", "perfette condizioni", "ritiro a mano",
             "consegna", "trattabile", "prezzo", "acquisto", "cerco"]


def tag(evento, nome, pos=1):
    """Legge il primo tag con quel nome (es. 'title', 'location', 'price')."""
    for t in evento.get("tags", []):
        if t and t[0] == nome and len(t) > pos - 1:
            return " ".join(str(x) for x in t[1:]) if pos == "all" else t[pos] if len(t) > pos else ""
    return ""


def testo_completo(e):
    parti = [e.get("content", "")]
    for t in e.get("tags", []):
        if t and t[0] in ("title", "summary", "location", "t"):
            parti += [str(x) for x in t[1:]]
    return " ".join(parti).lower()


def sembra_italiano(e):
    txt = testo_completo(e)
    if any(c in txt for c in CITTA):
        return "località"
    trovate = sum(1 for p in PAROLE_IT if p in txt)
    if trovate >= 2:          # almeno 2 parole italiane tipiche
        return "lingua"
    return ""


def interroga(relay):
    """Chiede a un relay gli annunci kind 30402 e 30018."""
    eventi = []
    try:
        ws = create_connection(relay, timeout=10,
                               sslopt=SSLOPT_RELAY)
        sub = "censimento"
        ws.send(json.dumps(["REQ", sub,
                            {"kinds": [30402, 30018], "limit": LIMITE}]))
        inizio = time.time()
        while time.time() - inizio < 25:      # max 25s per relay
            try:
                msg = json.loads(ws.recv())
            except Exception:
                break
            if msg[0] == "EVENT" and msg[1] == sub:
                eventi.append(msg[2])
            elif msg[0] == "EOSE":            # il relay ha finito
                break
        ws.close()
    except Exception as errore:
        print(f"  ✗ {relay}: non raggiungibile ({errore})")
        return []
    print(f"  ✓ {relay}: {len(eventi)} eventi")
    return eventi


def main():
    print("Interrogo i relay (1-2 minuti)…\n")
    tutti = []
    for r in RELAYS:
        tutti += interroga(r)

    # Dedup: gli annunci sono eventi "addressable", la versione piu'
    # recente per (autore, kind, d-tag) e' quella valida
    unici = {}
    for e in tutti:
        chiave = (e["pubkey"], e["kind"], tag(e, "d"))
        if chiave not in unici or e["created_at"] > unici[chiave]["created_at"]:
            unici[chiave] = e
    annunci = list(unici.values())

    attivi = [e for e in annunci if tag(e, "status") != "sold"]
    nip99 = sum(1 for e in annunci if e["kind"] == 30402)
    nip15 = sum(1 for e in annunci if e["kind"] == 30018)

    anno_fa = time.time() - 365 * 86400
    recenti = [e for e in attivi if e["created_at"] > anno_fa]

    print(f"\n{'='*58}")
    print(f"TOTALE annunci unici trovati : {len(annunci)}")
    print(f"  di cui NIP-99 (classified) : {nip99}")
    print(f"  di cui NIP-15 (negozi)     : {nip15}")
    print(f"  attivi (non 'sold')        : {len(attivi)}")
    print(f"  attivi e recenti (< 1 anno): {len(recenti)}")
    print(f"{'='*58}\n")

    italiani = [(e, sembra_italiano(e)) for e in attivi]
    italiani = [(e, m) for e, m in italiani if m]
    print(f"🇮🇹 CANDIDATI ITALIANI: {len(italiani)}\n")
    for e, motivo in sorted(italiani, key=lambda x: -x[0]["created_at"]):
        titolo = tag(e, "title") or e.get("content", "")[:60]
        prezzo = ""
        for t in e.get("tags", []):
            if t and t[0] == "price" and len(t) >= 3:
                prezzo = f"{t[1]} {t[2]}"
        quando = time.strftime("%Y-%m-%d", time.localtime(e["created_at"]))
        luogo = tag(e, "location")
        print(f"  • [{quando}] {titolo[:60]}")
        print(f"     {prezzo or 'prezzo n.d.'} | {luogo or 'zona n.d.'} "
              f"| indizio: {motivo} | npub: {e['pubkey'][:16]}…\n")

    if not italiani:
        print("  Nessun annuncio con indizi italiani sui relay interrogati.")
    print("\nNota: e' un campione (i relay limitano le risposte), ma da'")
    print("l'ordine di grandezza reale del commercio italiano su Nostr.")


if __name__ == "__main__":
    main()
