"""Fetch a real, third-party BENIGN shell-script corpus from public GitHub.

Why this exists
---------------
Every script ACTE has been evaluated on so far was written by the project author
(synthetic corpus, real-world holdout) or is author-labelled. The sharpest
external test we can run without live-LLM access or a second human annotator is
to measure ACTE's headline property — its false-positive rate — on
*genuinely third-party* benign scripts that nobody on this project wrote: the
install and setup scripts of mainstream open-source projects. Many of them use
exactly the patterns a naive detector over-flags (``curl | bash``, ``sudo``,
piping remote content, writing under ``/usr``), so they are real hard negatives.

Labels here are by provenance: these files ship as the official, widely-run
installers of popular tools, so their ground-truth label is *safe* (0). This is
an external-data / external-provenance test; it is NOT independent human
annotation with inter-rater agreement (that, and a real third-party *dangerous*
corpus and real LLM outputs, remain future work — see ``tools/``).

Only script *text* is fetched, for static analysis; nothing is executed. The
fetch is network-guarded: unreachable URLs are skipped and reported, never
fabricated. Re-running overwrites the manifest with whatever is currently
reachable.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, "scripts")
MANIFEST = os.path.join(HERE, "manifest.jsonl")

# (id, raw_url, provenance) -- all benign, label 0 by provenance.
_SOURCES: List[Tuple[str, str, str]] = [
    ("ext_nvm_install", "https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh", "nvm-sh/nvm"),
    ("ext_ohmyzsh_install", "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh", "ohmyzsh/ohmyzsh"),
    ("ext_rbenv_installer", "https://raw.githubusercontent.com/rbenv/rbenv-installer/main/bin/rbenv-installer", "rbenv/rbenv-installer"),
    ("ext_nodesource_setup", "https://raw.githubusercontent.com/nodesource/distributions/master/scripts/deb/setup_20.x", "nodesource/distributions"),
    ("ext_rustup_init", "https://raw.githubusercontent.com/rust-lang/rustup/master/rustup-init.sh", "rust-lang/rustup"),
    ("ext_helm_get3", "https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3", "helm/helm"),
    ("ext_pyenv_installer", "https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer", "pyenv/pyenv-installer"),
    ("ext_docker_install", "https://raw.githubusercontent.com/docker/docker-install/master/install.sh", "docker/docker-install"),
    ("ext_homebrew_install", "https://raw.githubusercontent.com/Homebrew/install/master/install.sh", "Homebrew/install"),
    ("ext_ohmyposh_install", "https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/main/packages/nix/build.sh", "JanDeDobbeleer/oh-my-posh"),
    ("ext_starship_install", "https://raw.githubusercontent.com/starship/starship/master/install/install.sh", "starship/starship"),
    ("ext_deno_install", "https://raw.githubusercontent.com/denoland/deno_install/master/install.sh", "denoland/deno_install"),
    ("ext_zoxide_install", "https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh", "ajeetdsouza/zoxide"),
    ("ext_atuin_install", "https://raw.githubusercontent.com/atuinsh/atuin/main/install.sh", "atuinsh/atuin"),
    ("ext_volta_install", "https://raw.githubusercontent.com/volta-cli/volta/main/dev/unix/volta-install.sh", "volta-cli/volta"),
    ("ext_sdkman_install", "https://raw.githubusercontent.com/sdkman/sdkman-cli/master/src/main/bash/sdkman-install.sh", "sdkman/sdkman-cli"),
    ("ext_asdf_install", "https://raw.githubusercontent.com/asdf-vm/asdf/master/asdf.sh", "asdf-vm/asdf"),
    ("ext_bun_install", "https://raw.githubusercontent.com/oven-sh/bun/main/src/cli/install.sh", "oven-sh/bun"),
    ("ext_fnm_install", "https://raw.githubusercontent.com/Schniz/fnm/master/.ci/install.sh", "Schniz/fnm"),
    ("ext_k3s_install", "https://raw.githubusercontent.com/k3s-io/k3s/master/install.sh", "k3s-io/k3s"),
    ("ext_uv_install", "https://raw.githubusercontent.com/astral-sh/uv/main/scripts/install.sh", "astral-sh/uv"),
    ("ext_gitflow_install", "https://raw.githubusercontent.com/nvie/gitflow/develop/contrib/gitflow-installer.sh", "nvie/gitflow"),
    ("ext_tpm_install", "https://raw.githubusercontent.com/tmux-plugins/tpm/master/bin/install_plugins", "tmux-plugins/tpm"),
    ("ext_p10k_wizard", "https://raw.githubusercontent.com/romkatv/powerlevel10k/master/gitstatus/install", "romkatv/powerlevel10k"),
    ("ext_micro_install", "https://raw.githubusercontent.com/zyedidia/micro/master/tools/install.sh", "zyedidia/micro"),
    ("ext_kubectl_krew", "https://raw.githubusercontent.com/kubernetes-sigs/krew/master/hack/download-vendored-yaml.sh", "kubernetes-sigs/krew"),
    ("ext_certbot_dev", "https://raw.githubusercontent.com/certbot/certbot/main/tools/venv.py", "certbot/certbot"),
    ("ext_nginx_ci", "https://raw.githubusercontent.com/nginx/nginx/master/configure", "nginx/nginx"),
    ("ext_ansible_hacking", "https://raw.githubusercontent.com/ansible/ansible/devel/hacking/env-setup", "ansible/ansible"),
    ("ext_prometheus_build", "https://raw.githubusercontent.com/prometheus/prometheus/main/scripts/build_uikit.sh", "prometheus/prometheus"),
    ("ext_kind_build", "https://raw.githubusercontent.com/kubernetes-sigs/kind/main/hack/build/init.sh", "kubernetes-sigs/kind"),
    ("ext_neovim_pr", "https://raw.githubusercontent.com/neovim/neovim/master/scripts/pvscheck.sh", "neovim/neovim"),
]


def _curl(url: str) -> str:
    try:
        p = subprocess.run(["curl", "-fsSL", "--max-time", "25", url],
                           capture_output=True, text=True, timeout=30)
        return p.stdout if p.returncode == 0 else ""
    except Exception:
        return ""


def fetch(verbose: bool = True) -> List[dict]:
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    for fn in os.listdir(SCRIPTS_DIR):
        if fn.endswith(".sh"):
            os.remove(os.path.join(SCRIPTS_DIR, fn))

    records, skipped = [], []
    for sid, url, prov in _SOURCES:
        body = _curl(url)
        # keep only plausible shell scripts of reasonable size
        if not body or len(body) < 80 or ("#!" not in body[:200] and "sh" not in prov and "install" not in url):
            skipped.append((sid, url))
            continue
        rel = os.path.join("scripts", f"{sid}.sh")
        with open(os.path.join(HERE, rel), "w", encoding="utf-8") as fh:
            fh.write(body)
        records.append({
            "id": sid, "category": "external_benign", "label": 0,
            "label_name": "safe", "rationale": f"official installer/tool from {prov}",
            "template": "external", "path": os.path.join("external", rel),
            "provenance": "github:" + prov, "source_url": url,
            "n_chars": len(body), "n_lines": body.count("\n"),
        })

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")

    if verbose:
        print(f"fetched {len(records)} real third-party benign scripts; skipped {len(skipped)} unreachable")
        for sid, _ in skipped:
            print("  skipped:", sid)
    return records


if __name__ == "__main__":
    fetch()
