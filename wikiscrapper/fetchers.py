from wikiscrapper.helpers import URL_INFOS, wiki_quote


def fetch_base_info(wikipage, session):
    """
    Fetcher for `pid`, `description`.
    """
    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "info",
    }

    results = session.get(url=url_full, params=params)
    data = results.json()

    if "query" in data and "pages" in data["query"]:
        wikipage.pid = int(next(iter(data["query"]["pages"])))  # Only one element

        if wikipage.pid < 0:
            raise AttributeError("PID should not be negative.")

    # Get the short description
    data = session.get(
        url=f"https://{wikipage.lang}.wikipedia.org/api/rest_v1/page/summary/{wiki_quote(wikipage.title)}?redirect=true"
    ).json()
    if "description" in data:
        wikipage.description = data["description"]
    else:
        wikipage.description = "(no description found)"


def fetch_pageassessments(wikipage, session):
    """
    Fetcher for `pageassessments`.
    """
    pid = str(wikipage.pid)

    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "pageassessments",
    }

    results = session.get(url=url_full, params=params)
    data = results.json()

    if "query" in data and "pages" in data["query"] and "pageassessments" in data["query"]["pages"][pid]:
        wikipage.add_pageassessments(data["query"]["pages"][pid]["pageassessments"])


FETCHERS = [
    fetch_base_info,
    fetch_pageassessments,
]
