CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.rt_discovery (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS raw.rt_details (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS raw.rt_score (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS raw.rt_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS raw.mc_general (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS raw.mc_critic_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);

CREATE TABLE IF NOT EXISTS raw.mc_user_reviews (
    _loaded_at TIMESTAMP,
    _source_file VARCHAR,
    data JSON
);
