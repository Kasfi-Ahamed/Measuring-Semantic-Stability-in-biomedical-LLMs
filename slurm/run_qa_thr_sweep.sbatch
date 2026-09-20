#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=0:20:00
#SBATCH -o qa_thr_sweep_%j.log
#SBATCH -J qa_thr
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#
# Small-model job: no 7-8B weights, so the 16/20 GB cards are fine. Excludes g32-2gpu-1
# (V100, no native bf16 -- this job still loads bf16 weights) and g48-2gpu-1 (node health).
#
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
export HF_HOME=$HOME/data/hf_cache
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
~/.conda/envs/torch_gpu/bin/python -u << 'PY'
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEVICE="cuda"
name="cross-encoder/nli-MiniLM2-L6-H768"
tok=AutoTokenizer.from_pretrained(name, local_files_only=True)
model=AutoModelForSequenceClassification.from_pretrained(name, local_files_only=True).to(DEVICE).eval()
id2label={int(k):v for k,v in model.config.id2label.items()}
ENTAIL=next(i for i,l in id2label.items() if "entail" in str(l).lower())
print("id2label", id2label, "ENTAIL_IDX", ENTAIL, flush=True)

def p_ent(a,b):
    enc=tok(a,b,return_tensors="pt",truncation=True,max_length=256)
    enc={k:v.to(DEVICE) for k,v in enc.items()}
    with torch.no_grad():
        probs=torch.softmax(model(**enc).logits[0].float(), dim=-1)
    return float(probs[ENTAIL])

cases={
 "a": ["heart attack","myocardial infarction","MI"],
 "b": ["aspirin","diabetes","the femur"],
 "c": ["yes","affirmative","no"],
}
print("\nPairwise bidirectional entailment probs:", flush=True)
for name,ans in cases.items():
    print(f"\n=== {name} {ans} ===", flush=True)
    for i in range(len(ans)):
        for j in range(i+1,len(ans)):
            eij,eji=p_ent(ans[i],ans[j]),p_ent(ans[j],ans[i])
            print(f"  {ans[i]!r}<->{ans[j]!r}: {eij:.4f}/{eji:.4f}  min={min(eij,eji):.4f}", flush=True)

class UF:
    def __init__(self,n):
        self.p=list(range(n))
    def find(self,x):
        while self.p[x]!=x: self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a,b):
        ra,rb=self.find(a),self.find(b)
        if ra!=rb: self.p[ra]=rb

def n_clusters(ans, thr):
    n=len(ans); uf=UF(n)
    lows=[a.strip().lower() for a in ans]
    for i in range(n):
        for j in range(i+1,n):
            if lows[i]==lows[j]:
                uf.union(i,j); continue
            if p_ent(ans[i],ans[j])>=thr and p_ent(ans[j],ans[i])>=thr:
                uf.union(i,j)
    return len({uf.find(i) for i in range(n)})

print("\nThreshold sweep (expect a=1, b=3, c=2):", flush=True)
for thr in [0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.72,0.75,0.80]:
    ka,kb,kc=n_clusters(cases["a"],thr),n_clusters(cases["b"],thr),n_clusters(cases["c"],thr)
    ok = (ka==1 and kb==3 and kc==2)
    print(f"  thr={thr:.2f}  a={ka} b={kb} c={kc}  {'OK' if ok else ''}", flush=True)
PY
