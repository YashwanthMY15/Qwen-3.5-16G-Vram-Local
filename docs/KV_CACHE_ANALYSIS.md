# iq4_nl KV Cache Analysis

## What is KV Cache?

KV (Key-Value) Cache stores attention states during inference. Larger context = larger cache.

---

## Cache Size Formula

```
KV Cache Size = 2 × n_layers × n_ctx × n_heads_kv × head_dim × bytes_per_value
```

---

## Cache Comparison by Model

### 35B-A3B (n_embd=2048, n_heads_kv=2, n_layers=40)

| Context | f16 Cache | iq4_nl Cache | Savings | Fits 16GB? |
|---------|-----------|--------------|---------|------------|
| 4K | 160 MB | 40 MB | 75% | ✅ |
| 16K | 640 MB | 160 MB | 75% | ✅ |
| 32K | 1,280 MB | 320 MB | 75% | ✅ |
| 64K | 2,560 MB | 640 MB | 75% | ⚠️ Tight |
| 128K | 5,120 MB | 1,280 MB | 75% | ❌ No |

**35B-A3B with iq4_nl**:
- Model: 14.2 GB (Q3_K_S)
- Cache (32K): 0.32 GB
- Compute buffer: ~0.5 GB
- **Total: ~15 GB** ✅ Fits!

### 27B (n_embd=5120, n_heads_kv=2, n_layers=64)

| Context | f16 Cache | iq4_nl Cache | Savings | Fits 16GB? |
|---------|-----------|--------------|---------|------------|
| 4K | 512 MB | 128 MB | 75% | ✅ |
| 16K | 2,048 MB | 512 MB | 75% | ✅ |
| 32K | 4,096 MB | 1,024 MB | 75% | ⚠️ Tight |
| 64K | 8,192 MB | 2,048 MB | 75% | ⚠️ With Q3_K_S |
| 128K | 16,384 MB | 4,096 MB | 75% | ❌ No |

**27B with iq4_nl**:
- Model: 12.3 GB (Q3_K_S)
- Cache (64K): 2.0 GB
- Compute buffer: ~0.5 GB
- **Total: ~14.8 GB** ✅ Fits with 65/65 layers!

### 9B (n_embd=4096, n_heads_kv=2, n_layers=36)

| Context | f16 Cache | iq4_nl Cache | Savings | Fits 16GB? |
|---------|-----------|--------------|---------|------------|
| 4K | 288 MB | 72 MB | 75% | ✅ |
| 16K | 1,152 MB | 288 MB | 75% | ✅ |
| 32K | 2,304 MB | 576 MB | 75% | ✅ |
| 64K | 4,608 MB | 1,152 MB | 75% | ✅ |
| 128K | 9,216 MB | 2,304 MB | 75% | ✅ Still fits! |

**9B with iq4_nl**:
- Model: 5.7 GB (Q4_K_XL)
- Cache (128K): 2.3 GB
- Compute buffer: ~0.5 GB
- **Total: ~8.5 GB** ✅ Plenty of room!

---

## Key Insights

### Why iq4_nl Matters

| Benefit | Description |
|---------|-------------|
| **75% smaller** | 4x more context for same VRAM |
| **Enables 64K+ context** | 27B can fit 64K with all layers on GPU |
| **No graph splits** | Everything stays in VRAM |
| **Minimal quality loss** | iq4_nl is "non-linear" optimized for attention |

### When to Use iq4_nl

| Model | Recommendation |
|-------|----------------|
| **35B-A3B** | Use iq4_nl for 32K+ context |
| **27B** | MUST use iq4_nl for 64K context |
| **9B** | Optional (already fits 128K with f16) |

### Requirements

```bash
# iq4_nl REQUIRES Flash Attention ON
--flash-attn on -ctk iq4_nl -ctv iq4_nl

# This does NOT work (cache falls back to f16)
--flash-attn auto -ctk iq4_nl -ctv iq4_nl
```

---

## Practical Recommendations

### 35B-A3B Configuration
```bash
# Best for 16GB VRAM
- Q3_K_S model (14.2 GB)
- iq4_nl cache
- 32K context
- 30/40 GPU layers
```

### 27B Configuration
```bash
# Best for quality vision
- Q3_K_S model (12.3 GB)
- iq4_nl cache
- 64K context
- 65/65 GPU layers (ALL!)
```

### 9B Configuration
```bash
# Fastest, most context
- Q4_K_XL model (5.7 GB)
- f16 cache (plenty of room)
- 128K context
- All GPU layers
```

---

## Cache Type Comparison

| Cache Type | Bits | Size vs f16 | Quality | Flash Attn |
|------------|------|-------------|---------|------------|
| f16 | 16 | 100% | Perfect | Optional |
| q8_0 | 8 | 50% | Excellent | Optional |
| **iq4_nl** | 4 | **25%** | Very Good | **Required** |
| q4_0 | 4 | 25% | Good | Optional |

**iq4_nl** = "4-bit non-linear" - optimized for attention patterns

---

*Generated: March 4, 2026*
