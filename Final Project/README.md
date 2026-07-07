# Blood Proteome GO Enrichment – Interactive Visualization

Interactive Gene Ontology (GO) enrichment visualizations for the **PeptideAtlas human blood proteome**.  
Open any of the HTML files in `results/` directly in a browser — no server needed.

## Visualizations

| File | Description |
|------|-------------|
| [`results/go_enrichment_network.html`](results/go_enrichment_network.html) | Force-directed network — nodes = GO terms, edges = shared genes. Hover to see term details and gene lists. |
| [`results/go_enrichment_interactive.html`](results/go_enrichment_interactive.html) | Interactive bubble/scatter of enriched GO terms, colored by namespace. |
| [`results/go_enrichment_dotplot.html`](results/go_enrichment_dotplot.html) | Dot plot of top enriched terms (size = gene count, color = FDR). |

## Reproducing the analysis

### 1. Install dependencies

```bash
pip install goatools pandas numpy matplotlib seaborn plotly networkx
```

### 2. Run GO enrichment

```bash
python peptide_atlas_go_enrichment.py   # computes enrichment → results/go_enrichment_results.tsv
```

### 3. Generate interactive HTMLs

```bash
python go_network_graph.py   # network graph
python go_enrichment.py      # dotplot + interactive scatter
```

### Data

- `data/peptide_atlas_blood.tsv` – raw PeptideAtlas blood proteome export  
- `data/peptide_atlas_unique_genes.tsv` – unique gene symbols used as the study set  
- Large background files (`go-basic.obo`, `gene2go`) are downloaded automatically on first run.

## Namespace color coding

| Color | Namespace |
|-------|-----------|
| Blue  | Biological Process |
| Red   | Molecular Function |
| Green | Cellular Component |
