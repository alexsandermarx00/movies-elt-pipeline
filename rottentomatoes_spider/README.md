# Rotten Tomatoes Spider

A Scrapy spider for extracting comprehensive data from Rotten Tomatoes.

## Installation

Ensure you have installed the required dependencies from the `requirements.txt` file before running the spider.

```bash
pip install -r requirements.txt
```

## Usage

This project contains a primary spider named `rtspider`. You can pass parameters dynamically via the command line to tell it which movie you are scraping, and what type of data you want to extract.

### General Syntax

```bash
scrapy crawl rtspider -a movie=<movie_name_slug> -a action=<extraction_mode> [options]
```

- `movie`: The URL slug of the movie on Rotten Tomatoes. (e.g. `godzilla_x_kong_the_new_empire`, `dune_part_two`)
- `action`: The extraction mode you want to execute (`score`, `reviews`, or `details`).
- `max_pages`: *(Optional)* Defines the maximum number of paginated pages to scrape when using `reviews` action (defaults to `2`).
- `-o`: *(Optional)* Manual local output override. Note: standard execution will automatically dispatch output to the `.output/` directory natively, or to an S3 object instance if the `FEED_URI` environment variable is engaged.

---

## Extraction Modes (`action`)

The spider supports four distinct modes of data extraction.

### 1. `score`
Pulls high-level rating and synopsis information.
**Extracted Data:** Movie ID, overall/verified audience score, overall/top critics score, and description. 

**Execution Example:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=score
```

### 2. `reviews`
Pulls and paginates through the user reviews for the specified movie.
**Extracted Data:** Movie ID, review rating, quote, review ID, verified status, profanity/spoiler flags, user details, and creation date.

**Execution Example:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=reviews -a max_pages=5
```

### 3. `details`
Pulls technical details from the underlying page metadata integration.
**Extracted Data:** Movie ID, title, film rating (e.g. PG-13), release date, and internal IDs (`rtid`, `urlid`).

**Execution Example:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=details
```

### 4. `critic_reviews`
Pulls and paginates through critic reviews for the specified movie.
**Extracted Data:** Movie ID, review ID, critic name, publication, score, quote, review date.

**Execution Example:**
```bash
scrapy crawl rtspider -a movie=dune_part_two -a action=critic_reviews -a max_pages=5
```

---

## Discovery via Wikidata Crosswalk

Previously, this project included `rt_discovery_spider.py` for dynamic movie discovery. This has been replaced by a Wikidata crosswalk mapping (IMDB ID → RT URL Slug), bridging records directly and deterministically into our pipeline without requiring exploratory scraping.

---

## Orchestration

The scraper is executed via Apache Airflow. The Dockerfile for execution is located in the root `airflow/` directory. Airflow runs the scrapers as subprocesses (using BashOperator), writing the output as JSON files which are then loaded into DuckDB.
