
with source as (
    select * from {{ source('bronze', 'rt_details') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
),

details as (
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
    qualify row_number() over (partition by movie_id order by _loaded_at desc) = 1
)

select
    d.movie_id,
    d.title,
    d.rating,
    d.release_date,
    d.rtid,
    d.urlid,
    xw.imdb_id,
    d._loaded_at,
    d._source_file
from details d
left join {{ ref('silver_rt_crosswalk') }} xw
    on xw.rt_slug = d.movie_id
