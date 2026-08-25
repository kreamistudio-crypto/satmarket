#!/usr/bin/env bash
#
# IL DEPLOY DI BARATTOLO, dalla parte del VPS (ago 2026).
#
# Gira ogni minuto da un timer systemd, guarda se il ref `pronto` si e'
# mosso e in quel caso aggiorna il mercatino. Nel caso normale — cioe'
# quasi sempre — fa un `git fetch` e se ne va senza dire niente.
#
# LE QUATTRO REGOLE, che sono il motivo per cui questo file esiste
# invece di un `git pull && systemctl restart` in un cron:
#
# 1) SI SEGUE `pronto`, NON `main`. Quel ref lo fa avanzare solo la CI
#    quando prove e controllo dei segreti sono verdi (vedi il job
#    `pronto` in .github/workflows/prove.yml). Cosi' «la CI e' passata»
#    non e' una domanda da fare a un'API con un token in mano: e' il
#    fatto stesso che il ref si sia mosso. Un commit rosso resta su
#    main e in produzione non ci arriva mai.
#
# 2) SI TIRA, NON SI VIENE SPINTI. Nessuna chiave di questa macchina
#    sta nei secret di GitHub: chi compromette GitHub, o una action di
#    terzi, non arriva al nodo Lightning. La direzione del deploy e'
#    una decisione di sicurezza, non di comodita'.
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
#     ./deploy.sh --dimmi    guarda e basta, non tocca niente

set -uo pipefail

CARTELLA="${BARATTOLO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
SERVIZIO="${BARATTOLO_SERVIZIO:-barattolo}"
SALUTE="${BARATTOLO_SALUTE:-http://127.0.0.1:8080/api/salute}"
ATTESA="${BARATTOLO_ATTESA:-45}"     # secondi dati al server per rispondere
RAMO="${BARATTOLO_RAMO:-pronto}"
BACKUP_DA_TENERE=5

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

git fetch --quiet origin "$RAMO" 2>/dev/null || {
  dillo "⚠️ git fetch non riuscito (rete? credenziali?): riprovo al giro dopo"
  exit 0
}

QUI="$(git rev-parse HEAD)"
LA="$(git rev-parse "origin/$RAMO" 2>/dev/null)" || {
  dillo "⚠️ il ramo «$RAMO» non esiste ancora su origin: la CI non l'ha mai alzato"
  exit 0
}

if [[ "${1:-}" == "--dimmi" ]]; then
  dillo "qui: ${QUI:0:8}  ·  pronto: ${LA:0:8}"
  [[ "$QUI" == "$LA" ]] && dillo "in pari" || dillo "c'e' un aggiornamento"
  git --no-pager log --oneline "$QUI..$LA" 2>/dev/null | sed 's/^/    /'
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

NOVITA="$(git --no-pager log --oneline "$QUI..$LA" 2>/dev/null | head -10)"
dillo "🚀 aggiornamento: ${QUI:0:8} → ${LA:0:8}"

# IL DATABASE SI COPIA PRIMA, e si copia con l'API di sqlite invece che
# con `cp`: il server sta girando, e un file copiato a caldo mentre
# qualcuno scrive e' un file che al momento del bisogno non si apre.
# Non e' il backup giornaliero (quello vive per conto suo): e' la rete
# per i cinque minuti attorno al deploy, quando gira anche `init_db`
# con le sue migrazioni.
mkdir -p backup
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
  rm -f .deploy-bocciato
  dillo "✅ in produzione ${LA:0:8}"
  avvisa "🚀 <b>Barattolo aggiornato</b> — <code>${LA:0:8}</code>
$(echo "$NOVITA" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')"
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
