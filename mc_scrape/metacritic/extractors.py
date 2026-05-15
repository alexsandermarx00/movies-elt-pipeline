import logging
import requests
from typing import Generator

from .client import build_url, build_search_url, build_browse_url, get_api_key, MCO_TYPE_MOVIE
from .models import GeneralItem, CriticReview, UserReview, DiscoveredMovie

logger = logging.getLogger(__name__)


def iter_general(session: requests.Session, movie: str) -> Generator[GeneralItem, None, None]:
    url = build_url(movie, "general")
    response = session.get(url)
    response.raise_for_status()
    body = response.json()
    item = body["data"]["item"]
    yield GeneralItem.from_api(movie, item)


def iter_critic_reviews(session: requests.Session, movie: str) -> Generator[CriticReview, None, None]:
    url = build_url(movie, "critic_reviews")
    page = 0
    total = 0
    while url is not None:
        page += 1
        response = session.get(url)
        response.raise_for_status()
        body = response.json()
        items = body["data"]["items"]
        total += len(items)
        logger.info("critic_reviews '%s' page %d: got %d items (total so far: %d)", movie, page, len(items), total)
        for item in items:
            yield CriticReview.from_api(movie, item)
        next_link = body.get("links", {}).get("next")
        url = next_link["href"] if next_link else None


def iter_user_reviews(session: requests.Session, movie: str) -> Generator[UserReview, None, None]:
    url = build_url(movie, "user_reviews")
    page = 0
    total = 0
    while url is not None:
        page += 1
        response = session.get(url)
        response.raise_for_status()
        body = response.json()
        items = body["data"]["items"]
        total += len(items)
        logger.info("user_reviews '%s' page %d: got %d items (total so far: %d)", movie, page, len(items), total)
        for item in items:
            yield UserReview.from_api(movie, item)
        next_link = body.get("links", {}).get("next")
        url = next_link["href"] if next_link else None


def iter_search(
    session: requests.Session,
    query: str,
    *,
    mco_type_id: int = MCO_TYPE_MOVIE,
    limit: int = 30,
    max_items: int | None = None,
) -> Generator[DiscoveredMovie, None, None]:
    api_key = get_api_key(session)
    offset = 0
    total = 0
    yielded = 0
    while True:
        url = build_search_url(query, api_key=api_key, mco_type_id=mco_type_id, offset=offset, limit=limit)
        logger.info("search '%s' offset=%d limit=%d", query, offset, limit)
        response = session.get(url)
        response.raise_for_status()
        body = response.json()
        items = body["data"]["items"]
        total += len(items)
        logger.info("search '%s': got %d items (total so far: %d)", query, len(items), total)
        for item in items:
            yield DiscoveredMovie.from_slug(item["slug"], method="search")
            yielded += 1
            if max_items is not None and yielded >= max_items:
                logger.info("search stopped at max_items=%d", max_items)
                return
        if len(items) < limit:
            break
        offset += limit
    logger.info("search '%s' done: %d results", query, total)


def iter_browse(
    session: requests.Session,
    *,
    mco_type_id: int = MCO_TYPE_MOVIE,
    sort_by: str = "-metaScore",
    limit: int = 24,
    max_items: int | None = None,
    release_year_min: int | None = None,
    release_year_max: int | None = None,
    genres: list[str] | None = None,
    streaming_network_ids: list[int] | None = None,
    in_theatres: bool | None = None,
    release_type: str | None = None,
) -> Generator[DiscoveredMovie, None, None]:
    api_key = get_api_key(session)
    offset = 0
    total = 0
    yielded = 0
    while True:
        url = build_browse_url(
            api_key=api_key,
            mco_type_id=mco_type_id,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            release_year_min=release_year_min,
            release_year_max=release_year_max,
            genres=genres,
            streaming_network_ids=streaming_network_ids,
            in_theatres=in_theatres,
            release_type=release_type,
        )
        logger.info("browse offset=%d limit=%d", offset, limit)
        response = session.get(url)
        response.raise_for_status()
        body = response.json()
        items = body["data"]["items"]
        total += len(items)
        logger.info("browse: got %d items (total so far: %d)", len(items), total)
        for item in items:
            yield DiscoveredMovie.from_slug(item["slug"], method="browse")
            yielded += 1
            if max_items is not None and yielded >= max_items:
                logger.info("browse stopped at max_items=%d", max_items)
                return
        if len(items) < limit:
            break
        offset += limit
    logger.info("browse done: %d movies total", total)
