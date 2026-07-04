# Gold Layer — Entity-Relationship Diagram

```mermaid
erDiagram
    dim_date {
        int     date_key        PK
        date    date_day
        int     year
        int     quarter
        int     month_number
        varchar month_name
        int     day_of_month
        int     day_of_week
        varchar day_name
        int     week_of_year
        varchar year_quarter
    }

    dim_movie {
        int     movie_key           PK
        varchar movie_natural_key
        varchar mc_slug
        varchar rt_movie_id
        varchar title
        int     release_year
        varchar rating
        int     duration_minutes
        varchar imdb_id
        varchar primary_genre
        varchar rt_urlid
    }

    dim_critic {
        int     critic_key          PK
        varchar author_slug
        varchar critic_name
        varchar publication_name
        varchar publication_slug
    }

    fact_movie_score {
        int     score_key           PK
        int     movie_key           FK
        varchar platform
        int     critic_score
        int     user_score
        int     critic_review_count
        int     user_review_count
    }

    fact_critic_review {
        int     critic_review_key   PK
        int     movie_key           FK
        int     critic_key          FK
        int     date_key            FK
        varchar platform
        int     score
        varchar quote
    }

    dim_movie       ||--o{ fact_movie_score   : "movie_key"
    dim_movie       ||--o{ fact_critic_review : "movie_key"
    dim_critic      ||--o{ fact_critic_review : "critic_key"
    dim_date        ||--o{ fact_critic_review : "date_key"
```

## Notes

- `platform` is either `'metacritic'` or `'rottentomatoes'` in both fact tables.
- `mc_slug` and `rt_movie_id` in `dim_movie` may be NULL for single-source movies (FULL OUTER JOIN between platforms).
- `movie_key`, `critic_key`, and `date_key` FKs in `fact_critic_review` are nullable — unresolvable references produce NULL rather than dropped rows.
- MC user scores are normalised from the 0–10 raw scale to 0–100 (`× 10`). RT audience score is derived from `likedCount / (likedCount + notLikedCount)`.
