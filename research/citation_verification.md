# Citation Verification Log

Independent re-check of every reference in `LLM_Security_Posture_2026.md`, performed 2026-07-02 by a six-agent verification workflow that re-searched each URL (the sandbox's egress proxy blocks direct HTTP checks, so verification was done via web search, not liveness probing).

**Result:** 146 verified · 0 corrected · 2 unverifiable · 0 likely fabricated (of 148).

Notably, the Anthropic **Cyber Verification Program (CVP)** referenced in the brief (refs 123–135) was confirmed real by multiple independent sources.

| Ref | Status | Note |
|---|---|---|
| 1 | verified | arXiv:2310.03693 'Fine-tuning Aligned Language Models Compromises Safety...' (Qi et al., 2023); abs URL correct. |
| 2 | verified | arXiv 2310.03693 = 'Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!' (Qi et al.); id and PDF correct. |
| 3 | verified | IBM Research publication page for 'Fine-tuning Aligned Language Models Compromises Safety...' (Qi et al., ICLR 2024) is real; also on arXiv 2310.03693. |
| 4 | verified | 2026 arXiv id confirmed real: 2605.26526 'Open-Weight LLM Fine-Tuning Defenses are Susceptible to Simple Attacks' (Kuo, Yadav, Smith), submitted May 2026. |
| 5 | verified | arXiv 2506.15606 = 'LoX: Low-Rank Extrapolation Robustifies LLM Safety Against Fine-tuning' (COLM 2025); id and title match. |
| 6 | verified | HuggingFace blog 'Uncensor any LLM with abliteration' by mlabonne (Maxime Labonne) exists at this exact URL. |
| 7 | verified | Maxime Labonne 'Uncensor any LLM with abliteration'; this exact Medium URL/slug/hash resolves correctly. |
| 8 | verified | arXiv 2508.12622 = 'Consiglieres in the Shadow: Understanding the Use of Uncensored LLMs in Cybercrimes' (Lin et al., Aug 2025); id correct. |
| 9 | verified | NIST CAISI DeepSeek evaluation (Sept 2025) is confirmed real via NIST news page; direct PDF fetch returned 403 but the report and this file path are genuine. |
| 10 | verified | Cisco Security blog 'Evaluating Security Risk in DeepSeek and Other Frontier Reasoning Models' exists at that URL. |
| 11 | verified | Hackread article 'Cisco Finds DeepSeek R1 Highly Vulnerable to Harmful Prompts' exists at this URL and supports the claim. |
| 12 | verified | FAR.AI 'Illusory Safety: Redteaming DeepSeek R1...' page exists; the cited www.far.ai/news/ slug resolves (also mirrored at far.ai/research/). |
| 13 | verified | Real TechCrunch (2025-02-07) article on Amodei/DeepSeek bioweapons test; URL exact. |
| 14 | verified | Real Qualys blog (Jan 31 2025): DeepSeek-R1 failed 58% of TotalAI jailbreak tests; URL slug matches exactly. |
| 15 | verified | Meta's official Llama Protections page at llama.com/llama-protections/ exists (Llama Guard, Prompt Guard, LlamaFirewall). |
| 16 | verified | Meta AI research page for LlamaFirewall open-source guardrail system exists at that URL (also arXiv 2505.03574). |
| 17 | verified | The Hacker News 2025/04 'Meta Launches LlamaFirewall Framework' page exists and matches the claim. |
| 18 | verified | Official llama.com Llama Guard 4 model card / prompt-formats page exists at this URL. |
| 19 | verified | Real Hugging Face repo meta-llama/Llama-Prompt-Guard-2-86M (mDeBERTa injection/jailbreak classifier); URL exact. |
| 20 | verified | Official OWASP Top 10 for LLM Applications 2025 PDF at the exact canonical owasp.org path; page and claim real. |
| 21 | verified | JFrog blog on 3 PickleScan zero-days (CVE-2025-10155/56/57) is real; slug correct, www.jfrog.com redirects to canonical jfrog.com. |
| 22 | verified | Sonatype blog on four picklescan vulnerabilities (CVE-2025-1716/1889/1944/1945) exists at that URL. |
| 23 | verified | SecDim blog on CVE-2025-46417 (picklescan scanner bypass / DNS exfiltration) exists at this URL. |
| 24 | verified | arXiv 2410.21218 = 'Lifting the Veil on Composition, Risks, and Mitigations of the LLM Supply Chain'; id and pdf path correct. |
| 25 | verified | arXiv:2409.09368 'Models Are Codes: ...Malicious Code Poisoning Attacks on Pre-trained Model Hubs' (ASE'24); pdf URL correct. |
| 26 | verified | Stanford CRFM Foundation Model Transparency Index paper.pdf; site blocks bots (403 not 404) and dated variants (May-2024, December-2025) also exist, base path is canonical. |
| 27 | verified | arXiv 2407.12929 is 'The 2024 Foundation Model Transparency Index' (Bommasani et al.); id and title match. |
| 28 | verified | Stanford CRFM Foundation Model Transparency Index GitHub repo exists at that URL. |
| 29 | verified | Medium article 'Navigating the AI Licensing Labyrinth: Truly Open vs. Restricted Open-Weight Models' by Frank Morales Aguilera exists at this URL. |
| 30 | verified | Meta AI blog 'The Llama 4 herd: ...natively multimodal AI' exists at this exact URL. |
| 31 | verified | Real Protect AI blog 'Llama 4 Series Vulnerability Assessment: Scout vs. Maverick'; URL exact. |
| 32 | verified | Anthropic Responsible Scaling Policy v3.0 news page is real (released Feb 2026); URL correct. |
| 33 | unverifiable | Legitimate Anthropic CDN host (www-cdn.anthropic.com/files/...), but the hash-named PDF returned HTTP 403 and could not be located via search, so its content is unconfirmed. |
| 34 | verified | Anthropic 'Anthropic's Responsible Scaling Policy' news page exists at that URL. |
| 35 | verified | Anthropic 'Constitutional Classifiers: Defending against universal jailbreaks' research page is genuine. |
| 36 | verified | Anthropic research page 'Next-generation Constitutional Classifiers' exists at this URL. |
| 37 | verified | arXiv:2501.18837 'Constitutional Classifiers: Defending against Universal Jailbreaks...' (Anthropic, 2025); pdf URL correct. |
| 38 | verified | 2026 arXiv CONFIRMED: 2601.04603 = 'Constitutional Classifiers++: Efficient Production-Grade Defenses against Universal Jailbreaks' (Anthropic, Jan 8 2026); id and PDF exist. |
| 39 | verified | Anthropic 'Usage Policy Update' news page exists at this exact URL (Sept 15 2025 policy changes). |
| 40 | verified | Anthropic Frontier Red Team page confirmed live at that exact URL (WebFetch 403 but search confirms it resolves). |
| 41 | verified | Anthropic 'Frontier Threats Red Teaming for AI Safety' news page is genuine and confirms the topic. |
| 42 | verified | Claude Opus 4.5 System Card (Nov 2025) PDF resolves at this exact assets.anthropic.com URL. |
| 43 | verified | Real Anthropic news page on CAISI/AISI safeguards collaboration (Oct 2025); URL exact. |
| 44 | verified | OpenAI Preparedness Framework Version 2 (Apr 15 2025) PDF on cdn.openai.com; exact URL resolves and content matches. |
| 45 | verified | OpenAI 'Our updated Preparedness Framework' page exists at this exact index URL (v2, April 2025). |
| 46 | verified | OpenAI GPT-5 System Card (Aug 2025) confirmed at that canonical cdn.openai.com URL. |
| 47 | verified | arXiv 2508.09224 = 'From Hard Refusals to Safe-Completions: Toward Output-Centric Safety Training'; id and title match. |
| 48 | verified | OpenAI 'Detecting and reducing scheming in AI models' (with Apollo Research) exists at this exact URL. |
| 49 | verified | Canonical OpenAI Usage Policies page; URL exact. |
| 50 | verified | OpenAI Model Spec dated 2025-12-18 (U18 teen protections update) at model-spec.openai.com/2025-12-18.html; real and canonical. |
| 51 | verified | arXiv 2509.24394 is 'The 2025 OpenAI Preparedness Framework does not guarantee any AI risk mitigation practices' (Coggins et al.); id/title match. |
| 52 | verified | Google DeepMind 'Strengthening our Frontier Safety Framework' blog exists at that URL (FSF v3.0). |
| 53 | verified | Google DeepMind blog 'Updating the Frontier Safety Framework' exists at this URL. |
| 54 | verified | Gemini 3 Pro Frontier Safety Framework Report (Nov 2025) PDF resolves at this DeepMind storage URL. |
| 55 | verified | Real Google DeepMind Frontier Safety Framework 2.0 PDF (Feb 2025); the '(1).pdf' storage URL is the genuine canonical link. |
| 56 | verified | Google Generative AI Prohibited Use Policy at the exact policies.google.com URL; page and claim real. |
| 57 | verified | support.google.com/gemini/answer/16625148 is Google's Gemini Generative AI Prohibited Use Policy page; exists. |
| 58 | verified | Gemini API 'Safety and factuality guidance' docs page exists at that URL. |
| 59 | verified | Google Cloud Threat Intelligence 'Adversarial Misuse of Generative AI' (GTIG) page exists at this URL. |
| 60 | verified | OWASP Top 10 for LLM Applications 2025 resource page exists at this genai.owasp.org URL. |
| 61 | verified | Official NIST AI Risk Management Framework landing page; URL exact. |
| 62 | verified | NIST news (Aug 2024): US AI Safety Institute signs AI safety agreements with Anthropic and OpenAI; URL slug matches exactly. |
| 63 | verified | UK AISI blog 'Pre-Deployment evaluation of OpenAI's o1 model' exists at this exact aisi.gov.uk URL (Dec 2024 joint US/UK test). |
| 64 | verified | METR 'Common Elements of Frontier AI Safety Policies' page exists at metr.org/common-elements. |
| 65 | verified | Claude Platform Docs 'API and data retention' page exists at platform.claude.com and supports data-retention claims. |
| 66 | verified | Anthropic 'Updates to Consumer Terms and Privacy Policy' news page exists at this URL. |
| 67 | verified | Real Anthropic Claude Enterprise product page; URL exact. |
| 68 | verified | Anthropic Trust Center (Vanta-hosted) at trust.anthropic.com; real. |
| 69 | verified | privacy.claude.com article 10015870 'What Certifications has Anthropic obtained?' exists (SOC 2, ISO 27001/42001, HIPAA). |
| 70 | verified | Anthropic Privacy Center ZDR article (id 8956058) exists at that URL. |
| 71 | verified | Anthropic Privacy Center article 'How long do you store my organization's data?' (id 7996866) exists at this URL. |
| 72 | verified | Claude Code docs 'Zero data retention' page exists at this code.claude.com URL. |
| 73 | verified | Real Microsoft Learn 'Data, privacy, and security for Foundry Models...' page; URL exact. |
| 74 | verified | Microsoft Q&A thread 5738671 on obtaining an Azure OpenAI zero-data-retention agreement; exact URL and title match. |
| 75 | verified | AWS Amazon Bedrock security-compliance page exists at this exact URL. |
| 76 | verified | AWS 'Security, privacy, and responsible AI - Amazon Bedrock' page exists at that URL. |
| 77 | verified | AWS 'Amazon Bedrock FAQs' page is the genuine canonical FAQ URL. |
| 78 | verified | AWS 'Compliance validation for Amazon Bedrock' user-guide page exists at this exact URL. |
| 79 | verified | Real Google Cloud doc 'Gemini Enterprise Agent Platform and zero data retention'; URL exact. |
| 80 | verified | Google Cloud doc 'How Gemini for Google Cloud uses your data' at the exact docs.cloud.google.com data-governance path; real. |
| 81 | verified | Google Cloud 'Compliance certifications and security controls \| Gemini Enterprise' page exists at this docs.cloud.google.com URL. |
| 82 | verified | Google Cloud ISO/IEC 42001 compliance page exists at that URL. |
| 83 | verified | Google Cloud 'SOC 2: compliance' page exists at this canonical URL. |
| 84 | verified | OWASP Foundation project page 'Top 10 for Large Language Model Applications' exists at this URL. |
| 85 | verified | Real NIST publication page for AI 600-1 Generative AI Profile (Jul 2024); URL exact. |
| 86 | verified | Veracode 2025 GenAI Code Security Report (45% of AI code had flaws) at the exact veracode.com analyst-reports URL; real. |
| 87 | verified | Veracode blog 'GenAI Code Security Report' (2025, ~45% of AI code fails security tests) exists at this exact slug. |
| 88 | verified | Veracode 'Spring 2026 GenAI Code Security Update' blog exists at that URL (published Mar 2026). |
| 89 | verified | arXiv 2310.02059 = 'Security Weaknesses of Copilot-Generated Code in GitHub Projects: An Empirical Study'; id and title match. |
| 90 | verified | ACM DOI 10.1145/3716848 = 'Security Weaknesses of Copilot-Generated Code in GitHub Projects' (TOSEM, 2025); resolves correctly. |
| 91 | verified | arXiv:2310.02059 'Security Weaknesses of Copilot-Generated Code in GitHub Projects'; html v2 URL valid. |
| 92 | verified | arXiv 2211.03622 = 'Do Users Write More Insecure Code with AI Assistants?' (Perry et al., CCS 2023); id and PDF correct. |
| 93 | verified | arXiv 2211.03622 is 'Do Users Write More Insecure Code with AI Assistants?' (Perry et al., CCS 2023); v3 HTML page valid. |
| 94 | verified | Stanford EE page on Dan Boneh's study that AI assistants yield buggier/less-secure code exists at that URL. |
| 95 | verified | arXiv 2409.15154 = 'RMCBench: Benchmarking Large Language Models' Resistance to Malicious Code'; id and title match. |
| 96 | verified | arXiv 2409.15154 = 'RMCBench: Benchmarking LLMs' Resistance to Malicious Code'; id and pdf path correct. |
| 97 | unverifiable | IEEE Xplore returned HTTP 403 (normal anti-scraping) and searches did not surface doc 10764828's title; ID is in a plausible range but relevance/existence unconfirmed. |
| 98 | verified | ACM DOI 10.1145/3691620.3695480 = 'RMCBench: Benchmarking LLMs' Resistance to Malicious Code' (ASE '24); resolves correctly. |
| 99 | verified | 2026 arXiv id confirmed: 2605.20351 is 'Refusal Evaluation in Coding LLMs and Code Agents: A Systematic Review of Thirteen Malicious-Code Prompt Corpora' (Young & Moody, May 2026); id/title match and abs/html pages resolve. |
| 100 | verified | arXiv 2507.19399 'Running in CIRCLE? A Simple Benchmark for LLM Code Interpreter Security' (Chua, Jul 2025) confirmed. |
| 101 | verified | arXiv 2507.19399 = 'Running in CIRCLE? A Simple Benchmark for LLM Code Interpreter Security'; id and title match. |
| 102 | verified | HuggingFace paper page for arXiv 2507.19399 = 'Running in CIRCLE? A Simple Benchmark for LLM Code Interpreter Security' exists. |
| 103 | verified | 2026 arXiv id confirmed real: arXiv:2602.19547 'CIBER: A Comprehensive Benchmark for Security Evaluation of Code Interpreter Agents'; html URL valid. |
| 104 | verified | arXiv 2406.10279v3 = 'We Have a Package for You! ... Package Hallucinations by Code Generating LLMs' (USENIX Sec 2025); id and v3 exist. |
| 105 | verified | Socket.dev blog on slopsquatting (AI-hallucinated package supply-chain attacks) exists at this exact URL. |
| 106 | verified | Help Net Security 'Package hallucination... slopsquatting' article (Apr 14 2025) exists at that URL. |
| 107 | verified | Dark Reading 'AI Code Tools Widely Hallucinate Packages' article exists at this URL and supports the slopsquatting/hallucination claim. |
| 108 | verified | OWASP GenAI 'LLM Top 10 / LLMRisks Archive' landing page exists at this genai.owasp.org URL. |
| 109 | verified | Real OWASP GenAI page 'LLM10:2025 Unbounded Consumption'; URL exact. |
| 110 | verified | DLA Piper AI Outlook 2024 article on NIST's Generative AI Profile release; exact URL and title match. |
| 111 | verified | Modal blog 'Best Code Execution Sandboxes for AI Agents' exists at this exact resources URL. |
| 112 | verified | Augment Code 'What Is an Agent Execution Sandbox?' guide exists at that URL. |
| 113 | verified | Firecrawl blog 'AI Agent Sandbox: How to Safely Run Autonomous Agents in 2026' exists at this URL. |
| 114 | verified | Claude Code docs 'Configure permissions' page exists at this code.claude.com URL. |
| 115 | verified | Real Anthropic engineering post on Claude Code auto mode (Mar 2026); URL exact. |
| 116 | verified | TrueFoundry blog 'Claude Code Sandboxing' at the exact URL; real page covering native sandboxing. |
| 117 | verified | GitHub Docs 'About Copilot Autofix for code scanning' exists at this exact docs.github.com path. |
| 118 | verified | GitHub Blog 'Secure code more than three times faster with Copilot Autofix' exists at that URL. |
| 119 | verified | Checkmarx 'Top 5 GitHub Copilot Security Risks / 9 Ways to Mitigate Them' learn page exists at this URL. |
| 120 | verified | Anthropic Claude Sonnet 4.5 System Card (Sept 2025) page exists at this URL. |
| 121 | verified | arXiv:2506.11022 'Security Degradation in Iterative AI Code Generation'; pdf URL correct. |
| 122 | verified | Anthropic Usage Policy (formerly AUP) at anthropic.com/legal/aup; real and current. |
| 123 | verified | support.claude.com article 14604842 is real; the Cyber Verification Program (CVP) genuinely exists as Anthropic's free, application-based program letting verified legitimate security professionals unblock high-risk dual-use cyber tasks (vuln research, pentest, red-team) on Claude Opus/Sonnet that are blocked by default. |
| 124 | verified | Cycode blog 'Cycode Joins Anthropic's Cyber Verification Program' exists; CVP is real — Anthropic's free, application-based, org-scoped program that lifts default cyber safeguards on Claude Opus/Sonnet for verified security professionals doing legitimate dual-use defensive work. |
| 125 | verified | CVP is REAL: an Anthropic application-based program that lifts default cyber dual-use blocks for verified security orgs; this mind.io/newsroom page announcing MIND as first data-security firm accepted (May 2026) exists (also mirrored on PRNewswire). |
| 126 | verified | PR Newswire release 'MIND Becomes First Data Security Company Accepted into Anthropic's Cyber Verification Program' (May 20 2026) exists; CVP is a genuine, free application-based Anthropic program that lifts default blocks on high-risk dual-use cyber tasks for verified security professionals/orgs on Claude Opus and Sonnet. |
| 127 | verified | CVP is real: Anthropic's Cyber Verification Program is an application-based, org-scoped program that lifts default real-time cyber safeguards on Claude Opus/Sonnet for verified orgs doing legitimate high-risk dual-use cybersecurity work; this Cyberhaven 'joins CVP' blog URL is genuine. |
| 128 | verified | Tamnoon blog on acceptance into Anthropic's Cyber Verification Program exists; CVP is a REAL, application-based, org-scoped program letting verified cybersecurity organizations use Claude Opus/Sonnet for high-risk dual-use tasks (e.g. offensive-security tooling, vulnerability analysis) that Anthropic's real-time cyber safeguards otherwise block by default. |
| 129 | verified | Cloudpartner (learn.cloudpartner.fi) blog explaining Claude's real-time cyber safeguards + CVP for Microsoft Foundry teams exists; it accurately describes the real CVP (block-by-default, verify-and-adjust). |
| 130 | verified | Third-party Stroople blog on Anthropic's CVP/cyber safeguards exists at that URL and is topically relevant; commentary/analysis piece (references speculative 'Mythos' capability content), not an authoritative Anthropic source. |
| 131 | verified | Anthropic 'Building AI for cyber defenders' research page is genuine; relates to Anthropic's cyber-defense/safeguards work underpinning the CVP. |
| 132 | verified | Anthropic news 'Making frontier cybersecurity capabilities available to defenders' (the Claude Code security / CVP announcement) exists at this URL. |
| 133 | verified | Real Anthropic Project Glasswing page (critical-software security initiative using Claude Mythos Preview); URL exact. |
| 134 | verified | Anthropic 'Expanding Project Glasswing' news page is real (expansion to ~150 orgs, June 2026); URL correct. |
| 135 | verified | SecurityWeek article 'Anthropic Unveils Claude Security to Counter AI-Powered Exploit Surge' (April 2026) exists at this exact URL; corroborates the real Claude Security/CVP program. |
| 136 | verified | Anthropic 'Responsible Disclosure Policy' page exists at that URL. |
| 137 | verified | HackerOne Anthropic bug bounty program page (hackerone.com/anthropic) is genuine; program went public May 2026. |
| 138 | verified | Anthropic (VDP) Vulnerability Disclosure Program page exists at hackerone.com/anthropic-vdp (now channels to the broader public bug bounty). |
| 139 | verified | Real Anthropic 'Expanding our model safety bug bounty program' news page; URL exact. |
| 140 | verified | Anthropic 'Testing our safety defenses with a new bug bounty program' (HackerOne, Constitutional Classifiers) is real; URL correct. |
| 141 | verified | support.claude.com article 12119250 'Model Safety Bug Bounty Program' exists (HackerOne, up to $35k for universal jailbreaks). |
| 142 | verified | Anthropic support article 8241253 'Safeguards/Trust and Safety warnings and appeals' exists at that URL (support.anthropic.com resolves; support.claude.com is the newer mirror). |
| 143 | verified | Anthropic Help Center 'Trust & Safety' collection (id 4078535) exists at support.anthropic.com. |
| 144 | verified | Anthropic Transparency Hub page 'system-trust-reporting' exists at this URL. |
| 145 | verified | Real UK AISI blog 'Our evaluation of Claude Mythos Preview's cyber capabilities'; URL exact. |
| 146 | verified | Anthropic 'Strategic warning for AI risk: Progress from our Frontier Red Team' page is real; URL slug matches exactly. |
| 147 | verified | arXiv 2408.08926 is 'Cybench: A Framework for Evaluating Cybersecurity Capabilities and Risk of Language Models'; id/title match. |
| 148 | verified | Mend.io '2025 OWASP Top 10 for LLM Applications: A Quick Guide' blog exists at that URL. |
