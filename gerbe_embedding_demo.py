"""
gerbe_embedding_demo.py
-----------------------
Demonstrates gerbe‑style obstruction detection on 2‑D multilingual
embeddings.  A 10° drift in the EN→FR shortcut triggers an obstruction.

Usage examples
--------------
# Happy path (interactive plot window)
python gerbe_embedding_demo.py

# Inject drift, save provenance graph to PNG, exit 1 on error (CI‑friendly)
python gerbe_embedding_demo.py --inject-bug --save-fig drift.png --fail-on-error
"""

import argparse
import itertools
import math
import sys

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


# ---------- helper: 2‑D rotation matrix ------------------------------------
def rot(theta_rad: float) -> np.ndarray:
    """Return a 2×2 rotation matrix for angle theta_rad (radians)."""
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, -s], [s, c]])


def deep_close(a: np.ndarray, b: np.ndarray, tol: float = 1e-6) -> bool:
    return np.allclose(a, b, atol=tol)


def compose(M2: np.ndarray, M1: np.ndarray) -> np.ndarray:
    """Matrix composition: first apply M1, then M2."""
    return M2 @ M1


# ---------- obstruction detector ------------------------------------------
def obstruction_detector(contexts, morphisms, sample_vec, k: int = 3):
    """Return list of (context tuple, lhs, rhs) that violate consistency."""
    bad = []
    for combo in itertools.combinations(contexts, k):
        first, *_, last = combo
        # chained matrix via successive composites
        M_chain = np.eye(sample_vec.shape[0])
        for a, b in zip(combo[:-1], combo[1:]):
            M_chain = compose(morphisms[(a, b)], M_chain)
        M_direct = morphisms[(first, last)]
        lhs, rhs = M_chain @ sample_vec, M_direct @ sample_vec
        if not deep_close(lhs, rhs):
            bad.append((combo, lhs, rhs))
    return bad


# ---------- graph visual ---------------------------------------------------
def draw_graph(contexts, morphisms, obstructions):
    G = nx.DiGraph()
    G.add_nodes_from(contexts)
    G.add_edges_from(morphisms)
    pos = nx.spring_layout(G, seed=4)

    plt.figure(figsize=(6, 4), constrained_layout=True)
    nx.draw(G, pos, with_labels=True, node_size=1500, font_size=10)
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels={e: f"{e[0]}→{e[1]}" for e in morphisms}, font_size=8
    )
    # mark each failing triangle with ⚠
    for combo, *_ in obstructions:
        xs = [pos[n][0] for n in combo]
        ys = [pos[n][1] for n in combo]
        plt.text(sum(xs) / len(xs), sum(ys) / len(ys), "⚠", fontsize=18, ha="center")
    plt.title("Gerbe Embedding Obstruction Graph")
    plt.axis("off")


# ---------- synthetic data -------------------------------------------------
def build_synthetic():
    contexts = ["EN", "ES", "FR"]
    base = np.array([1.0, 0.0])
    morphisms = {
        ("EN", "ES"): rot(math.radians(30)),
        ("ES", "FR"): rot(math.radians(30)),
        ("EN", "FR"): rot(math.radians(60)),
    }
    return contexts, morphisms, base


# ---------- CLI & main -----------------------------------------------------
def parse():
    p = argparse.ArgumentParser(description="Gerbe embedding demo")
    p.add_argument("--k", type=int, default=3, help="overlap order (default 3)")
    p.add_argument("--inject-bug", action="store_true",
                   help="rotate EN→FR by +10° (makes paths disagree)")
    p.add_argument("--save-fig", nargs="?", const="embedding_graph.png",
                   help="save provenance graph to file instead of showing "
                        "(optional custom filename)")
    p.add_argument("--fail-on-error", action="store_true",
                   help="exit 1 if any obstruction is found")
    return p.parse_args()


def main():
    args = parse()
    contexts, morphisms, sample = build_synthetic()

    # Optional drift
    if args.inject_bug:
        morphisms[("EN", "FR")] = rot(math.radians(70))  # 60° + 10° drift

    # Detect inconsistencies
    bad = obstruction_detector(contexts, morphisms, sample, k=args.k)

    # Console summary
    if bad:
        print("*** Obstruction detected! ***")
        for combo, lhs, rhs in bad:
            print(f"{combo}:  lhs={lhs}  rhs={rhs}")
    else:
        print("No obstruction detected.")

    # Plot or save figure
    draw_graph(contexts, morphisms, bad)
    if args.save_fig is not None:
        plt.savefig(args.save_fig, dpi=150)
        print(f"Graph saved to {args.save_fig}")
    else:
        plt.show()

    # CI gate
    if args.fail_on_error and bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
