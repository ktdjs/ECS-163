#!/usr/bin/env python3
"""
GO Enrichment Network Graph
────────────────────────────
Loads go_enrichment_results.tsv and builds an interactive force-directed
network where:
  • Nodes  = significant GO terms
  • Node size ∝ number of study genes
  • Node colour = namespace (BP / MF / CC)
  • Edges = two GO terms share ≥ MIN_SHARED genes → edge weight = Jaccard index
  • Hover shows term name, gene count, top genes

Run:
    python go_network_graph.py
Output:
    results/go_enrichment_network.html
"""

import os
import ast
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go_plotly
import networkx as nx

# ── Paths ─────────────────────────────────────────────────────────────────────
script_dir  = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, "results")
tsv_path    = os.path.join(results_dir, "go_enrichment_results.tsv")

# ── Config ────────────────────────────────────────────────────────────────────
MIN_SHARED  = 3      # minimum shared genes to draw an edge
TOP_TERMS   = 120    # keep only the N most significant terms per namespace for clarity
SEED        = 42

NS_COLORS = {
    "biological_process": "#3b82f6",   # blue
    "molecular_function": "#ef4444",   # red
    "cellular_component": "#22c55e",   # green
}
NS_LABELS = {
    "biological_process": "Biological Process",
    "molecular_function": "Molecular Function",
    "cellular_component": "Cellular Component",
}

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(tsv_path, sep="\t")
df["study_genes"] = df["study_genes"].apply(ast.literal_eval)

# Keep top N per namespace by significance
parts = []
for ns in NS_COLORS:
    sub = df[df["class"] == ns].sort_values("p_corr").head(TOP_TERMS)
    parts.append(sub)
df = pd.concat(parts, ignore_index=True)
print(f"Building network from {len(df)} GO terms …")

# ── Build gene sets ───────────────────────────────────────────────────────────
term_genes  = {row["GO"]: set(row["study_genes"]) for _, row in df.iterrows()}
term_meta   = {row["GO"]: row for _, row in df.iterrows()}

# ── Build graph ───────────────────────────────────────────────────────────────
G = nx.Graph()

for go_id, meta in term_meta.items():
    G.add_node(
        go_id,
        label    = meta["term"],
        ns       = meta["class"],
        n_genes  = meta["n_genes"],
        p_corr   = meta["p_corr"],
        genes    = sorted(term_genes[go_id]),
    )

go_ids = list(term_genes.keys())
for i in range(len(go_ids)):
    for j in range(i + 1, len(go_ids)):
        a, b = go_ids[i], go_ids[j]
        shared = term_genes[a] & term_genes[b]
        if len(shared) >= MIN_SHARED:
            union   = term_genes[a] | term_genes[b]
            jaccard = len(shared) / len(union) if union else 0
            G.add_edge(a, b, weight=jaccard, shared=len(shared))

print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

# ── Layout ────────────────────────────────────────────────────────────────────
# Use Fruchterman-Reingold; seed for reproducibility.
pos = nx.spring_layout(G, weight="weight", seed=SEED, k=0.35, iterations=80)

# ── Build Plotly traces ───────────────────────────────────────────────────────

# --- Edges ---
edge_x, edge_y, edge_alpha = [], [], []
for u, v, data in G.edges(data=True):
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]
    edge_alpha.append(data["weight"])

edge_trace = go_plotly.Scatter(
    x=edge_x, y=edge_y,
    mode="lines",
    line=dict(width=0.7, color="rgba(150,150,150,0.35)"),
    hoverinfo="none",
    showlegend=False,
)

# --- Nodes (one trace per namespace for legend) ---
node_traces = []
for ns, color in NS_COLORS.items():
    ns_nodes = [n for n, d in G.nodes(data=True) if d["ns"] == ns]
    if not ns_nodes:
        continue

    node_x = [pos[n][0] for n in ns_nodes]
    node_y = [pos[n][1] for n in ns_nodes]
    sizes  = [max(10, min(50, math.log2(G.nodes[n]["n_genes"] + 1) * 7))
              for n in ns_nodes]

    # Build hover text
    hover = []
    for n in ns_nodes:
        d = G.nodes[n]
        top_g = ", ".join(d["genes"][:12])
        if len(d["genes"]) > 12:
            top_g += f" … (+{len(d['genes'])-12} more)"
        hover.append(
            f"<b>{d['label']}</b><br>"
            f"{n}<br>"
            f"Genes: {d['n_genes']}<br>"
            f"FDR: {d['p_corr']:.2e}<br>"
            f"<i>{top_g}</i>"
        )

    node_traces.append(go_plotly.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=sizes,
            color=color,
            opacity=0.85,
            line=dict(width=0.8, color="white"),
        ),
        text=[G.nodes[n]["label"] if G.nodes[n]["n_genes"] > 40 else ""
              for n in ns_nodes],
        textfont=dict(size=7, color="#1e293b"),
        textposition="top center",
        hovertext=hover,
        hoverinfo="text",
        name=NS_LABELS[ns],
    ))

# ── Figure ────────────────────────────────────────────────────────────────────
fig = go_plotly.Figure(
    data=[edge_trace] + node_traces,
    layout=go_plotly.Layout(
        title=dict(
            text=(
                "GO Enrichment Network – Blood Proteome (PeptideAtlas)<br>"
                "<sup>Nodes = GO terms · Size ∝ gene count · "
                "Edges = shared genes (Jaccard ≥ threshold) · "
                "Hover for details</sup>"
            ),
            font=dict(size=15),
        ),
        showlegend=True,
        legend=dict(
            title="Namespace",
            itemsizing="constant",
            font=dict(size=11),
        ),
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        margin=dict(t=90, l=10, r=10, b=10),
        width=1400,
        height=900,
    ),
)

out_path = os.path.join(results_dir, "go_enrichment_network.html")
fig.write_html(out_path, include_plotlyjs=True)
print(f"\nNetwork graph saved to {out_path}")
print("Open in a browser — zoom, pan, and hover over nodes to explore.")
