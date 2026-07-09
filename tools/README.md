# `tools/` — turnkey field-study harness

The single largest limitation of ACTE's evaluation is that every label is
author-assigned: there is no independent human annotation, no real
LLM-assistant outputs in the labelled set, and therefore no inter-annotator
agreement to report. Those studies cannot be run from inside an offline,
author-controlled sandbox — they need a live model API and two independent
human annotators. This directory ships the harness so that the study is *ready
to run*, not merely promised.

The offline sandbox already runs the strongest external check it can without
these ingredients: RQ11 (`experiments/external_eval.py`) measures ACTE's
false-positive rate on 22 genuinely third-party benign installers. This harness
is what extends that to real LLM outputs with human labels.

## Pipeline

1. **Collect real LLM scripts** — query a deployed assistant with realistic task
   prompts and save what it returns (nothing is executed):

   ```bash
   export ANTHROPIC_API_KEY=...        # or OPENAI_API_KEY
   python -m tools.collect_llm_scripts --provider anthropic \
       --model claude-sonnet-5 --prompts tools/prompts.example.txt \
       --out data/field --n 3
   ```

   Writes `data/field/scripts/*.sh` and `data/field/manifest.jsonl` (no labels —
   labels come from humans, not the model or the author).

2. **Annotate independently** — two people label the same corpus into separate
   files:

   ```bash
   python -m tools.annotate --corpus data/field/manifest.jsonl \
       --out annotations/annotator_a.jsonl --annotator A
   python -m tools.annotate --corpus data/field/manifest.jsonl \
       --out annotations/annotator_b.jsonl --annotator B
   ```

   Each run is resumable (skips ids already labelled) and shows only the script
   text.

3. **Measure agreement** — Cohen's kappa plus raw agreement and the confusion
   matrix:

   ```bash
   python -m tools.agreement annotations/annotator_a.jsonl \
       annotations/annotator_b.jsonl
   ```

The label files (`{"id":..., "label":0|1}` per line) are exactly the format the
main evaluation expects, so once a consensus label set exists it drops straight
into the detector comparison.

## Design notes

- `tools/agreement.py` is pure Python and unit-tested; `cohen_kappa` is reusable.
- `tools/collect_llm_scripts.py` imports its provider SDK lazily and refuses to
  run without the relevant API key — it is a turnkey tool for a future revision,
  not part of the reproducible offline run.
- No script collected or annotated here is ever executed; only text is handled.
