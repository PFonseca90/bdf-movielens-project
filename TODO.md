# Todos
- [x] Add Group CSV
- [x] Add Jupytext & Scaffold
- [x] Outline the presentation
- [x] Presentation: Add pages as interesting questions have charts
- [x] Start backup presentation - Keni
- [x] Analyze 32M locally
- [x] Analyze 32M & 1b on S3 - Pedro
- [ ] Answer Basic Questions: Include SQL in source
- [ ] Answer More Interesting Questions - Everybody
- [ ] Explore & Add Complimentary Datasets
    - [x] IMDB - Libi
    - [ ] TMDB - Keni
    - [x] Rotten Tomatoes, Reference in README.md - Libi
- [x] Organize Game Code in Repo - Libi
- [ ] Prettify Basic Answers Charts
- [ ] AWS Glue/Athena, Add queries to repo - Pedro
- [ ] AWS Glue/Athena, Benchmark - Pedro
- [ ] Indicate limitations and possibilities for future work.
- [ ] Merge Code
- [ ] Organize Code for Submissions - Keni

## Objectives
- Become familiar with a dataset that can start small and grow to be really big yet manageable with limited hardware
- Become familiar with tools and architecture choices that support reproducible analysis, and can scale from local execution to the cloud when appropriate.

1. Start local, then scale the same architectural idea to the cloud.
1. Consider:
    - Storage
    - Compute
    - Metadata
    - Performance
    - Cost


## Approach

| Operation         | Local               | Online            |
|-------------------|---------------------|-------------------|
| Data Storage      | Local Disk          | S3                |
| Download Method   | Local Disk          | CloudShell or Glue Shell Python Script)    |
| Compression       | Optional            | Snappy Parquet    |
| EDA               | FG-DATA Profiling?  |                   |
| Partitioning      | Run Python script   | Partition on S3   |
| Basic Questions   | Run                 | Run               |
| Evolved Questions | Run                 | Run               |

## Cloud Notes
- Partition large ratings table by year, extracted from UNIX Timestamp
-

## More Interesting Questions

1. Genre Evolution & Audience Shifts
 - Genre fatigue vs. resurgence: How have average ratings and total viewing volume for genres like Westerns, Sci-Fi, or Superheroes changed from the late 1990s to today?
 - Cross-genre performance: Do hybrid films (e.g., Comedy|Sci-Fi or Horror|Mystery) earn higher average ratings than single-genre films, or do they polarize viewers?
 - The "Sequel Decay" effect: Using movie titles and release years, how sharply does audience sentiment drop between an original movie and its sequels?

2. Behavioral & Rating Biases
- The "Nostalgia Effect" (Release Year vs. Rating Year): Do users rate older classics (e.g., 1970s films) higher than modern releases simply because only dedicated fans seek out older movies?
- Rating inflation or harshness over time: Have MovieLens users become more generous or more critical with their star ratings over the last 25 years?
- User rating archetypes: Can you segment users into "generous raters" (average rating > 4.2), "harsh critics" (average < 2.5), and "polarized raters" (mostly 5s and 0.5s)?
- Binge-rating patterns: Using rating_timestamp, how do a user's ratings change during a single sitting? (For example, do users rate movies lower at the end of a long session?)

3. Tag Semantics & Content Discovery (NLP / Text Analytics)
- Sentiment vs. star ratings: Which user-applied tags (e.g., "twist ending", "slow burn", "overrated", "visually stunning") correlate with the highest and lowest star ratings?
- Cult classics & polarizing films: Which movies have a mediocre average rating (~3.0) but an unusually high standard deviation—meaning people either love them or hate them?
- Hidden gems: Which films have very high average ratings (> 4.2) among a small, passionate group of viewers (e.g., 50–200 ratings) compared to mainstream blockbusters?

4. Recommender System Diagnostics (Data Engineering Focus)
- Popularity bias (The Long Tail): What percentage of all 25 million ratings belong to just the top 1% of most-watched movies?
- Cold-start velocity: How quickly does a newly released movie accumulate its first 100 ratings after being added to the platform?

5. Correlation between profitability and ratings
- Ratings of movies by particular directors
- Which directors, actors, have the highest ratings
- Is Nicholas Cage the most profitable actor
- Do people like Monster movies? Popularity of monsters vs years
- What are the popular genres in 2026?
- Which Genre is popular and when?
