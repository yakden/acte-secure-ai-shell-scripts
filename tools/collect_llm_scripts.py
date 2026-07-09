"""Collect *real* LLM-generated shell scripts for the field study.

Every script ACTE has been evaluated on is synthetic or author-curated. The
reviewer's first ask is the study we cannot run from author data: real outputs
of deployed LLM coding assistants, labelled by independent humans. This tool is
the collection half of that harness. Given a prompt set (one natural-language
task per line, e.g. "write a bash script that backs up /etc to S3"), it queries
a real assistant API and saves each returned shell script plus a manifest that
``tools.annotate`` and ``tools.agreement`` consume.

It deliberately does **not** run in the offline sandbox and does **not** ship
any API key: the caller supplies one via environment variable. Two providers are
supported out of the box; both are optional imports so the module loads (and is
importable/testable) without either SDK installed.

  * Anthropic  — ``ANTHROPIC_API_KEY``   (``pip install anthropic``)
  * OpenAI     — ``OPENAI_API_KEY``       (``pip install openai``)

Nothing generated here is executed. Scripts are extracted from fenced code
blocks in the model reply and written as text for static analysis and human
labelling only.

Usage::

    python -m tools.collect_llm_scripts --provider anthropic \
        --model claude-sonnet-5 --prompts tools/prompts.example.txt \
        --out data/field --n 1
"""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import List, Optional

# Extracts the body of the first fenced code block, tolerating a language tag.
_FENCE = re.compile(r"```(?:bash|sh|shell|zsh)?\s*\n(.*?)```", re.DOTALL)


def extract_script(reply: str) -> Optional[str]:
    """Pull the first shell code block out of a model reply, or None."""
    m = _FENCE.search(reply)
    if m:
        body = m.group(1).strip()
        return body or None
    # Fall back to the raw reply if it already looks like a script.
    if reply.lstrip().startswith("#!"):
        return reply.strip()
    return None


def _load_prompts(path: str) -> List[str]:
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def _gen_anthropic(model: str, prompt: str) -> str:
    import anthropic  # optional dependency, imported lazily
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=model, max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(getattr(b, "text", "") for b in msg.content)


def _gen_openai(model: str, prompt: str) -> str:
    from openai import OpenAI  # optional dependency, imported lazily
    client = OpenAI()  # reads OPENAI_API_KEY
    resp = client.chat.completions.create(
        model=model, max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


_PROVIDERS = {"anthropic": _gen_anthropic, "openai": _gen_openai}


def collect(provider: str, model: str, prompts: List[str], out_dir: str,
            n: int = 1) -> List[dict]:
    """Query the assistant ``n`` times per prompt; write scripts + manifest.

    Returns the manifest records. Labels are intentionally omitted — these are
    for independent human annotation (``tools.annotate``), not self-labelling.
    """
    gen = _PROVIDERS.get(provider)
    if gen is None:
        raise ValueError(f"unknown provider {provider!r}; choose from {sorted(_PROVIDERS)}")

    scripts_dir = os.path.join(out_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    records: List[dict] = []
    idx = 0
    for pi, prompt in enumerate(prompts):
        for k in range(n):
            reply = gen(model, prompt)
            script = extract_script(reply)
            if not script:
                print(f"  no code block for prompt {pi} sample {k}; skipped")
                continue
            sid = f"llm_{provider}_{pi:03d}_{k}"
            rel = os.path.join("scripts", f"{sid}.sh")
            with open(os.path.join(out_dir, rel), "w", encoding="utf-8") as fh:
                fh.write(script)
            records.append({
                "id": sid, "path": rel, "provenance": f"{provider}:{model}",
                "prompt": prompt, "n_chars": len(script),
                # no 'label' on purpose — assigned by independent human annotators
            })
            idx += 1

    manifest = os.path.join(out_dir, "manifest.jsonl")
    with open(manifest, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"collected {len(records)} real LLM scripts -> {manifest}")
    print("next: run tools.annotate twice (two annotators), then tools.agreement")
    return records


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Collect real LLM-generated shell scripts for annotation.")
    ap.add_argument("--provider", choices=sorted(_PROVIDERS), required=True)
    ap.add_argument("--model", required=True, help="e.g. claude-sonnet-5 or gpt-4o")
    ap.add_argument("--prompts", required=True, help="one task per line")
    ap.add_argument("--out", required=True, help="output corpus directory")
    ap.add_argument("--n", type=int, default=1, help="samples per prompt")
    args = ap.parse_args(argv)

    key_env = "ANTHROPIC_API_KEY" if args.provider == "anthropic" else "OPENAI_API_KEY"
    if not os.environ.get(key_env):
        print(f"error: {key_env} is not set; this tool needs a real API key and "
              "does not run in the offline sandbox.")
        return 2

    collect(args.provider, args.model, _load_prompts(args.prompts), args.out, args.n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
