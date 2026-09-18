#!/bin/bash
# Job A watcher. On 33347 leaving the queue:
#   COMPLETED 0:0 -> nothing is quarantined, nothing is submitted, 33441 is released.
#   anything else -> quarantine, submit A1 and A2, release 33441 once A1 is RUNNING.
# 33441 is released on EVERY path, including failure paths, because a held QA-margin job
# nobody releases is a worse outcome than a delay to A2.
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"

sub () {   # sub <sbatch file> -> echoes job id. Delegates to slurm/sbatch_retry.sh so there
           # is ONE retry implementation in the tree, not a copy that can drift from it.
  SBATCH_RETRY_N=10 SBATCH_RETRY_SLEEP=60 ./slurm/sbatch_retry.sh "$1"
}

release_qa () {
  if squeue -h -j 33441 -o "%T %r" 2>/dev/null | grep -q JobHeldUser; then
    if scontrol release 33441 2>&1; then
      echo "RELEASED 33441 (QA margin) at $(date +%H:%M:%S)"
    else
      echo "*** FAILED TO RELEASE 33441 -- IT IS STILL HELD. MANUAL ACTION NEEDED: scontrol release 33441"
    fi
  else
    echo "33441 is not in JobHeldUser state; nothing to release ($(squeue -h -j 33441 -o '%T %r' 2>/dev/null))"
  fi
}

until [ -z "$(squeue -h -j 33347 -o %T 2>/dev/null)" ]; do sleep 60; done
sleep 30
ST=$(sacct -j 33347 -X -n -o State | head -1 | tr -d ' ')
EX=$(sacct -j 33347 -X -n -o ExitCode | head -1 | tr -d ' ')
EL=$(sacct -j 33347 -X -n -o Elapsed | head -1 | tr -d ' ')
echo "=== JOB A 33347 EXITED: State=$ST ExitCode=$EX Elapsed=$EL at $(date +%H:%M:%S) ==="
echo "--- last non-progress log lines ---"
tr '\r' '\n' < logs/mm_a9_jobA_33347.log | grep -avE "it/s\]|batch/s\]|CUI/s\]" | tail -6

if [ "$ST" = "COMPLETED" ] && [ "$EX" = "0:0" ]; then
  echo "RESULT: job A COMPLETED cleanly. No quarantine. A1/A2 NOT submitted."
  ls -l outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_partA* 2>/dev/null
  release_qa
  exit 0
fi

echo "RESULT: job A did NOT complete cleanly ($ST/$EX)."
echo "--- quarantine ---"
bash scripts/quarantine_partial_map.sh

echo "--- submitting the halves ---"
A1=$(sub slurm/run_mm_a9_jobA1.sbatch)
A2=$(sub slurm/run_mm_a9_jobA2.sbatch)
echo "A1=${A1:-SUBMIT-FAILED}  A2=${A2:-SUBMIT-FAILED}"

if [ -z "$A1" ]; then
  echo "*** A1 DID NOT SUBMIT after 10 attempts. Releasing 33441 rather than stranding it."
  release_qa
  exit 1
fi

echo "--- waiting for A1 ($A1) to reach RUNNING (cap: 90 min) ---"
deadline=$(( $(date +%s) + 5400 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  s=$(squeue -h -j "$A1" -o %T 2>/dev/null)
  if [ "$s" = "RUNNING" ]; then
    echo "A1 $A1 is RUNNING at $(date +%H:%M:%S)"
    release_qa
    echo "--- queue ---"; squeue -u "$USER" -o "%.10i %.16j %.9T %.10M %.16r"
    exit 0
  fi
  if [ -z "$s" ]; then
    echo "*** A1 $A1 left the queue without being seen RUNNING: $(sacct -j $A1 -X -n -o State,ExitCode)"
    release_qa; exit 1
  fi
  sleep 60
done
echo "*** A1 still not RUNNING after 90 min. Releasing 33441 anyway so it is not stranded."
release_qa
squeue -u "$USER" -o "%.10i %.16j %.9T %.10M %.16r"
