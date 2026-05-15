from pydantic import BaseModel
from datetime import datetime


class DiscoveredMovie(BaseModel):
    slug: str
    discovered_at: datetime
    method: str  # "browse" or "search"

    @classmethod
    def from_slug(cls, slug: str, method: str) -> "DiscoveredMovie":
        return cls(
            slug=slug,
            discovered_at=datetime.utcnow(),
            method=method,
        )


class GeneralItem(BaseModel):
    movie_slug: str
    id: int
    title: str
    slug: str
    description: str | None
    release_date: str | None
    premiere_year: int | None
    rating: str | None
    duration: int | None
    in_theaters: bool | None
    tagline: str | None
    imdb_id: str | None
    genres: list[str]
    critic_score: int | None
    critic_review_count: int | None
    critic_sentiment: str | None

    @classmethod
    def from_api(cls, movie_slug: str, item: dict) -> "GeneralItem":
        critic_summary = item.get("criticScoreSummary") or {}
        genres = [g["name"] for g in (item.get("genres") or []) if "name" in g]
        return cls(
            movie_slug=movie_slug,
            id=item["id"],
            title=item["title"],
            slug=item["slug"],
            description=item.get("description"),
            release_date=item.get("releaseDate"),
            premiere_year=item.get("premiereYear"),
            rating=item.get("rating"),
            duration=item.get("duration"),
            in_theaters=item.get("inTheaters"),
            tagline=item.get("tagline"),
            imdb_id=item.get("imdbId"),
            genres=genres,
            critic_score=critic_summary.get("score"),
            critic_review_count=critic_summary.get("reviewCount"),
            critic_sentiment=critic_summary.get("sentiment"),
        )


class CriticReview(BaseModel):
    movie_slug: str
    quote: str
    score: int | None
    url: str | None
    date: str | None
    author: str | None
    author_slug: str | None
    publication_name: str | None
    publication_slug: str | None

    @classmethod
    def from_api(cls, movie_slug: str, item: dict) -> "CriticReview":
        return cls(
            movie_slug=movie_slug,
            quote=item.get("quote", ""),
            score=item.get("score"),
            url=item.get("url"),
            date=item.get("date"),
            author=item.get("author"),
            author_slug=item.get("authorSlug"),
            publication_name=item.get("publicationName"),
            publication_slug=item.get("publicationSlug"),
        )


class UserReview(BaseModel):
    movie_slug: str
    review_id: str
    quote: str | None
    score: int | None
    date: str | None
    author: str | None
    spoiler: bool
    thumbs_up: int | None
    thumbs_down: int | None

    @classmethod
    def from_api(cls, movie_slug: str, item: dict) -> "UserReview":
        return cls(
            movie_slug=movie_slug,
            review_id=item.get("id", ""),
            quote=item.get("quote"),
            score=item.get("score"),
            date=item.get("date"),
            author=item.get("author"),
            spoiler=item.get("spoiler", False),
            thumbs_up=item.get("thumbsUp"),
            thumbs_down=item.get("thumbsDown"),
        )
