# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-03-04

### Optimized — Final Config Locked

#### Repo Cleanup

- Root reduced from 80 → 27 entries
- Archived 10 old benchmark scripts → `archive/benchmarks/`
- Archived 17 old startup/setup scripts → `archive/scripts/`
- Archived 5 old test scripts → `archive/tests/`
- Archived 12 outdated docs → `archive/docs/`
- All root-level `*.log` files moved → `logs/`
- All JSON results moved → `results/`
- Deleted junk files (`nul`, fake zip)

#### Benchmark Regression Fixed

- **Root cause**: `--flash-attn auto` + 128K ctx + f16 KV + missing thinking disable
- **Fix**: `--flash-attn on` + tuned context + quantized KV + `enable_thinking: false`
- **Recovery**: 94 t/s → 109+ t/s

#### Context Pushed to Maximum (256K)

- Model native max: 262,144 tokens — now fully utilized
- All 33 layers remain on GPU at 256K
- Total VRAM: ~10.6 GB (5.4 GB headroom)

#### KV Quantization Study — q8_0 Crowned Winner

Benchmarked all three viable types at 256K context (8-prompt, with warmup):

| KV Type  | KV Size     | Avg Gen      | Peak Gen      | Min Gen      | Verdict       |
| -------- | ----------- | ------------ | ------------- | ------------ | ------------- |
| iq4_nl   | 2304 MB     | 89.9 t/s     | 98.0 t/s      | 84.6 t/s     | ❌ Slowest    |
| q4_0     | 2304 MB     | 92.3 t/s     | 95.6 t/s      | 90.1 t/s     | ⚠️ Mid        |
| **q8_0** | **4352 MB** | **97.5 t/s** | **112.2 t/s** | **90.0 t/s** | ✅ **Winner** |

**Key insight**: On RTX 5080 SM120, VRAM bandwidth is fast enough that 8-bit reads
beat the dequant compute overhead of 4-bit types. q8_0 is both fastest AND
highest quality (~99.9% vs f16) at 256K context.

#### KV Quality Guide (documented)

| Type   | Quality vs f16 | Notes                                           |
| ------ | -------------- | ----------------------------------------------- |
| f16    | 100%           | Doesn't fit at 256K (8704 MB needed)            |
| q8_0   | ~99.9%         | Imperceptible loss, USE THIS                    |
| iq4_nl | ~98-99%        | Better than q4_0, but SM120 dequant overhead    |
| q4_0   | ~97-98%        | Avoid — compounds at long ctx, no speed benefit |

### Final Locked Config

```
-c 262144 --flash-attn on -ctk q8_0 -ctv q8_0
--chat-template-kwargs '{"enable_thinking":false}'
```

Saved to: `start_servers_speed.bat`, `config/servers.yaml`

---

## [1.2.0] - 2026-03-04

### Added

#### heretic-v1 Model (Decensored 35B-A3B)

- **Qwen3.5-35B-A3B-heretic-Q4_K_M.gguf** (21.2GB) - Decensored via MPOA
- **mmproj-heretic-BF16.gguf** (903MB) - Vision projector for heretic
- **Refusal rate**: 11/100 vs 92/100 original
- **KL divergence**: 0.0366 (minimal quality loss)
- Vision working ✅
- Speed: ~7 t/s (limited by VRAM - 21.2GB > 16GB)
- `start_heretic_vision.bat` startup script (port 8006)

#### Documentation

- `docs/KV_CACHE_ANALYSIS.md` - Detailed iq4_nl cache analysis
- `docs/HERETIC_COMPARISON.md` - heretic vs original comparison

### Research Findings

#### RTX-STone Analysis: ❌ NOT RECOMMENDED

- No GitHub repository (404 error)
- Requires Python 3.10-3.11 (incompatible with 3.12)
- 8GB package size (suspicious)
- Official PyTorch nightly already supports SM120
- **Verdict**: Security risk, avoid

#### FlashMLA Analysis: ⚠️ DEEPSEEK ONLY

- 32x speedup for DeepSeek-V3 models
- NOT compatible with Qwen (different attention: MLA vs MHA)
- Open source and legitimate
- **Verdict**: Only install if using DeepSeek

#### PyTorch SM120 Analysis: ❌ NOT NEEDED

- llama.cpp is self-contained (doesn't use PyTorch)
- Official PyTorch nightly supports SM120 via cu128
- Only needed for: training, Stable Diffusion, ComfyUI
- **Verdict**: Not needed for inference

### Changed

- Updated PERFORMANCE_MATRIX.md with heretic-v1 data
- Updated PROGRESS_CHECKLIST.md with all findings

---

## [1.1.0] - 2026-03-04

### Added

#### 35B-A3B Vision Support 🎉

- **MAJOR DISCOVERY**: 35B-A3B + Vision WORKS!
- mmproj-35B-F16.gguf has projection_dim=2048 matching n_embd=2048
- Downloaded Qwen3.5-35B-A3B-Q3_K_S.gguf (14.2GB)
- Vision tested and working
- `start_35b_a3b_vision_optimized.bat` startup script
- `test_35b_vision.py` test script

#### KV Cache Optimization

- **iq4_nl cache**: 75% smaller than f16
- Requires `--flash-attn on` (not auto!)
- Enables 64K context with all GPU layers on 27B

#### Documentation

- `docs/COMPLETE_ANALYSIS.md` - Full analysis of all discoveries
- `docs/PERFORMANCE_MATRIX.md` - Performance comparison matrix

### Performance Results

| Model   | Quant   | Vision | Gen t/s | Context | GPU Layers |
| ------- | ------- | ------ | ------- | ------- | ---------- |
| 35B-A3B | Q4_K_M  | ❌     | 70      | 64K     | 40/40      |
| 35B-A3B | Q3_K_S  | ✅     | 35      | 32K     | 30/40      |
| 27B     | Q3_K_S  | ✅     | 37      | 64K     | 65/65      |
| 9B      | Q4_K_XL | ✅     | 112     | 128K    | All        |

### Technical Discoveries

1. **Flash Attention**: Must be FORCED ON for iq4_nl cache
2. **Graph Splits**: Cause 50%+ speed loss
3. **MoE Efficiency**: 35B-A3B uses only 3B active params
4. **RTX-STone**: Driver limits SM120 to SM89 performance

---

## [1.0.0] - 2026-03-04

### Added - Initial Release

#### Core Infrastructure

- llama.cpp b8196 with CUDA support (Windows native)
- Dual-server architecture:
  - Port 8002: Qwen3.5-35B-A3B (64K context) - Coding focused
  - Port 8003: Qwen3.5-9B (128K context + Vision) - Multimodal

#### Models

- Qwen3.5-35B-A3B-Q4_K_M.gguf (20GB) - MoE architecture, 3B active params
- Qwen3.5-27B-Q4_K_M.gguf (16GB) - Dense model
- Qwen3.5-9B-UD-Q4_K_XL.gguf (5.7GB) - With vision support
- mmproj-F16.gguf (876MB) - Vision projector (only works with 9B)

#### Scripts

- `start_servers.bat` - Unified dual-server startup with best practices
- `start_35b.bat` - 35B server with mode selection
- `start_9b.bat` - 9B server with mode selection
- `stop_servers.bat` - Stop all servers
- `test_vision.py` - Vision API testing script
- `qwen_api.py` - Python API helper with official presets

#### Documentation

- `PROGRESS_CHECKLIST.md` - Project state tracking
- `QUICK_START.md` - Quick reference guide
- `FINAL_OPTIMIZATION_REPORT.md` - Complete optimization documentation
- `COMPARISON_VLLM_REDDIT.md` - vLLM analysis
- `COMPARISON_OLLAMA_VANILLA.md` - Ollama comparison

### Performance Achieved

| Server  | Prompt Speed | Gen Speed | Context |
| ------- | ------------ | --------- | ------- |
| 35B-A3B | 65-71 t/s    | ~70 t/s   | 64K     |
| 9B      | 1568 t/s     | 112 t/s   | 128K    |

### Key Discoveries

1. **vLLM Limitations**: Requires Linux/WSL, doesn't work native Windows
2. **llama.cpp Speed**: 30-50x faster than Ollama vanilla
3. **Vision Limitation**: 35B-A3B incompatible with mmproj (n_embd mismatch)
4. **Thinking Mode**: Qwen3.5 has thinking mode causing 2-3x slowdown
5. **Context Scaling**: 9B can do 128K, 35B limited to 64K on 16GB VRAM

### Technical Specifications

- GPU: NVIDIA RTX 5080 (16GB VRAM, SM120)
- CPU: AMD Ryzen 9 9800X3D
- RAM: 96GB
- Platform: Windows 11

---

## Version History Summary

| Version | Date       | Key Changes                                                        |
| ------- | ---------- | ------------------------------------------------------------------ |
| 1.2.0   | 2026-03-04 | heretic-v1, KV cache analysis, RTX-STone/FlashMLA/PyTorch research |
| 1.1.0   | 2026-03-04 | 35B-A3B vision, iq4_nl cache, performance matrix                   |
| 1.0.0   | 2026-03-04 | Initial release with dual-server setup                             |
| 0.5.0   | 2026-03-04 | Vision API working on 9B                                           |
| 0.4.0   | 2026-03-04 | Migrated from Ollama to llama.cpp                                  |
| 0.3.0   | 2026-03-03 | Abandoned SGLang (VRAM limits)                                     |
| 0.2.0   | 2026-03-03 | Abandoned vLLM (Windows incompatibility)                           |
| 0.1.0   | 2026-03-03 | Project started                                                    |
