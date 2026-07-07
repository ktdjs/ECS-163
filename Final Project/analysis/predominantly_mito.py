"""
Narrow the 826 mito-touched Reactome pathways down to the *predominantly*
(and exclusively) mitochondrial ones.

For each human Reactome pathway, compute the mito fraction:
    mito fraction = (mito genes in pathway) / (all genes in pathway)
and bucket pathways by threshold (>=50/75/90/100%).

Mito-gene basis: data/sym2entrez.json — the MitoCarta 3.0 set (1,136 proteins)
mapped to Entrez IDs (Reactome is keyed on Entrez). The mapping covers 1,124 of
the 1,136; of those, 873 appear in >=1 human Reactome pathway. This is the
MitoCarta basis, NOT the blood-proteome GO enrichment.

Usage:
    python analysis/predominantly_mito.py
"""
import json
from collections import defaultdict

p2g = defaultdict(set)
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and c[1].startswith('R-HSA') and c[5] == 'Homo sapiens':
            p2g[c[1]].add(c[0])

mito = {str(v) for v in json.load(open('data/sym2entrez.json')).values()}

# pathways touched by mito genes
touched = [p for p, g in p2g.items() if g & mito]
print(f"Total distinct human Reactome pathways (all levels): {len(p2g)}")
print(f"Pathways touched by >=1 mito gene: {len(touched)}")
print()

# id -> name
name = {}
with open('data/reactome_pathways.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 2 and c[0].startswith('R-HSA'):
            name[c[0]] = c[1]

rows = []
for p in touched:
    tot = len(p2g[p]); m = len(p2g[p] & mito)
    rows.append((m / tot, m, tot, p, name.get(p, p)))

for thr in (0.5, 0.75, 0.9, 1.0):
    n = sum(1 for r in rows if r[0] >= thr)
    print(f"  >= {int(thr*100):3d}% mito : {n} pathways")
print()
print("Predominantly mitochondrial (>=50%), by mito-fraction, min 5 genes:")
print(f"  {'frac':>5} {'mito':>4} {'tot':>4}  pathway")
for frac, m, tot, p, nm in sorted([r for r in rows if r[0] >= 0.5 and r[2] >= 5], reverse=True):
    print(f"  {frac:5.0%} {m:4d} {tot:4d}  {nm.strip()[:60]}")
