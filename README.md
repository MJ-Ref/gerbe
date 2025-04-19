# Gerbe Obstruction Detector 🪄

A **local‑to‑global consistency validator** inspired by gerbe theory (stacks  
of groupoids & 2‑cocycles). It spots higher‑order inconsistencies,  
non‑reversible transforms, and silent drift in multi‑model or federated AI  
pipelines **before** they hit production.

<p align="center">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue" />
  <img src="https://img.shields.io/badge/Python-3.9%2B-green" />
</p>

---

## 📦 Repository layout

| Path | Purpose |
|------|---------|
| `gerbe_obstruction_detector.py` | **Triangle + policy** toy checker |
| `gerbe_embedding_demo.py` | **2‑D multilingual embeddings** (drift flag, `--save-fig`) |
| `gerbe_edge_demo.py` | **Edge/federated** – N‑dim numeric drift + inverse checks |
| `gerbe_full_demo.py` | **Kitchen‑sink** – embeddings **+** policy **+** artefact reports |
| `tests/` | (Optional) pytest suite you can extend |

---

## 🔧 Installation

```bash
# Clone the repo
git clone https://github.com/MJ-Ref/gerbe.git
cd gerbe

# Set up env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # if you add one
# or, because deps are light:
pip install numpy networkx matplotlib
```

Python ≥ 3.9 recommended.

---

## 🚀 Quick start

```bash
# 1 · Policy triangle check
python gerbe_obstruction_detector.py

# 2 · Multilingual embedding validator (inject 10° drift)
python gerbe_embedding_demo.py --inject-bug --fail-on-error

# 3 · Federated scenario (5 % numeric drift, 64‑D)
python gerbe_edge_demo.py --nodes 4 --dim 64 --drift 0.05 --k 3 --fail-on-error

# 4 · Full‑stack demo with artefact reports (CI‑ready)
python gerbe_full_demo.py --nodes 8 --dim 128 --drift 0.04 \
  --policy-drift 0.20 --k 3 --report --fail-on-error
```

Graph legend:

* **Black edge** = reversible transform OK  
* **Red edge**  = inverse sanity check failed  
* **⚠** inside simplex = numeric embedding obstruction  
* **✖** inside simplex = policy (JSON) obstruction  

If `--fail-on-error` is supplied, the script exits 1 to gate CI.

---

## 🖼️ Interactive vs Head‑less runs

| Mode | What happens | When to use |
|------|--------------|-------------|
| **Interactive** (default) | Matplotlib GUI pops up; terminal waits until you close it. | Local exploration. |
| **Head‑less** | No window. PNG + JSON + HTML report written to `./reports/`. | CI, SSH, evidence packets. |

### Head‑less cheat sheet

```bash
# Minimal head‑less run (PNG+JSON+HTML)
python gerbe_full_demo.py --report

# Extended example (numeric + policy drift, CI gate)
python gerbe_full_demo.py --nodes 8 --dim 128 --drift 0.04 \
  --policy-drift 0.2 --k 3 --report --fail-on-error
```

> **Tip:** multi‑line Bash commands need **plain ASCII `\`** line ‑continuations.  
> Fancy spaces from chat copy‑paste can confuse `zsh` (`unknown file attribute`).

`gerbe_embedding_demo.py` supports `--save-fig filename.png` to save just the  
figure and skip the GUI.

---

## 🧠 How it works (high level)

1. **Contexts** (devices, languages, micro‑agents) become *objects* in a groupoid.  
2. **Morphisms** = reversible transforms (policy rewrite, embedding rotation).  
3. For every *k*‑simplex (default 3):

   ```
   obj₁ → obj₂ → … → objₖ   vs.   obj₁ → objₖ
   ```

   If paths disagree → **degree‑2 obstruction** (the core gerbe 2‑cocycle).  
4. Optional inverse check (`M·M⁻¹ ≈ I`) marks red edges.

---

## 🛠 CI integration (GitHub Actions)

```yaml
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
      - run: python gerbe_full_demo.py --nodes 8 --dim 128 \
             --drift 0.02 --policy-drift 0.1 --k 3 \
             --report --fail-on-error
```

Any obstruction or bad inverse stops the PR from merging; PNG + HTML attach to build artefacts.

---

## ✨ Validation demos in depth

### `gerbe_embedding_demo.py`

| Demo detail | Why it matters |
|-------------|----------------|
| 2‑D toy embeddings | Easy to visualise. |
| Rotations model EN→ES→FR | Realistic weight‑sharing analogue. |
| `--inject-bug` flag | Reproduces mis‑aligned retrain. |

### `gerbe_edge_demo.py`

| Demo detail | Why it matters |
|-------------|----------------|
| 64‑D embeddings (configurable) | Production‑scale vectors. |
| Random orthonormal matrices | Stand‑in for privacy‑preserving transforms. |
| Drift injection | Models rogue device versions. |
| k‑simplex up to Čech | Guarantees incumbents don’t. |

### `gerbe_full_demo.py`

| Demo detail | Why it matters |
|-------------|----------------|
| Numeric + policy layers combined | Mirrors real multi‑layer stacks. |
| Artefact reports (PNG + JSON + HTML) | Machine‑parsable & auditor‑friendly. |
| CI gate flag (`--fail-on-error`) | Drop‑in pipeline safety net. |

---

## 🗺 Roadmap

* **Typed API / Pydantic models** — pluggable transform registry  
* **Graphviz export** — PDF provenance certs for audits  
* **gRPC micro‑service** — online validation guardrail  
* **Automatic repair suggestions** — minimal patch hints  
* **Edge delta sync** — ship only overlap maps (privacy by design)

---

*Gerbe: from the French “sheaf of wheat” 🌾—we weave scattered data into a  
coherent harvest of insight.*

