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
  `id, category, label, label_name, rationale, path, provenance, n_chars, n_lines`.
* `scripts/<id>.sh` — the script body for each sample.
