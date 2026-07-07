import json
import re
from collections import defaultdict
import pandas as pd

em=pd.read_csv("data/ts_blood_celltype_means.tsv",sep="\t")
em["ens0"]=em["ensembl"].str.split(".").str[0]
em=em.drop_duplicates("ens0").set_index("ens0"); expr_ens=set(em.index)

children=defaultdict(set); parents=defaultdict(set); nodes=set()
for line in open("data/reactome_hierarchy.txt"):
    f=line.rstrip("\n").split("\t")
    if len(f)<2: continue
    p,c=f[0],f[1]
    if not(p.startswith("R-HSA") and c.startswith("R-HSA")): continue
    children[p].add(c); parents[c].add(p); nodes|={p,c}
p2ens=defaultdict(set); pname={}
for line in open("data/Ensembl2Reactome_All_Levels.txt"):
    f=line.rstrip("\n").split("\t")
    if len(f)<6 or f[5]!="Homo sapiens" or not f[0].startswith("ENSG"): continue
    p2ens[f[1]].add(f[0].split(".")[0]); pname[f[1]]=f[3]; nodes.add(f[1])
roots=set(n for n in nodes if not parents[n])
leaves=[n for n in nodes if not children[n]]

# ancestors (incl self) via upward DAG walk -- memoized
_anc={}
def anc(n):
    if n in _anc: return _anc[n]
    s={n}
    for p in parents[n]: s|=anc(p)
    _anc[n]=s; return s
# descendant leaves of a node
_dl={}
def desc_leaves(n):
    if n in _dl: return _dl[n]
    if not children[n]: r={n}
    else:
        r=set()
        for c in children[n]: r|=desc_leaves(c)
    _dl[n]=r; return r

leaf_genes={l:(p2ens.get(l,set())&expr_ens) for l in leaves}
leaf_genes={l:g for l,g in leaf_genes.items() if g}

DET=0.10
def passing(l, col): return (em.loc[list(leaf_genes[l]),col]>=DET).mean()>0.9

# cache passing-leaf sets per cell-type column
COLS={"mono":"classical_detect","neut":"neutrophil_detect"}
passleaves={k:set(l for l in leaf_genes if passing(l,c)) for k,c in COLS.items()}

print(f"passing leaves ({COLS['mono']} >= {DET}, >90% genes): "
      f"{len(passleaves['mono'])} of {len(leaf_genes)}")

def lca_of(leafset):
    leafset=list(leafset)
    if not leafset: return []
    common=set.intersection(*[anc(l) for l in leafset])
    # lowest = common nodes not an ancestor of any other common node
    return [c for c in common if not any(c!=c2 and c in anc(c2) for c2 in common)]

# ── report table: LCA of passing leaves per root category (monocyte) ──
rows=[]
for R in sorted(roots):
    pls=[l for l in passleaves["mono"] if R in anc(l)]
    if not pls: continue
    for lo in lca_of(pls):
        dl=desc_leaves(lo)
        rows.append({"category":pname.get(R,R)[:32],"n_pass":len(pls),
                     "LCA":pname.get(lo,lo)[:40],"LCA_is_root":(lo in roots),
                     "leaves_under_LCA":len(dl),
                     "pass_under_LCA":len(dl&passleaves["mono"])})
df=pd.DataFrame(rows).sort_values(["category"])
print(df.to_string(index=False))

# ── per-subgroup pass stats for the Level 3½ viz (results/l3r_pass.json) ──
# subgroup ids are the Reactome nodes rendered as bars in the visualization
ids=re.findall(r'"id": "(R-HSA-\d+)"',
               open("results/transcriptome_multilevel_viz.html").read())

def subgroup_stats(node, cell):
    measured=[l for l in desc_leaves(node) if l in leaf_genes]
    if not measured: return None
    pset=passleaves[cell]
    pls=[l for l in measured if l in pset]
    lcas=lca_of(pls)
    lca_name=" / ".join(sorted(pname.get(x,x) for x in lcas)) if lcas else None
    return {"passFrac":round(len(pls)/len(measured),4),
            "nPass":len(pls),"nLeaves":len(measured),
            "lcaName":lca_name}

def gene_coverage(node):
    # genes annotated to this subgroup's descendant leaves, regardless of whether
    # Tabula Sapiens measured them. measured = annotated ∩ expressed-universe.
    # the >90% test silently drops the (annotated − measured) genes; surface that.
    annot=set()
    for l in desc_leaves(node): annot|=p2ens.get(l,set())
    return len(annot), len(annot & expr_ens)

out={}
for i in ids:
    rec={}
    for cell in COLS:
        s=subgroup_stats(i,cell)
        if s: rec[cell]=s
    if rec:
        nAnnot,nMeas=gene_coverage(i)
        rec["nGenesAnnotated"]=nAnnot
        rec["nGenesMeasured"]=nMeas
        out[i]=rec

with open("results/l3r_pass.json","w") as fh:
    json.dump(out,fh,separators=(",",":"),sort_keys=True)
print(f"wrote results/l3r_pass.json for {len(out)}/{len(ids)} subgroups")
