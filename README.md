# Gerbe Obstruction Detector 🪄

A **local‑to‑global consistency validator** inspired by gerbe theory  
(stacks of groupoids & 2‑cocycles).  
It spots higher‑order inconsistencies, non‑reversible transforms, and silent
drift in multi‑model or federated AI pipelines **before** they hit production.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-green" />
</p>

---

## 📦 Repository layout (after Stage 3)

| Path | Purpose |
|------|---------|
| `gerbe_obstruction_detector.py` | **Policy + numeric** triangle checker (toy). |
| `gerbe_embedding_demo.py` | 2‑D multilingual embeddings; `--inject-bug`. |
| `gerbe_edge_demo.py` | Federated / edge demo – N‑dim drift + inverse checks. |
| `gerbe_full_demo.py` | Kitchen‑sink run – embeddings + policy + HTML/PNG artefacts. |
| `synthetic_harness/` | **Stage 3 benchmark** (dataset generator + PR/F1 evaluator). |
| `bench/` | Scalability spike scripts (Stage 1). |
| `taxonomy/` | Reversible‑transform registry & unit tests (Stage 2). |
| `docs/STAGE_3_REPORT.md` | What we achieved, how, and final metrics. |

---

## 🔧 Install

```bash
git clone https://github.com/your‑org/gerbe.git
cd gerbe
python -m venv .venv && source .venv/bin/activate
pip install numpy networkx matplotlib
```

(Only CPU NumPy/BLAS needed; optional `torch` if you extend Stage 2.)

---

## 🚀 Quick tour

```bash
# Policy triangle check
python gerbe_obstruction_detector.py

# 2‑D embeddings with drift (should fail)
python gerbe_embedding_demo.py --inject-bug --fail-on-error

# Edge scenario (64‑D, 5 % numeric drift)
python gerbe_edge_demo.py --nodes 4 --dim 64 --drift 0.05 --k 3

# Stage‑3 harness (200 graphs) — prints P/R/F1
cd synthetic_harness
python generate_cases.py --n-graphs 200 --min-nodes 80 --max-nodes 120 --out sample.pkl
python eval_precision.py --in sample.pkl
```

> **Stage‑3 result (sample run)**: Precision ≈ 0.94   •  Recall ≈ 0.97   •  F1 ≈ 0.95

---

## 🧠 How the checker works

1. **Contexts** (e.g. devices, languages) are groupoid objects.  
2. **Morphisms** = reversible transforms (rotation, JSON patch).  
3. For every triangle `obj₁→obj₂→obj₃` vs `obj₁→obj₃`, compare results.  
4. Relative L2 tolerance (default 30 %) decides pass/fail.  
5. Optional inverse check marks red edges when `M·M⁻¹ ≉ I`.

---

## 🖥️ Head‑less vs GUI

| Mode | Output | Use‑case |
|------|--------|---------|
| GUI (default) | Matplotlib window | Local exploration. |
| `--report`    | PNG + JSON + HTML in `./reports` | CI pipelines, audit packs. |

---

## 🛠 CI gate (GitHub Actions example)

```yaml
name: Gerbe Validate

on: [pull_request]

jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install numpy networkx matplotlib
      - run: |
          python gerbe_full_demo.py --nodes 8 --dim 128 \
            --drift 0.02 --policy-drift 0.1 --k 3 \
            --report --fail-on-error
```

Any obstruction (⚠ numeric or ✖ policy) exits 1 and blocks the PR.

---

## ✨ Stage 3 in a nutshell

* **Bidirectional edges** + inverse matrices guarantee every triangle orientation is checked.  
* **Drift amplitude ± 0.5** dwarfs numeric noise.  
* **Truth‑set includes every triangle containing a drifted edge** — zero hidden positives.  
* **Relative Frobenius tolerance 30 %** eliminates noise FPs but still flags real drift.

Final benchmark (1 000 graphs, 100–300 nodes each):

| Precision | Recall | F1 |
|-----------|--------|----|
| **0.94** | **0.97** | **0.95** |

See `docs/STAGE_3_REPORT.md` for the journey.

---

## 🗺 Roadmap

* **Stage 4 – `gerbe validate` CLI** (repo CI gate).  
* Auto‑discover graph (`gerbe scan`) for zero‑config adoption.  
* Typed transform registry & Graphviz audit export.

---

*Gerbe = French “sheaf of wheat” 🌾— weaving scattered models & policies into coherent, harvestable insight.*
