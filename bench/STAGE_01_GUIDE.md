# Stage 1 ‑ Scalability & Performance Spike 🚀

*Objective:*  
Demonstrate that Gerbe’s triangle‑obstruction check scales to **≥ 1 000 contexts**
and 128‑D embeddings within acceptable latency and memory budgets.

---

## 1 · Folder layout

```
bench/
├── 01_scalability.py   # generates graphs & times two algorithms
├── STAGE_1_GUIDE.md    # <‑‑ you are here
```

---

## 2 · Key pass criteria

| Graph size | Target wall‑time | Target peak RAM |
|------------|-----------------|------------------|
| 1 000 nodes, avg deg ≈ 4, k = 3 | **< 30 s** on laptop CPU | **< 8 GB** RSS |

*If you have a GPU available, log the GPU‑batched results as “bonus.”*

---

## 3 · Running a single benchmark

```bash
cd bench
python 01_scalability.py --nodes 1000 --dim 128 --deg 4
```

Expected console line:

```
1000 nodes | 128‑D |  4000 edges |  15347 triangles | baseline 120.00s 800.0MB | pruned  12.34s 620.0MB
```

Interpretation:

* **baseline** = brute O(n³) — serves as a “worst case” reference.
* **pruned**   = edge‑aware algorithm — this must hit the targets.

---

## 4 · Sweep & plotting

To generate a quick scalability table:

```bash
python 01_scalability.py --sweep      # sweeps 100 → 600 by 100
```

Copy the output into a spreadsheet or Python notebook to plot nodes vs time.

---

## 5 · Deliverables

1. **`results.md`** (create in the same folder) containing:
   * Table of node counts, triangle counts, runtime, RAM.
   * A short paragraph: “Meets/Doesn’t meet Stage 1 threshold.”
2. **Optional**: screenshot of gprof/flamegraph if you optimized further.

---

## 6 · Troubleshooting FAQ

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: psutil` | dependency missing | `pip install psutil` |
| Runtime >> targets | Graph is dense; check `--deg` parameter. | Ensure `--deg` ≈ 4 when benchmarking. |
| Memory > 8 GB | NumPy not releasing; or dense matrix mult. | Make sure only sparse dict of edges stored; don’t build full n×n matrix. |

---

## 7 · Next steps

*Green Stage 1* ➜ move on to Stage 2 (reversible transform taxonomy).  
*Red Stage 1* ➜ profile hotspots, try GPU batch in PyTorch or limit radius‑R neighborhoods; re‑bench until green or raise blocker.

---

