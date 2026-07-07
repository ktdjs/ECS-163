import csv
from collections import defaultdict

SUBGROUP = 'R-HSA-1428517'

# pathways listed under this category (exclude the parent self-row)
pathways = []
with open('data/reactome_mito_groups.tsv') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        if row['subgroup_id'] == SUBGROUP and row['reactome_id'] != SUBGROUP:
            pathways.append((row['reactome_id'], row['pathway_name'].strip()))

pids = {p for p,_ in pathways}

# gene sets per pathway (human, entrez)
p2g = defaultdict(set)
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and c[5] == 'Homo sapiens' and c[1] in pids:
            p2g[c[1]].add(c[0])
# also parent union
parent = set()
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and c[5]=='Homo sapiens' and c[1]==SUBGROUP:
            parent.add(c[0])

sizes = {p: len(p2g[p]) for p,_ in pathways if p2g[p]}
union = set().union(*[p2g[p] for p,_ in pathways if p2g[p]])
n_path = len(sizes)
total_memberships = sum(sizes.values())

print(f"Category: Aerobic respiration & respiratory electron transport ({SUBGROUP})")
print(f"Parent pathway's own gene set (union as Reactome defines it): {len(parent)}")
print()
print(f"Total distinct genes across child pathways : {len(union)}")
print(f"Total child pathways (with genes)          : {n_path}")
print(f"Sum of pathway sizes (memberships)         : {total_memberships}")
print(f"Avg genes per pathway                      : {total_memberships/n_path:.1f}")
print(f"OVERLAP INDEX = memberships / distinct genes: {total_memberships/len(union):.2f}")
print(f"  -> each gene belongs to {total_memberships/len(union):.2f} of these pathways on average")
print()
# how many genes appear in >1 pathway
gene_pcount = defaultdict(int)
for p,_ in pathways:
    for g in p2g[p]:
        gene_pcount[g]+=1
multi = sum(1 for v in gene_pcount.values() if v>1)
print(f"Genes in >1 pathway: {multi}/{len(union)} ({100*multi/len(union):.0f}%)")
print()
print("Per-pathway sizes:")
for p,name in sorted(pathways, key=lambda x:-sizes.get(x[0],0)):
    if sizes.get(p): print(f"  {sizes[p]:4d}  {name}")
