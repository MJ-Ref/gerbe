"""
gerbe_core.py
-------------
Tiny façade so CLI and benchmarks can import `check_triangles`.
Swap in the real library later.
"""

import itertools, numpy as np, networkx as nx

def _deep_close(a, b, rel_tol=0.30):
    diff = np.linalg.norm(a - b)
    base = np.linalg.norm(a)
    return diff / base < rel_tol if base else diff == 0

def _triangles(G):
    return (c for c in nx.enumerate_all_cliques(G) if len(c) == 3)

def check_triangles(graph, tol=0.30, changed_files=None):
    """
    Parameters
    ----------
    graph : dict with keys {contexts, mats, patches}
    tol   : relative Frobenius tolerance
    changed_files : optional set(str) -> restrict to affected edges
    Returns
    -------
    list[tuple(triangle, 'numeric'|'policy')]
    """
    ctx   = graph["contexts"]
    mats  = graph["mats"]
    patch = graph.get("patches", {})
    vec   = graph.get("base_vec", np.zeros(64))
    baseP = graph.get("base_policy", {})

    # If changed_files passed, prune edge sets (stub – expand later)
    if changed_files:
        mats  = {k:v for k,v in mats.items()  if any(f in k for f in changed_files)}
        patch = {k:v for k,v in patch.items() if any(f in k for f in changed_files)}

    G = nx.Graph(); G.add_edges_from(mats.keys())
    issues = []

    for a, b, c in _triangles(G):
        # numeric embedding check
        if all(k in mats for k in [(a,b),(b,c),(a,c)]):
            lhs = mats[(b,c)] @ (mats[(a,b)] @ vec)
            rhs = mats[(a,c)] @ vec
            if not _deep_close(lhs, rhs, tol):
                issues.append(((a,b,c), "numeric"))
        # policy JSON check
        if patch and all(k in patch for k in [(a,b),(b,c),(a,c)]):
            chain  = {**baseP, **patch[(a,b)], **patch[(b,c)]}
            direct = {**baseP, **patch[(a,c)]}
            if chain != direct:
                issues.append(((a,b,c), "policy"))

    return issues
