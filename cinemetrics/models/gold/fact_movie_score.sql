with mc_user_agg as (
    select
        movie_slug,
        round(avg(score), 1)    as user_score,
        count(*)                as user_review_count
    from {{ ref('silver_mc_user_reviews') }}
    where score is not null
    group by movie_slug
),
mc_scores as (
    select
        dm.movie_key,
        'metacritic'                        as platform,
        mc.critic_score,
        ua.user_score,
        mc.critic_review_count,
        coalesce(ua.user_review_count, 0)   as user_review_count
    from {{ ref('dim_movie') }} dm
    join {{ ref('silver_mc_general') }} mc on mc.movie_slug = dm.mc_slug
    left join mc_user_agg ua               on ua.movie_slug = dm.mc_slug
    where dm.mc_slug is not null
),
rt_scores as (
    select
        dm.movie_key,
        'rottentomatoes'                    as platform,
        try_cast(json_extract_string(rts.critics_all, '$.score')       as integer) as critic_score,
        try_cast(json_extract_string(rts.critics_all, '$.reviewCount') as integer) as critic_review_count,
        -- Audience score derived from like/dislike counts; no pre-computed score in source
        case
            when (
                try_cast(json_extract_string(rts.audience_all, '$.likedCount')    as integer) +
                try_cast(json_extract_string(rts.audience_all, '$.notLikedCount') as integer)
            ) > 0
            then round(
                100.0
                * try_cast(json_extract_string(rts.audience_all, '$.likedCount') as integer)
                / (
                    try_cast(json_extract_string(rts.audience_all, '$.likedCount')    as integer) +
                    try_cast(json_extract_string(rts.audience_all, '$.notLikedCount') as integer)
                )
            )::integer
        end                                 as user_score,
        (
            try_cast(json_extract_string(rts.audience_all, '$.likedCount')    as integer) +
            try_cast(json_extract_string(rts.audience_all, '$.notLikedCount') as integer)
        )                                   as user_review_count
    from {{ ref('dim_movie') }} dm
    join {{ ref('silver_rt_score') }} rts  on rts.movie_id = dm.rt_movie_id
    where dm.rt_movie_id is not null
),
combined as (
    select * from mc_scores
    union all
    select * from rt_scores
)
select
    row_number() over (order by movie_key, platform)    as score_key,
    movie_key,
    platform,
    critic_score,
    user_score,
    critic_review_count,
    user_review_count
from combined
