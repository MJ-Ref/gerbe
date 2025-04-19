"""
gerbe_full_demo.py
==================
Ambitious “all‑in‑one” demonstration of gerbe‑style local‑to‑global
validation over BOTH numeric embeddings *and* JSON‑style policy blobs.

Highlights
----------
• N nodes (default = 6) with D‑dim embeddings (default = 64)
• Random orthonormal matrices as reversible transforms
• Optional *numeric* drift  (`--drift`)        – simulates stale weights
• Optional *policy*  drift  (`--policy-drift`) – simulates rule skew
• k‑simplex obstruction detector  +  inverse sanity check
• Provenance graph (black = OK, red = bad inverse,
  ⚠ = embedding obstruction, ✖ = policy obstruction)
• `--report`  ➜  writes **JSON + PNG + self‑contained HTML** to ./reports/
• `--fail-on-error`  ➜  CI‑friendly exit 1 if any inconsistency exists
"""

# ---------------------------------------------------------------------------
# Imports & globals
# ---------------------------------------------------------------------------
import argparse
import base64
import itertools
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def rot_matrix(dim: int) -> np.ndarray:
    """Random orthonormal rotation via QR."""
    Q, _ = np.linalg.qr(np.random.randn(dim, dim))
    return Q


def deep_close(a: np.ndarray, b: np.ndarray, tol: float = 1e-5) -> bool:
    return np.allclose(a, b, atol=tol)


def compose(M2: np.ndarray, M1: np.ndarray) -> np.ndarray:
    """Apply M1 then M2 (matrix mult)."""
    return M2 @ M1


def inverse_ok(M: np.ndarray, tol: float = 1e-5) -> bool:
    """Check orthonormality."""
    return deep_close(M @ M.T, np.eye(M.shape[0]), tol)


def compose_policy(base: Dict, patch: Dict) -> Dict:
    """Overlay patch dict onto base dict (immutable)."""
    out = base.copy()
    out.update(patch)
    return out


# ---------------------------------------------------------------------------
# Obstruction detection
# ---------------------------------------------------------------------------
def embedding_obstructions(
    contexts: List[str],
    mats: Dict[Tuple[str, str], np.ndarray],
    vec: np.ndarray,
    k: int = 3,
    tol: float = 1e-5,
):
    bad = []
    for combo in itertools.combinations(contexts, k):
        first, *_, last = combo
        chain = np.eye(vec.shape[0])
        for a, b in zip(combo[:-1], combo[1:]):
            chain = compose(mats[(a, b)], chain)
        lhs = chain @ vec
        rhs = mats[(first, last)] @ vec
        if not deep_close(lhs, rhs, tol):
            bad.append(combo)
    return bad


def policy_obstructions(
    contexts: List[str],
    patches: Dict[Tuple[str, str], Dict],
    base: Dict,
    k: int = 3,
):
    bad = []
    for combo in itertools.combinations(contexts, k):
        first, *_, last = combo
        pol_chain = base
        for a, b in zip(combo[:-1], combo[1:]):
            pol_chain = compose_policy(pol_chain, patches[(a, b)])
        pol_direct = compose_policy(base, patches[(first, last)])
        if pol_chain != pol_direct:
            bad.append(combo)
    return bad


# ---------------------------------------------------------------------------
# Graph drawing
# ---------------------------------------------------------------------------
def draw_graph(
    contexts,
    mats,
    inv_ok,
    emb_bad,
    pol_bad,
    outfile: str | None = None,
):
    G = nx.DiGraph()
    G.add_nodes_from(contexts)
    G.add_edges_from(mats.keys())
    pos = nx.spring_layout(G, seed=8)

    plt.figure(figsize=(8, 6), constrained_layout=True)
    edge_colors = ["red" if not inv_ok[e] else "black" for e in G.edges()]
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=2000,
        font_size=10,
        edge_color=edge_colors,
        width=2,
    )
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels={e: f"{e[0]}→{e[1]}" for e in mats},
        font_size=7,
    )

    def mark(combo, symbol, color):
        xs = [pos[n][0] for n in combo]
        ys = [pos[n][1] for n in combo]
        plt.text(
            sum(xs) / len(xs),
            sum(ys) / len(ys),
            symbol,
            fontsize=20,
            ha="center",
            va="center",
            color=color,
        )

    for c in emb_bad:
        mark(c, "⚠", "orange")
    for c in pol_bad:
        mark(c, "✖", "purple")

    plt.title("Gerbe AI — provenance graph")
    plt.axis("off")
    if outfile:
        plt.savefig(outfile, dpi=150)
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Synthetic network generator
# ---------------------------------------------------------------------------
def build_network(
    n: int,
    dim: int,
    drift: float,
    policy_drift_chance: float,
):
    ctx = [f"Node{i+1}" for i in range(n)]
    base_vec = np.zeros(dim)
    base_vec[0] = 1.0
    base_policy = {"pii_allowed": False, "age_limit": 13}

    mats, patches = {}, {}

    # spanning chain
    for i in range(n - 1):
        mats[(ctx[i], ctx[i + 1])] = rot_matrix(dim)
        patches[(ctx[i], ctx[i + 1])] = {}

    # shortcuts + optional drift
    for i in range(n):
        for j in range(i + 2, n):
            M = np.eye(dim)
            for a, b in zip(ctx[i:j], ctx[i + 1 : j + 1]):
                M = compose(mats[(a, b)], M)
            if drift:
                M += drift * np.random.randn(dim, dim)
            mats[(ctx[i], ctx[j])] = M

            patch = {}
            if random.random() < policy_drift_chance:
                patch["age_limit"] = random.choice([15, 16, 18])
            patches[(ctx[i], ctx[j])] = patch

    return ctx, mats, patches, base_vec, base_policy


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def get_args():
    p = argparse.ArgumentParser(description="Gerbe full‑stack demo")
    p.add_argument("--nodes", type=int, default=6)
    p.add_argument("--dim", type=int, default=64)
    p.add_argument("--drift", type=float, default=0.0,
                   help="numeric drift magnitude (0‑1)")
    p.add_argument("--policy-drift", type=float, default=0.0,
                   help="probability a shortcut mutates policy")
    p.add_argument("--k", type=int, default=3,
                   help="simplex order to test (3=triangles)")
    p.add_argument("--report", action="store_true",
                   help="write JSON + PNG + HTML to ./reports/")
    p.add_argument("--fail-on-error", action="store_true")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = get_args()
    ctx, mats, patches, base_vec, base_policy = build_network(
        args.nodes, args.dim, args.drift, args.policy_drift
    )

    inv_ok = {e: inverse_ok(M) for e, M in mats.items()}
    emb_bad = embedding_obstructions(ctx, mats, base_vec, k=args.k)
    pol_bad = policy_obstructions(ctx, patches, base_policy, k=args.k)
    bad_edges = [e for e, ok in inv_ok.items() if not ok]

    # ---------------- Console summary ----------------
    if any([emb_bad, pol_bad, bad_edges]):
        print("=== Inconsistencies detected ===")
    if emb_bad:
        print(f"Embedding obstructions (k={args.k}):")
        for c in emb_bad:
            print("  ⚠", " → ".join(c))
    if pol_bad:
        print(f"Policy obstructions (k={args.k}):")
        for c in pol_bad:
            print("  ✖", " → ".join(c))
    if bad_edges:
        print("Non‑reversible transforms:", bad_edges)
    if not (emb_bad or pol_bad or bad_edges):
        print("No obstruction detected.")

    # ---------------- Artefact generation ----------------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    png_path = REPORT_DIR / f"{timestamp}.png" if args.report else None

    draw_graph(ctx, mats, inv_ok, emb_bad, pol_bad,
               outfile=str(png_path) if png_path else None)

    if args.report:
        json_path = REPORT_DIR / f"{timestamp}.json"
        with json_path.open("w") as jf:
            json.dump({
                "timestamp": timestamp,
                "nodes": ctx,
                "bad_inverse_edges": bad_edges,
                "embedding_obstructions": emb_bad,
                "policy_obstructions": pol_bad,
                "k": args.k,
                "numeric_drift": args.drift,
                "policy_drift_prob": args.policy_drift
            }, jf, indent=2)
        print(f"JSON  →  {json_path}")

        # HTML one‑pager
        html_path = REPORT_DIR / f"{timestamp}.html"
        b64_png = base64.b64encode(png_path.read_bytes()).decode() if png_path else ""
        html = f"""
        <html><head><title>Gerbe Report {timestamp}</title>
        <style>
            body{{font-family:Arial, sans-serif;}}
            summary{{cursor:pointer;font-weight:bold;margin-top:1em;}}
            img{{max-width:100%;border:1px solid #888;}}
        </style></head><body>
        <h2>Gerbe AI Consistency Report — {timestamp}</h2>
        {"<img src='data:image/png;base64," + b64_png + "'/>" if b64_png else ""}
        <details open><summary>JSON details</summary>
        <pre>{json.dumps(json.loads(json_path.read_text()), indent=2)}</pre>
        </details>
        </body></html>
        """
        html_path.write_text(html, encoding="utf-8")
        print(f"HTML →  {html_path}")

    # ---------------- CI gate ----------------
    if args.fail_on_error and (emb_bad or pol_bad or bad_edges):
        sys.exit(1)


if __name__ == "__main__":
    main()

