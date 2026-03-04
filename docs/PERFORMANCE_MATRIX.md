# Performance Comparison Matrix - RTX 5080 16GB

## Test Date: March 4, 2026

---

## Model Performance Summary

| Model | Quant | Size | Vision | GPU Layers | Graph Splits | Prompt t/s | Gen t/s | Context |
|-------|-------|------|--------|------------|--------------|------------|---------|---------|
| **35B-A3B** | Q4_K_M | 20.5 GB | ❌ | 40/40 | 0 | 65-71 | **~70** | 64K |
| **35B-A3B** | Q3_K_S | 14.2 GB | ✅ | 30/40 | 40 | 135 | 35 | 32K |
| **heretic-v1** | Q4_K_M | 21.2 GB | ✅ | 25/41 | 2 | 66 | **7** ⚠️ | 32K |
| **27B** | Q3_K_S | 12.3 GB | ✅ | 65/65 | 0 | 413 | **37** | 64K |
| **27B** | Q4_K_M | 16.7 GB | ✅ | 53/65 | 12 | 191 | 12 | 16K |
| **9B** | Q4_K_XL | 5.7 GB | ✅ | All | 0 | 1568 | **112** | 128K |

### heretic-v1 Notes
- **Decensored**: 11/100 refusals vs 92/100 original
- **Quality**: KL divergence 0.0366 (minimal loss)
- **Speed**: Limited by VRAM (21.2 GB > 16 GB)
- **Best for**: Uncensored tasks (accept slower speed)

---

## Key Findings

### 35B-A3B Architecture Advantage
- **MoE (Mixture of Experts)**: 35B total, only 3B active per token
- **Why it's fast**: Only 8 routed + 1 shared expert activated
- **n_embd**: 2048 (smaller than 27B's 5120)
- **Layers**: 40 (vs 64 for 27B)

### Graph Split Impact
- **0 splits**: Full GPU speed (optimal)
- **40 splits**: ~50% speed loss due to CPU↔GPU transfers
- **Solution**: Fit model entirely in VRAM or accept slower speed

### Vision Compatibility
| Model | n_embd | mmproj | projection_dim | Match |
|-------|--------|--------|----------------|-------|
| 35B-A3B | 2048 | mmproj-35B-F16.gguf | 2048 | ✅ |
| 27B | 5120 | mmproj-27B-F16.gguf | 5120 | ✅ |
| 9B | 4096 | mmproj-F16.gguf | 4096 | ✅ |

---

## Recommended Configurations

### Option A: Maximum Quality (Recommended)
```
Port 8002: 35B-A3B Q4_K_M (Coding, no vision)
           - 64K context, ~70 t/s
           
Port 8003: 9B Q4_K_XL (Fast Vision)
           - 128K context, 112 t/s
           
Port 8005: 27B Q3_K_S (Quality Vision)
           - 64K context, 37 t/s, ALL 65 GPU layers
```

### Option B: Simpler Setup (2 Servers)
```
Port 8002: 35B-A3B Q4_K_M (Coding, no vision)
           - 64K context, ~70 t/s
           
Port 8003: 27B Q3_K_S + Vision (All multimodal tasks)
           - 64K context, 37 t/s
```

### Option C: Single Server (Switch as needed)
```
Use 35B-A3B Q4_K_M for coding (fastest)
Use 27B Q3_K_S + Vision when vision needed
```

---

## Use Case Recommendations

| Task | Best Model | Reason |
|------|------------|--------|
| **Coding** | 35B-A3B Q4_K_M | Best knowledge, 70 t/s, no vision needed |
| **Fast Vision** | 9B Q4_K_XL | 112 t/s, 128K context |
| **Quality Vision** | 27B Q3_K_S | All GPU layers, 37 t/s, good quality |
| **Long Context** | 9B Q4_K_XL | 128K context support |
| **Quality + Vision** | 35B-A3B Q3_K_S | Most knowledge, vision works, 35 t/s |
| **Uncensored** | heretic-v1 Q4_K_M | Decensored (11% vs 92% refusals), 7 t/s ⚠️ |

---

## KV Cache Optimization

### Best Practice
```bash
--flash-attn on -ctk iq4_nl -ctv iq4_nl
```

### Cache Size Comparison (64K context)
| Cache Type | Size | Quality | Flash Attn |
|------------|------|---------|------------|
| f16 | 2048 MB | Perfect | Optional |
| q8_0 | 1024 MB | Excellent | Optional |
| **iq4_nl** | **512 MB** | Very Good | **Required** |

---

## Unsloth Recommended Settings

### For Coding (Non-Thinking Mode)
```bash
--temp 0.6 --top-p 0.95 --top-k 20
--presence-penalty 0.0
--chat-template-kwargs "{\"enable_thinking\":false}"
```

### For General Tasks (Non-Thinking Mode)
```bash
--temp 0.7 --top-p 0.8 --top-k 20
--presence-penalty 1.5
--chat-template-kwargs "{\"enable_thinking\":false}"
```

---

## RTX-STone Potential Improvement

Installing RTX-STone could provide **40-60% performance boost**:

| Model | Current | With RTX-STone (est.) |
|-------|---------|----------------------|
| 35B-A3B | 70 t/s | 98-112 t/s |
| 27B | 37 t/s | 52-59 t/s |
| 9B | 112 t/s | 157-179 t/s |

**Install**: `pip install rtx-stone[all]`

---

## Files Structure

```
qwen-llm/
├── models/unsloth-gguf/
│   ├── Qwen3.5-35B-A3B-Q4_K_M.gguf       # 20.5GB - Coding (no vision)
│   ├── Qwen3.5-35B-A3B-Q3_K_S.gguf       # 14.2GB - Vision capable
│   ├── Qwen3.5-35B-A3B-heretic-Q4_K_M.gguf # 21.2GB - Decensored
│   ├── Qwen3.5-27B-Q3_K_S.gguf           # 12.3GB - Quality Vision
│   ├── Qwen3.5-9B-UD-Q4_K_XL.gguf        # 5.7GB - Fast Vision
│   ├── mmproj-35B-F16.gguf               # 858MB - 35B vision
│   ├── mmproj-heretic-BF16.gguf          # 903MB - heretic vision
│   ├── mmproj-27B-F16.gguf               # 928MB - 27B vision
│   └── mmproj-F16.gguf                   # 918MB - 9B vision
├── start_35b.bat                         # Coding server (no vision)
├── start_27b_vision.bat                  # Quality vision server
├── start_heretic_vision.bat              # Decensored vision server
├── start_all_servers.bat                 # Launch all servers
├── stop_all_servers.bat                  # Stop all
├── test_35b_vision.py                    # Vision API test
└── docs/
    ├── PERFORMANCE_MATRIX.md             # This file
    ├── KV_CACHE_ANALYSIS.md              # iq4_nl cache analysis
    └── HERETIC_COMPARISON.md             # heretic vs original
```

---

*Generated: March 4, 2026*
*Hardware: RTX 5080 16GB, Ryzen 9 9800X3D, 96GB RAM*
