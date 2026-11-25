# Big Data Foundations — MovieLens Project

NOVA IMS — Postgraduate Program in Data Analysis & Business Analytics  
Course: Big Data Foundations

## Project Overview

This project analyses the MovieLens dataset to study how audience preferences and movie popularity evolve over time.

The project is designed to demonstrate a progression from local data processing and analytics to a scalable cloud-based architecture.

The initial analysis is developed locally using DuckDB, Parquet and Python. The project will later be scaled using AWS services such as Amazon S3, AWS Glue and Amazon Athena.

## ⭐ Main deep question: Critics vs Crowd ("Film Snob or Popcorn Person?")

**Question:** For which movies and genres do professional critics and regular viewers disagree the most?

| Voice | Source | Measure (0-100) |
|---|---|---|
| Critics | Rotten Tomatoes (Kaggle, Stefano Leone, scraped 2020) | Tomatometer = % of critics with a positive review |
| Crowd | **MovieLens 32M ratings** (our big data) | % of ratings ≥ 3.5★ (same rule RT uses for its audience score) |
| Check | IMDb `title.ratings` (official dataset) | averageRating × 10 |

* **Gap** = crowd − critics. **Rank gap** = crowd percentile − critics percentile (main measure, because MovieLens users grade harder overall: crowd 53.9 vs critics 61.8 on average).
* **Joins:** MovieLens → IMDb exact via `links.imdbId`; MovieLens → RT on normalised title + year (±1), strictly one-to-one. 13,738 matches; 6,932 films with ≥100 ratings and ≥20 critic reviews (≈27M of the 32M ratings).

**Key findings (results/critics_vs_crowd/)**
1. Critics and crowd mostly agree (r = 0.78), but audiences agree with each other more (MovieLens vs IMDb r = 0.91).
2. Critics rank **Children, Animation, Horror and Musical** films higher; the crowd ranks **War, Mystery, Drama, Crime** higher.
3. Critics adore old classics (1930s: 93% vs crowd 72%).
4. Hall of Shame: crowd loved *The Butterfly Effect* (crowd 73 vs critics 33); critics loved *Antz*, *The Blair Witch Project*, *Addams Family Values*.

### Reproduce (from the project root)
1. `pip install -r requirements.txt`
2. Put the raw files here (not in git):
   * `Data/Raw/ml-32m/` ← unzip https://files.grouplens.org/datasets/movielens/ml-32m.zip
   * `Data/External/rotten_tomatoes/rotten_tomatoes_movies.csv` ← https://www.kaggle.com/datasets/stefanoleone992/rotten-tomatoes-movies-and-critic-reviews-dataset
   * `Data/External/imdb/title.ratings.tsv.gz` ← https://datasets.imdbws.com/title.ratings.tsv.gz
3. Run in order:
   ```
   python src/01_data_ingestion_32m.py     # MovieLens CSV -> Parquet
   python src/06_ingest_external.py        # RT + IMDb -> Parquet
   python src/07_critics_vs_crowd.py       # join + analysis -> results/critics_vs_crowd/*.csv
   python src/08_export_game_data.py       # -> presentation/film-snob-game/src/gameData.json
   python src/09_make_charts.py            # -> results/charts/*.png
   ```
4. Cloud (AWS Academy Learner Lab): upload the Parquet files to S3, then run `sql/athena/01_create_tables.sql`, `02_ctas_ratings_by_year.sql`, `03_critics_vs_crowd.sql` in Athena. Record "Data scanned" and "Run time" in `results/athena_evidence.csv`.
5. Game: open `presentation/film-snob-game/dist/index.html` (double-click). To rebuild after new data: `cd presentation/film-snob-game && npm install && npm run build`.

### Folder map
```
src/                      Python pipeline (01-05 team ingestion/EDA/benchmarks, 06-09 critics vs crowd)
sql/athena/               Athena DDL, CTAS (partitioned by year), critics-vs-crowd queries
results/critics_vs_crowd/ CSV results   results/charts/ PNG charts for the slides
presentation/film-snob-game/  classroom game (React + Vite), reads src/gameData.json
Data/ (git-ignored)       Raw/, External/, Parquet/
```

## Canonical Question

1. What are the movie genres in the dataset?
1. What is the number of movies per genre?
1. What is the movie rating distribution per user?
1. What are the movies with the highest average rating?

## Main Research Questions

The project will explore questions such as:

1. How have the popularity and audience appreciation of movie genres evolved over time?
2. Are the most popular genres and movies also the most highly rated?
3. Can recurring movie themes show identifiable cycles of popularity and audience appreciation?
4. Which genres or themes retain audience attention for longer after release?
5. How does the popularity of actors or directors evolve over time and across different genres or themes?

Additional research questions may be introduced as the project evolves.

## Additional Research Questions:
- Minimum ratings per user
- 

## Presentation Outline

- XXX
- YYY
- Basic Questions (Maybe knock these out to keep a punch?)
- Evolved Questions:
    - Do Sequels Polarize Users?
    - 
- ZZZ

## Current Progress

The project environment has been set up locally in VS Code, including a dedicated Python virtual environment and the required packages for data processing and analysis. The project repository has also been created and connected to GitHub, with Git configured to exclude local environments, raw datasets and generated files.

The MovieLens dataset has been added locally to `Data/Raw/`, and the development environment has been successfully validated with DuckDB, Polars, PyArrow, Pandas and Matplotlib. The next step is to build the initial ingestion pipeline to inspect the CSV files, validate the data and convert them to Parquet.
