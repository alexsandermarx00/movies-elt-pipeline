import re
import scrapy
from rottentomatoes.items import FilmSlugItem

SLUG_RE = re.compile(r"^/m/([^/?#]+)")


class RtDiscoverySpider(scrapy.Spider):
    name = "rt_discovery_spider"

    def __init__(self, browse_url="movies_in_theaters", max_pages=5, **kwargs):
        self.allowed_domains = ["www.rottentomatoes.com"]
        self.action = "discovery"
        try:
            self.max_pages = int(max_pages)
        except ValueError:
            self.max_pages = 5
        self.start_urls = [f"https://www.rottentomatoes.com/browse/{browse_url}/"]
        super().__init__(**kwargs)
        self.logger.info(
            "Initialized rt_discovery_spider with browse_url='%s' max_pages=%d",
            browse_url,
            self.max_pages,
        )

    def parse(self, response, page=1):
        seen = set()
        for href in response.css("a::attr(href)").getall():
            match = SLUG_RE.match(href)
            if match:
                slug = match.group(1)
                if slug not in seen:
                    seen.add(slug)
                    self.logger.info("Discovered slug: %s", slug)
                    yield FilmSlugItem(slug=slug)

        self.logger.info("Page %d: extracted %d slugs", page, len(seen))

        if page >= self.max_pages:
            self.logger.info("Reached max_pages=%d, stopping.", self.max_pages)
            return

        next_page = response.css("a[data-track='next']::attr(href)").get()
        if not next_page:
            next_page = response.css("a.js-prev-next-btn[rel='next']::attr(href)").get()
        if not next_page:
            next_page = response.css("a[rel='next']::attr(href)").get()

        if next_page:
            self.logger.info("Following next page: %s", next_page)
            yield response.follow(
                next_page,
                callback=self.parse,
                cb_kwargs={"page": page + 1},
            )
        else:
            self.logger.info("No next-page link found on page %d, stopping.", page)
