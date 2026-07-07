"""
Compute the mito-gene FRACTION for each Level-3½ Reactome category.

mito fraction = (MitoCarta genes in the category subtree) / (all genes in the subtree)

A "category" = a Reactome parent pathway plus every descendant pathway (the whole
subtree), so the gene set is the union over the subtree. Mito genes = MitoCarta 3.0
mapped to Entrez (data/sym2entrez.json). Human pathways only.

This is the weight the Level-3½ blocks should be multiplied by:
    weighted area = RNA total * mito fraction

Usage:  python analysis/category_mito_fraction.py
"""
import json
from collections import defaultdict, deque

# ---- load Reactome human gene2pathway ----
p2g = defaultdict(set)
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and c[1].startswith('R-HSA') and c[5] == 'Homo sapiens':
            p2g[c[1]].add(c[0])

# ---- hierarchy (human only) ----
children = defaultdict(set)
with open('data/reactome_hierarchy.txt') as f:
    for line in f:
        a, b = line.rstrip('\n').split('\t')[:2]
        if a.startswith('R-HSA') and b.startswith('R-HSA'):
            children[a].add(b)

# ---- name -> id (human) ----
name2id = {}
with open('data/reactome_pathways.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 3 and c[0].startswith('R-HSA') and c[2] == 'Homo sapiens':
            name2id.setdefault(c[1], c[0])

mito = {str(v) for v in json.load(open('data/sym2entrez.json')).values()}

def subtree_genes(root_id):
    seen, genes = set(), set()
    q = deque([root_id])
    while q:
        p = q.popleft()
        if p in seen:
            continue
        seen.add(p)
        genes |= p2g.get(p, set())
        q.extend(children.get(p, ()))
    return genes

# Level-3½ viz label -> exact Reactome term name (from the note fields in the HTML)
CATEGORIES = [
    ("Aerobic Resp. & ETC",   "Aerobic respiration and respiratory electron transport"),
    ("Translation",           "Translation"),
    ("Lipid Metabolism",      "Metabolism of lipids"),
    ("Transcription",         "RNA Polymerase II Transcription"),
    ("Stress Response",       "Cellular responses to stress"),
    ("Protein Homeostasis",   "Metabolism of proteins"),
    ("Innate Immune",         "Innate Immune System"),
    ("Mito Biogenesis",       "Mitochondrial biogenesis"),
    ("Mito Protein Degrad.",  "Mitochondrial protein degradation"),
    ("Amino Acid Metab.",     "Metabolism of amino acids and derivatives"),
    ("Apoptosis",             "Apoptosis"),
    ("Autophagy",             "Macroautophagy"),
    ("Vitamin & Cofactor",    "Metabolism of vitamins and cofactors"),
    ("Biological Oxidations",  "Biological oxidations"),
    ("Protein Import",        "Mitochondrial protein import"),
    ("Ca2+ Transport",        "Mitochondrial calcium ion transport"),
]

print(f"{'category':<24}{'reactome id':<16}{'mito':>6}{'total':>7}{'frac':>8}")
print("-" * 61)
for label, term in CATEGORIES:
    pid = name2id.get(term)
    if not pid:
        print(f"{label:<24}{'NOT FOUND':<16}  term='{term}'")
        continue
    g = subtree_genes(pid)
    m = len(g & mito)
    frac = m / len(g) if g else 0
    print(f"{label:<24}{pid:<16}{m:>6}{len(g):>7}{frac:>8.3f}")
