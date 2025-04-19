"""
taxonomy/reversible_transforms.py
---------------------------------
Catalog of *common* ML‑ops transforms plus an `approx_inverse()` stub
for each.  The goal is to quantify how many real‑world ops are
reversible *enough* for gerbe checks.

The registry maps a name → (forward_fn, inverse_fn, sample_value).

For fuzzy inverses we check L2 or semantic equality within a tolerance.
"""

import json
import numpy as np
import torch
import copy

REGISTRY = {}

def register(name):
    def _wrap(fnsample):
        REGISTRY[name] = fnsample
        return fnsample
    return _wrap

# --------------------------------------------------------------------
# 1. Identity (baseline sanity)
@register("identity")
def _( ):
    fwd = lambda x: x
    inv = lambda x: x
    sample = 42
    return fwd, inv, sample

# --------------------------------------------------------------------
# 2. fp32 ↔ fp16 tensor cast
@register("fp32_to_fp16")
def _():
    fwd = lambda t: t.half()
    inv = lambda t: t.float()
    sample = torch.randn(5, 5, dtype=torch.float32)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 3. LoRA merge (rank‑r update)  ~ inverse via subtract
@register("lora_merge")
def _():
    rank_r = 4
    A = torch.randn(16, rank_r)
    B = torch.randn(rank_r, 16)
    delta = A @ B
    fwd = lambda W: W + delta
    inv = lambda W: W - delta
    sample = torch.randn(16, 16)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 4. Quantize int8 <-> dequantize
@register("int8_quant")
def _():
    scale = 0.02
    fwd = lambda arr: (arr / scale).round().clip(-128,127).astype(np.int8)
    inv = lambda q: q.astype(np.float32) * scale
    sample = np.random.randn(32,).astype(np.float32)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 5. Temperature‑scale logits
@register("temp_scale_logits")
def _():
    T = 0.7
    fwd = lambda l: l / T
    inv = lambda l: l * T
    sample = torch.randn(10)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 6. JSON policy patch
@register("json_patch_age")
def _():
    patch = {"age_limit": 16}
    def fwd(js): 
        out = copy.deepcopy(js)
        out.update(patch)
        return out
    def inv(js):
        out = copy.deepcopy(js)
        if "age_limit" in out and out["age_limit"]==16:
            out.pop("age_limit")
        return out
    sample = {"pii_allowed": False, "age_limit": 13}
    return fwd, inv, sample

# --------------------------------------------------------------------
# 7. Lower‑case string ↔ Title‑case
@register("string_lower")
def _():
    fwd = lambda s: s.lower()
    inv = lambda s: s.title()
    sample = "Gerbe AI"
    return fwd, inv, sample
### Stage 2 artifact: **taxonomy/reversible\_transforms.py**


"""
taxonomy/reversible_transforms.py
---------------------------------
Catalog of *common* ML‑ops transforms plus an `approx_inverse()` stub
for each.  The goal is to quantify how many real‑world ops are
reversible *enough* for gerbe checks.

The registry maps a name → (forward_fn, inverse_fn, sample_value).

For fuzzy inverses we check L2 or semantic equality within a tolerance.
"""

import json
import numpy as np
import torch
import copy

REGISTRY = {}

def register(name):
    def _wrap(fnsample):
        REGISTRY[name] = fnsample
        return fnsample
    return _wrap

# --------------------------------------------------------------------
# 1. Identity (baseline sanity)
@register("identity")
def _( ):
    fwd = lambda x: x
    inv = lambda x: x
    sample = 42
    return fwd, inv, sample

# --------------------------------------------------------------------
# 2. fp32 ↔ fp16 tensor cast
@register("fp32_to_fp16")
def _():
    fwd = lambda t: t.half()
    inv = lambda t: t.float()
    sample = torch.randn(5, 5, dtype=torch.float32)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 3. LoRA merge (rank‑r update)  ~ inverse via subtract
@register("lora_merge")
def _():
    rank_r = 4
    A = torch.randn(16, rank_r)
    B = torch.randn(rank_r, 16)
    delta = A @ B
    fwd = lambda W: W + delta
    inv = lambda W: W - delta
    sample = torch.randn(16, 16)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 4. Quantize int8 <-> dequantize
@register("int8_quant")
def _():
    scale = 0.02
    fwd = lambda arr: (arr / scale).round().clip(-128,127).astype(np.int8)
    inv = lambda q: q.astype(np.float32) * scale
    sample = np.random.randn(32,).astype(np.float32)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 5. Temperature‑scale logits
@register("temp_scale_logits")
def _():
    T = 0.7
    fwd = lambda l: l / T
    inv = lambda l: l * T
    sample = torch.randn(10)
    return fwd, inv, sample

# --------------------------------------------------------------------
# 6. JSON policy patch
@register("json_patch_age")
def _():
    patch = {"age_limit": 16}
    def fwd(js): 
        out = copy.deepcopy(js)
        out.update(patch)
        return out
    def inv(js):
        out = copy.deepcopy(js)
        if "age_limit" in out and out["age_limit"]==16:
            out.pop("age_limit")
        return out
    sample = {"pii_allowed": False, "age_limit": 13}
    return fwd, inv, sample

# --------------------------------------------------------------------
# 7. Lower‑case string ↔ Title‑case
@register("string_lower")
def _():
    fwd = lambda s: s.lower()
    inv = lambda s: s.title()
    sample = "Gerbe AI"
    return fwd, inv, sample




### Stage 2 artifact: **taxonomy/unit\_tests.py**

#!/usr/bin/env python
"""
taxonomy/unit_tests.py
----------------------
Loop over all transforms in reversible_transforms.REGISTRY,
apply forward then inverse, and compute an error metric.

Pass criteria:
  * numeric tensors/arrays: max abs diff < 1e-3
  * JSON / dict / str: exact equality

Prints a summary table and exits 1 if overall pass rate < 70 %.
"""

import sys, math, json, numpy as np, torch
from reversible_transforms import REGISTRY

PASS, FAIL = [], []

def is_equal(a, b):
    if isinstance(a, (np.ndarray, torch.Tensor)):
        return float(np.max(np.abs(a - b))) < 1e-3
    return a == b

for name, fn in REGISTRY.items():
    fwd, inv, sample = fn()
    try:
        out = fwd(sample)
        back = inv(out)
        ok = is_equal(sample, back)
    except Exception as e:
        ok = False
        back = f"(error: {e})"
    (PASS if ok else FAIL).append(name)
    status = "✅" if ok else "❌"
    print(f"{status} {name:<20} | sample→fwd→inv == orig ? {ok}")

print("\nSummary:", len(PASS), "pass,", len(FAIL), "fail")
if len(PASS) / (len(PASS)+len(FAIL)) < 0.70:
    sys.exit("Fail rate too high for Stage‑2 threshold")
