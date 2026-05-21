CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.rt_discovery (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

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
