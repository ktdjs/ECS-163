# Why it is possible to actually *know* one whole transcriptome

## The claim

A human transcriptome is ~20,000 genes. Taken as a list, that is not knowable — no
viewer can hold 20,000 independent facts in mind, and no single screen can show them
legibly. The premise of this atlas is that **a transcriptome is not 20,000 independent
dimensions.** Genes are massively *reused*: the same gene participates in many pathways,
and pathways nest into a small number of broad functional categories. Because of this
redundancy, the *effective* complexity of a transcriptome is far smaller than its gene
count, and the whole thing becomes comprehensible **when viewed through the pathway
lens at the right level of abstraction.**

This document records the reasoning and the measurement that backs it.

## The measurement: an overlap index that scales to *n* pathways

Pairwise overlap (Jaccard between every pair of pathways) does not scale: *n* pathways
give *n(n−1)/2* numbers and no single summary. We use one scalar instead:

```
overlap index = (sum of all pathway sizes) / (number of distinct genes)
              = average number of pathways each gene belongs to
```

Interpretation:

- **1.0** — perfect partition, zero overlap (every gene lives in exactly one pathway)
- **> 1.0** — redundancy; e.g. 2.0 means the average gene appears in two pathways
- **max = n** — every gene in every pathway

It needs only two totals, so it is identical to compute for 2 pathways or 2,000.

### Leaf-only, not hierarchical

Reactome pathways are **nested**: "Respiratory electron transport" is a *parent* that
contains Complex I/III/IV assembly as sub-pathways, so its genes are counted in both the
parent and the children. Counting all levels inflates the index with mere *containment*
rather than genuine side-by-side sharing. Every number below is computed over **leaf
pathways only** — parent nodes that are ancestors of another pathway in the set are
dropped, using the Reactome hierarchy (`data/reactome_hierarchy.txt`). This isolates
*lateral* overlap (distinct processes sharing genes) from *vertical* overlap (a process
and its own sub-steps).

The correction is large. Example — **Aerobic respiration & respiratory electron
transport**:

| | all levels | leaf-only |
|---|---|---|
| pathways | 16 | 11 |
| distinct genes | 261 | 210 |
| overlap index | **1.94** | **1.07** |

Almost all of the apparent 1.94 was the parent "Respiratory electron transport" double-
counting its children. The true lateral redundancy is only ~1.07.

## Results: lateral overlap within Reactome categories

Leaf-only overlap index, for the categories that contain more than one leaf pathway
(single-pathway categories are 1.00 by definition and omitted):

| Category | leaf paths | distinct genes | overlap index |
|---|---|---|---|
| Diseases of DNA repair | 12 | 44 | 3.20 |
| Base Excision Repair | 9 | 90 | 3.08 |
| Signaling by Hedgehog | 3 | 51 | 2.76 |
| Translation | 6 | 154 | 2.66 |
| Signaling by Rho/Miro GTPases | 14 | 365 | 2.50 |
| Cell Cycle, Mitotic | 6 | 261 | 2.12 |
| DNA Double-Strand Break Repair | 6 | 129 | 1.94 |
| Diseases of metabolism | 31 | 39 | 1.54 |
| Metabolism of lipids | 53 | 524 | 1.47 |
| Apoptosis | 21 | 141 | 1.40 |
| Innate Immune System | 19 | 657 | 1.18 |
| RNA Polymerase II Transcription | 12 | 362 | 1.18 |
| Metabolism of amino acids and derivatives | 20 | 122 | 1.07 |
| Aerobic respiration & respiratory electron transport | 11 | 210 | 1.07 |
| Metabolism of vitamins and cofactors | 13 | 168 | 1.01 |

(full table produced by `analysis/all_categories_overlap.py`)

Two patterns:

1. **Within a category, lateral overlap is generally modest** (mostly 1.0–1.5). Metabolic
   and respiratory categories in particular are close to partitions — their leaf pathways
   describe largely distinct gene sets. Repair and core signaling categories are the
   exception (2.5–3.2), where many small pathways re-describe the same shared machinery.
2. **The redundancy lives *across* categories, not inside them.** Aggregated over all leaf
   pathways in this Reactome slice:

   > **439 leaf pathways · 5,614 distinct genes · 12,542 memberships · overlap index 2.23**

   Each gene sits in ~2.2 leaf pathways *on average* once you span the whole map — higher
   than almost any single category — because the sharing is between categories (a gene
   used in both metabolism and signaling, etc.).

## Mitochondria vs. the whole cell, in pathway counts

Counting *distinct* Reactome pathways (human) that a gene set touches:

| | Distinct pathways |
|---|---|
| **Whole cell** (all human genes) | **2,845** |
| **Mitochondria** (genes mapped via MitoCarta) | **826** |
| Mito share | **~29%** |

So mitochondrial genes participate in about **826 of the cell's 2,845 pathways — roughly
a third**. Two qualifications:

- These are pathways the mito genes *touch*, not *exclusively mitochondrial* pathways —
  many of the 826 are general pathways (metabolism, apoptosis signaling) a mito gene
  happens to also belong to.
- Counts include pathways at **all hierarchy levels** (parents + children), applied
  consistently to both rows, so the ratio is fair even though the absolute counts include
  nested pathways.

This is the same specialization story from the other direction: a single organelle's gene
set reaches a third of the cell's pathways, yet each of its genes is individually a
specialist (~7 pathways/gene vs ~12 cell-wide). Concentrated coverage by specialist genes
is exactly what lets one compartment be summarized by a small, stable pathway set.
(Produced by `analysis/path_counts.py`.)

### The mito gene set, precisely

"Mitochondrial gene" here means a **MitoCarta 3.0** protein (localization-defined, not
mtDNA — only 37 genes are mtDNA-encoded; ~99% are nuclear-encoded and imported). The
canonical count is **1,136**. The pathway analysis funnels that set down:

| | count |
|---|---|
| MitoCarta 3.0 proteins (canonical) | 1,136 |
| → mapped to an Entrez ID (`data/sym2entrez.json`; Reactome is Entrez-keyed) | 1,124 |
| → present in ≥1 human Reactome pathway | **873** |
| → in *no* Reactome pathway | 251 |

So every "mito fraction" below is computed against the 1,124-gene Entrez set, of which
only 873 actually reach Reactome. The 251 unannotated genes cannot contribute to any
pathway count.

### From 826 touched to 88 exclusively mitochondrial

The 826 *touched* pathways are mostly shared (a mito gene that also sits in a general
metabolism or apoptosis pathway). Ranking each pathway by mito fraction separates the
shared from the irreducibly-mitochondrial:

| mito fraction | pathways |
|---|---|
| ≥ 50% | 177 |
| ≥ 75% | 120 |
| ≥ 90% | 107 |
| **= 100%** | **88** |

**88 pathways are 100% mitochondrial** — every annotated gene is a MitoCarta gene. They
fall into four exclusively-mitochondrial themes:

- **OXPHOS assembly & function** — Complex I biogenesis (68 genes), Complex III/IV
  assembly, ubiquinol biosynthesis, ATP synthesis by chemiosmotic coupling.
- **Mitochondrial gene expression** — mt-rRNA / mRNA / tRNA modification, mitochondrial
  translation initiation/elongation/termination.
- **Core mitochondrial metabolism** — TCA cycle and its regulation, PDH complex,
  fatty-acid β-oxidation steps, branched-chain amino-acid catabolism.
- **Mito-specific cofactor assembly** — iron-sulfur cluster biogenesis, protein
  lipoylation.

This is the flip side of dual-localization: about half of mito genes moonlight in other
compartments, yet there remains a hard core of 88 pathways that **no non-mitochondrial
gene ever enters** — the part of the cell that is mitochondrion and nothing else.
(Produced by `analysis/predominantly_mito.py`.)

## Why this makes a transcriptome knowable

Put the pieces together:

- **Compression.** ~20,000 genes collapse onto a few hundred leaf pathways, which nest
  into **26 top-level categories**. The number of things a viewer must track drops by two
  to three orders of magnitude.
- **Low effective dimensionality.** Genes are not independent. The overlap index of 2.23
  is the quantitative statement that the gene→pathway annotation is dense and structured;
  the same handful of functional modules explain most of the expressed genome. (This
  echoes the PCA result elsewhere in the project: 5 PCs capture 85% of variance across
  cell types.)
- **Specialists vs generalists is itself structure.** Mitochondrial genes participate in
  ~7 Reactome pathways each vs ~12 for the average gene, and the mitochondrion touches
  only ~826 of the cell's ~2,845 pathways (~29%). That a whole organelle's gene set is
  this *concentrated* is exactly what lets one compartment be summarized by a small,
  stable set of pathways.
- **A pathway reads at every scale.** Because the same pathway is meaningful from a gene
  module to a cohort, one label (e.g. OXPHOS) can carry the viewer across all five scales
  of the atlas. The drill-down interface plus the persistent pathway lens is the
  *interface* that exploits this structure — the biology is compressible, and the
  visualization is the decompressor.

**Therefore:** you can know a whole transcriptome not by reading 20,000 genes, but by
reading the much smaller, highly-overlapping set of pathways they collapse into — and by
moving fluidly between levels of abstraction. The overlap index is the evidence that this
collapse is real and not a convenient simplification.

## Caveats

- **Annotation density, not ground truth.** "Pathways per gene" partly reflects how
  thoroughly Reactome has curated a region of biology. The leaf-only correction and the
  consistent Reactome universe make *relative* comparisons fair, but absolute values
  inherit Reactome's coverage bias.
- **This slice, not all of Reactome.** Numbers are computed over the Reactome subset
  reachable from the project's gene set (`data/reactome_gene2pathway.txt`,
  `data/reactome_mito_groups.tsv`), not the entire database.
- **"Knowable" means comprehensible at an abstraction level, not exhaustively.** The claim
  is about tractability through structure, not that every gene-level detail is captured by
  pathways.
