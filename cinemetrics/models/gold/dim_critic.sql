with mc_critics as (
    select
        author_slug,
        author              as critic_name,
        publication_name,
        publication_slug
    from {{ ref('silver_mc_critic_reviews') }}
    where author_slug is not null
    qualify row_number() over (partition by author_slug order by _loaded_at desc) = 1
)
select
    row_number() over (order by author_slug)    as critic_key,
    author_slug,
    critic_name,
    publication_name,
    publication_slug
from mc_critics
