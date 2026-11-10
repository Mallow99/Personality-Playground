# Hardware and compatibility notebook

**Evidence reviewed: November 9, 2026.** No measurements from the purchased PC have
been made. The cloud development environment is not that PC.

Three separate questions must be answered: can a backend run inference on this GPU,
can a training stack update an adapter on this GPU and OS, and can the resulting
custom model actually be served? A yes to the first does not establish the others.

## What the reviewed documentation establishes

| Area                            | Documented evidence                                                                                                                                                        | What remains unverified                                                                                                        |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| AMD inference                   | llama.cpp documents HIP builds on Linux and Windows. Its Windows example explicitly identifies `gfx1100` with RX 7900 XTX/XT/GRE. It also documents Windows Vulkan builds. | Driver/toolchain combination, model architecture, stability, usable speed, and GPU offload on this exact PC                    |
| Chat API                        | llama.cpp's server documents OpenAI-compatible chat completions.                                                                                                           | End-to-end operation with BFI and the selected model / chat template                                                           |
| Custom serving                  | The server documents `--lora` and `--lora-scaled` options.                                                                                                                 | Whether the selected base, training format, conversion, adapter, quantization, and runtime version work together               |
| AMD training                    | No specific training stack/version has been validated here.                                                                                                                | Current official GPU/OS matrix, PyTorch/ROCm versions, precision, optimizer and quantization kernels, peak memory, correctness |
| Named model candidates / Strata | Names are retained in `vision.md`. Exact artifacts and the intended Strata project are not yet resolved.                                                                   | Model cards, architecture support, licenses, release identity, actual performance                                              |

Reviewed upstream files:

- [llama.cpp build documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#hip)
  (Git blob `4e3bfe651b391fa5a7ffa4e63922ed43b99c8d93`; HIP and Vulkan sections).
- [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
  (Git blob `dad14aaf16f813bae974a5e92aa41116a5d3386b`; API features and LoRA flags).

Upstream `master` changes. These are documentation observations, not successful
builds, benchmarks, or blanket compatibility guarantees. Consult the current
[AMD Radeon/ROCm documentation](https://rocm.docs.amd.com/projects/radeon/en/latest/)
and [PyTorch installation guidance](https://pytorch.org/get-started/locally/) before
selecting a training stack; their current support matrices were not validated in
this milestone. Do not translate CUDA-only QLoRA instructions into AMD promises.

## Memory intuition, not a fit guarantee

27 billion parameters at exactly 4 bits each occupy about **13.5 GB / 12.6 GiB** in
raw weight bits. Real quantization adds metadata and mixed-precision tensors; context
KV cache, compute buffers, display use, and other applications also consume memory.
FP16 raw weights alone would be about 54 GB. Training additionally needs activations,
gradients, optimizer state, and working memory even if most base weights are frozen.
A 24 GB inference possibility says little about 27B training feasibility.

More system RAM can help CPU offload and larger working sets. It does not increase
VRAM or guarantee comfortable decoding. Mixture-of-experts active-parameter counts
alone do not tell you how much total storage or RAM is required. Check total weights,
offload behavior, memory bandwidth, disk use, and measured latency.

## Arrival checklist

1. Verify actual CPU, GPU, RAM, board, storage, OS, firmware, and driver versions.
   Check CPU firmware/vendor guidance and system stability before diagnosing model
   software. Save a plain-text inventory locally, excluding serials and personal data.
2. Check storage headroom. The OS, model variants, checkpoints, optimizer state,
   caches, and exports can use a 1 TB drive quickly. Download one candidate at a time.
3. Start with a modest compatible quantized model and an explicit context limit.
   Confirm GPU offload using server logs and GPU monitoring; a reply alone may be CPU inference.
4. Record idle RAM/VRAM, load time, prompt processing time, time to first token,
   generation rate, peak RAM/VRAM, context length, quantization, and output settings.
   BFI's elapsed time measures the whole request; it does not measure first-token
   latency or generation speed separately.
5. Repeat with normal desktop applications open. Then test the intended larger
   companion and smaller fallback under the same prompts and settings.
6. Stop/unload using the server's supported mechanism; verify VRAM is released.
7. Only propose a RAM upgrade or Linux installation after a specific measured
   bottleneck and a credible remedy. No hardware purchase is authorized by this plan.

## Measurement record to copy for each attempt

```text
Date / PC inventory reference:
OS / driver / backend version or commit:
Exact model ID / revision / file hash / license:
Quantization / context / GPU layers / chat template:
Prompt and sampling settings / run count:
Idle and peak RAM / VRAM:
Load seconds / first-token seconds / output tokens per second:
Other applications open / system stability:
Unload behavior / failures / logs:
Inference established? Training established? Custom serving established?
Conclusion and next measurement:
```
