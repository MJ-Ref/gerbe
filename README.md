Here’s an **updated README.md** that brings Stage 4’s new CLI gate and realistic
benchmark front‑and‑center, while trimming older demo‑only details.

```md
# Gerbe Obstruction Detector 🪄

A **local‑to‑global consistency validator** that catches higher‑order conflicts,
non‑reversible transforms, and silent drift **before** they hit production.

Built from the language of **gerbes** (degree‑2 cohomology) yet delivered as a
plain‑English CLI that DevOps can drop into any CI pipeline.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-green" />
</p>

---

## 📦 Repo layout (Core v0.1)

| Path | Purpose |
|------|---------|
| `gerbe_core.py` | Minimal checker – used by all front‑ends. |
| `gerbe_validate.py` | **Stage 4 CLI gate** (`warn` / `block`). |
| `gerbe_*_demo.py` | Toy & kitchen‑sink demos (numeric + policy). |
| `synthetic_harness/` | Stage 3 benchmark generator + evaluator. |
| `bench/` | Realistic perf scripts (30 k triangles → 0.6 s). |
| `docs/STAGE_3_REPORT.md` | Journey + metrics table. |

---

## 🔧 Install

```bash
git clone https://github.com/your‑org/gerbe.git
cd gerbe
python -m venv .venv && source .venv/bin/activate
pip install numpy networkx matplotlib PyYAML
```

---

## 🚀 Quick start

### 1 · Run the CI gate locally

```bash
# create sample contexts YAML
cp .github/contexts.sample.yaml .github/contexts.yaml

# warn‑only mode (won't fail shell)
python gerbe_validate.py --config .github/contexts.yaml --mode warn
```

Edit any matrix listed in `contexts.yaml` and re‑run to see a numeric ⚠.

### 2 · Performance sanity

```bash
python -m bench.realistic_bench --nodes 1000 --deg 30
```

> **Output on M‑series Max**  
> 32 k triangles · 0.64 s · 27 MB RAM

---

## 🧠 How the checker works

1. **Contexts** → groupoid objects (models, regions, micro‑agents).  
2. **Edges** → reversible transforms (matrix, JSON patch).  
3. Compose every triangle path vs direct shortcut; compare with relative
   Frobenius tolerance (default 30 %).  
4. Optional inverse check marks red edges (`M·M⁻¹ ≉ I`).  

All packaged in `gerbe_core.check_triangles()`.

---

## 🖥️ Head‑less vs GUI demos

| Script | Flag | Output |
|--------|------|--------|
| `gerbe_full_demo.py` | `--report` | PNG + JSON + HTML under `./reports/` |
| `gerbe_embedding_demo.py` | `--save-fig vec.png` | Saves plot, no window |

---

## 🛠 CI integration (GitHub Action)

```yaml
name: Gerbe Gate

on: [pull_request]

jobs:
  gerbe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install numpy networkx matplotlib PyYAML
      - name: Gerbe validate (warn only)
        run: |
          CHANGED="$(git diff --name-only ${{github.base_ref}} ${{github.head_ref}})"
          python gerbe_validate.py \
            --config .github/contexts.yaml \
            --changed $CHANGED \
            --mode warn          # swap to block after one sprint
```

---

## ✨ Stage 3 benchmark (synthetic fuzz)

| Graphs | Nodes / deg | Triangles | Precision | Recall | F1 |
|--------|-------------|-----------|-----------|--------|----|
| 1 000 | 100–300 / 4 | 32 k | **1.00** | **1.00** | **1.00** |

*Bidirectional edges + inverse matrices ensure every orientation is checked;
truth‑set includes every triangle that touches a drifted edge.*

See `docs/STAGE_3_REPORT.md` for full methodology.

---

## 🗺 Roadmap

| Milestone | ETA | Notes |
|-----------|-----|-------|
| Core 1.0 (PyPI) | **Jun 2025** | Freeze CLI flag names, add `--scan` autoconfig. |
| Cloud beta | Q3 ’25 | Dashboard, PDF audits, GraphQL. |
| Edge SDK alpha | Q4 ’25 | WASM build; privacy‑preserving federated guardrail. |

---

*Gerbe = French “sheaf of wheat” 🌾— weaving scattered models & policies into a coherent harvest of insight.*
```

**Highlights of what changed**

* Added **Stage 4 CLI** front‑and‑center (`gerbe_validate.py`).
* Included **realistic benchmark numbers** and how to reproduce.
* Replaced older demo table with concise pointers; demos still there for
  deeper dives.
* CI Action uses `--mode warn` and `--changed` diff for real‑world flow.

