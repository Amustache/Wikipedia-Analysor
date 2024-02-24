import datetime
from dataclasses import dataclass
from pprint import pprint
from typing import List, Union
from urllib.parse import urlparse, unquote

import requests
from requests import Session

# URLs
URL_INFOS = "https://{lang}.wikipedia.org/w/api.php"
URL_STATS = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/{access}/{agent}/{uri_article_name}/{granularity}/{start}/{end}"

# Consts
WIKI_LIMIT = 500  # From the API
GLOBAL_LIMIT = WIKI_LIMIT
DEFAULT_DURATION = int(2 * 365.25)  # Number of days for contributions
DEFAULT_LANGS = ["en", "fr", "de"]
ACCESS = "all-access"  # From the API
AGENTS = "all-agents"  # From the API


@dataclass
class WikiPage:
    None


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


@dataclass
class WikiQuery:
    # Parameters
    targets: Union[str, List[str]] = None  # Targets to seek for
    target_langs: Union[str, List[str]] = None  # Languages to seek for
    last_updated: datetime.datetime = None  # When was the query made
    target_duration: int = DEFAULT_DURATION  # Number of days for contributions
    granularity: str = "daily"  # Granularity for contributions
    backlinks_limit: int = GLOBAL_LIMIT  # Number of backlinks to retrieve at most
    contributions_limit: int = GLOBAL_LIMIT  # Number of contributions to retrieve at most
    verbose: bool = False  # PRINT EVERYTHING or don't

    def __post_init__(self):
        if isinstance(self.targets, str):
            self.targets = self.targets.split()

        if self.target_langs is None:
            self.target_langs = DEFAULT_LANGS
        if isinstance(self.target_langs, str):
            self.target_langs = self.target_langs.split()

        # Session
        self.s = get_session()  # Session for requests

        self.results = {}

        self.links_to_find = {}
        self.find_links(self.targets)

    def add_targets(self, targets: Union[str, List[str]]):
        if isinstance(targets, str):
            targets = targets.split()

        self.targets += targets
        self.find_links(targets)

    def add_langs(self, langs: Union[str, List[str]]):
        if isinstance(langs, str):
            langs = langs.split()

        self.target_langs += langs
        self.find_links(self.targets)

    def find_links(self, targets):
        for link in targets:
            if link == "":
                continue
            link = link.replace('"', "").replace("'", "").replace(",", "")  # If copypasta from Python
            # If it's a link, extract lang and name
            if "wikipedia.org" in link:
                lang, name = extract_lang_name(link)
                if lang not in self.links_to_find:
                    self.links_to_find[lang] = set()
                self.links_to_find[lang].add(name)
            # Else, we assume it's directly a name, and try to find it
            else:
                if "*" not in self.links_to_find:
                    self.links_to_find["*"] = set()
                self.links_to_find["*"].add(link)
        # Each name without a lang will be tracked down using target langs
        if "*" in self.links_to_find:
            for name in self.links_to_find["*"]:
                for lang in self.target_langs:
                    if lang not in self.links_to_find:
                        self.links_to_find[lang] = set()
                    self.links_to_find[lang].add(name)

            del self.links_to_find["*"]
        if self.verbose:
            pprint(self.links_to_find)


test = WikiQuery("Bonjour")
print(test)
print(test.links_to_find)
test.add_targets("https://en.wikipedia.org/wiki/H._P._Lovecraft")
test.add_targets(["Martin Vetterli", "Philippe Moris"])
print(test)
print(test.links_to_find)
test.add_langs("it")
print(test)
print(test.links_to_find)
