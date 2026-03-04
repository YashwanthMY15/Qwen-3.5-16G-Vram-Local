<div align="center">

<h1>⚡ Qwen3.5-35B-A3B on 16GB GPU</h1>

<p><strong>Maximum-speed local LLM on consumer hardware — 124 t/s with 152K context, vision enabled, fully documented.</strong></p>

<p><em>Tested on RTX 5080 · Works on any NVIDIA 16GB (RTX 30xx / 40xx / 50xx)</em></p>

<br>

<table>
  <tr>
    <td align="center"><b>⚡ Avg Speed</b></td>
    <td align="center"><b>🏎️ Peak Speed</b></td>
    <td align="center"><b>🧠 Context</b></td>
    <td align="center"><b>👁️ Vision</b></td>
    <td align="center"><b>🎮 GPU Layers</b></td>
    <td align="center"><b>💾 VRAM</b></td>
  </tr>
  <tr>
    <td align="center"><h2>124 t/s</h2></td>
    <td align="center"><h2>166 t/s</h2></td>
    <td align="center"><h2>152K</h2></td>
    <td align="center"><h2>✅ On</h2></td>
    <td align="center"><h2>41 / 41</h2></td>
    <td align="center"><h2>15.4 GB</h2></td>
  </tr>
  <tr>
    <td align="center">Q3_K_S · MoE</td>
    <td align="center">single token burst</td>
    <td align="center">155,904 tokens</td>
    <td align="center">mmproj loaded</td>
    <td align="center">all on GPU</td>
    <td align="center">245 MB free</td>
  </tr>
</table>

<br>

![GPU](https://img.shields.io/badge/NVIDIA-16GB_VRAM-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![Models](https://img.shields.io/badge/RTX_3060_Ti-RTX_5080-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Windows_Linux-native-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![llama.cpp](https://img.shields.io/badge/llama.cpp-b8196+-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)

</div>

---

## 🗺️ Contents

- [What's In Here](#-whats-in-here)
- [Key Results](#-key-results)
- [Quick Start](#-quick-start)
- [⚠️ The Discovery: 155,904 Token Cliff](#️-the-discovery-155904-token-cliff)
- [All Three Server Configs](#-all-three-server-configs)
- [Why the 35B MoE Is Faster Than It Looks](#-why-the-35b-moe-is-faster-than-it-looks)
- [Quantization Notes](#-quantization-notes)
- [Hardware Notes](#-hardware-notes)
- [Benchmarking](#-benchmarking)
- [Repo Structure](#-repo-structure)
- [Contributing](#-contributing--reproducing)

---

## 📦 What's In Here

A production-tested llama.cpp setup for **Qwen3.5-35B-A3B** (MoE) on **any NVIDIA 16GB GPU** — everything you need to hit max speed locally:

- ✅ **Verified numbers** — every benchmark run fresh, no aspirational figures
- 🔍 **Context cliff discovery** — the exact token count where 16GB GPUs hit a wall, and why
- 👁️ **Working vision** — multimodal (image input) confirmed working
- 🎛️ **Three ready-to-run profiles** — coding · fast vision · quality
- 📁 **Drop-in scripts** — Windows `.bat` launchers, Python benchmarks, health checks

> **Works on:** RTX 3060 Ti 16GB · RTX 4060 Ti 16GB · RTX 4070 Ti Super · RTX 4080 · RTX 5080 · Any NVIDIA 16GB+

---

## 📊 Key Results

### 🥇 35B-A3B Q3_K_S — Coding Server (Best Config)

| Metric              | Value                              |
| ------------------- | ---------------------------------- |
| ⚡ Generation speed | **124.7 t/s avg · 166.4 t/s peak** |
| 📥 Prompt ingestion | **538 t/s**                        |
| 🧠 Context window   | **155,904 tokens (≈152K)**         |
| 👁️ Vision           | **Yes** — mmproj loaded            |
| 💾 VRAM used        | **15.4 GB** (245 MB free)          |
| 🎮 GPU layers       | **41 / 41** — fully on GPU         |
| 🗜️ KV cache         | iq4_nl — only **856 MB** at 152K   |
| 📦 Model size       | 14.2 GB (Q3_K_S, 3.94 bpw)         |

### 🔀 All Three Profiles Compared

| Profile            | Model          | Port |  ⚡ Speed   | 🧠 Context | 💾 VRAM |
| ------------------ | -------------- | :--: | :---------: | :--------: | :-----: |
| 🖥️ **Coding**      | 35B-A3B Q3_K_S | 8002 | **124 t/s** |  **152K**  | 15.4 GB |
| 👁️ **Vision/Chat** | 9B Q4_K_XL     | 8003 | **97 t/s**  |  **256K**  | 10.6 GB |
| 🎯 **Quality**     | 27B Q3_K_S     | 8004 | **36 t/s**  |    64K     | 12.9 GB |

> **⚠️ One server at a time.** The 35B alone uses 15.4 GB — no two models fit in 16 GB simultaneously.

---

## 🚀 Quick Start

### Prerequisites

**1. Get llama.cpp**

Download the latest CUDA release from [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases):

```
llama-bXXXX-bin-win-cuda-12.4-x64.zip   ← Windows
```

Extract to `./llama-bin/` in this repo root.

**2. Download the models**

```bash
# 35B Coding server (14.2 GB)
huggingface-cli download unsloth/Qwen3.5-35B-A3B-GGUF \
  Qwen3.5-35B-A3B-Q3_K_S.gguf \
  mmproj-Qwen3.5-35B-A3B-F16.gguf \
  --local-dir ./models/unsloth-gguf/

# 9B Vision server (5.4 GB)
huggingface-cli download unsloth/Qwen2.5-VL-9B-Instruct-GGUF \
  Qwen2.5-VL-9B-Instruct-Q4_K_XL.gguf \
  --local-dir ./models/unsloth-gguf/
```

Or use the included helper: `python download_model.ps1`

**3. Python** (benchmark scripts only) — 3.11+ with `pip install requests`

---

### Start a Server

<table>
<tr><th>Windows</th><th>Linux / Mac</th></tr>
<tr>
<td>

```bat
REM Coding — 35B, 152K, vision
start_servers_speed.bat coding

REM Vision — 9B, 256K
start_servers_speed.bat vision

REM Quality — 27B, 64K
start_servers_speed.bat quality
```

</td>
<td>

```bash
./llama-bin/llama-server \
  -m ./models/unsloth-gguf/Qwen3.5-35B-A3B-Q3_K_S.gguf \
  --mmproj ./models/unsloth-gguf/mmproj-35B-F16.gguf \
  --host 127.0.0.1 --port 8002 \
  -c 155904 -ngl 99 \
  --flash-attn on \
  -ctk iq4_nl -ctv iq4_nl \
  --temp 0.6 --top-p 0.95 --top-k 20 \
  --chat-template-kwargs '{"enable_thinking":false}'
```

</td>
</tr>
</table>

### Verify It's Running

```bash
# Health check
curl http://127.0.0.1:8002/health

# First inference
curl -X POST http://127.0.0.1:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Write a Python fibonacci function"}],
    "max_tokens": 300
  }'
```

> **💡 First 2 requests will be slow (~12 t/s).** This is CUDA PTX→sm_120 JIT compilation (Blackwell one-time warmup). Full 124 t/s kicks in from request 3 onward. Don't benchmark until warm.

---

## ⚠️ The Discovery: 155,904 Token Cliff

> **This is the main reason this repo exists.** There is a hard, precise performance cliff in Qwen3.5-35B-A3B on 16GB GPUs that nobody had documented. Here's what it looks like:

```
  Context    Speed
  ───────    ─────────────────────────────────────────────────────
   64,000    109 t/s  ████████████████████████████████████████
   96,000    109 t/s  ████████████████████████████████████████
  128,000    119 t/s  ████████████████████████████████████████████
  148,000    114 t/s  ██████████████████████████████████████████
  155,904    124 t/s  ██████████████████████████████████████████████  ← SWEET SPOT
  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
  156,160      9 t/s  ███  ← 93% speed DROP at +256 tokens
  160,000     10 t/s  ████
  192,000      8 t/s  ███
  256,000      9 t/s  ███
```

### The Numbers

|   Context   | CUDA_Host Buffer |    Speed    |    Status    |
| :---------: | :--------------: | :---------: | :----------: |
|     64K     |      136 MB      |   109 t/s   |      ✅      |
|     96K     |      200 MB      |   109 t/s   |      ✅      |
|    128K     |      264 MB      |   119 t/s   |      ✅      |
|    148K     |      304 MB      |   114 t/s   |      ✅      |
| **155,904** |  **312.52 MB**   | **124 t/s** |  ✅ **MAX**  |
| **156,160** |  **313.02 MB**   |  **9 t/s**  | ❌ **CLIFF** |
|    160K     |      328 MB      |   10 t/s    |      ❌      |
|    192K     |      392 MB      |    8 t/s    |      ❌      |
|    256K     |      520 MB      |    9 t/s    |      ❌      |

### Why It Happens

Qwen3.5-35B-A3B uses a **hybrid recurrent architecture** — 30 Gated DeltaNet layers (linear recurrent) interleaved with 10 standard Gated Attention layers. llama.cpp allocates a `CUDA_Host compute buffer`: pinned host RAM for PCIe data transfers on every inference pass.

This buffer grows with context size. Between 155,904 and 156,160 tokens, it crosses an **internal alignment boundary** — jumping from 312.52 MB to 313.02 MB (a 0.5 MB step). Past this threshold, per-token PCIe transfer volume exceeds available bandwidth, and the model slows 10×.

```
312.52 MB  →  fast  ✅   (below alignment boundary)
313.02 MB  →  slow  ❌   (above alignment boundary)
```

**It is NOT a VRAM issue.** The model fits in VRAM at 192K and 256K too. VRAM is not the constraint — PCIe bandwidth for recurrent state transfers is.

**This is specific to hybrid recurrent architectures.** Pure transformer models (Qwen 9B, 27B) don't have this constraint — they don't use Gated DeltaNet layers and have no recurrent state PCIe transfers.

📄 **Full technical write-up with reproduce steps:** [`DISCOVERY.md`](DISCOVERY.md)

---

## 🎛️ All Three Server Configs

### 🖥️ Coding — 35B-A3B Q3_K_S (Port 8002)

```bash
-m Qwen3.5-35B-A3B-Q3_K_S.gguf
--mmproj mmproj-35B-F16.gguf
-c 155904 -ngl 99 --flash-attn on
-ctk iq4_nl -ctv iq4_nl
--chat-template-kwargs '{"enable_thinking":false}'
```

| Decision               | Reasoning                                                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Q3_K_S over Q4_K_M** | Q4_K_M = 20.5 GB → partial CPU offload → 3–4 t/s. Q3_K_S = 14.2 GB → all 41 layers on GPU → 124 t/s. Full GPU wins by 30×.                |
| **iq4_nl KV cache**    | MoE uses only 10/40 layers for attention. KV at 152K = only 856 MB. iq4_nl dequants faster on SM120 for small KV.                         |
| **thinking disabled**  | `enable_thinking:false` prevents 2–3× slowdown from chain-of-thought overhead. Use `true` only when you explicitly need reasoning traces. |
| **-c 155904**          | Exactly one step below the 313 MB PCIe alignment cliff. This is the verified sweet spot.                                                  |

---

### 👁️ Fast Vision — 9B Q4_K_XL (Port 8003)

```bash
-m Qwen2.5-VL-9B-Instruct-Q4_K_XL.gguf
--mmproj mmproj-Qwen2.5-VL-9B-F16.gguf
-c 262144 -ngl 99 --flash-attn on
-ctk q8_0 -ctv q8_0
--chat-template-kwargs '{"enable_thinking":false}'
```

Full 256K context (model native max). Uses **q8_0 KV** — not iq4_nl — because the 9B is a dense model with 33 attention layers. At RTX 5080's 960 GB/s bandwidth, raw read speed matters more than dequant cost, so the larger but faster q8_0 wins.

---

### 🎯 Quality — 27B Q3_K_S (Port 8004)

```bash
-m Qwen2.5-VL-27B-Instruct-Q3_K_S.gguf
--mmproj mmproj-Qwen2.5-VL-27B-F16.gguf
-c 65536 -ngl 99 --flash-attn on
-ctk iq4_nl -ctv iq4_nl
--chat-template-kwargs '{"enable_thinking":false}'
```

Dense model — **all 27B parameters active per token** (no MoE sparsity). Generates the highest quality output of the three but runs at 36 t/s because there's no expert routing shortcut. Use this when output quality is the priority over speed.

---

## 🧬 Why the 35B MoE Is Faster Than It Looks

The "35B" label is misleading. Here's the actual compute:

```
  Dense 27B:  27B params active per token  →  36 t/s  🐢
  Dense  9B:   9B params active per token  →  97 t/s  🐇
  MoE   35B:  ~3B params active per token  → 124 t/s  🚀
```

Qwen3.5-35B-A3B has **256 experts** total, but only **8 routed + 1 shared** activate per token. Effective compute ≈ 3B parameters per forward pass — comparable to a 3B dense model. This is why a nominally "35B" model at 14.2 GB outruns a dense 27B at 12.3 GB by 3.4×.

**Architecture breakdown:**

| Component             | Detail                                 |
| --------------------- | -------------------------------------- |
| Total layers          | 40 transformer layers                  |
| Recurrent layers      | 30 × Gated DeltaNet (linear recurrent) |
| Attention layers      | 10 × Gated Attention (standard)        |
| Experts per MoE block | 256 total · 8 routed + 1 shared active |
| Embedding dim         | n_embd = 2048                          |
| KV heads              | n_heads_kv = 4                         |
| KV footprint          | Only 10 layers need KV cache → tiny    |

The tiny KV footprint (only 10 attention layers vs 40 for a dense model) is also why iq4_nl KV cache works better here than q8_0 — there's simply less KV data to transfer, so dequant speed dominates over read bandwidth.

---

## 🗜️ Quantization Notes

### 35B-A3B MoE: Standard Quants Win

> **Don't use Unsloth Dynamic quants for the MoE model.** UD-Q4_K_XL uses MXFP4 mixed-precision layers that underperform on MoE architectures — confirmed by Unsloth's founder.

|   Quant    |    Size     | Perplexity |     vs Q8_0     | Notes                           |
| :--------: | :---------: | :--------: | :-------------: | ------------------------------- |
|    Q8_0    |   36.9 GB   |   6.534    |    baseline     | Too large for 16 GB             |
|   Q4_K_M   |   ~20 GB    |   6.669    |      +2.1%      | Too large for full GPU          |
| **Q3_K_S** | **14.2 GB** |  **~6.9**  |     **~5%**     | ✅ **Best for 16 GB** — all GPU |
| UD-Q4_K_XL |   ~19 GB    |   7.170    | **+9.7% worse** | ❌ Avoid on MoE                 |

Q3_K_S is the only quant that fits all 41 layers on a 16 GB GPU. The ~5% perplexity increase vs Q4_K_M is a much smaller penalty than the 30× speed loss from partial CPU offload (124 t/s vs 3–4 t/s).

### Dense Models (9B, 27B): Unsloth Dynamic is Fine

For dense models, UD quants perform normally. The MXFP4 issue is specific to MoE routing.

### KV Cache: Different Rules for MoE vs Dense

| Model type      | Best KV quant | Why                                                            |
| --------------- | :-----------: | -------------------------------------------------------------- |
| MoE (35B-A3B)   |   `iq4_nl`    | Only 10 attention layers → small KV → dequant speed wins       |
| Dense (9B, 27B) |    `q8_0`     | 33+ attention layers → large KV → read bandwidth wins on SM120 |

> **⚠️ Never mix K and V quant types.** Using different quants for `-ctk` and `-ctv` causes a significant slowdown. Always set both to the same value.

---

## 🖥️ Hardware Notes

### Compatible 16GB NVIDIA GPUs

The 35B-A3B Q3_K_S model (14.2 GB) fits on any NVIDIA card with **16 GB+ VRAM**. Speeds vary by generation:

| GPU                   | VRAM  |  Est. Speed  | Notes                                 |
| --------------------- | :---: | :----------: | ------------------------------------- |
| **RTX 5080**          | 16 GB | **124 t/s**  | ✅ Tested — SM120, GDDR7              |
| RTX 5070 Ti           | 16 GB | ~100-110 t/s | Same arch, slightly less bandwidth    |
| **RTX 4080**          | 16 GB |  ~85-95 t/s  | SM89, GDDR6X — should hit same cliff  |
| **RTX 4070 Ti Super** | 16 GB |  ~75-85 t/s  | Cut-down 4080, still fast             |
| **RTX 4060 Ti**       | 16 GB |  ~55-70 t/s  | Narrower bus, but works               |
| **RTX 3060 Ti**       | 16 GB |  ~45-60 t/s  | Older arch, still capable             |
| RTX 3090 / 4090       | 24 GB |    Higher    | Can run Q4_K_M full-GPU, more context |

> **The 155,904 context cliff is architecture-dependent, not GPU-specific.** All cards above should hit the same cliff at the same token count — it's about the `CUDA_Host buffer` alignment in llama.cpp, not VRAM or GPU model. If you test on a different card, please report your cliff point!

### Tested Hardware

| Component | Tested              | Notes                          |
| --------- | ------------------- | ------------------------------ |
| GPU       | RTX 5080 16GB GDDR7 | SM120 Blackwell                |
| CPU       | Ryzen 7 9800X3D     | 8-core, not Ryzen 9            |
| RAM       | 96 GB DDR5          | Overkill — 32 GB sufficient    |
| PCIe      | 5.0 x16             | 4.0 x16 should be fine         |
| OS        | Windows 11 Pro      | Linux untested but should work |

### GPU Architecture Notes

| Topic                   | Detail                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **SM120 (Blackwell)**   | Pre-built llama.cpp uses CUDA 12.4 which lacks sm_120. PTX→sm_120 JIT on first run = 2 slow requests, then full speed.          |
| **SM89 (Ada Lovelace)** | 40xx series has native support in CUDA 12.x — no JIT warmup needed                                                              |
| **Source build**        | `-DCMAKE_CUDA_ARCHITECTURES=120 -DGGML_CUDA_FA_ALL_QUANTS=ON` for native Blackwell kernels. Potential +10–20% gain.             |
| **PCIe bandwidth**      | Recurrent state transfers (MoE) are PCIe-bound. Gen 4 vs 5 shouldn't change cliff location, only affect post-cliff performance. |

### Minimum Requirements

| Component  |      Minimum       |        Recommended        |
| ---------- | :----------------: | :-----------------------: |
| GPU VRAM   |       16 GB        |       16 GB+ NVIDIA       |
| System RAM |       32 GB        |           64 GB           |
| PCIe       |      3.0 x16       |         4.0 x16+          |
| OS         | Windows 10 / Linux | Windows 11 / Ubuntu 22.04 |
| llama.cpp  |       b5000+       |          b8196+           |

---

## 📈 Benchmarking

```bash
# Quick benchmark — runs 5 requests, reports avg/peak/p95
python tests/simple_benchmark.py 8002

# Health check across all ports
python tests/health_check.py

# Side-by-side model comparison
python tests/compare_models.py

# Vision / multimodal test
python tests/vision_test.py
```

Full documented results: [`results/BENCHMARK_RESULTS.md`](results/BENCHMARK_RESULTS.md)

---

## 📁 Repo Structure

```
qwen35-rtx5080-guide/
│
├── 📄 README.md                  ← You are here
├── 📄 DISCOVERY.md               ← Full 155,904 cliff write-up
├── 📄 CHANGELOG.md               ← Version history
│
├── ⚙️  config/
│   ├── servers.yaml              ← All server configs — edit model paths here
│   └── config_loader.py         ← Python config loader
│
├── 🧪 tests/
│   ├── simple_benchmark.py      ← Main benchmark (avg/peak/p95)
│   ├── health_check.py          ← Server liveness check
│   ├── compare_models.py        ← Side-by-side comparison
│   ├── benchmark.py             ← Extended benchmark suite
│   └── vision_test.py           ← Multimodal / image test
│
├── 📊 results/
│   └── BENCHMARK_RESULTS.md     ← Full documented benchmark run
│
├── 📚 docs/
│   ├── KV_CACHE_ANALYSIS.md     ← KV quant deep-dive
│   ├── PERFORMANCE_MATRIX.md    ← Model comparison matrix
│   ├── 27B_OPTIMIZATION_ANALYSIS.md
│   └── RESEARCH_FINDINGS.md
│
├── 🚀 start_servers_speed.bat    ← Windows: launch coding/vision/quality
├── 🔧 start_servers_standard.bat ← Windows: standard profiles
├── 🛑 stop_servers.bat           ← Windows: kill all servers
├── 🐍 server_manager.py          ← Python server lifecycle manager
├── 🐍 qwen_api.py                ← Minimal API client helper
└── 📥 download_model.ps1         ← Model download script
```

---

## 🤝 Contributing / Reproducing

**Help expand GPU compatibility data!** Test on your 16GB card and report:

| Field                               | Example        |
| ----------------------------------- | -------------- |
| GPU + VRAM                          | RTX 4080 16GB  |
| llama.cpp version                   | b8500          |
| `CUDA_Host compute buffer` at cliff | 313.02 MB      |
| Context size at cliff               | 156,160        |
| Speed before / after                | 85 t/s → 8 t/s |

This helps confirm whether the 155,904 cliff is universal or shifts with GPU/architecture.

Other useful contributions:

- 🐧 **Linux results** — same hardware, different OS
- 🔨 **Native sm_89/sm_120 builds** — source compile benchmarks
- 🧪 **Other MoE models** — does the cliff exist on other hybrid-recurrent architectures?

---

## 🔗 Related

- 📖 [Reddit thread: Qwen3.5-35B-A3B on RTX 5080](https://www.reddit.com/r/LocalLLaMA/comments/1rei65v/) — starting point for these benchmarks
- 🤗 [Unsloth GGUF models](https://huggingface.co/unsloth) — Q3_K_S and vision models
- 🤗 [Bartowski GGUF models](https://huggingface.co/bartowski) — Q4_K_M (better PPL than UD-Q4_K_XL for MoE)
- 🛠️ [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases)
- 🤖 [Qwen on HuggingFace](https://huggingface.co/Qwen)

---

## 📜 License

**Scripts and configs:** MIT — use freely, no attribution required.

**Model weights:** Subject to [Qwen's license](https://huggingface.co/Qwen/Qwen2.5-72B/blob/main/LICENSE) (Apache 2.0 for base models).

---

<div align="center">

**⭐ Star if this saved you hours of benchmarking**

**🔄 Test on your GPU · Report your cliff · Help the community**

_Numbers are reproducible · PRs welcome · MIT license_

</div>
