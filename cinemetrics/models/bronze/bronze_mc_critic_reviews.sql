
with source as (
    select * from {{ source('raw', 'mc_critic_reviews') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
)

select
    json_extract_string(record, '$.movie_slug')       as movie_slug,
    json_extract_string(record, '$.author')           as author,
    json_extract_string(record, '$.author_slug')      as author_slug,
    json_extract_string(record, '$.publication_name') as publication_name,
    json_extract_string(record, '$.publication_slug') as publication_slug,
    json_extract_string(record, '$.quote')            as quote,
    try_cast(json_extract_string(record, '$.score') as integer) as score,
    json_extract_string(record, '$.url')              as url,
    json_extract_string(record, '$.date')             as review_date,
    _loaded_at,
    _source_file
from unnested
where json_extract_string(record, '$.movie_slug') is not null
