with reviews as (
    select
        r.movie_slug,
        r.author_slug,
        try_cast(r.review_date as date)     as review_date,
        r.score,
        r.quote
    from {{ ref('silver_mc_critic_reviews') }} r
    where r.score is not null
),
enriched as (
    select
        dm.movie_key,
        dc.critic_key,
        dd.date_key,
        'metacritic'                        as platform,
        r.score,
        r.quote
    from reviews r
    left join {{ ref('dim_movie') }}  dm on dm.mc_slug     = r.movie_slug
    left join {{ ref('dim_critic') }} dc on dc.author_slug = r.author_slug
    left join {{ ref('dim_date') }}   dd on dd.date_day    = r.review_date
)
select
    row_number() over (order by movie_key, critic_key, date_key)    as critic_review_key,
    movie_key,
    critic_key,
    date_key,
    platform,
    score,
    quote
from enriched
