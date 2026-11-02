# CCAR-F Exam Practice Bank: Set 6
## Domain 3: Prompt Engineering & Context Management (Part 1: Prompt Caching & Token Economics)
### Questions 156 – 185

---

### Q156. The Strict Prefix Rule in Prompt Caching
An architect configures prompt caching with `cache_control: {"type": "ephemeral"}` on a 10,000-token system prompt. In request 1, the user prompt is: `"What is the weather?"`. In request 2, the user prompt is: `"What is the capital of France?"`. What happens to the cached system prompt during request 2?

**A)** The cache is completely invalidated because the user query changed.
**B)** Cache Hit: The system prompt remains fully cached and is read at a 90% discount (`cache_read_input_tokens`), because prompt caching matches strictly from the beginning of the prompt (prefix matching), and the system prompt prefix was unchanged.
**C)** The API throws an error because cache keys must be manually specified.
**D)** Request 2 runs on a cached model weights server.

**Correct Answer:** B

**Explanation:**
Anthropic's prompt caching operates on a **strict prefix-matching** algorithm. As long as the initial sequence of tokens (Tools → System Prompt → early messages) remains byte-for-byte identical, the cache will hit for that entire prefix. Changes occurring *after* the cached prefix breakpoint (such as a new user message at the end) do not invalidate the cached prefix before it.

**Why other options are incorrect:**
- **A)** Changing subsequent tokens does NOT invalidate prior identical prefixes.
- **C)** Anthropic automatically computes cache keys from token prefix hashes.
- **D)** Prompt caching caches key-value activations of input tokens, not fine-tuned weights.

---

### Q157. Cache Invalidation via Upstream Dynamic Data
A developer places a dynamic timestamp at the very top of their system prompt:
`system = f"Current Time: {datetime.now()}. You are an enterprise assistant..."`
A cache breakpoint `cache_control: {"type": "ephemeral"}` is placed at the end of the system prompt. What is the operational impact on prompt caching?

**A)** The cache hits 100% of the time because the model understands time.
**B)** 100% Cache Miss Penalty: Because the timestamp changes every second, the prompt prefix is never identical, causing continuous cache writes (`cache_creation_input_tokens`) at a 1.25x cost penalty and 0% cache reads.
**C)** The API automatically rounds timestamps to the nearest hour.
**D)** The timestamp is stripped before hashing.

**Correct Answer:** B

**Explanation:**
*Upstream Timestamp Invalidation* is one of the most severe prompt caching anti-patterns. Because prefix matching is byte-exact, injecting a dynamic variable (like `datetime.now()`, request UUIDs, or random session IDs) at the beginning of the prompt alters the token sequence from token 1. This guarantees that every request is a cache miss, forcing an expensive cache write (billed at 1.25x base input price) on every single turn. Dynamic values must ALWAYS be placed *after* the cached prefix.

**Why other options are incorrect:**
- **A, C, D)** The caching engine evaluates raw token bytes literally; it does not round, strip, or ignore timestamps.

**Anti-Pattern Alert:**
*Dynamic Prefix Invalidation*: Placing timestamps, request IDs, or variable counters before static cached prompts, permanently breaking prompt caching.

---

### Q158. Cache Time-To-Live (TTL) and Refresh Semantics
What is the default Time-To-Live (TTL) for an ephemeral prompt cache entry in the Anthropic Messages API, and how is the expiration timer affected by incoming requests?

**A)** Default TTL is 24 hours and expires regardless of usage.
**B)** Default TTL is 5 minutes (with an optional 1-hour configuration); every successful cache hit automatically resets the TTL timer back to the full window.
**C)** Default TTL is 30 seconds and cannot be extended.
**D)** Cache entries never expire once created.

**Correct Answer:** B

**Explanation:**
Anthropic's standard prompt cache TTL is 5 minutes (with extended 1-hour options available). Crucially, the cache uses a sliding expiration window: every time a request arrives that hits the cached prefix, the TTL timer resets back to 5 minutes. In an active conversation or multi-turn agent loop where turns occur within 5 minutes of each other, the cache remains "warm" indefinitely without paying for re-writes.

**Why other options are incorrect:**
- **A)** 24 hours is the batch processing SLA, not interactive cache TTL.
- **C)** 30 seconds is too short for real-world conversational turns.
- **D)** Caches are ephemeral and evict when idle to free GPU memory.

---

### Q159. The Four Cache Breakpoint Limit
How many `cache_control: {"type": "ephemeral"}` breakpoints can a developer specify within a single Messages API request?

**A)** Unlimited.
**B)** Exactly 1 breakpoint per account.
**C)** Up to 4 breakpoints per request.
**D)** Zero; caching is purely automatic.

**Correct Answer:** C

**Explanation:**
Anthropic's API allows up to **4 cache breakpoints** (`cache_control`) in a single request. This allows developers to establish layered cache tiers:
1. Breakpoint 1: Static Tools schema.
2. Breakpoint 2: Large static System Prompt / Reference Corpus.
3. Breakpoint 3: Multi-turn conversation history prefix.
4. Breakpoint 4: Ephemeral user context or few-shot examples.

**Why other options are incorrect:**
- **A)** Breakpoints are bounded by hardware constraints to a maximum of 4.
- **B)** The limit is per-request, not per-account.
- **D)** Breakpoints must be explicitly declared via `cache_control`.

---

### Q160. Minimum Token Threshold for Prompt Caching
A developer places `cache_control: {"type": "ephemeral"}` on a short 100-token system prompt when calling `claude-sonnet-5-5`. The API response usage shows:
`input_tokens: 100, cache_creation_input_tokens: 0, cache_read_input_tokens: 0`.
Why did prompt caching fail to activate?

**A)** The developer's credit card was declined.
**B)** Minimum Token Threshold: Prompt caching requires a minimum prefix length (typically 1,024 tokens for Sonnet/Opus, or 2,048 for specific tiers). Payloads below this threshold are not cached because caching small prompts provides negligible performance and cost benefits.
**C)** System prompts cannot be cached.
**D)** The model was offline.

**Correct Answer:** B

**Explanation:**
Anthropic enforces a minimum prompt size threshold before caching engages (typically 1,024 tokens on flagship models like Claude 5.5 Sonnet and Opus, or 2,048 tokens on select tiers). Below this threshold, the computational overhead of caching KV states exceeds the latency savings. Prompts shorter than the threshold are processed as standard uncached input tokens without penalty.

**Why other options are incorrect:**
- **A)** Credit failures return HTTP 402/403, not a successful 200 OK with zero cache tokens.
- **C)** System prompts are the primary target for prompt caching.
- **D)** A 200 OK response indicates the model is online and operational.

---

### Q161. Interpreting the `usage` Object in Cached Requests
A developer receives the following usage metrics from an API call:
```json
{
  "usage": {
    "input_tokens": 150,
    "output_tokens": 400,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 8500
  }
}
```
How should this request be billed?

**A)** The developer is billed for 8,650 full-price input tokens and 400 output tokens.
**B)** 8,500 tokens were read from cache at a ~90% discount (0.1x base rate), 150 uncached input tokens were billed at standard 1.0x rate, and 400 output tokens were billed at the standard output rate.
**C)** All tokens were free because the cache hit.
**D)** The request was an error because `cache_creation_input_tokens` is 0.

**Correct Answer:** B

**Explanation:**
The `usage` object breaks down token consumption precisely:
- `cache_read_input_tokens: 8500`: Retrieved from the warm cache at a 90% discount (0.1x standard input pricing).
- `input_tokens: 150`: The new tokens that arrived after the cache breakpoint, billed at standard input price (1.0x).
- `cache_creation_input_tokens: 0`: No new cache entries were written.
- `output_tokens: 400`: Generated output tokens billed at standard output rate.

**Why other options are incorrect:**
- **A)** Ignores the 90% cache read discount.
- **C)** Cache reads provide a 90% discount, not 100% free compute.
- **D)** `cache_creation_input_tokens: 0` is the ideal steady-state for a cache hit.

---

### Q162. Cache Write Price Premium
What is the billing multiplier for writing tokens to the prompt cache (`cache_creation_input_tokens`) compared to standard base input tokens on a 5-minute TTL?

**A)** 0.5x (half price).
**B)** 1.0x (same price).
**C)** ~1.25x (a 25% premium on initial write, recovered on subsequent discounted reads).
**D)** 10.0x.

**Correct Answer:** C

**Explanation:**
Writing to the ephemeral cache incurs an initial write premium: typically 1.25x the standard input token rate for a 5-minute TTL (or ~2.0x for a 1-hour TTL). This premium covers the cost of writing KV activations to GPU memory. However, because subsequent reads are discounted by 90% (0.1x), the write cost is fully amortized after just two requests hitting the cache.

**Why other options are incorrect:**
- **A, B, D)** Standard Anthropic pricing structures cache writes at 1.25x for 5m TTL.

---

### Q163. Batch Processing API Economics
An enterprise needs to classify 500,000 archived support tickets. The results are needed within 24 hours, not in real-time. Which API feature provides the largest direct cost reduction for this asynchronous workload?

**A)** Real-time streaming.
**B)** The Anthropic Message Batches API: Provides a flat 50% discount on all input and output tokens for asynchronous workloads processed within a 24-hour SLA window.
**C)** Setting `max_tokens: 1`.
**D)** Running the requests using a VPN.

**Correct Answer:** B

**Explanation:**
The Anthropic Message Batches API is purpose-built for non-latency-sensitive, high-volume workloads (backfills, evaluations, batch labeling). By submitting requests in batch format, Anthropic schedules inference during off-peak capacity, offering an automatic **50% discount** across all input and output tokens while guaranteeing completion within 24 hours.

**Why other options are incorrect:**
- **A)** Streaming provides low latency for interactive users, but carries standard pricing.
- **C)** Limiting to 1 token truncates classification outputs.
- **D)** VPNs do not affect token pricing.

---

### Q164. Combining Prompt Caching with the Batches API
Can prompt caching be utilized in conjunction with the Message Batches API?

**A)** No, the Batches API strictly prohibits prompt caching.
**B)** Yes; when batch requests share a common prefix (e.g. identical system prompt or few-shot corpus) and include `cache_control`, batch items benefit from prompt caching discounts on top of the batch pricing discount.
**C)** Yes, but only on weekends.
**D)** Only if the batch contains fewer than 5 items.

**Correct Answer:** B

**Explanation:**
Prompt caching and Batch Processing can be stacked. If a batch of 10,000 requests all share the same 20,000-token system prompt and guidelines, applying `cache_control` allows the batch runner to cache the prefix, compounding the 50% batch discount with the 90% prompt cache read discount for massive cost savings.

**Why other options are incorrect:**
- **A)** Prompt caching is fully supported within the Batches API.
- **C, D)** There are no weekend restrictions or low item limits.

---

### Q165. Input vs. Output Token Asymmetry
On Claude 5.5 Sonnet, standard pricing is \$3 per million input tokens and \$15 per million output tokens. What architectural lesson does this 5x price difference dictate for cost-conscious system design?

**A)** Always maximize output tokens because they generate higher quality.
**B)** Output Token Conservation: Because output tokens are 5x more expensive than input tokens (and reasoning/thinking tokens are billed as output tokens), architects should design prompts to be expressive on input while constraining output verbosity to concise, structured, necessary information.
**C)** Input tokens should be avoided entirely.
**D)** Models should only output binary numbers.

**Correct Answer:** B

**Explanation:**
In frontier LLMs, output token generation requires autoregressive decoding (generating one token at a time sequentially), which is computationally far more demanding than parallel input prompt ingestion. Output tokens cost roughly 5x more than input tokens. Efficient architectures invest tokens in clear input context and instructions, while directing the model to generate concise, high-density outputs.

**Why other options are incorrect:**
- **A)** Maximizing output tokens unnecessarily inflates billing.
- **C)** Input context is required for grounded generation.
- **D)** Binary output is impractical for human and software consumption.

---

### Q166. Token Pre-Flight Counting via `/v1/messages/count_tokens`
Before sending a 400,000-token multi-document analysis request to Claude, how can an application verify the exact token count to enforce budget controls without incurring inference costs?

**A)** Count the number of characters and divide by 4.
**B)** Call the Anthropic Token Counting endpoint (`/v1/messages/count_tokens`): It accurately counts the tokens for the exact model tokenizer and returns the token count instantly at zero generation cost.
**C)** Send the request with `max_tokens: 0`.
**D)** Ask Claude in chat how many tokens the prompt has.

**Correct Answer:** B

**Explanation:**
Heuristics like `len(text) // 4` are rough approximations that fail dramatically on code, JSON, non-English languages, and structured markup. Anthropic provides a dedicated `/v1/messages/count_tokens` endpoint that passes the prompt through the exact model tokenizer, returning precise token metrics for system prompts, tools, and messages before any inference is executed.

**Why other options are incorrect:**
- **A)** Character division is inaccurate and leads to budget overruns.
- **C)** `max_tokens: 0` is invalid and rejected with an HTTP 400 error.
- **D)** An LLM cannot count its own incoming prompt tokens during runtime.

---

### Q167. Ordering Elements for Optimal Prompt Caching
In what order must request elements be structured to ensure valid, efficient prompt caching in the Anthropic Messages API?

**A)** Messages → System Prompt → Tools
**B)** Tools (top) → System Prompt → Message History (bottom)
**C)** System Prompt → Tools → System Prompt
**D)** Alphabetical order by key name

**Correct Answer:** B

**Explanation:**
The Anthropic API evaluates prompt prefixes in a strict architectural order:
1. `tools` definitions (first/highest in prefix)
2. `system` prompt blocks
3. `messages` array (chronological order)
Placing tool definitions and static system instructions at the very top establishes a stable prefix. Placing a cache breakpoint at the end of the system prompt ensures the entire static setup is cached for all subsequent conversational messages.

**Why other options are incorrect:**
- **A, C, D)** The API prefix compilation strictly adheres to Tools → System → Messages.

---

### Q168. Cache Miss via Parameter Mutation
An application has a static 20,000-token system prompt cached. On turn 2, the developer changes `max_tokens` from 4096 to 8192 and leaves the system prompt and tools completely identical. Does this change invalidate the prompt cache?

**A)** Yes, any parameter change invalidates the entire cache.
**B)** No; generation parameters (`max_tokens`, `temperature`, `stop_sequences`) are inference controls, NOT prompt prefix tokens. The cached KV prefix remains valid and results in a cache hit.
**C)** Yes, changing `max_tokens` requires re-training the model.
**D)** The API crashes.

**Correct Answer:** B

**Explanation:**
Prompt caching caches the computed Key-Value (KV) attention states of the **input prompt text and tools**. Runtime generation parameters—such as `max_tokens`, `temperature`, or `stop_sequences`—govern the decoding sampler, not the prompt prefix. Modifying `max_tokens` between requests does not invalidate the existing cached prompt prefix.

**Why other options are incorrect:**
- **A)** Only changes to cached input tokens (tools, system, messages) invalidate the KV cache.
- **C, D)** Generation sampling parameters do not require retraining or cause crashes.

---

### Q169. Cost Trade-Off: Extended Thinking in High-Throughput Pipelines
A financial services firm runs 500,000 automated transaction checks per day. An engineer suggests enabling `budget_tokens: 4000` extended thinking on all checks. Standard check answers are 50 tokens long. What is the financial consequence?

**A)** Token costs remain unchanged because thinking is free.
**B)** Massive Cost Explosion: Thinking tokens are billed at the full output token rate (\$15/MTok). Adding up to 4,000 output tokens to 500,000 requests adds 2 billion output tokens per day (\$30,000/day extra), which is economically catastrophic for high-throughput simple classification.
**C)** The company receives a discount for thinking deeply.
**D)** Latency drops to 1 millisecond.

**Correct Answer:** B

**Explanation:**
Extended thinking tokens are billed identically to standard output tokens. In high-throughput, low-complexity pipelines (like simple transaction categorization), blanket enablement of large thinking budgets incurs astronomical output token costs for negligible accuracy gains. Extended thinking should be reserved for high-stakes, ambiguous, or complex multi-step reasoning tasks.

**Why other options are incorrect:**
- **A, C)** Thinking tokens are billable compute.
- **D)** Generating 4,000 thinking tokens increases latency significantly.

---

### Q170. Dynamic Few-Shot Insertion Behind Cache Breakpoints
An application uses 50 few-shot examples (10,000 tokens) that are static, but dynamically retrieves 2 fresh examples (500 tokens) based on vector search for each user query. How should cache breakpoints be placed to maximize efficiency?

**A)** Place a cache breakpoint after the 2 dynamic examples.
**B)** Breakpoint 1 on the 10,000 static few-shot examples (ensuring they hit the cache 100% of the time); place the 2 dynamic examples *after* the breakpoint so only the 500 new tokens are billed as uncached inputs.
**C)** Do not use prompt caching with few-shot examples.
**D)** Put dynamic examples before the static examples.

**Correct Answer:** B

**Explanation:**
To maximize cache utilization, static invariant content must always precede dynamic content. By grouping the 50 permanent few-shot examples first and pinning a cache breakpoint immediately after them, that 10,000-token block hits the cache on every request. The 2 variable examples sit after the breakpoint, ensuring only 500 tokens are billed at standard uncached input rates.

**Why other options are incorrect:**
- **A)** Placing the breakpoint after dynamic data means the prefix changes every request, causing 100% cache misses.
- **C)** Few-shot corpuses are prime candidates for caching.
- **D)** Putting dynamic examples first destroys the cache for the subsequent static examples.

---

### Q171. The "Cache Thrashing" Anti-Pattern
An application rotates through 10 completely different 50,000-token document corpuses on every alternating request under a single API key, with 10 seconds between requests. What performance issue occurs?

**A)** Perfect 100% cache hits.
**B)** Cache Thrashing: Because the prompt prefix is constantly replaced with completely different corpuses before any corpus can be reused, the system repeatedly pays cache write penalties without ever getting cache read benefits.
**C)** The GPU catches fire.
**D)** Anthropic blocks the IP address.

**Correct Answer:** B

**Explanation:**
*Cache Thrashing* occurs when an application alternates between disparate large prefixes faster than the cache can yield reuse hits. Writing a 50k token corpus costs 1.25x. If the next request sends a different 50k corpus, another 1.25x write is charged. If prefixes are never reused within their TTL, the application pays 25% *more* than if caching were disabled entirely. Architectural solution: affinity routing (route requests regarding Document A to the same worker instance).

**Why other options are incorrect:**
- **A)** Alternating prefixes guarantees 0% cache hits.
- **C, D)** Thrashing causes economic waste, not physical damage or IP bans.

**Anti-Pattern Alert:**
*Cache Thrashing*: Rapidly rotating diverse, un-reused large contexts through prompt caching, paying constant 1.25x cache write penalties with zero cache reads.

---

### Q172. Ephemeral Cache Eviction Under Cloud Pressure
Can a prompt cache entry be evicted before its 5-minute TTL expires?

**A)** No, the TTL is legally guaranteed by Anthropic SLA.
**B)** Yes; because prompt caching is explicitly designated as "ephemeral", cache entries may be evicted early under rare conditions of extreme GPU memory contention or infrastructure rebalancing. Applications must be designed to handle cache misses gracefully.
**C)** Yes, caches are evicted every 2 seconds.
**D)** Only if the user types the word "evict".

**Correct Answer:** B

**Explanation:**
"Ephemeral" caching means that while entries are retained under normal operation for the duration of the TTL, they are not durable persistent storage. During rare periods of peak infrastructure load or GPU rebalancing, warm cache entries may be evicted before TTL expiration. Client systems should always treat caching as an opportunistic performance optimization, not an immutable state guarantee.

**Why other options are incorrect:**
- **A)** Ephemeral services do not guarantee 100% memory residency against load spikes.
- **C, D)** Eviction is managed by GPU memory management algorithms, not arbitrary 2-second clocks or magic words.

---

### Q173. Token Billing for Tool Schemas
A developer registers 25 complex tools with exhaustive JSON schemas, consuming a total of 6,000 tokens. How are these tool definition tokens billed?

**A)** Tool definition tokens are completely free and never billed.
**B)** Tool definitions are prepended to the input prompt and billed as standard input tokens on every turn; however, they can and should be cached using `cache_control` to reduce ongoing costs by 90%.
**C)** Tool definitions are billed as output tokens.
**D)** Tools are billed per function execution, not per token.

**Correct Answer:** B

**Explanation:**
Tool definitions are part of the model's input context. In the Messages API, tool schemas are serialized and injected into the prompt prefix. If your tool schemas consume 6,000 tokens, every request incurs 6,000 input tokens. Because tool definitions are static across a session, placing a `cache_control` breakpoint on tools ensures that these 6,000 tokens are read from cache at a 90% discount on turns 2 through N.

**Why other options are incorrect:**
- **A)** Tool schemas consume GPU memory and are billable input tokens.
- **C)** Tools are inputs, not generated outputs.
- **D)** Billing is strictly token-based, not execution-event-based.

---

### Q174. Cost Comparison: Haiku vs. Sonnet vs. Opus
In an architectural review, a team evaluates model choices for a high-volume semantic log classifier processing 100 million logs per month. The classification requires extracting three fields. What is the most cost-effective recommendation?

**A)** Use `claude-opus-5-5` with maximum extended thinking.
**B)** Use `claude-haiku-4-5` with prompt caching and concise structured outputs: Haiku is significantly faster and costs an order of magnitude less than Opus/Sonnet, while possessing ample reasoning power for structured log extraction.
**C)** Build a custom neural network from scratch in assembly language.
**D)** Use Opus on Mondays and Haiku on Fridays.

**Correct Answer:** B

**Explanation:**
Matching workload complexity to model tier is a fundamental responsibility of a Claude Architect. Straightforward classification, data extraction, and routing on massive data volumes (100M events/month) do not require the heavyweight reasoning of Opus. Deploying `claude-haiku-4-5` delivers sub-second latency and reduces monthly API spend by up to 80-90% compared to frontier models.

**Why other options are incorrect:**
- **A)** Opus is vastly over-powered and financially wasteful for routine log parsing.
- **C)** Building neural nets in assembly is an absurd engineering distraction.
- **D)** Day-of-week model switching is nonsensical.

---

### Q175. The Risk of Caching User-Specific PII
A developer places a prompt cache breakpoint after a block containing a specific user's Social Security Number and medical records. Another user on the same multi-tenant SaaS platform submits a query. Can User 2 access User 1's cached KV states?

**A)** Yes, prompt caches are completely public across all Anthropic users worldwide.
**B)** Prompt caches are isolated to the specific API organization/workspace; however, within the same organization, if another request shares the exact same prefix, it can hit the cache. To prevent cross-tenant data contamination, organizations must partition tenant contexts or avoid caching sensitive customer-specific PII in shared prefixes.
**C)** Anthropic automatically deletes all PII using quantum algorithms.
**D)** Prompt caching encrypts tokens so the model cannot read them.

**Correct Answer:** B

**Explanation:**
Anthropic enforces strict workspace/organization isolation: no external organization can hit or inspect your cache. However, within a single company's API key, prefix hashing is deterministic. If a multi-tenant application caches Tenant A's private data in a global prefix, there is a risk of context entanglement. Multi-tenant SaaS architectures should keep shared prompts (system instructions, codebases) cached, while isolating tenant-specific PII in uncached message turns.

**Why other options are incorrect:**
- **A)** Caches are strictly partitioned across Anthropic accounts.
- **C, D)** Fictional mechanisms.

---

### Q176. Estimating Cache Amortization Break-Even
If an organization writes 10,000 tokens to the prompt cache (costing 1.25x base input rate), how many subsequent requests hitting that cache are required to break even compared to not using caching at all?

**A)** Exactly 100 requests.
**B)** Just 2 requests: On turn 1 (write), cost is 1.25x. On turn 2 (read), cost is 0.1x. Total for 2 requests = 1.35x vs. 2.0x without caching (a 32% net savings by Turn 2).
**C)** Caching never saves money.
**D)** 10,000 requests.

**Correct Answer:** B

**Explanation:**
Prompt caching breaks even almost immediately:
- Without caching: Request 1 (1.0x) + Request 2 (1.0x) = 2.0x total cost.
- With caching: Request 1 (1.25x write) + Request 2 (0.1x read) = 1.35x total cost.
By the second request, prompt caching is already 32% cheaper than uncached requests. By request 10, savings exceed 80%.

**Why other options are incorrect:**
- **A, D)** Amortization happens orders of magnitude faster.
- **C)** Caching provides verified 80-90% net savings across multi-turn sessions.

---

### Q177. The Impact of System Prompt Formatting on Caching
A developer accidentally leaves an automated linter in their CI pipeline that randomly re-orders XML tags in the system prompt on every server deploy:
Deploy 1: `<rules>...</rules><context>...</context>`
Deploy 2: `<context>...</context><rules>...</rules>`
What happens to the production prompt cache on each deploy?

**A)** The cache continues working because XML tags are order-independent in Claude.
**B)** Cache Invalidation: Even though the semantic meaning is identical, token prefix order is changed, resulting in a complete cache miss and requiring a new cache write on every deploy.
**C)** The API rejects the XML.
**D)** Anthropic charges a fine.

**Correct Answer:** B

**Explanation:**
Prompt caching relies on exact, deterministic token sequences. Even if the semantic meaning is identical, changing the order of XML blocks, swapping whitespace, or altering dictionary keys changes the resulting token IDs. The caching engine sees a different sequence and treats it as a brand-new prompt, triggering a cache miss. Static prompts must maintain fixed, deterministic serialization.

**Why other options are incorrect:**
- **A)** Semantic understanding does not bypass token-exact hashing.
- **C)** Valid XML is accepted by Claude regardless of order.
- **D)** There are no fines; only standard billing for cache writes.

---

### Q178. Caching Large Reference Documents (RAG vs. Long-Context Cache)
An enterprise has a 100,000-token employee policy manual. Employees ask 5,000 questions about it every day. Which architecture provides the lowest operational complexity and highest answer quality?

**A)** Build a complex chunking, vector embedding, and RAG retrieval pipeline with a vector database.
**B)** Long-Context Prompt Caching: Inject the entire 100,000-token manual into the system prompt with a cache breakpoint; the manual is cached once, read 5,000 times at a 90% discount, eliminating chunking fragmentation and vector database infrastructure entirely.
**C)** Have an employee read the manual aloud over the phone.
**D)** Print the manual and scan it with a webcam on every query.

**Correct Answer:** B

**Explanation:**
For documents that comfortably fit within Claude's massive context window (100k - 500k tokens), long-context prompt caching often obsoletes traditional RAG for single-corpus domains. Placing the entire document in the cached prompt eliminates chunking boundary issues, embedding retrieval errors, and vector database hosting costs, while giving Claude 100% of the source material at a 90% discounted read cost.

**Why other options are incorrect:**
- **A)** Traditional RAG adds indexing pipelines, chunking heuristics, and vector DB maintenance costs that may be unnecessary for corpora under 500k tokens.
- **C, D)** Manual physical operations are impractical.

---

### Q179. Multi-Turn Conversation History Caching Strategy
In a customer support chat lasting 15 turns, how can prompt caching be used to minimize costs as conversation history grows?

**A)** Put a cache breakpoint on every single word.
**B)** Pin a cache breakpoint on the static System Prompt/Tools, and dynamically move a second cache breakpoint to the second-to-last user turn, allowing the growing historical prefix to be cached and reused on subsequent turns.
**C)** Clear history after every turn.
**D)** Never cache conversation history.

**Correct Answer:** B

**Explanation:**
In long multi-turn conversations, conversation history itself becomes a major cost driver. By maintaining a cache breakpoint on the static system prompt/tools and a rolling breakpoint on the recent completed turn, the prior conversation history is cached. Each new user turn only pays for standard input tokens on the newest message, while reading the entire accumulated conversation at the 90% cache discount.

**Why other options are incorrect:**
- **A)** Word-level caching is impossible.
- **C)** Clearing history causes immediate amnesia.
- **D)** Ignoring caching leads to quadratically growing input token costs.

---

### Q180. Token Budgeting for High-Concurrency Webhooks
An incoming webhook handler triggers Claude on every GitHub push event. During a company-wide merge event, 200 webhooks fire in 5 seconds. To prevent exhausting the organization's TPM (Tokens Per Minute) limit, what architectural pattern must be deployed?

**A)** Process all 200 webhooks synchronously in parallel.
**B)** Queue and Rate-Limit (Leaky Bucket / Token Bucket): Ingest webhooks into a message queue (e.g. AWS SQS or RabbitMQ) and pull requests via worker nodes configured with concurrency limits and rate governors that throttle consumption to stay safely below Anthropic TPM limits.
**C)** Delete 190 of the webhooks.
**D)** Disable authentication on the webhook endpoint.

**Correct Answer:** B

**Explanation:**
Sudden bursts of webhook events can easily overwhelm API rate limits (TPM and RPM), leading to cascading HTTP 429 errors. Production architectures decouple ingestion from processing using message queues. Workers consume messages at a controlled rate that conforms to the account's allocated token quotas.

**Why other options are incorrect:**
- **A)** Uncontrolled bursts cause immediate rate-limit failures.
- **C)** Dropping 95% of events causes data loss.
- **D)** Disabling authentication introduces severe security vulnerabilities.

---

### Q181. Cache Read Latency Benefits
Beyond financial savings, what is the primary operational performance advantage of prompt caching for large prompts?

**A)** Time-To-First-Token (TTFT) Latency Reduction: Because the model does not need to recompute KV attention states for the cached prefix, time-to-first-token is significantly faster (often 50-80% lower latency) on warm cache hits.
**B)** The server CPU temperature decreases.
**C)** The response text contains fewer vowels.
**D)** It eliminates the need for internet connectivity.

**Correct Answer:** A

**Explanation:**
Processing a 100,000-token prompt from scratch takes significant compute time before the first output token can be emitted. With prompt caching, the precomputed KV activations are loaded directly from memory, slashing TTFT latency by up to 50–80%. This creates a much more responsive user experience in interactive and agentic workflows.

**Why other options are incorrect:**
- **B, C, D)** Unrelated to LLM inference acceleration.

---

### Q182. Handling Cache Eviction in Multi-Agent Loops
In a long-running multi-agent workflow, a subagent is called after a 10-minute idle period. The previous cache entry has expired (TTL was 5 minutes). What occurs during the subagent's execution?

**A)** The workflow crashes with an unhandled exception.
**B)** Transparent Cache Re-creation: The API automatically treats the request as a cache miss, processes the prompt, writes a fresh cache entry (`cache_creation_input_tokens`), resets the TTL to 5 minutes, and completes the request successfully without client disruption.
**C)** The subagent forgets its system prompt.
**D)** The user must re-enter their password.

**Correct Answer:** B

**Explanation:**
Cache expiration is completely non-disruptive to application logic. If a request arrives after TTL expiration, the Anthropic API simply recomputes the prefix, stores a new cache entry, and fulfills the request. The only difference is billing (`cache_creation_input_tokens` instead of `cache_read_input_tokens`) and slightly higher initial latency.

**Why other options are incorrect:**
- **A)** Cache expiration is a normal operational event, not a fatal crash.
- **C)** The prompt is supplied in the request, so instructions are never forgotten.
- **D)** API caching has no connection to user passwords.

---

### Q183. Cache Breakpoint Placement on Empty Lists
A developer specifies `cache_control: {"type": "ephemeral"}` inside an empty `tools: []` list. What happens?

**A)** The entire internet crashes.
**B)** The API ignores the breakpoint or rejects the payload because cache breakpoints must be attached to valid, non-empty content blocks (e.g. specific tool definitions, system text blocks, or user message content blocks).
**C)** It caches the concept of nothingness.
**D)** It doubles token billing.

**Correct Answer:** B

**Explanation:**
`cache_control` annotations must be placed on specific content blocks (such as a text block in the `system` parameter, a specific tool definition object in `tools`, or a content block within `messages`). Placing a cache breakpoint on an empty structure is invalid and cannot establish a cacheable token prefix.

**Why other options are incorrect:**
- **A, C, D)** Fanciful claims; the API schema enforces structured placement on valid blocks.

---

### Q184. Cost Tracking Across Different Model Tiers
An engineering manager wants to monitor the ROI of migrating a code-explanation agent from `claude-opus-5-5` to `claude-sonnet-5-5`. How should the cost comparison be measured?

**A)** By comparing the monthly electric bill of the office.
**B)** By tracking the exact token breakdown (`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`) across both models for an identical benchmark test suite and calculating total cost using their published rate cards.
**C)** By asking Claude which model it likes better.
**D)** By counting the number of Git commits per week.

**Correct Answer:** B

**Explanation:**
Objective model ROI evaluation requires token-level telemetry. By running a standardized evaluation suite against both models and capturing exact usage metrics across uncached input, cached reads, cache writes, and output tokens, the team can quantify both the cost difference and any output quality trade-offs accurately.

**Why other options are incorrect:**
- **A, C, D)** Electric bills, subjective model preferences, and commit counts do not provide token-level financial accounting.

---

### Q185. Domain 3 Prompt Caching Summary Rule
Which statement summarizes the golden rule of prompt caching architecture?

**A)** Put variable and dynamic data first, and static data at the end.
**B)** Invariant, static, heavyweight context (Tools and System Prompts) must ALWAYS be positioned at the beginning of the prompt and protected by `cache_control`, while dynamic, fluctuating, or ephemeral data must sit AFTER the cache breakpoint.
**C)** Never cache anything larger than 100 tokens.
**D)** Cache entries should be refreshed every millisecond.

**Correct Answer:** B

**Explanation:**
The fundamental law of prompt caching is: **Static at the top, dynamic at the bottom**. Prefix matching requires that the beginning of the prompt remain byte-for-byte identical. Placing static tools and system instructions first ensures maximum cache hit rates (90% savings), while variable content placed after the cache breakpoint avoids invalidating the warm prefix.

**Why other options are incorrect:**
- **A)** Inverts the rule and destroys caching.
- **C)** Caching requires at least 1,024 tokens to engage.
- **D)** Refreshing every millisecond defeats the purpose of caching.

