#!/bin/bash
# Download and extract UMLS Metathesaurus Full Subset (2026AA).
# Store outside the git repo under $HOME/data/umls (home quota: 200GB).

set -euo pipefail

# Direct NLM link for "UMLS Metathesaurus Full Subset" (~5.4GB zip / ~38GB extracted)
FILE_URL="https://download.nlm.nih.gov/umls/kss/2026AA/umls-2026AA-metathesaurus-full.zip"

DEST="$HOME/data/umls"
ZIP_PATH="$DEST/umls-metathesaurus-full.zip"
EXTRACT_DIR="$DEST/2026AA"

if [[ -z "${UTS_API_KEY:-}" ]]; then
  echo "ERROR: UTS_API_KEY is not set." >&2
  echo 'Run: export UTS_API_KEY="my-key"' >&2
  exit 1
fi

mkdir -p "$DEST"

echo "=== Home disk space ==="
df -h "$HOME"
echo

# Free space in GB (portable: use 1K-blocks from df -Pk)
avail_kb=$(df -Pk "$HOME" | awk 'NR==2 {print $4}')
avail_gb=$((avail_kb / 1024 / 1024))
echo "Available on \$HOME: ~${avail_gb} GB"
if (( avail_gb < 50 )); then
  echo "WARNING: Less than 50GB free. Download needs ~44GB peak (5.4GB zip + 38GB extracted)." >&2
  echo "Continue at your own risk, or free space first." >&2
fi
echo

DOWNLOAD_URL="https://uts-ws.nlm.nih.gov/download?url=${FILE_URL}&apiKey=${UTS_API_KEY}"

echo "Downloading UMLS Metathesaurus Full Subset to:"
echo "  $ZIP_PATH"
echo "(Resume-capable; will retry until complete.)"
echo

# Large file: keep retrying curl with resume until the download finishes.
while true; do
  if curl -L --fail -C - \
      --retry 5 --retry-delay 10 \
      -o "$ZIP_PATH" \
      "$DOWNLOAD_URL"; then
    break
  fi
  echo "curl failed or connection dropped; retrying resume in 10s..." >&2
  sleep 10
done

if [[ ! -s "$ZIP_PATH" ]]; then
  echo "ERROR: Download missing or empty: $ZIP_PATH" >&2
  exit 1
fi

echo
echo "Download OK ($(du -h "$ZIP_PATH" | cut -f1)). Extracting to $EXTRACT_DIR ..."
mkdir -p "$EXTRACT_DIR"
unzip -o "$ZIP_PATH" -d "$EXTRACT_DIR"

echo "Extraction succeeded; deleting zip to reclaim space..."
rm -f "$ZIP_PATH"

echo
echo "=== Done ==="
echo "Extracted path: $EXTRACT_DIR"
du -sh "$EXTRACT_DIR"

echo
echo "Reminders:"
echo "1. Run this on a login/interactive session, not a short SLURM batch job"
echo "   (the download can outlast a small job's time limit)."
echo "2. Add to ~/.bashrc:"
echo "   export UMLS_DIR=\$HOME/data/umls"
