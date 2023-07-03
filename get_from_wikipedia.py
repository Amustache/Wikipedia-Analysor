import requests
from urllib.parse import urlparse, unquote, quote
from pprint import pprint
import datetime
import json
from collections import Counter

# URLs
URL_INFOS = "https://{lang}.wikipedia.org/w/api.php"
URL_STATS = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/{access}/{agent}/{uri_article_name}/{granularity}/{start}/{end}"

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

GLOBAL_LIMIT = 25
WIKI_LIMIT = 500  # From the API

BACKLINKS_LIMIT = GLOBAL_LIMIT
CONTRIBS_LIMIT = WIKI_LIMIT
DEFAULT_DURATION = int(2 * 365.25)
ACCESS = "all-access"
AGENTS = "all-agents"
GRANULARITY = "daily"

VERBOSE = False

DEFAULT_LANGS = ["en", "fr", "de"]
TARGET_DURATION = DEFAULT_DURATION


def get_session():
    # Starts request session, that will be used through the whole process
    s = requests.Session()
    s.headers.update(HEADERS)
    s.params.update(PARAMS)

    return s


s = get_session()


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


def qprint(json_queries):
    """
    Check if correct JSON and prints.
    """
    print(json.dumps(json_queries, indent=2))


def wiki_quote(page_name):
    """
    Transform into valid wiki URI.
    """
    return quote(page_name.replace(" ", "_"))


def links_to_find(target_links, target_langs=None):
    if target_langs is None:
        target_langs = DEFAULT_LANGS

    to_find = {}
    for link in target_links:
        # If it's a link, extract lang and name
        if "wikipedia.org" in link:
            lang, name = extract_lang_name(link)
            if lang not in to_find:
                to_find[lang] = set()
            to_find[lang].add(name)
        # Else, we assume it's directly a name, and try to find it
        else:
            if "*" not in to_find:
                to_find["*"] = set()
            to_find["*"].add(link)

    # Each name without a lang will be tracked down using target langs
    for name in to_find["*"]:
        for lang in target_langs:
            if lang not in to_find:
                to_find[lang] = set()
            to_find[lang].add(name)

    del to_find["*"]

    if VERBOSE:
        pprint(to_find)

    return to_find


def fetch_data(to_find, target_langs=None):
    # Check if the page exists, gather information if it does
    # https://www.mediawiki.org/wiki/API:Info
    # https://www.mediawiki.org/wiki/API:Langlinks
    if target_langs is None:
        target_langs = DEFAULT_LANGS

    queries = {}
    for lang, names in to_find.items():
        url_full = URL_INFOS.format(lang=lang)
        # We group the queries per target lang for less queries
        titles = "|".join(names)
        params = {
            "titles": titles,
            "prop": "info|langlinks",
            "lllimit": WIKI_LIMIT,  # We want all langs in order to find our target langs
        }

        results = s.get(url=url_full, params=params)
        data = results.json()

        if "query" in data and "pages" in data["query"]:
            data = data["query"]["pages"]

        for pid, obj in data.items():
            title = obj["title"]

            # Will only keep the latest successful query for same name pages
            queries[title] = {
                "query": {
                    "lang": lang,
                }
            }

            # Page was not found with that language
            if int(pid) < 0:
                queries[title]["error"] = "not found"
                continue

            queries[title]["query"].update({
                "pid": int(pid),
                "timestamp": datetime.datetime.today().isoformat(),
                "duration": TARGET_DURATION,
            })

            # Add the query language in the list of langs
            queries[title]["langs"] = {
                lang: {
                    "name": title,
                }
            }

            # Add the other target langs
            if "langlinks" in obj:
                for langlink in obj["langlinks"]:
                    if not target_langs or langlink["lang"] in target_langs:  # Use all langs if no target lang
                        queries[title]["langs"][langlink["lang"]] = {
                            "name": langlink["*"]
                        }

    if VERBOSE:
        qprint(queries)

    # Merge linked pages with different names
    # We assume here that pages are correctly linked (by Wikipedia) between each other
    next_queries = {}
    for name, obj in queries.items():
        if "error" in obj:
            next_queries[name] = obj
            continue

        skip = False
        for _, page in obj["langs"].items():
            if page["name"] in next_queries.keys():
                skip = True
                break

        if not skip:
            next_queries[name] = obj
    queries = next_queries

    if VERBOSE:
        qprint(queries)

    return queries


def fetch_backlinks(queries):
    # Find the backlinks for each
    # For important pages (looking at you, "École polytechnique fédérale de Lausanne"), can take some time!
    # Set BACKLINKS_LIMIT to control that.
    # https://www.mediawiki.org/wiki/API:Backlinks
    for name, obj in queries.items():
        if "error" in obj:
            continue

        for lang, page in obj["langs"].items():
            blcontinue = ""
            blcounter = 0
            url_full = URL_INFOS.format(lang=lang)

            while blcounter < BACKLINKS_LIMIT:
                params = {
                    "list": "backlinks",
                    "bltitle": page["name"],
                    "bllimit": min(BACKLINKS_LIMIT, WIKI_LIMIT),
                }
                if blcontinue != "":
                    params["blcontinue"] = blcontinue

                results = s.get(url=url_full, params=params)
                data = results.json()

                if "query" in data and "backlinks" in data["query"]:
                    bldata = data["query"]["backlinks"]
                else:
                    obj["error"] = "could not retrieve informations (backlinks)"
                    break

                if "backlinks" not in page:
                    page["backlinks"] = set()  # This is to delete doubles

                if bldata:
                    for backlink in bldata:
                        page["backlinks"].add(backlink["title"])
                        blcounter += 1

                if "continue" in data:
                    blcontinue = data["continue"]["blcontinue"]
                else:
                    break

            if "backlinks" in page and isinstance(page["backlinks"], set):
                page["backlinks"] = list(page["backlinks"])  # Sets are not valid JSON objects, lists are

    if VERBOSE:
        qprint(queries)

    return queries


def fetch_pageprops_revisions(queries):
    # Get some of the missing informations
    # https://www.mediawiki.org/wiki/API:Pageprops
    # https://www.mediawiki.org/wiki/API:Revisions
    for name, obj in queries.items():
        if "error" in obj:
            continue

        for lang, page in obj["langs"].items():
            url_full = URL_INFOS.format(lang=lang)
            params = {
                "titles": page["name"],
                "prop": "pageprops|revisions",
                "rvlimit": 1,
                "rvprop": "timestamp|user",
                "rvdir": "newer",
            }

            results = s.get(url=url_full, params=params)
            data = results.json()

            if "query" in data and "pages" in data["query"]:
                content = data["query"]["pages"]
                pid = next(iter(content))
                page["pid"] = int(pid)
                content = content[pid]
                page["pwikidata"] = content["pageprops"]["wikibase_item"]
                page["creation"] = {
                    "timestamp": content["revisions"][0]["timestamp"],
                    "user": content["revisions"][0]["user"],
                }
            else:
                obj["error"] = "could not retrieve informations (props)"

    if VERBOSE:
        qprint(queries)

    return queries


def fetch_contributors(queries, target_contributors=None):
    # Contributors
    # https://www.mediawiki.org/wiki/API:Contributors
    for name, obj in queries.items():
        if "error" in obj:
            continue

        for lang, page in obj["langs"].items():
            pccontinue = ""
            pccounter = 0
            url_full = URL_INFOS.format(lang=lang)
            params = {
                "titles": page["name"],
                "prop": "contributors",
                "pclimit": min(CONTRIBS_LIMIT, WIKI_LIMIT),
            }

            while pccounter < CONTRIBS_LIMIT:
                if pccontinue != "":
                    params["pccontinue"] = pccontinue

                results = s.get(url=url_full, params=params)
                data = results.json()

                if "query" in data and "pages" in data["query"]:
                    pcdata = data["query"]["pages"][str(page["pid"])]
                else:
                    obj["error"] = "could not retrieve informations (contributors)"
                    break

                if "contributors" not in page:
                    page["contributors"] = set()  # Data should already be a set, but I'm being cautious

                if pcdata:
                    page["contributors"].update(
                        [
                            contributor["name"]
                            for contributor in pcdata["contributors"]
                            if not target_contributors or contributor["name"] in target_contributors
                            # Use all contributors if no target contributors are specified
                        ]
                    )
                    pccounter += len(pcdata["contributors"])

                if "continue" in data:
                    pccontinue = data["continue"]["pccontinue"]
                else:
                    break

            if "contributors" in page and isinstance(page["contributors"], set):
                page["contributors"] = list(page["contributors"])  # Sets are not valid JSON objects, lists are

    if VERBOSE:
        qprint(queries)

    return queries


def fetch_contributions(queries):
    # Contributions
    # https://www.mediawiki.org/wiki/API:Revisions
    for name, obj in queries.items():
        if "error" in obj:
            continue

        for lang, page in obj["langs"].items():
            rvcontinue = ""
            url_full = URL_INFOS.format(lang=lang)
            params = {
                "titles": page["name"],
                "prop": "revisions",
                "rvprop": "timestamp|user|size",
                "rvstart": obj["query"]["timestamp"],
                "rvend": (datetime.datetime.fromisoformat(obj["query"]["timestamp"]) - datetime.timedelta(
                    days=obj["query"]["duration"])).isoformat(),
                "rvdir": "older",  # rvstart has to be later than rvend with that mode
                "rvlimit": WIKI_LIMIT,
            }

            while True:
                if rvcontinue != "":
                    params["rvcontinue"] = rvcontinue

                results = s.get(url=url_full, params=params)
                data = results.json()

                if "query" in data and \
                        "pages" in data["query"] and "revisions" in data["query"]["pages"][str(page["pid"])]:
                    rvdata = data["query"]["pages"][str(page["pid"])]["revisions"]
                else:
                    obj["error"] = "could not retrieve informations (contributions)"
                    break

                if "contributions" not in page:
                    page["contributions"] = {
                        "items": [],
                    }

                if rvdata:
                    for revision in rvdata:
                        page["contributions"]["items"].append({
                            "timestamp": revision["timestamp"],
                            "username": revision["user"],
                            "size": revision["size"],
                        })

                if "continue" in data:
                    rvcontinue = data["continue"]["rvcontinue"]
                else:
                    break

    if VERBOSE:
        qprint(queries)

    return queries


def fetch_pageviews(queries):
    # Pageviews
    # https://wikimedia.org/api/rest_v1/#/Pageviews%20data/get_metrics_pageviews_per_article__project___access___agent___article___granularity___start___end_
    for name, obj in queries.items():
        if "error" in obj:
            continue

        for lang, page in obj["langs"].items():
            url_full = URL_STATS.format(
                lang=lang,
                access=ACCESS,
                agent=AGENTS,
                uri_article_name=wiki_quote(page["name"]),
                granularity=GRANULARITY,
                start=(datetime.datetime.fromisoformat(obj["query"]["timestamp"]) - datetime.timedelta(
                    days=obj["query"]["duration"])).strftime('%Y%m%d00'),
                end=datetime.datetime.fromisoformat(obj["query"]["timestamp"]).strftime('%Y%m%d00'),
            )

            results = s.get(url=url_full)
            data = results.json()

            if "items" in data:
                if "pageviews" not in page:
                    page["pageviews"] = {
                        "granularity": GRANULARITY,
                        "access": ACCESS,
                        "agent": AGENTS,
                        "items": [],
                    }

                for item in data["items"]:
                    page["pageviews"]["items"].append({
                        "timestamp": datetime.datetime.strptime(item["timestamp"], "%Y%m%d%H").isoformat(),
                        "views": item["views"],
                    })
            else:
                obj["error"] = "could not retrieve informations (pageviews)"
                continue

    if VERBOSE:
        qprint(queries)

    return queries


def get_from_wikipedia(target_links, target_langs=None, target_contributors=None):
    if target_langs is None:
        target_langs = DEFAULT_LANGS

    to_find = links_to_find(target_links, target_langs)
    queries = fetch_data(to_find, target_langs)
    fetch_backlinks(queries)
    fetch_pageprops_revisions(queries)
    fetch_contributors(queries, target_contributors)
    fetch_contributions(queries)
    fetch_pageviews(queries)

    return queries


def main():
    # Links are provided
    target_links = [
        "https://fr.wikipedia.org/wiki/Martin_Vetterli",
        "https://en.wikipedia.org/wiki/%C3%89cole_Polytechnique_F%C3%A9d%C3%A9rale_de_Lausanne",
        "https://en.wikipedia.org/wiki/Jean-Pierre_Hubaux",
        "https://it.wikipedia.org/wiki/Jean-Michel_LErreur",
        "https://fr.wikipedia.org/wiki/%C3%89cole_polytechnique_f%C3%A9d%C3%A9rale_de_Lausanne",
        "it.wikipedia.org/wiki/Jean-Michel_LErreur",
        "Michael_Grätzel",
        "Patrick Aebischer",
    ]

    # Chosen Langs
    target_langs = ["en", "fr", "de"]

    # Chosen contributors
    target_contributors = []

    # Length for the revisions, in days
    target_duration = DEFAULT_DURATION

    queries = get_from_wikipedia(target_links, target_langs, target_contributors)

    import json
    with open('results.json', 'w', encoding='utf-8') as f:
        json.dump(queries, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()