# Big Data Foundations — MovieLens Project

NOVA IMS — Postgraduate Program in Data Analysis & Business Analytics  
Course: Big Data Foundations

## Project Overview

This project analyses the MovieLens dataset to study how audience preferences and movie popularity evolve over time.

The project is designed to demonstrate a progression from local data processing and analytics to a scalable cloud-based architecture.

The initial analysis is developed locally using DuckDB, Parquet and Python. The project will later be scaled using AWS services such as Amazon S3, AWS Glue and Amazon Athena.

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

## Local Setup
The project dependencies are stored in a requirements file, run the following:

```sh
pip install -r requirements.txt
```

## Jupytext

Notebooks are good at prototyping, but especially messy in version control. This project uses jupytext. 

Feel free to write code in the `notebook/` folder or use the python modules in `src/`. To sync the codes, run:

Syncs all `.py` to `ipynb`:
```sh
uv run jupytext --sync src/*.py
```

Sync one notebook to `.py`:

```sh
jupytext --sync notebooks/imdb_download.ipynb 
```

We do not commit the notebooks, `.ipynb` files, they are ignored. Run the sync above to get notebook files.

Alternative, pre-commit handles it all.

## Data Layout
Data is not included in the repo; instead we provide scripts that can download the required data end-to-end. Where this is not possible, instructions is included in this README.

The expected data layout following a successful setup is outlined below:

```
PROJECT_ROOT
____Data
| |____Parquet
| | |____TMDB
| | | |____tmdb_ml32m_features.parquet
| | |____IMDB
| | | |____title_episode.parquet
| | | |____name_basics.parquet
| | | |____title_basics.parquet
| | | |____title_ratings.parquet
| | | |____title_principals.parquet
| | | |____title_akas.parquet
| | | |____title_crew.parquet
| | |____MovieLens
| | | |____ratings.parquet
| | | |____movies.parquet
| | | |____tags.parquet
| | | |____links.parquet
| |____Raw
| | |____TMDB
| | | |____tmdb_enriched_ml32m.jsonl
| | | |____tmdb.jsonl
| | |____IMDB
| | | |____title.principals.tsv.gz
| | | |____title.akas.tsv.gz
| | | |____title.basics.tsv.gz
| | | |____title.crew.tsv.gz
| | | |____title.ratings.tsv.gz
| | | |____name.basics.tsv.gz
| | | |____title.episode.tsv.gz
| | |____MovieLens
| | | |____links.csv
| | | |____tags.csv
| | | |____checksums.txt
| | | |____ratings.csv
| | | |____README.txt
| | | |____movies.csv
```
