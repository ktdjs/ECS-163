import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import cm
import seaborn as sns
import textwrap

from goatools.base import download_go_basic_obo
from goatools.base import download_ncbi_associations
from goatools.obo_parser import GODag
from goatools.anno.genetogo_reader import Gene2GoReader
from goatools.goea.go_enrichment_ns import GOEnrichmentStudyNS

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
results_dir = os.path.join(script_dir, "results")
os.makedirs(results_dir, exist_ok=True)

sys.path.insert(0, data_dir)
from genes_ncbi_homo_sapiens_proteincoding import GENEID2NT as GeneID2nt_human


# ── 1. Load input genes ─────────────────────────────────────────────────────
genes_df = pd.read_csv(
    os.path.join(data_dir, "peptide_atlas_unique_genes.tsv"),
    sep="\t",
    header=None,
    names=["Symbol"],
)
test_genes = genes_df["Symbol"].dropna().unique().tolist()
print(f"Input genes from Peptide Atlas: {len(test_genes)}")

# ── 2. Build symbol <-> GeneID mappings ──────────────────────────────────────
symbol_to_id = {v.Symbol: v.GeneID for v in GeneID2nt_human.values()}
id_to_symbol = {v: k for k, v in symbol_to_id.items()}

# ── 3. Download / load GO ontology and gene2go annotations ──────────────────
obo_path = os.path.join(data_dir, "go-basic.obo")
if not os.path.isfile(obo_path):
    obo_path = download_go_basic_obo(obo_path)
fin_gene2go = os.path.join(data_dir, "gene2go")
if not os.path.isfile(fin_gene2go):
    fin_gene2go = download_ncbi_associations()
obodag = GODag(obo_path)

fin_gene2go_human = os.path.join(data_dir, "gene2go_human")
if not os.path.isfile(fin_gene2go_human):
    print("Filtering gene2go to human (taxid 9606) ...")
    with open(fin_gene2go) as f_in, open(fin_gene2go_human, "w") as f_out:
        for line in f_in:
            if line.startswith("#") or line.startswith("9606\t"):
                f_out.write(line)
    print("  Done.")

objanno = Gene2GoReader(fin_gene2go_human, taxids=[9606])
ns2assoc = objanno.get_ns2assc()

# ── 4. Set up enrichment object ─────────────────────────────────────────────
goeaobj = GOEnrichmentStudyNS(
    GeneID2nt_human.keys(),
    ns2assoc,
    obodag,
    propagate_counts=False,
    alpha=0.05,
    methods=["fdr_bh"],
)

# Collect all GO items (used to count total genes per GO term)
GO_items = []
for ns in ("BP", "CC", "MF"):
    assoc = goeaobj.ns2objgoea[ns].assoc
    for geneid_set in assoc.values():
        GO_items += list(geneid_set)


# ── 5. Run enrichment ───────────────────────────────────────────────────────
def go_it(test_genes):
    mapped_genes = []
    for gene in test_genes:
        if gene in symbol_to_id:
            mapped_genes.append(symbol_to_id[gene])
    print(f"Mapped genes: {len(mapped_genes)} / {len(test_genes)}")

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
                list(map(lambda y: id_to_symbol[y], r.study_items)),
            ]
            for r in goea_results_sig
        ],
        columns=[
            "GO",
            "term",
            "class",
            "p",
            "p_corr",
            "n_genes",
            "n_study",
            "n_go",
            "study_genes",
        ],
    )

    GO = GO[GO.n_genes > 1]
    return GO


df = go_it(test_genes)

NAMESPACE_LABELS = {
    "biological_process": "BP – Biological Process",
    "molecular_function": "MF – Molecular Function",
    "cellular_component": "CC – Cellular Component",
}

NAMESPACE_DESC = {
    "biological_process": (
        "Biological Process (BP): A recognized series of events or molecular "
        "functions with a defined beginning and end relevant to the functioning "
        "of living units (cells, tissues, organs, organisms)."
    ),
    "molecular_function": (
        "Molecular Function (MF): Activities at the molecular level, such as "
        "catalytic or binding activities performed by individual gene products "
        "or assembled complexes."
    ),
    "cellular_component": (
        "Cellular Component (CC): A component of a cell that is part of a "
        "larger structure, such as an anatomical structure (e.g. rough ER) or "
        "a gene product group (e.g. ribosome, proteasome)."
    ),
}

# ── 6. Save full results ────────────────────────────────────────────────────
out_dir = results_dir

df_save = df.copy()
df_save["class_label"] = df_save["class"].map(NAMESPACE_LABELS)
df_save = df_save.sort_values(["class", "p_corr"])
df_save.to_csv(os.path.join(out_dir, "go_enrichment_results.tsv"), sep="\t", index=False)
print(f"\nFull results saved ({len(df_save)} significant terms)")

# ── 7. Print summary per namespace ──────────────────────────────────────────
print("\n" + "=" * 80)
for ns, desc in NAMESPACE_DESC.items():
    subset = df[df["class"] == ns].sort_values("p_corr")
    print(f"\n{desc}")
    print(f"  Significant terms: {len(subset)}")
    if len(subset) > 0:
        print(f"  Top 5:")
        for _, row in subset.head(5).iterrows():
            print(f"    {row['GO']}  {row['term']}  (p_corr={row['p_corr']:.2e}, genes={row['n_genes']})")
print("=" * 80)

# ── 8. Plot top 10 per namespace ─────────────────────────────────────────────
for ns, label in NAMESPACE_LABELS.items():
    subset = df[df["class"] == ns].sort_values("p_corr").head(10).copy()
    if subset.empty:
        continue

    subset["per"] = subset["n_genes"] / subset["n_go"]
    subset = subset.sort_values("per", ascending=True)

    fig, (cbar_ax, main_ax) = plt.subplots(
        1, 2, figsize=(10, max(3, len(subset) * 0.45)),
        gridspec_kw={"width_ratios": [1, 15]},
    )

    norm = mpl.colors.Normalize(vmin=subset["p_corr"].min(), vmax=subset["p_corr"].max())
    sm = cm.ScalarMappable(norm=norm, cmap=cm.bwr_r)
    mpl.colorbar.ColorbarBase(cbar_ax, cmap=cm.bwr_r, norm=norm, orientation="vertical")
    cbar_ax.set_ylabel("FDR corrected p-value", fontsize=9)

    sns.barplot(
        data=subset,
        x="per",
        y="term",
        palette=sm.to_rgba(subset["p_corr"].values),
        ax=main_ax,
    )
    main_ax.set_yticklabels([textwrap.fill(t, 30) for t in subset["term"]])
    main_ax.set_xlabel("Fraction of study genes / GO term genes")
    main_ax.set_title(f"{label}\n({NAMESPACE_DESC[ns].split(':')[0]})")

    plt.tight_layout()
    fname = f"go_enrichment_{ns}.png"
    fig.savefig(os.path.join(out_dir, fname), dpi=200, bbox_inches="tight")
    print(f"Saved {fname}")
    plt.close(fig)

print("\nDone.")
