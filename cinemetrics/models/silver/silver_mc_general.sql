
with source as (
    select * from {{ source('bronze', 'mc_general') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
)

select
    json_extract_string(record, '$.movie_slug')                               as movie_slug,
    json_extract_string(record, '$.slug')                                     as slug,
    try_cast(json_extract_string(record, '$.id') as integer)                  as id,
    json_extract_string(record, '$.title')                                    as title,
    json_extract_string(record, '$.description')                              as description,
    json_extract_string(record, '$.release_date')                             as release_date,
    try_cast(json_extract_string(record, '$.premiere_year') as integer)       as premiere_year,
    json_extract_string(record, '$.rating')                                   as rating,
    try_cast(json_extract_string(record, '$.duration') as integer)            as duration_minutes,
    try_cast(json_extract_string(record, '$.in_theaters') as boolean)         as in_theaters,
    json_extract_string(record, '$.tagline')                                  as tagline,
    json_extract_string(record, '$.imdb_id')                                  as imdb_id,
    cast(json_extract(record, '$.genres') as varchar)                         as genres,
    try_cast(json_extract_string(record, '$.critic_score') as integer)        as critic_score,
    try_cast(json_extract_string(record, '$.critic_review_count') as integer) as critic_review_count,
    json_extract_string(record, '$.critic_sentiment')                         as critic_sentiment,
    _loaded_at,
    _source_file
from unnested
where json_extract_string(record, '$.movie_slug') is not null
qualify row_number() over (partition by movie_slug order by _loaded_at desc) = 1
