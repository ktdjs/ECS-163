import csv, itertools
from collections import defaultdict, Counter

gene2paths = {}
path2genes = defaultdict(set)
top2genes = defaultdict(set)   # top-level category (first segment)

with open('data/mitocarta3.tsv') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        sym = row['Symbol'].strip()
        raw = (row['MitoPathways'] or '').strip()
        if not raw or raw in ('0','0.0'):
            continue
        paths = [p.strip() for p in raw.split('|') if p.strip()]
        if not paths:
            continue
        gene2paths[sym] = paths
        for p in paths:
            path2genes[p].add(sym)
            top2genes[p.split('>')[0].strip()].add(sym)

n_genes = len(gene2paths)
counts = [len(v) for v in gene2paths.values()]
multi = sum(1 for c in counts if c > 1)
print(f"Genes with >=1 pathway annotation: {n_genes}")
print(f"Distinct (leaf) pathways: {len(path2genes)}")
print(f"Top-level categories: {len(top2genes)}")
print()
print(f"Genes in >1 pathway: {multi} ({100*multi/n_genes:.1f}%)")
print(f"Genes in exactly 1 pathway: {n_genes-multi} ({100*(n_genes-multi)/n_genes:.1f}%)")
print(f"Mean pathways/gene: {sum(counts)/n_genes:.2f}   max: {max(counts)}")
print()
dist = Counter(counts)
print("Pathways-per-gene distribution:")
for k in sorted(dist):
    print(f"  {k:2d} pathways: {dist[k]:4d} genes")
print()
# Top-level category overlap (genes shared between big categories)
print("=== Top-level category sizes (genes) ===")
for cat, gs in sorted(top2genes.items(), key=lambda x:-len(x[1])):
    print(f"  {len(gs):4d}  {cat}")
print()
print("=== Most overlapping top-level category PAIRS (shared genes) ===")
pairs = []
cats = list(top2genes)
for a,b in itertools.combinations(cats,2):
    inter = top2genes[a] & top2genes[b]
    if inter:
        uni = top2genes[a] | top2genes[b]
        pairs.append((len(inter), len(inter)/len(uni), a, b))
for n,j,a,b in sorted(pairs, reverse=True)[:12]:
    print(f"  {n:4d} shared (Jaccard {j:.2f})  {a}  <->  {b}")
