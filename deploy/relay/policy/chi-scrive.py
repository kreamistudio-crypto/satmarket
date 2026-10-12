#!/usr/bin/env python3
"""Chi puo' scrivere sul relay di Barattolo.

FAIL-CLOSED: se la lista non si legge resta l'ultima buona, e se
qualcosa esplode si RIFIUTA. Un relay che rifiuta i nostri annunci e'
un guasto che si vede in un'ora; uno che accetta da chiunque e' un
disco pieno che si scopre a cose fatte.

LA RETE NON SI TOCCA MAI DA QUI: la lista arriva in un file che un
timer rinfresca per conto suo.

LE PORTE SONO DUE (12 ott 2026, cantiere relay-per-mostro).
1) LA LISTA, quella di sempre: chi firma sta in `chiavi.txt` (la
   piattaforma, il coordinatore, i venditori con la chiave provata) e
   scrive quel che vuole. Niente e' cambiato.
2) LA BUCA DELLE LETTERE DEL COORDINATORE: chi NON sta in lista puo'
   lasciare UNA cosa sola, un messaggio indirizzato al nostro Mostro.
   Sono le richieste dei telefoni — presa, rilascio, voto — firmate da
   chiavi usa-e-getta che in una lista non possono stare. Fino a oggi
   passavano dal solo relay.mostro.network, che non e' nostro: caduto
   lui, nessuno prendeva, rilasciava o votava.
   LA FORMA E' STRETTA, ed e' quella che la pagina manda davvero
   (`mostroChiama` in miniapp.html): kind 14, UN tag `p` ed e' il
   coordinatore, UNA scadenza vicina (NIP-40: il relay lo butta da
   se'), pochi tag, pochi byte. Tutto il resto resta fuori come ieri,
   compresa la chat fra le due parti e quella col moderatore, che sono
   kind 14 ma con un altro destinatario (decisione di Andrea).
   E TRE FRENI, perche' una buca aperta a chiunque e' una buca: tanti
   al minuto per indirizzo IP, tanti per chiave, tanti in tutto. Le
   chiavi nascono nuove a ogni scambio, quindi il freno vero e' l'IP;
   quello in tutto e' il tetto del disco. Vivono in memoria: quando
   strfry rilancia questo file ripartono da zero, e va bene cosi'.
   Chi sta in lista i freni non li vede.
"""
import ipaddress
import json
import os
import sys
import time

# E' una CARTELLA montata, non un file: un bind mount di un file
# singolo ancora l'inode, e il primo rinfresco atomico congelerebbe
# la lista per sempre senza che niente fallisca.
CHIAVI = "/etc/strfry-policy/chiavi.txt"
PIATTAFORMA = "2e7afe3f9af8c3dc90d6e8acaf5d7aa926a54f0c22f1c555707309c059fe831b"

# IL DESTINATARIO della buca: la chiave PUBBLICA del nostro
# coordinatore, la stessa scritta in `router.conf` (una prova di
# prove.py le tiene uguali). Qui sta scolpita e non in `chiavi.txt`,
# perche' quel file dice CHI SCRIVE e li' dentro il coordinatore e'
# una riga uguale a quella di un venditore: non si distingue. Il giorno
# che il coordinatore cambia chiave si cambiano le due righe insieme.
MOSTRO = "afe3de9aa8616d7c2e62eb336d3a127cf9daa9b4482ab1e9361d5c175d3b8cf3"

KIND_PER_MOSTRO = 14
# I byte dell'evento intero, scritto stretto. 16 KB sono la partenza
# (decisione di Andrea, da confermare sui messaggi veri: PRODUZIONE,
# «LA BUCA DEL COORDINATORE»); strfry di suo ne lascerebbe 64.
BYTE_MAX = 16384
TAG_MAX = 6
# La pagina mette la scadenza a un'ora (`P2P_SCADENZA_MSG`); strfry
# tollera un orologio avanti di 15 minuti. Due ore tengono dentro
# tutte e due le cose, e un messaggio che vuole restare un mese no.
SCADENZA_MAX_S = 7200

FINESTRA_S = 60
PER_IP = 30
PER_CHIAVE = 10
IN_TUTTO = 600
# Quante voci tiene un freno prima di buttare le piu' vecchie: senza,
# la memoria del freno sarebbe lei il disco pieno.
VOCI_MAX = 20000

NO_LISTA = "restricted: solo Barattolo, i suoi venditori e i messaggi per il suo coordinatore P2P"
NO_FRENO = "rate-limited: troppi messaggi in un minuto, riprova fra poco"

_ammesse = {PIATTAFORMA}
_visto = 0.0


def rileggi():
    global _ammesse, _visto
    try:
        quando = os.path.getmtime(CHIAVI)
        if quando == _visto:
            return
        with open(CHIAVI, encoding="utf-8") as f:
            fresche = set()
            for riga in f:
                k = riga.strip().lower()
                if len(k) == 64 and all(c in "0123456789abcdef" for c in k):
                    fresche.add(k)
        _ammesse = fresche | {PIATTAFORMA}
        _visto = quando
    except Exception:
        pass


def per_mostro(ev, adesso):
    """PURA: l'evento ha la forma di un messaggio per il coordinatore?
    Torna "" se si', altrimenti il perche' (che finisce nel log di
    strfry e nella risposta al client). Non guarda chi firma e non
    conta niente: quello e' dei freni."""
    if ev.get("kind") != KIND_PER_MOSTRO:
        return NO_LISTA
    tags = ev.get("tags")
    if not isinstance(tags, list) or len(tags) > TAG_MAX:
        return "restricted: troppi tag per un messaggio al coordinatore"
    destinatari, scadenze = [], []
    for t in tags:
        if (not isinstance(t, list) or len(t) < 2
                or not all(isinstance(x, str) for x in t)):
            return "restricted: tag malformato"
        if t[0] == "p":
            destinatari.append(t[1])
        elif t[0] == "expiration":
            scadenze.append(t[1])
    if destinatari != [MOSTRO]:
        return NO_LISTA
    if len(scadenze) != 1 or not scadenze[0].isdigit():
        return "restricted: al coordinatore si scrive con una scadenza (NIP-40)"
    fra = int(scadenze[0]) - adesso
    if fra <= 0 or fra > SCADENZA_MAX_S:
        return "restricted: scadenza troppo lontana o gia' passata"
    stretto = json.dumps(ev, separators=(",", ":"), ensure_ascii=False)
    if len(stretto.encode("utf-8")) > BYTE_MAX:
        return "restricted: messaggio troppo grande"
    return ""


def secchio_ip(info):
    """PURA: sotto quale nome si conta questo indirizzo. Un IPv4 e' se
    stesso; un IPv6 e' la sua /64, che e' quanto ne ha in mano una casa
    sola. Quel che non si sa leggere finisce TUTTO in un secchio solo:
    nel dubbio si frena insieme, non si lascia passare a parte."""
    testo = str(info or "").split(",")[-1].strip()
    try:
        ip = ipaddress.ip_address(testo)
    except ValueError:
        return "?"
    if ip.version == 6:
        if ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        # dal NUMERO e non dal testo: un indirizzo con la zona
        # (`fe80::1%eth0`) col testo non si lascerebbe tagliare
        return str(ipaddress.IPv6Network((int(ip) >> 64 << 64, 64)))
    return str(ip)


class Freno:
    """Quanti in una finestra, per nome. `libero` guarda, `segna`
    scrive: le due cose sono separate perche' un messaggio fermato da
    UN freno non deve consumare il posto negli altri due."""

    def __init__(self, tetto, finestra=FINESTRA_S):
        self.tetto, self.finestra, self.visti = tetto, finestra, {}

    def libero(self, chi, adesso):
        coda = self.visti.get(chi)
        if not coda:
            return True
        soglia = adesso - self.finestra
        while coda and coda[0] <= soglia:
            coda.pop(0)
        return len(coda) < self.tetto

    def segna(self, chi, adesso):
        if chi not in self.visti and len(self.visti) >= VOCI_MAX:
            soglia = adesso - self.finestra
            for k in [k for k, c in self.visti.items()
                      if not c or c[-1] <= soglia]:
                del self.visti[k]
            if len(self.visti) >= VOCI_MAX:
                self.visti.clear()
        self.visti.setdefault(chi, []).append(adesso)


_freno_ip = Freno(PER_IP)
_freno_chiave = Freno(PER_CHIAVE)
_freno_tutti = Freno(IN_TUTTO)


def giudica(d, adesso):
    """Il giudice: (accetta?, perche'). Prima la lista, poi la buca."""
    ev = d["event"]
    chi = ev["pubkey"].lower()
    if chi in _ammesse:
        return True, ""
    perche = per_mostro(ev, adesso)
    if perche:
        return False, perche
    ip = secchio_ip(d.get("sourceInfo"))
    if not (_freno_ip.libero(ip, adesso)
            and _freno_chiave.libero(chi, adesso)
            and _freno_tutti.libero("tutti", adesso)):
        return False, NO_FRENO
    _freno_ip.segna(ip, adesso)
    _freno_chiave.segna(chi, adesso)
    _freno_tutti.segna("tutti", adesso)
    return True, ""


def main():
    for linea in sys.stdin:
        id_ev = ""
        try:
            d = json.loads(linea)
            id_ev = d["event"]["id"]
            rileggi()
            ok, perche = giudica(d, time.time())
        except Exception:
            ok, perche = False, NO_LISTA
        print(json.dumps({
            "id": id_ev,
            "action": "accept" if ok else "reject",
            "msg": "" if ok else perche,
        }), flush=True)


if __name__ == "__main__":
    main()
