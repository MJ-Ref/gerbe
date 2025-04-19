"""
gerbe_edge_demo.py
------------------
Ambitious demonstration of gerbe‑style obstruction detection in an
*edge / federated* setting with higher‑dimensional embeddings.

Key features
------------
• N‑dim (default 64) embeddings for multiple devices.
• Random orthonormal (rotation) matrices as reversible transforms.
• Optional noise injection to simulate drift / non‑reversible edges.
• k‑simplex obstruction detector up to full Čech cover.
• Inverse‑function verifier (marks red edges when |M·M⁻¹ − I| > ε).
• Provenance graph with coloured edges and ⚠ triangles/tetrahedra.
• CLI flags for node count, dimension, drift, k‑order, and CI fail.

Usage
-----
    python gerbe_edge_demo.py              # happy path
    python gerbe_edge_demo.py --drift 0.05 # inject 5 % drift
    python gerbe_edge_demo.py --k 4        # test tetrahedra
    python gerbe_edge_demo.py --fail-on-error

Dependencies: numpy, networkx, matplotlib
"""

import argparse
import itertools
import math
import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# ---------- Helpers ---------------------------------------------------------


def random_rotation(dim: int) -> np.ndarray:
    """Return a random dim × dim orthonormal matrix via QR decomposition."""
    A = np.random.randn(dim, dim)
    Q, _ = np.linalg.qr(A)
    return Q


def deep_close(a: np.ndarray, b: np.ndarray, tol: float = 1e-5) -> bool:
    return np.allclose(a, b, atol=tol)


def compose(M2: np.ndarray, M1: np.ndarray) -> np.ndarray:
    """Apply M1 then M2."""
    return M2 @ M1


def inverse_check(M: np.ndarray, tol: float = 1e-5) -> bool:
    """True if M·Mᵀ ≈ I (i.e. M is orthonormal within tol)."""
    return deep_close(M @ M.T, np.eye(M.shape[0]), tol)


# ---------- Obstruction detector -------------------------------------------


def obstruction_detector(
    contexts, morphisms, sample_vec, k: int = 3, tol: float = 1e-5
):
    """Return list of (context tuple, lhs, rhs) that violate consistency."""
    bad = []
    for combo in itertools.combinations(contexts, k):
        first, *_, last = combo
        # build chained matrix via successive composites
        M_chain = np.eye(sample_vec.shape[0])
        for a, b in zip(combo[:-1], combo[1:]):
            M_chain = compose(morphisms[(a, b)], M_chain)
        M_direct = morphisms[(first, last)]
        lhs = M_chain @ sample_vec
        rhs = M_direct @ sample_vec
        if not deep_close(lhs, rhs, tol):
            bad.append((combo, lhs, rhs))
    return bad


# ---------- Visualisation ---------------------------------------------------


def draw_graph(contexts, morphisms, inverses_ok, obstructions):
    G = nx.DiGraph()
    G.add_nodes_from(contexts)
    for src_dst in morphisms:
        G.add_edge(*src_dst)

    pos = nx.spring_layout(G, seed=7)
    plt.figure(figsize=(7, 5), constrained_layout=True)

    # Edge colours: red if inverse check failed
    edge_colors = [
        "red" if not inverses_ok[e] else "black" for e in G.edges()
    ]
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1800,
        font_size=10,
        edge_color=edge_colors,
        width=2,
    )
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels={e: f"{e[0]}→{e[1]}" for e in morphisms},
        font_size=8,
    )

    # Mark every failing simplex with ⚠
    for combo, *_ in obstructions:
        xs = [pos[n][0] for n in combo]
        ys = [pos[n][1] for n in combo]
        plt.text(
            sum(xs) / len(xs),
            sum(ys) / len(ys),
            "⚠",
            fontsize=20,
            ha="center",
            va="center",
        )

    plt.title("Edge‑Gerbe Provenance Graph")
    plt.axis("off")
    plt.show()


# ---------- Data generation -------------------------------------------------


def build_network(num_nodes: int, dim: int, drift: float):
    contexts = [f"Edge{i+1}" for i in range(num_nodes)]
    base_vec = np.zeros(dim)
    base_vec[0] = 1.0  # canonical embedding
    morphisms = {}

    # Create a spanning chain (Edge1→Edge2→…)
    for i in range(num_nodes - 1):
        morphisms[(contexts[i], contexts[i + 1])] = random_rotation(dim)

    # Derive all direct shortcuts (Edge_i → Edge_j) and optionally add drift
    for i in range(num_nodes):
        for j in range(i + 2, num_nodes):
            M_chain = np.eye(dim)
            for a, b in zip(contexts[i:j], contexts[i + 1 : j + 1]):
                M_chain = compose(morphisms[(a, b)], M_chain)
            if drift > 0:
                M_chain += drift * np.random.randn(dim, dim)
            morphisms[(contexts[i], contexts[j])] = M_chain

    return contexts, morphisms, base_vec


# ---------- CLI & main ------------------------------------------------------


def parse():
    p = argparse.ArgumentParser(description="Gerbe edge demo")
    p.add_argument("--nodes", type=int, default=4, help="number of edge devices")
    p.add_argument("--dim", type=int, default=64, help="embedding dimension")
    p.add_argument(
        "--drift",
        type=float,
        default=0.0,
        help="noise level added to shortcut transforms",
    )
    p.add_argument("--k", type=int, default=3, help="order of overlap to test")
    p.add_argument("--fail-on-error", action="store_true")
    return p.parse_args()


def main():
    args = parse()

    # Build synthetic edge network
    contexts, morphisms, sample = build_network(args.nodes, args.dim, args.drift)

    # Check each morphism's inverse quality
    inverses_ok = {edge: inverse_check(M) for edge, M in morphisms.items()}

    # Higher‑order obstruction test
    obstructions = obstruction_detector(
        contexts, morphisms, sample, k=args.k
    )

    # ----- Console output -----
    if obstructions:
        print("*** Obstructions detected! ***")
        for combo, *_ in obstructions:
            print("   ▸", " → ".join(combo))
    else:
        print("No obstruction detected.")

    bad_edges = [e for e, ok in inverses_ok.items() if not ok]
    if bad_edges:
        print("*** Non‑reversible edges (drift too large):", bad_edges)

    # ----- Provenance graph -----
    draw_graph(contexts, morphisms, inverses_ok, obstructions)

    # ----- CI gate -----
    if args.fail_on_error and (obstructions or bad_edges):
        sys.exit(1)


if __name__ == "__main__":
    main()
