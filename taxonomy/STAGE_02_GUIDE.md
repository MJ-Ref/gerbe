
# Stage 2 ‑ Reversible Transform Taxonomy 🚦

*Objective:*  
Prove that **≥ 70 %** of real‑world ML‑ops transforms used in our target
pipelines can be given a *good‑enough* inverse, making them suitable
“morphisms” for Gerbe obstruction checks.

---

## 1 · Folder layout

```
taxonomy/
├── reversible_transforms.py   # registry of (forward, inverse) snippets
├── unit_tests.py              # auto‑discovers registry, runs round‑trip checks
└── STAGE_2_GUIDE.md           # <‑‑ you are here
```

---

## 2 · What counts as “reversible”?

| Payload type | Metric | Pass threshold |
|--------------|--------|----------------|
| **NumPy / PyTorch tensors** | `max(abs(orig − inv(fwd(orig))))` | < 1 e‑3 |
| **JSON / Python dicts** | structural equality (`==`) | exact |
| **Strings** | equality | exact |

A transform can be *approximate* (e.g., fp32 ↔ fp16) as long as we never lose
more than 1 ‰ in absolute value.

---

## 3 · Running the tests

```bash
cd taxonomy
python unit_tests.py
```

You’ll see per‑transform results:

```
✅ identity              | sample→fwd→inv == orig ? True
✅ fp32_to_fp16          | ...
❌ string_lower          | False (title‑case isn’t true inverse)
...
Summary: 5 pass, 1 fail
```

* The script exits **1** (CI fail) if global pass‑rate < 70 %.
* A Green run is the **Stage 2 exit‑criteria**.

---

## 4 · Adding a new transform

1. Open `reversible_transforms.py`.
2. Add a function decorated with `@register("your_name")` that returns  
   `(forward_fn, inverse_fn, sample_value)`.
3. `sample_value` should be *small* to keep tests fast.
4. Re‑run `unit_tests.py` — the new transform is auto‑discovered.

```python
@register("bfloat16_cast")
def _():
    fwd = lambda t: t.bfloat16()
    inv = lambda t: t.float()
    sample = torch.randn(8, 8)
    return fwd, inv, sample
```

---

## 5 · Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: torch` | PyTorch not installed. | `pip install torch` (CPU wheel fine). |
| Fuzzy numeric fails by 1e‑2 | Tolerance too strict for that op. | Add per‑op custom tolerance OR drop from registry. |
| Many transforms fail | Update pass‑rate threshold **only after** team review—keep bar high. |

---

## 6 · Expected deliverables

* **Green CI** for `taxonomy/unit_tests.py`  
  (≥ 70 % pass, exit code 0).
* PR description listing:  
  * total transforms,  
  * pass/fail counts,  
  * any open questions.

Optional:

* `taxonomy/reversible_transforms.md` — human‑readable table you can copy‑paste into the white‑paper.

---

## 7 · What happens next

Stage 2 feeds directly into Stage 3 (synthetic falsification harness).  
Only transforms that pass here will be used to generate fuzzed graphs for
precision/recall testing.

A failing Stage 2 means we either:

1. **Improve inverses** (better math, metadata), or  
2. **Relax requirement** (accept some one‑way morphisms and adjust proofs).

Keep the sprint tight—**2 days** to green or raise a blocker.

---

