#!/bin/bash
# LA GUARDIA DEL RUNNER DELLA VM-2050 (ott 2026, cantiere runner-vm,
# decisione di Andrea). Il runner la esegue PRIMA di ogni job
# (ACTIONS_RUNNER_HOOK_JOB_STARTED nel suo .env): se il job non e' il
# `prove` del workflow di main di questo repo, lanciato da un push o a
# mano, si ferma qui e sulla macchina non gira una riga del suo codice.
#
# E' il lucchetto vero, ed e' per questo che sta sulla VM e non nel
# workflow: un ramo puo' riscrivere il workflow (e chiedere
# `runs-on: vm-2050`), non questo file, che e' di root e il runner lo
# legge e basta. Il workflow manda qui solo main; questa guardia lo
# pretende.
#
# Chiude se manca qualcosa: una variabile vuota e' un no, mai un si'.
# Sulla VM sta in /opt/ci-guardia/solo-main.sh, root:root 755; la copia
# nel repo e' questa, e le due si confrontano con sha256sum.
set -u

REPO_ATTESO="kreamistudio-crypto/satmarket"
WORKFLOW_ATTESO="$REPO_ATTESO/.github/workflows/prove.yml@refs/heads/main"

echo "guardia vm-2050: repo=${GITHUB_REPOSITORY:-?} ref=${GITHUB_REF:-?}" \
     "evento=${GITHUB_EVENT_NAME:-?} job=${GITHUB_JOB:-?}" \
     "workflow=${GITHUB_WORKFLOW_REF:-?}"

no() {
    echo "::error::guardia vm-2050: $1. Su questa macchina gira solo il job prove di main."
    exit 1
}

[ "${GITHUB_REPOSITORY:-}" = "$REPO_ATTESO" ] || no "repo diverso"
[ "${GITHUB_REF:-}" = "refs/heads/main" ] || no "non e' main"
[ "${GITHUB_WORKFLOW_REF:-}" = "$WORKFLOW_ATTESO" ] || no "workflow diverso da quello di main"
case "${GITHUB_EVENT_NAME:-}" in
    push|workflow_dispatch) ;;
    *) no "evento «${GITHUB_EVENT_NAME:-}» (solo push e lancio a mano)" ;;
esac
[ "${GITHUB_JOB:-}" = "prove" ] || no "job «${GITHUB_JOB:-}» (solo prove)"

echo "guardia vm-2050: ok"
