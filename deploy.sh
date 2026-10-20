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
#         QUESTA macchina — e se quel file non c'e', o e' vuoto, non
#         si tira NIENTE (dal 1 ott 2026: prima c'era una cintura di
#         cartone sull'autore, vedi sotto);
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
# sotto, ed e' il gesto «questo lo rilascio io».
# A FILE ASSENTE (O VUOTO) NON SI TIRA NIENTE (1 ott 2026, la B7 del
# secondo audit). Fino a ieri c'era una «cintura di cartone»: senza il
# file, bastava che l'AUTORE della punta fosse uno di noi — ma in git
# l'autore e' TESTO LIBERO, lo scrive chiunque. Le firme sono accese
# dal 23 set; il caso che questa riga copre e' il file sparito per un
# errore di ripristino, e in quel caso il deploy deve FERMARSI e
# dirlo, non tornare a fidarsi di una riga che chiunque scrive.
# Per spegnere le firme apposta: PRODUZIONE, «IL DEPLOY CHE SI FIDA
# SOLO DI MAIN» — si rimette il file, non si toglie.
FIRMATARI="${BARATTOLO_FIRMATARI:-/etc/barattolo-deploy/firmatari}"
AVVISA_ATTESA_DOPO=600   # secondi di «aspetto» prima di dirlo a qualcuno

cd "$CARTELLA" || { echo "❌ non trovo $CARTELLA"; exit 1; }

dillo() { echo "[$(date '+%F %T')] $*"; }

# Il messaggio ai moderatori passa dal bot che c'e' gia': il token e
# gli id li legge dal config, che su questa macchina c'e' e nella repo
# non c'e' mai stato. Fail-open totale — un avviso che non parte non
# deve poter far fallire un deploy riuscito, ne' salvarne uno rotto.
#
# NEL GRUPPO DEGLI ADMIN, SE C'E' (12 ott 2026, cantiere
# deploy-nel-gruppo). Col gruppo acceso nel config (`ADMIN_CANALE_ID`,
# vedi server.py, «IL GRUPPO DEGLI ADMIN») gli avvisi del server sono
# usciti dalla chat privata, e quelli di questo script no: «🚀
# Barattolo aggiornato» arrivava ancora in privato a ognuno. Adesso
# l'avviso va nel gruppo, UNO: il secondo argomento dice in quale
# stanza — `riepiloghi` per l'aggiornamento riuscito, `errori` (di
# serie) per tutto il resto: rifiuto, attesa, rollback, guasti.
# LE STESSE PAROLE, e nessun avviso in piu' o in meno. Una stanza
# senza numero, o che non risponde, vale il Generale. SE IL GRUPPO NON
# RISPONDE (bot tolto, numero sbagliato, Telegram che rifiuta) l'avviso
# va in privato a ogni moderatore, com'era: e lo si legge in una riga
# del journal, non in un messaggio in piu'. Senza la leva — o con una
# leva storta — e' lo script di ieri.
# LA LEVA SI LEGGE COME LA LEGGE IL SERVER (`_leggi_gruppo_admin`):
# l'id di un gruppo con gli argomenti e' negativo e comincia per -100,
# il numero di una stanza e' un intero sopra 1. Sono due copie della
# stessa regola — qui non si puo' importare il server — e una prova le
# tiene uguali, caso per caso.
avvisa() {
  python3 - "$1" "${2:-errori}" <<'PY' 2>/dev/null || true
import sys, json, urllib.request
try:
    from config import BOT_TOKEN, ADMIN_IDS
except Exception:
    sys.exit(0)


def manda(chat, stanza=0):
    """Un messaggio a una chat: True solo se Telegram dice «ok»."""
    dati = {"chat_id": chat, "text": sys.argv[1], "parse_mode": "HTML",
            "disable_web_page_preview": True}
    if stanza:
        dati["message_thread_id"] = stanza
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data=json.dumps(dati).encode(),
                headers={"Content-Type": "application/json"}),
                timeout=10) as risposta:
            return json.load(risposta).get("ok") is True
    except Exception:
        return False


def gruppo_e_stanza(argomento):
    """(id del gruppo, numero della stanza): 0 e 0 a leva spenta o
    storta, 0 la stanza che manca (il Generale)."""
    try:
        import config
        grezzo = getattr(config, "ADMIN_CANALE_ID", 0)
        gruppo = 0 if isinstance(grezzo, bool) else int(str(grezzo).strip() or 0)
    except Exception:
        return 0, 0
    if gruppo >= -1000000000000:
        return 0, 0
    try:
        stanze = getattr(config, "ADMIN_CANALE_ARGOMENTI", {})
        grezzo = stanze.get(argomento, 0) if isinstance(stanze, dict) else 0
        stanza = 0 if isinstance(grezzo, bool) else int(str(grezzo).strip() or 0)
    except Exception:
        stanza = 0
    return gruppo, (stanza if stanza > 1 else 0)


gruppo, stanza = gruppo_e_stanza(sys.argv[2])
if gruppo:
    # prima nella sua stanza; se quella non risponde, nel Generale
    if manda(gruppo, stanza) or (stanza and manda(gruppo)):
        sys.exit(0)
    print("   ⚠️ avviso: il gruppo degli admin non ha risposto, lo mando "
          "in privato ai moderatori")
for chat in ADMIN_IDS:
    manda(chat)
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

# L'AVVISO IN PRESTITO (20 ott 2026, cantiere backup-database-occupato):
# il backup giornaliero (`deploy/backup-fuori.sh`) quando cade lo deve
# dire nella stessa stanza degli avvisi del deploy, con lo stesso bot e la
# stessa regola del gruppo. La regola vive QUI, in `avvisa`, e una seconda
# copia nel backup sarebbe una terza da tenere uguale: lui chiama
# `deploy.sh --avvisa "<testo>"`, e questo ramo manda e se ne va PRIMA di
# ogni git, senza toccare niente.
if [[ "${1:-}" == "--avvisa" ]]; then
  avvisa "${2:-}"
  exit 0
fi

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
  if [[ ! -s "$FIRMATARI" ]]; then
    MOTIVO="manca il file dei firmatari ($FIRMATARI): senza, nessuna punta si tira"
    return 10
  fi
  if ! git -c gpg.ssh.allowedSignersFile="$FIRMATARI" \
         verify-commit "$sha" >/dev/null 2>&1; then
    MOTIVO="${sha:0:8} non porta la firma di una chiave di $FIRMATARI"
    return 10
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
# Se la copia non riesce si va avanti lo stesso — il deploy puo' essere
# proprio la cura — ma da ottobre 2026 lo si DICE in chat: il 18 ott il
# database era rotto e questa riga lo scriveva solo nel journal.
# UNA COPIA SOLA, CONTROLLATA (20 ott 2026, cantiere
# backup-database-occupato): la fa `deploy/copia-db.py` — API di backup,
# 30 s di attesa sul lucchetto, tetto di 90 s, `integrity_check` sulla
# copia — e da QUESTA copia nasce anche l'archivio qui sotto. Prima erano
# due letture del vivo, e la seconda (il `sqlite3` senza attesa) cadeva
# su «database is locked» mentre la prima era riuscita. Il `timeout 150`
# e' la cintura sopra il tetto dell'aiutante.
COPIA="backup/pre-deploy-$(date +%Y%m%d-%H%M%S)-${QUI:0:8}.db"
DB_VIVO="$(python3 -c 'from config import DB; print(DB)' 2>/dev/null)"
ESITO_COPIA="$(timeout 150 python3 deploy/copia-db.py "${DB_VIVO:-satmarket.db}" "$COPIA" 2>/dev/null)"
case $? in
  0) COPIA_DETTA="integra"
     dillo "💾 copia del database messa da parte, integra: $COPIA ($ESITO_COPIA)" ;;
  3) COPIA_DETTA="non-integra"
     dillo "⚠️ copia del database messa da parte ma NON integra: $ESITO_COPIA" ;;
  *) COPIA_DETTA=""
     rm -f "$COPIA" "$COPIA.parziale"
     dillo "⚠️ copia del database NON riuscita: ${ESITO_COPIA:-nessuna risposta (tetto di tempo?)} — si va avanti lo stesso" ;;
esac
ls -1t backup/pre-deploy-*.db 2>/dev/null | tail -n +$((BACKUP_DA_TENERE + 1)) \
  | xargs -r rm -f

# IL BACKUP CHE ESCE, PRIMA DI OGNI DEPLOY (19 ott 2026, il database
# rotto due volte; richiesta di Andrea). La copia qui sopra sta sullo
# STESSO disco: se il VPS sparisce, sparisce con lui. Quindi prima del
# reset parte anche l'archivio cifrato del giornaliero
# (`deploy/backup-fuori.sh`, lo stesso script, lo stesso bot, lo stesso
# canale), col nome del commit che sta per arrivare. Gira dal file del
# repo PRIMA del reset: nessuno lo riscrive mentre corre.
# NON FERMA IL DEPLOY, ed e' voluto: con Telegram giu' una cura urgente
# deve poter arrivare lo stesso — la copia locale qui sopra c'e', e
# l'archivio resta in backup/fuori/ per il PC. Ma lo si DICE in chat.
# Il tetto di 120 secondi sta largo anche nei 300 dell'unita' di prima (la nuova ne da' 600).
# Dal 20 ott l'archivio prende la copia di qui sopra (`--copia`) invece di
# rileggere il vivo; senza una copia non c'e' archivio da fare, e lo si
# dice. 150 + 120 secondi stanno ancora nei 600 dell'unita'.
ARCHIVIO=""
if [ -z "$COPIA_DETTA" ]; then
  ARCHIVIO="senza-copia"
  dillo "⚠️ niente copia, niente archivio per il canale dei backup: si va avanti"
elif [ -f "${BARATTOLO_BACKUP_ENV:-/etc/barattolo-backup.env}" ]; then
  if timeout 120 bash deploy/backup-fuori.sh --prima-del-deploy "${LA:0:8}" --copia "$COPIA"; then
    ARCHIVIO="mandato"
    dillo "📦 archivio cifrato mandato al canale dei backup"
  else
    ARCHIVIO="non-partito"
    dillo "⚠️ archivio per il canale dei backup non riuscito: si va avanti"
  fi
else
  ARCHIVIO="senza-env"
  dillo "⚠️ manca /etc/barattolo-backup.env: nessun archivio prima del deploy"
fi
# L'AVVISO DICE LA VERITA' (20 ott 2026): il 20 ott il bot ha scritto «la
# copia locale c'è» senza saperlo. Adesso un avviso solo, che nomina lo
# stato vero di tutt'e due: la copia (c'e' ed e' integra / c'e' ma rotta /
# non c'e') e l'archivio. Tutto a posto, o solo l'env mancante (com'era):
# nessun avviso, bastano le righe del journal.
GUARDA="Guardare <code>journalctl -u barattolo-deploy -n 40</code>."
case "$COPIA_DETTA:$ARCHIVIO" in
  integra:mandato|integra:senza-env) ;;
  integra:*)
    avvisa "⚠️ <b>Il backup su Telegram prima del deploy non è partito</b> (${LA:0:8}). La copia locale c'è ed è integra (<code>integrity_check</code> ok): <code>$COPIA</code>. Il deploy va avanti. $GUARDA" ;;
  non-integra:*)
    if [ "$ARCHIVIO" = "mandato" ]; then STATO_ARCHIVIO="l'archivio è partito lo stesso, con la copia rotta"; else STATO_ARCHIVIO="nessun archivio nel canale"; fi
    avvisa "⚠️ <b>La copia del database prima del deploy NON è integra</b> (${LA:0:8}): $(scappa "$ESITO_COPIA"). Vuol dire che è rotto il database vivo; $STATO_ARCHIVIO. Il deploy va avanti: guardare subito <code>/api/salute</code>, e prima di toccare qualcosa si chiede a Claude. $GUARDA" ;;
  *)
    avvisa "⚠️ <b>La copia del database prima del deploy NON è riuscita</b> (${LA:0:8}): $(scappa "${ESITO_COPIA:-nessuna risposta, tetto di tempo}"). Nessuna copia locale nuova e nessun archivio nel canale: restano quelli di prima. Il deploy va avanti; guardare <code>/api/salute</code>. $GUARDA" ;;
esac

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
$NOVITA" riepiloghi
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
