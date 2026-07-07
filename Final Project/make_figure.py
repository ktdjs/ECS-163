#!/usr/bin/env python3
"""
Generate the five-scale ladder figure for the ECS 163 progress report.
Shows the five biological scales (proposal framing) mapped to the six
implemented levels/glyphs, with the persistent pathway lens spanning all.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

OUT = "/Users/rls/Desktop/youtube-videos/transcriptome-go-visualization/results/scale_ladder.png"

NAVY  = "#1a1a4a"
AMBER = "#ffb300"
BLUE  = "#3a6ea5"
DONE  = "#2e7d32"
PROTO = "#b08400"
WIP   = "#a33"
GRAY  = "#5a5a6a"

fig, ax = plt.subplots(figsize=(8.6, 3.05), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 36)
ax.axis("off")

# ── Panel geometry ───────────────────────────────────────────────────────────
n = 5
pad = 1.6
total_w = 100 - 2 * pad
gap = 1.4
pw = (total_w - (n - 1) * gap) / n
top = 33.0
ph = 20.0
bottom = top - ph

scales = [
    ("Scale 1", "One gene\nmodule"),
    ("Scale 2", "One cell\n(mito interior)"),
    ("Scale 3", "One sample\n(cell types)"),
    ("Scale 4", "One sample\n× 24 h"),
    ("Scale 5", "Many samples\n(cohort)"),
]
glyphs = ["network", "treemap", "bubbles", "clock", "petals"]
levels = [
    "L1 · co-expression\nnetwork",
    "L2–3½ · TCA arcs,\ntreemap, radial",
    "L5 · bubble\nscatter (UMAP)",
    "Circadian\nclock face",
    "GTEx petals +\nconstellation",
]
statuses = ["In progress", "Done", "Done", "Prototype", "Prototype"]
status_col = [WIP, DONE, DONE, PROTO, PROTO]

def glyph(ax, kind, cx, cy, s):
    c = NAVY
    if kind == "network":
        pts = [(-0.55, 0.35), (0.5, 0.55), (0.0, -0.1), (-0.4, -0.55), (0.55, -0.45)]
        edges = [(0,2),(1,2),(2,3),(2,4),(0,3),(1,4)]
        for a, b in edges:
            ax.plot([cx+pts[a][0]*s, cx+pts[b][0]*s],
                    [cy+pts[a][1]*s, cy+pts[b][1]*s], color=GRAY, lw=0.8, zorder=1)
        for i,(x,y) in enumerate(pts):
            ax.add_patch(Circle((cx+x*s, cy+y*s), 0.16*s,
                         color=AMBER if i==2 else BLUE, zorder=2))
    elif kind == "treemap":
        rects = [(-0.6,-0.6,0.7,1.2,AMBER),(0.1,-0.6,0.5,0.7,BLUE),
                 (0.1,0.1,0.5,0.5,"#7a9cc6"),(-0.6,0.6,0.0,0.0,None)]
        for x,y,w,h,col in rects:
            if col:
                ax.add_patch(Rectangle((cx+x*s, cy+y*s), w*s, h*s,
                             facecolor=col, edgecolor="white", lw=1.0))
    elif kind == "bubbles":
        np.random.seed(3)
        for i in range(7):
            x = np.random.uniform(-0.6,0.6); y = np.random.uniform(-0.55,0.55)
            r = np.random.uniform(0.1,0.22)
            ax.add_patch(Circle((cx+x*s, cy+y*s), r*s,
                         color=AMBER if i==0 else BLUE, alpha=0.85))
    elif kind == "clock":
        ax.add_patch(Circle((cx, cy), 0.62*s, facecolor="none", edgecolor=NAVY, lw=1.3))
        for ang in range(0,360,30):
            a = np.radians(ang)
            ax.plot([cx+0.52*s*np.cos(a), cx+0.62*s*np.cos(a)],
                    [cy+0.52*s*np.sin(a), cy+0.62*s*np.sin(a)], color=GRAY, lw=0.7)
        ax.plot([cx, cx+0.34*s*np.cos(np.radians(60))],
                [cy, cy+0.34*s*np.sin(np.radians(60))], color=AMBER, lw=1.6)
        ax.plot([cx, cx+0.45*s*np.cos(np.radians(160))],
                [cy, cy+0.45*s*np.sin(np.radians(160))], color=NAVY, lw=1.1)
    elif kind == "petals":
        lens = [0.62,0.4,0.55,0.3,0.5,0.35,0.58,0.42]
        for i,L in enumerate(lens):
            a = np.radians(i*45)
            ax.plot([cx, cx+L*s*np.cos(a)],[cy, cy+L*s*np.sin(a)],
                    color=AMBER if i==0 else BLUE, lw=2.2, solid_capstyle="round")

for i in range(n):
    x0 = pad + i * (pw + gap)
    cx = x0 + pw / 2
    # panel box
    ax.add_patch(FancyBboxPatch((x0, bottom), pw, ph,
                 boxstyle="round,pad=0.0,rounding_size=1.2",
                 facecolor="#f4f4fa", edgecolor=NAVY, lw=1.1))
    # scale label
    sc, name = scales[i]
    ax.text(cx, top - 2.2, sc, ha="center", va="top",
            fontsize=8.5, fontweight="bold", color=NAVY)
    ax.text(cx, top - 4.3, name, ha="center", va="top",
            fontsize=7.6, color=GRAY, linespacing=1.0)
    # glyph
    glyph(ax, glyphs[i], cx, bottom + 7.6, 4.0)
    # level label
    ax.text(cx, bottom + 2.7, levels[i], ha="center", va="center",
            fontsize=6.7, color=NAVY, linespacing=1.05)
    # status pill
    ax.add_patch(FancyBboxPatch((cx-4.6, bottom-2.9), 9.2, 2.3,
                 boxstyle="round,pad=0.0,rounding_size=1.1",
                 facecolor=status_col[i], edgecolor="none"))
    ax.text(cx, bottom-1.75, statuses[i], ha="center", va="center",
            fontsize=6.6, color="white", fontweight="bold")
    # connecting arrow
    if i < n - 1:
        ax.add_patch(FancyArrowPatch((x0+pw+0.05, bottom+ph/2),
                     (x0+pw+gap-0.05, bottom+ph/2),
                     arrowstyle="-|>", mutation_scale=9, color=GRAY, lw=1.0))

# zoom-out caption above
ax.annotate("", xy=(pad+total_w, 35.2), xytext=(pad, 35.2),
            arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.0))
ax.text(pad+total_w/2, 35.6, "zoom out  →  molecular to cohort",
        ha="center", va="bottom", fontsize=7.2, color=GRAY, style="italic")

# pathway-lens ribbon spanning all panels
ry = bottom - 6.6
ax.add_patch(FancyBboxPatch((pad, ry), total_w, 3.1,
             boxstyle="round,pad=0.0,rounding_size=1.4",
             facecolor=AMBER, edgecolor="none", alpha=0.95))
ax.text(pad+total_w/2, ry+1.55,
        "Pathway lens — the SDHA / OXPHOS token persists across every scale; "
        "only the glyph changes",
        ha="center", va="center", fontsize=7.6, color=NAVY, fontweight="bold")

plt.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01)
fig.savefig(OUT, dpi=300, bbox_inches="tight", pad_inches=0.04)
print("Figure written to:", OUT)
