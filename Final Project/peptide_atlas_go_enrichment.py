import numpy as np
import pandas as pd
import sys
import os
import urllib.request
import gzip
import shutil
from collections import defaultdict

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
results_dir = os.path.join(script_dir, "results")
os.makedirs(data_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

# Load gene list from PeptideAtlas blood TSV
peptide_atlas_path = os.path.join(data_dir, "peptide_atlas_blood.tsv")
pa_df = pd.read_csv(peptide_atlas_path, sep="\t")
test_genes = pa_df["biosequence_gene_name"].dropna().unique().tolist()
print(f"Loaded {len(test_genes)} unique genes from PeptideAtlas blood dataset")

# --- Background gene set ---
sys.path.insert(0, data_dir)
from genes_ncbi_homo_sapiens_proteincoding import GENEID2NT as GeneID2nt_human

# --- GO enrichment setup ---
from goatools.base import download_go_basic_obo
from goatools.obo_parser import GODag
from goatools.anno.genetogo_reader import Gene2GoReader
from goatools.goea.go_enrichment_ns import GOEnrichmentStudyNS

obo_path = os.path.join(data_dir, "go-basic.obo")
if not os.path.isfile(obo_path):
    obo_path = download_go_basic_obo(obo_path)

fin_gene2go = os.path.join(data_dir, "gene2go")
fin_gene2go_human = os.path.join(data_dir, "gene2go_human")

# Skip full download if the human-filtered file already exists.
if not os.path.isfile(fin_gene2go) and not os.path.isfile(fin_gene2go_human):
    gz_path = fin_gene2go + ".gz"
    url = "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz"
    print(f"Downloading {url}")
    print("  (This file is ~1.2 GB. One-time download.)")

    def _progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            print(
                f"\r  {downloaded / 1e6:.1f} / {total_size / 1e6:.1f} MB ({pct:.0f}%)",
                end="",
                flush=True,
            )
        else:
            print(f"\r  {downloaded / 1e6:.1f} MB downloaded", end="", flush=True)

    urllib.request.urlretrieve(url, gz_path, reporthook=_progress_hook)
    print("\n  Decompressing ...")
    with gzip.open(gz_path, "rb") as f_in, open(fin_gene2go, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(gz_path)
    print("  Done.")
elif os.path.isfile(fin_gene2go):
    print(f"Using existing {fin_gene2go}")

# Pre-filter gene2go to human-only (taxid 9606) — shrinks ~10 GB to ~15 MB,
# turning a 100-second parse into a few seconds.
if not os.path.isfile(fin_gene2go_human):
    print("Filtering gene2go to human (taxid 9606) ...")
    with open(fin_gene2go) as f_in, open(fin_gene2go_human, "w") as f_out:
        for line in f_in:
            if line.startswith("#") or line.startswith("9606\t"):
                f_out.write(line)
    print("  Done.")
else:
    print(f"Using existing {fin_gene2go_human}")

# Evidence-code-filtered gene2go: remove low-confidence Cellular Component annotations.
# HDA (High-throughput Direct Assay) CC annotations come from mass spec membrane
# fractionation screens — proteins detected there aren't necessarily membrane proteins
# (e.g. CHD4 is nuclear but appears in membrane fractions as noise). IEA is fully
# automated and unreliable. Filtering these restores correct CC placement.
fin_gene2go_ev = os.path.join(data_dir, "gene2go_human_ev_filtered")
if not os.path.isfile(fin_gene2go_ev):
    print("Filtering gene2go by evidence code (removing HDA/IEA for CC) ...")
    # For CC: keep only IDA/IPI/IMP/IGI/IC/TAS/EXP/IEP (direct experimental)
    # plus IBA (curated phylogenetic via PAINT). Drop all sequence-similarity
    # (ISS/ISA/ISM), high-throughput screens (HDA/HMP/HGI/HTP), and
    # purely computational codes (IEA/RCA/IKR/ISO/NAS/ND).
    _SKIP_CC  = {"IEA", "HDA", "HMP", "HGI", "HTP", "NAS", "ND",
                 "ISS", "ISA", "ISM", "RCA", "IKR", "ISO"}
    _SKIP_ANY = {"IEA", "NAS", "ND"}
    kept = dropped = 0
    with open(fin_gene2go_human) as fi, open(fin_gene2go_ev, "w") as fo:
        for line in fi:
            if line.startswith("#"):
                fo.write(line)
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                fo.write(line)
                continue
            ev, cat = parts[3], parts[7].strip()
            if ev in _SKIP_ANY or (cat == "Component" and ev in _SKIP_CC):
                dropped += 1
                continue
            fo.write(line)
            kept += 1
    print(f"  Done. Kept {kept}, dropped {dropped} annotations.")
else:
    print(f"Using existing {fin_gene2go_ev}")

obodag = GODag(obo_path)

# Build symbol → GeneID mapper, including all known aliases so that genes
# whose PeptideAtlas symbol is an older/alternate name still resolve.
mapper = {}
alias_mapper = {}   # alias → canonical GeneID  (lower priority than direct symbol)
for key in GeneID2nt_human:
    nt = GeneID2nt_human[key]
    mapper[nt.Symbol] = nt.GeneID
    for alias in (nt.Aliases or []):
        a = alias.strip()
        if a and a not in mapper:
            alias_mapper[a] = nt.GeneID

def resolve_gene(symbol):
    """Return GeneID for a symbol, falling back to alias table."""
    if symbol in mapper:
        return mapper[symbol]
    return alias_mapper.get(symbol)

inv_map = {v: k for k, v in mapper.items()}
print(f"Symbol mapper: {len(mapper):,} symbols + {len(alias_mapper):,} aliases")

objanno = Gene2GoReader(fin_gene2go_ev, taxids=[9606])
ns2assoc = objanno.get_ns2assc()

goeaobj = GOEnrichmentStudyNS(
    GeneID2nt_human.keys(),
    ns2assoc,
    obodag,
    propagate_counts=False,
    alpha=0.05,
    methods=["fdr_bh"],
)

GO_items = []
for ns in ["BP", "CC", "MF"]:
    temp = goeaobj.ns2objgoea[ns].assoc
    for item in temp:
        GO_items += temp[item]


def go_it(test_genes):
    print(f"Input genes: {len(test_genes)}")
    mapped_genes = []
    for gene in test_genes:
        gid = resolve_gene(gene)
        if gid is not None:
            mapped_genes.append(gid)
    print(f"Mapped genes: {len(mapped_genes)}")

    goea_results_all = goeaobj.run_study(mapped_genes)
    goea_results_sig = [r for r in goea_results_all if r.p_fdr_bh < 0.05]
    GO = pd.DataFrame(
        [
            [
                r.GO,
                r.goterm.name,
                r.goterm.namespace,
                r.p_uncorrected,
                r.p_fdr_bh,
                r.ratio_in_study[0],
                r.ratio_in_study[1],
                GO_items.count(r.GO),
                list(map(lambda y: inv_map[y], r.study_items)),
            ]
            for r in goea_results_sig
        ],
        columns=[
            "GO", "term", "class", "p", "p_corr",
            "n_genes", "n_study", "n_go", "study_genes",
        ],
    )
    GO = GO[GO.n_genes > 1]
    return GO


# ── Run enrichment ────────────────────────────────────────────────────────────
df = go_it(test_genes)
df["per"] = df.n_genes / df.n_go
print(f"\nSignificant GO terms: {len(df)}")

NAMESPACE_LABELS = {
    "biological_process": "Biological Process",
    "molecular_function": "Molecular Function",
    "cellular_component": "Cellular Component",
}

# ── Summary with gene counts per category ─────────────────────────────────────
print("\n" + "=" * 80)
total_unique = set()
for ns, label in NAMESPACE_LABELS.items():
    ns_df = df[df["class"] == ns]
    unique_genes = set()
    for genes in ns_df["study_genes"]:
        unique_genes.update(genes)
    total_unique.update(unique_genes)
    print(f"\n{label}: {len(ns_df)} significant terms, {len(unique_genes)} unique genes")
    for _, row in ns_df.sort_values("p_corr").head(5).iterrows():
        print(f"  {row['GO']}  {row['term']}  (p_corr={row['p_corr']:.2e}, genes={row['n_genes']})")
print(f"\nTotal unique genes across all categories: {len(total_unique)}")
print("=" * 80)

# ── Ancestor-fallback: rescue genes with no significant GO term ───────────────
# For any study gene that appears in zero enriched GO terms, walk its GO
# annotations up the DAG until we reach a term that IS enriched, and add
# the gene there. This rescues genes whose own specific GO terms weren't
# significant but whose broader category clearly was.

sig_go_ids = set(df["GO"])
NS_MAP_SHORT = {"BP": "biological_process", "CC": "cellular_component", "MF": "molecular_function"}

# Build gene → {ns: set(go_ids)} from the filtered gene2go
gene_go_by_ns: dict = {}   # GeneID → {"BP": set, "CC": set, "MF": set}
with open(fin_gene2go_ev) as fh:
    for line in fh:
        if line.startswith("#"): continue
        parts = line.split("\t")
        if len(parts) < 8: continue
        try:
            gid = int(parts[1])
        except ValueError:
            continue
        go_id = parts[2]
        cat   = parts[7].strip()
        ns_short = {"Process": "BP", "Component": "CC", "Function": "MF"}.get(cat)
        if ns_short is None: continue
        gene_go_by_ns.setdefault(gid, {"BP": set(), "CC": set(), "MF": set()})
        gene_go_by_ns[gid][ns_short].add(go_id)

# Find currently categorised genes (in any sig term)
categorised_genes: set = set()
for genes in df["study_genes"]:
    categorised_genes.update(genes)

# For each uncategorised study gene, try to find a significant ancestor
rescued: list[dict] = []    # extra rows to append to df
for gene_sym in test_genes:
    if gene_sym in categorised_genes:
        continue
    gid = resolve_gene(gene_sym)
    if gid is None:
        continue
    go_ns = gene_go_by_ns.get(gid, {})
    for ns_short, go_set in go_ns.items():
        ns_long = NS_MAP_SHORT[ns_short]
        best_ancestor = None
        best_depth    = -1
        for go_id in go_set:
            # Walk up DAG
            node = obodag.get(go_id)
            if node is None: continue
            queue = list(node.parents)
            visited = {go_id}
            depth = 0
            while queue:
                parent = queue.pop(0)
                if parent.id in visited: continue
                visited.add(parent.id)
                depth += 1
                if parent.id in sig_go_ids:
                    if depth > best_depth:
                        best_depth = depth
                        best_ancestor = parent.id
                    break
                queue.extend(parent.parents)
        if best_ancestor and best_ancestor in sig_go_ids:
            # Check this ancestor row exists in df
            anc_rows = df[df["GO"] == best_ancestor]
            if anc_rows.empty: continue
            anc_row = anc_rows.iloc[0]
            # Append gene to that row's study_genes (by adding a synthetic row)
            rescued.append({
                "GO": best_ancestor,
                "term": anc_row["term"],
                "class": ns_long,
                "p": anc_row["p"],
                "p_corr": anc_row["p_corr"],
                "n_genes": 1,
                "n_study": anc_row["n_study"],
                "n_go": anc_row["n_go"],
                "study_genes": [gene_sym],
                "per": anc_row["per"],
                "rescued": True,
            })
            categorised_genes.add(gene_sym)

if rescued:
    # Merge rescued genes back into the existing rows (add to study_genes list)
    # rather than duplicating rows: update each anchor term's gene list.
    rescue_map: dict = {}  # GO → set of rescued genes
    for r in rescued:
        rescue_map.setdefault(r["GO"], set()).add(r["study_genes"][0])

    def _add_rescued(row):
        extra = rescue_map.get(row["GO"], set())
        if extra:
            row = row.copy()
            row["study_genes"] = list(row["study_genes"]) + sorted(extra)
            row["n_genes"] = len(row["study_genes"])
        return row

    df = df.apply(_add_rescued, axis=1)
    print(f"\nAncestor-fallback rescued {len(rescue_map)} additional genes "
          f"(added to existing significant terms).")

# Recount after rescue
categorised_after: set = set()
for genes in df["study_genes"]:
    categorised_after.update(genes)

still_missing = set(test_genes) - categorised_after
print(f"Coverage after rescue: {len(categorised_after)}/{len(test_genes)} "
      f"({100*len(categorised_after)/len(test_genes):.1f}%)")
if still_missing:
    print(f"Still uncategorised ({len(still_missing)}): {sorted(still_missing)}")

# ── Save full results ─────────────────────────────────────────────────────────
df_save = df.copy()
df_save["class_label"] = df_save["class"].map(NAMESPACE_LABELS)
df_save = df_save.sort_values(["class", "p_corr"])
tsv_path = os.path.join(results_dir, "go_enrichment_results.tsv")
df_save.to_csv(tsv_path, sep="\t", index=False)
print(f"\nFull results saved to {tsv_path} ({len(df_save)} terms)")

# ── Static PNG plot (top 10 overall) ──────────────────────────────────────────
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import cm
import textwrap
import seaborn as sns

df_plot = df.sort_values("p_corr").head(10)

fig, (ax_cb, ax_bar) = plt.subplots(
    1, 2, figsize=(9, 5), gridspec_kw={"width_ratios": [1, 14]}
)

cmap = mpl.cm.bwr_r
norm = mpl.colors.Normalize(vmin=df_plot.p_corr.min(), vmax=df_plot.p_corr.max())
color_mapper = cm.ScalarMappable(norm=norm, cmap=cm.bwr_r)

mpl.colorbar.ColorbarBase(ax_cb, cmap=cmap, norm=norm, orientation="vertical")
ax_cb.set_ylabel("FDR corrected p-value")

sns.barplot(
    data=df_plot,
    x="per",
    y="term",
    hue="term",
    palette=dict(zip(df_plot["term"], color_mapper.to_rgba(df_plot.p_corr.values))),
    legend=False,
    ax=ax_bar,
)
bar_labels = [
    f"{textwrap.fill(t, 22)}  ({n})" for t, n in zip(df_plot["term"], df_plot["n_genes"])
]
ax_bar.set_yticks(range(len(bar_labels)))
ax_bar.set_yticklabels(bar_labels, fontsize=8)
ax_bar.set_xlabel("Fraction of GO term genes in study")
plt.suptitle("GO Enrichment – Human Blood Proteome (PeptideAtlas)", fontsize=11)
plt.tight_layout()

png_path = os.path.join(results_dir, "peptide_atlas_go_enrichment.png")
plt.savefig(png_path, dpi=200, bbox_inches="tight")
print(f"Static plot saved to {png_path}")
plt.close()

# ── Interactive HTML treemap ──────────────────────────────────────────────────
# Hierarchy:  Root -> Namespace -> GO terms (nested by DAG) -> Genes
# Click any node to drill down; breadcrumb bar to navigate back.

import plotly.graph_objects as go_plotly

NS_COLORS = {
    "biological_process": "#3b82f6",
    "molecular_function": "#ef4444",
    "cellular_component": "#22c55e",
}

ids = []
labels = []
parents = []
values = []
hover_texts = []
marker_colors = []


def add_node(node_id, label, parent, value, hover, color):
    ids.append(node_id)
    labels.append(label)
    parents.append(parent)
    values.append(value)
    hover_texts.append(hover)
    marker_colors.append(color)


add_node("root", "Blood Proteome GO Enrichment", "", 0, "", "#f1f5f9")

for ns, ns_label in NAMESPACE_LABELS.items():
    ns_df = df[df["class"] == ns]
    if ns_df.empty:
        continue

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

    sig_go_ids = set(ns_df["GO"].values)
    term_genes = {row["GO"]: set(row["study_genes"]) for _, row in ns_df.iterrows()}

    # For each significant term, BFS up the GO DAG to find the nearest
    # significant ancestor — this builds a proper nested hierarchy.
    term_to_parent = {}
    for go_id in sig_go_ids:
        goterm = obodag.get(go_id)
        if goterm is None:
            term_to_parent[go_id] = ns
            continue
        nearest = None
        queue = list(goterm.parents)
        visited = {go_id}
        while queue:
            p = queue.pop(0)
            if p.id in visited:
                continue
            visited.add(p.id)
            if p.id in sig_go_ids:
                nearest = p.id
                break
            queue.extend(p.parents)
        term_to_parent[go_id] = nearest or ns

    children_map = defaultdict(set)
    for go_id, parent_id in term_to_parent.items():
        if parent_id != ns:
            children_map[parent_id].add(go_id)

    def descendant_genes(go_id):
        """Genes already accounted for by descendant significant GO terms."""
        result = set()
        for child in children_map.get(go_id, []):
            result.update(term_genes.get(child, set()))
            result.update(descendant_genes(child))
        return result

    base = NS_COLORS[ns]

    for _, row in ns_df.sort_values("p_corr").iterrows():
        go_id = row["GO"]
        parent_id = term_to_parent[go_id]
        n_genes = row["n_genes"]

        add_node(
            go_id,
            f"{row['term']} ({n_genes} genes)",
            parent_id,
            0,
            f"<b>{row['term']}</b><br>"
            f"{go_id}<br>"
            f"Genes in study: {n_genes}<br>"
            f"Total GO term size: {row['n_go']}<br>"
            f"p_corr: {row['p_corr']:.2e}",
            base,
        )

        direct = sorted(term_genes.get(go_id, set()) - descendant_genes(go_id))
        for gene in direct:
            add_node(f"{go_id}|{gene}", gene, go_id, 1, f"<b>{gene}</b>", base)

fig = go_plotly.Figure(
    go_plotly.Treemap(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="remainder",
        hovertext=hover_texts,
        hoverinfo="text",
        marker=dict(colors=marker_colors, line=dict(width=1, color="#e2e8f0")),
        textinfo="label",
        maxdepth=2,
        pathbar=dict(visible=True, textfont=dict(size=13)),
        tiling=dict(pad=3),
    )
)

fig.update_layout(
    title=dict(
        text="GO Enrichment – Blood Proteome (PeptideAtlas)<br>"
        "<sup>Click a category to drill down · Use the bar above to navigate back</sup>",
        font=dict(size=16),
    ),
    margin=dict(t=80, l=10, r=10, b=10),
    width=1200,
    height=700,
)

html_path = os.path.join(results_dir, "go_enrichment_interactive.html")
fig.write_html(html_path, include_plotlyjs=True)
print(f"Interactive treemap saved to {html_path}")

# ── Plasma protein supplement ─────────────────────────────────────────────────
# Every protein in the PeptideAtlas blood dataset is by definition detected in
# blood plasma. We split them into two biologically meaningful groups:
#   • Classically secreted  — has a GO:0005615/GO:0005576/GO:0005576 (extracellular
#     space / extracellular region) annotation with direct experimental evidence
#   • Non-classically released — detected in plasma but primarily intracellular
#     (leaked from lysed cells, shed via vesicles, etc.)

EXTRACELLULAR_GO = {
    "GO:0005615",  # extracellular space
    "GO:0005576",  # extracellular region
    "GO:0070062",  # extracellular exosome
    "GO:0072562",  # blood microparticle
    "GO:0005796",  # Golgi lumen (secretory pathway marker)
}

# Build set of GeneIDs annotated to extracellular terms (CC namespace)
ec_gene_ids: set = set()
cc_assoc = ns2assoc.get("CC", {})
for gid, go_set in cc_assoc.items():
    if go_set & EXTRACELLULAR_GO:
        ec_gene_ids.add(gid)

pa_df = pd.read_csv(peptide_atlas_path, sep="\t")
pa_df = pa_df.dropna(subset=["biosequence_gene_name"])

plasma_rows = []
for _, row in pa_df.iterrows():
    gene = row["biosequence_gene_name"]
    gid  = resolve_gene(gene)
    if gid is None:
        continue
    secreted = gid in ec_gene_ids
    plasma_rows.append({
        "gene":          gene,
        "presence_level": row.get("presence_level", "unknown"),
        "norm_PSMs":     row.get("norm_PSMs_per_100K", 0),
        "probability":   row.get("probability", 0),
        "secreted":      secreted,
        "origin":        "Classically secreted" if secreted else "Non-classically released",
    })

plasma_df = pd.DataFrame(plasma_rows)
secreted_n    = plasma_df["secreted"].sum()
nonsecr_n     = (~plasma_df["secreted"]).sum()
print(f"\nPlasma protein supplement:")
print(f"  Classically secreted (extracellular GO):  {secreted_n}")
print(f"  Non-classically released (intracellular): {nonsecr_n}")

# ── 2-D dot-plot visualization ────────────────────────────────────────────────
# One dot per significant GO term; axes show enrichment strength and gene ratio.
# This is the standard bioinformatics "bubble chart" (clusterProfiler-style).

import numpy as np

TOP_N = 25  # terms per namespace shown in the dot plot

NS_ORDER = {
    "biological_process": 0,
    "molecular_function":  1,
    "cellular_component":  2,
}

NS_COLORS_DOT = {
    "biological_process": "#3b82f6",
    "molecular_function":  "#ef4444",
    "cellular_component":  "#22c55e",
}

rows_plot = []
for ns in ["biological_process", "molecular_function", "cellular_component"]:
    sub = df[df["class"] == ns].copy()
    sub = sub.sort_values("p_corr").head(TOP_N)
    sub["neg_log10_p"] = -np.log10(sub["p_corr"].clip(lower=1e-300))
    sub["gene_ratio"]  = sub["n_genes"] / sub["n_study"]
    sub["ns"]          = ns
    rows_plot.append(sub)

dot_df = pd.concat(rows_plot, ignore_index=True)
dot_df["ns_order"] = dot_df["ns"].map(NS_ORDER)
dot_df = dot_df.sort_values(["ns_order", "neg_log10_p"], ascending=[True, False])

# Build gene hover strings (first 10 genes)
def _gene_hover(genes):
    g = sorted(genes)
    shown = ", ".join(g[:10])
    if len(g) > 10:
        shown += f" … (+{len(g)-10} more)"
    return shown

dot_df["gene_str"] = dot_df["study_genes"].apply(_gene_hover)

import plotly.graph_objects as go_plotly2

fig2 = go_plotly2.Figure()

for ns in ["biological_process", "molecular_function", "cellular_component"]:
    sub = dot_df[dot_df["ns"] == ns]
    color = NS_COLORS_DOT[ns]
    label = NAMESPACE_LABELS[ns]

    fig2.add_trace(go_plotly2.Scatter(
        x=sub["gene_ratio"],
        y=sub["term"],
        mode="markers",
        name=label,
        marker=dict(
            size=sub["n_genes"].clip(upper=200) / 3 + 6,
            color=sub["neg_log10_p"],
            colorscale="Viridis",
            cmin=0,
            cmax=dot_df["neg_log10_p"].quantile(0.95),
            showscale=(ns == "biological_process"),
            colorbar=dict(
                title="-log₁₀(FDR)",
                thickness=12,
                len=0.5,
                y=0.75,
            ) if ns == "biological_process" else None,
            line=dict(color=color, width=1.5),
            symbol="circle",
        ),
        customdata=np.column_stack([
            sub["GO"],
            sub["n_genes"],
            sub["n_go"],
            sub["p_corr"].apply(lambda v: f"{v:.2e}"),
            sub["gene_str"],
        ]),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ID: %{customdata[0]}<br>"
            "Genes in study: %{customdata[1]}<br>"
            "GO term size: %{customdata[2]}<br>"
            "FDR: %{customdata[3]}<br>"
            "GeneRatio: %{x:.3f}<br>"
            "<i>%{customdata[4]}</i>"
            "<extra></extra>"
        ),
    ))

# Add plasma protein origin annotations as a separate annotation band
origin_colors = {"Classically secreted": "#16a34a", "Non-classically released": "#dc2626"}
for origin, grp in plasma_df.groupby("origin"):
    top10 = grp.nlargest(10, "norm_PSMs")
    fig2.add_annotation(
        x=1.12, xref="paper",
        y=0, yref="paper",
        text=(
            f"<b>{origin}</b> (n={len(grp)})<br>"
            + "  ".join(top10["gene"].tolist())
        ),
        showarrow=False,
        align="left",
        font=dict(size=9, color=origin_colors[origin]),
        xanchor="left",
        yanchor="top" if origin == "Classically secreted" else "bottom",
    )

total_height = max(700, len(dot_df) * 20 + 120)

fig2.update_layout(
    title=dict(
        text=(
            "GO Enrichment – Blood Proteome (PeptideAtlas) · 2-D Dot Plot<br>"
            "<sup>Dot size ∝ gene count · Dot colour = −log₁₀(FDR) · "
            f"Plasma proteins: {secreted_n} secreted / {nonsecr_n} non-classically released</sup>"
        ),
        font=dict(size=15),
    ),
    xaxis=dict(title="Gene Ratio (genes in study / study size)", zeroline=False),
    yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
    legend=dict(orientation="h", y=1.04, x=0),
    margin=dict(t=100, l=300, r=250, b=60),
    height=total_height,
    width=1400,
    plot_bgcolor="#f8fafc",
)

dot_path = os.path.join(results_dir, "go_enrichment_dotplot.html")
fig2.write_html(dot_path, include_plotlyjs=True)
print(f"2-D dot plot saved to {dot_path}")
print("\nDone. Open the HTML files in a browser to explore results interactively.")
