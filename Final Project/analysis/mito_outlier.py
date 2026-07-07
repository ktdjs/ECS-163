import json, random, statistics as st
from collections import defaultdict

e2p = defaultdict(set)
with open('data/reactome_gene2pathway.txt') as f:
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and c[1].startswith('R-HSA') and c[5] == 'Homo sapiens':
            e2p[c[0]].add(c[1])

all_genes = list(e2p.keys())
bg_counts = [len(e2p[g]) for g in all_genes]

mito_entrez = {str(v) for v in json.load(open('data/sym2entrez.json')).values()}
mito_in = [g for g in mito_entrez if g in e2p]
mito_counts = [len(e2p[g]) for g in mito_in]

print(f"Human genes in Reactome: {len(all_genes)}")
print(f"Mito genes mapped to Reactome: {len(mito_in)} / {len(mito_entrez)}")
print()
print("PATHWAYS PER GENE")
print(f"  background  mean {st.mean(bg_counts):.2f}  median {st.median(bg_counts):.0f}")
print(f"  mito        mean {st.mean(mito_counts):.2f}  median {st.median(mito_counts):.0f}")
print()

# Coverage: distinct pathways covered by the mito set vs random same-size sets
mito_cov = len(set().union(*[e2p[g] for g in mito_in]))
n = len(mito_in)
random.seed(0)
sims = []
for _ in range(2000):
    samp = random.sample(all_genes, n)
    sims.append(len(set().union(*[e2p[g] for g in samp])))
mean_sim = st.mean(sims); sd_sim = st.pstdev(sims)
z = (mito_cov - mean_sim)/sd_sim
ge = sum(1 for s in sims if s >= mito_cov)
print("DISTINCT PATHWAY COVERAGE (set of {} genes)".format(n))
print(f"  mito set covers      {mito_cov} distinct pathways")
print(f"  random same-size set {mean_sim:.0f} +/- {sd_sim:.0f}  (z = {z:+.1f})")
print(f"  random sets >= mito:  {ge}/2000  -> mito covers {'FEWER' if z<0 else 'MORE'} pathways than random")
