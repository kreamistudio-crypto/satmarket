#!/usr/bin/env python3
"""IL GIUDICE DEL DEPLOY: «la CI e' verde SU QUESTO COMMIT?» (set 2026).

Lo chiama `deploy.sh` sul VPS PRIMA di tirare un commit, ed e' la meta'
in Python dei suoi controlli (le altre — sta su main, va solo in avanti,
la firma — sono due righe di git e stanno nello script).

PERCHE' ESISTE. Fino al 21 set 2026 «la CI e' verde» era scritta nel
fatto stesso che il ref `pronto` si fosse mosso: lo alza solo il job
`pronto`, e solo a prove verdi. Era vero finche' a muoverlo era la CI —
ma il repo e' privato su un piano gratuito, il ramo non si puo'
proteggere, e chiunque abbia scrittura fa `git push origin
qualunque:pronto` senza che la CI giri nemmeno (audit del 19 set, G2).
Un ref che chiunque puo' spostare non dimostra niente: la domanda va
FATTA, a chi la CI l'ha girata davvero.

COSA CHIEDE, e a chi: alle Actions di GitHub, i giri del workflow
`prove.yml` per quel commit esatto. Ne vale uno solo: nato da un PUSH
SU MAIN (un giro verde su un ramo di lato non conta: il workflow di un
ramo lo scrive chi ha il ramo), con i due lavori `prove` e `segreti`
finiti in `success`. Sono gli stessi due che il semaforo aspetta
(`needs: [prove, segreti]`), e una prova in prove.py li tiene legati.

QUEL CHE NON FERMA, detto qui perche' non lo si creda: chi sa scrivere
su MAIN scrive anche il workflow, e un workflow riscritto e' verde
quanto vuole. Questo giudice ferma il push di lato e il commit rosso;
contro un account GitHub compromesso regge solo la FIRMA, che GitHub
non possiede (vedi deploy.sh, «LA FIRMA»).

TRE VERDETTI, e il terzo e' la ragione del file:
  si       (esce 0)  — si tira;
  no       (esce 10) — la CI ha detto rosso: rifiutato, e non si riprova;
  aspetta  (esce 20) — non si sa ANCORA (la CI gira, GitHub non
                       risponde, il token non apre): non si tira e si
                       riprova al giro dopo. Nel dubbio non si tira MAI:
                       qualunque altro codice d'uscita, un crash
                       compreso, deploy.sh lo legge come «aspetta».
Sulla prima riga dell'uscita c'e' il motivo, in parole.

IL TOKEN e' quello con cui il VPS fa gia' `git fetch`: si chiede a git
(`git credential fill`), cosi' ce n'e' UNO in UN posto. Non passa mai da
un argomento ne' da una variabile d'ambiente (li vede `ps`), e non
finisce mai nell'uscita: ogni riga stampata passa da `_senza_token`.
Deve saper LEGGERE e basta — fine-grained, solo questo repo,
«Contents: Read-only» e «Actions: Read-only». Come si controlla sta in
docs/PRODUZIONE.md, «IL TOKEN DEL VPS».

Uso:
    python3 giudice_deploy.py ci <sha di 40 caratteri>
    python3 giudice_deploy.py token      che token e', senza mostrarlo

Solo libreria standard, come i tre heredoc di deploy.sh: gira col
python di sistema, senza il venv del servizio.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

SI, NO, ASPETTA = "si", "no", "aspetta"
USCITE = {SI: 0, NO: 10, ASPETTA: 20}

API = "https://api.github.com"
WORKFLOW = ".github/workflows/prove.yml"
RAMO_MAIN = "main"
# gli stessi due del `needs:` del semaforo, e una prova li tiene legati
LAVORI_RICHIESTI = ("prove", "segreti")
ATTESA_S = 15


# ----------------------- i giudici, puri -----------------------------

def repo_da_url(url: str) -> str:
    """«proprietario/repo» dall'URL del remoto, o '' se non e' GitHub.
    Le credenziali dentro l'URL (https://utente:token@...) si saltano."""
    m = re.search(r"github\.com[:/]+([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
                  (url or "").strip())
    return f"{m.group(1)}/{m.group(2)}" if m else ""


def token_da_credenziali(testo: str) -> str:
    """La riga `password=` della risposta di `git credential fill`."""
    for riga in (testo or "").splitlines():
        if riga.startswith("password="):
            return riga[len("password="):].strip()
    return ""


def token_da_url(url: str) -> str:
    """Il ripiego: il token scritto DENTRO l'URL del remoto
    (https://token@github.com/... o https://utente:token@github.com/...).
    Non e' il posto giusto per un token, ma se sta li' e' quello che
    git usa — e allora e' quello da chiedere di controllare."""
    m = re.match(r"https://([^/@]+)@github\.com/", (url or "").strip())
    if not m:
        return ""
    return m.group(1).split(":", 1)[-1]


def sha_valido(sha: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{40}", sha or ""))


def giri_di_main(risposta: dict, sha: str) -> list:
    """I soli giri che contano: QUEL commit, QUEL workflow, nati da un
    PUSH SU MAIN. Un giro dello stesso commit su un altro ramo non
    entra: il workflow di un ramo lo scrive chi ha il ramo."""
    return [g for g in ((risposta or {}).get("workflow_runs") or [])
            if g.get("head_sha") == sha
            and g.get("path") == WORKFLOW
            and g.get("event") == "push"
            and g.get("head_branch") == RAMO_MAIN]


def giudica_lavori(lavori: list, giro_finito: bool) -> tuple:
    """(verdetto, motivo) per UN giro, dai suoi lavori. Passa solo
    `success`: `skipped` e `cancelled` non sono un verde. Un lavoro che
    MANCA a giro finito e' un no — e' il workflow a cui qualcuno ha
    tolto una delle due domande."""
    for nome in LAVORI_RICHIESTI:
        suoi = [l for l in (lavori or []) if l.get("name") == nome]
        if not suoi:
            if giro_finito:
                return NO, f"nella CI di questo commit manca «{nome}»"
            return ASPETTA, f"la CI non ha ancora aperto «{nome}»"
        for l in suoi:
            if l.get("status") != "completed":
                return ASPETTA, f"la CI sta ancora girando («{nome}»)"
            if l.get("conclusion") != "success":
                return NO, (f"la CI e' rossa: «{nome}» e' finito "
                            f"{l.get('conclusion') or 'senza esito'}")
    return SI, "la CI e' verde su main per questo commit"


def somma_verdetti(verdetti: list) -> tuple:
    """Piu' giri per lo stesso commit sono rari (un giro rilanciato
    resta lo stesso giro). Basta un si'; senno' un dubbio resta un
    dubbio; e' no solo se TUTTI dicono no."""
    if not verdetti:
        return ASPETTA, ("nessun giro della CI su main per questo commit "
                         "(non ancora partito, o mai esistito)")
    for cercato in (SI, ASPETTA, NO):
        for verdetto, motivo in verdetti:
            if verdetto == cercato:
                return verdetto, motivo
    return ASPETTA, "verdetto illeggibile"


def motivo_http(codice: int) -> str:
    """Le parole per un rifiuto di GitHub. Tutti «aspetta»: nessuno di
    questi dice che il COMMIT e' cattivo, dicono che non si riesce a
    chiedere — e chi legge l'avviso deve sapere cosa toccare."""
    if codice == 401:
        return "GitHub rifiuta il token del VPS (401): scaduto o revocato?"
    if codice in (403, 404):
        return (f"il token del VPS non puo' leggere le Actions ({codice}): "
                "gli serve «Actions: Read-only» — o e' finito il tetto "
                "delle richieste")
    return f"GitHub ha risposto {codice}"


def descrivi_token(token: str, scopes) -> str:
    """Che token e', SENZA mostrarlo. `scopes` e' l'intestazione
    X-OAuth-Scopes (None se la richiesta non e' riuscita): i token
    classici la portano e dice cosa sanno fare; i fine-grained no, e
    per loro la parola finale sta sulla pagina di GitHub e nel
    `git push --dry-run` di PRODUZIONE."""
    if not token:
        return "nessun token trovato: ne' da git credential ne' nell'URL"
    if token.startswith("github_pat_"):
        return ("fine-grained (github_pat_…): bene. I permessi si leggono "
                "SOLO sulla pagina del token su GitHub: devono essere "
                "«Contents: Read-only» e «Actions: Read-only», su questo "
                "solo repo")
    larghi = sorted(s.strip() for s in (scopes or "").split(",") if s.strip())
    if scopes is None:
        return "token classico o di altro tipo: GitHub non ha detto gli scope"
    if any(s in ("repo", "public_repo", "workflow", "write:packages",
                 "admin:org", "delete_repo") for s in larghi):
        return ("⚠️ token CLASSICO con scope " + ", ".join(larghi) +
                ": SA SCRIVERE sul repo. Va sostituito con un fine-grained "
                "in sola lettura")
    return "token classico, scope: " + (", ".join(larghi) or "nessuno")


def _senza_token(testo: str, token: str) -> str:
    """La cintura: qualunque cosa si stampi, il token non c'e'."""
    testo = str(testo)
    if token and len(token) >= 8:
        testo = testo.replace(token, "«token»")
    return re.sub(r"(gh[pousr]_|github_pat_)[A-Za-z0-9_]{8,}", "«token»",
                  testo)


# ----------------------- il mondo, intorno ---------------------------

def _git(*argomenti, entra: str = "") -> str:
    ambiente = dict(os.environ, GIT_TERMINAL_PROMPT="0",
                    GCM_INTERACTIVE="never")
    try:
        r = subprocess.run(("git",) + argomenti, input=entra, text=True,
                           capture_output=True, timeout=20, env=ambiente)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def trova_token_e_repo() -> tuple:
    url = _git("config", "--get", "remote.origin.url").strip()
    token = token_da_credenziali(
        _git("credential", "fill",
             entra="protocol=https\nhost=github.com\n\n"))
    if not token:
        token = token_da_url(url)
    repo = os.environ.get("BARATTOLO_REPO", "").strip() or repo_da_url(url)
    return token, repo


def _chiedi(percorso: str, token: str) -> tuple:
    """(codice, corpo, intestazioni) — codice 0 se GitHub non risponde."""
    base = os.environ.get("BARATTOLO_API", "").strip() or API   # il banco
    richiesta = urllib.request.Request(base + percorso, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "barattolo-deploy"})
    try:
        with urllib.request.urlopen(richiesta, timeout=ATTESA_S) as r:
            return r.status, json.loads(r.read().decode("utf-8")), r.headers
    except urllib.error.HTTPError as e:
        return e.code, {}, e.headers
    except Exception:
        return 0, {}, {}


def giudica_ci(sha: str, token: str, repo: str, chiedi=_chiedi) -> tuple:
    if not sha_valido(sha):
        return ASPETTA, "lo sha da giudicare non e' uno sha"
    if not repo:
        return ASPETTA, "non so quale repo chiedere a GitHub"
    if not token:
        return ASPETTA, "sul VPS non trovo il token per chiedere a GitHub"
    codice, corpo, _ = chiedi(
        f"/repos/{repo}/actions/runs?head_sha={sha}&per_page=100", token)
    if codice == 0:
        return ASPETTA, "GitHub non risponde"
    if codice != 200:
        return ASPETTA, motivo_http(codice)
    verdetti = []
    for giro in giri_di_main(corpo, sha):
        codice, lavori, _ = chiedi(
            f"/repos/{repo}/actions/runs/{giro.get('id')}/jobs"
            "?filter=latest&per_page=100", token)
        if codice != 200:
            verdetti.append((ASPETTA, motivo_http(codice) if codice
                             else "GitHub non risponde"))
            continue
        verdetti.append(giudica_lavori(lavori.get("jobs") or [],
                                       giro.get("status") == "completed"))
    return somma_verdetti(verdetti)


def main(argv: list) -> int:
    # sotto systemd l'ambiente nasce quasi vuoto (la lezione di HOME):
    # senza LANG l'uscita potrebbe non essere UTF-8, e il motivo porta
    # «» ed e' — che finiscono in un avviso Telegram
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(argv) == 3 and argv[1] == "ci":
        token, repo = trova_token_e_repo()
        verdetto, motivo = giudica_ci(argv[2], token, repo)
        print(_senza_token(motivo, token))
        return USCITE[verdetto]
    if len(argv) == 2 and argv[1] == "token":
        token, repo = trova_token_e_repo()
        scopes = None
        if token:
            codice, _, intestazioni = _chiedi("/rate_limit", token)
            if codice == 200:
                scopes = intestazioni.get("X-OAuth-Scopes") or ""
        print(_senza_token(f"repo: {repo or '?'}\n"
                           + descrivi_token(token, scopes), token))
        return 0
    print(__doc__.split("Uso:")[1].split("Solo libreria")[0].strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
