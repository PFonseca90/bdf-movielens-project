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
