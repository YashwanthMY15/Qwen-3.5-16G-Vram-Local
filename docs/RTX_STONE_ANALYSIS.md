# RTX-STone / kentstone84 Analysis

## Date: March 4, 2026

---

## Summary

| Aspect | Assessment |
|--------|------------|
| **Project** | github.com/kentstone84/PyTorch-2.10.0a0 |
| **PyPI Package** | `pip install rtx-stone[all]` |
| **Legitimate?** | ⚠️ Probably, but controversial |
| **Verified?** | ❌ No independent verification |
| **Needed for llama.cpp?** | ❌ No |
| **Recommendation** | ❌ DO NOT INSTALL |

---

## What It Claims

### 1. NVIDIA Driver Gatekeeping

| Claim | Details |
|-------|---------|
| Problem | Driver "actively rejects" sm_120 kernels |
| Mechanism | Silent fallback to sm_89 (Ada) |
| Impact | 30-40% performance loss |
| Solution | Patch 3 hex bytes in driver |
| Proof | 3D Mark: 29,604 → 47,616 (+60.8%) |

### 2. Technical Approach

```
1. Reverse engineer NVIDIA driver with Ghidra
2. Find 3 sm_120 rejection functions
3. Patch 3 hex bytes (fail → pass)
4. Replace system driver with patched version
```

### 3. What's Included

| Component | Version |
|-----------|---------|
| PyTorch | 2.10.0a0 |
| Triton | 3.3+ |
| Flash Attention 2 | Included |
| Package Size | 8.3 GB |
| Python Support | 3.10-3.11 only |

---

## Red Flags

### 1. Author Behavior

Aggressive language in README:
- "To the losers that claim that I am a fraud"
- "Most of you losers can't run a video game"
- "shut the hell up and say thank you"
- "get the fuk out of my repo"

**Analysis**: Defensive behavior suggests community skepticism exists.

### 2. Technical Concerns

| Issue | Severity |
|-------|----------|
| Driver patching required | 🔴 High risk |
| Voids GPU warranty | 🔴 Permanent |
| Driver signature bypass | 🔴 Security risk |
| 8.3 GB package | 🟡 Suspicious |
| No third-party verification | 🟡 Unproven |
| Python 3.10-3.11 only | 🔴 Blocks 3.12 |

### 3. Conflict with Official PyTorch

| Source | Position |
|--------|----------|
| **PyTorch team (ptrblck)** | "pip install --pre torch --index-url cu128 works now" |
| **RTX-STone** | "Driver blocks sm_120, need patches" |

**Most likely**: PyTorch compiles sm_120 correctly, but driver may not be fully optimized. Patched driver may help, but 60% claim is unverified.

---

## Positive Signs

| Aspect | Status |
|--------|--------|
| Open source | ✅ GitHub public |
| Source code | ✅ Available |
| Documentation | ✅ Comprehensive |
| Active development | ✅ 56 commits |
| PyPI package | ✅ Published |
| Technical depth | ✅ Shows real work |

---

## For llama.cpp Users

### Why RTX-STone Doesn't Help

| Component | Uses PyTorch? | RTX-STone Helps? |
|-----------|---------------|------------------|
| llama.cpp | ❌ No | ❌ No |
| Qwen3.5 inference | ❌ No | ❌ No |
| Vision (mmproj) | ❌ No | ❌ No |
| Training/fine-tuning | ✅ Yes | ⚠️ Maybe |

**llama.cpp is self-contained** - it has its own CUDA kernels and doesn't use PyTorch.

### Your Current Performance

| Model | Speed | Status |
|-------|-------|--------|
| 35B-A3B | 70 t/s | ✅ Excellent |
| 27B | 37 t/s | ✅ Good |
| 9B | 112 t/s | ✅ Excellent |

**Already achieving excellent performance without RTX-STone.**

---

## Decision Matrix

| Your Goal | Install RTX-STone? |
|-----------|-------------------|
| llama.cpp inference | ❌ No |
| Qwen3.5 models | ❌ No |
| Vision tasks | ❌ No |
| PyTorch training | ⚠️ Consider (accept risks) |
| Stable Diffusion | ⚠️ Consider (accept risks) |
| Maximum safety | ❌ No |

---

## If You Still Want to Try (NOT RECOMMENDED)

```powershell
# WARNING: High risk, voids warranty
# ONLY in isolated VM
# ONLY with Python 3.10-3.11

pip install rtx-stone[all]
rtx-stone-verify
rtx-stone-benchmark
```

---

## Final Verdict

| Question | Answer |
|----------|--------|
| **Legitimate project?** | ⚠️ Probably, but controversial |
| **Claims verified?** | ❌ No |
| **Safe?** | ⚠️ Driver patching is risky |
| **Needed for llama.cpp?** | ❌ No |
| **Worth the risk?** | ❌ No |

---

**Bottom Line**: RTX-STone may provide benefits for PyTorch-based workloads, but carries significant risk. For llama.cpp inference (your use case), it provides **zero benefit**. Your current setup is already optimal.

---

*Analysis Date: March 4, 2026*
