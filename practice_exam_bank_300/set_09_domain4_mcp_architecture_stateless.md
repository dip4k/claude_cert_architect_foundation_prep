# CCAR-F Exam Practice Bank: Set 9
## Domain 4: Tool Design & Model Context Protocol (Part 2: MCP Architecture & 2026 Specification)
### Questions 246 – 275

---

### Q246. The Three Core MCP Primitives
What are the three fundamental primitives exposed by Model Context Protocol (MCP) servers to AI clients?

**A)** GET, POST, DELETE.
**B)** Tools (`tools/*`), Resources (`resources/*`), and Prompts (`prompts/*`).
**C)** Models, Weights, and Hyperparameters.
**D)** Users, Groups, and Permissions.

**Correct Answer:** B

**Explanation:**
The Model Context Protocol (MCP) standard organizes server capabilities into three distinct primitives:
1. **Tools (`tools/*`)**: Executable functions that allow the model to take actions or produce side-effects (e.g. database writes, API mutations).
2. **Resources (`resources/*`)**: Application data and context exposed via URIs (like GET endpoints) that provide read-only context (files, schemas, live metrics).
3. **Prompts (`prompts/*`)**: User-controlled reusable message templates and workflows, typically exposed as UI slash commands.

**Why other options are incorrect:**
- **A)** HTTP verbs are transport primitives, not MCP conceptual primitives.
- **C)** ML training parameters are not exposed via MCP.
- **D)** Identity entities are authorization concepts, not MCP protocol capabilities.

---

### Q247. MCP Tools vs. Direct API Tool Definitions
What is the primary architectural advantage of defining tools via an MCP Server rather than hardcoding tool schemas directly in your Python API script?

**A)** MCP tools run on the GPU for free.
**B)** Universal Interoperability & Decoupling: An MCP server exposes tools through an open standard, allowing the exact same tool server to be connected simultaneously to Claude Desktop, Claude Code, custom enterprise agents, or other AI hosts without duplicating code or modifying API payloads.
**C)** Direct API tools cannot return JSON.
**D)** MCP tools do not require network connectivity.

**Correct Answer:** B

**Explanation:**
Hardcoding tool definitions inside individual API scripts tightly couples the tools to that specific application. MCP establishes a universal client-server architecture: an MCP server implements tools once, and any MCP-compliant host (Claude Desktop, IDE extensions, CLI agents, custom orchestrators) can discover and execute those tools dynamically without rewriting integration code.

**Why other options are incorrect:**
- **A)** Tool execution runs on the server hosting the MCP process, not free cloud GPUs.
- **C)** Direct API tools support standard JSON.
- **D)** MCP servers communicate over local standard I/O (stdio) or HTTP/SSE networks.

---

### Q248. The MCP July 28, 2026 Specification Evolution
What major architectural shift was introduced in the **July 28, 2026 MCP specification (`2026-07-28`)** compared to legacy 2024/2025 versions?

**A)** MCP was deprecated in favor of raw WebSockets.
**B)** Transition to a Stateless Request/Response Core: The protocol core transitioned from a bidirectional stateful session model to a stateless request/response architecture, eliminating sticky session requirements and enabling horizontal scaling behind standard load balancers.
**C)** All tools must now be written in Fortran.
**D)** MCP servers were restricted to single-user desktop computers.

**Correct Answer:** B

**Explanation:**
Early iterations of MCP relied on stateful, bidirectional transport sessions that made horizontal scaling, multi-region routing, and serverless hosting difficult. The landmark `2026-07-28` specification modernized MCP into a **stateless request/response architecture**: every request is self-describing, allowing requests to hit any server instance behind standard round-robin load balancers without requiring sticky sessions or persistent handshakes.

**Why other options are incorrect:**
- **A)** MCP is the active industry standard, not deprecated.
- **C)** Official SDKs exist for TypeScript, Python, Go, Rust, Java, etc.
- **D)** The 2026 spec was specifically hardened for enterprise cloud deployments.

---

### Q249. Header-Based Routing in the 2026 MCP Specification
In the modern 2026 MCP specification, how can enterprise API gateways (like Envoy, Kong, or AWS API Gateway) route incoming MCP tool requests without parsing the full JSON body?

**A)** By inspecting custom HTTP headers: Method and target names travel via standardized HTTP headers (`Mcp-Method` and `Mcp-Name`), allowing edge gateways to handle routing, authentication, and rate limiting prior to decoding the JSON payload.
**B)** Gateways must use deep neural networks to guess the tool name.
**C)** By requiring every tool to use a different TCP port.
**D)** Header-based routing is forbidden in MCP.

**Correct Answer:** A

**Explanation:**
A key optimization of the 2026 stateless MCP specification is **Header-Based Routing**. Requests emit standardized HTTP headers (such as `Mcp-Method: tools/call` and `Mcp-Name: query_database`). This allows lightweight API gateways and reverse proxies to inspect the intended tool, verify OAuth permissions, and route traffic to the appropriate microservice cluster without the computational cost of parsing large JSON request bodies.

**Why other options are incorrect:**
- **B)** Neural networks are not used for network gateway routing.
- **C)** Port-per-tool architectures are unmaintainable and insecure.
- **D)** Header routing is a premier feature of the modern spec.

---

### Q250. Cacheable Lists via `ttlMs` in the 2026 MCP Spec
An enterprise agent queries an MCP server that hosts 40 tools. Under the 2026 specification, how does the server prevent the agent from repeatedly querying `tools/list` on every single turn?

**A)** The server disconnects the client if it asks twice.
**B)** Cacheable Lists: The server returns a `ttlMs` (Time-To-Live in milliseconds) parameter in its `tools/list` response, allowing the client to cache the tool schemas locally and eliminate redundant network chatter.
**C)** The client must store tools on a USB stick.
**D)** Tools list queries are permanently cached forever.

**Correct Answer:** B

**Explanation:**
In high-throughput environments, repeatedly fetching `tools/list` and `resources/list` creates substantial network overhead. The 2026 MCP specification introduced cacheable list responses: servers can include a `ttlMs` field indicating how long the client may cache the schema definitions, dramatically cutting down on redundant round trips.

**Why other options are incorrect:**
- **A)** Disconnecting clients breaks application functionality.
- **C)** USB transfer is not an API caching mechanism.
- **D)** Schemas evolve; permanent immutable caching would prevent schema updates.

---

### Q251. MCP Resources vs. Tools
What is the conceptual and operational distinction between an MCP Resource and an MCP Tool?

**A)** Resources and Tools are identical words for the same thing.
**B)** Resources are application-controlled read-only context (analogous to HTTP GET) that expose data without side effects; Tools are model-controlled actions (analogous to HTTP POST) that execute computations or mutate external state.
**C)** Resources cost money; Tools are free.
**D)** Resources can only be read by human users, not AI models.

**Correct Answer:** B

**Explanation:**
- **Resources (`resources/*`)**: Passive, read-only data endpoints identified by URIs (`postgres://schema/users`, `file:///logs/app.log`). They provide grounding data without side effects, giving the application deterministic control over what context is shared.
- **Tools (`tools/*`)**: Active, executable functions that the model invokes autonomously to produce changes, execute queries, or trigger external API calls.

**Why other options are incorrect:**
- **A)** They serve fundamentally different architectural roles.
- **C)** Billing is governed by model tokens, not protocol primitive names.
- **D)** Resources are explicitly designed to be attached to LLM context.

---

### Q252. Templated Resource URIs in MCP
An MCP server exposes customer profiles. Instead of registering 100,000 individual static URIs, how does the server declare resource endpoints dynamically?

**A)** It cannot; all 100,000 URIs must be statically declared at startup.
**B)** Templated Resource URIs: The server declares a URI template (e.g. `customer://profiles/{customer_id}`), allowing clients to construct or match dynamic resource requests at runtime.
**C)** By creating 100,000 subdomains on the internet.
**D)** By storing customer records in the client's RAM.

**Correct Answer:** B

**Explanation:**
MCP supports **Resource Templates** using RFC 6570 URI templates (e.g., `analytics://reports/{report_id}/metrics`). This allows servers to expose vast or dynamically generated datasets through a single parameter-driven resource pattern without enumerating every entity in advance.

**Why other options are incorrect:**
- **A)** Static enumeration of millions of resources causes memory exhaustion.
- **C, D)** Subdomain proliferation and RAM stuffing are absurd engineering anti-patterns.

---

### Q253. Resource Subscriptions and `listChanged` Notifications
A live monitoring agent connects to an MCP server tracking server metrics. How can the agent receive updates when underlying resources change without constantly polling?

**A)** Polling every 50 milliseconds in a busy loop.
**B)** Resource Subscriptions: The client subscribes to specific resource URIs (`subscribe: true`); when underlying data changes, the server emits a `notifications/resources/updated` or `listChanged` event to alert the host.
**C)** The server sends an SMS text message to the engineer.
**D)** Subscriptions are disallowed in MCP.

**Correct Answer:** B

**Explanation:**
MCP natively supports publish/subscribe mechanics for resources. Clients can register subscriptions for specific URIs. When the underlying database row, file, or log stream updates, the server pushes an asynchronous notification, allowing the host to fetch the fresh resource context without burning bandwidth on aggressive polling loops.

**Why other options are incorrect:**
- **A)** Aggressive polling degrades server performance and consumes network bandwidth.
- **C)** Protocol updates occur within the protocol stream, not via SMS.
- **D)** Subscriptions are an official, standard MCP primitive.

---

### Q254. MCP Prompts Primitive in UI Workflows
What is the primary function of the MCP `prompts/*` primitive?

**A)** To automatically write marketing copy on Twitter.
**B)** User-Controlled Workflow Templates: Exposing parameterized prompt templates (e.g. `/summarize-pr`, `/debug-incident`) that end users can select in their UI, customize with arguments, and execute as guided workflows.
**C)** To replace the Claude system prompt entirely.
**D)** To generate random passwords.

**Correct Answer:** B

**Explanation:**
MCP Prompts are server-defined template snippets designed for human-in-the-loop workflows. In hosts like Claude Desktop or Claude Code, available prompts surface as interactive slash commands. When selected, the host prompts the user for any declared arguments (e.g., `ticket_id`), interpolates them into the template, and submits the structured prompt to the model.

**Why other options are incorrect:**
- **A, D)** Not the architectural purpose of MCP prompts.
- **C)** MCP prompts populate the user/workflow message layer; they do not overwrite core safety system prompts.

---

### Q255. Developing MCP Servers with the Python SDK
In the official Python MCP SDK, which decorator is used to register a function as an executable tool?

**A)** `@mcp.action()`
**B)** `@mcp.tool()`
**C)** `@app.route()`
**D)** `@server.expose_everything()`

**Correct Answer:** B

**Explanation:**
In the official Python MCP SDK (`mcp.server.fastmcp` or core SDK), the `@mcp.tool()` decorator is the standard pattern for registering functions. The SDK inspects the Python function's type hints and docstring to generate the compliant JSON Schema automatically.

**Why other options are incorrect:**
- **A, D)** Non-existent decorators in the MCP SDK.
- **C)** `@app.route()` is standard Flask for HTTP endpoints, not the MCP tool decorator.

---

### Q256. Testing MCP Servers with the MCP Inspector
Before deploying an MCP server to production, which official developer utility allows architects to visually test tool schemas, execute test calls, and inspect resources in an interactive browser UI?

**A)** `npx @modelcontextprotocol/inspector`
**B)** `npm install virus`
**C)** Microsoft Paint
**D)** Wireshark packet capture only

**Correct Answer:** A

**Explanation:**
The **MCP Inspector** (`npx @modelcontextprotocol/inspector`) is Anthropic's official development and testing tool for MCP. It spins up a local web interface that connects to any local or remote MCP server, allowing developers to inspect exposed tools, validate JSON schemas, test resource subscriptions, and trigger tool calls interactively before connecting to Claude.

**Why other options are incorrect:**
- **B, C, D)** Fanciful or inappropriate tools for validating MCP protocol implementations.

---

### Q257. Authorization Hardening: OAuth 2.1 in MCP 2026
How does the July 2026 MCP specification enforce secure, enterprise-grade authorization between AI clients and remote MCP servers?

**A)** Hardcoded API keys shared in public GitHub repositories.
**B)** Standardized OAuth 2.1 and OpenID Connect (OIDC) integration: Remote MCP servers declare authentication metadata, allowing hosts to authenticate via scoped bearer tokens, preventing unauthenticated access and establishing cryptographically verified user identity.
**C)** Password authentication using plain text HTTP basic auth.
**D)** Authorization is not supported; all MCP servers must be public.

**Correct Answer:** B

**Explanation:**
The 2026 specification tightened enterprise security by formalizing **OAuth 2.1 and OIDC** integration. Remote MCP servers declare their token endpoints and required scopes. The AI host performs an authenticated handshake, obtaining short-lived bearer tokens that are passed in request headers. This enables fine-grained identity tracking and enforces least-privilege enterprise governance.

**Why other options are incorrect:**
- **A, C)** Hardcoding keys or plain text basic auth violates security baselines.
- **D)** Enterprise MCP servers routinely protect sensitive internal corporate data.

---

### Q258. The Extensions Framework in MCP 2026
In the 2026 MCP specification, how are specialized capabilities like long-running asynchronous background jobs and rich interactive user interfaces (*MCP Apps*) architected?

**A)** They are hacked into tool descriptions using markdown strings.
**B)** The MCP Extensions Framework: Formal protocol extensions that servers and clients negotiate during initialization, providing structured channels for background task lifecycles and client-rendered visual UI widgets without polluting core primitives.
**C)** They require installing a secondary operating system.
**D)** They are strictly banned by Anthropic.

**Correct Answer:** B

**Explanation:**
Rather than bloating the core protocol, the 2026 MCP specification introduced the **Extensions Framework**. Advanced capabilities (such as tracking asynchronous background tasks or rendering rich visual interactive cards/widgets via MCP Apps) are implemented as standardized extensions. Clients and servers negotiate supported extensions during capabilities exchange, preserving core protocol simplicity.

**Why other options are incorrect:**
- **A)** Hacking features into descriptions is brittle and non-standard.
- **C)** Protocol extensions run inside standard software processes.
- **D)** Extensions are an official, first-class architectural standard.

---

### Q259. The "Tool Bloat" Anti-Pattern in MCP Ecosystems
An enterprise connects 10 MCP servers to Claude Code, exposing 120 tools simultaneously in every conversation. The model starts choosing the wrong tools, latency increases by 4x, and costs surge. What anti-pattern is occurring?

**A)** The Multi-Core CPU Bottleneck.
**B)** Tool Bloat Anti-Pattern: Exposing too many competing tool schemas simultaneously overwhelms the model's context window, dilutes attention, increases latency, and causes tool selection confusion.
**C)** The Python Interpreter Overload.
**D)** The Git Index Lock.

**Correct Answer:** B

**Explanation:**
*Tool Bloat* occurs when developers connect dozens of servers without filtering, dumping 100+ tools into the prompt. Each tool schema consumes tokens on every turn. More critically, high semantic overlap between dozens of tools degrades the model's ability to select the right one, leading to hallucinations and hesitation.

**Why other options are incorrect:**
- **A, C, D)** The failure is an LLM context and decision-space overload, not a local hardware or OS lock issue.

**Anti-Pattern Alert:**
*Tool Bloat*: Exposing unbounded numbers of tools in a single session without scoping, semantic routing, or on-demand loading, destroying model precision and latency.

---

### Q260. Mitigating Tool Bloat via Progressive Discovery
What is the recommended architectural solution to prevent Tool Bloat in systems with hundreds of available MCP tools?

**A)** Delete 90% of the company's software.
**B)** Progressive Tool Discovery / Dynamic Tool Registries: Index tool capability cards in a semantic vector store; analyze the incoming user query, retrieve only the top 3-5 most relevant candidate tools dynamically, and present only those tools in the active API call.
**C)** Merge all 100 tools into a single tool named `do_everything`.
**D)** Force the user to type tool schemas manually.

**Correct Answer:** B

**Explanation:**
**Progressive Discovery** (or Semantic Tool Routing) is the enterprise standard for managing large tool catalogs. Instead of loading 100 tools into every prompt, tool metadata is indexed in a vector store. When a user prompt arrives, a semantic router retrieves the top 3–5 candidate tools relevant to that specific task, keeping the prompt lean and tool selection accuracy high.

**Why other options are incorrect:**
- **A)** Deleting internal tools destroys business utility.
- **C)** A monolithic `do_everything` tool bypasses typing safety and creates extreme hallucination risks.
- **D)** Manual schema typing is unusable.

---

### Q261. MCP Host vs. Client vs. Server Architecture
In a setup where a developer uses Claude Desktop to query a local SQLite database via MCP, match each component to its architectural role:
1. Claude Desktop application
2. The SQLite MCP Server process
3. The MCP connection layer inside Claude Desktop

**A)** 1: Server, 2: Client, 3: Host
**B)** 1: Host, 2: Server, 3: Client
**C)** 1: Client, 2: Host, 3: Server
**D)** All three are Servers

**Correct Answer:** B

**Explanation:**
- **Host**: The user-facing AI application (e.g. Claude Desktop, Claude Code, or a custom IDE) that coordinates the user session and model interactions.
- **Client**: The connector module within the host that opens transports, sends requests, and maintains protocol connections.
- **Server**: The independent process or service that implements tools, exposes resources, and accesses the underlying data (e.g. SQLite, GitHub API).

**Why other options are incorrect:**
- **A, C, D)** Misclassify the host, client, and server boundaries.

---

### Q262. Transport Mechanisms in MCP: Stdio vs. HTTP/SSE
When should an MCP server use standard input/output (`stdio`) transport versus HTTP with Server-Sent Events (SSE)?

**A)** `stdio` is exclusively for mainframes; SSE is exclusively for mobile phones.
**B)** `stdio` is ideal for local subprocesses launched directly by the host machine (low latency, zero port binding, process-isolated); HTTP/SSE (or stateless HTTP in 2026) is required for remote, networked, or containerized microservices hosted across networks.
**C)** `stdio` is deprecated and banned in 2026.
**D)** HTTP is only used for downloading images.

**Correct Answer:** B

**Explanation:**
- **`stdio`**: The host spawns the MCP server as a local child process, communicating over standard stdin/stdout pipes. This is fast, secure, and requires no network ports, making it the preferred transport for local desktop/CLI tools.
- **HTTP / SSE**: Connects over TCP networks, enabling hosts to reach remote MCP servers running on Kubernetes clusters, serverless containers, or external SaaS platforms.

**Why other options are incorrect:**
- **A, C, D)** `stdio` remains a core local transport; HTTP is the standard network transport.

---

### Q263. Security Isolation of Local MCP Subprocesses
A developer runs an MCP server on their laptop that executes local bash commands. What security boundary protects the rest of the developer's system?

**A)** MCP automatically sandboxes all operating systems in virtual machines.
**B)** None by default: A local `stdio` MCP server executes with the exact operating system permissions of the user account running the host process, unless explicitly sandboxed inside a Docker container, jail, or restricted execution sandbox.
**C)** The Anthropic cloud server scans the laptop's hard drive every 10 seconds.
**D)** Python code cannot modify files on macOS or Windows.

**Correct Answer:** B

**Explanation:**
Local `stdio` MCP servers run as child processes under the user's OS user account. If an MCP server exposes unrestricted shell execution (`bash`), it possesses the user's full permissions to read, write, or delete files. Developers must exercise extreme caution: sensitive tools should be confined inside containers or explicit sandbox runtimes.

**Why other options are incorrect:**
- **A)** MCP is a protocol, not an automatic kernel virtualization engine.
- **C)** Anthropic APIs have no access to the client machine's local disk.
- **D)** Python has full local filesystem write capabilities.

**Anti-Pattern Alert:**
*Unsandboxed Local Shell MCP*: Equipping local MCP servers with unrestricted terminal execution without container isolation or path boundaries.

---

### Q264. Managing MCP Configuration Files (`claude_desktop_config.json`)
Where are local MCP servers configured for the Claude Desktop application on macOS/Linux?

**A)** Inside `~/.bash_profile`
**B)** Inside `~/Library/Application Support/Claude/claude_desktop_config.json` (or `~/.config/Claude/claude_desktop_config.json`) under the `mcpServers` JSON key.
**C)** In the DNS registry.
**D)** On the Anthropic public website.

**Correct Answer:** B

**Explanation:**
Claude Desktop reads its active MCP server registry from `claude_desktop_config.json`. The file defines executable paths, environment variables, and command-line arguments under the `mcpServers` object, launching configured servers as child processes upon application startup.

**Why other options are incorrect:**
- **A, C, D)** Non-standard paths that are not read by the desktop host.

---

### Q265. MCP Error Handling: Protocol Errors vs. Tool Execution Errors
If an MCP tool function raises a Python `DivisionByZero` exception during execution, how should the MCP server respond to the client?

**A)** Close the TCP connection abruptly without sending any response.
**B)** Return a valid MCP tool response where `isError: true` and the `content` array contains a text block explaining the division by zero error, allowing the model to understand the mathematical error.
**C)** Return an internal JSON-RPC `-32603` protocol crash error that disconnects the server.
**D)** Pretend the answer is infinity.

**Correct Answer:** B

**Explanation:**
MCP cleanly separates **Protocol Errors** (malformed JSON-RPC, unknown method names) from **Tool Execution Errors** (business logic exceptions, divide by zero, invalid input). Tool exceptions should NOT crash the protocol connection. The server catches the exception and returns a successful JSON-RPC response containing `isError: true` and a descriptive message, allowing the LLM to inspect the failure and self-correct.

**Why other options are incorrect:**
- **A, C)** Crashing or disconnecting the server terminates the entire agent session for a recoverable input error.
- **D)** Faking mathematical answers is an unacceptable hallucination.

---

### Q266. Exposing Database Schemas via MCP Resources
What is the most token-efficient way for an MCP server to provide an SQL database schema to Claude?

**A)** Force Claude to call `get_table_schema` 50 times in 50 consecutive tool execution turns.
**B)** Expose the schema as an MCP Resource: `postgres://schemas/public` which the host can read directly and attach to the initial context window, providing full schema grounding before Claude emits its first turn.
**C)** Print the schema to a PDF file and email it.
**D)** Do not provide the schema; let Claude guess column names.

**Correct Answer:** B

**Explanation:**
Using an MCP Resource for static or slowly changing context (like database schemas or system topology) is far more efficient than tool calls. Resources can be attached upfront, avoiding the latency and token overhead of multiple round-trip exploratory tool calls, while grounding the model in the exact column names before it writes SQL queries.

**Why other options are incorrect:**
- **A)** 50 consecutive tool calls create massive latency and burn turn budgets.
- **C, D)** Emailing PDFs or guessing columns are completely non-viable.

---

### Q267. Asynchronous Tools in Python FastMCP
When implementing an I/O-heavy tool (such as querying an external REST API) using Python FastMCP, how should the function be defined?

**A)** Synchronously using `time.sleep()`.
**B)** Asynchronously using `async def` and non-blocking HTTP clients (like `httpx.AsyncClient`), ensuring the server event loop remains responsive to concurrent requests.
**C)** In assembly language.
**D)** By spawning a new thread on every letter typed.

**Correct Answer:** B

**Explanation:**
Modern MCP servers handle concurrent requests. Defining tools with `async def` and utilizing asynchronous, non-blocking libraries (such as `httpx` or `asyncpg`) prevents blocking the server's main event loop during network I/O, ensuring high throughput and fast response times across concurrent agent calls.

**Why other options are incorrect:**
- **A)** Blocking synchronous sleeps freeze the entire server event loop.
- **C, D)** Impractical and detrimental to software scalability.

---

### Q268. Multi-Tenant MCP Server Architecture
An enterprise hosts a shared remote MCP server connecting to Salesforce. Multiple different users from different departments access the server through their individual AI agents. How must tenant security be enforced?

**A)** Run all queries under a single shared administrator account.
**B)** Tenant Context Propagation: The incoming MCP request must carry the authenticated user's bearer token or identity context in its headers; the MCP server verifies the token and scopes all Salesforce API operations strictly to that specific user's permissions.
**C)** Trust the model to only ask for appropriate data.
**D)** Disconnect the server whenever a second user connects.

**Correct Answer:** B

**Explanation:**
In multi-tenant remote MCP deployments, the server must never execute operations using a global god-mode account. Incoming requests must propagate verified user credentials (via OAuth bearer tokens). The server extracts the caller's identity and executes backend queries within that user's authorized security boundary, preventing horizontal privilege escalation.

**Why other options are incorrect:**
- **A)** Shared admin accounts eliminate audit trails and violate least privilege.
- **C)** Relying on model trust provides zero security against prompt injection.
- **D)** Dropping connections breaks multi-user availability.

**Anti-Pattern Alert:**
*God-Mode MCP Connection*: Running shared multi-tenant MCP servers with hardcoded super-admin credentials, allowing any connected agent to access all enterprise data.

---

### Q269. The Role of JSON-RPC 2.0 in MCP
What underlying messaging protocol standard does MCP use for structured request/response framing?

**A)** gRPC over HTTP/3.
**B)** JSON-RPC 2.0 (with standardized `jsonrpc`, `id`, `method`, and `params` fields).
**C)** SOAP XML.
**D)** Raw ASCII text.

**Correct Answer:** B

**Explanation:**
MCP is built on the established **JSON-RPC 2.0** protocol specification. Every message follows standard JSON-RPC framing: requests declare a `jsonrpc: "2.0"`, an integer or string `id`, a `method` name (e.g. `tools/call`), and a `params` dictionary, providing structured, language-agnostic message exchange.

**Why other options are incorrect:**
- **A, C, D)** MCP standardizes specifically on JSON-RPC 2.0, not gRPC, SOAP, or raw text.

---

### Q270. Handling Tool Deprecation in MCP Servers
An engineering team needs to retire an older tool `query_db_v1` in an active MCP server without instantly breaking legacy clients. What is the recommended deprecation strategy?

**A)** Delete the tool immediately without notice.
**B)** Mark the tool description with a deprecation notice: `"[DEPRECATED: Use query_db_v2 instead]. Queries legacy tables..."`, log deprecation warnings on execution, and schedule a formal retirement date in alignment with API versioning policy.
**C)** Change the tool to return random errors.
**D)** Change the database password.

**Correct Answer:** B

**Explanation:**
Tool deprecation in distributed agent ecosystems requires graceful transition windows. Updating the description informs the model that a superior tool is available (`query_db_v2`), encouraging the LLM to migrate its tool selection naturally, while leaving the legacy tool functional for existing callers until formal decommissioning.

**Why other options are incorrect:**
- **A)** Instant deletion causes immediate runtime crashes in active clients.
- **C, D)** Injecting random errors or breaking passwords degrades system reliability.

---

### Q271. Tool Argument Sanitization Against Path Traversal
An MCP tool `read_log_file(filename)` is implemented as:
```python
with open("/var/log/app/" + filename) as f:
  return f.read()
```
An attacker inputs: `filename = "../../../etc/shadow"`. What vulnerability is present and how should it be remediated?

**A)** Buffer Overflow; rewrite in Rust.
**B)** Path Traversal Vulnerability: The tool fails to sanitize path arguments. Remediation: Resolve absolute paths using `os.path.realpath()` and verify that the target path strictly starts with the allowed directory prefix (`/var/log/app/`) before opening.
**C)** MCP protocol corruption; restart the host.
**D)** Temperature mismatch.

**Correct Answer:** B

**Explanation:**
Path Traversal (`../`) is a critical security vulnerability in file-reading tools. Untrusted LLM inputs must never be directly concatenated into filesystem paths. Tool implementations must validate that the canonical, resolved path stays strictly within the designated root directory, rejecting any path traversal attempts.

**Why other options are incorrect:**
- **A)** Python manages memory safely; the issue is directory traversal logic.
- **C, D)** Protocol and temperature have no bearing on filesystem path validation.

---

### Q272. Caching Tool Return Data Inside MCP Servers
A tool `fetch_github_repo_stars(repo)` is called frequently by multiple agents. How can the MCP server minimize external GitHub API rate limit consumption?

**A)** Refuse to answer 50% of requests.
**B)** Implement an in-memory TTL Cache (e.g. `cachetools.TTLCache`) inside the MCP server handler, caching repository star counts for 5 minutes and returning cached responses for identical parameters.
**C)** Hardcode the star count to 1,000,000.
**D)** Block all GitHub requests permanently.

**Correct Answer:** B

**Explanation:**
Caching at the MCP server layer protects downstream third-party APIs from rate-limit exhaustion. When multiple agents or recurring loops query the same static or slowly changing data, an in-memory cache returns verified data instantly without burning external API quotas.

**Why other options are incorrect:**
- **A, D)** Refusing or blocking requests destroys tool utility.
- **C)** Hardcoding fake numbers produces inaccurate data.

---

### Q273. Discovering MCP Capabilities at Runtime
When an MCP client initiates a connection to an MCP server, what initial method handshake exchanges supported features?

**A)** `exit()`
**B)** `initialize`: The client and server exchange supported protocol versions, capabilities (tools, resources, prompts, extensions), and implementation metadata.
**C)** `ping`
**D)** `reboot_system`

**Correct Answer:** B

**Explanation:**
The `initialize` method is the foundational handshake of MCP. The client transmits its protocol version and supported capabilities; the server responds with its version, server information, and capability flags, establishing the operational contract for the session.

**Why other options are incorrect:**
- **A, C, D)** Standard RPC lifecycles begin with initialization, not exit, ping, or reboot commands.

---

### Q274. Managing Binary Assets via MCP Resources
Can an MCP server expose binary data (such as PDF files or PNG images) through the `resources/*` primitive?

**A)** No, MCP is strictly limited to 7-bit ASCII text.
**B)** Yes; MCP resources support binary content blocks containing a `blob` field with base64-encoded binary data and an explicit `mimeType` (e.g. `application/pdf`, `image/png`).
**C)** Yes, but only if the file is smaller than 10 bytes.
**D)** Binary files must be emailed to the user.

**Correct Answer:** B

**Explanation:**
The MCP Resource specification explicitly supports binary assets. A resource representation can return a `blob` containing base64-encoded data alongside its standard MIME type (`application/pdf`, `image/jpeg`), allowing multimodal hosts and agents to ingest PDFs, images, and binary artifacts cleanly.

**Why other options are incorrect:**
- **A)** MCP natively supports binary blobs via base64 encoding.
- **C)** Resources handle standard file sizes up to host-configured memory limits.
- **D)** Email is not part of the MCP protocol transport.

---

### Q275. Domain 4 Summary: Modern Tool & MCP Architecture
What principles define best-practice Tool & MCP architecture in CCAR-F enterprise standards?

**A)** Expose hundreds of unauthenticated shell scripts and let the model figure it out.
**B)** Standardized, Layered, Least-Privilege Architecture: Use strict JSON Schemas with rich semantic descriptions, enforce idempotency on state-altering operations, distinguish transient from fatal errors with `is_error`, leverage modern stateless MCP for horizontal scaling, protect downstream resources with progressive tool discovery, and enforce strict authentication (OAuth 2.1) and path sanitization.
**C)** Avoid using tools in production agents.
**D)** Hardcode all data in system prompts without external APIs.

**Correct Answer:** B

**Explanation:**
Production tool design combines rigorous schema contracts, actionable error recovery, and modern open protocols (MCP). System reliability depends on stateless scalability, least-privilege scoping, defensive argument sanitization, and avoiding tool bloat through progressive discovery.

**Why other options are incorrect:**
- **A, C, D)** Uncontrolled tool sprawl, avoiding external tools, or stuffing everything into static prompts violates enterprise AI architectural design.

