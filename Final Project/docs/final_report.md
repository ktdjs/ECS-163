# Interactive Healthy Blood: A Pathway Atlas from One Gene Module to a Thousand Donors

**Team 29 — Johnny Betmansour, Robin Sayar, Kevali Shah**
**ECS 163 (Information Visualization) — Spring 2026 — Final Progress & Design Report**

---

## 1. Motivation & Problem

Whole blood is the most-measured human tissue in transcriptomics, yet every available dataset
is visualized in isolation: Tabula Sapiens captures it at single-cell resolution, GTEx provides
hundreds of cross-sectional bulk donors, and GSE223613 follows donors across a full day. No
unified interactive view lets a user move from the molecular scale to the cohort scale within
a single tool.

The deeper problem is that a transcriptome — roughly 20,000 genes — is not *knowable* as a list.
No viewer can hold 20,000 independent facts in mind, and no single screen can render them legibly.
The premise of this atlas is that **a transcriptome is not 20,000 independent dimensions.** Genes
are massively reused: the same gene participates in many pathways, and pathways nest into a small
number of broad functional categories. Because of this redundancy, the *effective* complexity of a
transcriptome is far smaller than its gene count, and the whole becomes comprehensible **when viewed
through the pathway lens at the right level of abstraction.**

We quantify this with a single scalar, the **overlap index** = (sum of all pathway sizes) / (number
of distinct genes) = the average number of pathways each gene belongs to. A value of 1.0 is a perfect
partition (every gene in exactly one pathway); values above 1.0 indicate redundancy. Computed over
leaf pathways only (dropping parent nodes that merely contain their children, so we isolate genuine
lateral sharing from vertical containment), the project's Reactome slice gives **439 leaf pathways ·
5,614 distinct genes · 12,542 memberships · overlap index 2.23** — each gene sits in ~2.2 leaf pathways
on average. Crucially, redundancy lives *across* categories, not inside them: most individual categories
are close to partitions (overlap index 1.0–1.5), while repair and core signaling categories are the
exception (2.5–3.2). This structured redundancy — a few hundred pathways nesting into 26 top-level
categories — is what compresses 20,000 genes by two to three orders of magnitude and makes the
transcriptome tractable. (This echoes the project's PCA result: 5 principal components capture ~85% of
variance across cell types.)

Our hero is **SDHA** (succinate dehydrogenase subunit A), the only TCA-cycle enzyme also embedded in
the inner mitochondrial membrane as Complex II of the electron transport chain. SDHA, OXPHOS, and the
mitochondrion form a single thread that is biologically meaningful at every scale — which genes compose
the pathway, which compartment it occupies, how active it is in a given cell type — making it a natural
bridge across all five levels.

## 2. Data Sources

The atlas draws on several real, publicly documented datasets, each anchoring a distinct scale:

- **Tabula Sapiens (blood scRNA-seq)** [Tabula Sapiens Consortium, *Science* 2022]: 85,233 whole-blood
  cells across 22 cell types (the atlas narrative foregrounds 17 blood cell types for the cross-type
  view). This is the primary expression source for Levels 3–5; all RNA-count encodings derive from
  mean expression across pathway genes within a cell type.
- **MitoCarta 3.0** [Rath et al., *Nucleic Acids Research* 2021]: 1,136 experimentally validated human
  mitochondrial proteins with sub-organelle localization and pathway annotations. The pathway analysis
  funnels this set down: 1,124 map to an Entrez ID, of which **873 reach at least one human Reactome
  pathway** (251 are unannotated). Only 37 of the 1,136 are mtDNA-encoded; ~99% are nuclear-encoded and
  imported.
- **Reactome pathway hierarchy** [via Kanehisa-style curated pathway databases; Reactome hierarchy file
  `data/reactome_hierarchy.txt`]: provides the nesting that lets us compute leaf-only overlap and group
  the 873 MitoCarta genes into Reactome categories for Level 3½.
- **GEO GSE223613** [Gosch et al., *Forensic Science International: Genetics* 2023]: 10 donors × 8
  timepoints (every 3 h), whole-blood RNA-seq — the basis for the circadian clock-face prototype.
- **GEO GSE98582** [Wittenbrink et al., *JCI Insight* 2018]: 11 donors, dense 24-h microarray time series,
  used as a comparative circadian dataset with a dataset selector. TimeSignature (Wittenbrink 2018)
  showed that internal circadian time is predictable from a single blood sample, motivating the clock-face
  scale.
- **GO Cellular Component enrichment** (blood proteome): significant CC terms collapsed to a small set of
  compartments, used as the statistical summary behind the Level 4 cell-compartment treemap.

## 3. The Five (Really Six, with 3½) Scales

The visualization is a single self-contained HTML page (D3.js v7, Plotly.js, Cytoscape.js; CDN-only,
no build step) navigated via a fixed sidebar with scroll-linked section highlighting. The organizing
principle is a **drill-down from molecular to cohort scale**: the glyph changes at every level, but a
persistent pathway lens (the amber SDHA / OXPHOS token) keeps the same biology in view throughout.

1. **Level 1 — Genome → Chromosome 5 → SDHA sequence.** Locates SDHA at chromosome 5p15 and zooms to its
   nucleotide sequence (scroll-to-zoom, drag-to-pan). Establishes the hero gene and its inner-mitochondrial-
   membrane residence before any abstraction.
2. **Level 2 — SDHA in the TCA cycle.** A radial arc diagram of the Krebs cycle in the mitochondrial matrix.
   SDHA is the amber hero enzyme. Each arc uses a 3-layer width (faint halo, thick best-estimate line, thin
   lower bound), and particle speed encodes a tunable flux *hypothesis* — explicitly flagged as not measured
   reaction flux (real flux would require ¹³C-MFA or FBA).
3. **Level 3 — All pathways inside the mitochondrion.** A treemap (toggle to radial petal) of MitoCarta 3.0
   pathways (107 leaf pathways) detected in two contrasting blood cell types (neutrophil vs. classical
   monocyte). Area ∝ mean RNA count across pathway genes; OXPHOS (amber) contains SDHA.
4. **Level 3½ — Mitochondrial processes as Reactome categories.** The same MitoCarta genes grouped into
   Reactome categories — now **126 selectable subgroups** (defaulting to 16) — a mid-granularity layer between
   the 107-leaf treemap and the cell view. "Aerobic respiration & ETC" (amber) contains SDHA.
5. **Level 4 — The mitochondrion among cell compartments.** A GO Cellular Component treemap (toggle to radial)
   placing the mitochondrion alongside other compartments; area ∝ mean RNA counts per CC term.
6. **Level 5 — Mitochondrial activity across cell types.** A schematic UMAP-style bubble scatter colored by
   mitochondrial gene expression (amber = high OXPHOS activity), bubble size ∝ total RNA counts.

A **circadian clock-face prototype** (driven by GSE223613, with a GSE98582 selector) extends the thread to
the "one sample × 24 h" scale, alongside constellation, radial-petal, Andrews-curve, and co-expression-network
prototypes that are partially folded into the main page.

## 4. Design Decisions & Munzner-Style Rationale

Munzner's *Visualization Analysis and Design* (2014) is the primary framework: channel/expressiveness
analysis is applied at every level so that position, area, color, and motion encode appropriate data types.

- **Area ∝ total RNA counts.** At Levels 3, 3½, and 4, rectangle (or petal) area encodes the sum of mean RNA
  counts across a pathway/compartment's genes. The size channel is therefore purely data-driven; an earlier
  p-value/enrichment encoding on size was deliberately dropped to keep the channel unambiguous.
- **Treemap vs. radial petal.** Each compartment level offers a toggle: the treemap supports comparison of
  *absolute* magnitudes (aligned, space-filling), while the radial petal gives a quick *angular* overview of
  many pathways at once. Position is kept scale-conventional and coherent within each level.
- **Persistent amber pathway lens.** A single hero color marks SDHA / OXPHOS consistently across all levels.
  Persistent selection is the one piece of state that survives a scale change — the constellation/lens is the
  *lens*, the canvas is the *specimen* (a brushing-and-linking idiom).
- **Log/range encoding and honest uncertainty.** Level 2's 3-layer arc width shows a best estimate and a lower
  bound rather than a single deceptive value, and particle motion is labeled a hypothesis, not data.
- **GO enrichment as a statistical summary, not fabricated spatial localization.** The single most consequential
  design decision: a protein can occupy multiple compartments simultaneously, and dynamic localization makes any
  single spatial placement arbitrary. Rather than fabricate a physical map (the proposal's original
  "cell-anatomy diagram" placing each gene in one compartment), Level 4 uses GO Cellular Component **enrichment as
  an explicit statistical summary** — area encodes *how many genes are annotated to each compartment*, not where
  they physically sit. This trades a seductive but misleading spatial metaphor for an honest one.

## 5. Limitations & Caveats

- **Annotation density, not ground truth.** "Pathways per gene" partly reflects how thoroughly Reactome has
  curated a region of biology. The leaf-only correction and a consistent Reactome universe make *relative*
  comparisons fair, but absolute values inherit Reactome's coverage bias.
- **Annotation contamination.** Pathway membership occasionally misassigns genes — e.g. an OXPHOS subunit such
  as NDUFC2 appearing under "Neutrophil degranulation," or catalase sitting on the border of the mitochondrial
  gene set (peroxisomal by primary localization). Such cases inflate or blur a pathway's apparent footprint and
  are a reminder that the lens reflects curated annotation, not assay-level ground truth.
- **"Touched" vs. "exclusively mitochondrial."** Mitochondrial genes *touch* about 826 of the cell's ~2,845
  Reactome pathways (~29%), but most of those are general pathways a mito gene happens to also enter. Ranking by
  mito fraction separates the shared from the irreducible: only **88 pathways are 100% mitochondrial** (every
  annotated gene is a MitoCarta gene), grouped into OXPHOS assembly/function, mitochondrial gene expression, core
  mitochondrial metabolism, and mito-specific cofactor assembly. The atlas's pathway tiles represent the broader
  "touched" set, so a tile's presence does not imply the pathway is mitochondrion-specific.
- **Gene-basis transition.** The project moved its measurement basis from PeptideAtlas blood-proteome PSM counts
  to Tabula Sapiens scRNA-seq RNA counts mid-project, unifying Levels 3–5 on one measurement type; some legacy
  captions still reference PSM/PeptideAtlas as the proxy. Tabula Sapiens is the intended canonical gene/expression
  basis going forward.
- **Level 4 is an overlap, not a partition.** GO CC compartments share genes (a gene can be annotated to several
  compartments), so the Level 4 treemap is a non-partitioning summary — the areas do not sum to a disjoint whole,
  and a gene may be counted in more than one tile.
- **Knowable means comprehensible, not exhaustive.** The claim is tractability *through structure* at an
  abstraction level, not that every gene-level detail is captured by pathways. The numbers are also computed over
  the project's Reactome subset, not the entire database.

## 6. Remaining / Future Work

- **Full single-cell co-expression network (Level 1).** Computing pairwise Pearson correlations across all 85,233
  cells requires the full expression matrix; the current pipeline retained only mean-per-cell-type summaries, so a
  dedicated computation step is needed to render the OXPHOS co-expression module faithfully.
- **Fully integrating the prototypes.** The constellation, radial-petal (GTEx), Andrews-curve, and circadian
  clock-face prototypes are partially standalone; folding them into the main drill-down (and replacing the clock's
  sine-wave approximations with real GSE223613/GSE98582 counts) is the next consolidation step.
- **Normalizing RNA counts to a per-level percentage.** Area currently encodes raw summed counts; expressing each
  tile as a share of its level's total would make cross-level reading more comparable.
- **User evaluation.** A cognitive walkthrough (can a biology graduate student who did not build the tool follow
  the SDHA thread from Level 1 to Level 5 unaided?), an expert-validation check (do neutrophil-vs-monocyte pathway
  size differences match known biology?), and a Munzner-style visual-encoding audit remain to be run.

---

*Design framework: Munzner (2014). Datasets and methods cited above appear in the project's proposal and progress
reports; biological measurements (overlap index, pathway counts, the 88 exclusively-mitochondrial pathways) are
reproduced by the analysis scripts in `analysis/` and documented in `docs/transcriptome-knowability.md`.*
