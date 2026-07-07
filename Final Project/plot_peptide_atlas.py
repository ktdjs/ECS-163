import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
results_dir = os.path.join(script_dir, "results")
os.makedirs(results_dir, exist_ok=True)

df = pd.read_csv(os.path.join(data_dir, "peptide_atlas_blood.tsv"), sep="\t")
df = df.sort_values("norm_PSMs_per_100K", ascending=False).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(14, 6))

ax.bar(range(len(df)), df["norm_PSMs_per_100K"], width=1.0, color="#2563eb", edgecolor="none")

ax.set_xlabel("Proteins (sorted by abundance)", fontsize=13)
ax.set_ylabel("norm_PSMs_per_100K", fontsize=13)
ax.set_title("PeptideAtlas Blood Proteome — Normalized PSMs per 100K", fontsize=15, fontweight="bold")

ax.set_xlim(-10, len(df) + 10)
ax.set_xticks([])
ax.set_yscale("log")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

top_n = 10
x_offsets = [300,  450,  600,  750,  900, 1050, 1200, 1350, 1500, 1650]
y_positions = [80000]*top_n
for i in range(top_n):
    gene = df["biosequence_gene_name"].iloc[i]
    val  = df["norm_PSMs_per_100K"].iloc[i]
    ax.annotate(
        gene,
        xy=(i, val),
        xytext=(x_offsets[i], y_positions[i]),
        fontsize=9, fontweight="bold",
        ha="center", va="bottom",
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.7),
    )

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
out_path = os.path.join(results_dir, "peptide_atlas_blood_plot.png")
plt.savefig(out_path, dpi=200)
plt.show()
print(f"Saved to {out_path}")
