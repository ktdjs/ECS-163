#!/usr/bin/env python3.11
"""
Generate a hierarchically-clustered GO enrichment treemap.

Reads enrichment results from go_enrichment_results.tsv and uses an LLM
to recursively cluster GO terms into semantically coherent groups
(bottom-up: small clusters first, then grouped into progressively larger ones).

Usage:
    export OPENAI_API_KEY=sk-...
    python peptide_atlas_clustered_treemap.py
"""

import os
import sys
import json
import ast
import hashlib
import time
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go_plotly
from openai import OpenAI

# ── Paths ─────────────────────────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, "results")
cache_dir = os.path.join(results_dir, "cluster_cache")
os.makedirs(cache_dir, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
MODEL = "gpt-4o-mini"
MAX_CHILDREN = 10       # cluster further if a node has more children than this
MIN_CLUSTERS = 3        # minimum clusters per LLM call
MAX_CLUSTERS = 10       # maximum clusters per LLM call
MAX_DEPTH = 4           # safety cap on recursion depth
BATCH_SIZE = 150        # max terms per single LLM call (for reliability)

NAMESPACE_LABELS = {
    "biological_process": "Biological Process",
    "molecular_function": "Molecular Function",
    "cellular_component": "Cellular Component",
}

NS_COLORS = {
    "biological_process": "#3b82f6",
    "molecular_function": "#ef4444",
    "cellular_component": "#22c55e",
}

NS_LIGHT = {
    "biological_process": "#93c5fd",
    "molecular_function": "#fca5a5",
    "cellular_component": "#86efac",
}

# ── Load enrichment results ───────────────────────────────────────────────────
tsv_path = os.path.join(results_dir, "go_enrichment_results.tsv")
if not os.path.isfile(tsv_path):
    sys.exit(f"ERROR: {tsv_path} not found. Run peptide_atlas_go_enrichment.py first.")

df = pd.read_csv(tsv_path, sep="\t")
df["study_genes"] = df["study_genes"].apply(ast.literal_eval)
print(f"Loaded {len(df)} significant GO terms from {tsv_path}")

# ── OpenAI client ─────────────────────────────────────────────────────────────
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    sys.exit(
        "ERROR: OPENAI_API_KEY not set.\n"
        "  export OPENAI_API_KEY=sk-...\n"
        "  python peptide_atlas_clustered_treemap.py"
    )

client = OpenAI(api_key=api_key)


# ── LLM clustering ───────────────────────────────────────────────────────────

def _cache_path(term_ids: list[str]) -> str:
    key = hashlib.md5(json.dumps(sorted(term_ids)).encode()).hexdigest()
    return os.path.join(cache_dir, f"{key}.json")


def _llm_cluster_batch(terms: list[dict], target_clusters: int, max_retries=3) -> dict:
    """
    Single LLM call: group `terms` into `target_clusters` clusters.
    Returns {cluster_name: [GO IDs]}.
    """
    term_ids = [t["id"] for t in terms]
    cp = _cache_path(term_ids)
    if os.path.exists(cp):
        with open(cp) as f:
            cached = json.load(f)
        print(f"    (cached {len(terms)} terms → {len(cached)} clusters)")
        return cached

    term_list = "\n".join(
        f"- {t['id']}: {t['name']} ({t['n_genes']} genes)" for t in terms
    )

    prompt = (
        f"Group the following {len(terms)} Gene Ontology enrichment terms into "
        f"approximately {target_clusters} semantically coherent clusters based on "
        f"biological function similarity.\n\n"
        f"GO terms:\n{term_list}\n\n"
        f"Respond ONLY with valid JSON:\n"
        f'{{"Cluster Name": ["GO:xxxx", ...], ...}}\n\n'
        f"Rules:\n"
        f"- Every GO ID must appear in exactly one cluster\n"
        f"- Cluster names: short (2-5 words), biologically meaningful\n"
        f"- Prioritize semantic coherence over equal sizes\n"
        f"- Only output JSON, no explanation"
    )

    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a bioinformatics expert specializing in Gene Ontology. Respond only with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)

            assigned = set()
            for ids in result.values():
                assigned.update(ids)

            input_ids = set(t["id"] for t in terms)
            missing = input_ids - assigned
            extra = assigned - input_ids

            for k in list(result.keys()):
                result[k] = [gid for gid in result[k] if gid in input_ids]
                if not result[k]:
                    del result[k]

            if missing:
                smallest = min(result.keys(), key=lambda k: len(result[k]))
                result[smallest].extend(sorted(missing))
                print(f"    (patched {len(missing)} missing terms into '{smallest}')")
            if extra:
                print(f"    (removed {len(extra)} hallucinated IDs)")

            with open(cp, "w") as f:
                json.dump(result, f, indent=2)

            return result

        except Exception as e:
            print(f"    Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def llm_cluster(terms: list[dict]) -> dict:
    """
    Cluster terms, batching if necessary for reliability.
    Returns {cluster_name: [GO IDs]}.
    """
    if len(terms) <= BATCH_SIZE:
        target = min(MAX_CLUSTERS, max(MIN_CLUSTERS, len(terms) // 8))
        return _llm_cluster_batch(terms, target)

    # Batch: split terms, cluster each batch, then merge
    lookup = {t["id"]: t for t in terms}
    batches = [terms[i : i + BATCH_SIZE] for i in range(0, len(terms), BATCH_SIZE)]
    print(f"    Splitting {len(terms)} terms into {len(batches)} batches of ≤{BATCH_SIZE}")

    all_clusters = defaultdict(list)
    for i, batch in enumerate(batches):
        target = min(MAX_CLUSTERS, max(MIN_CLUSTERS, len(batch) // 8))
        print(f"    Batch {i + 1}/{len(batches)} ({len(batch)} terms, target {target} clusters)")
        batch_result = _llm_cluster_batch(batch, target)
        for name, ids in batch_result.items():
            all_clusters[name].extend(ids)

    # Merge clusters with similar names via a second LLM call
    if len(all_clusters) > MAX_CLUSTERS:
        cluster_summaries = []
        for name, ids in all_clusters.items():
            sample_names = [lookup[gid]["name"] for gid in ids[:5] if gid in lookup]
            cluster_summaries.append({
                "id": name,
                "name": name,
                "n_genes": len(ids),
            })

        print(f"    Merging {len(all_clusters)} batch-clusters into ≤{MAX_CLUSTERS} groups")
        merge_result = _llm_cluster_batch(
            cluster_summaries,
            target_clusters=min(MAX_CLUSTERS, max(MIN_CLUSTERS, len(cluster_summaries) // 3)),
        )

        merged = {}
        for meta_name, sub_cluster_names in merge_result.items():
            merged_ids = []
            for sc_name in sub_cluster_names:
                merged_ids.extend(all_clusters.get(sc_name, []))
            merged[meta_name] = merged_ids

        return merged

    return dict(all_clusters)


def recursive_cluster(terms: list[dict], depth=0) -> dict:
    """
    Recursively cluster terms into a nested hierarchy.

    Returns a nested dict where keys are cluster names and values are either:
      - A list of GO ID strings (leaf cluster)
      - A nested dict of the same structure (intermediate cluster)
    """
    if len(terms) <= MAX_CHILDREN or depth >= MAX_DEPTH:
        return {t["id"]: t for t in terms}  # leaf level: just GO terms

    indent = "  " * depth
    print(f"{indent}Depth {depth}: clustering {len(terms)} terms...")

    clusters = llm_cluster(terms)
    lookup = {t["id"]: t for t in terms}

    result = {}
    for cluster_name, cluster_ids in sorted(
        clusters.items(), key=lambda x: -len(x[1])
    ):
        cluster_terms = [lookup[gid] for gid in cluster_ids if gid in lookup]
        if not cluster_terms:
            continue

        if len(cluster_terms) <= MAX_CHILDREN:
            result[cluster_name] = cluster_terms
        else:
            result[cluster_name] = recursive_cluster(cluster_terms, depth + 1)

    return result


# ── Build treemap from hierarchy ──────────────────────────────────────────────

ids = []
labels_list = []
parents_list = []
values_list = []
hover_list = []
colors_list = []


def add_node(node_id, label, parent, value, hover, color):
    ids.append(node_id)
    labels_list.append(label)
    parents_list.append(parent)
    values_list.append(value)
    hover_list.append(hover)
    colors_list.append(color)


def count_genes_in_cluster(node) -> set:
    """Recursively collect all genes from a cluster subtree."""
    genes = set()
    if isinstance(node, list):
        for term_info in node:
            if isinstance(term_info, dict) and "study_genes" in term_info:
                genes.update(term_info["study_genes"])
    elif isinstance(node, dict):
        for v in node.values():
            if isinstance(v, dict) and "study_genes" in v:
                genes.update(v["study_genes"])
            elif isinstance(v, (dict, list)):
                genes.update(count_genes_in_cluster(v))
    return genes


def count_terms_in_cluster(node) -> int:
    """Recursively count GO terms in a cluster subtree."""
    if isinstance(node, list):
        return len(node)
    elif isinstance(node, dict):
        total = 0
        for v in node.values():
            if isinstance(v, dict) and "id" in v and v["id"].startswith("GO:"):
                total += 1
            elif isinstance(v, (dict, list)):
                total += count_terms_in_cluster(v)
        return total
    return 0


def _fmt_pval(val):
    try:
        return f"{float(val):.2e}"
    except (ValueError, TypeError):
        return str(val)


def _go_term_hover(t):
    return (
        f"<b>{t['name']}</b><br>"
        f"{t['id']}<br>"
        f"Genes in study: {t['n_genes']}<br>"
        f"Total GO term size: {t.get('n_go', '?')}<br>"
        f"p_corr: {_fmt_pval(t.get('p_corr', '?'))}"
    )


def _add_go_term_node(t, parent_id, base_color):
    """Add a GO term node and its gene children to the treemap."""
    go_id = t["id"]
    node_id = f"{parent_id}|{go_id}"
    add_node(
        node_id,
        f"{t['name']} ({t['n_genes']})",
        parent_id,
        0,
        _go_term_hover(t),
        base_color,
    )
    for gene in sorted(t.get("study_genes", [])):
        add_node(f"{node_id}|{gene}", gene, node_id, 1, f"<b>{gene}</b>", base_color)


def build_treemap_recursive(hierarchy, parent_id, ns, term_info_map, depth=0):
    """Walk the cluster hierarchy, adding treemap nodes."""
    base_color = NS_COLORS[ns]
    light_color = NS_LIGHT[ns]
    seen_ids = set()

    for cluster_name, node in hierarchy.items():
        # Deduplicate cluster IDs at the same level
        candidate_id = f"{parent_id}|{cluster_name}"
        if candidate_id in seen_ids:
            idx = 2
            while f"{candidate_id}_{idx}" in seen_ids:
                idx += 1
            candidate_id = f"{candidate_id}_{idx}"
        seen_ids.add(candidate_id)

        if isinstance(node, list):
            # Leaf cluster: list of term dicts
            all_genes = set()
            for t in node:
                all_genes.update(t.get("study_genes", []))

            add_node(
                candidate_id,
                f"{cluster_name} ({len(node)} terms, {len(all_genes)} genes)",
                parent_id,
                0,
                f"<b>{cluster_name}</b><br>"
                f"{len(node)} GO terms<br>"
                f"{len(all_genes)} unique genes",
                light_color,
            )

            for t in sorted(node, key=lambda x: x.get("p_corr", 1)):
                _add_go_term_node(t, candidate_id, base_color)

        elif isinstance(node, dict):
            if "id" in node and str(node.get("id", "")).startswith("GO:"):
                # Single GO term (base-case leaf from recursive_cluster)
                _add_go_term_node(node, parent_id, base_color)
            else:
                # Intermediate cluster: recurse
                all_genes = count_genes_in_cluster(node)
                n_terms = count_terms_in_cluster(node)

                add_node(
                    candidate_id,
                    f"{cluster_name} ({n_terms} terms, {len(all_genes)} genes)",
                    parent_id,
                    0,
                    f"<b>{cluster_name}</b><br>"
                    f"{n_terms} GO terms<br>"
                    f"{len(all_genes)} unique genes",
                    light_color,
                )
                build_treemap_recursive(node, candidate_id, ns, term_info_map, depth + 1)


# ── Main ──────────────────────────────────────────────────────────────────────

add_node("root", "Blood Proteome GO Enrichment (LLM-Clustered)", "", 0, "", "#f1f5f9")

for ns, ns_label in NAMESPACE_LABELS.items():
    ns_df = df[df["class"] == ns].copy()
    if ns_df.empty:
        continue

    print(f"\n{'='*70}")
    print(f"  {ns_label}: {len(ns_df)} terms")
    print(f"{'='*70}")

    all_ns_genes = set()
    for genes in ns_df["study_genes"]:
        all_ns_genes.update(genes)

    add_node(
        ns,
        f"{ns_label} ({len(all_ns_genes)} genes, {len(ns_df)} terms)",
        "root",
        0,
        f"<b>{ns_label}</b><br>{len(ns_df)} significant terms<br>{len(all_ns_genes)} unique genes",
        NS_COLORS[ns],
    )

    terms = []
    for _, row in ns_df.iterrows():
        terms.append({
            "id": row["GO"],
            "name": row["term"],
            "n_genes": row["n_genes"],
            "n_go": row["n_go"],
            "p_corr": row["p_corr"],
            "study_genes": row["study_genes"],
        })

    term_info_map = {t["id"]: t for t in terms}

    hierarchy = recursive_cluster(terms)

    # Save cluster hierarchy for inspection
    def _serializable(obj):
        if isinstance(obj, dict):
            return {k: _serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_serializable(i) for i in obj]
        if isinstance(obj, set):
            return sorted(obj)
        return obj

    hierarchy_path = os.path.join(results_dir, f"cluster_hierarchy_{ns}.json")
    with open(hierarchy_path, "w") as f:
        json.dump(
            _serializable(hierarchy),
            f,
            indent=2,
            default=str,
        )
    print(f"  Hierarchy saved to {hierarchy_path}")

    build_treemap_recursive(hierarchy, ns, ns, term_info_map)

# ── Create Plotly treemap ─────────────────────────────────────────────────────

fig = go_plotly.Figure(
    go_plotly.Treemap(
        ids=ids,
        labels=labels_list,
        parents=parents_list,
        values=values_list,
        branchvalues="remainder",
        hovertext=hover_list,
        hoverinfo="text",
        marker=dict(
            colors=colors_list,
            line=dict(width=1, color="#e2e8f0"),
        ),
        textinfo="label",
        maxdepth=3,
        pathbar=dict(visible=True, textfont=dict(size=13)),
        tiling=dict(pad=3),
    )
)

fig.update_layout(
    title=dict(
        text=(
            "GO Enrichment – Blood Proteome (PeptideAtlas)<br>"
            "<sup>LLM-clustered hierarchy · Click to drill down · Breadcrumb bar to navigate back</sup>"
        ),
        font=dict(size=16),
    ),
    margin=dict(t=80, l=10, r=10, b=10),
    width=1400,
    height=800,
)

html_path = os.path.join(results_dir, "go_enrichment_clustered.html")
fig.write_html(html_path, include_plotlyjs=True)
print(f"\nTreemap saved to {html_path}")
print("Open in a browser to explore the clustered hierarchy.")
