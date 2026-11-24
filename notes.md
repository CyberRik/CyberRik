# Engineering notes

How the projects on my [profile](README.md) were built: the decisions, the fixes that failed first, and the results that argued against me. Each section links to its repository.

---

### [Ancora](https://github.com/CyberRik/Ancora) - a durable execution runtime for AI workflows

AI pipelines lose work for boring reasons: an LLM call 500s, a GPU worker OOMs, a pod gets evicted - and a
multi-step, multi-dollar computation vanishes with no way to resume. Ancora records every side-effecting step
as an immutable event, so a worker can die mid-run and the workflow replays to exact state and continues.
It isn't an agent framework; it's the runtime that belongs underneath one.

**~60s → ~6s kill detection** · **284 tests green** · `mypy --strict` clean · chaos experiments that assert · **[OpenSSF Best Practices: passing](https://www.bestpractices.dev/projects/15907)**

**▶ [Watch the 2:38 demo](https://youtu.be/UVKmMZnP50A)** - the running system end to end, nothing mocked. It closes by SIGKILLing a live worker mid-run and machine-checking that the run recovered correctly: [jump straight to that at 2:01](https://youtu.be/UVKmMZnP50A?t=121).

**Chaos experiments that assert instead of demonstrate.** A demo that kills a worker and ends with a green
checkmark proves nothing - someone has to squint at the UI and agree. The chaos engine is a *test*: it
SIGKILLs a live activity-worker container mid-flight, waits out real recovery, then machine-checks three
invariants from Temporal's own history - no lost state, no re-executed activities, exactly-once effects -
against a recovery-time SLO.

**DAGs from causality, not timestamps.** Workflows are ordinary Python deciding step by step what to
schedule, so the DAG is emergent. Inferring parallelism from timestamps is a flattering lie: a fan-out drawn
as a chain looks perfectly reasonable to anyone who hasn't read the code. Ancora reads Temporal's causality
instead - every `ActivityTaskScheduled` names the workflow task that commanded it.

**Durability is not liveness.** Temporal guarantees state survives any crash; it cannot manufacture progress
out of no capacity. Fault tolerance had to become redundancy - a worker pool where killing one lets
survivors recover.

**The dangerous half of exactly-once is the half-committed effect.** A unique key forbids duplicates for
free. What a kill actually introduces is an effect that *began* and whose worker died before committing,
leaving a stale pending a retry could re-fire.

**Tracing across a process boundary.** A compute function is pickled and shipped to Ray, and OTel's ambient
context doesn't travel with it - the span orphans into its own root trace. Fixed by injecting the W3C
`traceparent` as plain data and re-extracting it worker-side.

📄 [RFC-0001](https://github.com/CyberRik/Ancora/blob/main/docs/RFC-0001-durable-ai-runtime.md) · [Implementation plan](https://github.com/CyberRik/Ancora/blob/main/docs/IMPLEMENTATION-PLAN.md)

---

### [TinyServe](https://github.com/CyberRik/tinyserve) - a from-scratch LLM inference runtime on llama.cpp

Continuous batching, block-based KV-cache accounting, admission control and pluggable fair
scheduling (FIFO / priority / WFQ) - built from scratch in async Python on top of llama.cpp, at a
scale small enough that every latency number traces back to a specific scheduling decision in the
code, not a black box. Not an attempt to beat vLLM/SGLang on throughput - an attempt to build the
same scheduling *ideas* somewhere fully explainable.

**Continuous batching validated with a real POC first** · **97.2% of wall time in `llama_decode()`** (measured, not assumed) · **WFQ bounds unfairness 2.54× vs strict Priority's 3.87×**

**▶ [Watch the 0:45 demo](https://youtu.be/ruPoUDw6xg4)** - the real server, nothing mocked: 16 concurrent streams sharing 2 decode slots, then the same requests under FIFO, Priority and WFQ, hot-swapped on the live server: [jump to the scheduler comparison at 0:25](https://youtu.be/ruPoUDw6xg4?t=25). Run from a browser at 6 requests, so its ratios are smaller than the benchmark's; the ordering is the same.

**Validate the risky bet before building around it.** Real multi-sequence batched decode - one
`llama_decode()` call advancing several independent requests together - was the whole point of the
project and the part most likely to not work. It was proven with a standalone script (two prompts,
one decode call, two independent continuations) before any scheduler, queue or admission layer was
built on top of the assumption.

**What a scheduling policy actually controls, once batching is continuous.** Every active sequence
advances one decode step per tick regardless of policy - that part isn't negotiable. The one honest
lever left is *which waiting request claims a free concurrency slot next*. FIFO, strict Priority and
WFQ are three different, benchmarked answers to exactly that question - measured head-to-head:
FIFO ignores priority entirely (0.45× ratio), strict Priority strongly favors the high-priority class
(3.87×) at real cost to the other, and WFQ bounds that unfairness (2.54×) instead of eliminating the
favoritism.

**A benchmark that argued against its own hypothesis - reported anyway.** Chunked prefill was
expected to visibly protect short requests' tail latency from a long prompt's prefill. It didn't,
measurably, at the scale tested - because the batch builder already sorts sequences by ascending
pending-token count each tick, so short requests are packed in *before* a long prefill regardless of
chunk size. The mechanism was traced and written up as a negative result, not tuned until a
difference appeared.

**Self-audit found a real gap in the admission controller before it shipped.** A pre-release
engineering audit against the original design doc found the admission controller was only checking
KV-cache budget - missing the queue-depth backpressure check the design called for, meaning a burst
of many small-footprint requests could grow the wait queue unboundedly. Fixed and verified live: with
a deliberately small queue cap, exactly the expected split of requests was accepted vs. rejected with
a distinct `queue_full` reason, not just "it compiles."

**Cross-checking a profiler against your own metric, not eyeballing either alone.** A real `py-spy`
sampling session found 97.2% of wall time inside `llama_decode()`; that fraction was then checked
quantitatively against the server's own `decode_step_duration_seconds` histogram from the same
window - independent agreement, not a single unverified reading.

---

### [senpai](https://github.com/CyberRik/senpai) - enterprise AI execution platform

Decomposes a request into a capability graph, resolves it as a dependency-aware DAG, and executes nodes
against retrieval and tool backends. Sales coaching is a judgement task where a confidently invented win
rate is worse than no answer - so grounding is mechanical, not prompted.

**About 70 tok/s** on a single Qwen3.6-35B MoE (about 3B active per token), against roughly 10 on the 27B it replaced

**Profile before optimising.** The platform was correct but slow, and the obvious suspects were wrong.
Instrumenting a turn showed generation was **98% of wall time**; tool execution 0.8%, retrieval ~1%. The real
cost was structural - the tool-selection round ran with `tool_choice="auto"`, so when the model decided no
further tools were needed it generated the entire answer just to signal that, and synthesis then threw it
away and regenerated. **Long turns paid for their answer twice.**

**Two failed fixes before the right one.** Capping `max_tokens` truncated long tool calls. Streaming and
aborting on answer prose broke tools that emit a preamble. Both reverted. What worked was removing the
ambiguity rather than policing it: `tool_choice="required"` plus a `finish` sentinel tool, so selection can
no longer generate a throwaway answer *because it can no longer generate prose at all*.

**Grounding as a whitelist, not an instruction.** Statistics are computed deterministically over a graph of
reps, deals, customers and products; the LLM only translates them to prose. Every number in the generated
text is extracted by regex and checked against a whitelist of the report's real figures - unlisted number,
text discarded. A model told not to invent statistics still will. One that structurally cannot publish an
unlisted number won't.

**Model routing decided with data.** A bf16 8B gave only 1.11× - bandwidth-bound. Q4 was the actual lever:
2.72× wall, 3.8× decode, at measured grounding parity (0.969 vs 0.969), cutting the slowest workflow from
334s to 152s. Style was the cost, not accuracy. That 27B/8B split was later retired: one MoE now does both tool
selection and synthesis, at about 70 tok/s with thinking off.

---

### [tool-calling-bfcl](https://github.com/CyberRik/tool-calling-bfcl) - function-calling model training

Synthetic-data pipelines, QLoRA fine-tuning of Qwen3-8B on an NVIDIA DGX Spark, and an automated eval
harness scored against the Berkeley Function-Calling Leaderboard.

**86.6%** across 8 BFCL v4 single-turn categories · **97.0%** on `simple_python` · **50K+** synthetic training examples

**The loss was being computed on the wrong tokens.** The original pipeline trained with full-sequence causal
loss, so gradients flowed through system prompts, user turns, inlined schemas and tool results - on
tool-heavy examples the model was optimising *conversation mimicry*. Underneath sat a quieter bug: the pad
token was set to EOS, and the collator masks labels wherever input matches the pad id, so turn terminators
were dropped from the loss **exactly where truncated JSON and EOS bailout were the observed failures**. The
uncomfortable consequence - every checkpoint from before the fix was optimising a different objective, so
those comparisons were thrown out rather than reinterpreted.

**Negative data did as much work as positive data.** Chat conversations with irrelevant tool schemas
injected, where the correct behaviour is to ignore the tools entirely. A model trained only on examples
where a tool *should* be called learns that a tool should *always* be called.

**Diversity sampling over random sampling.** Random blending oversamples the domains the source datasets
already agree on. Candidates are scored against a coverage report and prioritised for novel tool domains,
above-average conversation depth, and error-recovery patterns.

**A failure taxonomy, because "wrong" isn't a diagnosis.** Malformed and partial JSON are separated -
partial JSON is a generation-length problem, detected by where the parse error falls. Calling the wrong real
tool is distinct from hallucinating one. Inventing, omitting and mistyping arguments are three different
schema failures. There are behavioural categories too, for calling a tool where the model should have asked
a clarifying question - failures any output-shape metric scores as fine.

*Note: training token accuracy lands near 96–97%, the same range as the best `simple_python` score - they
measure entirely different things. Kept separate deliberately.*

---

### [indic-speaker-asr](https://github.com/CyberRik/indic-speaker-asr) - who said what, in multi-speaker Indic audio

Long conversational recordings - 12 hours, 9 Indic scripts, 2 to 8 speakers - diarized, transcribed, and every
word put under the right speaker. Each recording is transcribed **once** and its words assigned to the diarizer's
turns, so every diarizer is compared on identical words and a cpWER difference is purely a labelling difference.
Scored strictly: collar 0, overlapped speech included.

**WER 93.66 → 78.82** from one decoding fix · **cpWER 79.67 → 72.96, 0 of 99 recordings worse** · **DER 27.34** at collar 0 · an LLM relabeller built, measured and rejected

**The model was fine; the decode was wrong.** IndicConformer's output spelled phonetically correct words across
six scripts at once. The CTC head is *multi-softmax* - each language's 256-token block was trained under its own
softmax, so a Kannada logit and a Marathi logit were never meant to be compared, and a global argmax compares
them on every frame. Voting for the recording's language over its frames, then decoding inside that block, took
WER from 93.66 to 78.82. The naive decode stays in the results table as a scored ablation rather than a claim.

**A benchmark nobody can rerun isn't one.** faster-whisper's default temperature fallback re-decodes hard
segments by *sampling*, unseeded: one recording gave 87, 84 and 100 words on three identical runs. At
temperature 0 it gives 211 words every time - reproducible *and* better, and the corpus run fell from 396 to 153
minutes.

**The fix that held was the unglamorous one.** On 13 recordings the model's own language vote picked Urdu or
Nepali, so the whole transcript came out in the wrong script and scored 100% WER regardless of what was heard -
spoken Hindi and Urdu differ mainly in script. Falling back to Whisper when the detected language is outside the
target set cut cpWER to 72.96 with no recording worse. Not fitted to scores: routing Hindi- or Marathi-detected
recordings to Whisper instead made WER *worse* (82.56).

**Measure the ceiling before blaming the model.** LLM speaker relabelling (Qwen2.5-7B, in the spirit of
DiarizationLM) was guarded - confidence threshold, rogue-edit discard, an assertion that text never changes - and
still moved WDER the wrong way, 20.12 → 20.96. An oracle audit explained it: even after splitting at pauses,
**37.87% of words** sit in units spanning two true speakers, where no relabel can help. Its confidences were
always 0.8 or 0.9 - a number, not a signal.

**Look where the error is, not where it's expected.** Only 24% of pyannote's error seconds fall in overlapped
speech; most of it is ordinary single-speaker confusion - so source separation, the obvious next build, was not
the first one.

---

### [reach-asr](https://github.com/CyberRik/reach-asr) - noise-robust speech recognition for telephony audio

**There is no public corpus of real emergency-call audio** - 911 recordings are legally restricted almost
everywhere, for good privacy reasons. So this doesn't claim to have trained on them. It *constructs* the
acoustic condition and states exactly what was constructed: a 300–3400 Hz telephone passband, G.711 μ-law
companding, ESC-50 sirens and traffic at −5 to 10 dB SNR, and 5% packet loss over LibriSpeech speech.
Then it LoRA fine-tunes Whisper on that channel and serves the result over HTTP to
[reach-app](https://github.com/CyberRik/reach-app).

**23.76% → 21.20% WER, −2.56 pp (95% CI −3.85 to −1.31)** · **+0.87 pp cost on clean audio, measured not assumed** · **4.37% clean ceiling** · **30 signal-property and contract tests**

**The first run failed, and the loss curve said it was working.** Loss fell steadily from 1.82 to 0.71 while
WER more than *doubled* - 5.52% to 11.89%, worse in every SNR bucket. The cause was in the targets:
LibriSpeech references are ALL CAPS, Whisper emits cased text, and BPE splits uppercase into far more tokens.
The model spent its capacity learning a formatting change the eval normalizer then strips. It was learning to
shout, not to hear - and the loss curve was a correct measurement against the wrong objective.

**Measure the headroom before spending the GPU.** `whisper-small` scored 3.06% clean and 5.52% degraded on
that channel - 2.5 points of headroom total, and no fine-tune recovers a gap that isn't there. A seven-minute
probe on 200 utterances now runs first: under ~10 points, harden the channel instead of training.

**Four numbers, and the fourth is the one people skip.** Clean zero-shot is the ceiling, degraded zero-shot
the baseline, degraded fine-tuned the result - and clean fine-tuned is what the result cost. Without it,
"it learned to handle phone audio" and "it learned to *only* handle phone audio" are indistinguishable. The
gain is −2.56 pp, CI [1.31, 3.85] over a paired bootstrap; the cost is +0.87 pp on clean, CI [+0.35, +1.40].
Read honestly, that recovers 2.56 of the 19.39 points the channel cost - about 13% of the gap. Real, and
modest.

**One curve, not two effects.** The gain is monotone in SNR even in relative terms - 14.8% / 8.7% / 3.1%
across the bands, then −19.9% on clean. The regression is that curve's endpoint, not a separate finding: the
adapter reallocates capacity along the SNR axis, and it gains most in the low-SNR bucket that actually
matters here.

**The augmentation is the experiment, so it is tested like one.** A single `lowpass_biquad` is 2nd-order and
left ~10% of a 6 kHz tone standing inside a filter claiming to be a telephone passband - understating the
damage would have overstated the gap it produces. Three cascaded sections now. A remaining flaw is documented
rather than hidden: SNR is scaled to a mean over the whole clip, before the channel, so an impulsive noise
clip is nearly absent during the speech and its label is not the condition scored.

---

### [reach-app](https://github.com/CyberRik/reach-app) - R.E.A.C.H., emergency response platform

**Dispatch is the hard part, not the model.** A report arrives from a phone that may be wrong about where it
is, and a responder has to be routed to it while both are still moving. R.E.A.C.H. runs that loop: SOS intake,
live responder tracking over WebSockets, and OSRM routing with the encoded polylines decoded and positions
interpolated between updates - a stale marker on a dispatch map is a *failed* feature, not a degraded one.

Fake reports are screened on EXIF GPS, Haversine against the claimed location within a 3 km tolerance. The
check deliberately **fails open** on stripped metadata: most phones strip EXIF by default, and refusing a
genuine emergency is far worse than admitting a bad report a human will read anyway.

Voice reports capture in the browser through `MediaRecorder` and post to
[reach-asr](https://github.com/CyberRik/reach-asr); if inference is down the recording still saves and plays
back rather than being thrown away. The speech model itself lives in that repo - along with an honest
account of what it was and was not trained on.

Selected from **200+ startups** by IITM NIRMAAN · led a 5-member cross-functional team to MVP

---

### [medproqa](https://github.com/CyberRik/medproqa) - fine-tuned Phi-3 for medical QA

250K+ QA pairs curated from MedQA, MedMCQA and PubMedQA with schema normalisation and dedup - deduplicating
*before* benchmarking, since leakage between the mix and the eval set would have inflated the headline number
into meaninglessness.

**82.6% on MedMCQA** · hallucination **−28%** out-of-distribution · **38%** less GPU memory, **24%** lower training cost

---

### [portfolio](https://github.com/CyberRik/portfolio) - an explorable 3D workspace

A navigable 3D room where each object opens a section - the monitor runs an OS-style shell with Projects and
Timeline apps, architecture diagrams, and full case studies.

Its content layer enforces an **authenticity rule**: unwritten fields hold a marker that renders as a visible
gap, so the site can never quietly fill itself with plausible copy.

[Explore the room ↗](https://ritankar-mondal.vercel.app/)

---

### [smart-fan](https://github.com/CyberRik/smart-fan) - SmartFan, brand intelligence & share-of-voice

Automated sentiment and share-of-voice tracking across Twitter, YouTube and Google APIs. **87% F1** on a
hand-labelled evaluation set - hand-labelled being the part that makes it a claim rather than one model
grading another. Its ingestion design directly informed the GEO retrieval work later built at Gravton Labs.

---

### [path-planning](https://github.com/CyberRik/path-planning) - four RRT variants, benchmarked

**98% success across 1000+ runs** · path length **−27%** via smoothing · runtime **−41%** vs baseline RRT.
The run count exists to beat variance - on randomised planners a handful of runs will rank the variants in
any order you like.

---

### [rerouter-agent](https://github.com/CyberRik/rerouter-agent)

Agentic request routing - dispatching to the appropriate model or tool rather than forcing one path.
