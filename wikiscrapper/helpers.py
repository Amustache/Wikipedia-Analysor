# URLs
from urllib.parse import urlparse, unquote

import requests

URL_INFOS = "https://{lang}.wikipedia.org/w/api.php"
URL_STATS = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/{access}/{agent}/{uri_article_name}/{granularity}/{start}/{end}"

# Consts
WIKI_LIMIT = 500  # From the API
GLOBAL_LIMIT = WIKI_LIMIT
DEFAULT_DURATION = int(2 * 365.25)  # Number of days for contributions
DEFAULT_LANGS = {"de", "en", "fr"}
ACCESS = "all-access"  # From the API
AGENTS = "all-agents"  # From the API


def get_session():
    """
    Starts request session, that will be used through the whole process
    """
    # Parameters
    HEADERS = {
        "User-Agent": "EPFL WikiStats",
        "From": "noreply@epfl.ch",
        "Accept": "json",
    }

    PARAMS = {
        "action": "query",
        "format": "json",
    }

    s = requests.Session()
    s.headers.update(HEADERS)
    s.params.update(PARAMS)

    return s


def extract_lang_name(link: str) -> tuple[str, str]:
    """
    Extract name and lang
    """
    if "//" not in link:
        link = f"//{link}"
    parsed = urlparse(link)
    lang = parsed.hostname.split(".")[0]
    name = parsed.path.split("/")[-1]
    return lang, unquote(name)
