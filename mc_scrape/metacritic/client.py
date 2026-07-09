import os
import re
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://backend.metacritic.com/"
_MC_HOME = "https://www.metacritic.com/"
_API_KEY_RE = re.compile(r'apiKey=([A-Za-z0-9]+)')

# mcoTypeId values used by the finder/search endpoints
MCO_TYPE_MOVIE = 2
MCO_TYPE_TV = 1
MCO_TYPE_PERSON = 3

logger = logging.getLogger(__name__)


_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def make_session() -> requests.Session:
    import random
    import time

    session = requests.Session()
    # 429/5xx are retried with exponential backoff at the transport layer, and
    # Retry-After is honored (respect_retry_after_header). Knobs are env-tunable
    # so the request rate can be dialed to a site's tolerance without code edits.
    retry = Retry(
        total=int(os.environ.get("MC_MAX_RETRIES", "5")),
        backoff_factor=float(os.environ.get("MC_BACKOFF_FACTOR", "2")),
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    delay_min = float(os.environ.get("MC_REQUEST_DELAY_MIN", "1.0"))
    delay_max = float(os.environ.get("MC_REQUEST_DELAY_MAX", "3.0"))

    def _throttle(response, **kwargs):
        time.sleep(random.uniform(delay_min, delay_max))

    session.hooks["response"].append(_throttle)
    return session


def fetch_api_key(session: requests.Session) -> str:
    import random
    import time

    # A 200 with no apiKey in the HTML is a bot/interstitial page — a soft block.
    # urllib3's Retry can't catch it (it's a 200), so retry with backoff here.
    attempts = int(os.environ.get("MC_APIKEY_MAX_ATTEMPTS", "5"))
    for attempt in range(1, attempts + 1):
        logger.info("Fetching Metacritic API key from homepage (attempt %d/%d)", attempt, attempts)
        response = session.get(_MC_HOME)
        response.raise_for_status()
        match = _API_KEY_RE.search(response.text)
        if match:
            logger.info("API key fetched successfully")
            return match.group(1)
        if attempt < attempts:
            delay = min(2 ** attempt + random.uniform(0, 1), 60)
            logger.warning(
                "No API key in homepage HTML (likely a bot page); backing off %.1fs before retry",
                delay,
            )
            time.sleep(delay)
    raise RuntimeError("Could not extract Metacritic API key from page HTML after retries")


def get_api_key(session: requests.Session) -> str:
    env_key = os.environ.get("MC_API_KEY")
    if env_key:
        return env_key
    cached = getattr(session, "_mc_api_key", None)
    if cached:
        return cached
    key = fetch_api_key(session)
    session._mc_api_key = key  # type: ignore[attr-defined]
    return key


def build_url(movie: str, action: str) -> str:
    if action == "general":
        return BASE_URL + f"movies/metacritic/{movie}/web"
    elif action == "user_reviews":
        return BASE_URL + f"reviews/metacritic/user/movies/{movie}/web"
    elif action == "critic_reviews":
        return BASE_URL + f"reviews/metacritic/critic/movies/{movie}/web"
    else:
        raise ValueError(f"Unknown action: {action!r}")


def build_search_url(query: str, api_key: str, mco_type_id: int, offset: int, limit: int) -> str:
    params = (
        f"offset={offset}&limit={limit}"
        f"&mcoTypeId={mco_type_id}"
        f"&apiKey={api_key}"
        f"&componentName=search&componentDisplayName=Search&componentType=SearchResults"
    )
    return BASE_URL + f"finder/metacritic/search/{query}/web?{params}"


def build_browse_url(
    api_key: str,
    mco_type_id: int,
    offset: int,
    limit: int,
    sort_by: str = "-metaScore",
    release_year_min: int | None = None,
    release_year_max: int | None = None,
    genres: list[str] | None = None,
    streaming_network_ids: list[int] | None = None,
    in_theatres: bool | None = None,
    release_type: str | None = None,
) -> str:
    from urllib.parse import quote
    params = [
        f"mcoTypeId={mco_type_id}",
        f"limit={limit}",
        f"offset={offset}",
        f"sortBy={sort_by}",
        f"apiKey={api_key}",
        "componentName=finder&componentDisplayName=Movie+Finder&componentType=SearchResults",
    ]
    if release_year_min is not None:
        params.append(f"releaseYearMin={release_year_min}")
    if release_year_max is not None:
        params.append(f"releaseYearMax={release_year_max}")
    if in_theatres:
        params.append("inTheatres=true")
    if release_type:
        params.append(f"releaseType={release_type}")
    if streaming_network_ids:
        params.append(f"streamingNetworkIds={','.join(str(i) for i in streaming_network_ids)}")
    url = BASE_URL + "finder/metacritic/web?" + "&".join(params)
    if genres:
        url += "&genres=" + ",".join(quote(g) for g in genres)
    return url
