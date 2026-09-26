#!/usr/bin/env bash
#
# IL DEPLOY DI BARATTOLO, dalla parte del VPS (ago 2026).
#
# Gira ogni minuto da un timer systemd, guarda se il ref `pronto` si e'
# mosso e in quel caso aggiorna il mercatino. Nel caso normale — cioe'
# quasi sempre — fa un `git fetch` e se ne va senza dire niente.
#
# LE CINQUE REGOLE, che sono il motivo per cui questo file esiste
# invece di un `git pull && systemctl restart` in un cron:
#
# 1) SI SEGUE `pronto`, NON `main`. Quel ref lo fa avanzare la CI
#    quando prove e controllo dei segreti sono verdi (vedi il job
#    `pronto` in .github/workflows/prove.yml): e' il CAMPANELLO che
#    dice «c'e' qualcosa da guardare». Un commit rosso resta su main e
#    il campanello non suona.
#
# 2) SI TIRA, NON SI VIENE SPINTI. Nessuna chiave di questa macchina
#    sta nei secret di GitHub. La direzione del deploy e' una decisione
#    di sicurezza, non di comodita'.
#
# 5) IL CAMPANELLO NON E' UNA PROVA (set 2026, audit G2 — il numero e'
#    l'ordine in cui e' arrivata, non quello in cui gira: gira PRIMA
#    di tutto il resto). Fino al 21 set qui c'era scritto che «la CI
#    e' passata» stava nel fatto stesso che il ref si fosse mosso. Era
#    vero finche' a muoverlo era la CI: ma il repo e' privato su un
#    piano gratuito, i rami non si possono proteggere, e chiunque
#    abbia scrittura fa `git push origin qualunque:pronto` senza che
#    la CI giri nemmeno. E questo script ESEGUE quel che tira. Quindi
#    un commit si tira solo se, giudicato DA QUI:
#      a) sta su main (e' antenato di origin/main);
#      b) va IN AVANTI rispetto a quel che gira (niente ritorni a una
#         versione vecchia, niente storia riscritta);
#      c) la punta e' FIRMATA da una chiave scritta in un file di
#         QUESTA macchina — o, finche' quel file non c'e', ha almeno un
#         autore dei nostri, che e' una cintura di cartone (vedi sotto);
#      d) la CI e' verde SU DI LUI, chiesto a GitHub col token di sola
#         lettura di questa macchina (giudice_deploy.py).
#    Se uno fallisce NON SI TIRA, si scrive nel journal e si avvisano
#    i moderatori: «⛔ Deploy rifiutato». Nel dubbio — GitHub muto, la
#    CI che gira ancora — si ASPETTA, e dopo dieci minuti lo si dice.
#    IL GIUDICE E' SEMPRE QUELLO DI PRIMA: a giudicare un commit e' lo
#    script gia' in produzione, mai quello che il commit porta con se'.
#
# 3) SI TORNA INDIETRO DA SOLI. Dopo il riavvio si chiede a
#    /api/salute — che tocca il database, non solo il processo — e se
#    non risponde entro il tempo dato si rimette il commit di prima e
#    si riavvia ancora. Il mercatino e' mono-processo: una virgola
#    sbagliata lo spegne, e nessuno deve restare a fissare il journal
#    per accorgersene.
#
# 4) SI DICE SEMPRE COM'E' ANDATA. Ogni deploy — riuscito, fallito o
#    tornato indietro — finisce nel journal e in un messaggio ai
#    moderatori. Un aggiornamento che va in produzione in silenzio e'
#    un aggiornamento di cui nessuno sa la data.
#
# Uso a mano (utile per il primo giro e per il collaudo):
#     ./deploy.sh            aggiorna se c'e' qualcosa di nuovo
#     ./deploy.sh --forza    riapplica e riavvia anche se e' gia' in pari
#                            (e riprova un commit rifiutato o bocciato:
#                            il GIUDICE pero' non lo salta nemmeno lei)
#     ./deploy.sh --dimmi    guarda e basta, non tocca niente — e dice
#                            anche cosa ne pensa il giudice

set -uo pipefail

CARTELLA="${BARATTOLO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
SERVIZIO="${BARATTOLO_SERVIZIO:-barattolo}"
SALUTE="${BARATTOLO_SALUTE:-http://127.0.0.1:8080/api/salute}"
ATTESA="${BARATTOLO_ATTESA:-45}"     # secondi dati al server per rispondere
RAMO="${BARATTOLO_RAMO:-pronto}"
MAIN="${BARATTOLO_MAIN:-main}"
BACKUP_DA_TENERE=5
# LA FIRMA. Il file dei firmatari sta SU QUESTA MACCHINA e fuori dal
# repo, di root: e' l'unica meta' della regola che chi ha in mano
# GitHub non puo' riscrivere. Formato di ssh (`allowed_signers`), una
# riga per chiave: `andrea namespaces="git" ssh-ed25519 AAAA...`.
# Si guarda la sola PUNTA: chi firma la punta risponde di quel che c'e'
# sotto, ed e' il gesto «questo lo rilascio io». Finche' il file non
# c'e' (o e' vuoto) la firma NON si chiede, e ogni deploy lo dice.
FIRMATARI="${BARATTOLO_FIRMATARI:-/etc/barattolo-deploy/firmatari}"
# LA CINTURA DI CARTONE, per i giorni senza firme: l'autore della punta
# dev'essere uno di noi. In git l'autore e' TESTO LIBERO — lo scrive
# chiunque — quindi questa riga non ferma nessuno che sappia cosa fa:
# ferma il bot, la action di terzi, il commit arrivato da chissa' dove.
# La cura vera e' il file qui sopra.
NOSTRI="${BARATTOLO_AUTORI:-kreami.studio@gmail.com 62957276+alanbimbati@users.noreply.github.com}"
AVVISA_ATTESA_DOPO=600   # secondi di «aspetto» prima di dirlo a qualcuno

cd "$CARTELLA" || { echo "❌ non trovo $CARTELLA"; exit 1; }

dillo() { echo "[$(date '+%F %T')] $*"; }

# Il messaggio ai moderatori passa dal bot che c'e' gia': il token e
# gli id li legge dal config, che su questa macchina c'e' e nella repo
# non c'e' mai stato. Fail-open totale — un avviso che non parte non
# deve poter far fallire un deploy riuscito, ne' salvarne uno rotto.
avvisa() {
  python3 - "$1" <<'PY' 2>/dev/null || true
import sys, json, urllib.request
try:
    from config import BOT_TOKEN, ADMIN_IDS
except Exception:
    sys.exit(0)
for chat in ADMIN_IDS:
    try:
        urllib.request.urlopen(urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=json.dumps({"chat_id": chat, "text": sys.argv[1],
                             "parse_mode": "HTML",
                             "disable_web_page_preview": True}).encode(),
            headers={"Content-Type": "application/json"}), timeout=10)
    except Exception:
        pass
PY
}

# LE NOVITA' DEL DEPLOY, IN BREVE (26 set 2026): una riga per commit,
# solo il titolo, al massimo otto righe e poi «…e altri N». Prima qui
# c'era `git log --oneline | head -10`, e da noi il «titolo» di un
# commit e' il messaggio INTERO — un paragrafo solo, prove comprese —
# quindi l'avviso arrivava lungo come un verbale. Il titolo si taglia
# alla prima parentesi (la data: «Titolo (25 set 2026, ...)») o al
# primo punto, mai dentro un «...», e poi a circa 70 caratteri su uno
# spazio. Esce gia' scappato per l'HTML di Telegram. Fail-open come
# l'avviso: se git non risponde, le righe non ci sono e basta.
novita_brevi() {
  python3 - "$1" "$2" <<'PY' 2>/dev/null || true
import html, subprocess, sys

QUANTE = 8        # righe al massimo, poi «…e altri N»
LARGHEZZA = 70    # caratteri del titolo, circa: si taglia su uno spazio
PAROLINE = {"e", "o", "a", "di", "da", "in", "su", "con", "per", "tra", "fra",
            "il", "lo", "la", "i", "gli", "le", "un", "una", "uno", "del",
            "della", "dei", "delle", "nel", "nella", "al", "alla", "che"}

def primo_taglio(riga):
    """La prima parentesi o il primo punto FUORI dalle virgolette «»."""
    dentro = 0
    for i, c in enumerate(riga):
        if c == "«":
            dentro += 1
        elif c == "»":
            dentro = max(dentro - 1, 0)
        elif i and not dentro and riga[i - 1] == " " and c == "(":
            return i - 1
        elif i and not dentro and c == " " and riga[i - 1] == ".":
            return i - 1
    return len(riga)

def titolo(messaggio):
    riga = (messaggio.strip().splitlines() or [""])[0].strip()
    corto = riga[:primo_taglio(riga)].rstrip(" .,:;—-")
    riga = corto or riga
    if len(riga) > LARGHEZZA:
        pezzo = riga[:LARGHEZZA]
        if " " in pezzo[LARGHEZZA // 2:]:
            pezzo = pezzo.rsplit(" ", 1)[0]
        # e non si chiude dentro un «... lasciato aperto
        if pezzo.count("«") > pezzo.count("»") and pezzo.rfind("«") > LARGHEZZA // 2:
            pezzo = pezzo[:pezzo.rfind("«")].rstrip()
        # e non si chiude su «e il…»: via le paroline rimaste in coda
        parole = pezzo.split(" ")
        while len(parole) > 3 and parole[-1].lower() in PAROLINE:
            parole.pop()
        pezzo = " ".join(parole)
        riga = pezzo.rstrip(" .,:;—-") + "…"
    return riga or "(senza titolo)"

def novita(messaggi):
    righe = ["- " + html.escape(titolo(m), quote=False)
             for m in messaggi[:QUANTE]]
    altri = len(messaggi) - QUANTE
    if altri == 1:
        righe.append("…e un altro")
    elif altri > 1:
        righe.append(f"…e altri {altri}")
    return "\n".join(righe)

if __name__ == "__main__":
    uscita = subprocess.run(
        ["git", "--no-pager", "log", "-z", "--format=%B",
         f"{sys.argv[1]}..{sys.argv[2]}"],
        capture_output=True, encoding="utf-8", errors="replace")
    if uscita.returncode == 0:
        messaggi = [m for m in uscita.stdout.split("\0") if m.strip()]
        sys.stdout.reconfigure(encoding="utf-8")
        print(novita(messaggi))
PY
}

sta_bene() {
  # `--fail` o un 503 passerebbe per una risposta buona: la rotta
  # risponde 503 apposta quando il database non si apre, ed e' proprio
  # il caso che il rollback esiste per prendere.
  curl --fail --silent --show-error --max-time 5 "$SALUTE" >/dev/null 2>&1
}

aspetta_che_stia_bene() {
  local fine=$((SECONDS + ATTESA))
  while ((SECONDS < fine)); do
    sta_bene && return 0
    sleep 2
  done
  return 1
}

# le parole di un motivo finiscono in un messaggio HTML
scappa() { sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' <<<"$1"; }

# SI TIRANO TUTT'E DUE: `pronto` e' il campanello, `main` e' il metro
# con cui lo si misura. I refspec sono ESPLICITI: un clone nato
# `--single-branch` tirerebbe main senza scrivere origin/main, e il
# giudice misurerebbe contro un metro fermo al giorno del clone.
git fetch --quiet origin     "+refs/heads/$RAMO:refs/remotes/origin/$RAMO"     "+refs/heads/$MAIN:refs/remotes/origin/$MAIN" 2>/dev/null || {
  dillo "⚠️ git fetch non riuscito (rete? credenziali?): riprovo al giro dopo"
  exit 0
}

QUI="$(git rev-parse HEAD)"
LA="$(git rev-parse "origin/$RAMO" 2>/dev/null)" || {
  dillo "⚠️ il ramo «$RAMO» non esiste ancora su origin: la CI non l'ha mai alzato"
  exit 0
}

# IL GIUDICE (regola 5). Torna 0 = si tira, 10 = RIFIUTATO, 20 =
# ASPETTA; in MOTIVO le parole. L'ordine va dal controllo che costa
# meno a quello che esce in rete: un commit che non sta su main non
# merita nemmeno una domanda a GitHub. Non scrive niente su disco:
# lo chiama anche --dimmi.
MOTIVO=""
giudica() {
  local sha="$1" esito chi
  if ! git merge-base --is-ancestor "$sha" "origin/$MAIN" 2>/dev/null; then
    MOTIVO="${sha:0:8} non sta su $MAIN: qualcuno ha spostato «$RAMO» a mano"
    return 10
  fi
  if ! git merge-base --is-ancestor "$QUI" "$sha" 2>/dev/null; then
    MOTIVO="${sha:0:8} non viene DOPO ${QUI:0:8}, che e' quel che gira: un ritorno indietro o una storia riscritta"
    return 10
  fi
  if [[ -s "$FIRMATARI" ]]; then
    if ! git -c gpg.ssh.allowedSignersFile="$FIRMATARI" \
           verify-commit "$sha" >/dev/null 2>&1; then
      MOTIVO="${sha:0:8} non porta la firma di una chiave di $FIRMATARI"
      return 10
    fi
  else
    chi="$(git log -1 --format=%ae "$sha" 2>/dev/null)"
    case " $NOSTRI " in
      *" $chi "*) ;;
      *) MOTIVO="${sha:0:8} ha per autore «$chi», che non e' dei nostri"
         return 10 ;;
    esac
  fi
  MOTIVO="$(python3 giudice_deploy.py ci "$sha" 2>/dev/null)"
  esito=$?
  MOTIVO="${MOTIVO%%$'
'*}"          # la prima riga: il motivo
  case "$esito" in
    0)  return 0 ;;
    10) return 10 ;;
    *)  [[ -n "$MOTIVO" ]] || MOTIVO="il giudice della CI non ha risposto (uscito con $esito)"
        return 20 ;;
  esac
}

firme_dette() {
  [[ -s "$FIRMATARI" ]] && echo "firma richiesta ($FIRMATARI)" \
    || echo "⚠️ FIRME NON RICHIESTE: manca $FIRMATARI, vale solo l'autore"
}

if [[ "${1:-}" == "--dimmi" ]]; then
  dillo "qui: ${QUI:0:8}  ·  pronto: ${LA:0:8}  ·  $(firme_dette)"
  [[ "$QUI" == "$LA" ]] && dillo "in pari" || dillo "c'e' un aggiornamento"
  git --no-pager log --oneline "$QUI..$LA" 2>/dev/null | sed 's/^/    /'
  giudica "$LA"
  case $? in
    0)  dillo "⚖️ il giudice lo tirerebbe: $MOTIVO" ;;
    10) dillo "⛔ il giudice lo RIFIUTEREBBE: $MOTIVO" ;;
    *)  dillo "⏳ il giudice ASPETTEREBBE: $MOTIVO" ;;
  esac
  exit 0
fi

if [[ "$QUI" == "$LA" && "${1:-}" != "--forza" ]]; then
  exit 0                      # il caso normale: silenzio
fi

# IL FRENO, ed e' la riga senza la quale tutto il resto si rivolta:
# dopo un rollback il ref `pronto` resta avanti, quindi al giro dopo —
# fra un minuto — questo script riproverebbe lo STESSO commit rotto, e
# poi ancora, riavviando il mercatino ogni sessanta secondi per
# sempre. Un commit che ha fallito si prova UNA volta: per riprovarlo
# si spinge un commit nuovo (che e' anche quel che si dovrebbe fare)
# oppure si lancia questo script con --forza, a mano, guardando.
BOCCIATO="$(cat .deploy-bocciato 2>/dev/null || true)"
if [[ "$LA" == "$BOCCIATO" && "${1:-}" != "--forza" ]]; then
  exit 0
fi

# UN RIFIUTO SI DICE UNA VOLTA. Il ref resta dov'e', quindi senza
# questo timbro il giro dopo — fra un minuto — rigiudicherebbe lo
# stesso commit e riavviserebbe, ogni sessanta secondi. E' il freno di
# `.deploy-bocciato`, un passo prima.
RIFIUTATO="$(cat .deploy-rifiutato 2>/dev/null || true)"
if [[ "$LA" == "$RIFIUTATO" && "${1:-}" != "--forza" ]]; then
  exit 0
fi

giudica "$LA"
case $? in
  0) rm -f .deploy-attesa ;;
  10)
    dillo "⛔ deploy RIFIUTATO: $MOTIVO"
    echo "$LA" > .deploy-rifiutato
    rm -f .deploy-attesa
    avvisa "⛔ <b>Deploy rifiutato</b>: $(scappa "$MOTIVO")
Resta in produzione <code>${QUI:0:8}</code>. Non lo riprovo da solo: se e' un errore, si spinge un commit nuovo su main; se non lo e', qualcuno ha le mani sul repo."
    exit 1 ;;
  *)
    # ASPETTARE NON E' UN GUASTO — la CI che finisce, GitHub che
    # singhiozza — ma un'attesa che non finisce SI': e' il `git fetch`
    # muto dell'ago 2026, che lasciava il mercatino indietro per ore
    # mentre da fuori sembrava solo che non ci fosse niente di nuovo.
    # Si scrive la prima volta, e dopo dieci minuti lo si dice a
    # qualcuno, una volta sola.
    read -r A_SHA A_DA A_DETTO < .deploy-attesa 2>/dev/null || A_SHA=""
    ADESSO="$(date +%s)"
    if [[ "$A_SHA" != "$LA" ]]; then
      dillo "⏳ aspetto a tirare ${LA:0:8}: $MOTIVO"
      echo "$LA $ADESSO 0" > .deploy-attesa
    elif [[ "${A_DETTO:-0}" == "0" ]] && ((ADESSO - A_DA >= AVVISA_ATTESA_DOPO)); then
      dillo "⏳ ${LA:0:8} aspetta da $(((ADESSO - A_DA) / 60)) minuti: $MOTIVO"
      echo "$LA $A_DA 1" > .deploy-attesa
      avvisa "⏳ <b>Deploy fermo</b> da $(((ADESSO - A_DA) / 60)) minuti su <code>${LA:0:8}</code>: $(scappa "$MOTIVO")
Non tiro niente finche' non lo so. Resta in produzione <code>${QUI:0:8}</code>."
    fi
    exit 0 ;;
esac

NOVITA="$(novita_brevi "$QUI" "$LA")"
dillo "🚀 aggiornamento: ${QUI:0:8} → ${LA:0:8}  ·  $MOTIVO  ·  $(firme_dette)"

# IL DATABASE SI COPIA PRIMA, e si copia con l'API di sqlite invece che
# con `cp`: il server sta girando, e un file copiato a caldo mentre
# qualcuno scrive e' un file che al momento del bisogno non si apre.
# Non e' il backup giornaliero (quello vive per conto suo): e' la rete
# per i cinque minuti attorno al deploy, quando gira anche `init_db`
# con le sue migrazioni.
mkdir -p backup
chmod 700 backup     # dentro c'e' il database intero: solo root
python3 - "backup/pre-deploy-$(date +%Y%m%d-%H%M%S)-${QUI:0:8}.db" <<'PY' 2>/dev/null \
  && dillo "💾 copia del database messa da parte" \
  || dillo "⚠️ copia del database non riuscita: si va avanti lo stesso"
import sys, sqlite3
from config import DB
sorgente = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
destinazione = sqlite3.connect(sys.argv[1])
with destinazione:
    sorgente.backup(destinazione)
destinazione.close(); sorgente.close()
PY
ls -1t backup/pre-deploy-*.db 2>/dev/null | tail -n +$((BACKUP_DA_TENERE + 1)) \
  | xargs -r rm -f

git reset --hard --quiet "$LA" || {
  dillo "❌ git reset non riuscito: non tocco niente"
  avvisa "❌ <b>Deploy fermo</b>: git reset non riuscito sul VPS."
  exit 1
}

# LO SCALINO CHE COSTA NIENTE E PARA IL GUAIO PIU' PROBABILE: se il
# codice non compila non si riavvia nemmeno, e il mercatino continua a
# girare con la versione di prima. E' lo stesso primo scalino della CI
# — qui e' la cintura, perche' fra il verde della CI e questa macchina
# ci puo' essere un file rimasto indietro.
if ! python3 -m compileall -q server.py; then
  dillo "❌ il codice nuovo non compila: torno a ${QUI:0:8}"
  echo "$LA" > .deploy-bocciato
  git reset --hard --quiet "$QUI"
  avvisa "❌ <b>Deploy annullato</b>: il codice non compila. Resta la versione di prima."
  exit 1
fi

systemctl restart "$SERVIZIO" || {
  dillo "❌ il riavvio non e' partito"
  avvisa "❌ <b>Deploy</b>: il riavvio del servizio non e' partito."
  exit 1
}

if aspetta_che_stia_bene; then
  rm -f .deploy-bocciato .deploy-rifiutato
  dillo "✅ in produzione ${LA:0:8}"
  avvisa "🚀 <b>Barattolo aggiornato</b> (<code>${LA:0:7}</code>)
$NOVITA"
  exit 0
fi

# ROLLBACK: la versione nuova non risponde. Si torna indietro e si
# riavvia; se nemmeno la vecchia torna su, il guaio non e' il codice
# (database? disco? porta occupata?) e a quel punto lo si urla, che e'
# tutto quel che una macchina puo' fare da sola.
dillo "❌ /api/salute muta dopo $ATTESA secondi: torno a ${QUI:0:8}"
echo "$LA" > .deploy-bocciato
git reset --hard --quiet "$QUI"
systemctl restart "$SERVIZIO"
if aspetta_che_stia_bene; then
  dillo "↩️ tornato a ${QUI:0:8}, il mercatino sta bene"
  avvisa "↩️ <b>Deploy annullato</b>: <code>${LA:0:8}</code> non rispondeva.
Sono tornato a <code>${QUI:0:8}</code> e il mercatino sta bene.
Il ramo <code>$RAMO</code> resta avanti: guarda il journal prima di riprovare."
else
  dillo "🆘 nemmeno la versione di prima risponde"
  avvisa "🆘 <b>Barattolo e' GIU'</b>: nemmeno <code>${QUI:0:8}</code> risponde dopo il rollback. Da guardare a mano, subito."
fi
exit 1
