# 27B Vision Optimization Study: Final Results

## Executive Summary

**MAJOR BREAKTHROUGH**: Combining Q3_K_S model + iq4_nl KV cache + Flash Attention unlocks:

| Metric | Original (Q4_K_M) | Optimized (Q3_K_S + iq4_nl) | Improvement |
|--------|-------------------|----------------------------|-------------|
| **GPU Layers** | 53/65 | **65/65** | +12 layers on GPU |
| **Context** | 16K | **64K** | 4x improvement |
| **Prompt Speed** | 191 t/s | **413 t/s** | **2.2x faster** |
| **Gen Speed** | 12 t/s | **37 t/s** | **3x faster** |

---

## Key Discoveries

### 1. Flash Attention + iq4_nl Works When Forced ON

The previous error was because Flash Attention was set to "auto" and didn't activate. By forcing it ON with `--flash-attn on`, iq4_nl cache works perfectly!

```bash
--flash-attn on -ctk iq4_nl -ctv iq4_nl
```

### 2. Q3_K_S Model Fits Entirely on GPU

| Model | Size | GPU Layers | Quality |
|-------|------|------------|---------|
| Q4_K_M | 15.6 GB | 53-54/65 | Good |
| Q3_K_S | 12.3 GB | **65/65** | Acceptable |

The 3.3 GB savings allows ALL layers on GPU with room for larger context.

### 3. iq4_nl Cache is 75% Smaller Than f16

| Cache Type | 64K Context Size | Quality |
|------------|-----------------|---------|
| f16 | 2048 MB | Perfect |
| q8_0 | 1024 MB | Excellent |
| **iq4_nl** | **512 MB** | Very Good |

---

## Performance Comparison

### Q4_K_M (Original)

| Context | KV Type | GPU Layers | Prompt t/s | Gen t/s |
|---------|---------|------------|------------|---------|
| 4K | f16 | 54/65 | 159 | 11.2 |
| 16K | q8_0 | 53/65 | 191 | 12.3 |
| 32K | q8_0 | 52/65 | 183 | 11.6 |
| 64K | q8_0 | 51/65 | 149 | 9.8 |

### Q3_K_S + iq4_nl + Flash Attention (Optimized)

| Context | KV Type | GPU Layers | Prompt t/s | Gen t/s |
|---------|---------|------------|------------|---------|
| 32K | iq4_nl | **65/65** | 422 | 38.5 |
| **64K** | iq4_nl | **65/65** | **413** | **37.4** |
| 128K | iq4_nl | 62/65 | 301 | 26.2 |

---

## Quality Tradeoffs

### Q3_K_S vs Q4_K_M

Q3_K_S uses 3.94 BPW (bits per weight) vs 4.98 BPW for Q4_K_M:

| Aspect | Impact |
|--------|--------|
| Simple tasks | Negligible difference |
| Complex reasoning | Slight degradation |
| Vision tasks | Minimal impact (images are robust) |
| Code generation | Acceptable for most uses |

### iq4_nl vs f16 Cache

| Aspect | Impact |
|--------|--------|
| Short context (<16K) | No noticeable difference |
| Long context (>64K) | Slightly more "drift" |
| Factual accuracy | Well preserved |

---

## Optimal Configurations

### Maximum Speed (64K context)
```bash
llama-server.exe \
    -m Qwen3.5-27B-Q3_K_S.gguf \
    --mmproj mmproj-27B-F16.gguf \
    -c 65536 \
    --flash-attn on \
    -ctk iq4_nl -ctv iq4_nl \
    -ngl 99
```
**Result**: 65/65 GPU, 413 t/s prompt, 37 t/s gen

### Maximum Context (128K)
```bash
llama-server.exe \
    -m Qwen3.5-27B-Q3_K_S.gguf \
    --mmproj mmproj-27B-F16.gguf \
    -c 131072 \
    --flash-attn on \
    -ctk iq4_nl -ctv iq4_nl \
    -ngl 99
```
**Result**: 62/65 GPU, 301 t/s prompt, 26 t/s gen

### Maximum Quality (Q4_K_M, 16K)
```bash
llama-server.exe \
    -m Qwen3.5-27B-Q4_K_M.gguf \
    --mmproj mmproj-27B-F16.gguf \
    -c 16384 \
    -ctk q8_0 -ctv q8_0 \
    -ngl 99
```
**Result**: 53/65 GPU, 191 t/s prompt, 12 t/s gen (best quality)

---

## Final Recommendations

### Use Q3_K_S + iq4_nl When:
- Need **maximum speed** (37 t/s vs 12 t/s)
- Need **longer context** (64K vs 16K)
- Working with **vision tasks** (images tolerate quantization)
- **All GPU layers** important for latency

### Use Q4_K_M + q8_0 When:
- Need **maximum quality** for complex reasoning
- Working with **code generation** where precision matters
- Context fits in **16K**
- Can tolerate **slower responses**

---

## Updated Server Comparison

| Server | Model | Context | Speed | Quality | Best For |
|--------|-------|---------|-------|---------|----------|
| 8002 | 35B-A3B | 64K | 70 t/s | Best | Coding |
| 8003 | 9B | 128K | 112 t/s | Good | Fast vision |
| **8004** | **27B Q3_K_S** | **64K** | **37 t/s** | **Better** | **Quality vision** |

---

## Files to Update

1. `start_27b_vision.bat` - Add optimized configuration
2. `PROGRESS_CHECKLIST.md` - Update performance numbers
3. `README.md` - Update server comparison

---

*Study Date: March 4, 2026*
*Hardware: RTX 5080 16GB*
