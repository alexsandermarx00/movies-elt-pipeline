
with source as (
    select * from {{ source('bronze', 'mc_user_reviews') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
)

select
    json_extract_string(record, '$.movie_slug')                         as movie_slug,
    json_extract_string(record, '$.review_id')                          as review_id,
    json_extract_string(record, '$.author')                             as author,
    json_extract_string(record, '$.quote')                              as quote,
    try_cast(json_extract_string(record, '$.score') as integer)         as score,
    json_extract_string(record, '$.date')                               as review_date,
    try_cast(json_extract_string(record, '$.spoiler') as boolean)       as spoiler,
    try_cast(json_extract_string(record, '$.thumbs_up') as integer)     as thumbs_up,
    try_cast(json_extract_string(record, '$.thumbs_down') as integer)   as thumbs_down,
    _loaded_at,
    _source_file
from unnested
where json_extract_string(record, '$.movie_slug') is not null
qualify row_number() over (partition by review_id order by _loaded_at desc) = 1
