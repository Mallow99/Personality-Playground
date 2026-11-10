# Local runtime integration and researched references

BFI is meant to run on the purchased Windows PC: local Python service, local browser
interface, local history, and a replaceable local inference endpoint. Notion is an
optional project organizer; the app does not call it to start or chat. Web search,
calendar access, and frontier assistance are optional online capabilities with
separate configuration and source records.

## What is implemented

The existing OpenAI-compatible inference adapter is used by all three profiles.
Each can inherit the global endpoint/model or use its own `BFI_ACADEMIC_*`,
`BFI_ENGINEERING_*`, or `BFI_BUSINESS_*` routing overrides. The app checks `/models`
and sends non-streaming `/chat/completions` requests, optionally with standard
function-tool definitions. A compatible model, template, and runtime are required.
An endpoint being reachable does not establish tool-call quality.

```dotenv
BFI_BACKEND=openai
BFI_BASE_URL=http://127.0.0.1:8080/v1
BFI_MODEL=the-alias-your-server-advertises

# Optional per-character overrides; omit them to share the global route.
BFI_ENGINEERING_MODEL=your-coding-model-alias
BFI_ENGINEERING_BASE_URL=http://127.0.0.1:8081/v1
BFI_ACADEMIC_ADAPTER_LABEL=study-personality-r1
```

An adapter label records your configuration and makes it visible in provenance. It
does **not** load an adapter, prove its identity, or train weights. Load a compatible
adapter or merged artifact in the external server, use the appropriate alias, and
record verified artifact hashes and load evidence before claiming custom serving.

Prefer **interfacing first**: install and test the loader/runtime separately, then
point BFI at its local API. A future installer may check or bundle optional pieces,
but BFI does not currently install drivers, runtimes, models, Docker, WSL, or training
dependencies, and does not start/stop another application's model process.

## Strata findings

Reviewed November 9, 2026. A plausible match to the requested runtime is
[Niko1221/Strata](https://github.com/Niko1221/Strata). The owner did not supply a link,
so identity confirmation remains welcome; this is the concrete project researched.

| Evidence                                                                                        | What upstream documents                                                                                                              | What BFI has verified                                                                |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| [README](https://github.com/Niko1221/Strata/blob/main/README.md)                                | Qwen3.8-Flash-Next, compatible APIs, Windows/Linux/AMD paths                                                                         | Documentation read; no engine installed or model run here                            |
| [AMD HIP guide](https://github.com/Niko1221/Strata/blob/main/docs/AMD_HIP.md)                   | RX 7900 XTX listed as maintainer-tested; Windows RDNA3 package; driver and diagnostic guidance                                       | No test on the delivered PC, no blanket PyTorch/training inference                   |
| [Model guide](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md)                      | Low-RAM mode for 32 GB RAM + 24 GB GPU using Q2_0, IQ2_XS, or Coder; original downloads roughly 66–76 GB plus draft/vision artifacts | A credible configuration to investigate, not a comfort/performance guarantee         |
| [Management protocol](https://github.com/Niko1221/Strata/blob/main/docs/MANAGEMENT_PROTOCOL.md) | Owner-local process IPC with reviewed lifecycle operations and documented qualification limits                                       | Not implemented in BFI; inference APIs and model management are different interfaces |
| Personality LoRA serving                                                                        | No validated route identified in the reviewed material                                                                               | Unverified, independent of inference support                                         |

The model guide distinguishes total weight estimates from RAM headroom, SSD expert
reads, and low-RAM behavior. Do not simply add 32 GB RAM and 24 GB VRAM and conclude
that every 56 GB model fits comfortably. Context, OS use, display use, disk behavior,
and runtime placement matter. Measure before proposing a RAM upgrade.

[hongfaqiu/strata-manager](https://github.com/hongfaqiu/strata-manager) is a separate
community manager for runtimes, configurations, local models, API checks, and
monitoring. It is not the inference engine. Both projects may be useful, but BFI
should connect to one clearly identified running service and avoid competing
lifecycle authorities. Copy the service's actual loopback address and model ID
into `.env`; no guessed Strata port or alias is hard-coded here.

Reviewed Git blobs (upstream main can change):

- Strata README: `455cb4174cb09a8ff98256f44cc96d34fc9a12ec`
- AMD guide: `28c04845fa336c0bc53601ea5dd92cb81b5b49a4`
- Model guide: `924a580e269b7f8eeaa4c8660665676cc548e992`
- Management protocol: `4d3940e2244a20838692cbf064f538519d6cc105`
- Manager README: `4a9362710f62ac84665ce169605cd8d970f3698b`

## Capri references without story research

Only technical source and license material was used. No story synopsis or character
media was needed. The BFI geometric characters and animation code are original.

| Reference                                                                                                               | Useful pattern                                                    | Source/license evidence                                                                                                |
| ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| [CapriCore theme module](https://github.com/CapriChooms/CapriCore/blob/main/apps/desktop/renderer/interface-theme.mjs)  | Theme tokens separated from character behavior                    | File identifies GPL-3.0-only; blob `9f75d1fe98fdb07cce70420a24e588027541ff01`                                          |
| [CapriCore pose motion](https://github.com/CapriChooms/CapriCore/blob/main/apps/desktop/avatar-pose-motion.mjs)         | Bounded presentation motion distinct from model inference         | File identifies GPL-3.0-only; blob `60ff55c819fe7ba4668fb11cb44c00d2120a9ad8`                                          |
| [Capri Companion pose map](https://github.com/TheAgencyMGE/capri-companion/blob/main/src/renderer/character/poseMap.ts) | Pose follows surface/posture state rather than arbitrary movement | Repository LICENSE is MIT for source, with separate media rights; pose blob `4da218b6d40b6b421fc2c4c91d2276cc3f657a36` |

Reuse is welcome when the specific code or asset license permits it. Record source,
revision, modifications, notices, and distribution requirements before copying.
Source-code permission does not automatically cover a character, animation asset,
trademark, model, or dataset. Private use and publishing have different implications;
the configured GitHub repository was observed public and has not been made private.
Prefer documented interfaces and original implementations for interoperability;
do not bypass accounts, keys, access controls, or technical restrictions.
