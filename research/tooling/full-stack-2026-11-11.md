# BFI: the full AI tooling stack

Research date: 11 November 2026. This is a source-based assessment of the whole system: inference, optimization, model lifecycle, agents, tools, knowledge, speech, visuals, training, deployment, and measurement. It expands the earlier memory-heavy report, which remains a [memory appendix](memory-2026-11-11.md). No software was installed, no BFI source was modified, and no hardware performance results were produced. Recommendations are engineering judgments; linked capabilities come from official documentation or upstream source.

**The architecture I recommend is your own BFI handler coordinating replaceable specialist services.** Own the character identities, conversations, learned-adapter assignments, permissions, memory policy, and task state in the application. Let an inference runtime run weights, a speech stack process audio, and an asset service produce images. A common API can make them feel unified without forcing them into one enormous process.

Your recorded PC baseline is an Intel i7-13700K, Radeon RX 7900 XTX with 24 GB VRAM, 32 GB RAM, a 1 TB NVMe SSD, and Windows 11. Delivery, stability, and specifications still need verification. A separate Linux installation is an option, not an assumed requirement or purchase. The i7 machine does not have the Ryzen AI hardware required by Ryzen-specific NPU recipes. Sources: [BFI README](https://github.com/Mallow99/Personality-Playground#hardware-baseline), [hardware notebook](https://github.com/Mallow99/Personality-Playground/blob/main/docs/hardware.md).

BFI already has a FastAPI handler, SQLite conversation persistence, profiles, an inference adapter boundary, and bounded tools. Later work adds avatar integration; native Windows behavior and real inference remain distinct checks. Its current application is a local single-process prototype, not a deployed always-on service. Personality training into model weights remains a central project goal; memory and prompts support that work. Sources: [architecture](https://github.com/Mallow99/Personality-Playground/blob/work/docs/architecture.md), [training plan](https://github.com/Mallow99/Personality-Playground/blob/main/docs/training.md), [latest handoff](https://github.com/Mallow99/Personality-Playground/blob/work/docs/HANDOFF.md).

**1. The layers and the decisions they require**

| Layer | What it owns | First decision for BFI |
| --- | --- | --- |
| Model artifacts | Base weights, tokenizer, template, quantization, learned adapters | Exact checkpoint and artifact lineage |
| Inference | Running a model on CPU/GPU | Which runtime works well on the actual Radeon PC? |
| Optimization | Memory, prompt processing, generation, concurrency | Which bottleneck has been measured? |
| Model lifecycle | Downloading, loading, unloading, switching, health | Can the chosen runtime manage this itself? |
| Agent handler | Instructions, reasoning/tool loop, character state | Extend the existing handler; choose helpers deliberately |
| Tools and connectors | Files, search, calendars, browser, code, service actions | Which concrete workflows should the characters perform? |
| Workflow execution | Jobs, retries, cancellation, schedules, resumability | A simple queue first or a durable engine? |
| Knowledge and memory | Documents, preferences, experiences, corrections | What is authoritative and who can retrieve it? |
| Voice and perception | Microphone, transcription, synthesis, camera, screen | A modular speech pipeline or an integrated realtime model? |
| Character presentation | Poses, expression, animation, overlays | Preserve authored art; define a small presentation contract |
| Training | Learned personality and media adapters | Prove a small train-save-serve-evaluate loop |
| Operations and evaluation | Packaging, monitoring, backups, quality, performance | Make successful behavior reproducible |

Tools connected to this chat, software installed on your PC, and services exposed to BFI are three separate inventories. A library cannot automatically replace the model behind every chat application. Your own handler can call locally runnable models and supported hosted APIs, subject to each provider's capabilities and terms.

**2. Inference engines and local model servers**

An engine performs inference. A desktop runner may package an engine, download models, and serve an API. A manager controls these processes. Compare the actual underlying model/backend, because different frontends can wrap similar inference technology.

| Candidate | Role and strengths | Hardware/platform implications | BFI recommendation |
| --- | --- | --- | --- |
| [llama.cpp / llama-server](https://github.com/ggml-org/llama.cpp) | GGUF inference, CPU/GPU offload, broad backend ecosystem, local HTTP serving | HIP and Vulkan are relevant Radeon routes; model architecture and build still matter | **Reference baseline.** Useful for measured experiments and a transparent serving boundary |
| [Strata](https://github.com/Niko1221/Strata) | Local engine/app oriented around its supported models and resource-management approach | Current [AMD HIP guide](https://github.com/Niko1221/Strata/blob/main/docs/AMD_HIP.md) documents Windows gfx1100 packages relevant to RX 7900 XTX | **Compare seriously.** Preserve the existing research direction, but verify desired models, genuine tool calls, and custom-adapter serving separately |
| [LM Studio](https://lmstudio.ai/docs/developer/core/server) | Accessible GUI, model discovery, local APIs and model lifecycle controls | AMD documents Vulkan and ROCm runtime routes in its [playbook](https://developer.amd.com/playbooks/lmstudio-rocm-llms/) | **Good learning/experiment console.** Can also serve BFI if its API and capabilities fit |
| [Ollama](https://docs.ollama.com/quickstart) | Convenient model packaging, runner, API, and integrations | Local and cloud choices coexist; select explicitly and validate the exact supported model | **Convenience alternative.** Worth comparing on actual setup effort and behavior |
| [Lemonade](https://github.com/lemonade-sdk/lemonade) | PC-focused model server/manager using multiple backends and media capabilities | AMD-oriented development includes Radeon and Ryzen products; some features depend on hardware your Intel PC does not have | **Additional PC-focused contender.** Check the Radeon backend rather than assuming Ryzen NPU/hybrid features apply |
| [Transformers](https://github.com/huggingface/transformers) with PyTorch | Direct model loading, experimentation, training-adjacent inference, PEFT integration | Requires compatible PyTorch/device stack; serving throughput and memory need deliberate work | **Research and training reference.** Useful for verifying adapters before conversion |
| [vLLM](https://github.com/vllm-project/vllm) | Higher-throughput serving, continuous batching, prefix caching, and supported per-request LoRA | Upstream installation does not support native Windows; AMD feature support is specific to GPU, backend, model, and quantization | **Linux/server branch.** Valuable if concurrency or adapter serving justifies the platform work |
| [SGLang](https://github.com/sgl-project/sglang) | Agentic/large-scale serving, caching/scheduling, speculative and multimodal workloads | Current [AMD guide](https://docs.sglang.io/docs/hardware-platforms/amd_gpu) emphasizes Instinct GPU configurations | **Advanced server option.** An AMD support statement does not establish a native Windows 7900 XTX recipe |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | Graph-optimized inference across execution providers | Model export and provider support vary | **Useful for smaller components** such as embeddings and speech; not an automatic replacement for the chosen LLM engine |
| [TensorRT-LLM](https://nvidia.github.io/TensorRT-LLM/supported-hardware.html) | NVIDIA-specific optimized serving | NVIDIA hardware | Relevant to a future NVIDIA/cloud branch, outside the Radeon starting stack |
| [MLX LM](https://github.com/ml-explore/mlx-lm) | Apple-silicon inference, quantization, and fine-tuning | Apple silicon | Useful context for recommendations you see online; not an installation for this PC |

My first comparison would be llama.cpp versus Strata on a supported workload, with LM Studio as a practical manual testing option. Lemonade deserves a setup comparison if it simplifies Radeon deployment. Do not benchmark five tools simultaneously: establish a reference, then compare alternatives using identical artifacts when possible. When different engines cannot run the same artifact, report the comparison as a whole configuration rather than attributing every difference to the engine.

Model choice must consider tool calling, structured output, conversational style, practical task quality, vision needs, training feasibility, adapter export, and license. A model that produces attractive chat but unreliable tool arguments may be unsuitable for the Coding character. A large model's advertised context window is a maximum capability claim, not a useful default allocation.

**3. Optimization: what to tune, what each tool changes**

There are several performance targets: time before the first token, speed after generation starts, time to a completed useful task, throughput across requests, cold-start time, peak memory, and voice response latency. A setting can improve one while worsening another. Streaming improves responsiveness but does not itself increase token-generation throughput.

The conceptual GPU budget is weights plus conversation state/KV cache plus compute buffers, adapters, vision/audio components, and display/other application use. Architecture and backend change the details. Raw 4-bit weight arithmetic gives about 4 GB for 8B parameters, 7 GB for 14B, and 16 GB for 32B, in decimal units, before quantization metadata and all those additional allocations. These are intuition aids, not fit guarantees. A mixture-of-experts model's active parameter count describes computation per token, not the full weight-storage requirement.

| Technique | What changes | Relevant tooling | What to measure / qualification |
| --- | --- | --- | --- |
| Weight quantization | Fewer bits for weights, often enabling more GPU residency | GGUF tools in llama.cpp; runtime-supported quantized artifacts; [vLLM quantization backends](https://github.com/vllm-project/vllm/blob/main/docs/features/quantization/README.md) | Task and tool accuracy as well as memory/speed. Lowest bit count is not automatically the best result |
| GPU offload / placement | Which layers/tensors reside and compute on GPU versus CPU | llama.cpp, Strata, other runtime controls | Actual residency, prompt/decode speed, system RAM pressure, transfer cost |
| Context budgeting | How much history, evidence, and generated text is processed | Handler context builder and runtime context limits | Preserve needed evidence while reducing prompt work and state memory |
| KV/state precision | Memory used for attention state, where supported | Runtime cache dtype controls | Model/backend compatibility and long-context quality, not only reduced allocation |
| Efficient attention kernels | How attention work uses GPU memory and compute | HIP/Vulkan backends, runtime attention implementations | Exact architecture, precision, and backend. Do not assume a CUDA kernel is a Radeon optimization |
| Prefix caching | Reuse processing for an unchanged initial token sequence | [vLLM APC](https://github.com/vllm-project/vllm/blob/main/docs/features/automatic_prefix_caching.md), runtime prompt caching, SGLang cache mechanisms | Cold versus warm latency and cache hits. It reduces repeated prompt processing, not every cost of decoding |
| Continuous batching | Share inference execution among pending requests | llama-server, vLLM, SGLang | Combined throughput, individual tail latency, memory, fairness |
| Chunked prefill | Interleave long prompt processing with generation work | [vLLM scheduling controls](https://github.com/vllm-project/vllm/blob/main/docs/configuration/optimization.md) and supported server equivalents | First-token versus inter-token latency under mixed workloads |
| Speculative decoding | Propose several tokens, then verify with target model | Engine-supported draft models, n-gram or architecture-specific methods | Accepted draft tokens, extra memory, actual end-to-end speed, output semantics supported by the implementation |
| Model routing | Send requests to an appropriate model | Handler policy; optional gateway | Quality, cost, latency, data destinations, fallback visibility |
| Tool discovery and result shaping | Present relevant tools and compact results for each task | Existing typed tools, FastMCP, Composio discovery | Tool selection success and context size; retain evidence and complete relevant fields |
| Prompt compression | Remove or condense input information | [LLMLingua](https://github.com/microsoft/LLMLingua), selected summaries | Extra compressor cost and lost constraints/facts. Trial on retrieved material before using on authoritative instructions |
| KV offload/reuse across storage tiers | Move/reuse expensive context state | [LMCache](https://docs.lmcache.ai/developer_guide/integration.html) with compatible serving engines | Cache transfer versus recomputation cost; storage/RAM impact and compatibility. Advanced server option |
| Runtime compilation/tuned kernels | Specialize operations and reduce repeated overhead | PyTorch compilation or engine-specific paths | Compilation/cold-start costs, steady-state benefit, exact version/GPU support |
| Reasoning/output budgets | Spend fewer generation steps when a task needs a brief response | Model-aware decoding controls and handler policies | Correctness and useful-task latency; keep enough budget for difficult tasks |

For BFI, optimize in this order: verify GPU execution; choose a model/quantization with headroom; bound context and outputs; measure prompt and decode separately; test backend and attention settings; then test caching, batching, or speculation against a known workload. Profile first when a specific operation remains unexpectedly slow. Re-run quality cases after changing quantization or output constraints.

Quantization names are not interchangeable formats. GGUF, GPTQ/AWQ-style artifacts, FP8, and NF4/QLoRA recipes have different purposes and supported kernels. Current vLLM documentation explicitly provides a hardware matrix. Current [bitsandbytes documentation](https://huggingface.co/docs/bitsandbytes/installation) includes consumer AMD and Windows ROCm paths, so old claims that it is strictly CUDA-only are outdated; the chosen PyTorch/build/model combination still needs a real test.

There are also distinct caches: downloaded weight files on disk; compiled kernel artifacts; reusable token/KV state; cached tool/document results; and cached final answers. They have different validity rules. For example, a cached answer that predates your corrected preference can be stale even if its question is textually identical. Final-answer caching is a poor default for personalized companion conversations. Tool caches should carry source freshness and scope.

BFI's cache identity should include the relevant model revision, learned adapter, tokenizer/template, and permitted context. Cache reuse must not mix character-private evidence or ignore a changed adapter. A stable prompt layout can improve prefix reuse, but the content and ordering must still follow the model's actual template and the application's instruction rules.

**4. Model loading, swapping, gateways, and resource scheduling**

This is a major missing layer in many desktop prototypes. Three visible characters can have separate identities, prompts, histories, and memory scopes while sharing one base model. Another possible design uses one base plus supported character LoRAs. A third uses separate models loaded concurrently or on demand. These are different capacity plans and should be measured separately.

| Tool / approach | Role | When it earns a place |
| --- | --- | --- |
| [Current llama-server router](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) | Routes model names and manages model instances; current controls include loaded-model limits and memory margins | Evaluate first if llama.cpp is selected; existing capabilities may cover the need |
| [llama-swap](https://github.com/mostlygeek/llama-swap) | Separate model-process proxy with on-demand swaps, TTLs, and configurable coexistence | Useful for heterogeneous backends or explicit swapping policy; compare its overlap with runtime-native management |
| [Strata Manager](https://github.com/hongfaqiu/strata-manager) | Setup, downloads/configurations, service controls, monitoring, tuning, benchmarks for Strata | A management companion if Strata wins. It is a separate project and its engine-version compatibility needs checking |
| [LM Studio lifecycle controls](https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict) | JIT load, idle unload and auto-eviction | Use its own controls when it is the selected server; avoid two systems independently evicting the same models |
| [Ollama lifecycle controls](https://github.com/ollama/ollama/blob/main/docs/faq.mdx) | Keep-alive, loading and concurrency configuration | Use if Ollama is the selected runner; test actual queue/memory behavior |
| [LiteLLM](https://docs.litellm.ai/docs/) | Provider normalization, routing, fallback, usage tracking, optional gateway | Useful when local plus several hosted providers becomes a real requirement; it is not a weight-serving engine |
| A small handler-side job queue | Priority, cancellation, resource leases, progress and bounded background work | Needed before speech, art generation, indexing, and training compete for one GPU |

Proposed BFI policy: interactive speech/chat takes priority; document indexing and memory consolidation are lower-priority jobs; image generation and training run in explicit resource modes. Do not let a model manager unload the active conversation model because a background embedder made a request. Training should have a clean handoff of GPU resources rather than racing chat for the last available VRAM.

Load/unload policy must account for load latency. Aggressive eviction can save idle memory but create repeated cold starts. Persistent weights with bounded conversation slots may outperform frequent swaps for small turns. Measure the owner's actual pattern: alternating characters, a long coding session, a voice call, and an image-generation request.

**5. The handler and agent frameworks**

Your handler is the application coordinator: it selects a character/model/adapter, assembles permitted context, invokes the model, validates tool requests, executes allowed tools, records results, and updates presentation. It should expose capability information such as real tool support, streaming, vision, adapter selection, cancellation, and lifecycle management. Compatible API syntax alone cannot establish those capabilities.

| Candidate | What it contributes | Recommended position |
| --- | --- | --- |
| Existing BFI FastAPI + typed Python services | A small codebase with established profiles, history, tool boundaries, and avatar integration | **Keep as the application foundation** |
| [Pydantic AI](https://github.com/pydantic/pydantic-ai) | Typed agent loops, tools, model abstractions, structured results, optional harness/evaluation features | **First helper framework to assess** for the Python application |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Explicit state graphs, checkpoints, interruptions, resumable execution | **Use when multi-step task state demands it**; no need to adopt solely for chat history |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | Agent/tool loops, sessions, handoffs, tracing, voice/realtime integrations | **Alternative SDK**; provider-agnostic support exists, but individual features/backends still need checking |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | Multi-language agents and workflow orchestration | **Broader alternative**, especially if .NET/Microsoft integration becomes a project requirement |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Role-oriented teams and event-driven flows | **Optional collaboration experiment**; evaluate added calls, context duplication, and value |
| [Letta](https://github.com/letta-ai/letta-code) | Stateful identity/memory-oriented agent runtime | **Alternative runtime architecture**; evaluate before combining it with another owner of the same agent loop |
| [Dify](https://github.com/langgenius/dify) | Visual app/workflow builder with RAG, agents, models, integrations | **Separate prototyping option** for learning workflows; a larger platform than BFI currently needs |

Several frameworks can technically be combined. The decision should follow ownership: one main loop, one authoritative conversation/task store, clear tracing, and adapters at the boundaries. A multi-agent framework does not make multiple model copies fit into VRAM or guarantee better reasoning. Begin with explicit specialist delegation for a concrete task; compare it with a single-model baseline before paying the additional token and latency costs.

For structured tool arguments, prefer native constrained generation where supported plus application-side validation. [Outlines](https://github.com/dottxt-ai/outlines) is an additional structured-generation option. Valid JSON is only a formatting guarantee: the named file, selected date, requested action, or factual claim can still be wrong. Validate against the actual application state and show real tool failures instead of substituting successful-looking text.

**6. Useful tools, service integrations, and browser work**

| Need | Candidates | Selection rule for BFI |
| --- | --- | --- |
| Expose your Python tools | [MCP](https://modelcontextprotocol.io/docs/getting-started/intro), [FastMCP](https://gofastmcp.com/), direct typed functions/HTTP | Start with the existing functions; use MCP for reuse across compatible hosts |
| Connect many authenticated apps | [Composio](https://docs.composio.dev/docs/authentication) | Useful if maintaining several OAuth integrations becomes burdensome; evaluate credential/data custody and ongoing service cost |
| Narrow app workflows | Provider APIs / official connectors | Direct APIs give precise schemas, errors and scopes for a small set of known tasks |
| Scheduled and event-driven actions | [n8n](https://docs.n8n.io/hosting/) | Useful for recurring imports, notifications, and service-to-service workflows; separate from the live conversation loop |
| Web search | Existing Brave path, [Brave API](https://api-dashboard.search.brave.com/app/documentation/web-search), [Tavily](https://help.tavily.com/articles/3363168593-extracting-web-content-using-tavily), [SearXNG](https://docs.searxng.org/dev/search_api.html) | Compare evidence quality, cost, freshness, and maintenance. SearXNG self-hosting still queries external search services |
| Turn web pages into readable data | [Firecrawl](https://docs.firecrawl.dev/contributing/self-host), or a simpler content extractor for a narrow source | Distinct from search. Self-hosting requires operating its services; AI-backed features need configured model processing |
| Deterministic browser interactions | [Playwright](https://playwright.dev/python/docs/intro) | Best for repeatable known workflows and BFI UI checks |
| Open-ended browser tasks | [Browser Use](https://github.com/browser-use/browser-use) | Model-driven browser operations; evaluate reliability, calls, and local versus cloud browser settings |
| Code work | Repository tools, scoped execution, coding assistants | Return actual diffs, logs and test results; use task-specific workspaces |
| Calendar/course deadlines | Calendar API with the existing Canvas-to-Google-Calendar source | Start read-only and return freshness/sync status; memory should not silently override the deadline source |

The biggest practical improvement is often a well-designed tool: a clear name, typed inputs, useful error messages, bounded results, and source references. A character usually needs a small relevant tool set for a turn. Loading hundreds of descriptions increases context and selection work. Composio's current discovery approach and FastMCP's tool transformation/search features address this general problem, but the current BFI tool registry can also start with simple explicit selection.

Suggested first useful tools: find/read project material, query actual upcoming deadlines, inspect a repository change, run an allowed project check, and request a known art workflow. Keep searching, reading, editing, sending messages, and executing commands distinguishable actions. Retrieved documents provide evidence; they should not change which tools the application authorizes.

**7. Coding assistants and learning tools**

These help build BFI or perform coding work. They are distinct from the character runtime and from the inference server.

| Tool | Useful role | Assessment |
| --- | --- | --- |
| Existing Codex environment | Repository work, tests, documents, and connected tools | Continue using the current capability; its cloud workspace is not your permanent PC backend |
| [OpenCode](https://github.com/anomalyco/opencode) | Open coding-agent client with multiple agent modes | Candidate for a local coding workflow connected to a supported provider/runtime |
| [Aider](https://github.com/Aider-AI/aider) | Terminal coding assistance with Git-oriented change review and model connections | Useful comparison for a focused editing workflow; verify current model configuration rather than old example model names |
| [OpenHands Agent Canvas](https://github.com/OpenHands/OpenHands) | Current developer control center for coding agents, backends, and automations | Broader workbench to study; current project layout differs from older runtime tutorials |
| Versioned project instructions and skills | Working agreements, repeatable commands, design and learning notes | High value now. Describe actual repository practices and update them when decisions change |

For the skill-building goal, preserve a trace from request to file change to verification. Use clear diffs and a short explanation of why the code behaves differently. A useful coding assistant should expose enough evidence for you to explain the change, and the benchmark should include your ability to understand and reproduce it.

**8. Knowledge ingestion, retrieval, and memory**

This is one layer of the stack. It includes converting a source into usable text, indexing it, retrieving evidence, and managing durable facts or experiences. The initial system can keep original records in SQLite, then add selected components behind a provider interface.

| Responsibility | Relevant tools | Assessment |
| --- | --- | --- |
| Documents, PDFs, tables, OCR | [Docling](https://github.com/docling-project/docling) | Strong local candidate for course materials; test actual pages and preserve references |
| Embeddings | [FastEmbed](https://github.com/qdrant/fastembed), runtime embedding endpoints | CPU-first embeddings may preserve VRAM for interactive work; test relevance and indexing cost |
| Exact and semantic retrieval | SQLite FTS5; [Qdrant](https://github.com/qdrant/qdrant-client); [pgvector](https://github.com/pgvector/pgvector) | Choose storage needed by the winning approach; all three need not be separate services |
| Retrieval pipelines | [LlamaIndex](https://github.com/run-llama/llama_index), or narrow custom code | Useful when ingestion/query orchestration grows; distinguish toolkit from hosted parsing products |
| Extracted user/project memory | [Mem0](https://docs.mem0.ai/open-source/overview) | First incremental memory integration candidate |
| Consolidation, temporal evidence, reflection | [Hindsight](https://github.com/vectorize-io/hindsight) | Advanced comparison candidate with a larger service footprint |
| Peer and character perspectives | [Honcho](https://github.com/plastic-labs/honcho) | Companion-focused experiment; inspect its inferences separately from owner facts |
| Temporal relationships | [Graphiti](https://github.com/getzep/graphiti) | Specialist graph approach if historical relationship queries justify it |
| Connected knowledge and inspectability | [Cognee](https://github.com/topoteretes/cognee), [OpenViking](https://github.com/volcengine/OpenViking), [MemOS](https://github.com/MemTensor/MemOS) | Broader alternatives to assess against the same source/correction tests |
| Cross-assistant building knowledge | [memU](https://github.com/NevaMind-AI/memU) | Relevant to continuity across coding hosts; distinct from BFI's runtime memory needs |

Keep owner preferences, project facts, and character experiences explicitly scoped. Retrieve current evidence with source/date/status; preserve corrections and rejected suggestions. Document/source provenance matters as much as semantic similarity. The previous report supplies the detailed memory comparisons, archived-product findings, and acceptance cases; it remains an appendix rather than the organizing center of this stack.

**9. Voice, video calls, and perception**

The complete voice path is microphone capture, speech/turn detection, transcription or audio interpretation, character reasoning/tools, speech generation, playback, and interruption handling. Calling adds transport, device permissions, reconnect behavior, and potentially remote networking. Camera or screen perception adds selected frames and a compatible vision model. Rendering the character is another output channel.

| Candidate | Role | Fit and tradeoff |
| --- | --- | --- |
| [LiveKit](https://docs.livekit.io/agents/) | Realtime rooms/transport plus agent framework and frontend integration | First candidate for an actual browser/phone call experience; self-hosting or managed transport are distinct deployment choices |
| [Pipecat](https://docs.pipecat.ai/overview/introduction) | Python audio/video pipelines coordinating providers and transports | First comparison for a modular local speech pipeline; evaluate overlap with LiveKit before combining them |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Local speech recognition with CPU and relevant GPU backends | Test microphone accuracy and short-turn latency; batch transcription speed alone does not prove conversational responsiveness |
| [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | Local recognition, synthesis, VAD and other speech components | Useful compact toolkit and a route to several local voice models |
| [Kokoro](https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/kokoro.html) and supported Piper-family voices | Local TTS choices | Audition intelligibility, character identity, prosody, startup and synthesis time; evaluate individual model/voice assets |
| Existing selected vision-language model | Interpret camera frames, images or screenshots | Check real runtime support and image-token/resource costs; text models cannot gain vision merely from a tool label |
| Supported hosted realtime APIs | Integrated low-latency speech and multimodal interaction | Optional hybrid branch if quality/latency justify ongoing usage and sending audio/video to a provider |

A modular STT → LLM → TTS pipeline is easier to inspect, replace, and connect to explicit tools. An integrated speech model can provide more natural timing/prosody but may constrain supported runtimes, voices, tools, and hardware. Evaluate both against the actual target experience rather than selecting solely by a demo.

Proposed voice acceptance test: natural conversation with your own microphone, interruption while the character is speaking, a tool request with a visible result, model cancellation without ghost speech afterward, and a recoverable device/network interruption. Measure end-of-speech detection time, transcription delay, time to first audible response, sustained synthesis, and tool latency separately.

For video, start with user-triggered image/frame inspection. Continuous high-rate vision can compete with speech/text inference. Keep recording and long-term ingestion separate choices; a call need not become a permanent audio/video archive. A speaking PNG with authored expression/pose changes can support the first call interface without an image-to-video model generating every frame.

**10. Art generation, editing, avatars, and animation**

There are four distinct jobs: generate or edit source artwork; prepare clean transparent assets; build authored motion/rigs; and render approved assets in response to character state. Treat source art and its derived exports as separate artifacts with reversible revisions.

| Tool / approach | Useful job | Fit for the current direction |
| --- | --- | --- |
| [ComfyUI](https://docs.comfy.org/) | Reusable image/video workflows, conditioning, editing, and application integration | Strong media-production candidate. Use a separate job/resource mode instead of making live avatar presentation wait for diffusion |
| [Krita AI Diffusion](https://github.com/Acly/krita-ai-diffusion) | Artist-facing edits and region/reference/sketch guidance using ComfyUI | Particularly relevant to reviewing and correcting character art in an editable canvas; current source documents AMD ROCm Windows/Linux support |
| Krita / Inkscape-style source editing | Authored raster/vector corrections, layers, transparent exports | Useful workflow category already compatible with the existing art files; evaluate exact export/fidelity requirements |
| Existing BFI renderer + PySide6 host | Approved pose selection, expression/motion cues, desktop overlay | Preserve the useful integration and validate native Windows behavior; no wholesale renderer replacement is implied |
| [Inochi2D](https://github.com/Inochi2D/inochi2d) | Realtime mesh-based puppet animation from layered art | Open ecosystem alternative if rigging later becomes desirable; existing flat PNGs still need authored layers/rigging |
| [Live2D Cubism](https://www.live2d.com/en/sdk/about/) | Editor/SDK ecosystem for expressive 2D character rigs | Larger art/rigging commitment with its own licensing; a later branch, not an automatic improvement over authored poses |
| [Diffusers LoRA training](https://huggingface.co/docs/diffusers/training/lora) | Learn media-specific style/subject adaptation | Separate image-model experiment; it does not train the language character's personality |

Current [ComfyUI requirements](https://docs.comfy.org/installation/system_requirements) describe native Windows AMD paths, but custom nodes and individual checkpoints still require validation. Its installation documentation/source also differ in some packaging details; pin the actual working recipe and versions.

The latest BFI handoff keeps full poseable-character research Later and rejects the v5 artwork. Researching rig tools does not change that decision. A tracing library or animation engine cannot establish aesthetic quality, coherent body layers, or preserved character identity. Evaluate one source/reference versus one candidate at the same scale/background before broader conversions. Record approval of pose ideas separately from approval of their eventual rendered artwork.

For reproducibility, retain workflow JSON, exact model/LoRA revisions, source references, seed/settings when relevant, and the approved output. Future regeneration should be a deliberate new version, not an invisible rebuild that changes every character asset.

**11. Personality training and custom-model serving**

Training is a major project track. The important deliverable is a learned artifact that can be saved, reloaded, served through BFI, and compared fairly with its starting checkpoint. Getting a training UI to launch is one setup milestone; demonstrating that end-to-end loop is the meaningful experiment.

| Tool | Responsibility | Selection considerations |
| --- | --- | --- |
| [Transformers + PEFT](https://github.com/huggingface/peft) | Direct models and parameter-efficient adapters such as LoRA | Transparent baseline for inspecting what changes and reloading adapters |
| [TRL](https://github.com/huggingface/trl) | Supervised and preference/post-training methods | Useful for curated personality/behavior examples and later preference experiments |
| [Unsloth](https://unsloth.ai/docs/get-started/install/amd) | Optimized fine-tuning workflows with current AMD Windows/Linux documentation | First convenience/optimization candidate to validate on the Radeon PC |
| [Axolotl](https://docs.axolotl.ai/docs/installation.html) | Config-driven model training and experiment setup | Alternative for reproducible recipes if the chosen model/backend fits |
| [LlamaFactory](https://llamafactory.readthedocs.io/en/latest/) | UI and recipes spanning preparation, tuning, merging, quantization and evaluation | Useful learning option; its extensive method list is not a promise that every combination runs on RX 7900 XTX |
| [Accelerate](https://github.com/huggingface/accelerate) | Device/mixed-precision/distributed training plumbing | Usually used through or alongside the chosen trainer; not itself a personality-training recipe |
| [bitsandbytes](https://huggingface.co/docs/bitsandbytes/installation) | Low-bit/optimizer components for supported workflows | Current AMD/Windows support exists; match versions and kernels to the actual training setup |
| [MLflow](https://github.com/mlflow/mlflow) | Training parameters, metrics, artifacts, lineage and experiments | Candidate for tracking repeated experiments; begin with a readable local run record if that is sufficient |
| [Hugging Face Hub tooling](https://huggingface.co/docs/huggingface_hub/guides/download) | Download/cache pinned checkpoint revisions and manage artifacts | Useful now; private data/checkpoints do not need to be publicly uploaded |

The first personality experiment should choose a narrow trait and practical purpose, curate examples, keep held-out scenario families, train a small adapter, and compare the exact starting model with and without it under the same prompt/context/tools. Preserve task competence and calibrated uncertainty while measuring the intended personality change. Automatic judges can assist but should not replace human evaluation of the chosen traits.

A small model is useful for proving the engineering loop before scaling toward the larger ambition. The existing plan suggests a 1–4B feasibility range, not a guarantee or permanent model choice. LoRA reduces trainable parameter count, but base weights, activations, optimizer state, and sequence length still determine feasibility. Gradient accumulation and checkpointing trade runtime/compute against memory; low-bit training and long sequences require tested kernel support.

Plan serving before a large dataset: Transformers+PEFT directly; a supported adapter conversion; or merge into a compatible base and export/quantize. [vLLM's LoRA documentation](https://github.com/vllm-project/vllm/blob/main/docs/features/lora.md) describes supported per-request adapters, while llama.cpp has its own adapter path. Support is architecture-specific. Strata's documented inference support does not by itself establish our personality-adapter route. Re-evaluate behavior after conversion/quantization.

Record base/tokenizer revisions, dataset hashes/splits, template, adapter targets/rank, precision, optimizer, sequence length, batch/accumulation, seeds, packages/drivers, loss, peak memory and final artifact hashes. Keep language personality adapters, visual style adapters, voice models, prompts, skills, and remembered facts separately identifiable. Their updates can coordinate without pretending they are the same kind of learning.

**12. Background jobs, resumability, packaging, and deployment**

| Tool / mechanism | Useful responsibility | BFI recommendation |
| --- | --- | --- |
| Simple persisted application queue | Pending jobs, cancellation, progress, prioritization | Start here for modest single-PC work; ensure restart behavior is explicit |
| LangGraph checkpoints or framework-native persistence | Resume an agent's structured task state | Use when a multi-step agent task needs it |
| [Temporal](https://docs.temporal.io/develop/python) | Durable workflows, workers, timers, retries, cancellation | Larger option for long-running, failure-prone workflows; significant infrastructure for a small desktop prototype |
| n8n | Scheduled/event-based app workflows | Useful for calendar/doc synchronization and service automation; distinct from GPU scheduling |
| [uv](https://docs.astral.sh/uv/concepts/projects/sync/) and separate environments | Reproducible Python dependencies | Keep BFI, speech, ComfyUI and training dependencies isolated where versions conflict |
| Docker/Podman-style service packaging | Databases, web services, job workers, reproducible process environments | Useful where supported; containerization is not proof of GPU passthrough or isolation for arbitrary host mounts |
| OS service/startup configuration | Launch/restart the selected backend and handler | Essential for repeatable PC sessions; choose once process ownership is settled |
| [Tailscale](https://tailscale.com/docs/how-to/quickstart) | Private access between your devices | Candidate for reaching the PC from a phone; still design BFI authentication, browser media requirements and availability |
| [restic](https://github.com/restic/restic) plus database-aware exports | Versioned backups of conversations, memory and custom artifacts | Add a tested restore process, not just an export button |

The [Docker Desktop Windows GPU guide](https://docs.docker.com/desktop/features/gpu/) describes NVIDIA GPU-PV through WSL2 for its standard Linux-container passthrough path. It is not evidence that the same command provides Radeon GPU access. Native Windows AMD execution, Linux ROCm, and WSL/container recipes must be evaluated as separate configurations.

With 32 GB RAM and one GPU, every database, browser, embedding model, ComfyUI instance and tracing stack has a real footprint. A 1 TB system disk also holds OS/apps, original models, alternate quantizations, dataset copies, caches and training checkpoints. Start with a few intentional artifacts; avoid accumulating every promising checkpoint. Pin known-good environments and test an upgrade before replacing a working runtime.

For backups, first obtain a consistent database snapshot/export using the database's supported mechanism; SQLite provides an [online backup API](https://www.sqlite.org/backup.html). Then back up sources, preferences, prompts/configuration, custom adapters, approved art and workflow files. Record what can be redownloaded and what is irreplaceable. Retention and memory-deletion behavior should agree. Verify restoration to a fresh directory/instance.

A phone UI or cloud-hosted frontend does not make a powered-off PC run models. Remote availability needs an always-on machine or hosted backend. Keep a local-only mode and explicitly chosen hosted-model routes. Account for actual API/compute/storage usage and provider-supported authentication rather than assuming a chat subscription supplies unrestricted API access.

**13. Observability, profiling, and evaluation**

| Question | Useful tools | Evidence to keep |
| --- | --- | --- |
| Is the GPU used, and where is memory going? | Windows/AMD runtime monitoring; supported backend logs; [AMD SMI on its documented Linux platforms](https://github.com/ROCm/rocm-systems/blob/develop/projects/amdsmi/README.md) | GPU/CPU use, allocated/peak memory, load logs, driver/build |
| How fast are prompt processing and decoding? | [llama-bench](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md), runtime-native benchmarks | Same artifact/config, warmup, prompt/output lengths and repetitions |
| How does a serving endpoint behave under load? | [GuideLLM](https://github.com/vllm-project/guidellm), backend serving benchmarks | First-token/inter-token/end-to-end latency distributions and concurrency |
| Which operation is slow? | [PyTorch Profiler](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html) for supported builds; engine-specific profiling | Actual traces for the installed hardware/backend; Python timing alone does not explain every GPU bottleneck |
| What did the agent actually do? | Existing provenance/logs, [OpenTelemetry](https://github.com/open-telemetry/opentelemetry-python), [Langfuse](https://github.com/langfuse/langfuse) | Model request, retrieved sources, tool call/result, retries, timing, errors, final artifact |
| Did a model/prompt/tool change improve behavior? | [Promptfoo](https://github.com/promptfoo/promptfoo), Pydantic Evals | Versioned cases and assertions, comparable settings, failures and variation |
| Did tuning damage general ability? | [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) plus practical BFI tasks | Held-out competence alongside personality scoring |
| Did the browser/overlay behave correctly? | Playwright; actual Windows execution for native overlay | Rendered behavior, device/display scaling, cancellation/recovery |
| Is the artwork good? | Side-by-side source comparison and owner review | Explicit visual acceptance; engineering checks remain separate |

For a small stack, existing structured logs may be enough. Langfuse, MLflow and framework tracing overlap in some areas; select a main route when there is an inspection problem to solve. Trace storage can contain private prompts and tool results, so configure which content is retained and whether exporters are local or hosted. Do not send traces externally merely because a library enables a default integration.

Use a BFI workload suite with short conversation, long-context evidence, valid/invalid tool arguments, real tool failure, coding task, preference correction, trained-character behavior, image request, voice interruption, model switch, and restart. Record median and tail latency plus quality. A high synthetic tokens/second result is useful evidence about inference, not proof that the whole companion works well.

**14. Complete apps: adopt one or keep building BFI?**

| Application | Good reason to try it | Relationship to BFI |
| --- | --- | --- |
| [Open WebUI](https://github.com/open-webui/open-webui) | General local-model chat and knowledge workbench | Useful separate testing console; avoid creating an accidental second source of character state |
| [SillyTavern](https://github.com/SillyTavern/SillyTavern) | Character-oriented chats, lore/context and model experimentation | Useful reference for interaction design, not evidence of trained personality |
| [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) | Voice/vision/avatar companion reference | Current README says long-term memory was temporarily removed and v2 is early planning; inspect current features before adoption |
| Dify | Visual agent/RAG/workflow prototype | An alternative application-building route, not required around the existing FastAPI service |
| OpenHands Agent Canvas | Coding-agent/control-center experiments | Developer workbench rather than the BFI character presentation layer |

Trying a complete app can teach us what interactions you like before rebuilding them. Keep trial data separate and document what would need migration. Check current app, model and media licenses for the intended use; a public repository does not imply every included artifact has the same license.

**15. The stack I would put on the shortlist**

| Responsibility | Initial choice / experiment | Why |
| --- | --- | --- |
| Application | Existing BFI handler and SQLite | Preserves implemented work and learning trail |
| Local inference | Measured llama.cpp vs Strata trial; LM Studio as an accessible console | Directly relevant to Radeon/Windows plans |
| Management | Runtime-native lifecycle first; llama-swap for a demonstrated gap | Avoid competing process/eviction owners |
| Optimization | Model/quantization headroom, bounded context/output, backend checks, then cache/speculation tests | Targets measured cost and memory |
| Tools | Existing typed tools; FastMCP when sharing them; actual project/calendar/search workflows | Useful capabilities with inspectable results |
| Agent framework | Assess Pydantic AI; LangGraph when resumable workflows justify it | Fits Python without an automatic rewrite |
| Memory/knowledge | One memory pilot; CPU-first embeddings; Docling when course ingestion starts | Contains background resource use |
| Voice | LiveKit or Pipecat, local recognition/TTS comparison | Clear call/pipeline architecture |
| Art | ComfyUI and optionally Krita integration; retain approved poses/renderer | Separates art production from presentation |
| Training | Small PEFT/TRL or Unsloth train-save-serve comparison; assess Axolotl/LlamaFactory alternatives | Direct route toward learned personality |
| Measurement | Structured provenance + llama-bench/endpoint benchmark + BFI quality cases | Evidence before optimization claims |
| Deployment | Locked environments, intentional service ownership, consistent backups | Reproducibility and recoverability |

This is a shortlist of responsibilities, not an instruction to install every named alternative. Add a component when its role, owner, dependencies and verification are clear. The biggest integration work is likely in the boundaries: model capabilities, scoped tool results, streamed/cancelled generation, resource scheduling, and reliable artifact identity.

**16. A concrete research-to-implementation sequence**

1. **Record the machine and model baseline.** Verify hardware/driver/OS, choose a small compatible model plus exact files/template, and run actual GPU inference with versioned logs. No RAM or hardware purchase follows from this report.
2. **Measure and tune one workload.** Prompt/decode benchmark, real BFI chat/tool cases, realistic context and headroom. Compare one backend/quantization at a time. Establish cold and warm results.
3. **Complete one training loop.** On a feasible small model, train/save/reload a personality adapter, serve it, and compare against the unchanged checkpoint on held-out tasks. Keep this central goal visible while other work proceeds.
4. **Extend the handler contract.** Streaming, cancellation, capability reporting, versioned character/model/adapter identity, explicit job status and real provenance. These support voice and multiple characters later.
5. **Give it useful work.** One project tool, one deadline/source workflow, and correctable memory/knowledge. Evaluate actual task completion and recoverable failures.
6. **Add voice and media modes.** Speech prototype and avatar cues, then calls/vision; art requests through a managed queue. Resource tests should include the components used together.
7. **Test multiple characters and availability.** Compare shared-base identities, supported adapters, swaps and true concurrency. Add remote access, background jobs and richer services according to measured value.

Useful work before the PC arrives includes contracts, source organization, training examples, evaluation cases, UI designs and reproducible configuration plans. The PC is required to establish actual Radeon speed, memory fit, adapter/kernel compatibility, training capacity, and native overlay behavior. Source documentation establishes a plausible path; simulation, successful installation, and a polished hosted demo each establish different things.

**17. What belongs in this chat, on the PC, or on a server**

| Location | Appropriate capabilities | Boundary |
| --- | --- | --- |
| This chat's available tools | Research/search, images, code/workspace work, GitHub, Notion, and supported browser interaction | Session tool availability is not a permanent BFI deployment or a guarantee that every future chat has identical context |
| Your PC | Local model engine, BFI handler, speech components, media jobs, training, local storage | Processes need launch/health/resource management; local availability depends on the PC running |
| An optional always-on server | Remote model endpoints, scheduled workers, shared services, call availability | Additional operations and ongoing cost; not assumed necessary for the first local system |
| A hosted provider | Optional frontier/realtime models or managed connectors | Explicit provider account, supported integration, quotas, and data destinations |

MCP/API tools can expose selected BFI operations to compatible assistants. Connecting such a tool does not automatically replace a host application's inference engine or import all its past conversations. Define the service contract and test it in the exact client. Keep local BFI source data authoritative and record which integrations actually read/write it.

**18. Coherent setup patterns and their tradeoffs**

| Pattern | Typical components from this research | Benefit | Cost and maintenance |
| --- | --- | --- | --- |
| Local desktop system | BFI + one model server + selected local speech/knowledge tools | Control, offline-capable core, direct path to learned adapters | PC RAM/VRAM/disk and local troubleshooting; availability while powered on |
| Hybrid personal system | Local BFI and data with selected hosted model/tool calls | Can use specialist/frontier capabilities without making every workload local | Usage-based charges, latency/network dependency, explicit data-sharing rules |
| Managed API-first app | Hosted models, managed realtime/connectors, application backend | Faster route to a remotely available product | Recurring service cost, provider constraints, and less control over the underlying inference |
| Homelab/server system | Always-on host, serving runtime, private networking, workers, monitoring | Phone access and scheduled work independent of the desktop session | Server operations, power/compute/storage, backups and upgrades |

These are supported architectural patterns, not a claim about market share. The best starting fit for your recorded goals is the local desktop pattern with a carefully chosen optional hybrid route. The first budget should count disk duplicates, resident services, training checkpoints, hosted model calls, realtime transport, connectors and trace storage, not just the price of model weights.

The open-source license, download price, self-hosting ability, and permission to use a particular model/media asset are separate properties. Source review can narrow candidates; demonstrated integration, measured performance, and your acceptance determine the actual stack.
