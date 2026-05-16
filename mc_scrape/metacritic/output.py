import json
import os
import time
from pathlib import Path

from .models import CriticReview, DiscoveredMovie, GeneralItem, UserReview

FEED_URI = os.environ.get("FEED_URI", "./delta")


def _write_json(subdir: str, items: list) -> None:
    if not items:
        return
    out_dir = Path(FEED_URI) / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{int(time.time() * 1000)}.json"
    with open(out_file, "w") as f:
        json.dump([item.model_dump() for item in items], f, default=str)


def write_general(items: list[GeneralItem]) -> None:
    _write_json("general", items)


def write_critic_reviews(items: list[CriticReview]) -> None:
    _write_json("critic_reviews", items)


def write_user_reviews(items: list[UserReview]) -> None:
    _write_json("user_reviews", items)


def write_discovered(items: list[DiscoveredMovie]) -> None:
    _write_json("discovered_movies", items)
