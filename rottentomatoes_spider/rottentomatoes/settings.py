# Scrapy settings for rottentomatoes project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "rottentomatoes"

SPIDER_MODULES = ["rottentomatoes.spiders"]
NEWSPIDER_MODULE = "rottentomatoes.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "rottentomatoes (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   "rottentomatoes.middlewares.RottentomatoesSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   "rottentomatoes.middlewares.RottentomatoesDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    "rottentomatoes.extensions.SpiderExitCodeExtension": 500,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "rottentomatoes.pipelines.RottentomatoesPipeline": 3000
}


import os as _os

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# Rate knobs are env-tunable so concurrency can be dialed to RT's tolerance
# without editing code (see the scaling plan's "balanced" tuning).
AUTOTHROTTLE_ENABLED = True
DOWNLOAD_DELAY = float(_os.environ.get("RT_DOWNLOAD_DELAY", "2"))
RANDOMIZE_DOWNLOAD_DELAY = True  # uses 0.5–1.5× DOWNLOAD_DELAY per request
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = float(_os.environ.get("RT_AUTOTHROTTLE_MAX_DELAY", "30"))
AUTOTHROTTLE_TARGET_CONCURRENCY = float(_os.environ.get("RT_TARGET_CONCURRENCY", "1.0"))
CONCURRENT_REQUESTS_PER_DOMAIN = int(_os.environ.get("RT_CONCURRENCY_PER_DOMAIN", "4"))
AUTOTHROTTLE_DEBUG = False

# Retry on throttling / transient errors. 429 and 503 are the throttle signals;
# RetryMiddleware honors Retry-After. More attempts + backoff so a brief block
# recovers within the crawl instead of failing the whole shard.
RETRY_ENABLED = True
RETRY_TIMES = int(_os.environ.get("RT_RETRY_TIMES", "5"))
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
RETRY_BACKOFF = True  # Scrapy 2.12+: exponential backoff between retries

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
import os
FEED_EXPORT_ENCODING = "utf-8"
# LOG_FILE = "scrapy.log"

# Persistent Output Pipeline (S3, GCS, Local)
FEED_URI = os.environ.get('FEED_URI', '.output/%(action)s/%(name)s_%(time)s.json')
FEEDS = {
    FEED_URI: {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 4,
        'overwrite': True,
    }
}
