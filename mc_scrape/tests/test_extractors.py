from unittest.mock import MagicMock, patch
import pytest

from mc_scrape.metacritic.extractors import iter_general, iter_critic_reviews
from mc_scrape.metacritic.models import GeneralItem, CriticReview

@patch("mc_scrape.metacritic.extractors.build_url")
def test_iter_general(mock_build_url):
    mock_build_url.return_value = "http://fake-url"
    session = MagicMock()
    mock_response = MagicMock()
    # Mocking the JSON response expected by iter_general
    mock_response.json.return_value = {
        "data": {
            "item": {
                "id": "123",
                "slug": "test-movie",
                "title": "Test Movie"
            }
        }
    }
    session.get.return_value = mock_response

    results = list(iter_general(session, "test-movie"))

    assert len(results) == 1
    assert isinstance(results[0], GeneralItem)
    assert mock_build_url.called

@patch("mc_scrape.metacritic.extractors.build_url")
def test_iter_critic_reviews(mock_build_url):
    mock_build_url.return_value = "http://fake-url"
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "items": [
                {
                    "author": "Critic 1",
                    "score": 80,
                    "quote": "Great!"
                }
            ]
        },
        "links": {}
    }
    session.get.return_value = mock_response

    results = list(iter_critic_reviews(session, "test-movie", max_pages=1))

    assert len(results) == 1
    assert isinstance(results[0], CriticReview)
    assert mock_build_url.called
