# -*- coding: utf-8 -*-
"""
I COLLAUDI IN CI (22 set 2026), dentro una gabbia senza rete.

I collaudi girano il SERVER VERO su un database usa-e-getta, ed e' la
domanda che `prove.py` non fa: una colonna che manca, un nome definito
dopo il suo uso, un doppio con la firma vecchia. Fino a oggi li girava
solo chi se ne ricordava — e `collaudo_feedback_confermato` e' rimasto
ROSSO tre giorni (il `riga=` di `paga_venditore`, 19 set) senza che
nessuno lo vedesse. Adesso li gira la CI, e un collaudo rosso ferma il
deploy come una prova rossa.

L'ELENCO NON STA QUI: sta nel workflow, scritto a mano, uno per nome.
Entra solo un collaudo che e' stato GUARDATO — niente rete, nessun
config vero, stesso esito a ogni giro — e un collaudo nuovo non ci
finisce da solo per il fatto di chiamarsi `collaudo_*`.

LA GABBIA E' IL PEZZO DA NON TOGLIERE. «Senza rete» detto a parole non
regge: basta un `notifica` non sostituito, un cambio BTC/EUR chiesto
davvero, e il collaudo parla con Telegram o con Kraken — in CI passa o
non passa secondo il raffreddore di un server altrui, che e' il modo in
cui una CI smette di essere guardata. Quindi ogni collaudo parte con un
`sitecustomize` che ferma ogni connessione fuori da 127.0.0.1 (e ogni
risoluzione DNS di un nome che non sia `localhost`) come farebbe una
rete staccata — un OSError — e la SEGNA: una bussata fuori fa rosso il
collaudo anche se il collaudo, fail-open com'e' giusto, e' passato lo
stesso. Il `sitecustomize` vale anche per i processi figli, perche'
viaggia nel PYTHONPATH.

Uso:  python collaudi_ci.py collaudo_porta_timer collaudo_... [...]
"""
import os
import re
import subprocess
import sys
import tempfile
import time

QUI = os.path.dirname(os.path.abspath(__file__))
TEMPO_MAX_S = 600

GABBIA = r'''
import ipaddress as _ip
import os as _os
import socket as _so
import sys as _sys

_SEGNI = _os.environ.get("GABBIA_SEGNI", "")


def _segna(dove):
    riga = f"{_os.path.basename(_sys.argv[0] or '?')}: {dove}"
    print(f"⛔ GABBIA: bussata fuori — {riga}", file=_sys.stderr,
          flush=True)
    if _SEGNI:
        with open(_SEGNI, "a", encoding="utf-8") as f:
            f.write(riga + "\n")
    raise OSError(101, "rete staccata dalla gabbia dei collaudi")


def _di_casa(host):
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    host = str(host)
    if host in ("localhost", ""):
        return True
    try:
        return _ip.ip_address(host.split("%")[0]).is_loopback
    except ValueError:
        return False


_getaddrinfo = _so.getaddrinfo


def getaddrinfo(host, *a, **k):
    if not _di_casa(host):
        _segna(f"DNS {host}")
    return _getaddrinfo(host, *a, **k)


_so.getaddrinfo = getaddrinfo


def _guardia(nome):
    vero = getattr(_so.socket, nome)

    def fatto(self, indirizzo, *a, **k):
        if self.family in (_so.AF_INET, _so.AF_INET6) and \
                not _di_casa(indirizzo[0]):
            _segna(f"{nome} {indirizzo[0]}:{indirizzo[1]}")
        return vero(self, indirizzo, *a, **k)
    setattr(_so.socket, nome, fatto)


for _n in ("connect", "connect_ex"):
    _guardia(_n)

_sendto = _so.socket.sendto


def sendto(self, dati, *a):
    indirizzo = a[-1]
    if self.family in (_so.AF_INET, _so.AF_INET6) and \
            not _di_casa(indirizzo[0]):
        _segna(f"sendto {indirizzo[0]}:{indirizzo[1]}")
    return _sendto(self, dati, *a)


_so.socket.sendto = sendto
'''


# I SEGNI DI UNA RIGA ROSSA, come li stampano i banchi dei collaudi: la
# «✗» dei piu', il «NO» di collaudo_pagamento_p2p e di chi lo importa,
# «[NO]» e «[KO]» di qualche banco piu' vecchio, FAIL e ⛔ del lanciatore
# stesso. Un Traceback e' rosso a parte: si prende il blocco intero.
SEGNI_ROSSI = ("✗", "NO ", "[NO]", "[KO]", "FAIL", "⛔")
# ...e la riga di un'eccezione («KeyError: 'x'», «SyntaxError: …»)
FORMA_ECCEZIONE = re.compile(r"^[A-Za-z_][\w.]*(Error|Exception)(:|$)")


def righe_rosse(uscita):
    """TUTTE le righe rosse di un collaudo, con qualunque segno, ognuna
    con l'atteso e l'avuto che la seguono, e i Traceback interi, ovunque
    stiano nell'uscita.

    LA CODA NON BASTAVA (1 ott 2026, decisione di Andrea): la CI stampava
    le ultime quaranta righe, e `collaudo_db_contesa` dopo la riga caduta
    stampa le centinaia di «🏪» del giro — il registro diceva «23 passate,
    1 fallite» e nessuno poteva sapere QUALE. Una prova a tempo caduta a
    caso in CI e mai in locale e' esattamente il caso in cui serve il
    nome, perche' rifarla non la fa ricadere.
    E LA SOLA «✗» NON BASTAVA (12 ott 2026, richiesta di Andrea): i banchi
    del P2P scrivono «NO», e un collaudo con quattro rosse ne mostrava una
    — quella rimasta nella coda. Ora ogni segno vale, e l'atteso senza i
    due punti («atteso 400 con…», «atteso un rifiuto…») si prende pure."""
    righe = uscita.splitlines()
    rosse = []
    i = 0
    while i < len(righe):
        r = righe[i].strip()
        if r.startswith("Traceback (most recent call last):"):
            # il blocco intero: i frame (rientrati) e la riga dell'eccezione
            blocco = [r]
            j = i + 1
            while j < len(righe) and (not righe[j].strip()
                                      or righe[j].startswith((" ", "\t"))):
                if righe[j].strip():
                    blocco.append("    " + righe[j].strip())
                j += 1
            if j < len(righe):
                blocco.append("    " + righe[j].strip())
                j += 1
            rosse.extend(blocco)
            i = j
            continue
        if r.startswith(SEGNI_ROSSI):
            rosse.append(r)
            for dopo in righe[i + 1:i + 4]:
                if dopo.strip().startswith(("atteso", "avuto")):
                    rosse.append("    " + dopo.strip())
        elif FORMA_ECCEZIONE.match(r):
            # un'eccezione SENZA il «Traceback» davanti: un SyntaxError
            # stampa File, la riga, il cursore e «SyntaxError: …» e basta
            rosse.append(r)
        i += 1
    return rosse


def senza_segno(r):
    """La riga rossa senza il suo segno, per l'annotazione della CI."""
    for s in SEGNI_ROSSI:
        if r.startswith(s):
            return r[len(s):].strip()
    return r.strip()


def gira(nome, gabbia, segni):
    """Un collaudo, nella gabbia. Torna (ok, secondi, uscita)."""
    percorso = os.path.join(QUI, nome + ".py")
    if not os.path.exists(percorso):
        return False, 0.0, f"⛔ {nome}.py non esiste"
    amb = dict(os.environ)
    amb["PYTHONPATH"] = gabbia + (os.pathsep + amb["PYTHONPATH"]
                                  if amb.get("PYTHONPATH") else "")
    amb["PYTHONUTF8"] = "1"
    amb["PYTHONIOENCODING"] = "utf-8"
    amb["GABBIA_SEGNI"] = segni
    inizio = time.time()
    try:
        r = subprocess.run([sys.executable, percorso], cwd=QUI, env=amb,
                           capture_output=True, encoding="utf-8",
                           errors="replace", timeout=TEMPO_MAX_S)
        uscita, codice = r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        uscita = f"{e.stdout or ''}{e.stderr or ''}\n⛔ oltre {TEMPO_MAX_S}s"
        codice = -1
    return codice == 0, time.time() - inizio, uscita


def main(nomi):
    # la console di Windows parla cp1252, e una ✓ la farebbe esplodere
    sys.stdout.reconfigure(encoding="utf-8")
    if not nomi:
        print("Uso: python collaudi_ci.py collaudo_uno collaudo_due ...")
        return 2
    gabbia = tempfile.mkdtemp(prefix="gabbia-collaudi-")
    with open(os.path.join(gabbia, "sitecustomize.py"), "w",
              encoding="utf-8") as f:
        f.write(GABBIA)
    rossi = []
    for nome in nomi:
        nome = nome.removesuffix(".py")
        segni = os.path.join(gabbia, nome + ".segni")
        ok, secondi, uscita = gira(nome, gabbia, segni)
        bussate = (open(segni, encoding="utf-8").read().splitlines()
                   if os.path.exists(segni) else [])
        if bussate:
            ok = False
        segno = "✓" if ok else "✗"
        print(f"{segno} {nome}  ({secondi:.0f}s)", flush=True)
        if not ok:
            rossi.append(nome)
            print("\n".join("    " + r for r in uscita.splitlines()[-40:]))
            # E QUALI RIGHE SONO CADUTE, TUTTE, anche se stanno ben prima
            # della coda — una annotazione per riga, che GitHub mostra in
            # cima alla corsa senza aprire il registro
            rosse = righe_rosse(uscita)
            if rosse:
                print(f"    --- le righe rosse di {nome}, tutte ---")
                print("\n".join("    " + r for r in rosse))
                for k, r in enumerate(rosse):
                    if r.startswith("Traceback"):
                        # l'annotazione dice l'ECCEZIONE, cioe' l'ultima
                        # riga del blocco (le righe del blocco sono rientrate)
                        fine = k + 1
                        while fine < len(rosse) and rosse[fine].startswith("    "):
                            fine += 1
                        print(f"::error::{nome}: {rosse[fine - 1].strip()}")
                    elif r.startswith(SEGNI_ROSSI) or FORMA_ECCEZIONE.match(r):
                        print(f"::error::{nome}: {senza_segno(r)}")
            for b in bussate:
                print(f"    ⛔ rete: {b}")
                print(f"::error::{nome}: ha provato a uscire in rete ({b})")
            print(f"::error::{nome} e' rosso")
    print(f"\n{len(nomi) - len(rossi)} verdi, {len(rossi)} rossi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
