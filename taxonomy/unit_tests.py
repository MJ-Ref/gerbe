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
