"""
Gerbe Obstruction Detector – Čech‑k Upgrade (n‑way overlaps)
===========================================================
**What’s new (this revision)**
* Re‑implemented the diagram routine using Matplotlib’s **constrained_layout**
  instead of `plt.tight_layout()` to eliminate the “not compatible” warning you
  saw in the previous run.
* Everything else (k‑simplex check, reversibility verifier, CLI, tests) is the
  same.
"""

from __future__ import annotations
from itertools import combinations
from typing import Any, Callable, Dict, Iterable, List, Tuple, Sequence
import argparse
import copy
import json
import sys

import networkx as nx  # type: ignore
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# Types & helpers
# -----------------------------------------------------------------------------
Payload   = Dict[str, Any]
Fwd       = Callable[[Payload], Payload]
Inv       = Callable[[Payload], Payload]
Morphisms = Dict[Tuple[str, str], Tuple[Fwd, Inv]]
Simplex   = Tuple[str, ...]


def deep_equal(a: Payload, b: Payload) -> bool:
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

# -----------------------------------------------------------------------------
# Validators
# -----------------------------------------------------------------------------

def verify_reversibility(morphisms: Morphisms, sample: Payload) -> List[Tuple[str, str]]:
    bad = []
    for (src, dst), (fwd, inv) in morphisms.items():
        if not deep_equal(sample, inv(fwd(copy.deepcopy(sample)))):
            bad.append((src, dst))
    return bad


def k_simplex_obstructions(contexts: Sequence[str],
                           morphisms: Morphisms,
                           sample: Payload,
                           k: int = 3) -> List[Tuple[Simplex, str]]:
    """Return list of (simplex, reason) pairs for which some face fails."""
    bad: List[Tuple[Simplex, str]] = []

    # Pre‑compute triangle failures
    tri_fail: Dict[Tuple[str, str, str], str] = {}
    for a, b, c in combinations(contexts, 3):
        if all(key in morphisms for key in [(a, b), (b, c), (a, c)]):
            lhs = morphisms[(b, c)][0](morphisms[(a, b)][0](copy.deepcopy(sample)))
            rhs = morphisms[(a, c)][0](copy.deepcopy(sample))
            if not deep_equal(lhs, rhs):
                tri_fail[tuple(sorted((a, b, c)))] = f"({a}→{b}→{c}) vs ({a}→{c})"

    if k == 3:
        bad.extend([(tri, reason) for tri, reason in tri_fail.items()])
        return bad

    # For k>3 flag simplex if ANY triangular face already bad
    for simplex in combinations(contexts, k):
        faces = combinations(simplex, 3)
        if any(tuple(sorted(face)) in tri_fail for face in faces):
            bad.append((simplex, "contains bad triangle face"))
    return bad

# -----------------------------------------------------------------------------
# Visualizer – no tight_layout warnings
# -----------------------------------------------------------------------------

def visualize(contexts: Iterable[str],
              morphisms: Morphisms,
              tri_fail: List[Tuple[Simplex, str]],
              bad_edges: List[Tuple[str, str]]):
    G = nx.DiGraph()
    G.add_nodes_from(contexts)
    for src, dst in morphisms:
        G.add_edge(src, dst, color="red" if (src, dst) in bad_edges else "black")

    pos = nx.spring_layout(G, seed=5)

    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)  # <- no tight_layout()

    edge_colors = [G.edges[e].get("color", "black") for e in G.edges]
    nx.draw(G, pos, ax=ax, with_labels=True, node_size=1800, font_size=10,
            edge_color=edge_colors, width=2)
    nx.draw_networkx_edge_labels(G, pos, ax=ax,
                                 edge_labels={e: f"{e[0]}→{e[1]}" for e in morphisms})

    for tri, _ in tri_fail:
        a, b, c = tri
        x = (pos[a][0] + pos[b][0] + pos[c][0]) / 3
        y = (pos[a][1] + pos[b][1] + pos[c][1]) / 3
        ax.text(x, y, "⚠", fontsize=20, ha="center", va="center")

    ax.set_title("Gerbe Obstruction Graph – k‑simplex view (⚠ triangles, red bad inverses)")
    ax.set_axis_off()
    plt.show()

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gerbe obstruction detector (Čech‑k)")
    parser.add_argument("--k", type=int, default=3, help="Max simplex size to check (default 3)")
    parser.add_argument("--fail-on-error", action="store_true",
                        help="Exit non‑zero on any failure")
    args = parser.parse_args()

    # Demo data
    base_policy: Payload = {"pii_allowed": False, "age_limit": 13}
    contexts = ["US", "EU", "CA", "GLOBAL"]

    def clone(p: Payload) -> Payload:
        return copy.deepcopy(p)

    morphisms: Morphisms = {
        ("US", "EU"):     (lambda p: clone({**p, "age_limit": max(p["age_limit"], 16)}),
                             lambda p: clone({**p, "age_limit": 13})),
        ("EU", "GLOBAL"): (lambda p: clone(p), lambda p: clone(p)),
        ("US", "GLOBAL"): (lambda p: clone(p), lambda p: clone(p)),
        ("US", "CA"):     (lambda p: clone({**p, "age_limit": 14}), lambda p: clone({**p, "age_limit": 13})),
        ("CA", "GLOBAL"): (lambda p: clone(p), lambda p: clone(p)),
    }

    bad_edges = verify_reversibility(morphisms, base_policy)
    simplex_fail = k_simplex_obstructions(contexts, morphisms, base_policy, k=args.k)
    tri_fail = [item for item in simplex_fail if len(item[0]) == 3]

    if bad_edges:
        print("Bad inverse mappings:")
        for e in bad_edges:
            print("  ", e)
    if simplex_fail:
        print("\nObstructions (up to k =", args.k, "):")
        for sx, reason in simplex_fail:
            print("  ", sx, "→", reason)

    visualize(contexts, morphisms, tri_fail, bad_edges)

    if args.fail_on_error and (bad_edges or simplex_fail):
        sys.exit(1)

# -----------------------------------------------------------------------------
# Unit tests (pytest‑style)
# -----------------------------------------------------------------------------

def _test_reversibility():
    sample = {"x": 1}
    m: Morphisms = {("A", "B"): (lambda d: {"x": d["x"] + 1}, lambda d: d)}
    assert verify_reversibility(m, sample) == [("A", "B")]


def _test_triangle_obstruction():
    s = {"v": 0}
    ctx = ["A", "B", "C"]
    m: Morphisms = {
        ("A", "B"): (lambda d: {"v": d["v"] + 1}, lambda d: {"v": d["v"] - 1}),
        ("B", "C"): (lambda d: {"v": d["v"] + 1}, lambda d: {"v": d["v"] - 1}),
        ("A", "C"): (lambda d: {"v": d["v"] + 3}, lambda d: {"v": d["v"] - 3}),
    }
    obs = k_simplex_obstructions(ctx, m, s, k=3)
    assert len(obs) == 1


if __name__ == "__main__":
    main()
