#!/bin/bash
# Download Part 2 generative models into ~/data/models (idempotent).
# Run in a login/interactive session that can stay open for a few hours (~62GB).

set -u

MODELS_DIR="${HOME}/data/models"
mkdir -p "$MODELS_DIR"

if ! command -v hf >/dev/null 2>&1; then
  echo "ERROR: 'hf' CLI not found."
  echo 'Install with: pip install -U "huggingface_hub[cli]"'
  exit 1
fi

# repo_id|local_dirname
MODELS=(
  "mistralai/Mistral-7B-Instruct-v0.1|Mistral-7B-Instruct-v0.1"
  "BioMistral/BioMistral-7B|BioMistral-7B"
  "meta-llama/Meta-Llama-3-8B-Instruct|Meta-Llama-3-8B-Instruct"
  "aaditya/Llama3-OpenBioLLM-8B|Llama3-OpenBioLLM-8B"
)

succeeded=()
failed=()
skipped=()

for entry in "${MODELS[@]}"; do
  repo="${entry%%|*}"
  name="${entry##*|}"
  dest="${MODELS_DIR}/${name}"

  echo
  echo "======================================"
  echo "Model: ${repo}"
  echo "Dest:  ${dest}"
  echo "======================================"

  if [[ -f "${dest}/config.json" ]]; then
    echo "SKIP: ${dest}/config.json already exists (idempotent)."
    skipped+=("$name")
    continue
  fi

  mkdir -p "$dest"
  if hf download "$repo" --local-dir "$dest"; then
    if [[ -f "${dest}/config.json" ]]; then
      echo "OK: downloaded ${name}"
      succeeded+=("$name")
    else
      echo "FAIL: download finished but ${dest}/config.json is missing"
      failed+=("$name")
      if [[ "$repo" == meta-llama/* ]]; then
        echo "NOTE: ${repo} is a gated model. Run: hf auth login"
        echo "      Use a token from an account that has accepted Meta's licence"
        echo "      on the model page: https://huggingface.co/${repo}"
      fi
    fi
  else
    echo "FAIL: hf download exited non-zero for ${name}"
    failed+=("$name")
    if [[ "$repo" == meta-llama/* ]]; then
      echo "NOTE: ${repo} is a gated model. Run: hf auth login"
      echo "      Use a token from an account that has accepted Meta's licence"
      echo "      on the model page: https://huggingface.co/${repo}"
    fi
  fi
done

echo
echo "=== Download summary ==="
echo "Succeeded (${#succeeded[@]}): ${succeeded[*]:-none}"
echo "Skipped   (${#skipped[@]}): ${skipped[*]:-none}"
echo "Failed    (${#failed[@]}): ${failed[*]:-none}"

echo
echo "=== Disk used by ${MODELS_DIR} ==="
du -sh "$MODELS_DIR"

echo
echo "Reminder: run this in a login/interactive session that can stay open"
echo "for a few hours (four models, ~62GB total). Do not rely on a short"
echo "SLURM walltime for the full download."

if (( ${#failed[@]} > 0 )); then
  exit 1
fi
exit 0
