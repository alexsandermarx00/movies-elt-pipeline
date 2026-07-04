with source as (
    select * from {{ source('bronze', 'rt_crosswalk') }}
),
unnested as (
    select _loaded_at, _source_file,
           unnest(data::json[]) as record
    from source
)
select
    json_extract_string(record, '$.imdb_id')  as imdb_id,
    json_extract_string(record, '$.rt_slug')  as rt_slug,
    json_extract_string(record, '$.mc_slug')  as mc_slug,
    json_extract_string(record, '$.title')    as title,
    _loaded_at
from unnested
where json_extract_string(record, '$.rt_slug') is not null
-- One row per rt_slug; deduplicate across runs by keeping latest load
qualify row_number() over (
    partition by json_extract_string(record, '$.rt_slug')
    order by _loaded_at desc
) = 1
