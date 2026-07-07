#!/usr/bin/env python3
"""
Generate per-cell-type gene-expression value maps for the Level 1a genome overlay
(GENE_EXPR_LOCI). The HTML keeps the gene LOCI (symbol + chromosome + Mb position)
in gene_expr_loci.js; this script emits one small JSON per cell type holding just
the per-gene RNA mean, lazy-fetched by selectCT() on selection.

Source : data/reactome_genes_celltype_means.tsv  (11,445 genes x 25 cell types)
Loci   : data/gene_locus.tsv                      (genes shown on the karyogram)
Output : results/data/gene_expr/<key>.json  ->  {"SYMBOL": value, ...}

<key> is the cell type name lowercased with all spaces/commas/underscores/hyphens
removed — IDENTICAL to the sanitization selectCT()/renderCompartmentBars() use, so
the page fetches data/gene_expr/<sanitize(selectedCTName)>.json with no extra map.
"""
import csv, json, os, re

ROOT = "/Users/rls/Desktop/youtube-videos/transcriptome-go-visualization"
EXPR = f"{ROOT}/data/reactome_genes_celltype_means.tsv"
LOCI = f"{ROOT}/data/gene_locus.tsv"
OUTDIR = f"{ROOT}/results/data/gene_expr"


def sanitize(s):
    """Lowercase + strip spaces, commas, underscores, hyphens — matches the HTML."""
    return re.sub(r"[\s,_-]+", "", s.lower())


# ── genes that actually appear on the karyogram ────────────────────────────────
loci_syms = set()
with open(LOCI) as f:
    for row in csv.DictReader(f, delimiter="\t"):
        loci_syms.add(row["symbol"].strip())
print(f"Loci genes: {len(loci_syms)}")

# ── read the per-cell-type mean matrix ─────────────────────────────────────────
with open(EXPR) as f:
    reader = csv.reader(f, delimiter="\t")
    header = next(reader)
    # column index -> sanitized cell-type key, for every *_mean column
    mean_cols = {}
    for i, col in enumerate(header):
        if col.endswith("_mean"):
            mean_cols[i] = sanitize(col[: -len("_mean")])
    sym_idx = header.index("symbol")

    per_ct = {key: {} for key in mean_cols.values()}
    for row in reader:
        sym = row[sym_idx].strip()
        if sym not in loci_syms:
            continue
        for i, key in mean_cols.items():
            try:
                v = float(row[i])
            except (ValueError, IndexError):
                v = 0.0
            if v > 0:
                per_ct[key][sym] = round(v, 4)

print(f"Cell types: {len(per_ct)}")

# ── emit one JSON per cell type ────────────────────────────────────────────────
os.makedirs(OUTDIR, exist_ok=True)
manifest = {}
for key, genes in per_ct.items():
    path = f"{OUTDIR}/{key}.json"
    with open(path, "w") as f:
        json.dump(genes, f, separators=(",", ":"))
    manifest[key] = len(genes)
    print(f"  {key:32s} {len(genes):4d} genes  ({os.path.getsize(path)//1024} KB)")

# manifest lets the page know which keys exist (optional, for graceful fallback)
with open(f"{OUTDIR}/_manifest.json", "w") as f:
    json.dump(manifest, f, separators=(",", ":"))
print(f"\n✓ Wrote {len(per_ct)} files + _manifest.json to {OUTDIR}")
