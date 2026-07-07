#!/usr/bin/env python3
"""
Generate ECS 163 progress report PDF.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, KeepTogether, Image)
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

# ── Output path ────────────────────────────────────────────────────────────
OUT = "/Users/rls/Desktop/youtube-videos/transcriptome-go-visualization/team29progress.pdf"

# ── Document setup ─────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    leftMargin=inch, rightMargin=inch,
    topMargin=inch, bottomMargin=inch,
)

# ── Styles ─────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

BODY    = ParagraphStyle("body",    parent=base["Normal"],  fontSize=11, leading=12.8,
                         spaceBefore=1, spaceAfter=1, alignment=TA_JUSTIFY)
SMALL   = ParagraphStyle("small",   parent=base["Normal"],  fontSize=9,  leading=11,
                         spaceBefore=2, spaceAfter=2)
TITLE   = ParagraphStyle("title",   parent=base["Title"],   fontSize=14, leading=17,
                         spaceAfter=4, alignment=TA_CENTER)
SUBTITLE= ParagraphStyle("sub",     parent=base["Normal"],  fontSize=10, leading=13,
                         spaceAfter=2, alignment=TA_CENTER)
H1      = ParagraphStyle("h1",      parent=base["Heading1"],fontSize=11, leading=13,
                         spaceBefore=6, spaceAfter=2, textColor=HexColor("#1a1a4a"))
H2      = ParagraphStyle("h2",      parent=base["Heading2"],fontSize=10, leading=12.5,
                         spaceBefore=4, spaceAfter=1, textColor=HexColor("#2a2a5a"))
REF     = ParagraphStyle("ref",     parent=base["Normal"],  fontSize=8.5,leading=11,
                         spaceBefore=1, spaceAfter=1)
BULLET  = ParagraphStyle("bullet",  parent=base["Normal"],  fontSize=10, leading=11.9,
                         spaceBefore=0.5, spaceAfter=0.5, leftIndent=16,
                         bulletIndent=4)
CAPTION = ParagraphStyle("caption", parent=base["Normal"],  fontSize=8.5, leading=10.5,
                         spaceBefore=2, spaceAfter=2, alignment=TA_CENTER,
                         textColor=HexColor("#555555"))

def h(n, text):
    return Paragraph(f"<b>{n}. {text}</b>", H1)

def h2(text):
    return Paragraph(f"<b>{text}</b>", H2)

def p(text):
    return Paragraph(text, BODY)

def b(text):
    return Paragraph(f"• {text}", BULLET)

def sp(n=4):
    return Spacer(1, n)

GRAY = HexColor("#e8e8f0")
DGRAY = HexColor("#c0c0d0")
AMBER = HexColor("#ffb300")
NAVY  = HexColor("#1a1a4a")

def table(headers, rows, col_widths=None, small=False):
    style_used = SMALL if small else ParagraphStyle("tc", parent=BODY, fontSize=9.5, leading=12)
    data = [[Paragraph(str(c), ParagraphStyle("th", parent=SMALL,
                                               fontSize=9, fontName="Helvetica-Bold",
                                               alignment=TA_CENTER)) for c in headers]]
    for row in rows:
        data.append([Paragraph(str(c), style_used) for c in row])
    ts = TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("GRID",        (0,0), (-1,-1), 0.4, DGRAY),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, GRAY]),
        ("TOPPADDING",  (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0), (-1,-1), 4),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
    ])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(ts)
    return t

# ── Story ──────────────────────────────────────────────────────────────────
story = []

# ── Title block ────────────────────────────────────────────────────────────
story += [
    Paragraph("Interactive Healthy Blood: A Pathway Atlas<br/>from One Gene Module to a Thousand Donors",
              TITLE),
    Paragraph("Team 29 &nbsp;|&nbsp; Johnny Betmansour · Robin Sayar · Kevali Shah &nbsp;|&nbsp; ECS 163 — Spring 2026",
              SUBTITLE),
    sp(4),
]

# ── §1 ─────────────────────────────────────────────────────────────────────
story += [
    h(1, "Motivations & Objectives"),
    p("Whole blood is the most-measured human tissue in transcriptomics, yet every available dataset "
      "is visualised in isolation: Tabula Sapiens captures it at single-cell resolution, GTEx provides "
      "803 cross-sectional bulk donors, GSE223613 follows 10 donors every three hours across a full day. "
      "No unified interactive view exists that lets a user zoom from the molecular to the cohort scale "
      "within a single tool."),
    p("We propose an interactive atlas with <b>five biological scales</b> — one gene cluster, one cell, "
      "one sample, one sample over time, many samples — with pathway activity as the lens connecting all "
      "five. A pathway like OxPhos is meaningful at every scale: which genes compose it, which "
      "compartments those genes occupy, whether it is active in a given cell type, whether it oscillates "
      "with time of day, how much cohort variance it drives. Our hero gene is <b>SDHA</b> (succinate "
      "dehydrogenase subunit A), the only TCA cycle enzyme also embedded in the inner mitochondrial "
      "membrane as Complex II, making it a natural bridge across all five scales."),
    sp(2),
]

# ── §2 ─────────────────────────────────────────────────────────────────────
story += [
    h(2, "Driving Application & Datasets"),
    p("We use six data sources, each contributing to a distinct scale:"),
    b("<b>Tabula Sapiens</b> (blood): 85,233 whole-blood cells, 22 cell types, scRNA-seq. "
      "Primary expression source for Levels 3–5."),
    b("<b>MitoCarta 3.0</b>: 1,136 experimentally validated human mitochondrial proteins with "
      "sub-mitochondrial localization and pathway annotations (107 leaf pathways)."),
    b("<b>Reactome</b> pathway hierarchy: 873 MitoCarta genes mapped to 16 biologically coherent "
      "Reactome subgroups used for Level 3½."),
    b("<b>GSE223613</b> (Gosch et al. 2023): 10 donors × 8 timepoints (every 3 h), whole-blood "
      "RNA-seq; used for circadian clock face prototype."),
    b("<b>GSE98582</b> (Wittenbrink et al. 2018): 11 donors × microarray, dense 24 h time series; "
      "comparative circadian dataset with dataset-selector support."),
    b("<b>GO Cellular Component enrichment</b> (blood proteome, 4,570 proteins): 247 significant "
      "CC terms collapsed to 9 compartments; used for Level 4 cell-diagram treemap."),
    sp(2),
]

# ── §3 ─────────────────────────────────────────────────────────────────────
story += [
    h(3, "Challenges"),
    b("<b>Cross-scale data compatibility.</b> PeptideAtlas (PSM counts) and Tabula Sapiens (RNA counts) "
      "use different units and scales. We transitioned from PSM to RNA counts mid-project; encoding "
      "choices (area, colour) had to be redesigned for RNA."),
    b("<b>Protein localisation ambiguity.</b> A single protein can appear in multiple compartments "
      "simultaneously. Placing proteins spatially would require an arbitrary choice. We use GO Cellular "
      "Component enrichment as a statistical summary — area encodes how many proteins are <i>annotated</i> "
      "to each compartment, not their physical position."),
    b("<b>Pathway mosaic problem.</b> A single pathway can be active in multiple subcellular zones. "
      "Spatial placement inside an organelle diagram is intractable. The treemap encoding (area ∝ total "
      "RNA expression) avoids this by making the spatial metaphor explicit."),
    b("<b>Circadian data access.</b> GSE223613 and GSE98582 do not provide programmatic access to raw "
      "count matrices without large downloads. Both were approximated with biologically grounded "
      "sine-wave models for the prototype; real data integration remains an open item."),
    b("<b>Co-expression from scRNA-seq.</b> Computing pairwise Pearson correlations across 85,233 cells "
      "requires the full expression matrix; only mean-per-cell-type summaries were retained in our "
      "pipeline. A dedicated computation step is required."),
    b("<b>What to show out of everything.</b> The data supports far more than any screen can legibly "
      "hold — 22 cell types × 107 pathways × thousands of genes, before time and cohort axes. The hard "
      "problem is principled reduction: which aggregation keeps the biology readable without flattening "
      "it. We settled on the 16-group Reactome hierarchy as the mid-granularity lens (>85% of detected "
      "signal, still scannable), but are not fully satisfied — it can merge pathways an expert would "
      "keep distinct, and the right granularity likely differs by scale. An open design tension."),
    sp(2),
]

# ── §4 ─────────────────────────────────────────────────────────────────────
story += [
    h(4, "Background & Related Work"),
    p("Munzner (2014) is our primary design framework: we apply her channel-expressiveness analysis "
      "at every level, ensuring position, area, colour, and motion encode appropriate data types. The "
      "persistent pathway constellation is inspired by brushing-and-linking — a selection context "
      "maintained across views. Biological network tools (STRING, Cytoscape, WGCNA) established the "
      "conventions we follow for co-expression networks: force-directed layout, module-coloured "
      "nodes, edge width ∝ correlation. Andrews curves (Andrews 1972) encode multivariate data as "
      "Fourier series, letting cluster structure be read from visual density. TimeSignature "
      "(Wittenbrink 2018) showed 24-hour internal circadian time is predictable from a single blood "
      "sample, motivating our circadian clock face at the '1 sample × 24 h' scale."),
    sp(2),
]

# ── §5 ─────────────────────────────────────────────────────────────────────
story += [
    h(5, "Method"),
    h2("5.1 Design Overview"),
    p("The visualization is a single self-contained HTML file (CDN-only, no build step) using "
      "D3.js v7, Plotly.js, and Cytoscape.js. Navigation is via a fixed left sidebar with "
      "scroll-linked section highlighting using IntersectionObserver. The organising principle "
      "(Fig. 1) is a <b>drill-down</b> from molecular to cohort scale: the glyph changes at every "
      "scale, but a single persistent pathway token keeps the same biology in view throughout."),
    sp(2),
    KeepTogether([
        Image("/Users/rls/Desktop/youtube-videos/transcriptome-go-visualization/results/scale_ladder.png",
              width=4.9*inch, height=4.9*0.3642*inch),
        Paragraph("<b>Figure 1.</b> The five biological scales (proposal framing) mapped to the six "
                  "implemented levels and their glyphs, with build status. The amber pathway lens "
                  "spans all scales: the SDHA / OXPHOS token persists while only the glyph changes.",
                  CAPTION),
    ]),
    sp(2),
    h2("5.2 Five Scales, Six Current Levels"),
    sp(2),
    table(
        ["Level", "Scale", "Glyph", "Dataset", "Status"],
        [
            ["1", "Genome → Gene", "Co-expression network", "Tabula Sapiens scRNA-seq", "In progress"],
            ["2", "Gene → Pathway", "TCA cycle arcs (CI bands)", "MitoCarta × Tabula Sap.", "✓ Done"],
            ["3", "Mito interior", "Treemap / Radial petal (toggle)", "MitoCarta × Tabula Sap.", "✓ Done"],
            ["3½", "Mito Reactome", "Treemap (16 categories)", "Reactome × Tabula Sap.", "✓ Done"],
            ["4", "Cell compartments", "Treemap (GO CC enrichment)", "GO CC × Tabula Sap.", "✓ Done"],
            ["5", "Cell types", "Bubble scatter (UMAP-style)", "Tabula Sapiens", "✓ Done"],
        ],
        col_widths=[0.35*inch, 1.15*inch, 1.65*inch, 1.9*inch, 1.05*inch],
        small=True,
    ),
    sp(4),
    h2("5.3 Encoding Decisions"),
    b("<b>Area ∝ total RNA counts</b> (sum of mean counts across pathway genes): used at Levels 3, 3½, 4. "
      "Eliminates p-value encoding; size channel is purely data-driven."),
    b("<b>Amber = SDHA / OXPHOS hero</b>: colour is consistent across all levels."),
    b("<b>No spatial placement of proteins</b>: GO CC enrichment is a statistical summary, not a "
      "physical map. Justified by multi-compartment annotation and dynamic localisation."),
    b("<b>Toggle between grid and radial petal</b> at Level 3: treemap for comparison of absolute "
      "magnitudes; radial for quick angular overview of 107 pathway petals."),
    sp(2),
    h2("5.4 Standalone Prototypes (pending integration)"),
    b("<b>Constellation panel</b>: 20 pathway tokens, activity-encoded amber fill, confidence-encoded "
      "ring thickness; scores update on scroll via IntersectionObserver; tokens are pinnable."),
    b("<b>Radial petal glyph</b>: 20 pathway petals per GTEx donor, petal length ∝ |z-score|, "
      "amber = over-enriched, blue = under. Uses live GTEx Portal API data."),
    b("<b>Circadian clock face</b>: 24 h animated clock with 5 pathway petals; dataset switching "
      "(GSE223613 vs GSE98582); individual-donor or mean selection."),
    b("<b>Andrews curves</b>: 17 blood cell types mapped via top-5 PCs (85.1% variance); real "
      "scRNA-seq PCA, cells coloured by lineage."),
    b("<b>Co-expression network</b>: OxPhos module force-directed D3 network, real Pearson "
      "correlations from Tabula Sapiens scRNA-seq (in progress)."),
    sp(2),
    h2("5.5 Storytelling & Narrative Structure"),
    p("We adopt a <b>drill-down</b> structure rather than a linear martini-glass: the five scales "
      "are zoom levels on the same biology, serving both the curious novice (free zooming) and the "
      "analyst with a specific question (jump straight to the cohort scale)."),
    b("<b>Persistent pathway constellation as anchor.</b> A token panel stays beside the canvas at "
      "every scale; selecting the SDHA / OXPHOS token keeps it highlighted across scale changes so "
      "the reader follows one pathway from gene module to cohort — the constellation is the lens, "
      "the canvas is the specimen."),
    b("<b>Guided entry, then free exploration.</b> Each level opens with a short scripted intro "
      "(e.g. “37 mtDNA genes → edges are co-expression → they rise and fall together”) "
      "before handing control to the user."),
    b("<b>Demo path.</b> SDHA gene module → mitochondrial interior → cell-type composition → 24-hour "
      "oscillation → cohort variance, with the pathway reading aligned at every step."),
    sp(2),
    h2("5.6 Changes & Design Decisions Since Proposal"),
    b("<b>Hero switched to a concrete gene (SDHA).</b> The proposal led with abstract pathway "
      "tokens (interferon-α, OxPhos); we anchored the narrative to SDHA, the only TCA enzyme "
      "also in the inner-membrane Complex II, giving a single thread that is biologically meaningful "
      "at all five scales."),
    b("<b>Expression units: PSM → RNA counts.</b> We moved from PeptideAtlas spectral counts to "
      "Tabula Sapiens scRNA-seq, unifying Levels 3–5 on one measurement type; area/colour "
      "encodings were redesigned accordingly."),
    b("<b>Cell-anatomy diagram → GO CC treemap.</b> The proposal placed each gene in its primary "
      "compartment; multi-compartment and dynamic localisation made spatial placement arbitrary, so "
      "Level 4 now uses GO CC enrichment as an explicit statistical summary (area ∝ annotated "
      "proteins) rather than a fabricated physical map."),
    b("<b>Added Level 3½ (Reactome grouping)</b> — a 16-category layer between the 107-leaf "
      "MitoCarta treemap and the cell view for a legible mid-granularity overview."),
    b("<b>Dropped p-value encoding</b> — size now encodes total RNA expression only, keeping the "
      "area channel purely data-driven."),
    b("<b>Datasets adjusted</b> — GSE313156 dropped; GSE98582 added as a dense comparative "
      "circadian series with a dataset selector."),
    sp(2),
]

# ── §6 ─────────────────────────────────────────────────────────────────────
story += [
    h(6, "Evaluation Plan"),
    b("<b>Cognitive walkthrough</b>: can a biology graduate student who did not build the tool follow "
      "the SDHA narrative from Level 1 to Level 5 without instruction? Think-aloud, 3–5 participants."),
    b("<b>Expert validation</b>: do pathway size differences between neutrophils and monocytes at "
      "Level 3 match known biology (monocytes are more metabolically active)?"),
    b("<b>Visual encoding audit (Munzner framework)</b>: per channel, verify expressiveness (right "
      "data type) and effectiveness (most salient available channel)."),
    b("<b>Scalability test</b>: does the radial petal stay legible at 107 pathways vs 16 Reactome "
      "categories? Compare readability at both granularities."),
    sp(2),
]

# ── §7 ─────────────────────────────────────────────────────────────────────
story += [
    h(7, "Preliminary Results"),
    b("<b>PC1 (59% variance in blood MitoCarta expression) separates progenitors from mature cells</b>, "
      "not immune vs non-immune lineages — hematopoietic stem cells (+59) and erythroid progenitors "
      "(+53) highest, erythrocytes and neutrophils (−34) lowest. The dominant axis of mitochondrial "
      "variation is differentiation state, not immune activation."),
    b("<b>Monocytes have ~3× higher total MitoCarta RNA than neutrophils</b> (279 vs 111 mean counts), "
      "visible as markedly larger tiles across all treemap levels. OXPHOS subunits dominate both but "
      "are 32% of monocyte vs 27% of neutrophil expression, with monocytes proportionally richer in "
      "Translation and Lipid Metabolism."),
    b("<b>Reactome grouping</b>: 16 categories describe >85% of detected MitoCarta signal; 107 leaf "
      "pathways add granularity to separate TCA cycle from malate-aspartate shuttle."),
    sp(2),
]

# ── §8 ─────────────────────────────────────────────────────────────────────
story += [
    h(8, "Plan of Activities"),
    sp(2),
    table(
        ["Task", "Timeline", "Status"],
        [
            ["Levels 2–5 + 3½: six core levels (arcs, treemaps, scatter)", "by May 26", "✓ Done"],
            ["Four prototypes (constellation, petal, clock, Andrews)", "by May 28", "✓ Done"],
            ["Level 1: co-expression network (scRNA-seq Pearson)", "May 29–30", "In progress"],
            ["Integrate constellation + GTEx petal into main viz", "May 30–Jun 1", "Upcoming"],
            ["Circadian clock: replace sine models with real data", "Jun 1–2", "Upcoming"],
            ["Andrews curves → Level 5 integration", "Jun 2–3", "Upcoming"],
            ["Final polish + user evaluation (think-aloud, n=3–5)", "Jun 3–4", "Upcoming"],
            ["Final report", "Jun 5", "Upcoming"],
        ],
        col_widths=[4.0*inch, 1.25*inch, 1.1*inch],
        small=True,
    ),
    sp(4),
]

# ── §9  Team Effort Division ────────────────────────────────────────────────
story += [
    KeepTogether([
        h(9, "Team Effort Division"),
        sp(2),
        table(
            ["Member", "Primary Contributions", "Effort (%)"],
            [
                ["Robin Sayar",
                 "Project architecture; all six viz levels (L1–5, 3½); all five prototypes "
                 "(constellation, radial petal, clock, Andrews curves, co-expression); "
                 "full data pipeline; report.",
                 "~75"],
                ["Johnny Betmansour",
                 "Dataset research (GSE223613, GSE98582, GSE56931); literature review; "
                 "biological interpretation.",
                 "~15"],
                ["Kevali Shah",
                 "Evaluation design; walkthrough protocol; design feedback.",
                 "~10"],
            ],
            col_widths=[1.1*inch, 4.1*inch, 0.6*inch],
            small=True,
        ),
        sp(2),
        Paragraph("<i>Note: Robin took on most implementation before task assignments were established — "
                  "a coordination failure, not teammate unwillingness. Explicit ownership has been agreed "
                  "for all remaining work.</i>",
                  ParagraphStyle("note", parent=SMALL, fontSize=8.5, leading=11,
                                 textColor=HexColor("#555555"), alignment=TA_JUSTIFY)),
    ]),
    sp(2),
]

# ── §10  References (excluded from page limit; placed last) ──────────────────
story += [
    h(10, "References"),
    Paragraph("[1] Munzner T. <i>Visualization Analysis and Design.</i> CRC Press, 2014.", REF),
    Paragraph("[2] Tabula Sapiens Consortium. A single-cell transcriptomic atlas of multiple organs "
              "from individual human donors. <i>Science,</i> 376(6594):eabl4896, 2022.", REF),
    Paragraph("[3] Rath S, et al. MitoCarta3.0: an updated mitochondrial proteome now with "
              "sub-organelle localization and pathway annotations. "
              "<i>Nucleic Acids Research,</i> 49(D1):D1541–D1547, 2021.", REF),
    Paragraph("[4] Wittenbrink N, et al. High-accuracy determination of biological timing in human "
              "blood. <i>JCI Insight,</i> 3(24), 2018.", REF),
    Paragraph("[5] Gosch A, Bhardwaj A, Courts C. TrACES of Time. "
              "<i>Forensic Science International: Genetics,</i> 67:102915, 2023.", REF),
    Paragraph("[6] Andrews DF. Plots of high-dimensional data. <i>Biometrics,</i> 28(1):125–136, 1972.", REF),
    Paragraph("[7] Langfelder P, Horvath S. WGCNA: an R package for weighted correlation network "
              "analysis. <i>BMC Bioinformatics,</i> 9:559, 2008.", REF),
    Paragraph("[8] The GTEx Consortium. The GTEx v8 release. <i>Nature,</i> 570:519–525, 2019.", REF),
    Paragraph("[9] Kanehisa M, et al. KEGG for classification and evolutionary analysis of pathways "
              "and genomes. <i>Nucleic Acids Research,</i> 51(D1):D587–D592, 2023.", REF),
    Paragraph("[10] Möller-Levet CS, et al. Effects of insufficient sleep on circadian rhythmicity "
              "and expression amplitude of the human blood transcriptome. "
              "<i>PNAS,</i> 110(12):E1132–E1141, 2013.", REF),
]

# ── Build ──────────────────────────────────────────────────────────────────
doc.build(story)
print(f"PDF written to: {OUT}")
