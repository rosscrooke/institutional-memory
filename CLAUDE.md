# Best Practices for Working with Claude / AI Agents

Extracted from Partner Basecamp workshop materials (day1: Claude Code, Developer
Platform, Prompt Rescue, Diagnosing AI Problems; day2: Evals, Inference Optimization).

---

## 1. Prompt Engineering

- **One prompt, one job.** A single prompt doing classification + extraction + drafting
  at once causes task interference — e.g. empathetic response-drafting language inflates
  urgency, which biases priority classification. Split into a chain of focused steps
  when tasks compete for the model's attention.
- **Say what "empty" means.** An instruction like "always include all JSON fields even
  if empty" gets read as "fill them in," producing hallucinated entities. Be explicit:
  "leave unknown fields as `null`; never invent values."
- **Separate content from tone.** If a priority rubric says "P1 = system down, all users
  affected" but doesn't say _ignore emotional language_, angry/urgent wording alone will
  inflate priority. Add an explicit instruction to classify on stated facts, not tone.
- **Give negative few-shot examples for edge cases you actually saw fail** — e.g. an
  urgent-sounding feature request must still map to P4. Without an example showing this,
  the model defaults to matching urgency words to high severity.
- **Meta-prompt to diagnose your own prompt.** Paste the broken prompt plus 2–3 failing
  transcripts into a fresh Claude conversation and ask: _"What structural issues in this
  prompt could cause these outputs? Be specific about which instructions are ambiguous,
  conflicting, or missing."_ Treat the answer as a hypothesis list, not a verdict.
- **Prompt chaining** is the fix when tasks interfere: e.g. Classify → Extract → Draft,
  each with its own focused system prompt. Tradeoff: each step is a separate API call —
  weigh against a latency budget (e.g. "3 sequential calls need justification under a
  5s SLA").
- **A/B test competing prompt variants** on the same eval set rather than picking by feel.
- **Automatic prompt optimization**: once you've plateaued, generate several variants
  (via meta-prompting), eval each, keep the best — a simple loop beats guessing.
- **Protect what already passes.** Look at the eval's category breakdown before changing
  anything: fixes targeted at hard failing categories frequently regress easy passing
  ones. Always keep a regression/"clean case" test in your set.
- **Track your iteration log.** Recording each prompt version and its score turns "I
  fixed it" into a reproducible methodology you can defend and repeat on the next broken
  prompt.
- **Own the diagnostic judgment.** Never present a fix as "I just asked Claude to fix
  it." You decided what to ask, evaluated the result, and chose what to ship — that
  judgment is the deliverable, not the text Claude generated.

---

## 2. Diagnosing AI System Failures — The Diagnostic Loop

A repeatable 4-step framework for any AI failure, from one prompt to a multi-agent
pipeline:

1. **Symptom** — write down exactly what the user/customer reported, in their words.
   Don't reframe or interpret yet.
2. **Hypothesis** — force at least 3 hypotheses from the symptom alone, _before_ opening
   any artifact. Naming hypotheses up front reveals where your diagnostic instincts are
   strong or weak, and prevents anchoring on the first thing you see. Common structural
   hypotheses to keep on hand:
   - Routing / classification failure
   - Tool description too vague to use reliably
   - Missing or wrong escalation path
   - Sub-agent over-claiming resolution
   - Context not reaching the model that needs it
   - Cache placement breaking shared prompt regions
3. **Evidence** — for any agentic system, pull three artifacts first: system prompts
   (what is the agent trying to do?), tool descriptions (what can it see, when would it
   use each tool?), and execution traces (what actually happened, step by step). Grade
   each hypothesis against a _specific quoted line_ — "the prompt seems off" is not
   evidence; "line 12 tells the agent to retry forever with no timeout" is.
4. **Recommendation** — scope the fix to file → line → change → the specific failure it
   prevents. "Improve the prompt" is not a recommendation. If you can't cite the
   artifact and line, you're not done with Evidence yet.

Additional diagnostic discipline:

- **Read the rate, not one run.** A single non-deterministic agent trace proves nothing;
  run the same case multiple times (e.g. 5 trials) and read the resolution rate — one
  clean pass can hide a 20% success rate.
- **Isolate the model variable explicitly.** If the client suspects "the model isn't
  good enough," test that theory head-on by swapping in a bigger/pricier model on the
  same eval. Compare both the new success rate _and_ what it cost to find out — this is
  usually the strongest evidence for "it's not the model, it's the system around it."
- **Watch one trace end-to-end before touching code.** Aggregate pass/fail rates tell
  you _that_ something is broken, not _how_. Read a full transcript against the original
  complaint and note exactly where the agent stopped short (e.g. resolved one of two
  reported issues, then declared victory).
- **Use Claude to read traces, cautiously.** Drop a confusing transcript into Claude
  with something like _"Here's a trace from an agent that closed a ticket the customer
  says isn't fixed. Walk me through what it did and where it might have gone wrong."_
  Treat the output as a lead to chase, not an answer to trust.
- **Confirm the fix generalizes.** After a lever moves the rate on one case, rerun on a
  held-out set (different inputs, same class of problem). A fix that only works on the
  case you tuned on is overfitting — in an engagement, that's a finding, not a fix.
- **Change one thing at a time, then re-measure.** Never adjust prompt, tools, and
  routing simultaneously — you won't know which change moved the number.
- **Distinguish a failed run from a failed task.** An API error/timeout is
  infrastructure breaking (a failed _run_) — skip grading. A wrong-but-completed answer
  is the agent doing the wrong thing (a failed _task_) — grade it normally. Conflating
  the two hides real reliability problems.

---

## 3. Building Evals

- **Evals beat vibes.** "Try it a few times and see" doesn't scale; evals give you a
  baseline, a feedback loop (change something, re-run, check for regressions), and
  numbers you can defend before shipping to a customer.
- **Three-part architecture: Tasks → Runner → Graders → Results.**
  - _Tasks_ define what to test: query, expected behavior, category, and grader checks.
  - _Runner_ orchestrates execution (sends queries, collects transcripts, applies
    graders) and should **not** also print/display — keep it a pure function returning
    a data structure so you can swap displays, persist to JSON, or feed a dashboard.
  - _Graders_ return a binary score + a reason string. A task passes only if **all**
    checks from **all** graders on it pass.
- **Design the harness for extension, not just today's task:**
  - Look graders up in a registry dict keyed by type name, not an if/elif chain — a new
    grader type is one function + one dict entry.
  - Pass the agent function in as a parameter rather than importing it directly, so you
    can mock it, swap models, or wrap it with instrumentation without touching the
    runner.
  - Let the runner own transcript parsing (extracting final text, tool calls, etc.) so
    the agent itself doesn't need to know how it will be graded.
  - Run tasks concurrently (e.g. `ThreadPoolExecutor` for sync API calls, `asyncio.gather`
    for an async client) — but bound the concurrency to avoid rate limits.
- **Grader types worth having by default:**
  - String containment (`response_contains`) for exact expected substrings.
  - Numeric-with-tolerance (`response_numeric`) for computed answers.
  - Tool-use verification (`tool_use`) to confirm the agent _grounded_ its answer in a
    tool call rather than hallucinating — check tool name only when you just want "did
    it use the tool," and check exact arguments only when the argument value itself is
    what you're testing (e.g. synonym resolution). Don't over-constrain to a rigid call
    sequence — a valid, unexpected path to the right answer should still pass.
  - LLM-as-judge for open-ended queries with many valid phrasings or that require
    reasoning ("what do you sell?", "which is the better deal?"). Give the judge the
    original query, the agent's final text, and one atomic natural-language criterion;
    force a structured `PASS`/`FAIL` first line, then a reason, so parsing is trivial.
    Never ask one judge call to evaluate multiple criteria at once.
- **Establish a real baseline before changing anything.** LLM outputs are
  non-deterministic (recent models don't even expose temperature), so run the eval
  multiple times before you trust a number, and re-run after every change to detect both
  improvement and regression.
- **Inspect failures individually, not just the summary rate.** For each failing task,
  check what the agent actually said, which tools it called with what arguments, and
  whether the failure was tool selection, argument formatting, or the final answer. For
  passing tasks, ask if they're passing for the right reason (not by luck).
- **Write negative/edge-case tasks deliberately** — items not in a catalog, off-topic
  questions, malformed input — not just the happy path.
- **Track pass@k vs pass^k when reliability matters.** pass@k = passed at least once in
  k tries (distinguishes "possible" from "impossible"); pass^k = passed every time
  (distinguishes "flaky" from "reliably broken"). Use both to characterize wobble.
- **Guard the harness itself**: add a max-turns limit so a misbehaving agent can't loop
  forever, add per-task timeouts, retry transient API errors with backoff, and validate
  that every task dict has its required fields before a run.
- **Graduate from ad hoc to a real framework when the project matures** — e.g.
  Promptfoo, Braintrust, LangSmith, Harbor — rather than maintaining a bespoke harness
  indefinitely.

---

## 4. Inference Optimization

**Measure before you touch anything.** You cannot optimize — or bill a client for an
improvement — that you can't prove. Track four core metrics:

- **TTFT** (Time To First Token) — the UX number; how long a user stares at a spinner.
- **TTC** (Time To Completion) — the economics number; total request duration.
- **OTPS** (Output Tokens Per Second) — generation throughput once streaming starts.
- **Cache-aware $/unit** — a cost model that only counts `input × rate + output × rate`
  badly mis-prices any cached workload. Cache **writes** bill at **1.25×** the input
  rate (5-minute TTL); cache **reads** bill at **0.1×**. Verify actual cache behavior
  from `usage.cache_read_input_tokens`, never assume it from vibes.

**The six levers, roughly in order of leverage** (plus the zeroth: delete needless
round trips first — every serial call pays full network + prefill + generation cost,
and a chained call re-bills its own prior output as new input):

1. **Prompt caching.** Cache is a strict prefix match across
   tools → system → messages; any byte changed anywhere in the prefix invalidates
   everything after it. Put frozen, byte-identical content (playbooks, tool
   definitions, long system prompts) first and mark it with `cache_control`; keep
   volatile content (timestamps, request IDs, the actual per-call payload) _after_ the
   cached block. Minimum cacheable prefix length is **4096 tokens on Opus/Haiku, 2048 on
   Sonnet** — shorter prefixes silently don't cache at all.
2. **Model routing / portfolio, not one model.** Most real workloads are mostly routine.
   Run a cheap triage pass (e.g. Haiku) to classify ROUTINE vs COMPLEX, then route
   routine work to a cheap/fast model and only send genuinely hard cases to a bigger
   model. This is staffing leverage — "don't put the senior partner on every NDA."
3. **Output discipline.** Output tokens cost roughly **5× input tokens** and each one
   also costs wall-clock generation time (`TTC ≈ TTFT + output_tokens / OTPS`). Use
   structured outputs (`output_config.format` + JSON schema) so the response _is_ the
   deliverable — no "explain step by step, then JSON" preamble, no parsing regex — and
   the schema doubles as a machine-checkable spec. Right-size `max_tokens` to the actual
   artifact (don't leave an 8000-token ceiling on a 300-token JSON object). Use
   `output_config.effort` (`low`–`max`) to trade reasoning depth for tokens on
   Sonnet/Opus — note it **errors on Haiku**, which is already the low-latency tier.
4. **Streaming.** Stream the surviving call by default for anything user-facing: it
   turns TTC-only waiting into visible progress (TTFT) and avoids HTTP timeouts on long
   responses. TTFT is the number that determines whether a user watches or alt-tabs
   away.
5. **Parallelism with cache warming.** Independent items (contracts, tickets, docs) can
   run concurrently — but a cache entry only becomes readable once the _first_ response
   begins streaming, so firing N identical requests simultaneously all pay the cold-cache
   price. Send one request first to warm the cache, then fan out the rest. Size fan-out
   to your rate-limit tier; the SDK retries 429s with backoff automatically, but a
   properly-sized fan-out beats a fan-out that thrashes retries.
6. **Two-speed architecture (Batch API).** Split work into an interactive lane
   (streamed, low-latency, for a human watching) and a backfill lane (overnight, no one
   watching) run through the **Batch API at 50% off all token charges** — same models,
   same prompts, same schema, half the price, in exchange for latency you weren't going
   to spend anyway. This split — what the human touches vs. what runs in the dark — is
   the single highest-leverage architecture decision on volume workloads. (Batch API is
   Anthropic-API-only; not available on Bedrock, though Bedrock has its own batch
   product.)

**Non-negotiable: gate every optimization on an accuracy eval.** An optimization that
makes a pipeline faster/cheaper but drops correctness below the SLA isn't an
optimization — it converts a COGS problem into a liability problem. Run the quality
eval before declaring an optimization win, and verify on a holdout set never seen during
tuning (an optimization that only works on the tuning sample is overfitting, and reads
as a finding, not a fix, in a client review).

**Client-conversation checklist** (useful as a mental model even outside this exercise):
measure first → model portfolio + routing → cache the frozen prefix → discipline the
output → collapse round trips and stream the rest → parallelize with cache warming in
mind → two-speed architecture for volume → gate everything on accuracy.

---

## 5. Using Claude Code / Developer Platform / Subagents

- **Pick the right surface for the job.** Messages API = full control over agentic
  loops and custom orchestration (lowest level, most work). Agent SDK = a framework
  handling tool dispatch for you. Claude Code = developer productivity / repo-level
  tasks. claude.ai / Enterprise = end-user, non-developer workflows. Understanding the
  raw Messages-API loop makes the higher-level surfaces easier to reason about.
- **The agentic tool-use loop pattern:** `while response.stop_reason == "tool_use":`
  extract tool calls → execute them → append results as tool_result blocks → call the
  API again. Claude decides the sequence of calls; your code only orchestrates and
  executes. Pass `response.content` back as-is — it may contain thinking blocks
  alongside tool_use blocks, and dropping them breaks continuity.
- **Tool description quality determines tool selection quality.** Claude picks which
  tool to call largely from the `description` field. A vague description leads directly
  to wrong tool selection — treat tool descriptions with the same rigor as an API's
  public documentation.
- **Structured output constrains the final answer only, not the whole loop.** Apply
  `output_config.format` (a JSON schema) plus `tool_choice={"type":"none"}` only on the
  _final_ call after the tool loop has completed — during the loop, let Claude use tools
  normally. With adaptive thinking on, the structured JSON may sit in the last text
  block, not the first.
- **Use adaptive thinking / effort deliberately.** `output_config.effort` (or the
  `thinking={"type":"adaptive"}` control) trades reasoning depth against latency/cost.
  Route effort to task difficulty — high effort for ambiguous/high-stakes cases, low for
  routine ones — the same portfolio idea as model routing. Thinking traces double as an
  audit trail for _why_ the agent made a judgment call (e.g., why it chose to escalate).
- **Stream anything a human is waiting on.** Handle `thinking_delta`, `text_delta`, and
  `input_json_delta` events; call `stream.get_final_message()` after the stream ends to
  get the full response object for loop continuation.
- **Multi-agent/subagent systems are diagnosed the same way as single prompts — just
  with more artifacts.** A coordinator's system prompt decides routing; its tool list
  and each specialist's system prompt/tools are the next layer of evidence. A ticket
  with two problems getting only one handled is very often a coordinator instruction
  gap ("hand off once you've addressed _a_ concern" instead of "confirm every concern
  raised has been addressed before closing").
- **Never edit graders/tests/scoring logic to make a number move.** If the intended fix
  lives in prompts/tools/config, changing the eval itself to pass defeats the entire
  point of the diagnostic exercise — and, by extension, of any eval-driven engagement.
- **Keep API keys out of notebooks and chat windows entirely.** Use a gitignored `.env`
  file (or shell env var) that the setup code reads; never paste a key into a cell or
  a prompt — notebooks and chat transcripts have a way of ending up in client repos.
- **Work in your own tooling, not a browser scratchpad**, and don't paste code out of a
  chat window into a project — work the exercise/task directly in the repo so state,
  history, and diffs stay real and reviewable.

---

## 6. General Workflow Discipline

- **Diagnose before you prescribe.** On a real engagement, the fastest path to "fixed"
  and the fastest path to "the customer trusts your explanation" are the same path:
  symptom → hypothesis → evidence → scoped recommendation. Skipping straight to a fix
  produces a change nobody can defend when asked "why did that work?"
  A score improvement you can't explain is a demo; one with a diagnosis behind it is a
  methodology.
- **Name hypotheses before looking at artifacts.** This forces genuine reasoning rather
  than pattern-matching to the first thing you notice in the code/prompt/trace.
- **Isolate variables.** Test "is it the model?" by swapping only the model and holding
  everything else fixed; test "did my fix generalize?" with a holdout set; change one
  lever at a time when iterating.
- **Read the rate, not the anecdote.** Non-deterministic systems require multiple trials
  before a success/failure claim means anything. A single clean or single failed run is
  not evidence.
- **Protect regressions.** Every fix pass should include at least one "already works"
  case in the test set, because fixes aimed at hard failures frequently break easy
  passes.
- **Be honest about attribution.** When reporting on an AI-assisted improvement,
  separate what your engineering decision produced (a chain step, an explicit
  constraint, a diagnosed root cause) from what the model's baseline capability produced
  (you just stopped getting in its way). This distinction is what makes an engagement
  narrative credible to a technical buyer.
- **Use Claude as a second opinion, not a source of truth.** Whether diagnosing a trace,
  picking a prompt-fixing technique, or auditing your own process, treat model output as
  a hypothesis to evaluate against your own evidence — never as an answer to accept
  outright.
- **Bring quantitative proof, not vibes, to the client conversation.** Before/after rate,
  before/after cost, and the specific category breakdown that shows _why_ it moved are
  what make a fix "defensible" rather than "it seems better now."
- **Anticipate the obvious objection and pre-empt it with your own data.** E.g. "why not
  just pay for a better model?" — answer it with the head-to-head cost/accuracy test you
  already ran, not with a hand-wave.
- **State your assumptions when presenting numbers.** A benefits case (cost savings,
  latency improvement) without printed assumptions is the first thing a client audit
  committee will discount.

---

## Project context — read on demand

This repo implements a two-tier memory architecture: session-scoped short-term memory and
user-scoped long-term memory, with a curator deployed on a cron schedule.

- **`BRIEF.md`** — architecture, the decision log and its reasoning, platform object model,
  and five real bugs in the upstream scripts. Read it before changing anything in the
  memory layer, or when picking the project up cold.
- **`PLAN.md`** — build schedule, function contracts, the system prompt, and the code
  blocks to copy.

These are deliberately **not** `@` imports. `CLAUDE.md` and everything it imports load into
context on every single turn; these two are long, one-time reads that should be opened when
they are relevant and not paid for otherwise.
