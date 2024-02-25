import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from pprint import pprint

from wikiscrapper.WikiPage import WikiPage
from wikiscrapper.helpers import DEFAULT_DURATION, GLOBAL_LIMIT, DEFAULT_LANGS, get_session, extract_lang_name


@dataclass
class WikiQuery:
    # Parameters
    targets: str | Iterable[str] = None  # Targets to seek for
    target_langs: str | Iterable[str] = None  # Languages to seek for
    last_updated: datetime.datetime = datetime.datetime.now()  # When was the query made
    target_duration: int = DEFAULT_DURATION  # Number of days for contributions
    granularity: str = "daily"  # Granularity for contributions
    backlinks_limit: int = GLOBAL_LIMIT  # Number of backlinks to retrieve at most
    contributions_limit: int = GLOBAL_LIMIT  # Number of contributions to retrieve at most
    verbose: bool = False  # PRINT EVERYTHING or don't

    def __post_init__(self):
        # Create set for targets
        if self.targets is None:
            self.targets = set()
        if not isinstance(self.targets, set):
            self.targets = set(
                self.targets.split() if isinstance(self.targets, str) else self.targets
            )

        # Create set for langs
        if self.target_langs is None:
            self.target_langs = DEFAULT_LANGS
        if not isinstance(self.target_langs, set):
            self.target_langs = set(
                self.target_langs.split() if isinstance(self.target_langs, str) else self.target_langs
            )

        # Session
        self.s = get_session()  # Session for requests

        self.results = {}

        self.links_to_find = {}
        self.update_links_to_find(self.targets)

    def add_targets(self, targets: str | Iterable[str]):
        if isinstance(targets, str):
            targets = targets.split()

        self.targets.update(targets)
        self.update_links_to_find(targets)

    def add_langs(self, langs: str | Iterable[str]):
        if isinstance(langs, str):
            langs = langs.split()

        self.target_langs.update(langs)
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
                self.results[name] = WikiPage(name, lang)

                self.links_to_find[lang].remove(name)  # Found or non-existent
                if len(self.links_to_find[lang]) == 0:  # No more entries
                    del self.links_to_find[lang]
