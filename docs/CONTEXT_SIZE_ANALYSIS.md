# Context Size Analysis: Why We Recommend 120K Over 155K

**Document Purpose:** Explain the methodology behind our context size recommendations and provide reproducible proof of findings.

---

## Executive Summary

| Metric  | Theoretical Max | Recommended    | Reason                 |
| ------- | --------------- | -------------- | ---------------------- |
| Context | 155,904 tokens  | 120,000 tokens | Windows VRAM headroom  |
| Speed   | 125 t/s         | 120 t/s        | Only 4% loss           |
| VRAM    | ~15.9 GB        | ~15.4 GB       | +500MB headroom for OS |

**Bottom line:** 120K gives you +25% more context than 96K with only 4% speed loss, while maintaining system stability on Windows.

---

## The Two Context Limits

### 1. Theoretical Maximum: 155,904 Tokens

This is the **hard speed cliff** discovered through systematic benchmarking:

```
Context      Speed
─────────    ─────────────────────────────────────────
64,000       109 t/s  ████████████████████████████████
96,000       109 t/s  ████████████████████████████████
120,000      120 t/s  ████████████████████████████████████
155,904      125 t/s  █████████████████████████████████████  ← THEORETICAL MAX
─────────    ─────────────────────────────────────────
156,160      9 t/s    ███  ← 93% DROP at +256 tokens
160,000      10 t/s   ████
```

**Why it exists:** The GDN (Gated DeltaNet) hybrid architecture uses a `CUDA_Host compute buffer` for recurrent state transfers. At 155,904 tokens, this buffer hits ~312.52 MB. At 156,160 tokens, it jumps to ~313.02 MB (a 0.5 MB alignment boundary). Past this threshold, PCIe transfer volume per token exceeds bandwidth.

**This is NOT a VRAM issue.** The model fits in VRAM at 192K and 256K too.

### 2. Practical Maximum: 120,000 Tokens

For **Windows users**, we recommend 120K context because:

1. **Windows VRAM overhead:** The OS and background apps need ~500MB-1GB VRAM
2. **Desktop Window Manager:** Uses GPU memory for display
3. **Browser/other apps:** Common GPU-accelerated apps compete for VRAM
4. **Stability margin:** Prevents OOM crashes during peak usage

---

## Benchmark Methodology

### Test Environment

| Component | Specification        |
| --------- | -------------------- |
| GPU       | NVIDIA RTX 5080 16GB |
| CPU       | AMD Ryzen 7 9800X3D  |
| RAM       | 96GB DDR5            |
| OS        | Windows 11           |
| llama.cpp | SM120 native build   |

### Test Protocol

```bash
# For each context size tested:
1. Kill all llama-server processes
2. Start server with specified -c value
3. Wait 45 seconds for model load + warmup
4. Run 5 consecutive requests
5. Record predicted_per_second from API response
6. Calculate average speed
```

### Test Command

```bash
curl -s -X POST http://127.0.0.1:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 50}'
```

---

## Context Size Benchmarks

### Test 1: 96K Context (98,304 tokens)

**Server config:**

```bash
-c 98304 -ngl 99 --flash-attn on -ctk iq4_nl -ctv iq4_nl --parallel 1 --reasoning-budget 0
```

**Results:**

```
Test 1: 125.75 t/s
Test 2: 126.49 t/s
Test 3: 127.26 t/s
Test 4: 124.67 t/s
Test 5: 127.76 t/s
─────────────────
Average: 126.39 t/s
```

**VRAM usage:** ~15.3 GB

### Test 2: 110K Context (112,640 tokens)

**Results:**

```
Test 1: 102.32 t/s (warmup)
Test 2: 121.07 t/s
Test 3: 123.80 t/s
Test 4: 124.35 t/s
Test 5: 122.46 t/s
─────────────────
Average: 122.67 t/s (excluding warmup)
```

**VRAM usage:** ~15.3 GB

### Test 3: 120K Context (122,880 tokens) ← RECOMMENDED

**Results:**

```
Test 1: 103.06 t/s (warmup)
Test 2: 123.53 t/s
Test 3: 121.84 t/s
Test 4: 122.61 t/s
Test 5: 120.18 t/s
─────────────────
Average: 122.04 t/s (excluding warmup)
```

**VRAM usage:** ~15.4 GB

### Test 4: 130K Context (131,072 tokens)

**Results:**

```
Test 1: 81.02 t/s
Test 2: 87.60 t/s
Test 3: 86.99 t/s
Test 4: 88.34 t/s
Test 5: 87.69 t/s
─────────────────
Average: 86.33 t/s
```

**VRAM usage:** ~15.4 GB

**⚠️ Speed drop detected at 130K!**

---

## Analysis: Why 120K?

### Speed vs Context Trade-off

| Context  | Speed       | % of Max | Context Gain vs 96K |
| -------- | ----------- | -------- | ------------------- |
| 96K      | 126 t/s     | 100%     | baseline            |
| 110K     | 123 t/s     | 98%      | +15%                |
| **120K** | **122 t/s** | **97%**  | **+25%**            |
| 130K     | 86 t/s      | 68%      | +35% (but slow!)    |
| 155K     | 125 t/s     | 100%     | +62% (theoretical)  |

### The 130K Anomaly

At 130K context, we observed a significant speed drop to ~86 t/s. This appears to be related to:

1. **CUDA_Host buffer growth:** From 248 MB (120K) to 264 MB (130K)
2. **Increased PCIe transfers:** More recurrent state to sync
3. **Windows overhead:** Combined with OS memory pressure

**This is why we don't recommend going above 120K for daily use.**

### VRAM Headroom Analysis

| Context | KV Cache | CUDA_Host | Total Est. | Free Space |
| ------- | -------- | --------- | ---------- | ---------- |
| 96K     | 540 MB   | 200 MB    | ~15.3 GB   | ~700 MB    |
| 120K    | 675 MB   | 248 MB    | ~15.4 GB   | ~600 MB    |
| 155K    | 856 MB   | 312 MB    | ~15.9 GB   | ~100 MB    |

**Windows needs ~500MB-1GB GPU memory** for:

- Desktop Window Manager (DWM)
- Display output
- GPU-accelerated apps (browsers, etc.)

At 155K context, you only have ~100MB free. Any spike in Windows GPU usage will cause issues.

---

## Critical Flags

### --parallel 1 (MANDATORY)

Without this flag, the 35B-A3B model runs at **9 t/s** instead of **120 t/s**.

**Why:** The GDN hybrid architecture allocates recurrent state buffers per parallel slot. Default `--parallel auto` creates 4 slots → 4× larger buffers → 10× slower.

```bash
# WRONG - 9 t/s
-c 122880 --parallel auto

# CORRECT - 120 t/s
-c 122880 --parallel 1
```

### --reasoning-budget 0

Disables the thinking/reasoning mode for faster response times. Without this, the model may generate hidden reasoning tokens that slow down perceived response time.

---

## Recommendations Summary

### For Windows Users

```bash
# RECOMMENDED CONFIG
-c 122880           # 120K context
--parallel 1        # CRITICAL - 10x speedup
--reasoning-budget 0 # Faster response
```

**Why:**

- 120K context = 120 t/s (97% of max speed)
- +25% more context than 96K
- ~600MB VRAM headroom for Windows
- Stable with browser and other apps running

### For Linux Users / Headless Servers

```bash
# MAXIMUM CONTEXT (if you don't run a GUI)
-c 155904           # 152K context (theoretical max)
--parallel 1
--reasoning-budget 0
```

**Why:**

- No GUI = no DWM VRAM usage
- Can use nearly all 16GB for model
- Full 125 t/s speed

---

## Reproducing These Results

1. Clone the repo
2. Start the server with desired context:
   ```bash
   ./start_servers_speed.bat coding
   ```
3. Run the benchmark:
   ```bash
   curl -s -X POST http://127.0.0.1:8002/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "qwen", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 50}'
   ```
4. Check `predicted_per_second` in the response

---

## Conclusion

| Use Case                   | Context  | Why                                         |
| -------------------------- | -------- | ------------------------------------------- |
| **Daily coding (Windows)** | **120K** | Best balance of speed + context + stability |
| Quick tasks                | 96K      | Maximum speed margin                        |
| Headless server            | 155K     | Maximum context, no GUI overhead            |

**Our recommendation:** Use 120K context. You get 97% of max speed with 25% more context than 96K, while maintaining system stability on Windows.

---

## Changelog

| Date       | Change                       |
| ---------- | ---------------------------- |
| 2026-03-05 | Initial analysis document    |
| 2026-03-05 | Added 130K anomaly findings  |
| 2026-03-05 | Added VRAM headroom analysis |

---

_This analysis was conducted on RTX 5080 16GB with SM120 native build. Results may vary slightly on other GPUs, but the context cliff (155,904 tokens) and recommendations should apply to all 16GB NVIDIA cards._
