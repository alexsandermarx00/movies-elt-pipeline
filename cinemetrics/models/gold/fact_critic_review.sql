with mc_reviews as (
    select
        r.movie_slug,
        'mc::' || r.author_slug                     as author_slug,
        try_cast(r.review_date as date)             as review_date,
        r.score,
        r.quote,
        'metacritic'                                as platform
    from {{ ref('silver_mc_critic_reviews') }} r
    where r.score is not null
),
rt_reviews as (
    select
        r.movie_id                                                          as movie_slug,
        'rt::' || lower(replace(r.critic_name, ' ', '_'))                  as author_slug,
        try_cast(r.review_date as date)                                     as review_date,
        r.score,
        r.quote,
        'rottentomatoes'                                                    as platform
    from {{ ref('silver_rt_critic_reviews') }} r
    where r.critic_name is not null
),
all_reviews as (
    select * from mc_reviews
    union all
    select * from rt_reviews
),
enriched as (
    select
        case
            when r.platform = 'metacritic'
            then dm.movie_key
            else dm2.movie_key
        end                                         as movie_key,
        dc.critic_key,
        dd.date_key,
        r.platform,
        r.score,
        r.quote
    from all_reviews r
    left join {{ ref('dim_movie') }}  dm  on dm.mc_slug      = r.movie_slug
                                          and r.platform = 'metacritic'
    left join {{ ref('dim_movie') }}  dm2 on dm2.rt_movie_id = r.movie_slug
                                          and r.platform = 'rottentomatoes'
    left join {{ ref('dim_critic') }} dc  on dc.author_slug  = r.author_slug
    left join {{ ref('dim_date') }}   dd  on dd.date_day     = r.review_date
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
