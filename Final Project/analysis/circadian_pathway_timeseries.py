"""
Compute REAL circadian pathway-activity time-series for the clock-face viz
(results/prototype_clock_face.html) from GEO RNA-seq counts.

Dataset: GSE223613 (Gosch et al. 2023) — whole-blood RNA-seq, 10 participants
(A-J) sampled every 3 h over 24 h (08:00, 11:00, 14:00, 17:00, 20:00, 23:00,
02:00, 05:00). 80 samples, gene symbols as row names.

Method per pathway module:
  log2(CPM+1) per gene/sample -> z-score each gene across the 80 samples ->
  pathway score(sample) = mean z over the module's genes present in the matrix.
  Aggregate by timepoint (mean across the 10 donors) and per donor.
  Peak hour = timepoint of the max mean score.

Inputs (download once from GEO; not committed):
  GSE223613_counts.txt.gz          (suppl/)
  GSE223613_series_matrix.txt.gz   (matrix/)  -> sampling time + participant
Usage:
  python analysis/circadian_pathway_timeseries.py <counts.txt.gz> <series_matrix.txt.gz> [out.json]
"""
import sys, gzip, json, math

PATHS = {
 'oxphos': ['SDHA','SDHB','SDHC','UQCRC1','UQCRC2','UQCRFS1','ATP5F1A','ATP5F1B',
            'ATP5MC1','NDUFA1','NDUFB1','NDUFS1','NDUFV1','COX5A','COX6B1','COX4I1','CYC1'],
 'ifna':   ['IFIT1','IFIT3','MX1','MX2','ISG15','OAS1','OAS2','OAS3','RSAD2','IFI44',
            'IFI44L','STAT1','IRF7','OASL','USP18','HERC5'],
 'circ':   ['ARNTL','CLOCK','PER1','PER2','PER3','CRY1','CRY2','NR1D1','NR1D2','DBP',
            'TEF','NPAS2','CIART','BHLHE40','BHLHE41'],
 'hsp':    ['HSP90AA1','HSPA1A','HSPA1B','DNAJB1','HSPB1','HSPH1','BAG3','HSPA6',
            'DNAJA1','SERPINH1'],
 'neut':   ['ELANE','MPO','CEACAM8','CXCR2','S100A8','S100A9','FUT4','DEFA4','LCN2',
            'LTF','CAMP','CEACAM6'],
}
TPS = [8, 11, 14, 17, 20, 23, 2, 5]


def main():
    counts_path = sys.argv[1]
    series_path = sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else 'gse223613_real.json'

    # sample order -> (timepoint hour, participant)
    times, parts = [], []
    with gzip.open(series_path, 'rt') as f:
        for line in f:
            if line.startswith('!Sample_characteristics_ch1'):
                vals = [v.strip().strip('"') for v in line.rstrip('\n').split('\t')[1:]]
                if vals and vals[0].startswith('sampling time:'):
                    times = [float(v.split(':')[1].strip().split('.')[0]) for v in vals]
                elif vals and vals[0].startswith('participant:'):
                    parts = [v.split(':')[1].strip() for v in vals]

    wanted = set(g for L in PATHS.values() for g in L)
    genes = {}
    with gzip.open(counts_path, 'rt') as f:
        nS = len(f.readline().rstrip('\n').split('\t')) - 1
        colsum = [0.0] * nS
        for line in f:
            p = line.rstrip('\n').split('\t')
            v = [float(x) for x in p[1:]]
            for i in range(nS):
                colsum[i] += v[i]
            if p[0] in wanted:
                genes[p[0]] = v
    assert nS == len(times) == 80, (nS, len(times))

    logcpm = {g: [math.log2(v[i] / colsum[i] * 1e6 + 1) for i in range(nS)] for g, v in genes.items()}

    def z(x):
        m = sum(x) / len(x)
        sd = (sum((a - m) ** 2 for a in x) / len(x)) ** 0.5 or 1.0
        return [(a - m) / sd for a in x]
    zg = {g: z(v) for g, v in logcpm.items()}

    psample = {}
    for pid, glist in PATHS.items():
        found = [g for g in glist if g in zg]
        psample[pid] = [sum(zg[g][i] for g in found) / len(found) for i in range(nS)]

    part_ids = sorted(set(parts))

    def scores_for(pid, participant=None):
        out = []
        for tp in TPS:
            idxs = [i for i in range(nS) if times[i] == tp and (participant is None or parts[i] == participant)]
            out.append(round(sum(psample[pid][i] for i in idxs) / len(idxs), 4) if idxs else 0.0)
        return out

    donors = [{'id': f'Participant {p}', 'scores': {pid: scores_for(pid, p) for pid in PATHS}} for p in part_ids]
    meanScores = {pid: scores_for(pid) for pid in PATHS}
    peak = {pid: TPS[max(range(len(TPS)), key=lambda k: meanScores[pid][k])] for pid in PATHS}

    out = {
        'title': 'GSE223613',
        'subtitle': 'Whole blood RNA-seq · Gosch et al. 2023 · 10 donors · 8 timepoints (every 3 h) · real counts',
        'nDonors': len(part_ids), 'timepoints': TPS, 'donors': donors,
        'meanScores': meanScores, 'peak': peak,
        'genesUsed': {pid: [g for g in PATHS[pid] if g in zg] for pid in PATHS},
    }
    json.dump(out, open(out_path, 'w'))
    print(f'wrote {out_path}  | peak hours: {peak}')


if __name__ == '__main__':
    main()
