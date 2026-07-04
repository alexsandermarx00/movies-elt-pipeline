with source as (
    select * from {{ source('bronze', 'rt_critic_reviews') }}
),
unnested as (
    select _loaded_at, _source_file,
           unnest(data::json[]) as record
    from source
)
select
    json_extract_string(record, '$.movie_id')     as movie_id,
    json_extract_string(record, '$.review_id')    as review_id,
    json_extract_string(record, '$.critic_name')  as critic_name,
    json_extract_string(record, '$.publication')  as publication,
    json_extract_string(record, '$.score')        as score,
    json_extract_string(record, '$.quote')        as quote,
    json_extract_string(record, '$.review_date')  as review_date,
    _loaded_at
from unnested
where json_extract_string(record, '$.movie_id') is not null
qualify row_number() over (
    partition by json_extract_string(record, '$.review_id')
    order by _loaded_at desc
) = 1
