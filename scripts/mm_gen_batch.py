"""Batched causal concept generation — EXECUTION-ONLY change.

`generate_concept_single` is a verbatim copy of the notebook's per-row `generate_concept`
(the current production path). `generate_concept_batch` produces the SAME cleaned output
for a list of texts using left-padded batched generation with a correct attention mask.

Nothing about the method changes: same prompt, same chat template, same decoding
(do_sample=False greedy, max_new_tokens, pad/eos handling), same bf16 model. Batching only
changes how many sequences share a forward pass. Because greedy decoding under bf16 is not
guaranteed bit-identical across batch shapes, the batched path must be proven exactly
string-identical per model (scripts/mm_gen_verify.py) before it is trusted.

The helpers below (instruction, Llama-3 template, chat-template attach, output cleaner) are
copied verbatim from notebooks/02_concept_inference/MedMentions_generative_inference.ipynb
cell 6 so both paths share identical pre/post-processing.
"""
import re

import torch

CAUSAL_MAX_NEW_TOKENS = 16  # short concept span, not prose

_CONCEPT_INSTR = (
    "Identify the primary medical concept in the following clinical text. "
    "Reply with only the concept name.\n\n"
    "Text: {text}"
)

_LLAMA3_CHAT_TEMPLATE = (
    "{% set loop_messages = messages %}"
    "{% for message in loop_messages %}"
    "{% set content = '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'"
    "+ message['content'] | trim + '<|eot_id|>' %}"
    "{% if loop.index0 == 0 %}{% set content = bos_token + content %}{% endif %}"
    "{{ content }}{% endfor %}"
    "{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}{% endif %}"
)


def ensure_chat_template(tokenizer) -> None:
    """Attach a chat template when missing (OpenBioLLM = Llama-3 family)."""
    if getattr(tokenizer, "chat_template", None):
        return
    eot = tokenizer.convert_tokens_to_ids("<|eot_id|>")
    unk = getattr(tokenizer, "unk_token_id", None)
    if eot is not None and eot != unk:
        tokenizer.chat_template = _LLAMA3_CHAT_TEMPLATE
        return
    tokenizer.chat_template = (
        "{{ bos_token }}{% for message in messages %}"
        "{% if message['role'] == 'user' %}{{ '[INST] ' + message['content'] + ' [/INST]' }}"
        "{% elif message['role'] == 'assistant' %}{{ message['content'] }}"
        "{% endif %}{% endfor %}"
    )


def clean_concept_output(decoded: str) -> str:
    """Strip residual chat-template / scaffolding markers from decoded span."""
    text = decoded.strip()
    for marker in ("[/INST]", "</s>", "<s>"):
        text = text.replace(marker, " ")
    for marker in ("Answer:", "Concept:", "The primary medical concept is"):
        if marker in text:
            text = text.split(marker)[-1]
    m = re.search(
        r"(?is)the primary medical concepts?\b.*?\b(?:is|are)\b\s*:?\s*",
        text,
    )
    if m:
        text = text[m.end():]
    text = text.strip(" \"'`.")
    text = " ".join(text.split()).strip()
    return text[:200]


def _eos_ids_for(tokenizer):
    eos_ids = [tokenizer.eos_token_id] if tokenizer.eos_token_id is not None else []
    eot = tokenizer.convert_tokens_to_ids("<|eot_id|>")
    unk = getattr(tokenizer, "unk_token_id", None)
    if eot is not None and eot != unk and eot not in eos_ids:
        eos_ids.append(eot)
    return eos_ids


def _gen_kwargs(tokenizer):
    eos_ids = _eos_ids_for(tokenizer)
    kw = dict(
        max_new_tokens=CAUSAL_MAX_NEW_TOKENS,
        do_sample=False,  # greedy, T=0
        pad_token_id=tokenizer.pad_token_id,
    )
    if eos_ids:
        kw["eos_token_id"] = eos_ids if len(eos_ids) > 1 else eos_ids[0]
    return kw


def _prompt_for(text: str, tokenizer) -> str:
    ensure_chat_template(tokenizer)
    messages = [{"role": "user", "content": _CONCEPT_INSTR.format(text=text)}]
    return tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)


def _first_device(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cuda:0")


def generate_concept_single(text: str, tokenizer, model) -> str:
    """VERBATIM reproduction of the notebook's per-row generate_concept (reference path)."""
    prompt = _prompt_for(text, tokenizer)
    enc = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512, padding=True)
    dev = _first_device(model)
    enc = {k: v.to(dev) for k, v in enc.items()}
    input_len = enc["input_ids"].shape[-1]
    with torch.no_grad():
        out = model.generate(**enc, **_gen_kwargs(tokenizer))
    new_tokens = out[0][input_len:]
    decoded = tokenizer.decode(new_tokens, skip_special_tokens=True)
    return clean_concept_output(decoded)


def generate_concept_batch(texts, tokenizer, model, batch_size=16):
    """Batched, LEFT-padded greedy generation. Returns cleaned strings aligned to `texts`.

    Must be proven string-identical to generate_concept_single before use (verify gate)."""
    prev_side = tokenizer.padding_side
    tokenizer.padding_side = "left"
    dev = _first_device(model)
    gen_kwargs = _gen_kwargs(tokenizer)
    outs = []
    try:
        for i in range(0, len(texts), batch_size):
            chunk = [str(t) if t is not None else "" for t in texts[i:i + batch_size]]
            prompts = [_prompt_for(t, tokenizer) for t in chunk]
            enc = tokenizer(
                prompts, return_tensors="pt", truncation=True, max_length=512, padding=True
            )
            enc = {k: v.to(dev) for k, v in enc.items()}
            input_len = enc["input_ids"].shape[1]  # left-padded: same for every row
            with torch.no_grad():
                out = model.generate(**enc, **gen_kwargs)
            new_tokens = out[:, input_len:]
            decoded = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
            outs.extend(clean_concept_output(d) for d in decoded)
    finally:
        tokenizer.padding_side = prev_side
    return outs
