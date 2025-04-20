#!/usr/bin/env python
"""
taxonomy/unit_tests.py
----------------------
Round‑trip every transform in reversible_transforms.REGISTRY.

Return signature:
    fwd, inv, sample               -> default tol = 1e‑3
    fwd, inv, sample, tol          -> custom tolerance
"""

import sys, json, numpy as np
import torch
from reversible_transforms import REGISTRY

DEFAULT_TOL = 1e-3
PASS, FAIL = [], []

def max_abs(a, b):
    if isinstance(a, torch.Tensor):
        return float(torch.max(torch.abs(a - b)))
    if isinstance(a, np.ndarray):
        return float(np.max(np.abs(a - b)))
    return 0.0 if a == b else float("inf")

for name, fn in REGISTRY.items():
    try:
        result = fn()
        if len(result) == 3:
            fwd, inv, sample = result
            tol = DEFAULT_TOL
        elif len(result) == 4:
            fwd, inv, sample, tol = result
        else:
            raise ValueError("Return tuple must have 3 or 4 elements")

        back = inv(fwd(sample))
        err  = max_abs(sample, back)
        ok   = err < tol
    except Exception as e:
        ok   = False
        err  = f"error: {e}"

    (PASS if ok else FAIL).append(name)
    status = "✅" if ok else "❌"
    print(f"{status} {name:<20} | err {err:<10} tol {tol}")

print(f"\nSummary: {len(PASS)} pass, {len(FAIL)} fail")
if len(PASS) / (len(PASS) + len(FAIL)) < 0.70:
    sys.exit("Fail rate too high for Stage‑2 threshold")
