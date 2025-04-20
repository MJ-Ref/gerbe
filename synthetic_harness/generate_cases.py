#!/usr/bin/env python
"""
generate_cases.py
-----------------
Create a pickle dataset of random graphs with *known* injected
embedding + policy obstructions.

Each graph dict contains:
  contexts, mats, patches, base_vec, base_policy,
  emb_truth (list of triangles), pol_truth (list of triangles)
"""

import argparse, pickle, random, math
from typing import Dict, Tuple, List

import networkx as nx
import numpy as np

# --- utilities (place near top of generate_cases.py) -----------------
def triangles_with_edge(a, c, mats):
    """Return every node t that forms triangles (a,t,c) and (c,t,a)."""
    # Find nodes t such that (a, t) exists...
    neighbors_of_a = {t for (x, t) in mats if x == a and t != c}
    # ...and (t, c) also exists.
    ts = {t for t in neighbors_of_a if (t, c) in mats}
    return [tuple(sorted((a, t, c))) for t in ts]

# ---------------- basic helpers (clone from bench/full_demo) ---------------
def rot_matrix(dim: int) -> np.ndarray:
    q, _ = np.linalg.qr(np.random.randn(dim, dim))
    return q

def compose(m2: np.ndarray, m1: np.ndarray) -> np.ndarray:
    return m2 @ m1

# ---------------- synthetic graph generator --------------------------------
def synthetic_graph(n:int, dim:int, avg_deg:int):
    ctx = [f"N{i}" for i in range(n)]
    vec = np.zeros(dim); vec[0] = 1.0
    mats, patches = {}, {}
    G = nx.DiGraph()

    # 1. Spanning chain (consistent by construction)
    for i in range(n-1):
        m = rot_matrix(dim)  # Store matrix to calculate inverse easily
        mats[(ctx[i], ctx[i+1])] = m
        mats[(ctx[i+1], ctx[i])] = np.linalg.inv(m)      # NEW: reverse edge
        patches[(ctx[i], ctx[i+1])] = {}
        patches[(ctx[i+1], ctx[i])] = {}                # NEW
        G.add_edge(ctx[i], ctx[i+1])
        G.add_edge(ctx[i+1], ctx[i])                    # NEW

    # 2. Add random extra edges while preserving consistency
    # Target *pairs* of edges, will add forward and reverse for each
    target_edge_pairs = n * avg_deg
    num_edge_pairs = (len(mats) - (n-1)*2) // 2 # Current extra pairs (start with chain)

    while num_edge_pairs < target_edge_pairs:
        a, b = random.sample(ctx, 2)

        # Check if edge already exists in either direction OR if no path exists for composition
        # Use the G graph which now contains bidirectional edges for path finding
        # but the composition must follow a valid directed path using original edge matrices.
        # The original code assumed nx.has_path implies a composable path.
        if (a, b) in mats or (b, a) in mats or not nx.has_path(G, a, b):
            continue

        # compose along existing shortest path to maintain gluing
        # NOTE: shortest_path in the now-bidirectional G might include reverse edges.
        # The original logic relied on shortest_path finding a forward-composable path.
        # We retain this assumption.
        M = np.eye(dim)
        path_nodes = nx.shortest_path(G, a, b)
        try:
            for x, y in zip(path_nodes[:-1], path_nodes[1:]):
                # Ensure we are using the matrix corresponding to the path direction
                if (x, y) in mats:
                    M = compose(mats[(x, y)], M)
                else:
                    # This should not happen if shortest_path finds a valid forward path
                    # based on the initial graph structure. If it does, skip this edge pair.
                    print(f"Warning: shortest path {path_nodes} for {(a,b)} seems invalid, edge skipped.")
                    raise ValueError("Invalid path segment")
        except ValueError:
            continue # Skip this edge pair if composition fails

        mats[(a, b)] = M
        mats[(b, a)] = np.linalg.inv(M)                 # NEW
        patches[(a, b)] = {}
        patches[(b, a)] = {}                            # NEW
        G.add_edge(a, b)
        # G.add_edge(b, a) # This is redundant now, added in the loop start
        # Corrected: G already has (b,a) from the spanning chain or previous iterations,
        # but we need to ensure it's explicitly added if this is the first time
        # However, the spanning chain already added all nodes and reverse edges.
        # Let's ensure G reflects the added shortcut edge regardless.
        G.add_edge(b, a)                               # Ensure reverse edge is in G explicitly

        num_edge_pairs += 1 # Increment count of edge pairs added

    return ctx, mats, patches, vec, {"pii_allowed": False, "age_limit": 13}, G


DRIFT = 0.5          # How much to perturb matrices for embedding obstructions

# -------------- inject obstruction helpers ---------------------------------
def inject_embedding_obstruction(tri, mats, vec):
    a, b, c = tri
    if not all(k in mats for k in [(a, b), (b, c), (a, c)]):
        return False
    chain   = mats[(b, c)] @ mats[(a, b)]
    drifted = chain + DRIFT * np.random.randn(*chain.shape)
    mats[(a, c)] = drifted
    mats[(c, a)] = np.linalg.inv(drifted)      # ← keeps reverse edge consistent
    return True


def inject_policy_obstruction(tri, patches):
    a,b,c = tri
    if not all(k in patches for k in [(a,b),(b,c),(a,c)]): return False
    patch = {"age_limit": random.choice([15,16,18])}
    patches[(a,c)] = patch
    patches[(c,a)] = patch.copy()               # <-- keep symmetric
    return True

# ------------------ main ---------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-graphs", type=int, default=1000)
    ap.add_argument("--min-nodes", type=int, default=100)
    ap.add_argument("--max-nodes", type=int, default=300)
    ap.add_argument("--dim", type=int, default=64)
    ap.add_argument("--out", default="dataset.pkl")
    args = ap.parse_args()

    dataset=[]
    for gid in range(args.n_graphs):
        n = random.randint(args.min_nodes, args.max_nodes)
        ctx,mats,patches,vec,base_policy,G = synthetic_graph(n,args.dim,avg_deg=4)
        triangles=[clq for clq in nx.enumerate_all_cliques(G.to_undirected()) if len(clq)==3]
        random.shuffle(triangles)

        # Filter for triangles with all edges present in the directed graph
        directed_triangles = [
            tri for tri in triangles
            if all(k in mats for k in [(tri[0], tri[1]),
                                       (tri[1], tri[2]),
                                       (tri[0], tri[2])])
        ]
        random.shuffle(directed_triangles)

        emb_truth=[]
        pol_truth=[]
        # inject 1‑3 embedding obstructions in the first few directed triangles
        for tri in directed_triangles[: random.randint(1,3)]:
            a, b, c = tri # Capture the triangle nodes for the edge (a,c)
            if inject_embedding_obstruction(tri,mats,vec):
                # NEW: add every triangle that uses the drifted edge (a,c)
                emb_truth.extend(triangles_with_edge(a, c, mats))

        # inject 1‑2 policy obstructions (different triangles)
        # Use remaining directed triangles to avoid overlap with embedding obstructions
        start_idx = random.randint(1, 3) # Where embedding obstructions stopped
        for tri in directed_triangles[start_idx : start_idx + random.randint(1,2)]:
            a, b, c = tri # Capture the triangle nodes for the edge (a,c)
            if inject_policy_obstruction(tri,patches):
                # NEW: add every triangle that uses the edge (a,c) whose policy was patched
                pol_truth.extend(triangles_with_edge(a, c, mats))

        # Deduplicate truth sets
        emb_truth = list(set(emb_truth))
        pol_truth = list(set(pol_truth))

        dataset.append({
            "contexts":ctx,
            "mats":mats,
            "patches":patches,
            "base_vec":vec,
            "base_policy":base_policy,
            "emb_truth":emb_truth,
            "pol_truth":pol_truth
        })
        if (gid+1)%100==0:
            print(f"generated {gid+1}/{args.n_graphs}")

    with open(args.out,"wb") as f:
        pickle.dump(dataset,f)
    print(f"Saved dataset to {args.out} ({len(dataset)} graphs)")

if __name__=="__main__":
    main()
