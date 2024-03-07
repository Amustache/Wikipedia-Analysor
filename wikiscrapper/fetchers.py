from wikiscrapper.helpers import URL_INFOS


def fetch_info(wikipage, session):
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


def fetch_pageassessments(wikipage, session):
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
    fetch_info,
    fetch_pageassessments,
]
