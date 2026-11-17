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

L'ELENCO NON STA QUI: sta in `ci/collaudi.txt`, scritto a mano, uno per
riga. Entra solo un collaudo che e' stato GUARDATO — niente rete, nessun
config vero, stesso esito a ogni giro — e un collaudo nuovo non ci
finisce da solo per il fatto di chiamarsi `collaudo_*`.
FINO AL 13 OTT 2026 STAVA NEL WORKFLOW, e non ci deve tornare: ogni
collaudo nuovo cambiava `.github/workflows/prove.yml`, e dopo un commit
che tocca il workflow GitHub non lascia al robot spostare `pronto`
(«refusing to allow a GitHub App to create or update workflow»): il
deploy restava fermo finche' Andrea non lo spostava a mano. Adesso il
workflow dice solo `--elenco ci/collaudi.txt`, e un collaudo nuovo e'
una riga la'.

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

Uso:  python collaudi_ci.py --elenco ci/collaudi.txt     (quel che fa la CI)
      python collaudi_ci.py collaudo_porta_timer collaudo_... [...]
Opzioni (16 ott 2026, la CI leggera; senza, si gira come sempre):
      --paralleli N                 N collaudi alla volta (la CI: 2)
      --salvo-solo-documenti-da R   niente collaudi se HEAD differisce
                                    dal ramo R di origin solo per dei .md;
                                    e dal 17 nov solo i collaudi che VEDONO
                                    i file cambiati (`scegli_collaudi`; il
                                    nome resta per non toccare il workflow)
"""
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# stesso, e il «‼» dei due collaudi dell'AI (collaudo_impersonazione e
# collaudo_ricategorizza: la loro riga e' «✗ [atteso | detto] titolo», e
# «‼» e' lo sbaglio GRAVE — un annuncio legittimo bloccato, un annuncio
# spostato male). Un Traceback e' rosso a parte: si prende il blocco intero.
SEGNI_ROSSI = ("✗", "‼", "NO ", "[NO]", "[KO]", "FAIL", "⛔")
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


# LA FORMA DI UN NOME NELL'ELENCO: un collaudo, senza `.py`
FORMA_NOME = re.compile(r"collaudo_\w+")


def leggi_elenco(percorso):
    """L'ELENCO DEI COLLAUDI, dal suo file (13 ott 2026): `ci/collaudi.txt`.

    Una riga, un nome. Il `#` apre un commento (anche in coda a una
    riga), le righe vuote non contano. `fuori: collaudo_x` dichiara un
    collaudo che la CI NON gira. Torna (dentro, fuori, storte): le
    storte sono le righe che non hanno la forma di un nome, e chi chiama
    si deve FERMARE — una riga storta saltata in silenzio e' un collaudo
    che smette di girare senza che nessuno lo sappia."""
    dentro, fuori, storte = [], [], []
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            r = riga.split("#")[0].strip()
            if not r:
                continue
            lista = dentro
            if r.startswith("fuori:"):
                lista, r = fuori, r[len("fuori:"):].strip()
            (lista if FORMA_NOME.fullmatch(r) else storte).append(r)
    return dentro, fuori, storte


# ------------- LA CI LEGGERA (16 ott 2026, cantiere ci-leggera) ------
# Due leve, tutte e due di QUANDO e COME girano i collaudi, mai di COSA:
# l'elenco resta quello, la gabbia resta quella, e un collaudo rosso
# ferma il deploy come prima. Il perche' e i numeri: docs/CANTIERI.md,
# «La CI leggera».

# Il commit di soli documenti: i collaudi girano il SERVER, e il server
# non legge nessun .md (verificato il 16 ott: in server.py e nei
# collaudi i .md compaiono solo nei commenti). Le sezioni di prove.py
# che leggono i documenti girano TUTTE lo stesso, perche' prove.py non
# si tocca. Solo `.md`: un .txt, un .json o uno script accanto ai
# documenti fanno girare tutto.
FORMA_DOCUMENTO = re.compile(r".+\.md")


def solo_documenti(cambiati):
    """Vero solo se c'e' almeno un file cambiato e sono TUTTI .md.

    L'elenco VUOTO non e' «solo documenti»: vuol dire lo stesso albero
    di `pronto`, cioe' un giro rifatto a mano (un rosso a caso da
    ricontrollare), e chi rifà un giro lo vuole intero. None (il
    confronto non e' riuscito) gira tutto, sempre."""
    return bool(cambiati) and all(FORMA_DOCUMENTO.fullmatch(n)
                                  for n in cambiati)


def cambiati_da(base):
    """I file in cui l'albero di HEAD differisce da quello di `base`
    (un ramo di origin: in CI `pronto`). None se qualunque passo non
    riesce — e None vuol dire girare TUTTO.

    IL CONFRONTO E' CON `pronto` E NON COL PUSH DI PRIMA, ed e' il
    pezzo da non cambiare: con la coda della CI un giro in attesa puo'
    essere sostituito dal successivo e non girare mai. Se il commit
    saltato toccava il codice e quello dopo solo i documenti, il diff
    col push di prima direbbe «solo documenti» e il codice nuovo
    andrebbe in produzione senza un collaudo. `pronto` invece e' per
    costruzione l'ultimo albero passato col giro intero (o con un giro
    di soli documenti sopra un albero passato intero): quel che ne
    differisce solo per dei .md ha lo stesso codice gia' collaudato.
    Si confrontano gli ALBERI, non la storia: il checkout della CI e'
    corto, e basta la punta di `pronto` (--depth=1)."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", base or ""):
        return None
    locale = f"refs/remotes/origin/{base}"
    try:
        f = subprocess.run(["git", "fetch", "--quiet", "--depth=1", "origin",
                            f"+refs/heads/{base}:{locale}"],
                           cwd=QUI, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=120)
        if f.returncode != 0:
            return None
        d = subprocess.run(["git", "diff", "--name-only", "--no-renames",
                            locale, "HEAD"],
                           cwd=QUI, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if d.returncode != 0:
        return None
    return [r for r in d.stdout.splitlines() if r.strip()]


# ------------- I COLLAUDI SCELTI DAI FILE (17 nov 2026, cantiere ci-mirata)
# Andrea: «le CI sono decisamente troppo lente, quelle inutili devono
# essere saltate». Oltre ai soli documenti, adesso si saltano i collaudi
# che NON POSSONO vedere i file cambiati da `pronto`. Il criterio e'
# volutamente grosso, perche' un collaudo gira il SERVER VERO da cima a
# fondo e una funzione toccata non dice quali flussi attraversa:
# - un collaudo «vede» un file se lo importa (anche passando per un
#   altro collaudo o per il server, a qualunque profondita'), oppure se
#   il file e' NOMINATO nel testo di quel che importa (il nome, il
#   percorso, il modulo fra virgolette, la sua cartella fra virgolette:
#   cosi' si prendono anche le pagine servite, le letture e i
#   sottoprocessi). Quasi tutti importano server.py, quindi server.py e
#   ogni file che server.py nomina (miniapp.html, sw.js, vendor/...)
#   fanno girare TUTTO, come oggi;
# - fanno girare TUTTO anche i file che cambiano l'AMBIENTE di tutti:
#   il lanciatore stesso, il workflow, requirements.txt, il config
#   d'esempio; e un file sparito (chi lo leggeva ora esplode);
# - l'elenco (`ci/collaudi.txt`) fa girare i soli nomi NUOVI rispetto a
#   `pronto`; se l'elenco di `pronto` non si legge, tutto;
# - i .md restano fuori come dal 16 ott.
# Restano saltati, per esempio, i commit di soli prove.py, deploy/,
# estensione/, documenti e disegni che il server non nomina. Nel dubbio
# (un import che non si legge, un confronto non riuscito), TUTTO.
SEMPRE_TUTTO = ("collaudi_ci.py", "requirements.txt", "config_esempio.py")
CARTELLE_SEMPRE_TUTTO = (".github/",)


def _moduli_locali(testo, esiste):
    """I file del repo che `testo` importa (import e from, a ogni
    livello del file, anche dentro una funzione). None se non si legge
    come Python: chi chiama gira tutto."""
    import ast
    try:
        albero = ast.parse(testo)
    except (SyntaxError, ValueError):
        return None
    nomi = set()
    for n in ast.walk(albero):
        if isinstance(n, ast.Import):
            nomi.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            nomi.add(n.module)
            nomi.update(f"{n.module}.{a.name}" for a in n.names)
    out = set()
    for nome in nomi:
        base = nome.replace(".", "/")
        for cand in (base + ".py", base + "/__init__.py"):
            if esiste(cand):
                out.add(cand)
    return out


def senza_commenti(testo):
    """Il Python senza i commenti e senza le docstring: un «vedi
    prove.py» in un commento del server non vuol dire che il server
    legga prove.py (e nemmeno un `-- prove.py` nello schema SQL di una
    stringa). Restano il codice e le stringhe vere (i nomi dei
    file serviti, letti, lanciati). Se non si legge, il testo intero:
    una menzione in piu', mai una in meno."""
    import io
    import tokenize
    fuori, prima = [], tokenize.NEWLINE
    try:
        for t in tokenize.generate_tokens(io.StringIO(testo).readline):
            if t.type == tokenize.COMMENT:
                continue
            if t.type == tokenize.STRING and prima in (
                    tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                    tokenize.DEDENT):
                prima = t.type  # una docstring (o una stringa da sola)
                continue
            if t.type not in (tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
                              tokenize.NEWLINE) or t.type == tokenize.NEWLINE:
                prima = t.type
            fuori.append(t.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return testo
    # ...e i commenti dell'SQL dentro le stringhe (`-- ...` a inizio riga)
    return re.sub(r"(?m)^\s*--.*$", "", " ".join(fuori))


def _nominato(testo, percorso, esiste=lambda p: False):
    """Vero se `testo` nomina il file: il percorso, il nome del file, il
    modulo fra virgolette, o una sua cartella fra virgolette. Il solo
    nome non basta quando in cima al repo c'e' un file che si chiama
    uguale (estensione/manifest.json e manifest.json): li' serve il
    percorso."""
    nome = percorso.rsplit("/", 1)[-1]
    if percorso in testo:
        return True
    if (nome == percorso or not esiste(nome)) and nome in testo:
        return True
    if nome.endswith(".py") and re.search(
            r"""["']%s["']""" % re.escape(nome[:-3]), testo):
        return True
    parti = percorso.split("/")[:-1]
    for k in range(1, len(parti) + 1):
        cartella = "/".join(parti[:k])
        if re.search(r"""["']%s(?:/|["'])""" % re.escape(cartella), testo):
            return True
    return False


def scegli_collaudi(cambiati, nomi, elenco, leggi, esiste, nomi_base):
    """IL GIUDICE, senza git dentro (cosi' si prova). `cambiati` i file
    diversi da `pronto` (non vuoto, non solo .md: quelli li guarda gia'
    `solo_documenti`), `nomi` i collaudi dell'elenco, `elenco` il suo
    percorso, `leggi(p)` il testo di un file del repo, `esiste(p)`,
    `nomi_base` l'elenco di `pronto` (None se non si legge).
    Torna (scelti, perche'): scelti None vuol dire TUTTI."""
    perche = []
    resto = [f for f in cambiati if not FORMA_DOCUMENTO.fullmatch(f)]
    for f in resto:
        if f in SEMPRE_TUTTO or f.startswith(CARTELLE_SEMPRE_TUTTO):
            return None, [f"{f}: cambia l'ambiente di tutti → tutti"]
        if f != elenco and not esiste(f):
            return None, [f"{f}: sparito → tutti"]
    scelti = set()
    if elenco in resto:
        if nomi_base is None:
            return None, [f"{elenco}: l'elenco di prima non si legge → tutti"]
        nuovi = [n for n in nomi if n not in set(nomi_base)]
        scelti.update(nuovi)
        perche.append(f"{elenco}: " + (", ".join(nuovi) + " nuovi"
                                       if nuovi else "nessun nome nuovo"))
        resto = [f for f in resto if f != elenco]
    if not resto:
        return [n for n in nomi if n in scelti], perche
    # chi vede chi: ogni collaudo con quel che importa, a ogni profondita'
    cache_testo, cache_import = {}, {}

    def testo(p):
        if p not in cache_testo:
            cache_testo[p] = leggi(p)
        return cache_testo[p]

    cache_codice = {}

    def codice(p):
        if p not in cache_codice:
            cache_codice[p] = (senza_commenti(testo(p)) if p.endswith(".py")
                               else testo(p))
        return cache_codice[p]

    def importa(p):
        if p not in cache_import:
            cache_import[p] = _moduli_locali(testo(p), esiste)
        return cache_import[p]

    cache_nomina = {}

    def nomina(p, f):
        if (p, f) not in cache_nomina:
            cache_nomina[p, f] = _nominato(codice(p), f, esiste)
        return cache_nomina[p, f]

    nominati = {}
    for nome in nomi:
        visti, coda = set(), [nome + ".py"]
        while coda:
            p = coda.pop()
            if p in visti:
                continue
            visti.add(p)
            try:
                dentro = importa(p)
            except OSError:
                return None, perche + [f"{p}: non si legge → tutti"]
            if dentro is None:
                return None, perche + [f"{p}: non si legge come Python → tutti"]
            coda.extend(dentro - visti)
        for f in resto:
            if f in visti or any(nomina(p, f) for p in visti):
                nominati.setdefault(f, set()).add(nome)
    for f in resto:
        chi = nominati.get(f, set())
        scelti |= chi
        perche.append(f"{f}: " + ("tutti" if len(chi) == len(nomi) else
                                  f"{len(chi)} collaudi" if chi else
                                  "nessun collaudo lo vede"))
    if len(scelti) == len(nomi):
        return None, perche
    return [n for n in nomi if n in scelti], perche


def nomi_elenco_da(base, elenco):
    """I collaudi dell'elenco com'era su `base` (gia' preso da
    `cambiati_da`), o None se non si legge."""
    try:
        r = subprocess.run(["git", "show",
                            f"refs/remotes/origin/{base}:{elenco}"],
                           cwd=QUI, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    dentro = []
    for riga in r.stdout.splitlines():
        x = riga.split("#")[0].strip()
        if x and not x.startswith("fuori:"):
            dentro.append(x)
    return dentro


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


def togli_opzioni(argv):
    """Le due opzioni della CI leggera, tolte da argv ovunque stiano.
    Torna (paralleli, base, resto) oppure None se un'opzione e' storta
    — e chi chiama si FERMA: un «--paralleli due» ignorato in silenzio
    girerebbe in un modo diverso da quello scritto."""
    paralleli, base, resto = 1, None, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--paralleli", "--salvo-solo-documenti-da"):
            if i + 1 >= len(argv):
                return None
            v = argv[i + 1]
            if a == "--paralleli":
                if not v.isdigit() or not 1 <= int(v) <= 16:
                    return None
                paralleli = int(v)
            else:
                base = v
            i += 2
            continue
        resto.append(a)
        i += 1
    return paralleli, base, resto


def racconta(nome, ok, secondi, uscita, bussate):
    """Il blocco di un collaudo finito: la riga, e se e' rosso la coda,
    le righe rosse e le annotazioni. Lo stampa un filo solo (il
    principale), quindi due collaudi in parallelo non si mescolano."""
    segno = "✓" if ok else "✗"
    print(f"{segno} {nome}  ({secondi:.0f}s)", flush=True)
    if ok:
        return
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
    print(f"::error::{nome} e' rosso", flush=True)


def main(nomi):
    # la console di Windows parla cp1252, e una ✓ la farebbe esplodere
    sys.stdout.reconfigure(encoding="utf-8")
    opzioni = togli_opzioni(nomi)
    if opzioni is None:
        print("::error::opzione storta: --paralleli vuole un numero da 1 a "
              "16, --salvo-solo-documenti-da il nome di un ramo")
        return 2
    paralleli, base, nomi = opzioni
    elenco = None
    if nomi[:1] == ["--elenco"]:
        # DAL FILE, che e' quel che fa la CI. Un elenco che non si
        # legge, vuoto o con una riga storta e' ROSSO, mai «0 verdi, 0
        # rossi»: un giro che non gira niente non deve sembrare verde.
        if len(nomi) != 2:
            print("Uso: python collaudi_ci.py --elenco ci/collaudi.txt")
            return 2
        elenco = nomi[1].replace("\\", "/")
        try:
            nomi, _fuori, storte = leggi_elenco(nomi[1])
        except OSError as e:
            print(f"::error::l'elenco dei collaudi non si legge: {e}")
            return 2
        for r in storte:
            print(f"::error::riga storta nell'elenco dei collaudi: «{r}»")
        if storte:
            return 2
        if not nomi:
            print("::error::l'elenco dei collaudi e' vuoto: non gira niente")
            return 2
    if not nomi:
        print("Uso: python collaudi_ci.py --elenco ci/collaudi.txt\n"
              "     python collaudi_ci.py collaudo_uno collaudo_due ...")
        return 2
    if base is not None:
        cambiati = cambiati_da(base)
        if solo_documenti(cambiati):
            # si dice, e si dice QUALI: un salto muto sembrerebbe un
            # giro verde, ed e' la cosa che un «verde» non deve mai fare
            print(f"⏭ rispetto a `{base}` sono cambiati solo documenti "
                  f"({len(cambiati)} file .md): i {len(nomi)} collaudi "
                  "non girano, perche' il codice e' quello gia' collaudato. "
                  "prove.py e i segreti girano interi.")
            print("\n".join("    " + n for n in cambiati[:30]))
            print(f"::notice::collaudi saltati: rispetto a {base} solo "
                  f"documenti ({len(cambiati)} file .md)")
            return 0
        if not cambiati:
            print(f"rispetto a `{base}`: "
                  + ("confronto non riuscito, si gira tutto" if cambiati is None
                     else "lo stesso albero, si gira tutto"), flush=True)
        else:
            def leggi(p):
                with open(os.path.join(QUI, p), encoding="utf-8",
                          errors="replace") as f:
                    return f.read()
            scelti, perche = scegli_collaudi(
                cambiati, nomi, elenco, leggi,
                lambda p: os.path.isfile(os.path.join(QUI, p)),
                nomi_elenco_da(base, elenco) if elenco else None)
            print(f"rispetto a `{base}`: {len(cambiati)} file")
            print("\n".join("    " + r for r in perche[:40]))
            if scelti is None:
                print("si gira tutto", flush=True)
            elif not scelti:
                print(f"⏭ nessuno dei {len(nomi)} collaudi vede i file "
                      "cambiati: non gira niente. prove.py e i segreti "
                      "fanno la loro parte.")
                print(f"::notice::collaudi saltati: rispetto a {base} "
                      "nessun collaudo vede i file cambiati")
                return 0
            else:
                print(f"⏭ girano {len(scelti)} collaudi su {len(nomi)}, "
                      "quelli che vedono i file cambiati", flush=True)
                print(f"::notice::{len(scelti)} collaudi su {len(nomi)}: "
                      f"rispetto a {base} gli altri non vedono i file cambiati")
                nomi = scelti
    gabbia = tempfile.mkdtemp(prefix="gabbia-collaudi-")
    with open(os.path.join(gabbia, "sitecustomize.py"), "w",
              encoding="utf-8") as f:
        f.write(GABBIA)
    nomi = [n.removesuffix(".py") for n in nomi]

    def uno(nome):
        segni = os.path.join(gabbia, nome + ".segni")
        ok, secondi, uscita = gira(nome, gabbia, segni)
        bussate = (open(segni, encoding="utf-8").read().splitlines()
                   if os.path.exists(segni) else [])
        return nome, ok and not bussate, secondi, uscita, bussate

    rossi = []
    inizio = time.time()
    if paralleli == 1:
        finiti = map(uno, nomi)
    else:
        # IN PARALLELO (16 ott 2026): ogni collaudo e' gia' un processo
        # suo, col suo database usa-e-getta in una cartella temporanea e
        # il suo file di segni; i fili qui aspettano e basta. L'ordine in
        # cui si stampano e' quello in cui FINISCONO; il conto in fondo
        # e' lo stesso.
        print(f"(i collaudi girano {paralleli} alla volta)", flush=True)
        pool = ThreadPoolExecutor(max_workers=paralleli)
        finiti = (f.result() for f in
                  as_completed([pool.submit(uno, n) for n in nomi]))
    for nome, ok, secondi, uscita, bussate in finiti:
        racconta(nome, ok, secondi, uscita, bussate)
        if not ok:
            rossi.append(nome)
    print(f"\n{len(nomi) - len(rossi)} verdi, {len(rossi)} rossi"
          f"  (in {time.time() - inizio:.0f}s)")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
