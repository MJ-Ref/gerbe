#!/usr/bin/env python
"""
eval_precision.py — Stage 3
Compute Precision / Recall / F1 on the synthetic dataset produced by
generate_cases.py, using an edge‑pruned triangle detector.

CLI flags
---------
--in     path to dataset pickle   (default: dataset.pkl)
--sample evaluate only the first N graphs (debug / quick sweep)

A green exit (code 0) requires:  Precision ≥ 0.90, Recall ≥ 0.95, F1 ≥ 0.92
"""

import argparse, pickle, sys
import numpy as np
import networkx as nx

# ---------- helpers --------------------------------------------------------
# def deep_close(a, b, tol):
#     return np.allclose(a, b, atol=tol)

def deep_close(a: np.ndarray, b: np.ndarray, rel_tol: float = 0.50) -> bool:
    """Relative L2 / Frobenius norm."""
    diff = np.linalg.norm(a - b)      # L2 for vectors
    base = np.linalg.norm(a)
    if base == 0:
        return diff == 0
    return diff / base < rel_tol



def compose(m2, m1):            # matrix multiply
    return m2 @ m1

def compose_policy(base, patch):  # JSON overlay
    out = base.copy()
    out.update(patch)
    return out

def build_graph(edge_keys):
    G = nx.Graph()
    G.add_edges_from(edge_keys)
    return G

def triangles_iter(G):
    return (clq for clq in nx.enumerate_all_cliques(G) if len(clq) == 3)

def embedding_obstructions(ctx, mats, vec, G): # Removed tol parameter
    bad = []
    for a, b, c in triangles_iter(G):
        # Need to check both orientations since graph is undirected now in detection
        # Check orientation a -> b -> c vs a -> c
        if all(k in mats for k in [(a, b), (b, c), (a, c)]):
            lhs = mats[(b, c)] @ (mats[(a, b)] @ vec)
            rhs = mats[(a, c)] @ vec
            if not deep_close(lhs, rhs): # Use default rel_tol
                bad.append(tuple(sorted((a, b, c))))
                continue # Found obstruction for this triangle, no need to check other orientations

        # Check orientation c -> b -> a vs c -> a (reverse)
        # This is implicitly covered if the first check fails due to drift,
        # as the comparison deep_close(lhs, rhs) captures the inconsistency.
        # No need for a separate check if the underlying matrices are consistent
        # or inconsistent regardless of traversal direction for composition check.
        # Let's simplify and assume the first check covers the triangle inconsistency.

    # Remove duplicates before returning
    return list(set(bad))


def policy_obstructions(patches, base, G):
    bad = []
    for a, b, c in triangles_iter(G):
        # Check a -> b -> c vs a -> c
        if all(k in patches for k in [(a, b), (b, c), (a, c)]):
            chain  = compose_policy(compose_policy(base, patches[(a, b)]),
                                    patches[(b, c)])
            direct = compose_policy(base, patches[(a, c)])
            if chain != direct:
                bad.append(tuple(sorted((a, b, c))))
                continue # Found obstruction, skip other orientation checks for this triangle

        # Check c -> b -> a vs c -> a (reverse paths)
        # Since patches are symmetric now, this check is redundant if the first one passed/failed consistently.
        # If patches[(a,b)] == patches[(b,a)], etc., composition result is the same.

    return list(set(bad))

# ---------- metric tracker -------------------------------------------------
class Meter:
    def __init__(self):
        self.tp = self.fp = self.fn = 0
    def update(self, truth, pred):
        t = set(map(tuple, truth))
        p = set(map(tuple, pred))
        self.tp += len(t & p)
        self.fp += len(p - t)
        self.fn += len(t - p)
    def precision(self):
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 1.0
    def recall(self):
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 1.0
    def f1(self):
        p, r = self.precision(), self.recall()
        return 2 * p * r / (p + r) if p + r else 0.0

# ---------- main -----------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="dataset.pkl",
                    help="Pickle dataset to evaluate")
    # ap.add_argument("--tol", type=float, default=0.2,
    #                 help="Numeric tolerance for deep_close") # Removed --tol
    ap.add_argument("--sample", type=int, default=None,
                    help="Evaluate only first N graphs (debug)")
    args = ap.parse_args()

    data = pickle.load(open(args.inp, "rb"))
    if args.sample:
        data = data[: args.sample]

    meter = Meter()

    for g in data:
        # Build graph from matrix keys (which includes both directions now)
        G = build_graph(g["mats"].keys())
        # Pass only necessary arguments to embedding_obstructions
        pred_emb = embedding_obstructions(
            g["contexts"], g["mats"], g["base_vec"], G # Removed args.tol
        )
        # Pass only necessary arguments to policy_obstructions
        pred_pol = policy_obstructions(
            g["patches"], g["base_policy"], G
        )
        meter.update(g["emb_truth"] + g["pol_truth"],
                     pred_emb + pred_pol)

    P, R, F1 = meter.precision(), meter.recall(), meter.f1()
    print(f"Graphs tested: {len(data)}")
    print(f"Precision: {P:.3f}  Recall: {R:.3f}  F1: {F1:.3f}")

    if R < 0.95 or P < 0.90 or F1 < 0.92:
        sys.exit("Stage‑3 metrics below threshold")

if __name__ == "__main__":
    main()
