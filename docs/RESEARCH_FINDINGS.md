# Research Findings - RTX 5080 SM120

## Date: March 4, 2026

---

## Executive Summary

| Topic | Verdict | Action |
|-------|---------|--------|
| **RTX-STone** | ❌ NOT RECOMMENDED | Do not install |
| **FlashMLA** | ⚠️ DEEPSEEK ONLY | Only for DeepSeek models |
| **PyTorch SM120** | ❌ NOT NEEDED | llama.cpp doesn't use PyTorch |
| **heretic-v1** | ✅ WORKING | Optional for uncensored tasks |

---

## 1. RTX-STone Analysis

### What It Claims
- PyTorch 2.10 with native SM 120 support
- 20-30% faster than official PyTorch
- Triton compiler for custom CUDA kernels
- Flash Attention 2 support

### Security Assessment

| Issue | Severity | Details |
|-------|----------|---------|
| **No GitHub repo** | 🔴 Critical | URL returns 404 |
| **Python incompatibility** | 🔴 Blocker | Requires 3.10-3.11, user has 3.12 |
| **Package size** | 🟡 Suspicious | 8.3 GB (official PyTorch ~2GB) |
| **Unknown maintainer** | 🟡 Risk | "diverstone" - no track record |
| **No source code** | 🔴 Critical | Cannot audit |

### Why It's NOT Needed

Official PyTorch nightly already supports SM120:

```powershell
# Official, safe, works with Python 3.12
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

### Verdict: ❌ DO NOT INSTALL

---

## 2. FlashMLA Analysis

### What It Is
- Optimized attention kernels for DeepSeek-V3
- Created by DeepSeek team
- Ported to SM120 by SuperLuminal (community developer)

### GitHub Repository
- **Official**: github.com/deepseek-ai/FlashMLA
- **SM120 Fork**: github.com/IISuperluminaLII/FlashMLA_Windows_Linux_sm120
- **Status**: ✅ Open source, auditable

### Performance Claims

| Metric | Without FlashMLA | With FlashMLA | Speedup |
|--------|------------------|---------------|---------|
| Decode latency | ~120ms | ~3.7ms | **32x** |
| Prefill (1K tokens) | ~500ms | ~50ms | **10x** |

### Compatibility

| Model | FlashMLA Compatible | Reason |
|-------|---------------------|--------|
| DeepSeek-V3 | ✅ Yes | Uses MLA attention |
| Qwen3.5 | ❌ No | Uses standard MHA |
| Llama | ❌ No | Uses standard MHA |
| Mistral | ❌ No | Uses standard MHA |

### SM120 Limitations

| Feature | SM90 (H100) | SM100 (B200) | SM120 (RTX 50xx) |
|---------|-------------|--------------|------------------|
| Dense MLA | ✅ | ✅ | ✅ |
| Sparse MLA | ✅ FP8 | ✅ FP8 | ❌ |
| GMMA | ✅ | ✅ | ❌ |
| Shared Memory | Full | 227KB | **99KB** |

### Verdict: ⚠️ ONLY FOR DEEPSEEK

**For Qwen3.5**: No benefit (different attention architecture)

---

## 3. PyTorch SM120 Support

### Official Status

PyTorch team (ptrblck) confirmed on forums:
> "pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128 works now"

### Working Configurations (Confirmed by Users)

| GPU | Python | PyTorch | Status |
|-----|--------|---------|--------|
| RTX 5060 Ti | 3.10.x | nightly cu128 | ✅ Working |
| RTX 5070 Ti | 3.12.10 | 2.11.0.dev+cu128 | ✅ Working |
| RTX 5080 | 3.10+ | nightly cu128 | ✅ Working |

### Verification

```python
import torch
print(torch.cuda.get_arch_list())
# Should include 'sm_120'
```

### When You Need PyTorch

| Use Case | Needs PyTorch? |
|----------|----------------|
| llama.cpp inference | ❌ No |
| Training/fine-tuning | ✅ Yes |
| Stable Diffusion | ✅ Yes |
| ComfyUI | ✅ Yes |
| HuggingFace Transformers | ✅ Yes |

### Verdict: ❌ NOT NEEDED FOR LLAMA.CPP

**llama.cpp is self-contained** - it doesn't use PyTorch at all.

---

## 4. heretic-v1 Model

### What It Is
- Decensored version of Qwen3.5-35B-A3B
- Created using MPOA (Magnitude-Preserving Orthogonal Ablation)

### Performance

| Metric | Original | heretic-v1 |
|--------|----------|------------|
| Refusals | 92/100 | **11/100** |
| KL Divergence | 0 | 0.0366 |
| Quality | Baseline | Minimal loss |

### Files

| File | Size | Purpose |
|------|------|---------|
| Qwen3.5-35B-A3B-heretic-Q4_K_M.gguf | 21.2 GB | Model |
| mmproj-heretic-BF16.gguf | 903 MB | Vision projector |

### Speed on RTX 5080 16GB

- Generation: ~7 t/s (limited by VRAM)
- Vision: ✅ Working
- Port: 8006

### Verdict: ✅ OPTIONAL

Good for uncensored tasks, but slow due to VRAM constraints.

---

## 5. SM120 Hardware Limitations

### Consumer RTX 50xx vs Datacenter

| Feature | RTX 5080 (SM120) | B200 (SM100) |
|---------|------------------|--------------|
| Shared Memory | 99 KB | 227 KB |
| GMMA Instructions | ❌ No | ✅ Yes |
| TCGEN05 | ❌ No | ✅ Yes |
| TMEM | ❌ No | ✅ Yes |
| TMA | ❌ No | ✅ Yes |
| Sparse Attention | ❌ No | ✅ Yes |

### Impact on Performance

- Smaller tiles required (16x16 vs 64x128)
- More kernel passes needed
- ~50% of datacenter performance

---

## 6. Final Recommendations

### For Qwen3.5 Inference (Your Use Case)

| Component | Recommendation |
|-----------|----------------|
| **llama.cpp** | ✅ Already optimal |
| **RTX-STone** | ❌ Don't install |
| **FlashMLA** | ❌ Not compatible |
| **PyTorch SM120** | ❌ Not needed |
| **heretic-v1** | ⚠️ Optional (uncensored) |

### If You Want to Train/Fine-tune

```powershell
# Install official PyTorch with SM120 support
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

### If You Want to Run DeepSeek

```powershell
# Install FlashMLA
git clone https://github.com/IISuperluminaLII/FlashMLA_Windows_Linux_sm120.git
cd FlashMLA_Windows_Linux_sm120
set FLASH_MLA_ARCH=sm120
pip install -v .
```

---

## Summary Table

| Tool | Purpose | Safe? | Needed? | Action |
|------|---------|-------|---------|--------|
| **RTX-STone** | PyTorch SM120 | ❌ No | ❌ No | Skip |
| **FlashMLA** | DeepSeek attention | ✅ Yes | ❌ No | Skip |
| **PyTorch cu128** | Training/SD | ✅ Yes | ❌ No | Skip |
| **heretic-v1** | Uncensored | ✅ Yes | ⚠️ Optional | Optional |

---

*Research completed: March 4, 2026*
