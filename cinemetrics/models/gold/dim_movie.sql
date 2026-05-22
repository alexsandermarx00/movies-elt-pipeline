with mc as (
    select
        movie_slug                                  as mc_slug,
        title,
        premiere_year                               as release_year,
        rating,
        duration_minutes,
        imdb_id,
        json_extract_string(genres, '$[0]')         as primary_genre
    from {{ ref('silver_mc_general') }}
),
rt as (
    select
        movie_id                                    as rt_movie_id,
        title,
        coalesce(
            try_cast(release_date as integer),
            year(try_strptime(release_date, '%b %d, %Y')),
            year(try_cast(release_date as date))
        )                                           as release_year,
        urlid                                       as rt_urlid
    from {{ ref('silver_rt_details') }}
),
joined as (
    select
        coalesce(mc.mc_slug, rt.rt_movie_id)        as movie_natural_key,
        mc.mc_slug,
        rt.rt_movie_id,
        coalesce(mc.title, rt.title)                as title,
        coalesce(mc.release_year, rt.release_year)  as release_year,
        mc.rating,
        mc.duration_minutes,
        mc.imdb_id,
        mc.primary_genre,
        rt.rt_urlid
    from mc
    full outer join rt
        on lower(trim(mc.title)) = lower(trim(rt.title))
        and mc.release_year = rt.release_year
)
select
    row_number() over (order by title, release_year)    as movie_key,
    movie_natural_key,
    mc_slug,
    rt_movie_id,
    title,
    release_year,
    rating,
    duration_minutes,
    imdb_id,
    primary_genre,
    rt_urlid
from joined
