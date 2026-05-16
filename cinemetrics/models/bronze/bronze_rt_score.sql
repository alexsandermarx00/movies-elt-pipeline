
with source as (
    select * from {{ source('raw', 'rt_score') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
)

select
    json_extract_string(record, '$.movie_id')                   as movie_id,
    json_extract_string(record, '$.description')                as description,
    cast(json_extract(record, '$.audienceAll')     as varchar)  as audience_all,
    cast(json_extract(record, '$.audienceVerified') as varchar) as audience_verified,
    cast(json_extract(record, '$.criticsAll')     as varchar)   as critics_all,
    cast(json_extract(record, '$.criticsTop')     as varchar)   as critics_top,
    _loaded_at,
    _source_file
from unnested
where json_extract_string(record, '$.movie_id') is not null
