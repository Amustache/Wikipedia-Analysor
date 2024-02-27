from collections.abc import Iterable
from dataclasses import dataclass
from itertools import batched
from pprint import pprint
import datetime
import json


from wikiscrapper.helpers import (
    DEFAULT_DURATION,
    DEFAULT_LANGS,
    extract_lang_name,
    get_session,
    GLOBAL_LIMIT,
    URL_INFOS,
    WIKI_LIMIT,
    WIKI_TITLES_LIMIT,
)
from wikiscrapper.WikiPage import WikiPage


def merge_wiki_pages(found):
    """
    Merge linked pages with different names.

    We assume here that pages are correctly linked (by Wikipedia) between each other.

    :param found:
    :return:
    """
    results = {}
    for name, content in found.items():
        skip = False
        for langlink in content["langlinks"]:
            for page in langlink.values():  # Only one
                if page in results:  # Page with that name already exists
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
    verbose: bool = False  # PRINT EVERYTHING or don't

    def __post_init__(self):
        """
        Various attribute transformations
        """
        # Create set for targets
        if self.targets is None:
            self.targets = set()
        if not isinstance(self.targets, set):
            self.targets = set(self.targets.split() if isinstance(self.targets, str) else self.targets)

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

    def add_targets(self, targets: str | Iterable[str]):
        if isinstance(targets, str):
            targets = targets.split()

        self.targets.update(targets)
        self._update_links_to_find(targets)

    def add_langs(self, langs: str | Iterable[str]):
        if isinstance(langs, str):
            langs = langs.split()

        self.target_langs.update(langs)
        self._update_links_to_find(self.targets)

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
        if self.verbose:
            pprint(self.links_to_find)

    def update(self, force=False):
        # If we want to update all the links
        if force:
            self._update_links_to_find(self.targets)

        # If there is nothing to update, return
        if len(self.links_to_find) == 0:
            return

        # Try to find each page on Wikipedia
        found, not_found = self._find_wiki_pages()

        # Merge linked pages with different names
        results = merge_wiki_pages(found)

        # All links are found, prepare for next steps
        self.results.update(results)

        print(json.dumps(results))

        #     for query_name in names:
        #         self.results[query_name] = {}
        #
        #         # ...
        #         # ...
        #
        #         self.links_to_find[query_lang].remove(query_name)  # Found or non-existent
        #         if len(self.links_to_find[query_lang]) == 0:  # No more entries
        #             del self.links_to_find[query_lang]
        #
        # # We are done
        # self.links_to_find = local_links_to_find

    def _find_wiki_pages(self):
        """
        Try to find each page on Wikipedia.

        :return:
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
                        result[title]["error"] = "not found"
                        not_found.update(result)
                        continue

                    # Page is found
                    # Add languages
                    result[title]["langlinks"] = [
                        {langlink["lang"]: langlink["*"]} for langlink in content["langlinks"]
                    ]
                    result[title]["langlinks"].append({query_lang: title})

                    # Will only keep the latest successful result for same name pages
                    found.update(result)

        return found, not_found