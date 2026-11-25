"""Theme trends prototype: when were zombies, vampires, pandemics, apocalypse... 'in'?

Labels come from MovieLens user tags (regex per theme) + the MovieLens 'War' genre.
Outputs -> results/theme_trends/
  supply_by_era.csv      share of (tagged) films released per 5-year era that carry the theme
  audience_by_year.csv   share of ALL ratings in each rating year that went to theme films
  fresh_by_year.csv      same, but only ratings of films released that year or the year before ("buzz")
  contagion_quarterly.csv  COVID check: Contagion (2011) ratings per 10k ratings, 2019-2021
  theme_supply.png, contagion_covid.png
Run from the project root:  python src/10_theme_trends_prototype.py
"""
import time
from pathlib import Path
import duckdb
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PQ = ROOT / "Data/Parquet/ml-32m"
OUT = ROOT / "results/theme_trends"
OUT.mkdir(parents=True, exist_ok=True)

THEMES = [  # theme, regex on lower(tag)
    ("Zombies", r"\bzombie"),
    ("Vampires", r"\bvampire"),
    ("Virus & pandemic", r"\b(virus|pandemic|epidemic|outbreak|plague|contagion|infection|infected)\b"),
    ("Apocalypse", r"apocalyp|end of the world|nuclear war"),
    ("Dystopia", r"dystopi"),
    ("Superheroes", r"superhero"),
    ("AI & robots", r"artificial intelligence|\brobot"),
    ("Time travel", r"time travel"),
]

con = duckdb.connect()
con.execute(f"create view tags as select * from '{PQ}/tags.parquet'")
con.execute(f"create view ratings as select * from '{PQ}/ratings.parquet'")
con.execute("create table themes(theme varchar, pat varchar)")
con.executemany("insert into themes values (?, ?)", THEMES)

t0 = time.time()
# 1) label movies: one row per (theme, movie)
con.execute(f"""
create table movie_theme as
select t.theme, g.movieId, count(distinct g.userId) as taggers
from tags g join themes t on regexp_matches(lower(g.tag), t.pat)
group by 1, 2
union all
select 'War (genre)', movieId, null from '{PQ}/movies.parquet' where genres like '%War%'
""")
con.execute(rf"""
create table movies as
select movieId, title,
       try_cast(regexp_extract(trim(title), '\((\d{{4}})\)\s*$', 1) as int) as yr,
       movieId in (select movieId from tags) as tagged
from '{PQ}/movies.parquet'
""")
t1 = time.time()

# 2) SUPPLY: % of films released per 5-year era carrying the theme
#    (denominator = films with >=1 tag, because an untagged film can never be labelled; War uses all films)
con.execute("""
create table supply as
with den as (
  select (yr//5)*5 as era, count(*) as all_films, count(*) filter (where tagged) as tagged_films
  from movies where yr between 1950 and 2022 group by 1)
select (m.yr//5)*5 as era, mt.theme, count(distinct mt.movieId) as theme_films,
       any_value(case when mt.theme = 'War (genre)' then den.all_films else den.tagged_films end) as denom
from movie_theme mt join movies m using (movieId) join den on den.era = (m.yr//5)*5
where m.yr between 1950 and 2022 group by 1, 2
""")
con.execute(f"copy (select *, round(100.0*theme_films/denom, 2) as pct from supply order by theme, era) to '{OUT}/supply_by_era.csv' (header)")

# 3) AUDIENCE: share of each rating year's ratings that went to theme films (all films / fresh releases only)
con.execute("""
create table r as
select movieId, year(to_timestamp(timestamp)) as ry, count(*) as n from ratings group by 1, 2
""")
for name, cond in [("audience_by_year", "true"), ("fresh_by_year", "m.yr between r.ry - 1 and r.ry")]:
    con.execute(f"""
    copy (
      with f as (select r.* from r join movies m using (movieId) where {cond}),
           tot as (select ry, sum(n) as total from f group by 1)
      select f.ry as rating_year, mt.theme, sum(f.n) as theme_ratings, any_value(tot.total) as total_ratings,
             round(100.0*sum(f.n)/any_value(tot.total), 2) as pct
      from f join movie_theme mt using (movieId) join tot using (ry)
      group by 1, 2 order by 2, 1
    ) to '{OUT}/{name}.csv' (header)""")

# 4) COVID check: Contagion (2011) per 10k ratings, by quarter
con.execute(f"""
copy (
  with q as (select movieId, date_trunc('quarter', to_timestamp(timestamp)) as q from ratings
             where to_timestamp(timestamp) >= '2019-01-01' and to_timestamp(timestamp) < '2022-01-01')
  select strftime(q.q, '%Y') || '-Q' || quarter(q.q) as quarter,
         count(*) filter (where m.title = 'Contagion (2011)') as contagion_ratings,
         round(1e4 * count(*) filter (where m.title = 'Contagion (2011)') / count(*), 2) as per_10k
  from q join movies m using (movieId) group by q.q order by q.q
) to '{OUT}/contagion_quarterly.csv' (header)""")
t2 = time.time()
print(f"labelling {t1-t0:.1f}s | supply + audience + covid over 32M ratings {t2-t1:.1f}s")

# 5) charts (one series per panel -> one hue, no legend; peak labelled directly)
BLUE, INK, INK2, GRID = "#257de0", "#191919", "#666666", "#e6e6e6"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2})

show = ["Zombies", "Vampires", "Virus & pandemic", "Apocalypse", "Superheroes", "War (genre)"]
df = con.execute("select theme, era, 100.0*theme_films/denom as pct from supply where era >= 1955").df()
fig, axes = plt.subplots(2, 3, figsize=(12, 6.2))
for ax, th in zip(axes.flat, show):
    d = df[df.theme == th].sort_values("era")
    ax.plot(d.era, d.pct, color=BLUE, lw=2, marker="o", ms=4)
    top = d.loc[d.pct.idxmax()]
    end = min(int(top.era) + 4, 2023)  # data ends Oct 2023
    ha = "left" if top.era == d.era.min() else "right" if top.era == d.era.max() else "center"
    ax.annotate(f"peak {int(top.era)}–{str(end)[2:]}\n{top.pct:.1f}%", (top.era, top.pct),
                textcoords="offset points", xytext=(0, 8), ha=ha, fontsize=9, color=INK)
    ax.set_title(th, loc="left", fontsize=11, color=INK, fontweight="semibold")
    ax.set_ylim(0, d.pct.max() * 1.45)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}%")
    ax.set_xticks([1960, 1980, 2000, 2020])
fig.suptitle("When was each subject 'in'?  Share of films released in each 5-year era",
             x=0.01, ha="left", fontsize=13, color=INK, fontweight="semibold")
fig.text(0.01, 0.005, "Source: MovieLens 32M user tags (War = MovieLens genre). Each panel has its own scale. "
         "Last era = 2020–23 only. Prototype - TMDB keywords will make labels cleaner.", fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
fig.savefig(OUT / "theme_supply.png", dpi=200)

c = con.execute(f"select * from '{OUT}/contagion_quarterly.csv'").df()
fig, ax = plt.subplots(figsize=(9, 3.8))
colors = [BLUE if q.startswith("2020-Q1") or q.startswith("2020-Q2") else "#a9c9ef" for q in c.quarter]
ax.bar(c.quarter, c.per_10k, color=colors, width=0.7)
for x, v in zip(c.quarter, c.per_10k):
    if x in ("2019-Q2", "2020-Q2"):
        ax.text(x, v + 0.12, f"{v:.1f}", ha="center", fontsize=9, color=INK)
ax.set_title("COVID shows up in the data: 'Contagion' (2011) ratings per 10,000 ratings (x3 in spring 2020)",
             loc="left", fontsize=12, color=INK, fontweight="semibold")
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.tick_params(axis="x", labelsize=8.5)
fig.text(0.01, 0.01, "Source: MovieLens 32M ratings, 2019–2021.", fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / "contagion_covid.png", dpi=200)
print("wrote", *sorted(p.name for p in OUT.iterdir()))
