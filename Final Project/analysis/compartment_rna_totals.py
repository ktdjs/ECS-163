"""
Compute Level-4 compartment RNA totals consistently for all compartments.

area = sum of mean RNA counts across a compartment's genes, in one cell type
       (default: classical monocyte), from a full Tabula Sapiens blood matrix.

The original 9 hard-coded totals in transcriptome_multilevel_viz.html were never
reproducible from this repo (the full TS matrix lived only in Colab). This script
regenerates ALL 11 compartments from one source so they are comparable, and adds
lysosome + endosome.

Usage:
    python analysis/compartment_rna_totals.py /path/to/full_ts_blood_mean_expr.tsv [cell_type]

Expected matrix format: TSV with a 'Symbol' column + one column per cell type,
values = mean expression per gene in that cell type (same convention as
data/tabula_sapiens_mito_expr.tsv, but for ALL genes, not just MitoCarta).
"""
import sys, csv, ast

ENRICH = "results/go_enrichment_results.tsv"

# compartment label -> GO Cellular Component parent term (as written in the enrichment file)
COMPARTMENTS = {
    "Mitochondrion":         "mitochondrion",
    "Cytosol":               "cytosol",
    "Nucleus":               "nucleus",
    "Plasma Membrane":       "plasma membrane",
    "Endoplasmic Reticulum": "endoplasmic reticulum",
    "Peroxisome":            "peroxisome",
    "Extracellular Region":  "extracellular region",
    "Golgi Apparatus":       "Golgi apparatus",
    "Cytoskeleton":          "cytoskeleton",
    "Lysosome":              "lysosome",   # added
    "Endosome":              "endosome",   # added
}

def compartment_genes():
    term2genes = {}
    with open(ENRICH) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["class"] == "cellular_component":
                term2genes[row["term"]] = ast.literal_eval(row["study_genes"])
    return {label: term2genes[term] for label, term in COMPARTMENTS.items()
            if term in term2genes}

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    matrix_path = sys.argv[1]
    cell_type = sys.argv[2] if len(sys.argv) > 2 else "classical monocyte"

    expr = {}
    with open(matrix_path) as f:
        r = csv.DictReader(f, delimiter="\t")
        if cell_type not in r.fieldnames:
            sys.exit(f"cell type '{cell_type}' not found. Columns: {r.fieldnames}")
        for row in r:
            try:
                expr[row["Symbol"]] = float(row[cell_type])
            except (ValueError, KeyError):
                pass

    comp = compartment_genes()
    print(f"cell type: {cell_type}   matrix genes: {len(expr)}\n")
    print(f"{'compartment':<24}{'genes':>6}{'found':>6}{'RNA total':>11}")
    print("-" * 47)
    out = {}
    for label, genes in comp.items():
        found = [g for g in genes if g in expr]
        total = sum(expr[g] for g in found)
        out[label] = (len(genes), len(found), total)
        flag = "  <-- LOW COVERAGE" if len(found) < 0.8 * len(genes) else ""
        print(f"{label:<24}{len(genes):>6}{len(found):>6}{total:>11.1f}{flag}")
    print("\nIf coverage is low, the matrix is not the full transcriptome "
          "(e.g. the mito-only file) and totals for non-mito compartments are invalid.")

if __name__ == "__main__":
    main()
