# mc_scrape

Metacritic scraper that fetches general info, critic reviews, and user reviews for movies, writing output as pure JSON consumed by the bronze layer loader. Supports slug discovery via title search or bulk browse across the full catalog (~17k movies).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Setup

```bash
uv sync
```

## Usage

### Python

The CLI has three subcommands: `movie`, `search`, and `browse`.

---

#### `movie` — scrape a specific movie by slug

```bash
uv run python -m metacritic movie <movie_slug> <action>
```

| Argument | Description |
|---|---|
| `movie_slug` | Movie identifier as it appears in the Metacritic URL (e.g. `the-godfather`) |
| `action` | One of: `general`, `critic_reviews`, `user_reviews`, `all` |

```bash
# Fetch general info only
uv run python -m metacritic movie the-godfather general

# Fetch all critic reviews (paginated)
uv run python -m metacritic movie the-godfather critic_reviews

# Fetch all user reviews (paginated)
uv run python -m metacritic movie the-godfather user_reviews

# Fetch everything
uv run python -m metacritic movie the-godfather all
```

---

#### `search` — discover slugs by title query

Searches Metacritic for movies matching a query and writes results to the `browse` JSON output.

```bash
uv run python -m metacritic search "godfather"

# Limit results (useful for testing)
uv run python -m metacritic search "godfather" --max-items 3
```

---

#### `browse` — bulk-discover slugs across the full catalog

Paginates through all ~17k movies on Metacritic with optional filters. Results are written to the `browse` JSON output.

```bash
uv run python -m metacritic browse [--sort-by SORT] [--year-min YEAR] [--year-max YEAR] [--genre GENRE ...]
```

| Option | Description | Default |
|---|---|---|
| `--sort-by` | `'-metaScore'`, `'-userScore'`, or `'-releaseDate'` | `-metaScore` |
| `--year-min` | Filter to movies released from this year | — |
| `--year-max` | Filter to movies released up to this year | — |
| `--genre` | Filter by genre (repeatable) | — |
| `--max-items` | Maximum number of items to extract (useful for testing and Airflow task generation) | — |

```bash
# All movies sorted by Metascore
uv run python -m metacritic browse

# Recent dramas
uv run python -m metacritic browse --year-min 2020 --genre Drama

# Multiple genres
uv run python -m metacritic browse --genre Action --genre Thriller --sort-by -releaseDate

# Test with small sample (first 100 movies)
uv run python -m metacritic browse --max-items 100
```

---

**Output location:**

By default, JSON files are written to `./data/`:

```
./data/
├── mc_general/              (full movie metadata)
├── mc_critic_reviews/       (individual critic reviews)
├── mc_user_reviews/         (individual user reviews)
└── mc_discovered_movies/    (discovered slugs)
```

The `discovered_movies` file acts as a lightweight "discovered queue" that tracks:
- `slug` — the movie identifier
- `discovered_at` — timestamp when discovered
- `method` — how it was discovered (`browse` or `search`)

For Airflow: use the returned slug list directly for downstream tasks.

Set the `FEED_URI` environment variable to write elsewhere:

```bash
# Write to a custom local path
FEED_URI=/data/metacritic uv run python -m metacritic movie the-godfather all

# Write to S3
FEED_URI=s3://my-bucket/metacritic uv run python -m metacritic browse
```

## Reading the output with DuckDB

```sql
-- General info
SELECT * FROM read_json_auto('./data/mc_general/*.json');

-- Critic reviews
SELECT * FROM read_json_auto('./data/mc_critic_reviews/*.json');

-- User reviews
SELECT * FROM read_json_auto('./data/mc_user_reviews/*.json');

-- Discovered movies (slug discovery queue)
SELECT * FROM read_json_auto('./data/mc_discovered_movies/*.json');

-- Example: find all movies discovered via search for "godfather"
SELECT slug, discovered_at 
FROM read_json_auto('./data/mc_discovered_movies/*.json')
WHERE method = 'search';
```

From S3:

```sql
SELECT * FROM delta_scan('s3://my-bucket/metacritic/general');
```

## Finding movie slugs

The slug is the last segment of the Metacritic movie URL:

```
https://www.metacritic.com/movie/the-godfather/
                                  ^^^^^^^^^^^^^
                                  slug: the-godfather
```

You can also discover slugs programmatically:

```bash
# Search by title
uv run python -m metacritic search "the godfather"

# Browse entire catalog (writes slugs to ./delta/browse)
uv run python -m metacritic browse
```
