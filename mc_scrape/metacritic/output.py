import os
import json
import pyarrow as pa
import deltalake
from .models import GeneralItem, CriticReview, UserReview, DiscoveredMovie

FEED_URI = os.environ.get("FEED_URI", "./delta")

_GENERAL_SCHEMA = pa.schema([
    ("movie_slug", pa.string()),
    ("id", pa.int64()),
    ("title", pa.string()),
    ("slug", pa.string()),
    ("description", pa.string()),
    ("release_date", pa.string()),
    ("premiere_year", pa.int64()),
    ("rating", pa.string()),
    ("duration", pa.int64()),
    ("in_theaters", pa.bool_()),
    ("tagline", pa.string()),
    ("imdb_id", pa.string()),
    ("genres", pa.string()),
    ("critic_score", pa.int64()),
    ("critic_review_count", pa.int64()),
    ("critic_sentiment", pa.string()),
])

_CRITIC_SCHEMA = pa.schema([
    ("movie_slug", pa.string()),
    ("quote", pa.string()),
    ("score", pa.int64()),
    ("url", pa.string()),
    ("date", pa.string()),
    ("author", pa.string()),
    ("author_slug", pa.string()),
    ("publication_name", pa.string()),
    ("publication_slug", pa.string()),
])

_USER_SCHEMA = pa.schema([
    ("movie_slug", pa.string()),
    ("review_id", pa.string()),
    ("quote", pa.string()),
    ("score", pa.int64()),
    ("date", pa.string()),
    ("author", pa.string()),
    ("spoiler", pa.bool_()),
    ("thumbs_up", pa.int64()),
    ("thumbs_down", pa.int64()),
])


def write_general(items: list[GeneralItem]) -> None:
    if not items:
        return
    dicts = [item.model_dump() for item in items]
    for d in dicts:
        d["genres"] = json.dumps(d["genres"])
    arrow_table = pa.Table.from_pylist(dicts, schema=_GENERAL_SCHEMA)
    deltalake.write_deltalake(f"{FEED_URI}/general", arrow_table, mode="append")


def write_critic_reviews(items: list[CriticReview]) -> None:
    if not items:
        return
    dicts = [item.model_dump() for item in items]
    arrow_table = pa.Table.from_pylist(dicts, schema=_CRITIC_SCHEMA)
    deltalake.write_deltalake(f"{FEED_URI}/critic_reviews", arrow_table, mode="append")


def write_user_reviews(items: list[UserReview]) -> None:
    if not items:
        return
    dicts = [item.model_dump() for item in items]
    arrow_table = pa.Table.from_pylist(dicts, schema=_USER_SCHEMA)
    deltalake.write_deltalake(f"{FEED_URI}/user_reviews", arrow_table, mode="append")


_DISCOVERED_SCHEMA = pa.schema([
    ("slug", pa.string()),
    ("discovered_at", pa.timestamp("us")),
    ("method", pa.string()),
])


def write_discovered(items: list[DiscoveredMovie]) -> None:
    if not items:
        return
    dicts = [item.model_dump() for item in items]
    arrow_table = pa.Table.from_pylist(dicts, schema=_DISCOVERED_SCHEMA)
    deltalake.write_deltalake(f"{FEED_URI}/discovered_movies", arrow_table, mode="append")
