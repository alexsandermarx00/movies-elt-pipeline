# Camada Gold — Diagrama Entidade-Relacionamento

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

## Observações

- `platform` é `'metacritic'` ou `'rottentomatoes'` em ambas as tabelas fato.
- `mc_slug` e `rt_movie_id` em `dim_movie` podem ser NULL para filmes de fonte única (FULL OUTER JOIN entre plataformas).
- As FKs `movie_key`, `critic_key` e `date_key` em `fact_critic_review` são anuláveis — referências não resolvidas geram NULL em vez de descartar a linha.
- As notas de usuário do MC são normalizadas da escala bruta 0–10 para 0–100 (`× 10`). A nota do público do RT é derivada de `likedCount / (likedCount + notLikedCount)`.
