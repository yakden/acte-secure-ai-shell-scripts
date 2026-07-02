# Cover Letter — *Computers & Security* (Elsevier)

*Prepared for submission of the manuscript "Adaptive Trust-Oriented Runtime Security
for AI-Generated Shell Scripts." Fill in the bracketed date and any affiliation before
sending. Recommended target: **Computers & Security**; strong alternatives are
**IEEE Access** (fast, open access) and, for archival visibility, an arXiv preprint.*

---

[Date]

To the Editors-in-Chief,
*Computers & Security*

Dear Editors,

I am submitting the manuscript **"Adaptive Trust-Oriented Runtime Security for
AI-Generated Shell Scripts"** for consideration as a research article in *Computers &
Security*.

Large language models are increasingly used to generate shell scripts that reach
production with little human review. A syntactically clean script can still wipe a
disk, open a reverse shell, or exfiltrate credentials, and the static linters teams
already run were never designed to judge this kind of intent. The manuscript addresses
that gap with **ACTE (Adaptive Context-aware Trust Execution)**, a pre-execution trust
gate that scores a script through a compact, interpretable logistic model over semantic,
execution-context, and threat-intelligence features, adapts online from labelled
outcomes, and compiles its verdict into concrete enforcement artefacts (a seccomp
profile, an Open Policy Agent rule, and namespace/cgroup limits).

The contribution I would emphasise for your readership is not a single accuracy number
but the **rigour and honesty of the evaluation**. On a reproducible corpus the model
reaches F1 = 0.915 at roughly half a millisecond per script; I report this alongside
five-fold and leave-template-out cross-validation, bootstrap confidence intervals, an
independent hand-authored real-world holdout (on which a synthetic-trained, frozen model
keeps zero false positives), and a candid comparison with learned TF-IDF baselines that
match or exceed ACTE on raw F1. I also devote a full Threats-to-Validity section to the
study's genuine limitations — a synthetic, author-generated training corpus; simulated
rather than live enforcement; and the absence of an adaptive-attacker evaluation — and I
discuss how the model's monotonicity property doubles as an evasion vector. The entire
study is reproducible from a public, MIT-licensed repository with a full test suite and
a single-command runner.

I believe the work fits *Computers & Security* because it sits squarely at the
intersection of applied systems security, machine learning, and the emerging risk
surface of AI-assisted software engineering, and because it prioritises reproducibility
and measured claims over headline figures — values the journal is known for.

I confirm that this manuscript is original, has not been published previously, and is
not under consideration elsewhere; that all data and code are openly available; and that
there are no conflicts of interest to declare. The work is archived on Zenodo
(DOI: 10.5281/zenodo.21072886) and the codebase is public.

Thank you for your consideration. I would be glad to suggest reviewers or provide any
further material on request.

Sincerely,

**Denys Yakymov**
ORCID: 0009-0005-2398-8976
Email: yakden@gmail.com
[Affiliation, if any]

---

### Suggested reviewer areas (optional, if the journal asks)
- Runtime security / sandboxing (seccomp-bpf, namespaces, OPA)
- Security of AI-generated code / LLM application security (OWASP LLM Top 10)
- Applied machine learning for intrusion/anomaly detection

### Highlights (Elsevier asks for 3–5 short bullets, ≤85 characters each)
- A pre-execution trust gate scores AI-generated shell scripts in ~0.5 ms.
- Interpretable 13-feature logistic model with online SGD adaptation.
- Trust level compiles to seccomp, OPA/Rego, and cgroup enforcement artefacts.
- Evaluated with cross-validation, bootstrap CIs, and a real-world holdout.
- Honest limits: synthetic training data and simulated enforcement.
