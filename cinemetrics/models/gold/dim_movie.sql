with mc as (
    select
        movie_slug                                          as mc_slug,
        title,
        premiere_year                                       as release_year,
        rating,
        duration_minutes,
        imdb_id,
        json_extract_string(genres, '$[0]')                 as primary_genre
    from {{ ref('silver_mc_general') }}
    qualify imdb_id is null
        or row_number() over (partition by imdb_id order by _loaded_at desc) = 1
),
rt as (
    select
        movie_id                                            as rt_movie_id,
        -- Strip trailing year disambiguation suffix added by RT, e.g. "Magic Hour (2025)" → "Magic Hour"
        trim(regexp_replace(title, '\s*\(\d{4}\)\s*$', '')) as title,
        urlid                                               as rt_urlid,
        imdb_id
    from {{ ref('silver_rt_details') }}
    qualify imdb_id is null
        or row_number() over (partition by imdb_id order by _loaded_at desc) = 1
),
joined as (
    select
        coalesce(mc.mc_slug, rt.rt_movie_id)               as movie_natural_key,
        mc.mc_slug,
        rt.rt_movie_id,
        coalesce(mc.title, rt.title)                       as title,
        mc.release_year,
        mc.rating,
        mc.duration_minutes,
        coalesce(mc.imdb_id, rt.imdb_id)                   as imdb_id,
        mc.primary_genre,
        rt.rt_urlid
    from mc
    -- FULL OUTER JOIN keeps MC-only and RT-only movies as single-source rows.
    -- MC and RT are matched on imdb_id (sourced from Wikidata P345/P1258 mapping).
    full outer join rt
        on rt.imdb_id = mc.imdb_id
)
select
    row_number() over (order by title, release_year)        as movie_key,
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
