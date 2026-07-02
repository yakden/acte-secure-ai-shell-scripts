# Dataset Provenance

## Summary

The ACTE evaluation corpus is **synthetic and fully reproducible**. It is
produced entirely by `data/generate_dataset.py` from handcrafted templates and a
fixed random seed (`SEED = 1337`). Re-running the generator yields a
byte-identical corpus. No real user data, telemetry, or scraped third-party
scripts are included.

```bash
python -m data.generate_dataset      # regenerates data/scripts/ + manifests
```

## How samples are created

Each sample is an instantiation of a Python template function. Templates were
authored from **publicly documented, well-known shell idioms** — both benign
(backups, package installs, log rotation, git workflows) and malicious (the
classic bash fork bomb, `curl | sh` installers, `/dev/tcp` and netcat reverse
shells, `dd`/`mkfs` device wipes, SSH `authorized_keys` backdoors, cron
persistence). Parameter pools (directories, hosts, ports, packages, services)
introduce surface variety while keeping each sample's ground-truth label exact.
Exact-duplicate scripts are removed so metrics are not inflated by copies.

## Categories and labels

The binary ground-truth label is `1 = dangerous`, `0 = safe`.

| Category | Intent | Typical label |
|---|---|---|
| `safe_everyday` | Benign day-to-day scripts | 0 |
| `malicious` | Clearly malicious scripts | 1 |
| `ai_generated` | AI-assistant-style scripts (verbose comments, helpful framing) | mixed 0/1 |
| `obfuscated` | Obfuscated / evasive variants (base64, hex, octal, reversed, IFS tricks) | 1 |
| `sysadmin` | Realistic sysadmin tasks | mostly 0, a few 1 |

## Deliberate difficulty (honesty of the benchmark)

To avoid a trivially separable benchmark and to make the reported metrics
credible, the corpus intentionally includes:

* **Hard negatives** (label 0) — genuinely safe scripts that *use scary-looking
  commands*: bounded `rm -rf` of a tmp dir, privileged `apt-get install`,
  `curl` download + checksum (no exec), deploying a vetted config into `/etc`
  and reloading the service, recursive `chmod 755` on a web root, and `dd`
  copying one regular file to another (no block device). These stress
  **precision**.
* **Hard positives** (label 1) — genuinely dangerous payloads *crafted to evade
  the finite signature set*: a split download→`chmod +x`→execute sequence,
  catastrophic `find / -delete`, a Perl reverse shell, a deferred destructive
  `at` job, an unquoted-unset-variable `rm` wipe, and an env+Python remote
  exec. These stress **recall** and motivate ACTE's adaptive learning.

Every label is the *correct* ground truth for the script's actual behavior; the
difficulty comes from realistic ambiguity, never from mislabeling.

## Files

* `manifest.jsonl` / `manifest.csv` — one row per sample with
  `id, category, label, label_name, rationale, template, path, provenance,
  n_chars, n_lines`. The `template` field records the generating template
  function's name; it is the group key for the **leave-template-out
  cross-validation**, which guarantees no template contributes scripts to both
  the training and evaluation folds.
* `scripts/<id>.sh` — the script body for each sample.

## Real-world external validation set (independent holdout)

Because the corpus above is synthetic, the study also ships an **independent,
non-synthetic holdout** used only for testing (never for training or threshold
tuning): `data/real_world/`. It contains 41 hand-authored, realistic scripts
(21 dangerous, 20 safe) drawn from **publicly documented idioms** — routine
sysadmin/devops tasks on the safe side, and canonical, publicly catalogued
attack techniques (reverse shells, the bash fork bomb, device-wipe `dd`/`mkfs`,
SSH `authorized_keys` backdoors, cron persistence, obfuscated payloads) on the
dangerous side. Each script's source and labeling rationale are documented
inline in `data/real_world/build.py`, including the two deliberately hard cases
(a trusted-vendor `curl | sh` installer and a legitimate privileged `apt`
install). To keep the holdout genuinely external, no real-world script is a
near-duplicate of any training sample: the maximum sequence similarity to any
synthetic script is 0.83, and `tests/test_dataset.py` fails the build if any
holdout script exceeds 0.85 similarity. (Corpus deduplication itself uses a
SHA-256 content hash rather than the salted built-in `hash()`, so membership is
stable across runs and interpreters.) The RQ4 experiment
(`experiments/real_world_eval.py`) trains ACTE on the full synthetic corpus,
freezes it, and evaluates once on this holdout, giving a true train-synthetic /
test-real generalization measurement.
