#!/usr/bin/env python
"""
bench/01_scalability.py
=======================
Stress‑test Gerbe’s triangle‑obstruction check.

It benchmarks two algorithms:

• baseline_brute  – checks ALL triples (O(n³))
• edge_pruned     – enumerates only existing triangles in the graph
                    via NetworkX; expected to scale far better.

Outputs:
  nodes, dim, edges, triangles, baseline_sec, pruned_sec, peak_MB

If --out FILE is supplied, rows are appended to FILE in CSV format.

Usage
-----
# Single run (200 nodes, 128‑D, avg deg 4)
python bench/01_scalability.py --nodes 200 --dim 128 --deg 4

# Sweep 100→600 nodes in steps of 100
python bench/01_scalability.py --sweep --out sweep.csv
"""

import argparse
import csv
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np
import psutil

process = psutil.Process(os.getpid())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def rot_matrix(dim: int) -> np.ndarray:
    q, _ = np.linalg.qr(np.random.randn(dim, dim))
    return q


def deep_close(a: np.ndarray, b: np.ndarray, tol: float = 1e-6) -> bool:
    return np.allclose(a, b, atol=tol)


def compose(m2: np.ndarray, m1: np.ndarray) -> np.ndarray:
    return m2 @ m1


# ---------------------------------------------------------------------------
# Synthetic graph generator
# ---------------------------------------------------------------------------
def synthetic_graph(
    n: int, dim: int, avg_deg: int
) -> Tuple[List[str], Dict[Tuple[str, str], np.ndarray], np.ndarray, nx.Graph]:
    nodes = [f"N{i}" for i in range(n)]
    vec = np.zeros(dim)
    vec[0] = 1.0
    mats = {}
    G = nx.DiGraph()

    target_edges = n * avg_deg
    while len(mats) < target_edges:
        a, b = random.sample(nodes, 2)
        if (a, b) in mats:
            continue
        mats[(a, b)] = rot_matrix(dim)
        G.add_edge(a, b)
    return nodes, mats, vec, G


# ---------------------------------------------------------------------------
# Obstruction algorithms
# ---------------------------------------------------------------------------
def obstruction_baseline(
    nodes: List[str],
    mats: Dict[Tuple[str, str], np.ndarray],
    vec: np.ndarray,
) -> int:
    bad = 0
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                a, b, c = nodes[i], nodes[j], nodes[k]
                if all(k in mats for k in [(a, b), (b, c), (a, c)]):
                    lhs = mats[(b, c)] @ (mats[(a, b)] @ vec)
                    rhs = mats[(a, c)] @ vec
                    if not deep_close(lhs, rhs):
                        bad += 1
    return bad


def obstruction_edge_pruned(
    mats: Dict[Tuple[str, str], np.ndarray],
    vec: np.ndarray,
    graph: nx.Graph,
) -> int:
    bad = 0
    triangles = (
        clq for clq in nx.enumerate_all_cliques(graph.to_undirected()) if len(clq) == 3
    )
    for a, b, c in triangles:
        if all(k in mats for k in [(a, b), (b, c), (a, c)]):
            lhs = mats[(b, c)] @ (mats[(a, b)] @ vec)
            rhs = mats[(a, c)] @ vec
            if not deep_close(lhs, rhs):
                bad += 1
    return bad


# ---------------------------------------------------------------------------
# CSV helper
# ---------------------------------------------------------------------------
def write_row(csv_path: str, row: list[str]):
    file = Path(csv_path)
    write_header = not file.exists()
    with file.open("a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(
                [
                    "nodes",
                    "dim",
                    "edges",
                    "triangles",
                    "baseline_sec",
                    "pruned_sec",
                    "peak_MB",
                ]
            )
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Benchmark per run
# ---------------------------------------------------------------------------
def bench_once(n: int, dim: int, deg: int, csv_path: str | None):
    nodes, mats, vec, G = synthetic_graph(n, dim, deg)

    def run(fn):
        start = time.time()
        _ = fn(nodes, mats, vec) if fn == obstruction_baseline else fn(mats, vec, G)
        rt = time.time() - start
        mem_mb = process.memory_info().rss / (1024 * 1024)
        return rt, mem_mb

    t1, m1 = run(obstruction_baseline)
    t2, m2 = run(obstruction_edge_pruned)

    tri = sum(nx.triangles(nx.Graph(G)).values()) // 3
    print(
        f"{n:>4} nodes | {dim:>3}‑D | "
        f"{len(mats):>5} edges | {tri:>7} triangles | "
        f"baseline {t1:6.2f}s {m1:6.1f}MB | "
        f"pruned {t2:6.2f}s {m2:6.1f}MB"
    )

    if csv_path:
        write_row(
            csv_path,
            [
                n,
                dim,
                len(mats),
                tri,
                f"{t1:.2f}",
                f"{t2:.2f}",
                f"{max(m1, m2):.1f}",
            ],
        )


def sweep(deg: int, csv_path: str | None):
    print("nodes | triangles | baseline_s | pruned_s")
    for n in range(100, 601, 100):
        nodes, mats, vec, G = synthetic_graph(n, 64, avg_deg=deg)
        tri = sum(nx.triangles(nx.Graph(G)).values()) // 3

        def runtime(fn):
            start = time.time()
            _ = fn(nodes, mats, vec) if fn == obstruction_baseline else fn(mats, vec, G)
            return time.time() - start

        b = runtime(obstruction_baseline)
        p = runtime(obstruction_edge_pruned)
        print(f"{n:<5} | {tri:<10} | {b:<11.2f} | {p:<8.2f}")

        if csv_path:
            write_row(csv_path, [n, 64, len(mats), tri, f"{b:.2f}", f"{p:.2f}", "NA"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gerbe scalability benchmark")
    ap.add_argument("--nodes", type=int, default=200)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--deg", type=int, default=4, help="avg out‑degree per node")
    ap.add_argument("--sweep", action="store_true", help="run 100‑>600 node sweep")
    ap.add_argument(
        "--out",
        default=None,
        help="CSV file to append benchmark results (optional)",
    )
    args = ap.parse_args()

    if args.sweep:
        sweep(args.deg, args.out)
    else:
        bench_once(args.nodes, args.dim, args.deg, args.out)

