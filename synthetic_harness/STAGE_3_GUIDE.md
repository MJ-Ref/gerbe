# Stage 3 ‑ Synthetic Falsification Harness 🎯

*Objective*  
Verify that Gerbe’s obstruction detector is **accurate**:  
*high recall* (catches injected contradictions) and *low false‑positive* rate.

---

## 1 · Folder layout

```
synthetic_harness/
├── generate_cases.py     # builds labelled random graphs
├── eval_precision.py     # runs detector, computes P/R/F1
└── STAGE_3_GUIDE.md      # <‑‑ this file
```

(We’ll add the two scripts in PR‑2 of this stage.)

---

## 2 · Pass criteria

| Metric | Threshold |
|--------|-----------|
| **Recall** | ≥ 0.95 |
| **Precision** | ≥ 0.90 |
| **F1 score** | ≥ 0.92 |

Measurements taken over **1 000 random graphs** with:

* 100–300 nodes  
* 64‑D embeddings  
* Average degree ≈ 4  
* 1–5 injected embedding obstructions **and/or** policy obstructions per graph  
* Optional numeric noise that does **not** break consistency (to test FP rate).

---

## 3 · Running the harness

```bash
cd synthetic_harness
python generate_cases.py --n-graphs 1000 --out dataset.pkl
python eval_precision.py  --in dataset.pkl
```

`eval_precision.py` prints:

```
Graphs tested: 1000
True Obstructions:  4 999
Detected:          4 823
False Positives:      387
Recall: 0.964  Precision: 0.926  F1: 0.944
```

Script exits **0** only if all three thresholds meet the table above.

---

## 4 · Implementation hints

### 4.1 generate_cases.py

* Reuse `synthetic_graph()` from Stage 1 to build base graph.  
* Pick random triangles and **flip** one edge’s matrix (numeric) or JSON patch (policy) to create ground‑truth obstruction.  
* Store:  
  * `mats`, `patches`, `base_vec`, `base_policy`, `truth set` (list of offending triangles).

### 4.2 eval_precision.py

* Loop over stored graphs.  
* Run the same `embedding_obstructions()` and `policy_obstructions()` functions.  
* Compare detector output to ground‑truth sets → TP / FP / FN.

### 4.3 speed target

Full 1 000‑graph eval should finish **< 3 minutes** on laptop CPU.

---

## 5 · Deliverables

* `dataset.pkl` – serialized test graphs (ignored in git via `.gitattributes`)  
* `report.md` – summary table & one‑liner “Stage 3 passed / failed”  
* (Optional) ROC curve PNG if you sweep tolerance parameters.

---

## 6 · Troubleshooting tips

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Recall low | Bug injection not actually detectable (missing edge in graph). | Ensure each injected triple has all three edges present. |
| Many false positives | Tolerance too strict; numeric noise triggers flags. | Relax default tol or set per‑transform tol. |
| Runtime > 3 min | Graphs too dense; use `avg_deg` 4‑6. | Reduce node count or parallelise over CPU cores. |

---

## 7 · Stage exit

* **Green**: Precision, Recall, F1 ≥ thresholds → move to Stage 4 (auto‑graph generator).  
* **Red**: Identify which metric fails → tweak tolerance, improve inverse fns, or adjust injection logic.

---
