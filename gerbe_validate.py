
"""
gerbe_validate.py
-----------------
Thin wrapper around Gerbe Core that DevOps can drop into any CI.

Example:
    # warn‑only pass
    python gerbe_validate.py --config contexts.yaml --mode warn

    # block PR if any global inconsistency
    python gerbe_validate.py --config contexts.yaml --mode block --tolerance 0.30
"""

import argparse, sys, yaml, json
import numpy as np, pathlib, warnings  # Added imports
from gerbe_core import check_triangles   # <- you already have this function

def load_contexts(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# Added helper function
def config_to_runtime(cfg):
    """Turn YAML config into the dict expected by check_triangles()."""
    mats, patches = {}, {}
    for edge in cfg["edges"]:
        a, b = edge["src"], edge["dst"]

        # load numeric matrix if path exists; else identity
        mat_path = edge.get("matrix")
        if mat_path and pathlib.Path(mat_path).exists():
            mats[(a, b)] = np.load(mat_path)
        else:
            warnings.warn(f"No matrix for {a}->{b}; using identity")
            mats[(a, b)] = np.eye(64) # Assuming identity size, adjust if needed

        # inverse matrix
        inv_path = edge.get("inverse")
        if inv_path and pathlib.Path(inv_path).exists():
            mats[(b, a)] = np.load(inv_path)
        elif (a,b) in mats: # Check if forward matrix was loaded or created
             try:
                 mats[(b, a)] = np.linalg.inv(mats[(a, b)])
             except np.linalg.LinAlgError:
                 warnings.warn(f"Matrix for {a}->{b} is singular; cannot compute inverse.")
                 # Decide on fallback? Using identity for now.
                 mats[(b, a)] = np.eye(64) # Assuming identity size
        else:
             # If neither forward nor inverse exists, create identity for inverse too
             warnings.warn(f"No inverse matrix for {b}->{a}; using identity")
             mats[(b, a)] = np.eye(64) # Assuming identity size

        # policy patch (optional JSON)
        patch_path = edge.get("patch")
        if patch_path and pathlib.Path(patch_path).exists():
            with open(patch_path, 'r') as f: # Ensure file is closed
                 patches[(a, b)] = json.load(f)
            # Assuming patches are symmetric or handle asymmetry if needed
            # patches[(b, a)] = patches[(a, b)].copy() # Re-evaluate if this is correct logic

    return {
        "contexts": cfg["nodes"],
        "mats": mats,
        "patches": patches,
        "base_vec": np.eye(64)[0]          # = [1,0,0,…]
        # for even stronger coverage you can use:
        # "base_vec": np.random.default_rng(42).normal(size=64)
    }

def main():
    ap = argparse.ArgumentParser(description="Gerbe consistency gate")
    ap.add_argument("--config", required=True,
                    help="YAML defining nodes, edges, file‑globs")
    ap.add_argument("--mode", choices=["warn", "block"], default="warn",
                    help="'warn' prints issues; 'block' exits non‑zero")
    ap.add_argument("--tolerance", type=float, # Use graph tolerance if not specified
                    help="Relative L2 tolerance for numeric checks")
    ap.add_argument("--changed", nargs="*",
                    help="Optional list of files changed (limits scope)")
    args = ap.parse_args()

    graph_cfg = load_contexts(args.config)
    # Use helper to convert config to runtime structure
    runtime = config_to_runtime(graph_cfg)

    # Use config tolerance if CLI flag omitted
    tolerance = args.tolerance if args.tolerance is not None else graph_cfg.get('tolerance', 0.30)

    results = check_triangles(runtime, tol=tolerance,
                              changed_files=args.changed)

    if not results:          # everything glued
        print("✅  Gerbe gate: no inconsistencies")
        return

    # pretty print issues
    print("\n⚠  Gerbe found inconsistencies:")
    for tri, kind in results:
        print(f"   • {tri}   ({kind})")

    if args.mode == "block":
        sys.exit(1)          # fail CI
    else:
        print("\n   (mode=warn – CI passes)")

if __name__ == "__main__":
    main()
