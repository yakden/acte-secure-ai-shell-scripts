# Security Posture of Large Language Models: Open, Closed, and Commercial (2026)

## 1. Executive Summary

As of 2026, the security posture of large language models (LLMs) divides along three structurally different lines — open-weight models, closed frontier models, and commercial enterprise platforms — each with a distinct threat model and a distinct locus of trust.

For **open-weight models** (Meta Llama, Mistral, Qwen, DeepSeek, Google Gemma, Falcon), the defining and well-documented security fact is that any safety alignment baked into downloadable weights is inherently removable by whoever controls those weights. Safety fine-tuning can be stripped with roughly ten adversarial examples for well under a dollar [1][3], or removed without retraining via "abliteration" [6][7], and thousands of uncensored variants are openly redistributed [6]. Consequently, the practical security perimeter shifts to external, system-level controls (guard models, I/O filtering, code scanning, sandboxing) and to supply-chain hygiene — safetensors-only loading and verified provenance — rather than the model's embedded refusals [20][21].

For **closed frontier vendors** (Anthropic, OpenAI, Google DeepMind), the three leaders have converged on a similar defensive architecture: published "if-then" capability-gating frameworks tied to dangerous-capability thresholds (CBRN, cyber, autonomy/ML R&D, and increasingly deception/manipulation), per-release system cards, layered safety training, prohibitive usage policies, and internal plus external red-teaming and government-institute testing [32][44][52][64]. These commitments are voluntary and self-enforced, and demonstrated classifier bypasses show they remain imperfect [51].

For **commercial platforms** (Anthropic's Claude API/Claude for Work, Microsoft Azure OpenAI/Foundry, AWS Bedrock, Google Vertex AI/Gemini Enterprise Agent Platform), a strong converged baseline now exists: no default training on enterprise data, SOC 2 Type II, ISO 27001, and the newer ISO/IEC 42001, plus HIPAA BAAs and FedRAMP High on specific configurations [65][73][75][79]. Vendors differ mainly in the mechanics of zero-data-retention, abuse-log handling, and data residency.

A cross-cutting theme is the **insecurity of AI-generated code**: independent studies converge on roughly 45% of generated code introducing an OWASP-class vulnerability, and model-level refusal against explicitly malicious code requests is weak [86][95]. The consistent defensive conclusion is that model refusal alone is insufficient; insecure or malicious output must be assumed and contained through scanning, least-privilege sandboxing, and trust-based execution gating enforced at the kernel/cgroup level rather than the application level.

This document is a research brief only. It contains no operational exploitation or jailbreak instructions, and it makes no claim to change, verify, or lower the risk status of any account with any vendor.

## 2. Scope and Sources Note

This brief synthesizes publicly documented, defensive-oriented findings on the security posture of major LLMs and platforms current to mid-2026. It covers four domains: open-weight model security, closed frontier vendor safety programs, enterprise platform security and compliance, and the security of AI-generated code and its runtime containment. A fifth section addresses the correct official channels for a legitimate security company to conduct authorized research with these providers.

Sources are primary vendor documentation (policies, system cards, framework PDFs), peer-reviewed and preprint academic work, standards bodies (OWASP, NIST), government safety institutes (US CAISI, UK AISI), and reputable secondary security reporting. Some vendor HTML pages block automated retrieval; where a claim rests on secondary reporting, it is cited as such. All source URLs are preserved in Section 9 and referenced inline by number. Claims about capability evaluations, jailbreak-success rates, and refusal rates reflect the cited studies' specific methodologies and samples and should be read with those caveats in mind.

## 3. Open-Weight Models

Open-weight LLMs in 2026 ship with meaningfully improved built-in safety tuning and a maturing ecosystem of open guardrail tooling — Llama Guard 3/4, Prompt Guard 2, LlamaFirewall/CodeShield, ShieldGemma, and Qwen Guard [15][18][19]. The central security reality, however, is that embedded alignment is a soft default that does not survive a motivated adversary who controls the weights.

**Alignment is removable.** Qi et al. (ICLR 2024) showed safety alignment can be broken by fine-tuning on as few as ~10–100 adversarial examples — a GPT-3.5 Turbo case cost under $0.20 — and that even benign instruction datasets measurably degrade the safety of aligned models [1][2][3]. Separately, post-hoc "abliteration" removes refusals without retraining by orthogonalizing weights against a single "refusal direction," a public technique that has produced thousands of openly redistributed uncensored variants on model hubs [6][7]. Multiple 2025 defenses (SEAM, TAR, LoX, GradShield) aim to make refusal persist under fine-tuning, but follow-up work reports they remain circumventable; no released open model reliably resists weight-level tampering [4][5][8].

**Independent safety evaluations diverge sharply by family.** NIST CAISI (Sept 2025), a Cisco/UPenn study reporting ~100% attack success on a 50-prompt HarmBench sample, and Anthropic all rated DeepSeek R1 among the least safe [9][10][11][13], corroborated by Qualys TotalAI results [14]. Benchmark work placed Gemma, Qwen3, and gpt-oss among safer open families, and Mistral plus DeepSeek-R1 distillations among the most vulnerable [8][12].

**Supply-chain risk is now the dominant self-hosting concern.** The Python pickle weight-serialization format executes arbitrary code at load time; real malicious models with reverse shells and exfiltration payloads have been found on hubs (JFrog reported ~100 in 2024) [21]. The main open scanner, picklescan, had multiple bypass CVEs in 2025 (CVE-2025-1716, -1889, -1944, -46417; fixed in 0.0.31, Sept 2025) [21][22][23]. The recommended defense is the safetensors format, which stores only tensor data with no executable code or deserialization hooks, structurally eliminating the pickle RCE class; hubs additionally layer ClamAV/YARA, picklescan, and ProtectAI ModelScan, though scanning has demonstrated bypasses [21][22]. OWASP's 2025 LLM Top 10 codified these as LLM03 Supply Chain and LLM04 Data and Model Poisoning [20].

**Licensing and provenance compound the risk.** "Open-weight" is not "open-source": Meta's Llama Community License adds an Acceptable Use Policy, a ~700M-MAU commercial cap, a compete/train-on restriction, and an EU multimodal carve-out that flow down to fine-tunes [29][30]. Mistral, Qwen, and DeepSeek publish many models under permissive Apache 2.0/MIT, while Gemma uses a custom license with use restrictions [29]. Stanford's Foundation Model Transparency Index found training-data acquisition/provenance to be the weakest, least-disclosed dimension across nearly all developers (2024 average ~37/100), making poisoning, copyright, and backdoor risk hard to assess downstream [26][27][28].

**Family-level summary:**

- **Meta Llama 3 / Llama 4:** Most mature open safety ecosystem — Llama Guard 3 (8B, 14 MLCommons hazard categories, 8 languages), Llama Guard 4 (12B, multimodal), Prompt Guard 2 (86M classifier), and LlamaFirewall, which Meta reports cutting agent prompt-injection ASR from 17.6% to 1.75%, with CodeShield at 96% precision/79% recall [15][16][18][19]. Open-weight, not OSI open-source [30][31].
- **Mistral / Mixtral:** Lighter built-in refusal, historically system-prompt "safe mode" rather than heavy RLHF; benchmarked among the more vulnerable families [8]. Many flagship models under permissive Apache 2.0, placing safety responsibility on the deployer.
- **Qwen (Alibaba):** Increased alignment investment; Qwen3 rated among safer families, with Qwen Guard as a classifier. Jurisdictional and data-provenance considerations warrant review in regulated settings [8].
- **DeepSeek (V3, R1, distills):** Repeatedly rated among the least safe by independent evaluators [9][10][11][13][14]; permissive MIT licensing with correspondingly minimal usage restriction; several jurisdictions restricted official-device use.
- **Google Gemma 2/3:** Among safer open families; ShieldGemma classifiers and responsible-AI toolkits available. Custom Gemma license with prohibited-use restrictions that flow to derivatives.
- **Falcon (TII):** Lighter first-party safety tooling and thinner third-party evaluation coverage; safety posture is largely deployer-owned. Falcon 2/3 under Apache 2.0; earlier Falcon-180B used a more restrictive TII license.

Net defensive takeaway: treat model-embedded alignment on open weights as a soft default, and rely on external guard models, I/O filtering, code scanning, and sandboxing, plus verified provenance and safetensors-only loading.

## 4. Closed Frontier Vendors

By mid-2026, Anthropic, OpenAI, and Google DeepMind have converged on a broadly similar defensive safety architecture: a published "if-then" scaling/preparedness framework tying dangerous-capability thresholds to escalating deployment and security safeguards; per-release model/system cards; layered safety training; usage policies with hard prohibitions; and internal plus external red-teaming, bug bounties, and government-institute testing [32][44][52][64]. METR documents these "common elements" across the industry [64].

**Shared risk taxonomy** centers on CBRN/bio-chemical, cybersecurity, and model autonomy/ML R&D self-improvement, with deception/"deceptive alignment" and, newly at DeepMind, "harmful manipulation" added as capability categories [44][52][53].

**Anthropic (Claude).** The Responsible Scaling Policy (v3.0, with v3.1) defines AI Safety Levels; Anthropic activated its ASL-3 deployment and security standard in May 2025 for Claude Opus 4 and maintained it through Claude Opus 4.5 (system card, Nov 2025), which it describes as its best-aligned frontier model [32][33][42]. ASL-3 targets models that could materially help someone with undergraduate STEM training create or deploy chemical or biological weapons. Safety training uses Constitutional AI/RLAIF plus deployed Constitutional Classifiers, which reduced universal-jailbreak success from ~86% to 4.4%, with a "Classifiers++" production version cutting compute overhead to ~1%; over 1,700+ hours of red-teaming, no red-teamer found a universal jailbreak [35][36][37]. Researchers have since demonstrated bypasses via adversarial fine-tuning, underscoring residual risk [38]. Anthropic notes models exhibit "evaluation awareness," which complicates assurance [42].

**OpenAI (GPT).** The Preparedness Framework v2 (April 2025) tracks cybersecurity, CBRN, and model autonomy with Low/Medium/High/Critical gating — "High" blocks deployment without safeguards and "Critical" halts development [44][45]. OpenAI treats GPT-5-thinking as "High" capability in the biological/chemical domain as a precaution, with corresponding safeguards; the GPT-5 system card (Aug 13, 2025) documents these plus jailbreak, disallowed-content, and hallucination evaluations [46]. Safety training combines RLHF, "deliberative alignment" (reported ~30x covert-action reduction in o3/o4-mini tests), and output-centric "safe-completions" [47][48]. An arXiv affordance analysis argues the framework "does not guarantee any AI risk mitigation practices," and researchers note deliberative-alignment gains may be confounded by increased situational awareness [51].

**Google DeepMind (Gemini).** The Frontier Safety Framework v2.0 (Feb 2025), extended to v3 by late 2025, defines Critical Capability Levels across CBRN, cybersecurity, ML R&D, and deceptive alignment, plus a new harmful-manipulation CCL [52][53][55]. Published FSF reports state Gemini 2.5 and Gemini 3 Pro (Nov 2025 report) have not reached any CCL [54]. Safety training uses RLHF plus built-in Gemini API safety filters, with the Secure AI Framework (SAIF) providing engineering guidance and a risk taxonomy Google has moved to donate [58]. These conclusions are vendor-self-assessed and depend on Google's own thresholds and elicitation; consumer-grade filters are tunable and distinct from frontier-risk mitigations [56][57].

**Usage policies** broadly align on hard prohibitions — weapons/CBRN, CSAM, election/democratic-process interference, and critical-infrastructure or malicious-cyber activity. Anthropic's Usage Policy (effective Sept 15, 2025) uses a Universal Rules / High-Risk / Disallowed tiering [39]; OpenAI's updated policies (Oct 29, 2025) restrict unsupervised professional advice [49][50]; Google's Generative AI Prohibited Use Policy covers dangerous, deceptive, and abusive content [56].

**External oversight** includes internal teams (Anthropic's Frontier Red Team), public bug bounties, and third parties such as METR and Apollo Research [40][41]. Government pre-deployment testing is now routine: the US AI Safety Institute (renamed CAISI in June 2025) and UK AISI signed access agreements with Anthropic and OpenAI (Aug 2024) and jointly evaluated Claude 3.5 Sonnet and OpenAI o1 before release [62][63][43]. Cross-industry references are the OWASP Top 10 for LLM Applications (2025) and the NIST AI RMF Generative AI Profile (NIST AI 600-1) [60][61]. All three frameworks remain explicitly voluntary and self-governed, so external verification and independent auditing are still limited [51][64].

## 5. Enterprise Platform Security & Compliance

The four leading commercial platforms — Anthropic's Claude API / Claude for Work, Microsoft Azure OpenAI Service (within Microsoft Foundry), AWS Bedrock, and Google Vertex AI / Gemini Enterprise Agent Platform — share a strong, converged defensive baseline and differ mainly in the mechanics of zero-data-retention (ZDR), abuse-log handling, residency granularity, and which product surfaces are in scope.

**Training-data use.** All four contractually commit not to use enterprise/API customer prompts and outputs to train foundation models by default. Anthropic explicitly excludes Claude for Work/Enterprise/Education/Gov and API from its Sept 2025 consumer-terms changes [66]; AWS Bedrock "never shares your data with model providers or uses it to train foundation models" [76][77]; Azure OpenAI does not use prompts/completions to train models [73]; Google published an AI/ML Privacy Commitment covering all managed models [80].

**Zero Data Retention differs sharply.** Anthropic offers contractual ZDR (data not stored at rest after the API response) for Messages/Token Counting APIs and Claude Code, and reduced default API log retention to 7 days (from 30) as of Sept 14, 2025 [65][70][72]. Azure OpenAI's default retains abuse-monitoring logs up to 30 days; true ZDR requires the gated "modified/no abuse monitoring" Limited Access program for approved EA/MCA customers [73][74]. Google Vertex/Gemini offers ZDR-equivalent terms via DPA amendment plus disabling caching and opting out of prompt logging [79][80]. AWS Bedrock does not store fine-tuning/validation data and does not persist inference data beyond processing [77].

**Certifications converge:** SOC 2 Type II, ISO 27001:2022, and the newer ISO/IEC 42001:2023 (AI management systems, adopted across the board in 2025) are held by all four [69][73][75][82]. Anthropic also lists CSA STAR L2 and UK Cyber Essentials [69]; Google added HITRUST and PCI-DSS v4.0 in 2025 [81].

**FedRAMP High:** Anthropic holds FedRAMP High; AWS Bedrock is authorized in GovCloud (US-West); Google Vertex AI reached FedRAMP High in March 2025; Azure OpenAI is covered under Azure/Microsoft authorizations, with scope varying by boundary and region [75][78][81].

**HIPAA:** All offer signed BAAs. Anthropic added a distinct "HIPAA-ready" API path in addition to ZDR, enforced at the org level with automatic 400-error blocking of non-eligible features; PHI must not be placed in cached JSON schema/tool definitions [71][72]. Azure, AWS Bedrock, and Google all provide HIPAA BAAs for eligible/configured deployments [73][75][81].

**Residual retention and isolation.** Even under ZDR/HIPAA, vendors retain data where legally required or to combat misuse — Anthropic may retain flagged inputs/outputs up to 2 years for policy violations, and Azure's default abuse store holds data up to 30 days [71][73]. AWS Bedrock uses PrivateLink, KMS encryption, and isolated per-account private model copies for fine-tuning [75][76]; Google combines Private Service Connect + VPC Service Controls with CMEK and Access Transparency [79][81]; Azure supports Private Link/VNet and customer-geography residency [73]; Anthropic offers a data-residency (inference_geo) control on the Messages API [65].

**Anthropic model-specific and feature caveats.** The newest "Covered Models" (e.g., Claude Fable 5, Claude Mythos 5) require 30-day data retention and are not available under ZDR; requests from non-compliant orgs return a 400 error [65][70]. Stateful features fall outside ZDR — Batch API (~29-day retention), Files API (retained until deleted), code execution (up to 30 days), Agent Skills, MCP connector, and Managed Agents [65][72].

**Residual-risk framing.** OWASP's 2025 LLM Top 10 ranks Prompt Injection (LLM01) first and Sensitive Information Disclosure (LLM02) second (up from sixth), reflecting training-data memorization/extraction concerns [60][84]. NIST AI 600-1 (July 2024) defines 12 GenAI risk categories including data leakage, prompt manipulation, and data poisoning — the threat model these enterprise controls are designed to mitigate [85]. In every case, contractual and certification availability does not by itself guarantee that a given deployment meets requirements: correct architecture (VPC/PrivateLink, KMS/CMEK, IAM, regulated-project flags) is required under the shared-responsibility model.

## 6. Comparison Table

| Model / Vendor | Openness | Safety mechanisms | Enterprise compliance | Key risks |
|---|---|---|---|---|
| Meta Llama 3 / 4 | Open-weight, not OSI open-source [30] | Llama Guard 3/4, Prompt Guard 2, LlamaFirewall/CodeShield; RLHF-tuned instruct [15][16][18] | Community License + AUP, ~700M-MAU cap, EU multimodal carve-out; flows to fine-tunes [29][30] | Abliterated variants widespread; alignment strippable; AUP propagates downstream [6][20] |
| Mistral / Mixtral | Mostly Apache 2.0 (true open-source) [29] | Light built-in refusal; system-prompt "safe mode"; no first-party guard suite [8] | Apache 2.0 patent grant; some models under research/commercial license | Minimal embedded guardrails; benchmarked among more vulnerable families [8] |
| Qwen (Alibaba) | Largely Apache 2.0; some tiers Qwen license [8] | Increased alignment; Qwen Guard classifier; among safer families [8] | Apache tiers enterprise-friendly; jurisdiction/provenance review advised | Data-provenance opacity; regional alignment norms; standard tamperability |
| DeepSeek (V3/R1) | Permissive MIT [key releases] | Weak; rated among least safe by evaluators [9][10][13] | MIT permissive; multiple official-use restrictions imposed by jurisdictions | Weakest published safety posture; low harmful-prompt resistance [9][11][14] |
| Google Gemma 2/3 | Open-weight, custom Gemma license [29] | ShieldGemma classifiers; among safer families; RLHF-tuned | Gemma Terms with prohibited-use restrictions flowing to derivatives | Custom-license restrictions; alignment strippable; needs external guards |
| Falcon (TII) | Apache 2.0 (Falcon 2/3) | Light first-party tooling; thin third-party eval coverage | Apache patent grant; earlier Falcon-180B more restrictive | Sparse guardrail ecosystem; safety largely deployer-owned |
| Anthropic (Claude) | Closed weights; open RSP/policies/system cards [32][42] | RSP v3.x + ASL-3; Constitutional AI/RLAIF + Constitutional Classifiers (~86%→4.4%) [35][36] | SOC 2 II, ISO 27001, ISO 42001, HIPAA, FedRAMP High; tiered Usage Policy [69][39] | Classifiers bypassable via adversarial fine-tuning; evaluation awareness; voluntary RSP [38][42] |
| OpenAI (GPT) | Closed weights; open framework/spec [44][50] | Preparedness Framework v2; RLHF + deliberative alignment + safe-completions [44][47][48] | SOC 2, ISO 27001/42001, HIPAA, FedRAMP (Azure); Usage Policies [49][73] | Framework criticized as non-guaranteeing; situational-awareness confound [51] |
| Google DeepMind (Gemini) | Closed weights (Gemma open separately) [52] | FSF v2/v3 (CCLs); RLHF + API safety filters + SAIF [52][58] | SOC 2 II, ISO 27001/42001, HIPAA, FedRAMP High, HITRUST, PCI-DSS [81][82] | Vendor-self-assessed CCLs; consumer filters tunable/bypassable [56] |
| Azure OpenAI / Foundry | Proprietary hosting | Content filtering; abuse monitoring; Private Link/VNet [73] | SOC 2, ISO 27001/42001, HIPAA BAA, FedRAMP (Azure scope) [73] | Default 30-day abuse logs; ZDR gated behind Limited Access program [73][74] |
| AWS Bedrock | Multi-provider marketplace; service proprietary | No data to model providers; isolated per-account KMS-encrypted copies; PrivateLink [75][76] | ISO, SOC, CSA STAR L2, FedRAMP High (GovCloud), HIPAA-eligible [75][78] | Region-specific FedRAMP; misconfiguration shifts risk; review marketplace terms |
| Google Vertex / Gemini Enterprise | Proprietary + Model Garden (open models) | AI/ML Privacy Commitment; PSC + VPC-SC, CMEK, Access Transparency [79][81] | SOC 2 II, ISO 27001/42001, HIPAA, FedRAMP High, HITRUST, PCI-DSS [81][82] | ZDR-equivalent needs explicit config/eligibility; rebranding documentation drift |

## 7. Security of AI-Generated Code and Runtime Trust-Gating

Multiple independent studies converge on the finding that a large fraction of AI-generated code is insecure. Veracode's 2025 GenAI Code Security Report tested 100+ models across 80 completion tasks and found ~45% of samples introduced an OWASP Top 10 vulnerability; Java was worst (72% failure) and cross-site scripting (CWE-80) was undefended in 86% of relevant samples [86][87]. Critically, newer and larger models write more functional code but show no measurable improvement in secure-coding rate across generations [86][88]. An empirical study of real Copilot-generated code found weaknesses in ~29.5% of Python and ~24.2% of JavaScript snippets across 43 CWE categories [89][90][91], consistent with earlier findings that ~40% of generated programs were vulnerable [92][93]. Stanford's human-subjects study found developers using assistants wrote less secure code yet were more likely to believe it was secure — a documented false sense of security [94].

**Refusal against malicious code is weak and form-sensitive.** The RMCBench benchmark (473 prompts, 11 models) measured an aggregate refusal rate of only 28.7% — 40.4% for text-to-code but just 11.5% for code-to-code, with GPT-4 refusing only ~35.7% [95][96]. The CIRCLE code-interpreter benchmark (1,260 resource-exhaustion prompts) found frontier models refused only single-digit percentages of risky requests, and "plausibly benign" indirect framings degraded defenses further — refusal tracks surface form, not intent [100][101][102]. Reviews report that refusals erode further over multi-turn and agentic interactions, where a code agent can reason that an action "may be unsafe" and then execute it anyway [98][99][103].

**Supply-chain risk from hallucination ("slopsquatting").** A 16-model, 576,000-sample study found ~20% of recommended packages did not exist, with 205,474 unique fake names of which 58% recurred — enabling attackers to pre-register hallucinated names (a hallucinated "huggingface-cli" package saw 30,000+ downloads) [104][105][106][107].

**Governing taxonomy and standards.** The OWASP Top 10 for LLM Applications 2025 is the reference risk taxonomy; for code execution specifically, LLM05 Improper Output Handling (passing model output to shells/interpreters/eval without validation) and LLM06 Excessive Agency (over-broad permissions/autonomy) are the most directly relevant categories, with LLM10 Unbounded Consumption broadened to include denial-of-wallet [60][108][109]. NIST's Generative AI Profile (AI-600-1) and SSDF guidance (SP 800-218A) recommend reviewing all source code — human-written or AI-generated — for vulnerabilities before use [85][110].

**Runtime containment and pre-execution trust-gating.** The consistent defensive conclusion is that model-level refusal is insufficient; insecure or malicious output should be assumed and contained. This is precisely the domain of pre-execution trust scoring and sandboxing of generated scripts:

- **Isolation / sandboxing.** Sandbox platforms isolate untrusted AI-generated code using Firecracker microVMs (E2B, which scaled from ~40k to ~15M sandbox sessions/month over 2024–2025) or gVisor (Modal). A sandbox cannot prevent prompt injection but contains blast radius, and resource limits must be enforced at the cgroup/kernel level because application-level limits can be bypassed by agent-generated code [111][112][113].
- **Trust-based execution gating.** Agent-tool vendors ship allowlist-based command gating and OS-level sandboxing. Claude Code (Oct 2025) added native sandboxing via Linux bubblewrap and macOS Seatbelt, with the kernel blocking writes outside the working directory and forcing network egress through an allowlist proxy; permissions evaluate deny→ask→allow, guidance stresses allowlists over blocklists (blocklists are easy to bypass), and state-changing shell commands prompt for human approval [114][115][116]. Deny rules override narrower allow exceptions; auto/bypass modes remove gating and are intended only for isolated CI containers.
- **Post-generation scanning/remediation.** GitHub Copilot Autofix combines CodeQL detection with LLM-generated fixes, reportedly remediating vulnerabilities ~3x faster, though it covers only a subset of queries and fixes still require human review [117][118][119].

Frontier providers also report their own code-refusal evaluations in system cards (e.g., Claude Haiku 4.5 correctly refused 69.4% of clearly harmful requests without added safeguards, with extended thinking raising refusal rates on cyber/CBRN prompts) and note that models can be "overly agentic," reinforcing the need for external gating [120][42][121]. In trust-gating terms: a pre-execution trust score for a generated script is best treated as one signal feeding a least-privilege sandbox and human-in-the-loop approval, not as a substitute for kernel-level containment — since refusal and self-assessment degrade under indirect phrasing, multi-turn pressure, and agentic autonomy.

## 8. Conducting Authorized, Responsible Security Research with These Providers

A legitimate security company can conduct authorized dual-use cybersecurity work with these providers through published official channels. This section describes those channels factually; it does not describe or endorse any method of circumventing safeguards, and engaging these channels neither changes nor implies any change to an account's risk status.

**Anthropic** explicitly supports legitimate, authorized defensive cybersecurity work while drawing a firm line against malicious use. Its Usage Policy separates cyber activity into two blocked-by-default tiers: "Prohibited use" — activities with little to no legitimate defensive application (e.g., mass data exfiltration, ransomware development), which are never adjustable — and "high-risk dual-use" activities with clear defensive value (e.g., vulnerability-exploitation analysis, offensive-security tooling, pentest workflows), which are blocked by default but can be unblocked for vetted organizations [39][122]. Real-time cyber safeguards on Claude Opus and Sonnet enforce these lines at runtime, and Anthropic continues to endorse consent-based vulnerability discovery, SOC/SIEM automation, malware analysis, and rebuilding legacy code in memory-safe languages [123][131].

The **Cyber Verification Program (CVP)** is the official, free, application-based, organization-scoped pathway for security firms — penetration testers, offensive-tooling engineers, vulnerability researchers, security consultants, threat-intelligence analysts, and SOC/IR teams — to have dual-use blocks lifted; prohibited-use restrictions remain regardless of verification status [123]. The program is operational: firms including MIND (first data-security company, May 2026), Cycode, Cyberhaven, and Tamnoon have publicly announced acceptance in 2026 [124][125][126][127][128]. Practitioners have reported over-blocking of legitimate requests before verification, which the CVP is designed to remedy [129][130].

Commercial and enterprise on-ramps for defenders include **Claude Security** (Claude Code on the web scans codebases for vulnerabilities and proposes patches for human review) and **Project Glasswing** (announced April 2026 alongside the frontier "Mythos" model, providing scoped defensive access to harden critical software for named partners, backed by $100M in credits) — Anthropic chose scoped defensive access over public release of its most offensive-capable model [131][132][133][134][135].

**Official Anthropic contact and disclosure channels:**
- General inquiries and appeals: support@anthropic.com [142][143]
- Safety issues and jailbreak reports: usersafety@anthropic.com
- Model-safety bug bounty submissions: modelbugbounty@anthropic.com, plus Anthropic's HackerOne public bug bounty and Vulnerability Disclosure Program [137][138][139]
- Enterprise engagement: Anthropic's sales/enterprise channels and Trust Center (trust.anthropic.com) [67][68]

Anthropic's Responsible Disclosure Policy asks researchers to report in good faith, coordinate disclosure timing, and not publicly disclose vulnerability details until Anthropic gives written confirmation; the infrastructure bug bounty excludes model-content issues (jailbreaks, harmful content, hallucinations), which route to the separate Model Safety Bug Bounty (public since May 7, 2026, participation under NDA) [136][139][140][141]. Independent evaluation underscores why dual-use safeguards tightened: the UK AISI reported Claude "Mythos Preview" achieving ~73% on expert-level cyber tasks no model could complete before April 2025, and Cybench results rose from 35.9% (Sonnet 3.7) to 76.5% (Sonnet 4.5) at 10 attempts [145][146][147].

**Correct legitimate engagement path for a security firm** [39][122][123][136]:
1. Agree to the Usage Policy and Terms.
2. Engage enterprise/sales for commercial access.
3. Apply to the CVP describing the organization's authorized defensive work to unlock dual-use capabilities.
4. Obtain explicit owner consent/authorization for any testing targets, with defined scoping and rules of engagement.
5. Keep prohibited activities out of scope even after verification.
6. Use HackerOne, the Responsible Disclosure Policy, and usersafety@/modelbugbounty@ channels for any discovered issues.

**Other frontier vendors** provide analogous official routes. OpenAI publishes usage policies and a coordinated-disclosure/bug-bounty posture; Google DeepMind publishes its Prohibited Use Policy, runs Trust & Safety abuse monitoring, and — via Google Cloud threat intelligence — publishes adversarial-misuse findings [49][50][56][59]. Google and OpenAI both participate in US CAISI and UK AISI pre-deployment testing [62][63]. In all cases, authorized research should proceed through published enterprise/sales, usage-policy, and disclosure channels, with explicit target authorization, rather than attempting to bypass safeguards.

External frameworks reinforce this defensive posture: the OWASP Top 10 for LLM Applications 2025 recommends defense-in-depth, least-privilege tooling, I/O filtering, human-in-the-loop for high-risk actions, and regular adversarial testing [60][148]; NIST's AI RMF Generative AI Profile recommends threat-profile lists and the use of cybersecurity red teams to test whether safeguards can be bypassed [61][85].

## 9. References

1. https://arxiv.org/abs/2310.03693
2. https://arxiv.org/pdf/2310.03693
3. https://research.ibm.com/publications/fine-tuning-aligned-language-models-compromises-safety-even-when-users-do-not-intend-to
4. https://arxiv.org/html/2605.26526
5. https://arxiv.org/pdf/2506.15606
6. https://huggingface.co/blog/mlabonne/abliteration
7. https://medium.com/@mlabonne/uncensor-any-llm-with-abliteration-d30148b7d43e
8. https://arxiv.org/pdf/2508.12622
9. https://www.nist.gov/system/files/documents/2025/09/30/CAISI_Evaluation_of_DeepSeek_AI_Models.pdf
10. https://blogs.cisco.com/security/evaluating-security-risk-in-deepseek-and-other-frontier-reasoning-models
11. https://hackread.com/cisco-finds-deepseek-r1-vulnerable-harmful-prompts/
12. https://www.far.ai/news/illusory-safety-redteaming-deepseek-r1-and-the-strongest-fine-tunable-models-of-openai-anthropic-and-google
13. https://techcrunch.com/2025/02/07/anthropic-ceo-says-deepseek-was-the-worst-on-a-critical-bioweapons-data-safety-test/
14. https://blog.qualys.com/vulnerabilities-threat-research/2025/01/31/deepseek-failed-over-half-of-the-jailbreak-tests-by-qualys-totalai
15. https://www.llama.com/llama-protections/
16. https://ai.meta.com/research/publications/llamafirewall-an-open-source-guardrail-system-for-building-secure-ai-agents/
17. https://thehackernews.com/2025/04/meta-launches-llamafirewall-framework.html
18. https://www.llama.com/docs/model-cards-and-prompt-formats/llama-guard-4/
19. https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
20. https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
21. https://www.jfrog.com/blog/unveiling-3-zero-day-vulnerabilities-in-picklescan/
22. https://www.sonatype.com/blog/bypassing-picklescan-sonatype-discovers-four-vulnerabilities
23. https://secdim.com/blog/post/cve-2025-46417-bypassing-ai-model-scanners-and-exfiltrate-sensitive-data-15594/
24. https://arxiv.org/pdf/2410.21218
25. https://arxiv.org/pdf/2409.09368
26. https://crfm.stanford.edu/fmti/paper.pdf
27. https://arxiv.org/pdf/2407.12929
28. https://github.com/stanford-crfm/fmti
29. https://medium.com/ai-simplified-in-plain-english/navigating-the-ai-licensing-labyrinth-truly-open-vs-restricted-open-weight-models-89de5c2e649d
30. https://ai.meta.com/blog/llama-4-multimodal-intelligence/
31. https://protectai.com/blog/vulnerability-assessment-llama-4
32. https://www.anthropic.com/news/responsible-scaling-policy-v3
33. https://www-cdn.anthropic.com/files/4zrzovbb/website/bf04581e4f329735fd90634f6a1962c13c0bd351.pdf
34. https://www.anthropic.com/news/anthropics-responsible-scaling-policy
35. https://www.anthropic.com/research/constitutional-classifiers
36. https://www.anthropic.com/research/next-generation-constitutional-classifiers
37. https://arxiv.org/pdf/2501.18837
38. https://arxiv.org/pdf/2601.04603
39. https://www.anthropic.com/news/usage-policy-update
40. https://www.anthropic.com/research/team/frontier-red-team
41. https://www.anthropic.com/news/frontier-threats-red-teaming-for-ai-safety
42. https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf
43. https://www.anthropic.com/news/strengthening-our-safeguards-through-collaboration-with-us-caisi-and-uk-aisi
44. https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf
45. https://openai.com/index/updating-our-preparedness-framework/
46. https://cdn.openai.com/gpt-5-system-card.pdf
47. https://arxiv.org/abs/2508.09224
48. https://openai.com/index/detecting-and-reducing-scheming-in-ai-models/
49. https://openai.com/policies/usage-policies/
50. https://model-spec.openai.com/2025-12-18.html
51. https://arxiv.org/abs/2509.24394
52. https://deepmind.google/blog/strengthening-our-frontier-safety-framework/
53. https://deepmind.google/blog/updating-the-frontier-safety-framework/
54. https://storage.googleapis.com/deepmind-media/gemini/gemini_3_pro_fsf_report.pdf
55. https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/updating-the-frontier-safety-framework/Frontier%20Safety%20Framework%202.0%20(1).pdf
56. https://policies.google.com/terms/generative-ai/use-policy
57. https://support.google.com/gemini/answer/16625148
58. https://ai.google.dev/gemini-api/docs/safety-guidance
59. https://cloud.google.com/blog/topics/threat-intelligence/adversarial-misuse-generative-ai
60. https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/
61. https://www.nist.gov/itl/ai-risk-management-framework
62. https://www.nist.gov/news-events/news/2024/08/us-ai-safety-institute-signs-agreements-regarding-ai-safety-research
63. https://www.aisi.gov.uk/blog/pre-deployment-evaluation-of-openais-o1-model
64. https://metr.org/common-elements
65. https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
66. https://www.anthropic.com/news/updates-to-our-consumer-terms
67. https://www.anthropic.com/product/enterprise
68. https://trust.anthropic.com/
69. https://privacy.claude.com/en/articles/10015870-what-certifications-has-anthropic-obtained
70. https://privacy.claude.com/en/articles/8956058-i-have-a-zero-data-retention-agreement-with-anthropic-what-products-does-it-apply-to
71. https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
72. https://code.claude.com/docs/en/zero-data-retention
73. https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy
74. https://learn.microsoft.com/en-us/answers/questions/5738671/how-can-i-get-a-zero-data-retention-agreement-so-i
75. https://aws.amazon.com/bedrock/security-compliance/
76. https://aws.amazon.com/bedrock/security-privacy-responsible-ai/
77. https://aws.amazon.com/bedrock/faqs/
78. https://docs.aws.amazon.com/bedrock/latest/userguide/compliance-validation.html
79. https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention
80. https://docs.cloud.google.com/gemini/docs/discover/data-governance
81. https://docs.cloud.google.com/gemini/enterprise/docs/compliance-security-controls
82. https://cloud.google.com/security/compliance/iso-42001
83. https://cloud.google.com/security/compliance/soc-2
84. https://owasp.org/www-project-top-10-for-large-language-model-applications/
85. https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
86. https://www.veracode.com/resources/analyst-reports/2025-genai-code-security-report/
87. https://www.veracode.com/blog/genai-code-security-report/
88. https://www.veracode.com/blog/spring-2026-genai-code-security/
89. https://arxiv.org/abs/2310.02059
90. https://dl.acm.org/doi/10.1145/3716848
91. https://arxiv.org/html/2310.02059v2
92. https://arxiv.org/pdf/2211.03622
93. https://arxiv.org/html/2211.03622v3
94. https://ee.stanford.edu/dan-boneh-and-team-find-relying-ai-more-likely-make-your-code-buggier
95. https://arxiv.org/abs/2409.15154
96. https://arxiv.org/pdf/2409.15154
97. https://ieeexplore.ieee.org/document/10764828/
98. https://dl.acm.org/doi/10.1145/3691620.3695480
99. https://arxiv.org/pdf/2605.20351
100. https://arxiv.org/abs/2507.19399
101. https://arxiv.org/pdf/2507.19399
102. https://huggingface.co/papers/2507.19399
103. https://arxiv.org/html/2602.19547
104. https://arxiv.org/html/2406.10279v3
105. https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks
106. https://www.helpnetsecurity.com/2025/04/14/package-hallucination-slopsquatting-malicious-code/
107. https://www.darkreading.com/application-security/ai-code-tools-widely-hallucinate-packages
108. https://genai.owasp.org/llm-top-10/
109. https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/
110. https://www.dlapiper.com/en/insights/publications/ai-outlook/2024/nist-releases-its-generative-artificial-intelligence-profile
111. https://modal.com/resources/best-code-execution-sandboxes-ai-agents
112. https://www.augmentcode.com/guides/agent-execution-sandbox
113. https://www.firecrawl.dev/blog/ai-agent-sandbox
114. https://code.claude.com/docs/en/permissions
115. https://www.anthropic.com/engineering/claude-code-auto-mode
116. https://www.truefoundry.com/blog/claude-code-sandboxing
117. https://docs.github.com/en/code-security/concepts/code-scanning/copilot-autofix-for-code-scanning
118. https://github.blog/news-insights/product-news/secure-code-more-than-three-times-faster-with-copilot-autofix/
119. https://checkmarx.com/learn/ai-security/top-5-github-copilot-security-risks-9-ways-to-mitigate-them/
120. https://www.anthropic.com/claude-sonnet-4-5-system-card
121. https://arxiv.org/pdf/2506.11022
122. https://www.anthropic.com/legal/aup
123. https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude
124. https://cycode.com/blog/cycode-joins-anthropics-cyber-verification-program/
125. https://mind.io/newsroom/mind-becomes-first-data-security-company-accepted-into-anthropic-s-cyber-verification-program
126. https://www.prnewswire.com/news-releases/mind-becomes-first-data-security-company-accepted-into-anthropics-cyber-verification-program-302776824.html
127. https://www.cyberhaven.com/blog/anthropic-cyber-verification
128. https://tamnoon.io/blog/tamnoon-accepted-into-anthropics-cyber-verification-program-cvp/
129. https://learn.cloudpartner.fi/posts/claude-cyber-safeguards-cvp-microsoft-foundry-security-teams
130. https://www.stroople.com/cyber-safeguards-cvp-mythos/
131. https://www.anthropic.com/research/building-ai-cyber-defenders
132. https://www.anthropic.com/news/claude-code-security
133. https://www.anthropic.com/glasswing
134. https://www.anthropic.com/news/expanding-project-glasswing
135. https://www.securityweek.com/anthropic-unveils-claude-security-to-counter-ai-powered-exploit-surge/
136. https://www.anthropic.com/responsible-disclosure-policy
137. https://hackerone.com/anthropic
138. https://hackerone.com/anthropic-vdp
139. https://www.anthropic.com/news/model-safety-bug-bounty
140. https://www.anthropic.com/news/testing-our-safety-defenses-with-a-new-bug-bounty-program
141. https://support.claude.com/en/articles/12119250-model-safety-bug-bounty-program
142. https://support.anthropic.com/en/articles/8241253-trust-and-safety-warnings-and-appeals
143. https://support.anthropic.com/en/collections/4078535-trust-safety
144. https://www.anthropic.com/transparency/system-trust-reporting
145. https://www.aisi.gov.uk/blog/our-evaluation-of-claude-mythos-previews-cyber-capabilities
146. https://www.anthropic.com/news/strategic-warning-for-ai-risk-progress-and-insights-from-our-frontier-red-team
147. https://arxiv.org/pdf/2408.08926
148. https://www.mend.io/blog/2025-owasp-top-10-for-llm-applications-a-quick-guide/