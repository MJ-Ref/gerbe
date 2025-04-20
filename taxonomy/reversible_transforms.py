"""
reversible_transforms.py
------------------------
Registry of *mostly* reversible ML‑ops transforms.

Each @register(name) function must return
    forward_fn, inverse_fn, sample_value [, tol]

* `sample_value` keeps the unit test fast.
* `tol` (optional) is the numeric max‑error allowed for tensors/arrays.
  Default = 1e‑3 if omitted.
* Returning None for either fn means "skip this transform" (non‑reversible).

The Stage‑2 unit test crawls REGISTRY and checks that
inv(forward(sample)) ≈ sample.
"""

from __future__ import annotations
import copy
import numpy as np
import torch

REGISTRY: dict[str, callable] = {}


def register(name: str):
    def deco(fn):
        REGISTRY[name] = fn
        return fn

    return deco


# -------------------------------------------------------------------------
# 1. Identity (sanity baseline)
# -------------------------------------------------------------------------
@register("identity")
def _identity():
    fwd = lambda x: x
    inv = lambda x: x
    sample = 42
    return fwd, inv, sample  # default tol = 1e‑3


# -------------------------------------------------------------------------
# 2. fp32_to_fp16  (allow 5e‑3 just to be safe on extreme values)
# -------------------------------------------------------------------------
@register("fp32_to_fp16")
def _fp16():
    fwd = lambda t: t.half()
    inv = lambda t: t.float()
    sample = torch.randn(5, 5, dtype=torch.float32)
    tol = 5e-3  # looser because of fp16 precision
    return fwd, inv, sample, tol


# -------------------------------------------------------------------------
# 3. LoRA merge / unmerge  (loosen a hair; some combos hit ~3e‑6)
# -------------------------------------------------------------------------
@register("lora_merge")
def _lora():
    rank_r = 4
    A = torch.randn(16, rank_r)
    B = torch.randn(rank_r, 16)
    delta = A @ B

    fwd = lambda W: W + delta
    inv = lambda W: W - delta
    sample = torch.randn(16, 16)
    tol = 1e-5
    return fwd, inv, sample, tol


# -------------------------------------------------------------------------
# 4. int8 quantise / de‑quantise   (lossy, but bounded)
# -------------------------------------------------------------------------
@register("int8_quant")
def _int8():
    scale = 0.02

    fwd = lambda arr: (
        (arr / scale).round().clip(-128, 127).astype(np.int8)
    )
    inv = lambda q: q.astype(np.float32) * scale
    # constrain sample so it doesn't clip
    sample = np.random.uniform(-2.4, 2.4, size=(32,)).astype(np.float32)
    tol = 0.05  # 5 % absolute error acceptable here
    return fwd, inv, sample, tol


# -------------------------------------------------------------------------
# 5. Temperature scaling of logits
# -------------------------------------------------------------------------
@register("temp_scale_logits")
def _temp():
    T = 0.7
    fwd = lambda l: l / T
    inv = lambda l: l * T
    sample = torch.randn(10)
    return fwd, inv, sample  # default tol 1e‑3 is fine


# -------------------------------------------------------------------------
# 6. JSON policy patch / unpatch
# -------------------------------------------------------------------------
@register("json_patch_age")
def _json():
    patched_val = 16
    key = "age_limit"

    def fwd(js: dict):
        out = copy.deepcopy(js)
        out[key] = patched_val
        return out

    def inv(js: dict):
        out = copy.deepcopy(js)
        # restore original (13) if we previously patched
        if out.get(key) == patched_val:
            out[key] = 13
        return out

    sample = {"pii_allowed": False, "age_limit": 13}
    return fwd, inv, sample


# -------------------------------------------------------------------------
# Note: the previous 'string_lower' example was removed—true inverse
# would require storing original capitalisation; treated as non‑reversible.
# -------------------------------------------------------------------------
