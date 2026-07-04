-- Pre-creates every bronze table that the dbt sources read, so `dbt build`
-- succeeds even before a scraper has loaded data (the silver models simply
-- return empty). Each table matches the {_loaded_at, _source_file, data}
-- shape the load tasks INSERT into. Keep in sync with sources.yml.
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.rt_details (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.rt_score (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.rt_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.rt_critic_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.rt_crosswalk (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.mc_general (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.mc_critic_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS bronze.mc_user_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);
