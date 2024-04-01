from collections.abc import Iterable
from dataclasses import dataclass
from itertools import batched
from pprint import pprint
import datetime
import json


from wikiscrapper.fetchers import FETCHERS
from wikiscrapper.helpers import (
    DEFAULT_DURATION,
    DEFAULT_LANGS,
    extract_lang_name,
    get_session,
    GLOBAL_LIMIT,
    URL_INFOS,
    Verbose,
    WIKI_LIMIT,
    WIKI_TITLES_LIMIT,
)
from wikiscrapper.WikiPage import WikiPage


def merge_wiki_pages(found):
    """
    Merge linked pages with different names.

    We assume here that pages are correctly linked (by Wikipedia) between each other.

    :param found: dict of {name: data}.
    :return: dict of {name: data}.
    """
    results = {}
    for name, content in found.items():
        skip = False
        for _, pagename in content["langlinks"].items():
            if pagename in results:  # Page with that name already exists
                skip = True
                break

        if not skip:
            results[name] = content
    return results


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
    verbose: bool | int = False  # PRINT EVERYTHING or don't; 0/False = Normal, 1/True = Info, 2 = Debug, 3 = Trace

    def __post_init__(self):
        """
        Various attribute transformations
        """
        # Create set for targets
        if self.targets is None:
            self.targets = set()
        if isinstance(self.targets, str):
            self.targets = {self.targets}
        if not isinstance(self.targets, set):
            self.targets = set(self.targets)
        self.targets = set(filter(None, self.targets))  # Remove empty

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
        self._update_links_to_find(self.targets)

        if self.verbose >= Verbose.TRACE:
            pprint(">>> Post init is done.")

        return self

    def _update_links_to_find(self, targets):
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

        if self.verbose >= Verbose.TRACE:
            pprint(">>> Links to find updated:")
            pprint(self.links_to_find)

    def _find_wiki_pages(self):
        """
        Try to find each page on Wikipedia.

        `data` contains query language and timestamp.
        `data` for `found` contains the found pages in different languages
        `data` for `not_found` contains an error.

        :return: dict of {name: data}, dict of {name: data}.
        """
        found = {}
        not_found = {}

        for query_lang, names in self.links_to_find.items():
            # We group the queries per target lang for fewer queries
            url_full = URL_INFOS.format(lang=query_lang)
            # Only 50 titles at a time
            for batch in batched(names, WIKI_TITLES_LIMIT):
                titles = "|".join(batch)
                params = {
                    "titles": titles,
                    "prop": "langlinks",
                    "lllimit": WIKI_LIMIT,  # We want all langs in order to find our target langs
                    "redirects": 1,  # For those perky redirects
                }

                results = self.s.get(url=url_full, params=params)
                timestamp = datetime.datetime.now().isoformat()
                data = results.json()

                if "query" in data and "pages" in data["query"]:
                    data = data["query"]["pages"]
                else:
                    raise AttributeError("Error while querying.")

                for pid, content in data.items():
                    pageid = int(pid)
                    title = content["title"]

                    result = {
                        title: {
                            "query": {
                                "lang": query_lang,
                                "timestamp": timestamp,
                            }
                        }
                    }

                    # Page is not found with that language
                    if pageid < 0:
                        if self.verbose >= Verbose.DEBUG:
                            pprint(f">> `{query_lang}/{title}` not found.")

                        result[title]["error"] = "not found"
                        not_found.update(result)
                        continue

                    # Page is found
                    # Add languages
                    result[title]["langlinks"] = {}
                    if "langlinks" in content:
                        result[title]["langlinks"].update(
                            {langlink["lang"]: langlink["*"] for langlink in content["langlinks"]}
                        )
                    result[title]["langlinks"].update({query_lang: title})

                    # Will only keep the latest successful result for same name pages
                    found.update(result)

        # Nothing left to find
        self.links_to_find.clear()

        if self.verbose:
            pprint(f"> Found {len(found)} links ({len(not_found)} not found)")

        return found, not_found

    def _fetch_for_all(self):
        for page, langs in self.results.items():
            if self.verbose >= Verbose.INFO:
                pprint(f"> Fetching for `{page}`")

            if langs is None:
                if self.verbose >= Verbose.TRACE:
                    pprint(">>> Nothing to be done")
                continue

            for wikipage in langs.values():
                if self.verbose >= Verbose.DEBUG:
                    pprint(f">> For `{wikipage.lang}/{wikipage.title}`")

                for fetch_fun in FETCHERS:
                    if self.verbose >= Verbose.TRACE:
                        pprint(f">>> Using `{fetch_fun.__name__}`")
                    yield fetch_fun(wikipage, self.s)

    def add_targets(self, targets: str | Iterable[str]):
        if isinstance(targets, str):
            targets = targets.split()

        self.targets.update(targets)
        if self.verbose >= Verbose.DEBUG:
            pprint(f">> Added {len(targets)} new targets.")

        self._update_links_to_find(targets)

        return self

    def add_langs(self, langs: str | Iterable[str]):
        if isinstance(langs, str):
            langs = langs.split()

        self.target_langs.update(langs)

        if self.verbose >= Verbose.DEBUG:
            pprint(f">> Added {len(langs)} new langs.")

        self._update_links_to_find(self.targets)

        return self

    def update(self, force=False, gen=False):
        # If we want to update all the links
        if force:
            self._update_links_to_find(self.targets)

        # If there is nothing to update, return
        if len(self.links_to_find) == 0:
            return

        # Try to find each page on Wikipedia
        found, not_found = self._find_wiki_pages()

        # Merge linked pages with different names
        merged = merge_wiki_pages(found)

        # All links are found, prepare for next steps
        self.results.update({page: None for page in not_found.keys()})
        self.results.update(
            {
                page: {
                    lang: WikiPage(
                        title=content["langlinks"][lang],
                        lang=lang,
                    ).add_langs(content["langlinks"])
                    for lang in self.target_langs
                    if lang in content["langlinks"]
                }
                for page, content in merged.items()
            }
        )

        if gen:
            # Generator for fetching all attributs, for all pages
            expected = []
            for target, langs in self.results.items():
                if langs:
                    for lang, wikipage in langs.items():
                        for fetcher in FETCHERS:
                            expected.append((wikipage.lang, wikipage.title, fetcher.__name__))
            return self._fetch_for_all(), expected
        else:
            # Exhaust generator
            list(self._fetch_for_all())
            return self

    def export_json(self, file=None):
        def default_export(obj):
            if isinstance(obj, WikiPage):
                return obj.export_json()
            else:
                return "???"

        res = json.loads(json.dumps(self.results, default=default_export))

        if file:
            with open(file, "w") as f:
                json.dump(
                    res,
                    f,
                    indent=2,
                    default=default_export,
                )
        else:
            return res

    @property
    def num_targets(self):
        return len(self.targets)

    @property
    def num_targets_langs(self):
        return len(self.target_langs)

    @property
    def num_targets_not_found(self):
        return sum(value is None for value in self.results.values())

    @property
    def num_targets_found(self):
        return sum(value is not None for value in self.results.values())

    @property
    def num_pages(self):
        return sum(len(value) for value in self.results.values() if value is not None)

    def calculate_scores(self):
        for target, langs in self.results.items():
            if langs:
                for lang, wikipage in langs.items():
                    _ = wikipage.pri_score  # Only used to get the actual data
