# Shared env for MM/CADEC/QA GPU jobs. Source from repo root.
mkdir -p logs
export PY="${PY:-$HOME/.conda/envs/torch_gpu/bin/python}"
export HF_HOME="${HF_HOME:-$HOME/data/hf_cache}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export ASSUMED_QUOTA_GB="${ASSUMED_QUOTA_GB:-200}"
export DISK_PAUSE_GB="${DISK_PAUSE_GB:-10}"

# G4 LanguageTool needs a JRE. Binary lives at ~/data/jdk/temurin-17 (not ~/data/jdk/bin).
if [ -x "${JAVA_HOME:-}/bin/java" ]; then
  :
elif [ -x "$HOME/data/jdk/temurin-17/bin/java" ]; then
  export JAVA_HOME="$HOME/data/jdk/temurin-17"
elif [ -x "$HOME/data/jdk/bin/java" ]; then
  export JAVA_HOME="$HOME/data/jdk"
else
  echo "FATAL: no Java for LanguageTool G4 (tried JAVA_HOME, ~/data/jdk/temurin-17, ~/data/jdk)" >&2
  exit 1
fi
export PATH="$JAVA_HOME/bin:$PATH"
export PYTHONUNBUFFERED=1
echo "JAVA_HOME=$JAVA_HOME ($(java -version 2>&1 | head -1))"

# 7B/8B bf16: keep off 16–24GB cards (A4000 / Ada / 4500 / 6000).
BIG_GPU_EXCLUDE="${BIG_GPU_EXCLUDE:-g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g48-1gpu-[1-2],g48-2gpu-1}"
# Perturbations / encoders: only the known-bad node.
SMALL_GPU_EXCLUDE="${SMALL_GPU_EXCLUDE:-g48-2gpu-1}"
