"""
08 - Export the real Critics-vs-Crowd results for the classroom game.

Reads  Data/Parquet/analysis/critics_vs_crowd.parquet  (from 07)
       Data/Parquet/ml-32m/tags.parquet                (MovieLens user tags)
Writes presentation/film-snob-game/src/gameData.json

The game (React) only reads that JSON, so: re-run 07 + 08 -> rebuild the game
-> the presentation shows the newest numbers. No hand-typed numbers anywhere.
"""
from pathlib import Path
import json, re, hashlib
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CVC = (PROJECT_ROOT / "Data" / "Parquet" / "analysis" / "critics_vs_crowd.parquet").as_posix()
TAGS = (PROJECT_ROOT / "Data" / "Parquet" / "ml-32m" / "tags.parquet").as_posix()
RESULTS = PROJECT_ROOT / "results" / "critics_vs_crowd"
OUT = PROJECT_ROOT / "presentation" / "film-snob-game" / "src" / "gameData.json"

FAMOUS_ML_RATINGS = 10000     # only films most people have heard of go in the quiz
FAMOUS_CRITIC_REVIEWS = 40
PER_SIDE = 12                 # 12 crowd-loved + 12 critics-loved films

con = duckdb.connect()

# The "headline" genre of a film: MovieLens lists genres alphabetically,
# so we pick the most distinctive one with a priority list.
PRIORITY = ["Documentary", "Horror", "Animation", "Musical", "Western", "Film-Noir", "War",
            "Sci-Fi", "Fantasy", "Romance", "Comedy", "Crime", "Mystery", "Thriller",
            "Children", "Action", "Adventure", "Drama"]
MOTIF = {"Horror": "fin", "Thriller": "eye", "Mystery": "eye", "Crime": "eye", "Film-Noir": "eye",
         "Comedy": "slice", "Romance": "heart", "Animation": "heart", "Children": "heart",
         "Musical": "heart", "Action": "sun", "Adventure": "sun", "Western": "sun", "War": "city",
         "Documentary": "city", "Drama": "crescent", "Sci-Fi": "crescent", "Fantasy": "crescent"}
PALETTES = {
    "fin": [["#0b3a53", "#041b2b", "#ff5d5d"], ["#123b2f", "#05140f", "#e94f37"]],
    "eye": [["#2a2a2a", "#080808", "#f2f2f2"], ["#3b1f2b", "#0c0609", "#ffcf4a"]],
    "slice": [["#ffcf4a", "#b3261e", "#fff4d6"], ["#ff9f1c", "#6a1b2a", "#fff1c1"]],
    "heart": [["#ff8fb1", "#8c1d4f", "#fff1c1"], ["#7bdff2", "#1b4965", "#fdf0d5"]],
    "sun": [["#ff7a18", "#7a1230", "#ffd166"], ["#f6bd60", "#5c2a12", "#fff3b0"]],
    "city": [["#4a5a6a", "#161c24", "#9fb4c8"], ["#5e503f", "#1b1611", "#e0c9a6"]],
    "crescent": [["#1d2b4f", "#0a0f1f", "#c9d6ff"], ["#2d1e4f", "#0b0718", "#f1c0e8"]],
}

def headline_genres(genres: str) -> str:
    g = [x for x in PRIORITY if x in genres.split("|")]
    return " · ".join(g[:2]) if g else "Drama"

def short(text, limit=150):
    if not text:
        return "No critics consensus published."
    text = re.sub(r"<[^>]+>", "", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    return (cut[: cut.rfind(" ")] if " " in cut else cut).rstrip(",;:") + "…"

# ---------------- pick the films ----------------
# Ranked by RANK GAP (see 07). We also require the raw scores to point the
# same way, so the bars shown in the quiz never contradict the answer.
films = con.sql(f"""
    (SELECT *, 'crowd'   AS side FROM read_parquet('{CVC}')
      WHERE n_ratings >= {FAMOUS_ML_RATINGS} AND critic_reviews >= {FAMOUS_CRITIC_REVIEWS} AND gap > 5
      ORDER BY rank_gap DESC LIMIT {PER_SIDE})
    UNION ALL
    (SELECT *, 'critics' AS side FROM read_parquet('{CVC}')
      WHERE n_ratings >= {FAMOUS_ML_RATINGS} AND critic_reviews >= {FAMOUS_CRITIC_REVIEWS} AND gap < -5
      ORDER BY rank_gap ASC LIMIT {PER_SIDE})
""").df()

# ---------------- what the crowd wrote: top MovieLens tags ----------------
ids = ",".join(str(int(i)) for i in films.movieId)
tags = con.sql(f"""
    WITH t AS (
        SELECT movieId, lower(trim(tag)) AS clean_tag, COUNT(DISTINCT userId) AS users
        FROM read_parquet('{TAGS}')
        WHERE movieId IN ({ids}) AND length(trim(tag)) BETWEEN 3 AND 30
        GROUP BY movieId, clean_tag
    )
    SELECT movieId, clean_tag AS tag, users FROM t
    QUALIFY ROW_NUMBER() OVER (PARTITION BY movieId ORDER BY users DESC, clean_tag) <= 3
""").df()
tag_map = tags.groupby("movieId")["tag"].apply(list).to_dict()

movies = []
for k, r in enumerate(films.itertuples(), start=1):
    genre = headline_genres(r.genres)
    motif = MOTIF.get(genre.split(" · ")[0], "crescent")
    pal = PALETTES[motif][int(hashlib.md5(r.title.encode()).hexdigest(), 16) % 2]
    director = (r.directors or "").split(",")[0].strip()
    movie_tags = tag_map.get(r.movieId, [])
    movies.append({
        "id": k,
        "movieId": int(r.movieId),
        "title": r.title,
        "year": int(r.year),
        "genre": genre,
        "critics": int(round(r.critics_score)),
        "audience": int(round(r.crowd_score)),
        "criticsPct": int(round(r.critics_pct)),   # percentile among all analysed films
        "audiencePct": int(round(r.crowd_pct)),
        "rankGap": int(round(r.rank_gap)),
        "nRatings": int(r.n_ratings),
        "criticReviews": int(r.critic_reviews),
        "imdb": None if r.imdb_rating != r.imdb_rating else float(r.imdb_rating),
        "director": director,
        "motif": motif,
        "colors": pal,
        "tagline": f"{int(r.n_ratings):,} MovieLens ratings",
        "criticQuote": short(r.critics_consensus),
        "audienceQuote": " · ".join(movie_tags) if movie_tags else "no tags yet",
    })

# ---------------- genres for the Snob-o-meter ----------------
genre_df = con.sql(f"SELECT * FROM read_csv_auto('{(RESULTS / 'genre_gap.csv').as_posix()}')").df()
genres = [{
    "name": g.genre,
    "gap": round(float(g.avg_rank_gap), 1),     # rank gap (percentile points)
    "rawGap": round(float(g.avg_gap), 1),
    "critics": float(g.avg_critics),
    "crowd": float(g.avg_crowd),
    "movies": int(g.movies),
    "example": f"{g.example_title} ({int(g.example_year)})" if g.example_title == g.example_title else "",
} for g in genre_df.itertuples()]

# ---------------- headline numbers for the footer / about box ----------------
s = con.sql(f"""
    SELECT COUNT(*) AS movies, SUM(n_ratings) AS ratings,
           ROUND(CORR(crowd_score, critics_score), 2) AS corr,
           ROUND(AVG(critics_score), 1) AS avg_critics,
           ROUND(AVG(crowd_score), 1) AS avg_crowd,
           ROUND(100.0 * AVG(CASE WHEN ABS(rank_gap) <= 20 THEN 1 ELSE 0 END)) AS agree_pct
    FROM read_parquet('{CVC}')
""").fetchone()
stats = {"movies": int(s[0]), "ratings": int(s[1]), "correlation": float(s[2]),
         "avgCritics": float(s[3]), "avgCrowd": float(s[4]), "agreePct": int(s[5])}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"movies": movies, "genres": genres, "stats": stats},
                          ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Wrote {OUT} : {len(movies)} films, {len(genres)} genres")
print(json.dumps(stats))
