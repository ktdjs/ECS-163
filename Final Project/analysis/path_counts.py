import json
from collections import defaultdict
e2p = defaultdict(set)
all_paths=set()
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c=line.rstrip('\n').split('\t')
        if len(c)>=6 and c[1].startswith('R-HSA') and c[5]=='Homo sapiens':
            e2p[c[0]].add(c[1]); all_paths.add(c[1])
mito={str(v) for v in json.load(open('data/sym2entrez.json')).values()}
mito_paths=set()
for g in mito:
    if g in e2p: mito_paths|=e2p[g]
print(f"Total distinct human pathways (whole cell): {len(all_paths)}")
print(f"Pathways touched by mitochondrial genes   : {len(mito_paths)}")
print(f"Mito share                                : {100*len(mito_paths)/len(all_paths):.0f}%")
