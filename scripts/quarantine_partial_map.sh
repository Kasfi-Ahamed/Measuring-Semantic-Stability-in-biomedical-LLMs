#!/bin/bash
# Quarantine a killed mapping job's output before anything downstream can read it.
#
# THE HAZARD. Cell 11 writes the Amendment 9 receipt FIRST (line 628-630) and the corpus
# SECOND (line 632). A job killed during to_csv therefore leaves a COMPLETE, PASSING receipt
# beside a TRUNCATED CSV. A truncated 530MB CSV parses cleanly for its first N rows and looks
# like a corpus. R5 at the join reads the receipt and would pass; only R3's row count would
# catch it. This removes the file from reach rather than relying on one receipt to hold.
#
# Renames, never deletes: .PARTIAL keeps the evidence and takes the name out of every glob
# the pipeline uses.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
STAMP="$(date +%Y%m%dT%H%M%S)"
INTER="outputs/rq1/intermediate"
n=0
for f in "$INTER"/rq1_all_outputs_mapped_A9_partA.csv \
         "$INTER"/rq1_all_outputs_mapped_A9_partA.amendment9_receipt.json \
         "$INTER"/rq1_mapped*; do
  [ -e "$f" ] || continue
  mv -n -- "$f" "$f.PARTIAL.$STAMP"
  echo "QUARANTINED: $f -> $f.PARTIAL.$STAMP  ($(stat -c%s "$f.PARTIAL.$STAMP") bytes)"
  n=$((n+1))
done
if [ "$n" -eq 0 ]; then
  echo "nothing to quarantine: job A wrote no output file"
fi
echo "quarantined $n file(s)"
