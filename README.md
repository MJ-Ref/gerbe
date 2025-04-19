
# Gerbe Obstruction Detector 🪄

A **local‑to‑global consistency validator** inspired by gerbe theory (stacks
of groupoids & 2‑cocycles).  It spots higher‑order inconsistencies,
non‑reversible transforms, and silent drift in multi‑model or federated AI
pipelines **before** they hit production.

<p align="center">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue" />
  <img src="https://img.shields.io/badge/Python-3.9%2B-green" />
</p>

---

## 📦 Repository layout

| Path | Purpose |
|------|---------|
| `gerbe_obstruction_detector.py` | Core toy detector (triangles, policy JSON). |
| `gerbe_embedding_demo.py` | **Embedding demo** – checks multilingual linear transforms in 2‑D. |
| `gerbe_edge_demo.py` | **Edge/federated demo** – N‑dim embeddings, inverse checker, drift simulation, k‑simplex validation. |
| `tests/` | (Optional) pytest suite if you copy the provided snippets. |

---

## 🔧 Installation

```bash
# Clone the repo
$ git clone https://github.com/MJ-Ref/gerbe.git
$ cd gerbe

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# or, because deps are light:
pip install numpy networkx matplotlib
```

Python ≥ 3.9 recommended.

---

## 🚀 Quick start

```bash
# 1. Basic triangle check with policy blobs
python gerbe_obstruction_detector.py

# 2. Multilingual embedding validator (inject a 10° drift)
python gerbe_embedding_demo.py --inject-bug --fail-on-error

# 3. Edge / federated scenario with 5 % shortcut drift & 64‑D embeddings
python gerbe_edge_demo.py --nodes 4 --dim 64 --drift 0.05 --k 3 --fail-on-error
```

All scripts pop up a provenance graph:

* **Black edge** – reversible transform OK  
* **Red edge** – inverse sanity check failed  
* **⚠ inside simplex** – higher‑order obstruction (paths disagree)

If `--fail-on-error` is supplied, the script exits 1 to block CI.

---

## 🧠 How it works (high level)

1. **Contexts** (devices, languages, micro‑agents) become *objects* in a
   groupoid.
2. **Morphisms** are reversible transforms between contexts (policy rewrite,
   embedding rotation, data redaction …).
3. For every *k*-simplex (default 3 = triangle) the tool compares
   two paths:

```
obj₁ → obj₂ → … → obj_k   vs.   obj₁ → obj_k
```

If the composed map and the direct shortcut disagree within tolerance,
we’ve detected a **degree‑2 (or higher) obstruction** – the very heart of a
gerbe’s 2‑cocycle.

4. Optionally, each morphism’s inverse is verified (`M·M⁻¹ ≈ I`).  
   Failure marks that edge red.

---

## 🛠  CI integration

```yaml
# .github/workflows/gerbe-check.yml
name: Gerbe Validator

on: [pull_request]

jobs:
  gerbe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install numpy networkx matplotlib
      - run: python gerbe_edge_demo.py --nodes 4 --dim 64 --drift 0.02 --fail-on-error
```

A failing obstruction or bad inverse will stop the PR from merging.

---

## ✨ Validation demos in depth

### `gerbe_embedding_demo.py` — multilingual linear transforms

| What it shows | Why it matters |
|---------------|----------------|
| 2‑D toy embeddings (`dog` vector) | Easy to visualise; keeps math clear. |
| Rotations model EN→ES→FR translations | Realistic analogue for encoder/decoder weight sharing. |
| Drift injection `--inject-bug` | Simulates mis‑aligned retrain, catches it via gerbe check. |

### `gerbe_edge_demo.py` — federated / edge network

| What it shows | Why it matters |
|---------------|----------------|
| 64‑D embeddings (configurable) | Scales to production vector sizes. |
| Random orthonormal matrices | Stand‑in for privacy‑preserving transforms. |
| Noise / drift on shortcuts | Models rogue device versions or stale weights. |
| *k*-simplex up to Čech cover | Higher‑order guarantees no incumbent stack checks. |
| Red‑edge inverse verifier | Early detection of non‑reversible updates. |

---

## 🗺 Roadmap

* **Typed API / pydantic models** – pluggable transform registries.  
* **Graphviz export** – PDF provenance certificates for audits.  
* **gRPC service** – drop‑in micro‑service for online validation.  
* **Automatic repair suggestions** – minimal path patch to restore consistency.  
* **Edge delta sync** – send only overlap maps, preserving data privacy.

---


---

*Gerbe: from the French “sheaf of wheat” 🌾—we weave scattered data into a
coherent harvest of insight.*
