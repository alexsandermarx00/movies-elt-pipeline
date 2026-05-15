import os
import logging
from scrapy import signals

logger = logging.getLogger(__name__)


class SpiderExitCodeExtension:
    """
    Scrapy extension that propagates spider failures as non-zero exit codes.

    By default, Scrapy always exits with code 0 even when the spider raises
    exceptions or logs errors. This makes it impossible for orchestrators like
    Airflow's DockerOperator to detect failures automatically.

    This extension hooks into the `spider_closed` signal and checks the final
    stats for any recorded errors or exceptions. If any are found, it calls
    sys.exit(1) so the container exits with a non-zero code that Airflow can
    detect and mark the task as failed.
    """

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider, reason):
        stats = spider.crawler.stats.get_stats()

        error_count = stats.get("spider_exceptions/Exception", 0)
        log_errors = stats.get("log_count/ERROR", 0)

        if reason != "finished" or error_count > 0 or log_errors > 0:
            logger.error(
                "Spider closed with reason='%s', errors=%d, log_errors=%d. Exiting with code 1.",
                reason,
                error_count,
                log_errors,
            )
            os._exit(1)
