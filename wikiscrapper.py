import datetime
from dataclasses import dataclass
from pprint import pprint
from typing import List, Union, Set
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
        if self.targets is None:
            self.targets = list()
        if not isinstance(self.targets, list):
            self.targets = list(set(self.targets.split()))

        if self.target_langs is None:
            self.target_langs = DEFAULT_LANGS
        if not isinstance(self.target_langs, list):
            self.target_langs = list(set(self.target_langs.split()))

        # Session
        self.s = get_session()  # Session for requests

        self.results = {}

        self.links_to_find = {}
        self.update_links_to_find(self.targets)

    def add_targets(self, targets: Union[str, List[str]]):
        if isinstance(targets, str):
            targets = targets.split()

        self.targets += list(set(targets))
        self.update_links_to_find(targets)

    def add_langs(self, langs: Union[str, List[str]]):
        if isinstance(langs, str):
            langs = langs.split()

        self.target_langs += list(set(langs))
        self.update_links_to_find(self.targets)

    def update_links_to_find(self, targets):
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

    def update(self, force=False):
        # If we want to update all the links
        if force:
            self.update_links_to_find(self.targets)

        # If there is nothing to update, return
        if len(self.links_to_find) == 0:
            return

        # Local copy of links to find
        local_links_to_find = self.links_to_find.copy()

        for lang, names in local_links_to_find.items():
            for name in names:
                pass

                self.links_to_find[lang].remove(name)  # Found or non-existent

truc = {1,2,3}
test = WikiQuery("Bonjour")
print(test)
print(test.links_to_find)
test.add_targets("https://en.wikipedia.org/wiki/H._P._Lovecraft")
test.add_targets(["Martin Vetterli", "Philippe Moris", "Bonjour"])
print(test)
print(test.links_to_find)
test.add_langs("it")
print(test)
print(test.links_to_find)
