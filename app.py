# app.py  –  Gerbe sandbox demo
import streamlit as st, numpy as np, networkx as nx, matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Gerbe triangle validator", page_icon="🌾")

st.title("🌾  Gerbe sandbox — local→global checker")

# --- sidebar inputs -------------------------------------------------------
st.sidebar.header("Contexts")
a = st.sidebar.text_input("Context A", "US")
b = st.sidebar.text_input("Context B", "EU")
c = st.sidebar.text_input("Context C", "GLOBAL")

st.sidebar.header("Upload matrices (.npy)")
file_ab = st.sidebar.file_uploader(f"{a} → {b}",   type=".npy")
file_bc = st.sidebar.file_uploader(f"{b} → {c}",   type=".npy")
file_ac = st.sidebar.file_uploader(f"{a} → {c}",   type=".npy (optional)")

rel_tol = st.sidebar.slider("Relative tolerance ε", 0.01, 1.0, 0.30, 0.01)

# --- helpers --------------------------------------------------------------
def load_npy(file, dim):
    if file is None:
        return np.eye(dim)           # missing ⇒ identity
    return np.load(BytesIO(file.read()))

def deep_close(lhs, rhs, tol):
    diff = np.linalg.norm(lhs - rhs)
    base = np.linalg.norm(lhs)
    return diff / base < tol if base else diff == 0, diff / base

# --- main action ----------------------------------------------------------
if st.button("Validate ▶"):
    if file_ab is None or file_bc is None:
        st.error("Please upload at least A→B and B→C matrices.")
        st.stop()

    # load matrices
    M_ab = load_npy(file_ab, 64)
    M_bc = load_npy(file_bc, 64)
    M_ac = load_npy(file_ac, 64) if file_ac else np.eye(64)

    comp = M_bc @ M_ab              # path A→B→C
    ok, rel_err = deep_close(comp, M_ac, rel_tol)

    # --- result text ------------------------------------------------------
    if ok:
        st.success(f"✔  Triangle is consistent  (relative error {rel_err:.3f} < ε={rel_tol})")
    else:
        st.error(f"⚠  Obstruction detected!  (relative error {rel_err:.3f} ≥ ε={rel_tol})")

    # --- provenance graph -------------------------------------------------
    G = nx.DiGraph()
    G.add_edge(a, b); G.add_edge(b, c); G.add_edge(a, c)
    pos = nx.spring_layout(G, seed=7)
    fig, ax = plt.subplots()
    nx.draw(G, pos, with_labels=True, node_size=1200,
            edge_color=["black","black","red" if not ok else "black"],
            width=2, ax=ax)
    edge_lbls = {(a,b):f"{a}→{b}", (b,c):f"{b}→{c}", (a,c):f"{a}→{c}"}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_lbls, font_size=8, ax=ax)
    ax.set_axis_off()
    st.pyplot(fig)

    st.caption("Relative Frobenius error on composed vs shortcut matrix.")

# --- footer ---------------------------------------------------------------
st.markdown("---\nGerbe sandbox &nbsp;•&nbsp; "
            "[GitHub](https://github.com/your‑org/gerbe) "
            " •  Mathematical guarantee, plain‑English UX.")
