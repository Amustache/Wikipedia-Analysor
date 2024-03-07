from wikiscrapper.helpers import URL_INFOS


def fetch_pageassessments(wikipage, session):
    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "pageassessments",
    }

    results = session.get(url=url_full, params=params)
    data = results.json()

    if "query" in data and "pages" in data["query"] and "pageassessments" in data["query"]["pages"][wikipage.pid]:
        wikipage.add_pageassessments(data["query"]["pages"][wikipage.pid]["pageassessments"])


FETCHERS = [
    fetch_pageassessments,
]
