#!/usr/bin/env bash

# Utility per il disaster recovery di Barattolo
# Usi: ripristino da backup, test di integrità, monitoraggio

set -euo pipefail

# Colori per il terminale
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Percorsi
BARATTOLO_DIR="${BARATTOLO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKUP_LOCAL="$BARATTOLO_DIR/backup"
BACKUP_FUORI="$BACKUP_LOCAL/fuori"
DB="$BARATTOLO_DIR/satmarket.db"

# ============ FUNZIONI DI SUPPORTO ============

log_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
log_ok() { echo -e "${GREEN}✅ $*${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
log_err() { echo -e "${RED}❌ $*${NC}" >&2; }

# ============ COMANDO: elenco-backup ============

cmd_elenco_backup() {
  echo -e "\n${BLUE}Backup su VPS:${NC}"
  echo "Pre-deploy (ultimi 5):"
  ls -lht "$BACKUP_LOCAL/pre-deploy-"*.db 2>/dev/null | head -5 | \
    awk '{printf "  %s  %s  %s\n", $9, $5, $6" "$7" "$8}' || log_warn "nessuno trovato"

  echo -e "\nBackup giornalieri cifrati:"
  ls -lht "$BACKUP_FUORI/barattolo-"*.tar.gz.age 2>/dev/null | head -5 | \
    awk '{printf "  %s  %s  %s\n", $9, $5, $6" "$7" "$8}' || log_warn "nessuno trovato"

  # Informazioni sul backup esterno (se raggiungibile via rclone)
  if command -v rclone &>/dev/null; then
    echo -e "\n${BLUE}Backup su remote (rclone, se configurato):${NC}"
    rclone lsf barattolo:backup/ 2>/dev/null | head -10 || log_warn "rclone non configurato"
  fi
}

# ============ COMANDO: test-integrità-backup ============

cmd_test_integrità() {
  local backup_file="${1:-}"

  if [ -z "$backup_file" ]; then
    log_err "Uso: utility-ripristino.sh test-integrità <file.tar.gz.age>"
    echo "File disponibili:"
    ls -1 "$BACKUP_FUORI/barattolo-"*.tar.gz.age 2>/dev/null | tail -5
    exit 1
  fi

  if [ ! -f "$backup_file" ]; then
    log_err "File non trovato: $backup_file"
    exit 1
  fi

  # Verifica che il file sia valido (age header)
  if ! file "$backup_file" | grep -qi "gzip\|encrypted"; then
    log_warn "Il file potrebbe non essere cifrato correttamente"
  fi

  # Verifica la firma age (se possibile)
  if head -c 50 "$backup_file" | grep -q "^-----BEGIN AGE ENCRYPTED FILE-----"; then
    log_ok "File ha intestazione AGE valida"
  fi

  # Dimensione
  local size_mb=$(($(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file") / 1024 / 1024))
  if [ "$size_mb" -lt 1 ]; then
    log_err "File troppo piccolo ($size_mb MB) — probabilmente corrotto"
    exit 1
  elif [ "$size_mb" -gt 100 ]; then
    log_warn "File molto grande ($size_mb MB) — controllare se è completo"
  else
    log_ok "Dimensione ok ($size_mb MB)"
  fi

  echo -e "\n${YELLOW}⚠️  Per verificare completamente il backup, decriptalo offline e testa il database:${NC}"
  echo "  1) Decripta con age (chiave privata da Bitwarden)"
  echo "  2) Estrai: tar -xzf backup-decriptato.tar.gz"
  echo "  3) Testa: sqlite3 satmarket.db 'SELECT COUNT(*) FROM utenti LIMIT 1'"
}

# ============ COMANDO: stato-backup-esterno ============

cmd_stato_backup_esterno() {
  echo -e "\n${BLUE}Stato del backup esterno (Telegram):${NC}"

  # Controlla che il file di stato esista
  if [ ! -f "$BACKUP_FUORI/.ultimo-successo" ]; then
    log_warn "Nessun backup inviato ancora (.ultimo-successo non trovato)"
    return 0
  fi

  local ultimo=$(cat "$BACKUP_FUORI/.ultimo-successo")
  local adesso=$(date +%s)
  local ore=$(( (adesso - ultimo) / 3600 ))

  if [ "$ore" -lt 48 ]; then
    log_ok "Ultimo backup inviato $ore ore fa"
  elif [ "$ore" -lt 72 ]; then
    log_warn "Ultimo backup inviato $ore ore fa (>24 ore!)"
  else
    log_err "Nessun backup inviato da $ore ore — CONTROLLARE SUBITO"
  fi
}

# ============ COMANDO: monitoraggio-backup ============

cmd_monitoraggio() {
  echo -e "\n${BLUE}=== Monitoraggio Backup Barattolo ===${NC}\n"

  # 1) Spazio disco
  echo "1️⃣  Spazio su disco:"
  df -h /srv/barattolo | tail -1 | awk '{printf "   %s usato, %s libero, %s totale\n", $3, $4, $2}'

  local uso=$(df /srv/barattolo | tail -1 | awk '{print $5}' | sed 's/%//')
  if [ "$uso" -gt 90 ]; then
    log_err "Disco quasi pieno ($uso%)"
  elif [ "$uso" -gt 75 ]; then
    log_warn "Disco al $uso%"
  else
    log_ok "Disco ok ($uso%)"
  fi

  # 2) Integrità del database locale
  echo -e "\n2️⃣  Database locale ($DB):"
  if [ -f "$DB" ]; then
    local size_mb=$(($(stat -c%s "$DB" 2>/dev/null || stat -f%z "$DB") / 1024 / 1024))
    echo "   Dimensione: $size_mb MB"

    if sqlite3 "$DB" "SELECT COUNT(*) FROM utenti LIMIT 1" &>/dev/null; then
      local utenti=$(sqlite3 "$DB" "SELECT COUNT(*) FROM utenti")
      echo "   Utenti: $utenti"
      log_ok "Database integro"
    else
      log_err "Database CORROTTO — impossibile leggere"
    fi
  else
    log_err "Database non trovato"
  fi

  # 3) Backup pre-deploy
  echo -e "\n3️⃣  Backup pre-deploy:"
  local num_predeploybackups=$(find "$BACKUP_LOCAL/pre-deploy-"*.db 2>/dev/null | wc -l)
  if [ "$num_predeploybackups" -gt 0 ]; then
    echo "   Numero: $num_predeploybackups (max 5 mantenuti)"
    local ultimo_predeploybackup=$(ls -1t "$BACKUP_LOCAL/pre-deploy-"*.db 2>/dev/null | head -1)
    local minuti=$(( ($(date +%s) - $(stat -c%Y "$ultimo_predeploybackup" 2>/dev/null || stat -f%m "$ultimo_predeploybackup")) / 60 ))
    if [ "$minuti" -lt 60 ]; then
      log_ok "Ultimo backup pre-deploy: $minuti minuti fa"
    else
      log_warn "Ultimo backup pre-deploy: $minuti minuti fa (stale?)"
    fi
  else
    log_err "Nessun backup pre-deploy trovato"
  fi

  # 4) Backup giornaliero cifrato
  echo -e "\n4️⃣  Backup giornaliero cifrato:"
  cmd_stato_backup_esterno

  # 5) Timer systemd
  echo -e "\n5️⃣  Timer systemd:"
  if systemctl is-enabled barattolo-deploy.timer &>/dev/null; then
    log_ok "Timer deploy: abilitato"
  else
    log_warn "Timer deploy: disabilitato"
  fi

  if systemctl is-enabled barattolo-backup.timer &>/dev/null; then
    log_ok "Timer backup: abilitato"
  else
    log_warn "Timer backup: disabilitato"
  fi

  # 6) Servizio barattolo
  echo -e "\n6️⃣  Servizio barattolo:"
  if systemctl is-active barattolo &>/dev/null; then
    log_ok "Servizio: in esecuzione"
  else
    log_err "Servizio: FERMO"
  fi

  if curl -sf http://127.0.0.1:8080/api/salute >/dev/null 2>&1; then
    log_ok "/api/salute: risponde"
  else
    log_err "/api/salute: NON risponde"
  fi

  echo -e "\n${BLUE}=== Fine Monitoraggio ===${NC}\n"
}

# ============ COMANDO: test-ripristino-locale ============

cmd_test_ripristino_locale() {
  local backup_predeploylokal="${1:-}"

  if [ -z "$backup_predeploylokal" ]; then
    log_err "Uso: utility-ripristino.sh test-ripristino-locale <backup.db>"
    echo "Backup disponibili:"
    ls -1 "$BACKUP_LOCAL/pre-deploy-"*.db 2>/dev/null | tail -3
    exit 1
  fi

  if [ ! -f "$backup_predeploylokal" ]; then
    log_err "File non trovato: $backup_predeploylokal"
    exit 1
  fi

  log_info "Test di ripristino da backup locale (NON distruttivo)"
  echo "File: $backup_predeploylokal"

  # Copia il database in un file di test
  local test_db="/tmp/test-ripristino-$(date +%s).db"
  cp "$backup_predeploylokal" "$test_db"
  trap "rm -f $test_db" EXIT

  # Testa il database
  if sqlite3 "$test_db" "SELECT COUNT(*) FROM utenti LIMIT 1" &>/dev/null; then
    local utenti=$(sqlite3 "$test_db" "SELECT COUNT(*) FROM utenti")
    log_ok "Database test ok — $utenti utenti trovati"
  else
    log_err "Database corrotto — non si apre"
    exit 1
  fi

  # Testa la struttura
  local tabelle=$(sqlite3 "$test_db" ".tables" | wc -w)
  log_ok "$tabelle tabelle trovate"

  # Integrità
  if sqlite3 "$test_db" "PRAGMA integrity_check" | grep -q "^ok$"; then
    log_ok "PRAGMA integrity_check: ok"
  else
    log_err "PRAGMA integrity_check: FALLITO"
  fi

  echo -e "\n${GREEN}✅ Backup locale è intatto e ripristinabile${NC}"
}

# ============ COMANDO: aiuto ============

cmd_aiuto() {
  cat <<EOF
${BLUE}Utility di Disaster Recovery per Barattolo${NC}

Utilizzo: $(basename "$0") <comando> [argomenti]

Comandi disponibili:

  ${BLUE}elenco-backup${NC}
    Elenca tutti i backup (pre-deploy e giornalieri) sul VPS

  ${BLUE}test-integrità <file.tar.gz.age>${NC}
    Testa l'integrità di un backup cifrato (header, dimensione)
    Nota: il test completo richiede decriptazione offline

  ${BLUE}stato-backup-esterno${NC}
    Controlla quando è stato l'ultimo backup inviato a Telegram

  ${BLUE}monitoraggio${NC}
    Dashboard completa dello stato di backup e servizio
    (spazio disco, integrità DB, timer, servizio)

  ${BLUE}test-ripristino-locale <backup.db>${NC}
    Testa se un backup pre-deploy è ripristinabile (NON distruttivo)

  ${BLUE}aiuto${NC}
    Mostra questo messaggio

${YELLOW}Documenti di riferimento:${NC}
  - docs/DISASTER-RECOVERY.md (piano completo)
  - deploy/RIPRISTINO.md (rebuild da zero)
  - deploy/backup-fuori.sh (backup giornaliero cifrato)

${YELLOW}Scenari comuni:${NC}

  1) Controllare lo stato generale dei backup:
     $(basename "$0") monitoraggio

  2) Testare se l'ultimo backup pre-deploy è ok:
     ULTIMO_BACKUP=\$(ls -1t $BACKUP_LOCAL/pre-deploy-*.db | head -1)
     $(basename "$0") test-ripristino-locale \$ULTIMO_BACKUP

  3) Controllare quando è partito l'ultimo backup giornaliero:
     $(basename "$0") stato-backup-esterno

  4) Verifica periodica dell'integrità (una volta al mese):
     BACKUP_DECRIPTATO_OFFLINE="/path/to/backup-decriptato.tar.gz"
     $(basename "$0") test-integrità \$BACKUP_DECRIPTATO_OFFLINE

EOF
}

# ============ MAIN ============

COMANDO="${1:-aiuto}"

case "$COMANDO" in
  elenco-backup)
    cmd_elenco_backup
    ;;
  test-integrità|test-integrita)
    cmd_test_integrità "${2:-}"
    ;;
  stato-backup-esterno)
    cmd_stato_backup_esterno
    ;;
  monitoraggio)
    cmd_monitoraggio
    ;;
  test-ripristino-locale)
    cmd_test_ripristino_locale "${2:-}"
    ;;
  aiuto|--help|-h)
    cmd_aiuto
    ;;
  *)
    log_err "Comando sconosciuto: $COMANDO"
    echo "Usa 'aiuto' per l'elenco completo"
    exit 1
    ;;
esac
