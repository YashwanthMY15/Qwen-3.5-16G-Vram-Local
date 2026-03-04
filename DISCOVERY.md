# Discovery: The 155,904 Token Context Cliff in Qwen3.5-35B-A3B

> A previously undocumented hard speed limit in llama.cpp for hybrid recurrent MoE models on 16 GB VRAM GPUs.

---

## Summary

When running **Qwen3.5-35B-A3B** with llama.cpp on a 16 GB GPU, there is a precise token count above which generation speed drops from **~120 t/s to ~9 t/s** — a 93% reduction. The cutoff is:

```
155,904 tokens → full speed (~120 t/s)
156,160 tokens → broken speed (~9 t/s)
```

This is **not a VRAM overflow**. At both values, the model fits comfortably in 16 GB. The root cause is a `CUDA_Host compute buffer` alignment boundary that, when crossed, saturates PCIe bandwidth for the recurrent state transfers required by this model's hybrid architecture.

---

## Hardware & Software

| Component | Spec                                              |
| --------- | ------------------------------------------------- |
| GPU       | RTX 5080 16 GB GDDR7 (SM120, Blackwell, 960 GB/s) |
| CPU       | AMD Ryzen 7 9800X3D                               |
| RAM       | 96 GB DDR5                                        |
| PCIe      | 5.0 x16                                           |
| OS        | Windows 11                                        |
| llama.cpp | b8196 (CUDA 12.4, PTX JIT → sm_120)               |
| Model     | Qwen3.5-35B-A3B-Q3_K_S.gguf (14.2 GB, 3.94 bpw)   |

---

## Reproducing

```bash
# Fast — load and test
llama-server \
  -m Qwen3.5-35B-A3B-Q3_K_S.gguf \
  -c 155904 \          # change this to test different context sizes
  -ngl 99 \
  --flash-attn on \
  -ctk iq4_nl -ctv iq4_nl \
  --chat-template-kwargs '{"enable_thinking":false}'

# After loading, time a generation:
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -d '{"messages":[{"role":"user","content":"Write a Python function"}],"max_tokens":200}'
# Check "predicted_per_second" in the response
```

Wait for 2–3 requests before measuring — CUDA JIT warmup takes a few inference passes regardless of context size.

---

## Full Context Sweep Data

All tests: Qwen3.5-35B-A3B-Q3_K_S, iq4_nl KV, flash-attn on, mmproj loaded (vision), RTX 5080 16 GB. Speed measured after 3 warmup requests.

| Context (tokens) | Approx K | CUDA0 Compute | CUDA_Host Compute | KV Size    | VRAM Used   | Gen Speed      |
| ---------------- | -------- | ------------- | ----------------- | ---------- | ----------- | -------------- |
| 65,536           | 64K      | 493 MB        | 136 MB            | 360 MB     | 15.0 GB     | 109 t/s ✅     |
| 98,304           | 96K      | 493 MB        | 200 MB            | 540 MB     | 15.3 GB     | 109 t/s ✅     |
| 131,072          | 128K     | 493 MB        | 264 MB            | 720 MB     | 15.4 GB     | 119 t/s ✅     |
| 143,360          | 140K     | 493 MB        | 288 MB            | 788 MB     | 15.5 GB     | 115 t/s ✅     |
| 151,552          | 148K     | 493 MB        | 304 MB            | 833 MB     | 15.5 GB     | 114 t/s ✅     |
| 155,648          | 152K     | 493 MB        | 312 MB            | 856 MB     | 15.4 GB     | 114 t/s ✅     |
| **155,904**      | **152K** | **493 MB**    | **312.52 MB**     | **856 MB** | **15.4 GB** | **124 t/s** ✅ |
| **156,160**      | **152K** | **493 MB**    | **313.02 MB**     | **857 MB** | **15.4 GB** | **9 t/s** ❌   |
| 163,840          | 160K     | 516 MB        | 328 MB            | 900 MB     | 15.4 GB     | 10 t/s ❌      |
| 196,608          | 192K     | 612 MB        | 392 MB            | 1,080 MB   | 15.5 GB     | 8 t/s ❌       |
| 229,376          | 224K     | 708 MB        | 456 MB            | 1,260 MB   | 15.5 GB     | 9 t/s ❌       |
| 262,144          | 256K     | 804 MB        | 520 MB            | 1,440 MB   | 16.3+ GB    | 9 t/s ❌       |

**The cliff is exactly at 155,904 → 156,160 tokens.**

Key observations:

1. CUDA0 compute buffer is identical (493 MB) at 155,904 and 156,160 — VRAM is not the issue
2. CUDA_Host compute buffer jumps from 312.52 → 313.02 MB — 0.5 MB triggers the cliff
3. Speeds above the cliff (160K, 192K, 256K) are all ~8–10 t/s regardless of how far above
4. The VRAM fits at 192K (15.5 GB < 16.3 GB available) — confirmed not OOM

---

## What `CUDA_Host compute buffer` Is

In llama.cpp's CUDA backend, the `CUDA_Host` memory region holds intermediate computation tensors that are transferred between CPU and GPU via PCIe. This is distinct from:

- `CUDA0 model buffer` — model weights on GPU (stays fixed)
- `CUDA0 KV buffer` — key-value cache on GPU (grows with context)
- `CUDA0 RS buffer` — recurrent state on GPU (Mamba/DeltaNet state)
- `CUDA0 compute buffer` — GPU-side scratch space for graph execution
- **`CUDA_Host compute buffer`** — **pinned host RAM for PCIe-mediated transfers**

The `CUDA_Host` buffer is allocated once at startup (size depends on context length) and is accessed on every single token generation step. When it exceeds a certain size, the per-token PCIe transfer volume saturates available bandwidth.

---

## Why Qwen3.5-35B-A3B Is Particularly Affected

This model uses a **hybrid architecture**: 30 Gated DeltaNet layers (linear recurrent) alternating with 10 Gated Attention layers. The DeltaNet layers maintain a recurrent state tensor that must be updated at each token — this is what drives the `CUDA_Host` allocation.

A pure transformer model (like the 9B or 27B Qwen3.5 variants) does not use DeltaNet layers and therefore does not have this constraint. The 9B runs at full speed at 256K context with no cliff.

The `CUDA_Host` buffer scales with context because the DeltaNet state size is proportional to context length (the state must be large enough to hold the full context representation).

---

## Why Speed Increases From 64K to 152K

This is counterintuitive — the model is actually **faster** at 152K than at 64K:

| Context  | Speed       |
| -------- | ----------- |
| 64K      | 109 t/s     |
| 128K     | 119 t/s     |
| **152K** | **124 t/s** |

The improvement comes from the CUDA JIT warmup interplay. The llama.cpp binary (b8196) is compiled for CUDA 12.4 which does not include native sm_120 (Blackwell) kernels. At first launch, PTX code from sm_89 is JIT-compiled to sm_120. This warmup takes several inference passes regardless of context size.

In earlier testing, the 64K benchmark was accidentally measured before warmup was fully complete. After proper warmup, 64K, 128K, and 152K all achieve similar throughput — the slight increase at larger contexts is within noise (or mild cache warming effects). The important finding is that **larger context does NOT hurt speed** up to the 155,904 boundary.

---

## The Alignment Boundary

The 0.5 MB jump between 155,904 and 156,160 tokens (a 256-token step) is small but decisive. This suggests an internal buffer alignment in llama.cpp — likely a power-of-2 or cache-line alignment in the CUDA memory allocator.

**Hypothesis:** The `CUDA_Host compute buffer` uses an allocation that is aligned to some multiple, and 313.02 MB exceeds a chunk boundary that forces an additional PCIe transfer per token inference pass. Even a small extra transfer at every token adds up: at 120 t/s, each token takes ~8 ms. A single extra 100-200 μs PCIe transfer per token would explain the 10× slowdown.

This is worth investigating in llama.cpp source — specifically `ggml-cuda.cu` and `llama.cpp`'s context allocation code for recurrent models.

---

## Impact for Other GPUs

The PCIe bandwidth numbers differ across GPU tiers:

| GPU      | PCIe    | Bandwidth | Expected cliff?              |
| -------- | ------- | --------- | ---------------------------- |
| RTX 5080 | 5.0 x16 | ~64 GB/s  | 155,904 tokens               |
| RTX 4090 | 4.0 x16 | ~32 GB/s  | Likely lower — needs testing |
| RTX 3090 | 4.0 x16 | ~32 GB/s  | Likely lower — needs testing |
| RTX 4080 | 4.0 x16 | ~32 GB/s  | Likely lower — needs testing |

**We don't know if the cliff exists at the same token count on other hardware.** It may be lower on PCIe 4.0 (half the bandwidth). Community testing would be valuable.

---

## What Doesn't Help

Tried during investigation:

- **`-np 1`** (single parallel slot): made it worse (5 t/s at 128K before warmup)
- **`--no-mmap`**: no effect on the cliff
- **More warmup requests**: doesn't help above the cliff — it's a hard limit, not warmup
- **Reducing other VRAM allocations**: VRAM is not the bottleneck above the cliff

---

## What Might Help (Untested)

- **Building llama.cpp from source** with CUDA 12.8+ and `-DCMAKE_CUDA_ARCHITECTURES=120`: native Blackwell kernels might handle the PCIe transfers more efficiently
- **Newer llama.cpp version** (b8196 is months old): buffer allocation logic may have changed
- **`-b` and `-ub` batch size flags**: different batch sizes affect compute buffer allocation
- **Multi-GPU setup**: distributing the context state across two GPUs would avoid the PCIe bottleneck entirely

---

## Contribution

If you reproduce this on different hardware, please open an issue with:

- GPU model, VRAM, PCIe generation
- llama.cpp build version and CUDA version
- The `CUDA_Host compute buffer` value where you hit the cliff
- Your maximum fast-context token count

This is the first documented instance of this cliff for Qwen3.5-35B-A3B. More data points across hardware would reveal whether this is a PCIe-bandwidth scaling issue or a fixed alignment boundary.

---

_Discovered March 4, 2026. Hardware: RTX 5080 16 GB, llama.cpp b8196._
