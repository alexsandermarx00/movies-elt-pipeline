with mc_critics as (
    select
        'mc::' || author_slug                        as author_slug,
        author                                       as critic_name,
        publication_name,
        publication_slug
    from {{ ref('silver_mc_critic_reviews') }}
    where author_slug is not null
    qualify row_number() over (partition by author_slug order by _loaded_at desc) = 1
),
rt_critics as (
    -- One row per critic (author_slug): a critic who reviews for multiple
    -- publications would otherwise yield multiple rows, fanning out the join in
    -- fact_critic_review. Keep the most recently loaded publication, mirroring
    -- the dedup already applied to the Metacritic side above.
    select
        'rt::' || lower(replace(critic_name, ' ', '_')) as author_slug,
        critic_name,
        publication                                  as publication_name,
        null                                         as publication_slug
    from {{ ref('silver_rt_critic_reviews') }}
    where critic_name is not null
    qualify row_number() over (
        partition by lower(replace(critic_name, ' ', '_')) order by _loaded_at desc
    ) = 1
),
all_critics as (
    select * from mc_critics
    union all
    select * from rt_critics
)
select
    row_number() over (order by author_slug)    as critic_key,
    author_slug,
    critic_name,
    publication_name,
    publication_slug
from all_critics
