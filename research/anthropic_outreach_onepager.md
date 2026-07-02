# Company & Research Summary — for Anthropic outreach

> **How to use this.** This is a one-page dossier to attach when you contact Anthropic
> through the official channels listed at the end. Fill in the bracketed `[...]` fields
> with your company's real details. Do not overstate anything — the value of this
> document is that every claim in it is verifiable. It is **not** a verification
> instrument by itself; it is supporting evidence for a request you make through
> Anthropic's own programs and support.

---

## Who we are

- **Organization:** [legal company name], [country of registration], [year founded]
- **Focus:** Defensive cybersecurity research and engineering — [1-line description, e.g. "runtime security for AI-generated automation"]
- **Team / principal:** Denys Yakymov — ORCID [0009-0005-2398-8976](https://orcid.org/0009-0005-2398-8976) · yakden@gmail.com
- **Website / registration / references:** [company site], [any certifications, e.g. ISO 27001], [notable customers or partners if shareable]

## What we do and why it is legitimate

We build **defensive** tooling that detects and contains dangerous behaviour in
automatically-generated code. Our published, peer-reproducible flagship project is
**ACTE (Adaptive Context-aware Trust Execution)** — a pre-execution trust gate that
scores AI-generated shell scripts and compiles the verdict into enforcement policy
(seccomp / OPA / cgroup). It is open, archived, and reproducible:

- **Paper (archived, citable):** DOI [10.5281/zenodo.21072886](https://doi.org/10.5281/zenodo.21072886)
- **Code & data:** https://github.com/yakden/acte-secure-ai-shell-scripts (MIT-licensed; full test suite and one-command reproduction)
- **Supporting research:** an internal cited brief on the security posture of open/closed/commercial LLMs (available on request)

## Why our usage can resemble dual-use — and how we handle it

Detection research is inherently dual-use: to teach a system to recognise a reverse
shell, a device wipe, or an obfuscated download-and-run, we must **analyse and label
examples of exactly those techniques**. This can trigger automated safety filters even
though the intent and output are purely defensive. We operate accordingly:

- We work only on **authorized, defensive** problems (detection, sandboxing, policy generation) — never operational offense or evasion for misuse.
- Our datasets are **synthetic or drawn from already-public, well-documented idioms**, clearly labelled, and used to train detectors — consistent with Anthropic's Usage Policy, which permits authorized security research.
- Our work is **published and reproducible**, so our claims and our conduct are auditable.

## What we are asking Anthropic for

1. **Apply to / be evaluated for the Cyber Verification Program (CVP).** Per Anthropic's
   own documentation, the CVP is a free, application-based, organization-scoped program
   that lifts the default real-time cyber safeguards on Claude for **verified security
   organizations** — which is exactly our category of work. We would like to be assessed
   for it.
2. **If our account is currently flagged/limited:** a Trust & Safety review of the
   account with this context, so any restriction reflects our actual (defensive) use.
3. Guidance on the **right commercial footing** (Claude for Work / API / enterprise
   agreement) for a security firm doing this work at scale.

## Official channels (verified)

- **Cyber Verification Program & real-time cyber safeguards** — Anthropic's explainer and application entry point: https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude and the announcement "Making frontier cybersecurity capabilities available to defenders": https://www.anthropic.com/news/claude-code-security
- **Trust & Safety warnings and appeals** (for a flagged account): https://support.anthropic.com/en/articles/8241253-trust-and-safety-warnings-and-appeals
- **Usage Policy** (the basis for our compliance statements above): https://www.anthropic.com/legal/aup
- **Support / account help:** https://support.anthropic.com
- **Enterprise / Sales** (for a company-scoped agreement): https://www.anthropic.com/product/enterprise

## Attachments we can provide

- ACTE paper (PDF) and the Zenodo record
- Link to the open-source repository (code, data, tests, reproduction command)
- The LLM security-posture research brief (with its citation-verification log)
- [Company registration / certifications / prior responsible-disclosure history, if available]

*All URLs above were independently verified on 2026-07-02. This document makes no claim
to alter account status; it supports a request made through Anthropic's official programs.*
