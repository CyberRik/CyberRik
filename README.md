<h1 align="center">Ritankar Mondal</h1>

<p align="center">
  <b>AI Engineer</b> — LLM systems, retrieval, and the infrastructure underneath them
</p>

<p align="center">
  B.Tech Chemical Engineering, <b>IIT Madras</b> (2023–2027) &nbsp;·&nbsp; Chennai, India
</p>

<p align="center">
  <a href="https://ritankar-mondal.vercel.app/">
    <img src="https://img.shields.io/badge/Portfolio-000000?style=flat-square&logo=vercel&logoColor=white" alt="Portfolio" />
  </a>
  <a href="mailto:ritankarmondal123@gmail.com">
    <img src="https://img.shields.io/badge/Email-333333?style=flat-square&logo=maildotru&logoColor=white" alt="Email" />
  </a>
  <a href="https://github.com/CyberRik?tab=repositories">
    <img src="https://img.shields.io/badge/Repositories-181717?style=flat-square&logo=github&logoColor=white" alt="Repositories" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/C++-00599C?style=flat-square&logo=cplusplus&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Temporal-000000?style=flat-square&logo=temporal&logoColor=white" />
  <img src="https://img.shields.io/badge/Ray-028CF0?style=flat-square&logo=ray&logoColor=white" />
  <img src="https://img.shields.io/badge/Airflow-017CEE?style=flat-square&logo=apacheairflow&logoColor=white" />
  <img src="https://img.shields.io/badge/Postgres-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" />
</p>

---

I build LLM-powered applications, retrieval systems, and production backend infrastructure — tool-calling
models, document intelligence, RAG pipelines, and the runtimes they execute on. Hands-on across the full
loop: data curation, training, evaluation, and deployment.

The through-line in most of my work is **verification** — a system that claims fault tolerance should have a
test that asserts it, a model that cites a statistic should be structurally unable to invent one, and a
benchmark is only worth the things it holds fixed.

**Currently:** SDE Intern at **Otsuka Corporation**, Tokyo · building [Ancora](https://github.com/CyberRik/Ancora) · graduating 2027.

> Each project below opens — the summary is the claim, the dropdown is how it was earned.

---

## Featured

### [Ancora](https://github.com/CyberRik/Ancora) — a durable execution runtime for AI workflows

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/Temporal-000000?style=flat-square&logo=temporal&logoColor=white" /> <img src="https://img.shields.io/badge/Ray-028CF0?style=flat-square&logo=ray&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" /> <img src="https://img.shields.io/badge/OpenTelemetry-425CC7?style=flat-square&logo=opentelemetry&logoColor=white" /> <img src="https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white" />

AI pipelines lose work for boring reasons: an LLM call 500s, a GPU worker OOMs, a pod gets evicted — and a
multi-step, multi-dollar computation vanishes with no way to resume. Ancora records every side-effecting step
as an immutable event, so a worker can die mid-run and the workflow replays to exact state and continues.
It isn't an agent framework; it's the runtime that belongs underneath one.

**~60s → ~6s kill detection** · **284 tests green** · `mypy --strict` clean · chaos experiments that assert

<details>
<summary><b>Engineering notes</b></summary>

<br/>

**Chaos experiments that assert instead of demonstrate.** A demo that kills a worker and ends with a green
checkmark proves nothing — someone has to squint at the UI and agree. The chaos engine is a *test*: it
SIGKILLs a live activity-worker container mid-flight, waits out real recovery, then machine-checks three
invariants from Temporal's own history — no lost state, no re-executed activities, exactly-once effects —
against a recovery-time SLO.

**DAGs from causality, not timestamps.** Workflows are ordinary Python deciding step by step what to
schedule, so the DAG is emergent. Inferring parallelism from timestamps is a flattering lie: a fan-out drawn
as a chain looks perfectly reasonable to anyone who hasn't read the code. Ancora reads Temporal's causality
instead — every `ActivityTaskScheduled` names the workflow task that commanded it.

**Durability is not liveness.** Temporal guarantees state survives any crash; it cannot manufacture progress
out of no capacity. Fault tolerance had to become redundancy — a worker pool where killing one lets
survivors recover.

**The dangerous half of exactly-once is the half-committed effect.** A unique key forbids duplicates for
free. What a kill actually introduces is an effect that *began* and whose worker died before committing,
leaving a stale pending a retry could re-fire.

**Tracing across a process boundary.** A compute function is pickled and shipped to Ray, and OTel's ambient
context doesn't travel with it — the span orphans into its own root trace. Fixed by injecting the W3C
`traceparent` as plain data and re-extracting it worker-side.

📄 [RFC-0001](https://github.com/CyberRik/Ancora/blob/main/docs/RFC-0001-durable-ai-runtime.md) · [Implementation plan](https://github.com/CyberRik/Ancora/blob/main/docs/IMPLEMENTATION-PLAN.md)

</details>

---

### [senpai](https://github.com/CyberRik/senpai) — enterprise AI execution platform

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/GraphRAG-1C3C3C?style=flat-square&logo=graphql&logoColor=white" /> <img src="https://img.shields.io/badge/Capability%20Graphs-5A5A5A?style=flat-square" /> <img src="https://img.shields.io/badge/Otsuka%20Corporation-0072CE?style=flat-square" />

Decomposes a request into a capability graph, resolves it as a dependency-aware DAG, and executes nodes
against retrieval and tool backends. Sales coaching is a judgement task where a confidently invented win
rate is worse than no answer — so grounding is mechanical, not prompted.

**5× inference throughput** — 11 → 55 tok/s

<details>
<summary><b>Engineering notes</b></summary>

<br/>

**Profile before optimising.** The platform was correct but slow, and the obvious suspects were wrong.
Instrumenting a turn showed generation was **98% of wall time**; tool execution 0.8%, retrieval ~1%. The real
cost was structural — the tool-selection round ran with `tool_choice="auto"`, so when the model decided no
further tools were needed it generated the entire answer just to signal that, and synthesis then threw it
away and regenerated. **Long turns paid for their answer twice.**

**Two failed fixes before the right one.** Capping `max_tokens` truncated long tool calls. Streaming and
aborting on answer prose broke tools that emit a preamble. Both reverted. What worked was removing the
ambiguity rather than policing it: `tool_choice="required"` plus a `finish` sentinel tool, so selection can
no longer generate a throwaway answer *because it can no longer generate prose at all*.

**Grounding as a whitelist, not an instruction.** Statistics are computed deterministically over a graph of
reps, deals, customers and products; the LLM only translates them to prose. Every number in the generated
text is extracted by regex and checked against a whitelist of the report's real figures — unlisted number,
text discarded. A model told not to invent statistics still will. One that structurally cannot publish an
unlisted number won't.

**Model routing decided with data.** A bf16 8B gave only 1.11× — bandwidth-bound. Q4 was the actual lever:
2.72× wall, 3.8× decode, at measured grounding parity (0.969 vs 0.969), cutting the slowest workflow from
334s to 152s. Style was the cost, not accuracy.

</details>

---

### [tool-calling-bfcl](https://github.com/CyberRik/tool-calling-bfcl) — function-calling model training

<img src="https://img.shields.io/badge/Qwen3--8B-6236FF?style=flat-square" /> <img src="https://img.shields.io/badge/QLoRA-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" /> <img src="https://img.shields.io/badge/NVIDIA%20DGX%20Spark-76B900?style=flat-square&logo=nvidia&logoColor=white" /> <img src="https://img.shields.io/badge/BFCL-5A5A5A?style=flat-square" />

Synthetic-data pipelines, QLoRA fine-tuning of Qwen3-8B on an NVIDIA DGX Spark, and an automated eval
harness scored against the Berkeley Function-Calling Leaderboard.

**97% BFCL accuracy** (single-turn) · **50K+** synthetic training examples

<details>
<summary><b>Engineering notes</b></summary>

<br/>

**The loss was being computed on the wrong tokens.** The original pipeline trained with full-sequence causal
loss, so gradients flowed through system prompts, user turns, inlined schemas and tool results — on
tool-heavy examples the model was optimising *conversation mimicry*. Underneath sat a quieter bug: the pad
token was set to EOS, and the collator masks labels wherever input matches the pad id, so turn terminators
were dropped from the loss **exactly where truncated JSON and EOS bailout were the observed failures**. The
uncomfortable consequence — every checkpoint from before the fix was optimising a different objective, so
those comparisons were thrown out rather than reinterpreted.

**Negative data did as much work as positive data.** Chat conversations with irrelevant tool schemas
injected, where the correct behaviour is to ignore the tools entirely. A model trained only on examples
where a tool *should* be called learns that a tool should *always* be called.

**Diversity sampling over random sampling.** Random blending oversamples the domains the source datasets
already agree on. Candidates are scored against a coverage report and prioritised for novel tool domains,
above-average conversation depth, and error-recovery patterns.

**A failure taxonomy, because "wrong" isn't a diagnosis.** Malformed and partial JSON are separated —
partial JSON is a generation-length problem, detected by where the parse error falls. Calling the wrong real
tool is distinct from hallucinating one. Inventing, omitting and mistyping arguments are three different
schema failures. There are behavioural categories too, for calling a tool where the model should have asked
a clarifying question — failures any output-shape metric scores as fine.

*Note: training token accuracy and BFCL accuracy both land near 96–97% here and measure entirely different
things. Kept separate deliberately.*

</details>

---

### [portfolio](https://github.com/CyberRik/portfolio) — an explorable 3D workspace

<img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" /> <img src="https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white" /> <img src="https://img.shields.io/badge/React%20Three%20Fiber-000000?style=flat-square&logo=react&logoColor=61DAFB" /> <img src="https://img.shields.io/badge/Three.js-000000?style=flat-square&logo=threedotjs&logoColor=white" />

A navigable 3D room where each object opens a section — the monitor runs an OS-style shell with Projects and
Timeline apps, architecture diagrams, and full case studies.

Its content layer enforces an **authenticity rule**: unwritten fields hold a marker that renders as a visible
gap, so the site can never quietly fill itself with plausible copy.

<p><a href="https://ritankar-mondal.vercel.app/"><img src="https://img.shields.io/badge/Explore%20the%20room-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Live site" /></a></p>

---

### [medproqa](https://github.com/CyberRik/medproqa) — fine-tuned Phi-3 for medical QA

<img src="https://img.shields.io/badge/Phi--3-0078D4?style=flat-square&logo=microsoft&logoColor=white" /> <img src="https://img.shields.io/badge/QLoRA-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" /> <img src="https://img.shields.io/badge/Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white" />

250K+ QA pairs curated from MedQA, MedMCQA and PubMedQA with schema normalisation and dedup — deduplicating
*before* benchmarking, since leakage between the mix and the eval set would have inflated the headline number
into meaninglessness.

**82.6% on MedMCQA** · hallucination **−28%** out-of-distribution · **38%** less GPU memory, **24%** lower training cost

---

### [reach-app](https://github.com/CyberRik/reach-app) — R.E.A.C.H., emergency response platform

<img src="https://img.shields.io/badge/Whisper-412991?style=flat-square&logo=openai&logoColor=white" /> <img src="https://img.shields.io/badge/BART-FFD21E?style=flat-square&logo=huggingface&logoColor=black" /> <img src="https://img.shields.io/badge/WebSockets-010101?style=flat-square&logo=socketdotio&logoColor=white" /> <img src="https://img.shields.io/badge/Co--founder%20%26%20AI%20Lead-5A5A5A?style=flat-square" />

Emergency calls are the worst possible input for speech models — noise, panic, cross-talk — and the output
has to be trustworthy enough to dispatch against. Fine-tuned Whisper for real-time transcription, BART
summarisation for the dispatcher, spoof detection at **78% precision**, and SOS dispatch with responder
tracking over WebSockets under constraints where a slow update is a *failed* feature, not a degraded one.

Selected from **200+ startups** by IITM NIRMAAN · led a 5-member cross-functional team to MVP

---

### [smart-fan](https://github.com/CyberRik/smart-fan) — SmartFan, brand intelligence & share-of-voice

<img src="https://img.shields.io/badge/Gemini%202.5%20Flash-8E75B2?style=flat-square&logo=googlegemini&logoColor=white" /> <img src="https://img.shields.io/badge/n8n-EA4B71?style=flat-square&logo=n8n&logoColor=white" />

Automated sentiment and share-of-voice tracking across Twitter, YouTube and Google APIs. **87% F1** on a
hand-labelled evaluation set — hand-labelled being the part that makes it a claim rather than one model
grading another. Its ingestion design directly informed the GEO retrieval work later built at Gravton Labs.

---

### [path-planning](https://github.com/CyberRik/path-planning) — four RRT variants, benchmarked

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" />

**98% success across 1000+ runs** · path length **−27%** via smoothing · runtime **−41%** vs baseline RRT.
The run count exists to beat variance — on randomised planners a handful of runs will rank the variants in
any order you like.

---

### [rerouter-agent](https://github.com/CyberRik/rerouter-agent)

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />

Agentic request routing — dispatching to the appropriate model or tool rather than forcing one path.

---

## Experience

<details open>
<summary><b>Otsuka Corporation</b> — SDE Intern · Tokyo, Japan · <i>May – Jul 2026</i></summary>

<br/>

Synthetic-data pipelines producing 50K+ function-calling examples; QLoRA fine-tuning and automated evals for
Qwen3-8B on NVIDIA DGX Spark; architected **Senpai** — planner-driven capability graphs resolved as
dependency-aware DAGs over GraphRAG. Took inference throughput 5× (11 → 55 tok/s) through prefix caching,
persistent context caching and parallel execution.

</details>

<details>
<summary><b>Gravton Labs</b> — AI Engineer Intern · Ontario, Canada (Remote) · <i>Feb – May 2026</i></summary>

<br/>

Owned the crawl and attribution layer under a GEO visibility platform. Both halves are selection problems
disguised as data problems:

- A crawler with a page budget spends it on whatever URL order it received, drowning in blog posts while
  missing the pricing and comparison pages that actually drive AI answers. **Typed per-page-type budgets**
  with ranked selection and a per-prefix diversity cap decide quality *before* spend.
- Attribution against a global brand list matches everything, which is worse than matching nothing. Scoping
  to a layered candidate map means the system **can honestly return nothing** — which is what makes its
  matches worth anything.
- Migrated the backend from Encore TypeScript to FastAPI microservices on Railway + Supabase, mid-flight,
  while the pipeline kept collecting.
- Audited the Airflow migration metric-by-metric against the original and scored it **38% complete** — a far
  more useful number to hand someone than "mostly migrated."

</details>

<details>
<summary><b>OctonData</b> — Software Engineer Intern · San Francisco (Remote) · <i>Oct – Dec 2025</i></summary>

<br/>

Primary engineer on a document-intelligence platform running **10K+ pages/month** for U.S. tax documents,
where the same logical form arrives as a clean PDF, a phone photo, or a scan with handwriting in the margin.

- Hybrid pipeline that **routes per page** — OCR, CV layout detection, multimodal encoders, LLM fallback —
  because every individual method has a document class it fails on
- Long-document RAG accuracy up **20–30%** via semantic, recursive and hybrid chunking
- 429s from the model API turned out to be a *chunking* problem, not an API one: many small chunks meant many
  calls. Fixed by capping chunks per document and letting size grow, with local MiniLM embeddings so semantic
  splitting costs no API calls at all
- The dangerous merge bug is the one producing a *plausible* number — income figures across chunks should
  sum, invoice totals must not, and a generic recursive merge double-counts silently
- Onboarded **10+ U.S. CPA firms**, cutting manual review time **40%+**

</details>

<details>
<summary><b>Tecnod8.ai</b> — Machine Learning Intern · Remote · <i>Sep – Oct 2025</i></summary>

<br/>

Multilingual document parsing across **5+ languages** including RTL and Devanagari (YOLOv10, PP-DocLayout-L,
PaddleOCR), with ensemble layout inference handling rotation and adaptive scaling. Qwen3-VL for tables,
figures and charts; Gemma embeddings into ChromaDB for retrieval. Ranked **Top 20 nationally** for solo
pipeline contribution; Tecnod8 named to *Forbes India Select 200* during tenure.

</details>

---

## Also here

**Applied ML** — [smartpdf](https://github.com/CyberRik/smartpdf) ·
[house-prices-prediction](https://github.com/CyberRik/house-prices-prediction) ([demo ↗](https://rikk-house-prices-prediction.streamlit.app/)) ·
[stock-price-prediction](https://github.com/CyberRik/stock-price-prediction) ·
[pokemon](https://github.com/CyberRik/pokemon) ·
[langchain-tutorials](https://github.com/CyberRik/langchain-tutorials)

**Frontend** — [nike-landing](https://github.com/CyberRik/nike-landing) ·
[youtube-clone](https://github.com/CyberRik/youtube-clone) ·
[modal-window](https://github.com/CyberRik/modal-window) ·
[pig-game](https://github.com/CyberRik/pig-game) ·
[Guess-the-number](https://github.com/CyberRik/Guess-the-number)

---

## Technical Skills

<table>
<tr><td><b>Languages</b></td><td>
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/C++-00599C?style=flat-square&logo=cplusplus&logoColor=white" />
<img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" />
<img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" />
<img src="https://img.shields.io/badge/Bash-4EAA25?style=flat-square&logo=gnubash&logoColor=white" />
</td></tr>
<tr><td><b>LLM&nbsp;&&nbsp;ML</b></td><td>
<img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" />
<img src="https://img.shields.io/badge/Transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black" />
<img src="https://img.shields.io/badge/QLoRA%20%2F%20LoRA%20%2F%20PEFT-EE4C2C?style=flat-square" />
<img src="https://img.shields.io/badge/Instruction%20Tuning-5A5A5A?style=flat-square" />
<img src="https://img.shields.io/badge/Tool%20%26%20Function%20Calling-5A5A5A?style=flat-square" />
</td></tr>
<tr><td><b>Retrieval</b></td><td>
<img src="https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white" />
<img src="https://img.shields.io/badge/FAISS-0467DF?style=flat-square&logo=meta&logoColor=white" />
<img src="https://img.shields.io/badge/ChromaDB-FF6F61?style=flat-square" />
<img src="https://img.shields.io/badge/GraphRAG-1C3C3C?style=flat-square" />
<img src="https://img.shields.io/badge/Hybrid%20Retrieval%20%26%20Reranking-5A5A5A?style=flat-square" />
</td></tr>
<tr><td><b>Document&nbsp;AI</b></td><td>
<img src="https://img.shields.io/badge/Multimodal%20AI-5A5A5A?style=flat-square" />
<img src="https://img.shields.io/badge/PaddleOCR-0062B0?style=flat-square" />
<img src="https://img.shields.io/badge/YOLOv10-00FFFF?style=flat-square&logo=yolo&logoColor=black" />
<img src="https://img.shields.io/badge/CV%20Layout%20Detection-5A5A5A?style=flat-square" />
</td></tr>
<tr><td><b>Backend</b></td><td>
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
<img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" />
<img src="https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white" />
<img src="https://img.shields.io/badge/AsyncIO-3776AB?style=flat-square&logo=python&logoColor=white" />
</td></tr>
<tr><td><b>Pipelines</b></td><td>
<img src="https://img.shields.io/badge/Temporal-000000?style=flat-square&logo=temporal&logoColor=white" />
<img src="https://img.shields.io/badge/Ray-028CF0?style=flat-square&logo=ray&logoColor=white" />
<img src="https://img.shields.io/badge/Airflow-017CEE?style=flat-square&logo=apacheairflow&logoColor=white" />
<img src="https://img.shields.io/badge/Apify-FF9013?style=flat-square&logo=apify&logoColor=white" />
<img src="https://img.shields.io/badge/n8n-EA4B71?style=flat-square&logo=n8n&logoColor=white" />
<img src="https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white" />
</td></tr>
<tr><td><b>Cloud&nbsp;&&nbsp;Infra</b></td><td>
<img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/GCP-4285F4?style=flat-square&logo=googlecloud&logoColor=white" />
<img src="https://img.shields.io/badge/Azure-0078D4?style=flat-square&logo=microsoftazure&logoColor=white" />
<img src="https://img.shields.io/badge/Modal-7B68EE?style=flat-square" />
<img src="https://img.shields.io/badge/Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white" />
<img src="https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black" />
</td></tr>
<tr><td><b>Observability</b></td><td>
<img src="https://img.shields.io/badge/OpenTelemetry-425CC7?style=flat-square&logo=opentelemetry&logoColor=white" />
<img src="https://img.shields.io/badge/Jaeger-60D0E4?style=flat-square&logo=jaeger&logoColor=black" />
<img src="https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white" />
<img src="https://img.shields.io/badge/Grafana-F46800?style=flat-square&logo=grafana&logoColor=white" />
</td></tr>
</table>

---

## Achievements

- **98.61 percentile** in JEE Mains among 1.2M+ candidates · **Top 450** in WBJEE
- **AIR 71** (Junior Squad) and City Topper — Technothlon Prelims
- **Top 20 nationally** for solo ML pipeline contribution at Tecnod8.ai
- Selected from **200+ startups** by IITM NIRMAAN for R.E.A.C.H.

---

<div align="center">

<img height="150" src="https://github-stats-extended.vercel.app/api?username=CyberRik&show_icons=true&theme=graywhite&hide_border=true&hide_title=true&include_all_commits=true&count_private=true&icon_color=555555&text_color=555555" alt="GitHub statistics" />
<img height="150" src="https://github-stats-extended.vercel.app/api/top-langs/?username=CyberRik&layout=compact&theme=graywhite&hide_border=true&hide_title=true&langs_count=8&text_color=555555" alt="Most used languages" />

<br/><br/>

<sub><b>Currently active</b></sub>

<a href="https://github.com/CyberRik/Ancora"><img src="https://img.shields.io/github/last-commit/CyberRik/Ancora?style=flat-square&label=Ancora&labelColor=181717&color=3FCF8E" alt="Ancora last commit" /></a>
<a href="https://github.com/CyberRik/portfolio"><img src="https://img.shields.io/github/last-commit/CyberRik/portfolio?style=flat-square&label=portfolio&labelColor=181717&color=3FCF8E" alt="portfolio last commit" /></a>
<a href="https://github.com/CyberRik/rerouter-agent"><img src="https://img.shields.io/github/last-commit/CyberRik/rerouter-agent?style=flat-square&label=rerouter-agent&labelColor=181717&color=555555" alt="rerouter-agent last commit" /></a>
<a href="https://github.com/CyberRik/senpai"><img src="https://img.shields.io/github/last-commit/CyberRik/senpai?style=flat-square&label=senpai&labelColor=181717&color=555555" alt="senpai last commit" /></a>

</sub>

</div>
