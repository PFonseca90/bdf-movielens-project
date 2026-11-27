"""
09 - Charts for the slides (PNG) from the Critics-vs-Crowd results.
Reads results/critics_vs_crowd/*.csv + the analysis Parquet, writes results/charts/*.png
"""
from pathlib import Path
import duckdb
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "critics_vs_crowd"
OUT = ROOT / "results" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
CVC = (ROOT / "Data" / "Parquet" / "analysis" / "critics_vs_crowd.parquet").as_posix()

CRITICS, CROWD, INK, MUTED = "#c8102e", "#e09a1a", "#222222", "#8a8a8a"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})

# 1. Genre battle (rank gap)
g = pd.read_csv(RES / "genre_gap.csv").sort_values("avg_rank_gap")
fig, ax = plt.subplots(figsize=(8, 6.5))
ax.barh(g.genre, g.avg_rank_gap, color=[CROWD if v > 0 else CRITICS for v in g.avg_rank_gap])
ax.axvline(0, color=INK, lw=0.8)
for y, v in enumerate(g.avg_rank_gap):
    ax.text(v + (0.25 if v > 0 else -0.25), y, f"{v:+.1f}", va="center", ha="left" if v > 0 else "right", fontsize=9)
ax.set_xlabel("Average rank gap (percentile points)\n← critics rank it higher        crowd ranks it higher →")
ax.set_title("Genre Battle: who likes which genre more?", loc="left", fontweight="bold")
lim = g.avg_rank_gap.abs().max() + 2.5
ax.set_xlim(-lim, lim)
fig.tight_layout(); fig.savefig(OUT / "genre_battle.png", dpi=200); plt.close(fig)

# 2. Scatter critics vs crowd
d = duckdb.sql(f"SELECT critics_score, crowd_score, n_ratings FROM read_parquet('{CVC}')").df()
fig, ax = plt.subplots(figsize=(7, 6.5))
ax.scatter(d.critics_score, d.crowd_score, s=4, alpha=0.25, color=INK, linewidths=0)
ax.plot([0, 100], [0, 100], color=MUTED, lw=1, ls="--")
ax.text(97, 99, "perfect agreement", color=MUTED, ha="right", fontsize=9)
r = d.critics_score.corr(d.crowd_score)
ax.set_xlabel("Critics: Rotten Tomatoes Tomatometer (% positive)")
ax.set_ylabel("Crowd: % of MovieLens ratings ≥ 3.5★")
ax.set_title(f"{len(d):,} films: critics and crowd mostly agree (r = {r:.2f})", loc="left", fontweight="bold")
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
fig.tight_layout(); fig.savefig(OUT / "critics_vs_crowd_scatter.png", dpi=200); plt.close(fig)

# 3. Decade
dec = pd.read_csv(RES / "gap_by_decade.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(dec.decade, dec.avg_critics, marker="o", color=CRITICS, label="Critics (Tomatometer)")
ax.plot(dec.decade, dec.avg_crowd, marker="o", color=CROWD, label="Crowd (MovieLens)")
ax.set_xticks(dec.decade); ax.set_xticklabels([f"{d}s" for d in dec.decade])
ax.set_ylabel("% who liked it"); ax.set_ylim(0, 100); ax.legend(frameon=False)
ax.set_title("Critics adore the old classics far more than the crowd", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "gap_by_decade.png", dpi=200); plt.close(fig)

# 4. Match funnel
f = pd.read_csv(RES / "match_funnel.csv")
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(f.step[::-1], f.movies[::-1], color=MUTED)
for y, v in enumerate(f.movies[::-1]):
    ax.text(v, y, f" {v:,}", va="center", fontsize=9)
fig.suptitle(f"From {f.movies.iloc[0]:,} MovieLens films to {f.movies.iloc[5]:,} matched films", x=0.02, ha="left", fontweight="bold")
ax.set_xlabel("movies"); ax.set_xlim(0, f.movies.max() * 1.18)
fig.tight_layout(); fig.savefig(OUT / "match_funnel.png", dpi=200); plt.close(fig)

# 5. Who agrees with whom (correlations)
c = pd.read_csv(RES / "voice_correlations.csv").sort_values("correlation")
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.barh(c.pair, c.correlation, color=MUTED)
for y, v in enumerate(c.correlation):
    ax.text(v, y, f" {v:.2f}", va="center", fontsize=9)
ax.set_xlim(0, 1.05); ax.set_xlabel("Pearson correlation across films")
fig.suptitle("Audiences agree with each other more than with critics", x=0.02, ha="left", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "voice_correlations.png", dpi=200); plt.close(fig)

print("Charts:", sorted(p.name for p in OUT.glob("*.png")))
