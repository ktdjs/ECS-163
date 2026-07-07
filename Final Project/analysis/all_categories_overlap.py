import csv, json
from collections import defaultdict

# --- Reactome parent->children (human) ---
children = defaultdict(set)
with open('data/reactome_hierarchy.txt') as f:
    for line in f:
        a,b = line.rstrip('\n').split('\t')[:2]
        if a.startswith('R-HSA') and b.startswith('R-HSA'):
            children[a].add(b)

def descendants(root):
    seen=set(); stack=[root]
    while stack:
        x=stack.pop()
        for c in children.get(x,()):
            if c not in seen:
                seen.add(c); stack.append(c)
    return seen

# --- gene sets per pathway (human) ---
p2g = defaultdict(set)
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c=line.rstrip('\n').split('\t')
        if len(c)>=6 and c[1].startswith('R-HSA') and c[5]=='Homo sapiens':
            p2g[c[1]].add(c[0])

# --- subgroups (categories) from the mito groups file ---
cat_paths = defaultdict(set)     # subgroup_id -> set of reactome_ids
cat_name = {}
cat_group = {}
with open('data/reactome_mito_groups.tsv') as f:
    r=csv.DictReader(f,delimiter='\t')
    for row in r:
        sid=row['subgroup_id']
        cat_paths[sid].add(row['reactome_id'])
        cat_name[sid]=row['subgroup_name'].strip()
        cat_group[sid]=row['group_name'].strip()

def leaf_only(pset):
    # drop any p that is an ancestor of another member
    pset=set(pset)
    leaves=set()
    for p in pset:
        desc=descendants(p)
        if not (desc & (pset-{p})):
            leaves.add(p)
    return leaves

rows=[]
for sid,pset in cat_paths.items():
    leaves=leaf_only(pset)
    leaves=[p for p in leaves if p2g[p]]
    if not leaves: continue
    sizes=[len(p2g[p]) for p in leaves]
    union=set().union(*[p2g[p] for p in leaves])
    nL=len(leaves); tot=sum(sizes)
    idx=tot/len(union)
    rows.append((cat_name[sid], nL, len(union), tot/nL, idx))

print(f"{'category':<52}{'leaf':>5}{'genes':>7}{'avg/p':>7}{'overlap':>9}")
print('-'*80)
for name,nL,ng,avg,idx in sorted(rows,key=lambda x:-x[4]):
    print(f"{name[:50]:<52}{nL:>5}{ng:>7}{avg:>7.1f}{idx:>9.2f}")

# --- whole-set aggregate over ALL leaf pathways in the file ---
all_p=set().union(*cat_paths.values())
all_leaves=[p for p in leaf_only(all_p) if p2g[p]]
U=set().union(*[p2g[p] for p in all_leaves])
T=sum(len(p2g[p]) for p in all_leaves)
print('-'*80)
print(f"AGGREGATE (all leaf pathways, this Reactome subset):")
print(f"  leaf pathways {len(all_leaves)} | distinct genes {len(U)} | memberships {T} | overlap index {T/len(U):.2f}")
