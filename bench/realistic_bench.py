#!/usr/bin/env python
"""
realistic_bench.py
------------------
Generate a micro‑service‑style graph (~5 000 edges, ~30 000 triangles)
and measure Gerbe Core runtime and peak memory.

Usage:
    python realistic_bench.py --nodes 1000 --deg 10
"""

import argparse, tracemalloc, time, random, networkx as nx
import numpy as np
from gerbe_core import check_triangles

def make_graph(n, deg):
    ctx = [f"S{i}" for i in range(n)]
    G   = nx.DiGraph()
    mats = {}
    for _ in range(n * deg):
        a, b = random.sample(ctx, 2)
        if (a, b) in mats: continue
        mats[(a, b)] = np.eye(64)  # identity for perf test
        G.add_edge(a, b)
    return ctx, mats, G

def triangles(G):
    return [c for c in nx.enumerate_all_cliques(G.to_undirected()) if len(c)==3]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, default=1000)
    ap.add_argument("--deg",   type=int, default=10)
    args = ap.parse_args()

    ctx, mats, G = make_graph(args.nodes, args.deg)
    tris = triangles(G)
    print(f"{args.nodes=}  {args.deg=}  edges={len(mats):,}  triangles={len(tris):,}")

    tracemalloc.start()
    t0 = time.perf_counter()
    _ = check_triangles({"contexts":ctx,"mats":mats}, tol=0.30)  # numeric checker
    dt = time.perf_counter() - t0
    mem = tracemalloc.get_traced_memory()[1] / (1024*1024)
    tracemalloc.stop()

    print(f"Runtime {dt:,.2f} s   |   Peak RAM {mem:,.1f} MB")

if __name__ == "__main__":
    main()
