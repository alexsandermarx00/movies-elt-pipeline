import os
import sys
import logging
import argparse
from pathlib import Path

from .client import make_session, fetch_api_key, get_api_key
from .extractors import iter_general, iter_critic_reviews, iter_user_reviews, iter_search, iter_browse
from .output import FEED_URI, write_general, write_critic_reviews, write_user_reviews, write_discovered

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger(__name__)


def _marker_path(movie: str, action: str) -> Path:
    """Per-(movie, action) completion marker under FEED_URI/.done.

    Lets a re-run skip movies already scraped in a previous session — the key to
    surviving an IP block mid-catalog: re-trigger and it resumes where it stopped.
    """
    return Path(FEED_URI) / ".done" / action / f"{movie}.marker"


def run(movie: str, action: str, max_pages: int | None = None, force: bool = False) -> None:
    marker = _marker_path(movie, action)
    if not force and marker.exists():
        logger.info("Skipping '%s' (%s): already scraped (marker exists)", movie, action)
        return

    session = make_session()

    if action == "general":
        items = list(iter_general(session, movie))
        logger.info("Fetched %d general item(s) for '%s'", len(items), movie)
        write_general(items)
    elif action == "user_reviews":
        items = list(iter_user_reviews(session, movie, max_pages=max_pages))
        logger.info("Fetched %d user review(s) for '%s'", len(items), movie)
        write_user_reviews(items)
    elif action == "critic_reviews":
        items = list(iter_critic_reviews(session, movie, max_pages=max_pages))
        logger.info("Fetched %d critic review(s) for '%s'", len(items), movie)
        write_critic_reviews(items)
    elif action == "all":
        general_items = list(iter_general(session, movie))
        logger.info("Fetched %d general item(s) for '%s'", len(general_items), movie)
        write_general(general_items)

        user_items = list(iter_user_reviews(session, movie, max_pages=max_pages))
        logger.info("Fetched %d user review(s) for '%s'", len(user_items), movie)
        write_user_reviews(user_items)

        critic_items = list(iter_critic_reviews(session, movie, max_pages=max_pages))
        logger.info("Fetched %d critic review(s) for '%s'", len(critic_items), movie)
        write_critic_reviews(critic_items)
    else:
        raise ValueError(f"Unknown action: '{action}'")

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()


def run_apikey() -> None:
    """Fetch the Metacritic API key once and print it to stdout.

    Used by the DAG to resolve the key a single time and pass it to every scrape
    task via MC_API_KEY, so ~20k movie scrapes never re-hit the homepage (the
    main bot-block vector). Only the key is printed; logs go to stderr.
    """
    key = fetch_api_key(make_session())
    print(key)


def run_search(query: str, max_items: int | None = None) -> list[str]:
    session = make_session()
    items = list(iter_search(session, query, max_items=max_items))
    logger.info("Found %d result(s) for query '%s'", len(items), query)
    write_discovered(items)
    return [item.slug for item in items]


def run_browse(
    sort_by: str,
    year_min: int | None,
    year_max: int | None,
    genres: list[str] | None,
    max_items: int | None = None,
) -> list[str]:
    session = make_session()
    items = list(iter_browse(
        session,
        sort_by=sort_by,
        release_year_min=year_min,
        release_year_max=year_max,
        genres=genres or None,
        max_items=max_items,
    ))
    logger.info("Fetched %d movie(s) from browse", len(items))
    write_discovered(items)
    return [item.slug for item in items]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metacritic scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    movie_parser = subparsers.add_parser("movie", help="Scrape a specific movie by slug")
    movie_parser.add_argument("movie", help="Movie slug (e.g. the-godfather)")
    movie_parser.add_argument(
        "action",
        choices=["general", "user_reviews", "critic_reviews", "all"],
        help="Data to scrape",
    )
    movie_parser.add_argument("--max-pages", type=int, default=None,
                              help="Maximum number of pages to extract for reviews")
    movie_parser.add_argument("--force", action="store_true",
                              help="Re-scrape even if a completion marker exists (ignore resume)")

    subparsers.add_parser("apikey", help="Fetch and print the Metacritic API key")

    search_parser = subparsers.add_parser("search", help="Search movies by title query")
    search_parser.add_argument("query", help="Search query (e.g. 'godfather')")
    search_parser.add_argument("--max-items", type=int, default=None,
                               help="Maximum number of items to extract (useful for testing)")

    browse_parser = subparsers.add_parser("browse", help="Browse all movies with optional filters")
    browse_parser.add_argument("--sort-by", default="-metaScore",
                               choices=["-metaScore", "-userScore", "-releaseDate"],
                               help="Sort order (default: -metaScore)")
    browse_parser.add_argument("--year-min", type=int, default=None)
    browse_parser.add_argument("--year-max", type=int, default=None)
    browse_parser.add_argument("--genre", action="append", dest="genres",
                               help="Filter by genre (repeatable)")
    browse_parser.add_argument("--max-items", type=int, default=None,
                               help="Maximum number of items to extract (useful for testing)")

    args = parser.parse_args()

    try:
        if args.command == "movie":
            run(args.movie, args.action, args.max_pages, force=args.force)
        elif args.command == "apikey":
            run_apikey()
        elif args.command == "search":
            run_search(args.query, args.max_items)
        elif args.command == "browse":
            run_browse(args.sort_by, args.year_min, args.year_max, args.genres, args.max_items)
    except Exception as e:
        logging.error(e)
        sys.exit(1)
