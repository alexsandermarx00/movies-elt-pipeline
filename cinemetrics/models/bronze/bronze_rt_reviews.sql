
with source as (
    select * from {{ source('raw', 'rt_reviews') }}
),

unnested as (
    select
        _loaded_at,
        _source_file,
        unnest(data::json[]) as record
    from source
)

select
    json_extract_string(record, '$.movie_id')                                   as movie_id,
    json_extract_string(record, '$.reviewId')                                   as review_id,
    json_extract_string(record, '$.quote')                                      as quote,
    json_extract_string(record, '$.rating')                                     as rating,
    try_cast(json_extract_string(record, '$.isVerified')      as boolean)       as is_verified,
    try_cast(json_extract_string(record, '$.isSuperReviewer') as boolean)       as is_super_reviewer,
    try_cast(json_extract_string(record, '$.hasSpoilers')     as boolean)       as has_spoilers,
    try_cast(json_extract_string(record, '$.hasProfanity')    as boolean)       as has_profanity,
    json_extract_string(record, '$.creationDate')                               as created_at,
    json_extract_string(record, '$.userDisplayName')                            as user_display_name,
    json_extract_string(record, '$.userAccountLink')                            as user_account_link,
    json_extract_string(record, '$.userRealm')                                  as user_realm,
    json_extract_string(record, '$.userId')                                     as user_id,
    _loaded_at,
    _source_file
from unnested
where json_extract_string(record, '$.movie_id') is not null
