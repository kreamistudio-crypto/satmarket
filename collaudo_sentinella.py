# -*- coding: utf-8 -*-
"""
LA SENTINELLA DEL SERVER FERMO, dal vivo (17 nov 2026).

Il 17 nov alle 08:07 la produzione si e' fermata dopo una promozione:
porta aperta, /api/salute muta, journal zitto, e nessuna riga che
dicesse DOVE. La sentinella (server.py, «LA SENTINELLA DEL SERVER
FERMO») bussa a /api/salute da un filo suo; al primo silenzio scrive la
pila di tutti i fili, fermo da tanto esce col codice 70 e systemd lo
rialza. Qui si fa succedere davvero, su un server VERO lanciato con
uvicorn su loopback e un database usa-e-getta (dell'avvio gira la sola
sentinella: gli altri compiti uscirebbero in rete):

  1. il server parte e la riga del journal dice «accesa», con la porta
     presa dagli argomenti (`--port`);
  2. una rotta di cartone ferma il ciclo con un `time.sleep` dentro una
     `async def` — il guasto piu' brutale che ci sia: /api/salute
     smette di rispondere;
  3. la sentinella scrive la pila, e nella pila c'e' la riga colpevole;
  4. passato il tetto il processo esce da solo col codice 70 e lascia
     il segno accanto al database;
  5. il riavvio legge il segno, lo dice e lo cancella (l'avviso agli
     admin, in collaudo, si stampa);
  6. uno spegnimento normale (SIGTERM) NON fa scattare niente.

I tempi sono stretti apposta (1 s di colpo, 3 s di tetto): la logica e'
la stessa, le costanti si abbassano nel processo figlio.
NON TOCCA NIENTE DI VERO: config finto installato PRIMA di importare il
server, MODALITA_COLLAUDO, porta di loopback libera, nessuna rete.

Uso:  python collaudo_sentinella.py
"""
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SEGNO = ".sentinella-uscita"


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# ------------------------------------------------------------ il figlio
def figlio(porta: int, db: str):
    """Il server vero, col config finto e le costanti strette."""
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
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
    import uvicorn
    # DELL'AVVIO SOLO LA SENTINELLA (la lezione del 2 nov, promozione
    # rossa): gli altri compiti d'avvio chiedono il cambio a CoinGecko e
    # lo storico dei prezzi, e la gabbia della CI ferma ogni uscita in
    # rete. Allo spegnimento solo il segnale `_SI_CHIUDE`, che e' quello
    # che la sentinella guarda.
    server.app.router.on_startup[:] = [server.avvia_sentinella]
    server.app.router.on_shutdown[:] = [server.ferma_i_giri_lunghi]
    server.SENTINELLA_PRIMO_S = 1
    server.SENTINELLA_OGNI_S = 1
    server.SENTINELLA_TETTO_S = 1
    server.SENTINELLA_USCITA_S = 3

    @server.app.get("/cartone/blocca")
    async def blocca_il_ciclo():
        time.sleep(30)        # IL GUASTO: il ciclo fermo, come il 17 nov
        return {"ok": True}

    # gli argomenti come li vede la sentinella in produzione
    sys.argv = ["uvicorn", "server:app", "--host", "127.0.0.1",
                "--port", str(porta)]
    uvicorn.run(server.app, host="127.0.0.1", port=porta,
                log_level="warning", timeout_graceful_shutdown=2)


# ------------------------------------------------------------- il padre
def porta_libera() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Processo:
    def __init__(self, porta, db):
        self.p = subprocess.Popen(
            [sys.executable, "-u", os.path.abspath(__file__), "--figlio",
             str(porta), db],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace")
        self.righe = []
        self.t = threading.Thread(target=self._leggi, daemon=True)
        self.t.start()

    def _leggi(self):
        for r in self.p.stdout:
            self.righe.append(r.rstrip("\n"))

    def testo(self):
        return "\n".join(self.righe)

    def aspetta_riga(self, pezzo, entro):
        fine = time.monotonic() + entro
        while time.monotonic() < fine:
            if pezzo in self.testo():
                return True
            if self.p.poll() is not None:
                time.sleep(0.3)
                return pezzo in self.testo()
            time.sleep(0.1)
        return False


def salute(porta, tetto=2.0):
    apri = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with apri.open(f"http://127.0.0.1:{porta}/api/salute",
                       timeout=tetto) as r:
            return r.status
    except Exception:
        return None


def aspetta_salute(porta, entro=60):
    fine = time.monotonic() + entro
    while time.monotonic() < fine:
        if salute(porta) == 200:
            return True
        time.sleep(0.3)
    return False


def main():
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-sentinella-"),
                      "usa-e-getta.db")
    segno = os.path.join(os.path.dirname(db), SEGNO)
    print(f"Database usa-e-getta: {db}")

    print("\n[1. il server parte e la sentinella si accende]")
    porta = porta_libera()
    uno = Processo(porta, db)
    try:
        prova("/api/salute risponde 200", True, aspetta_salute(porta))
        prova("la riga del journal dice accesa, con la porta degli "
              "argomenti", True,
              uno.aspetta_riga(f"🧊 Sentinella del server fermo: accesa — "
                               f"http://127.0.0.1:{porta}/api/salute", 10))

        print("\n[2-4. il ciclo si ferma: pila, poi uscita col 70]")
        apri = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        threading.Thread(target=lambda: _ignora(
            lambda: apri.open(f"http://127.0.0.1:{porta}/cartone/blocca",
                              timeout=40).read()), daemon=True).start()
        time.sleep(0.5)
        prova("col ciclo fermo /api/salute non risponde", None,
              salute(porta, 1.5))
        prova("la sentinella scrive la pila al primo silenzio", True,
              uno.aspetta_riga("🧊 Sentinella: /api/salute muta", 10))
        try:
            codice = uno.p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            codice = "ancora vivo dopo 20 s"
        time.sleep(0.5)
        prova("passato il tetto il processo esce da solo col 70", 70, codice)
        prova("prima di uscire lo dice", True,
              "esco e systemd mi rialza" in uno.testo())
        prova("nella pila c'e' la riga colpevole (la rotta che dorme)",
              True, "blocca_il_ciclo" in uno.testo())
        prova("...e il filo principale, non solo la sentinella", True,
              "Current thread" in uno.testo()
              or "Thread 0x" in uno.testo())
        prova("il segno dell'uscita sta accanto al database", True,
              os.path.exists(segno))
    finally:
        if uno.p.poll() is None:
            uno.p.kill()

    print("\n[5. il riavvio legge il segno e lo dice]")
    porta = porta_libera()
    due = Processo(porta, db)
    try:
        prova("il server rinasce", True, aspetta_salute(porta))
        prova("il journal dice che si era fermato", True,
              due.aspetta_riga("🧊 Sentinella: riavviato dopo un blocco", 10))
        prova("l'avviso agli admin parte (in collaudo si stampa)", True,
              due.aspetta_riga("Il server si era fermato", 10))
        prova("il segno e' cancellato: l'avviso non si ripete", False,
              os.path.exists(segno))

        print("\n[6. lo spegnimento normale non fa scattare niente]")
        time.sleep(2.5)          # almeno un colpo sano della sentinella
        due.p.send_signal(signal.SIGTERM)
        try:
            codice = due.p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            codice = "ancora vivo dopo 20 s"
        # uvicorn, finito lo spegnimento dolce, rilancia il segnale che
        # l'ha fermato: -15 e' l'uscita pulita di oggi, 0 quella di ieri
        prova("SIGTERM: esce pulito entro 20 s, mai col 70", True,
              codice in (0, -signal.SIGTERM))
        prova("nessuna pila allo spegnimento", False,
              "🧊 Sentinella: /api/salute muta" in due.testo())
        prova("nessun segno nuovo", False, os.path.exists(segno))
    finally:
        if due.p.poll() is None:
            due.p.kill()

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    if FALLITE:
        print("\n--- l'uscita del primo server ---")
        print(uno.testo()[-4000:])
        print("--- l'uscita del secondo server ---")
        print(due.testo()[-3000:])
    return 1 if FALLITE else 0


def _ignora(f):
    try:
        f()
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--figlio":
        figlio(int(sys.argv[2]), sys.argv[3])
    else:
        sys.exit(main())
