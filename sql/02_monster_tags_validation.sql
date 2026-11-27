-- MONSTER THEMES - TAG VALIDATION
--
-- Objective: Compare tag mentions with distinct movies.
-- =====================================================

WITH monster_tags AS (
    SELECT
        movieId,
        CASE
            WHEN regexp_matches(LOWER(TRIM(tag)), '\bzombies?\b')
                THEN 'Zombies'
            WHEN regexp_matches(LOWER(TRIM(tag)), '\bvampires?\b')
                THEN 'Vampires'
            WHEN regexp_matches(LOWER(TRIM(tag)), '\baliens?\b')
                THEN 'Aliens'
            WHEN regexp_matches(LOWER(TRIM(tag)), '\bwerewol(f|ves)\b')
                THEN 'Werewolves'
            WHEN regexp_matches(LOWER(TRIM(tag)), '\bdinosaurs?\b')
                THEN 'Dinosaurs'
            WHEN regexp_matches(LOWER(TRIM(tag)), '\bkaiju\b|\bmonsters?\b')
                THEN 'Monsters'
        END AS creature_type
    FROM read_parquet('Data/Parquet/ml-32m/tags.parquet')
)

SELECT
    creature_type,
    COUNT(*) AS tag_mentions,
    COUNT(DISTINCT movieId) AS distinct_movies,
    COUNT(*) - COUNT(DISTINCT movieId) AS repeated_mentions
FROM monster_tags
WHERE creature_type IS NOT NULL
GROUP BY creature_type
ORDER BY distinct_movies DESC;


-- Monster themes by release decade - Count each movie only once per creature category

WITH tagged_movies AS (
    SELECT DISTINCT
        movieId,
        CASE
            WHEN regexp_matches(LOWER(tag), '\bzombies?\b')
                THEN 'Zombies'
            WHEN regexp_matches(LOWER(tag), '\bvampires?\b')
                THEN 'Vampires'
            WHEN regexp_matches(LOWER(tag), '\baliens?\b')
                THEN 'Aliens'
            WHEN regexp_matches(LOWER(tag), '\bwerewol(f|ves)\b')
                THEN 'Werewolves'
            WHEN regexp_matches(LOWER(tag), '\bdinosaurs?\b')
                THEN 'Dinosaurs'
            WHEN regexp_matches(LOWER(tag), '\bkaiju\b|\bmonsters?\b')
                THEN 'Monsters'
        END AS creature_type
    FROM read_parquet('Data/Parquet/ml-32m/tags.parquet')
),

movies_with_year AS (
    SELECT
        movieId,
        TRY_CAST(
            regexp_extract(title, '\(([0-9]{4})\)', 1)
            AS INTEGER
        ) AS release_year
    FROM read_parquet('Data/Parquet/ml-32m/movies.parquet')
),

tagged_movie_ids AS (
    SELECT DISTINCT movieId
    FROM read_parquet('Data/Parquet/ml-32m/tags.parquet')
),

movies_per_period AS (
    SELECT
        (m.release_year // 5) * 5 AS period,
        COUNT(*) AS total_movies,
        COUNT(t.movieId) AS tagged_movies
    FROM movies_with_year m
    LEFT JOIN tagged_movie_ids t
        ON m.movieId = t.movieId
    WHERE m.release_year BETWEEN 1950 AND 2022
    GROUP BY period
),

monsters_per_period AS (
    SELECT
        (m.release_year // 5) * 5 AS period,
        t.creature_type,
        COUNT(DISTINCT t.movieId) AS monster_movies
    FROM tagged_movies t
    JOIN movies_with_year m
        ON t.movieId = m.movieId
    WHERE
        t.creature_type IS NOT NULL
        AND m.release_year BETWEEN 1950 AND 2022
    GROUP BY period, t.creature_type
)

SELECT
    t.period,
    t.creature_type,
    t.monster_movies,
    d.total_movies,
    d.tagged_movies,
    ROUND(
        100.0 * t.monster_movies
        / NULLIF(d.tagged_movies, 0),
        2
    ) AS percentage_of_tagged_movies
FROM monsters_per_period t
JOIN movies_per_period d
    ON t.period = d.period
ORDER BY t.period, t.creature_type;




SELECT
    era,
    theme,
    theme_films,
    denom,
    pct
FROM read_csv_auto(
    'results/theme_trends/supply_by_era.csv'
)
WHERE theme IN (
    'Zombies',
    'Vampires',
    'Aliens',
    'Werewolves',
    'Dinosaurs',
    'Monsters'
)
AND era BETWEEN 2000 AND 2020
ORDER BY era, theme;
