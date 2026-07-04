import pytest
from rottentomatoes.items import (
    DetailsItem, ScoreItem, ReviewItem, CriticReviewItem, FilmSlugItem
)

def test_details_item():
    item = DetailsItem(movie_id="123", title="Test Movie", rating="PG-13", release="2020", rtid="rt123", urlid="test-movie")
    assert item["movie_id"] == "123"
    assert item["title"] == "Test Movie"

def test_score_item():
    item = ScoreItem(movie_id="123", audienceAll=80, criticsAll=90)
    assert item["audienceAll"] == 80
    assert item["criticsAll"] == 90

def test_review_item():
    item = ReviewItem(movie_id="123", rating=5.0, quote="Excellent", reviewId="rev1")
    assert item["quote"] == "Excellent"

def test_critic_review_item():
    item = CriticReviewItem(movie_id="123", critic_name="Critic", publication="NYT", score=100)
    assert item["critic_name"] == "Critic"

def test_film_slug_item():
    item = FilmSlugItem(slug="test-movie")
    assert item["slug"] == "test-movie"
