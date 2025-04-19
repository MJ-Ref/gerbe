# Gerbe Obstruction Detector

> **A topology‑inspired static analysis and runtime audit tool that verifies local‑to‑global consistency across policy, data, or agent transforms using Čech‑style obstruction checks.**

![Gerbe Banner](docs/banner.png)

---

## Table of Contents
1. [Background](#background)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Usage](#usage)
5. [CLI Flags](#cli-flags)
6. [Understanding the Output](#understanding-the-output)
7. [CI/CD Integration](#cicd-integration)
8. [API Reference](#api-reference)
9. [Extending the Detector](#extending-the-detector)
10. [Contributing](#contributing)
11. [Roadmap](#roadmap)
12. [License](#license)

---

## Background

A **gerbe** is a stack of groupoids that becomes locally trivial but can exhibit hidden *global* twists classified by degree‑2 cohomology. In practical terms, that is exactly the problem of *federated* or *multi‑agent* AI systems: every shard is self‑consistent, yet stitching them together can silently violate higher‑order constraints (privacy, policy, fairness, safety).

```
   Contexts         Morphisms              Global Consistency Test
 ─────────────    ──────────────       ─────────────────────────────
  A  B  C  …       fAB  fBC  fAC        Does (A→B→C) == (A→C) ?
```

The **Gerbe Obstruction Detector** makes those twists explicit. It:

* validates that every *morphism* (data or policy transform) is *reversible*;
* checks that all **k‑simplices** (default triangles) glue consistently;
* generates provenance diagrams so auditors can see exactly *where* and *why* a violation occurred.

---

## Features

| Capability | Description |
|------------|-------------|
| ⚠ **Čech‑k obstruction checks** | Detects inconsistencies in any overlap size *k* (triangles, tetrahedra, …). |
| 🔄 **Reversibility verification** | Flags morphisms whose forward/inverse pair fails a round‑trip test. |
| 🖼 **Automated provenance graph** | Renders a NetworkX/Matplotlib diagram with red edges (bad inverses) and ⚠ triangles (failed glue). |
| 🛠 **CLI with CI‑friendly exit codes** | `--fail-on-error` returns `1` if *any* obstruction or bad inverse is detected. |
| 🧪 **Pytest unit tests** | Out‑of‑the‑box test suite validates core detectors. |
| ✨ **Zero external services** | Pure Python; runs offline for privacy‑sensitive data. |

---

## Quick Start

### Requirements
* Python ≥ 3.9
* `pip install -r requirements.txt`  
  *(Installs `networkx`, `matplotlib`, `typing‑extensions`.)*

### Installation
```bash
# Clone the repo
$ git clone https://github.com/MJ-Ref/gerbe.git
$ cd gerbe

# (Optional) create venv
$ python -m venv .venv && source .venv/bin/activate

# Install deps
$ pip install -r requirements.txt
```

### Running the demo
```bash
$ python gerbe_obstruction_detector.py
```
You should see a provenance graph pop up and console output summarising any inconsistencies.

---

## Usage

```bash
$ python gerbe_obstruction_detector.py [--k K] [--fail-on-error]
```

**Example (block CI on any error):**
```bash
$ python gerbe_obstruction_detector.py --k 4 --fail-on-error
```

---

## CLI Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--k` | `3` | Maximum simplex size to check. `3` = triangles only; `4` includes tetrahedra, etc. |
| `--fail-on-error` | *off* | Exit with status `1` if **any** obstruction or bad inverse is found. Useful in CI/CD pipelines. |

---

## Understanding the Output

### Console
```
Bad inverse mappings:
   ('US', 'EU')

Obstructions (up to k = 4 ):
   ('US', 'EU', 'GLOBAL') → (US→EU→GLOBAL) vs (US→GLOBAL)
```
* **Bad inverse mappings** → forward/inverse pair failed round‑trip.
* **Obstructions** → paths through the overlap disagree; the tuple shows which contexts, and the reason explains the mismatch.

### Graph
* **Nodes** = contexts (tenants, agents, devices).
* **Black edge** = good inverse pair.
* **Red edge** = reversibility failure.
* **⚠ inside a simplex (triangle)** = local data fails to glue globally.

---

## CI/CD Integration

<details>
<summary>GitHub Actions example</summary>

```yaml
name: Consistency Checks
on: [push, pull_request]

jobs:
  gerbe‑check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - name: Run Gerbe obstruction detector
        run: python gerbe_obstruction_detector.py --fail-on-error
```
</details>

---

## API Reference

> All functions live in `gerbe_obstruction_detector.py`.  Import and reuse them in your own codebase if the CLI is too coarse‑grained.

### `verify_reversibility(morphisms, sample)`
Validate that every `(fwd, inv)` pair returns the *sample* payload after a round trip.
* **Returns** `List[Tuple[src, dst]]` of edges that fail.

### `k_simplex_obstructions(contexts, morphisms, sample, k=3)`
General Čech‑style obstruction check.
* **contexts** – iterable of context labels.
* **morphisms** – `{(src,dst): (fwd,inv)}` mapping.
* **sample** – representative payload to trace through transforms.
* **k** – highest simplex size to evaluate.
* **Returns** `List[(simplex, reason)]` for all failures up to size *k*.

### `visualize(contexts, morphisms, tri_fail, bad_edges)`
Render the provenance graph with NetworkX + Matplotlib. Triangles in `tri_fail` get ⚠; edges in `bad_edges` turn red.

### Extensibility hooks
* Swap `Payload` type alias for your own dataclass or pydantic model.
* Use a smarter `deep_equal` if semantic equivalence ≠ JSON identity.

---

## Extending the Detector

| Idea | Value |
|------|-------|
| **Edge privacy mode** | Ship the detector to devices, sync only overlap maps ≈ privacy‑by‑construction. |
| **Embedding payloads** | Trace vector representations through transforms to catch drift in multi‑modal RAG systems. |
| **Sheaf NN integration** | Combine with sheaf neural network layers to learn the *glue maps* themselves. |

---

## Contributing

1. Fork → create feature branch → PR.
2. Add/modify unit tests for any new functionality.
3. Ensure `pre‑commit run --all-files` passes (black, isort, flake8).
4. Confirm `pytest` is green and no CLI obstructions remain on sample data.

We welcome issues, discussions, and PRs ♥.

---

## Roadmap

| Milestone | ETA | Notes |
|-----------|-----|-------|
| **0.2.0** | 2025‑05 | JSON‑schema‑driven sample injection; YAML config support. |
| **0.3.0** | 2025‑06 | GraphQL API + Web dashboard for provenance diagrams. |
| **1.0.0** | 2025‑Q4 | Plug‑and‑play SDK for major LLM orchestrators (LangChain, Astra, AgentFlow). |

---

## License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

*Inspired by higher‑gauge theory and baked with 💚 by the Gerbe AI team.*

