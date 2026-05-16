
with source as (
    select * from {{ source('raw', 'rt_details') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
)

select
    json_extract_string(record, '$.movie_id') as movie_id,
    json_extract_string(record, '$.title')    as title,
    json_extract_string(record, '$.rating')   as rating,
    json_extract_string(record, '$.release')  as release_date,
    json_extract_string(record, '$.rtid')     as rtid,
    json_extract_string(record, '$.urlid')    as urlid,
    _loaded_at,
    _source_file
from unnested
where json_extract_string(record, '$.movie_id') is not null
