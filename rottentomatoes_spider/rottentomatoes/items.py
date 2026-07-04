# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class DetailsItem(Item):
    movie_id = Field()
    title = Field()
    rating = Field()
    release = Field()
    rtid = Field()
    urlid = Field()


class ScoreItem(Item):
    movie_id = Field()
    audienceAll = Field()
    audienceVerified = Field()
    criticsAll = Field()
    criticsTop = Field()
    description = Field()


class ReviewItem(Item):
    movie_id = Field()
    rating = Field()
    quote = Field()
    reviewId = Field()
    isVerified = Field()
    isSuperReviewer = Field()
    hasSpoilers = Field()
    hasProfanity = Field()
    creationDate = Field()
    userAccountLink = Field()
    userDisplayName = Field()
    userRealm = Field()
    userId = Field()


class CriticReviewItem(Item):
    movie_id    = Field()
    review_id   = Field()
    critic_name = Field()
    publication = Field()
    score       = Field()
    quote       = Field()
    review_date = Field()


class FilmSlugItem(Item):
    slug = Field()
