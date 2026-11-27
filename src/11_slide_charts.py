"""Slide charts: presentation-ready versions of our results, drawn from the CSVs in results/.

Reads ONLY files already in the repo (no raw data needed):
  results/theme_trends/supply_by_era.csv, audience_by_year.csv, contagion_quarterly.csv
    (made by src/10_theme_trends_prototype.py)
  results/critics_vs_crowd/genre_gap.csv, gap_by_decade.csv, match_funnel.csv,
    hall_of_shame_crowd_loved.csv, hall_of_shame_critics_loved.csv
    (made by src/07_critics_vs_crowd.py)
Outputs -> results/slide_charts/  (dark background, 1000 x 800 px, two fit side by side on a slide)
  creatures.png              Q2  share of films per 5-year era with each creature tag (peak marked)
  superheroes_covid.png      Q2  superhero share of yearly ratings + 'Contagion' ratings per quarter
  genre_battle.png           Q3  average rank gap crowd - critics, by genre
  classics_by_decade.png     Q3  % who liked the films of each decade, critics vs crowd
  match_funnel.png           Q3  how many films survive each matching step
  hall_of_shame.png          Q3  biggest critics/crowd disagreements
Run from the project root:  python src/11_slide_charts.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "results/theme_trends"
CVC = ROOT / "results/critics_vs_crowd"
OUT = ROOT / "results/slide_charts"
OUT.mkdir(parents=True, exist_ok=True)

GOLD, BLUE, CREAM, BG = "#E8B10A", "#4AA8E8", "#F3E9D2", "#140505"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": CREAM, "axes.labelcolor": CREAM,
                     "xtick.color": CREAM, "ytick.color": CREAM, "axes.edgecolor": (1, 1, 1, 0.3),
                     "font.size": 15})


def new_fig():
    f = plt.figure(figsize=(10, 8), dpi=100)
    f.patch.set_facecolor(BG)
    return f


def clean(ax):
    ax.set_facecolor(BG)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)


def header(f, title, sub, y=0.94):
    f.text(0.03, y, title, fontsize=22, fontweight="bold", color=GOLD)
    f.text(0.03, y - 0.035, sub, fontsize=13.5, alpha=0.9)


def source(f, text):
    f.text(0.02, 0.015, text, fontsize=11, alpha=0.7)


def save(f, name):
    f.savefig(OUT / name, facecolor=BG)
    plt.close(f)
    print("saved", OUT / name)


def era_label(era):
    """5-year era start -> words: 1955 -> 'late 1950s', 1970 -> 'early 1970s', 2020 -> '2020-23'."""
    if era == 2020:
        return "2020–23"
    return f"early {era}s" if era % 10 == 0 else f"late {era - 5}s"


# %% Q2 creatures: share of films per era (supply)
s = pd.read_csv(THEMES / "supply_by_era.csv")
rows = ["Monsters", "Aliens", "Vampires", "Zombies", "Werewolves", "Dinosaurs", "Superheroes"]
eras = sorted(s.era.unique())
f = new_fig()
ax = f.add_axes([0.0, 0.07, 1, 0.83])
ax.set_facecolor(BG)
for r_i, theme in enumerate(rows):
    x = s[s.theme == theme].set_index("era").pct
    peak = x.idxmax()
    y = len(rows) - 1 - r_i
    for c_i, era in enumerate(eras):
        v = x.get(era, 0.0)
        alpha = 0.05 + 0.95 * (v / x.max()) ** 2.2  # brightness = share relative to that creature's peak
        ax.add_patch(FancyBboxPatch((c_i + 0.07, y + 0.1), 0.86, 0.8, boxstyle="round,pad=0,rounding_size=0.1",
                                    fc=GOLD, ec="none", alpha=alpha))
        if era == peak:
            ax.add_patch(FancyBboxPatch((c_i + 0.07, y + 0.1), 0.86, 0.8, boxstyle="round,pad=0,rounding_size=0.1",
                                        fc="none", ec=CREAM, lw=1.8))
    ax.text(-0.2, y + 0.5, theme, ha="right", va="center", fontsize=17, fontweight="bold")
    ax.text(len(eras) + 0.25, y + 0.5, era_label(peak), ha="left", va="center", fontsize=14, color=GOLD,
            fontweight="bold")
for c_i, era in enumerate(eras):
    if era in (1950, 1970, 1990, 2010):
        ax.text(c_i + 0.5, -0.25, str(era), ha="center", va="top", fontsize=15)
    if era == 2020:
        ax.text(c_i + 0.5, -0.25, "2020–23", ha="center", va="top", fontsize=13)
ax.set_xlim(-4.6, len(eras) + 4.2)
ax.set_ylim(-1.0, len(rows) + 0.1)
ax.axis("off")
header(f, "Every creature had its era", "share of films per 5-year era with the tag · outlined box = peak")
source(f, "Source: MovieLens 32M user tags (results/theme_trends/supply_by_era.csv) · early eras and 2020–23 have few films")
save(f, "creatures.png")

# %% Q2 superheroes (audience) + COVID check
a = pd.read_csv(THEMES / "audience_by_year.csv")
c = pd.read_csv(THEMES / "contagion_quarterly.csv")
f = new_fig()
ax = f.add_axes([0.09, 0.58, 0.86, 0.27])
clean(ax)
sh = a[a.theme == "Superheroes"]
ax.plot(sh.rating_year, sh.pct, color=GOLD, lw=3.2)
pk = sh.loc[sh.pct.idxmax()]
ax.scatter([pk.rating_year], [pk.pct], s=70, color=GOLD, zorder=3)
ax.text(pk.rating_year - 0.6, pk.pct + 1.0, f"{pk.pct:.0f}% of all ratings in {int(pk.rating_year)}",
        ha="right", fontsize=15, fontweight="bold", color=GOLD)
ax.set_ylim(0, 13.5)
ax.set_xlim(sh.rating_year.min() - 1, sh.rating_year.max() + 1)
ax.grid(axis="y", color=(1, 1, 1, 0.12))
ax.tick_params(labelsize=13)
ax.set_ylabel("% of ratings", fontsize=13)
header(f, "Superheroes took over", "% of each year's ratings going to superhero films")
ax3 = f.add_axes([0.09, 0.1, 0.86, 0.25])
clean(ax3)
hl = c.quarter.isin(["2020-Q1", "2020-Q2"])
bars = ax3.bar(range(len(c)), c.per_10k, color=[GOLD if h else CREAM for h in hl], width=0.72)
for b, h in zip(bars, hl):
    if not h:
        b.set_alpha(0.3)
ax3.set_xticks([1.5, 5.5, 9.5])
ax3.set_xticklabels(["2019", "2020", "2021"], fontsize=13)
q = list(c.quarter)
before, after = c.per_10k[q.index("2019-Q2")], c.per_10k[q.index("2020-Q2")]
ax3.text(q.index("2020-Q2"), after + 0.25, f"{after:.1f} (×{after / before:.0f})", ha="center", fontsize=15,
         fontweight="bold", color=GOLD)
ax3.text(q.index("2019-Q2"), before + 0.25, f"{before:.1f}", ha="center", fontsize=14)
ax3.set_ylim(0, 6.6)
ax3.grid(axis="y", color=(1, 1, 1, 0.12))
ax3.set_axisbelow(True)
ax3.tick_params(labelsize=13)
ax3.set_ylabel("per 10,000", fontsize=13)
header(f, "COVID shows up: 'Contagion' (2011)", "its ratings per 10,000 ratings, by quarter", y=0.45)
source(f, "Source: MovieLens 32M ratings + user tags (results/theme_trends/)")
save(f, "superheroes_covid.png")

# %% Q3 genre battle
g = pd.read_csv(CVC / "genre_gap.csv").sort_values("avg_rank_gap")
f = new_fig()
ax = f.add_axes([0.03, 0.1, 0.94, 0.74])
clean(ax)
ax.barh(range(len(g)), g.avg_rank_gap, color=[GOLD if v > 0 else BLUE for v in g.avg_rank_gap], height=0.72)
for i, (genre, v) in enumerate(zip(g.genre, g.avg_rank_gap)):
    ax.text(0.3 if v < 0 else -0.3, i, genre, ha="left" if v < 0 else "right", va="center", fontsize=14)
    ax.text(v + (0.25 if v > 0 else -0.25), i, f"{v:+.1f}", ha="left" if v > 0 else "right", va="center",
            fontsize=13, color=GOLD if v > 0 else BLUE, fontweight="bold")
ax.axvline(0, color=CREAM, alpha=0.5, lw=1)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xlim(-12, 10.5)
ax.set_ylim(-0.7, len(g) + 0.7)
ax.tick_params(labelsize=13)
ax.set_xlabel("average rank gap (percentile points)", fontsize=13)
ax.text(-11.8, len(g), "◀ critics rank it higher", color=BLUE, fontsize=15, fontweight="bold", va="center")
ax.text(10.3, len(g), "crowd ranks it higher ▶", color=GOLD, fontsize=15, fontweight="bold", ha="right", va="center")
n_films = pd.read_csv(CVC / "overall_summary.csv").movies.iloc[0]
header(f, "Who likes which genre more?", f"{n_films:,} films · critics = Rotten Tomatoes · crowd = MovieLens 32M")
save(f, "genre_battle.png")

# %% Q3 classics by decade
d = pd.read_csv(CVC / "gap_by_decade.csv")
corr = pd.read_csv(CVC / "voice_correlations.csv")
r = corr.loc[corr.pair == "MovieLens crowd vs RT critics", "correlation"].iloc[0]
f = new_fig()
ax = f.add_axes([0.11, 0.12, 0.84, 0.7])
clean(ax)
xs = list(range(len(d)))
ax.fill_between(xs, d.avg_crowd, d.avg_critics, color=CREAM, alpha=0.08)
ax.plot(xs, d.avg_critics, color=BLUE, lw=3.2, marker="o", ms=8)
ax.plot(xs, d.avg_crowd, color=GOLD, lw=3.2, marker="o", ms=8)
ax.text(len(d) - 1, d.avg_critics.iloc[-1] + 4, "Critics", color=BLUE, fontsize=16, fontweight="bold", ha="center")
ax.text(len(d) - 1, d.avg_crowd.iloc[-1] - 7, "Crowd", color=GOLD, fontsize=16, fontweight="bold", ha="center")
ax.text(0.15, 99, f"{int(d.decade[0])}s: {d.avg_critics[0]:.0f} vs {d.avg_crowd[0]:.0f}", fontsize=16, fontweight="bold")
ax.set_xticks(xs)
ax.set_xticklabels([f"{int(d.decade[0])}s"] + [f"{str(int(v))[2:]}s" for v in d.decade[1:]], fontsize=13)
ax.set_ylim(30, 106)
ax.set_ylabel("% who liked it", fontsize=13)
ax.grid(axis="y", color=(1, 1, 1, 0.12))
ax.tick_params(labelsize=13)
header(f, "Critics adore the old classics", f"% who liked the films of each decade · overall correlation r = {r:.2f}")
source(f, f"Source: results/critics_vs_crowd/gap_by_decade.csv · crowd = % of ratings ≥ 3.5★ · "
          f"{int(d.decade.iloc[-1])}s = {int(d.movies.iloc[-1])} films only")
save(f, "classics_by_decade.png")

# %% Q3 match funnel
m = pd.read_csv(CVC / "match_funnel.csv").set_index("step").movies
steps = [("MovieLens movies", "MovieLens movies"),
         ("Matched MovieLens <-> RT (title+year)", "Matched to Rotten Tomatoes\n(same title + year ±1)"),
         ("Analysis set (>= 100 ML ratings, >= 20 reviews)", "Enough data\n(≥100 ratings, ≥20 reviews)")]
f = new_fig()
ax = f.add_axes([0.03, 0.15, 0.94, 0.65])
ax.set_facecolor(BG)
for i, (key, label) in enumerate(steps):
    v = m[key]
    y = len(steps) - 1 - i
    last = i == len(steps) - 1
    ax.barh(y, v, height=0.55, color=GOLD if last else CREAM, alpha=1 if last else 0.35)
    ax.text(v / 2 if v > 30000 else v + 1500, y - 0.42, f"{v:,}", va="center", ha="center" if v > 30000 else "left",
            fontsize=18, fontweight="bold", color=GOLD if last else CREAM)
    ax.text(0, y + 0.42, label.replace("\n", " "), fontsize=14, va="center")
ax.set_xlim(0, m.max() * 1.05)
ax.set_ylim(-0.9, len(steps) - 0.3)
ax.axis("off")
header(f, "Matching the critics to our data", "films left after each step of the MovieLens ↔ Rotten Tomatoes join")
source(f, "Source: results/critics_vs_crowd/match_funnel.csv")
save(f, "match_funnel.png")

# %% Q3 hall of shame (5 each way)
cl = pd.read_csv(CVC / "hall_of_shame_crowd_loved.csv").head(5)
ct = pd.read_csv(CVC / "hall_of_shame_critics_loved.csv").head(5)
f = new_fig()
ax = f.add_axes([0.42, 0.1, 0.55, 0.74])
clean(ax)
for block, (df, title, col) in enumerate([(cl, "Crowd loved, critics didn't", GOLD),
                                          (ct, "Critics loved, crowd didn't", BLUE)]):
    base = 11 - block * 6.2
    ax.text(0, base + 0.9, title, fontsize=15, fontweight="bold", color=col)
    for i, row in df.reset_index(drop=True).iterrows():
        y = base - i
        ax.plot([row.critics_score, row.crowd_score], [y, y], color=CREAM, alpha=0.35, lw=2.5)
        ax.scatter(row.critics_score, y, s=110, color=BLUE, zorder=3)
        ax.scatter(row.crowd_score, y, s=110, color=GOLD, zorder=3)
        ax.text(-4, y, f"{row.title} ({int(row.year)})", ha="right", va="center", fontsize=13)
ax.set_xlim(0, 102)
ax.set_ylim(0.2, 12.4)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xlabel("score (0–100)", fontsize=13)
ax.scatter([], [], color=BLUE, s=90, label="Critics")
ax.scatter([], [], color=GOLD, s=90, label="Crowd")
ax.legend(loc="lower right", frameon=False, fontsize=12, labelcolor=CREAM)
header(f, "The Hall of Shame", "the biggest disagreements between critics and crowd")
source(f, "Source: results/critics_vs_crowd/hall_of_shame_*.csv")
save(f, "hall_of_shame.png")
