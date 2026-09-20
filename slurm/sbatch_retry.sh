#!/bin/bash
# sbatch with the controller I/O-error window retried. USE THIS INSTEAD OF BARE sbatch.
#
# WHY. `sbatch: error: Batch job submission failed: I/O error writing script/environment to
# file` is a transient controller-side fault on this cluster, not a fault in the script. It
# has bitten three times on record:
#   2026-09-17 18:52-19:38  10 failures before qa_margin (33441) was accepted, ~46 min
#   2026-09-18 04:02        8 failures before jobA1 (33870) was accepted, 9th attempt
# A bare sbatch turns that window into a silently lost queue position. With a 2-job cap, a
# submission that fails while a slot is free can cost hours, and nothing in the output says
# so -- the operator sees one error line and a shell prompt.
#
# The retry is the DEFAULT for every submission in the cutoff chain. bash -n runs first and
# is chained with && so a script that cannot parse is never submitted: that is the E1/33220
# defect (docs/BUG_AUDIT.md, "verified but not enforced"), and it is cheap to not repeat.
#
# Usage:
#   slurm/sbatch_retry.sh <script.sbatch> [sbatch options...]   # options are placed BEFORE the script
#   SBATCH_RETRY_N=20 SBATCH_RETRY_SLEEP=30 slurm/sbatch_retry.sh <script.sbatch>
#   SBATCH_RETRY_DRYRUN=1 slurm/sbatch_retry.sh <script.sbatch>   # parse + echo, no submit
#
# Prints the job id alone on stdout when it succeeds, so it composes:
#   JID=$(slurm/sbatch_retry.sh slurm/foo.sbatch) || exit 1
set -uo pipefail

N="${SBATCH_RETRY_N:-15}"
SLEEP="${SBATCH_RETRY_SLEEP:-60}"
SCRIPT="${1:?usage: sbatch_retry.sh <script.sbatch> [sbatch args...]}"
shift || true

[ -f "$SCRIPT" ] || { echo "sbatch_retry: no such script: $SCRIPT" >&2; exit 2; }

# Parse before submitting, chained, so an unparseable script cannot reach the controller.
bash -n "$SCRIPT" || { echo "sbatch_retry: $SCRIPT FAILED bash -n; not submitting" >&2; exit 2; }

if [ -n "${SBATCH_RETRY_DRYRUN:-}" ]; then
  echo "sbatch_retry: DRY RUN -- $SCRIPT parses; would submit with: $*" >&2
  exit 0
fi

for try in $(seq 1 "$N"); do
  # OPTIONS BEFORE THE SCRIPT. sbatch treats everything after the script path as arguments
  # TO the script, so `sbatch script.sbatch --dependency=afterok:N` silently creates a job
  # with NO dependency -- which is exactly what happened on 2026-09-19 to the whole cut-off
  # chain: four jobs submitted, DEPENDENCY=(null) on all four, repaired with scontrol update
  # before any of them started. Silent, and the same shape as every other defect this week.
  out="$(sbatch "$@" "$SCRIPT" 2>&1)"
  if printf '%s' "$out" | grep -q "Submitted batch job"; then
    jid="$(printf '%s' "$out" | grep -oE '[0-9]+$')"
    echo "sbatch_retry: $SCRIPT -> job $jid (attempt $try/$N)" >&2
    # READ-BACK. A zero exit from sbatch says the command RAN, not that it did what was asked.
    # On 2026-09-19 all four cut-off jobs were submitted with --dependency AFTER the script
    # path; sbatch passed it to the script as an argument, every job was created with
    # Dependency=(null), and every call returned 0. Nothing in the wrapper noticed. The remedy
    # is not a better argument order -- that is this instance -- it is to read the resulting
    # state back and assert it, so the class cannot recur through some other option.
    # docs/BUG_AUDIT.md, "a success code is not a receipt".
    if [ $# -gt 0 ]; then
      _show="$(scontrol show job "$jid" 2>/dev/null)"
      _bad=0
      for _opt in "$@"; do
        case "$_opt" in
          --dependency=*)
            _w="${_opt#--dependency=}"
            printf '%s' "$_show" | grep -qE "Dependency=${_w}([( ]|$)" || {
              echo "sbatch_retry: READ-BACK FAILED on $jid -- asked --dependency=$_w, got $(printf '%s' "$_show" | grep -oE 'Dependency=[^ ]*')" >&2
              _bad=1; }
            ;;
          --hold)
            printf '%s' "$_show" | grep -q "JobHeldUser" || {
              echo "sbatch_retry: READ-BACK FAILED on $jid -- asked --hold, job is not held" >&2
              _bad=1; }
            ;;
        esac
      done
      if [ "$_bad" -ne 0 ]; then
        echo "sbatch_retry: job $jid EXISTS but does not match the request; NOT reporting success." >&2
        echo "              Repair with scontrol update, or scontrol hold it." >&2
        echo "$jid"; exit 3
      fi
      echo "sbatch_retry: read-back OK on $jid ($*)" >&2
    fi
    echo "$jid"
    exit 0
  fi
  echo "sbatch_retry: attempt $try/$N failed: $out" >&2
  # A real error in the script is permanent; only the controller I/O window is worth retrying.
  if ! printf '%s' "$out" | grep -q "I/O error writing script/environment to file"; then
    echo "sbatch_retry: not the transient controller error -- giving up immediately" >&2
    exit 1
  fi
  [ "$try" -lt "$N" ] && sleep "$SLEEP"
done
echo "sbatch_retry: $SCRIPT NOT SUBMITTED after $N attempts spanning ~$((N*SLEEP/60)) min" >&2
exit 1
