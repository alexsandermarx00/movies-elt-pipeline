import json
import scrapy
from urllib.parse import urlencode
from rottentomatoes.items import DetailsItem, ScoreItem, ReviewItem


class RtspiderSpider(scrapy.Spider):
    name = "rtspider"

    def __init__(self, movie, action, max_pages=2, **kwargs):
        self.allowed_domains = ["www.rottentomatoes.com"]
        self.start_urls = [f"https://www.rottentomatoes.com/m/{movie}"]
        self.action = action
        self.movie_id = movie
        try:
            self.max_pages = int(max_pages)
        except ValueError:
            self.max_pages = 2
        super().__init__(**kwargs)
        self.logger.info("Initialized spider for movie '%s' with action '%s' and max_pages '%s'", movie, action, self.max_pages)

    def parse(self, response):
        notas_json_str = response.xpath("//script[@id='media-scorecard-json']/text()").get()
        if not notas_json_str:
            self.logger.error("Could not find media-scorecard-json script tag in page.")
            return
        notas_json = json.loads(notas_json_str)

        if self.action == "score":
            scoreitem = ScoreItem()
            scoreitem["movie_id"] = self.movie_id
            score = notas_json["overlay"]
            scoreitem["audienceAll"] = score["audienceAll"]
            scoreitem["audienceVerified"] = score["audienceVerified"]
            scoreitem["criticsAll"] = score["criticsAll"]
            scoreitem["criticsTop"] = score["criticsTop"]
            scoreitem["description"] = notas_json["description"]

            yield scoreitem

        elif self.action == "reviews":
            movie_code = notas_json["criticReviewHref"].split("/")[-1]
            self.logger.info("Resolved internal movie code for %s: %s", self.movie_id, movie_code)
            base_url = f"https://www.rottentomatoes.com/napi/rtcf/v1/movies/{movie_code}/reviews"
            params = {
                "after": "",
                "before": "",
                "pageCount": 20,
                "topOnly": "false",
                "type": "audience",
                "verified": "false"
            }
            yield scrapy.Request(
                f"{base_url}?{urlencode(params)}",
                callback=self.parse_reviews,
                cb_kwargs={"n": self.max_pages, "movie_code": movie_code}
            )

        elif self.action == "details":
            details_str = response.xpath("//script[@id='mps-page-integration']/text()").get()
            if not details_str:
                self.logger.error("Could not find mps-page-integration script tag in page.")
                return
            import re
            match = re.search(r"window\.mpscall\s*=\s*(\{.*?\});", details_str, re.DOTALL)
            if not match:
                self.logger.error("Could not extract mpscall json from script.")
                return
            details = json.loads(match.group(1))

            detailsitem = DetailsItem()
            detailsitem["movie_id"] = self.movie_id
            detailsitem["title"] = details["title"]
            detailsitem["rating"] = details.get("cag[rating]")
            detailsitem["release"] = details.get("cag[release]")
            detailsitem["rtid"] = details.get("field[rtid]")
            detailsitem["urlid"] = details.get("cag[urlid]")

            yield detailsitem
        else:
            self.logger.error("Invalid action specified: %s", self.action)
            raise ValueError("Invalid action")

    def parse_reviews(self, response, n, movie_code):
        data = response.json()
        reviews_extracted = len(data.get("reviews", []))
        self.logger.info("Extracted %d reviews from current page", reviews_extracted)
        for review in data["reviews"]:
            reviewsitem = ReviewItem()
            reviewsitem["movie_id"] = self.movie_id
            reviewsitem["rating"] = review.get("rating", None)
            reviewsitem["quote"] = review.get("review", None)
            reviewsitem["reviewId"] = review.get("ratingId", None)
            reviewsitem["isVerified"] = review.get("isVerified", None)
            reviewsitem["isSuperReviewer"] = review.get("isSuperReviewer", None)
            reviewsitem["hasSpoilers"] = review.get("hasSpoilers", None)
            reviewsitem["hasProfanity"] = review.get("hasProfanity", None)
            reviewsitem["creationDate"] = review.get("createDate", None)
            user_data = review.get("user", {})
            reviewsitem["userAccountLink"] = user_data.get("profileHandle", None)
            reviewsitem["userDisplayName"] = review.get("displayName", None)
            reviewsitem["userRealm"] = user_data.get("realm", None)
            reviewsitem["userId"] = user_data.get("encryptedUserId", None)
            yield reviewsitem

        if data["pageInfo"]["hasNextPage"] is True and n > 1:
            self.logger.info("Found next page (n=%d limit remaining). Yielding next request.", n - 1)
            base_url = f"https://www.rottentomatoes.com/napi/rtcf/v1/movies/{movie_code}/reviews"
            params = {
                "after": data["pageInfo"]["endCursor"],
                "before": "",
                "pageCount": 20,
                "topOnly": "false",
                "type": "audience",
                "verified": "false"
            }
            yield scrapy.Request(
                f"{base_url}?{urlencode(params)}",
                callback=self.parse_reviews,
                cb_kwargs={"n": n - 1, "movie_code": movie_code}
            )
