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

The spider supports three distinct modes of data extraction.

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

---

## Docker Orchestration

This project includes a production-ready `Dockerfile` structured to separate the `ENTRYPOINT` context from dynamically overridable parameter `CMD`s, making it perfectly suited for Apache Airflow `DockerOperator` usage.

### 1. Build the Image
Build the Docker container locally using the provided `.dockerignore` to streamline the build cache:
```bash
docker build -t rtspider-image .
```

### 2. Execute a Crawl Test
Run the container to test execution. Since the `ENTRYPOINT` natively wraps `scrapy crawl`, simply pass your dynamic spider parameters directly as trailing arguments.

To route outputs strictly to an S3 bucket instead of the ephemeral container filesystem, inject the `FEED_URI` environment variable natively into the container:
```bash
docker run --rm -e FEED_URI="s3://my-datalake/rottentomatoes/%(action)s/%(name)s_%(time)s.json" rtspider-image rtspider -a movie=dune_part_two -a action=score
```

Alternatively, if you want to test locally and save the output directly to your host machine without using S3, you must map a volume from your local `.output/` directory into the container's `/app/.output/` working directory:
```bash
docker run --rm -v $(pwd)/.output:/app/.output rtspider-image rtspider -a movie=dune_part_two -a action=score
```
