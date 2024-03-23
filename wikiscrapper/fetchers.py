import datetime


from wikiscrapper.helpers import DEFAULT_DURATION, GLOBAL_LIMIT, URL_INFOS, wiki_quote


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


def fetch_backlinks(wikipage, session):
    """
    Fetcher for `backlinks`.
    """
    blcontinue = ""
    blcounter = 0
    url_full = URL_INFOS.format(lang=wikipage.lang)

    while blcounter < GLOBAL_LIMIT:
        params = {
            "list": "backlinks",
            "bltitle": wikipage.title,
            "bllimit": GLOBAL_LIMIT,
        }
        if blcontinue != "":
            params["blcontinue"] = blcontinue

        results = session.get(url=url_full, params=params)
        data = results.json()

        if "query" in data and "backlinks" in data["query"]:
            bldata = data["query"]["backlinks"]
        else:
            wikipage.errors.append("Could not retrieve information (backlinks)")
            break

        if bldata:
            wikipage.add_backlinks(bldata)
            blcounter += len(bldata)

        if "continue" in data:
            blcontinue = data["continue"]["blcontinue"]
        else:
            break


def fetch_more_infos(wikipage, session):
    """
    Fetcher for `pwikidata`, `creation`.
    """
    pid = str(wikipage.pid)

    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "pageprops|revisions",
        "rvlimit": 1,
        "rvprop": "timestamp|user",
        "rvdir": "newer",
    }

    results = session.get(url=url_full, params=params)
    data = results.json()

    if "query" in data and "pages" in data["query"]:
        content = data["query"]["pages"][pid]
        if "pageprops" in content and "wikibase_item" in content["pageprops"]:
            wikipage.pwikidata = content["pageprops"]["wikibase_item"]
        else:
            wikipage.pwikidata = -1

        wikipage.creation["timestamp"] = content["revisions"][0]["timestamp"]
        wikipage.creation["user"] = content["revisions"][0]["user"]
    else:
        wikipage.error.append("Could not retrieve information (props)")


def fetch_contributors(wikipage, session):
    """
    Fetcher for `contributors`
    """
    pid = str(wikipage.pid)

    pccontinue = ""
    pccounter = 0
    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "contributors",
        "pclimit": GLOBAL_LIMIT,
    }

    while pccounter < GLOBAL_LIMIT:
        if pccontinue != "":
            params["pccontinue"] = pccontinue

        results = session.get(url=url_full, params=params)
        data = results.json()

        if "query" in data and "pages" in data["query"]:
            pcdata = data["query"]["pages"][pid]
        else:
            wikipage.errors.append("Could not retrieve information (contributors)")
            break

        if pcdata:
            wikipage.add_contributors(pcdata["contributors"])
            pccounter += len(pcdata["contributors"])

        if "continue" in data:
            pccontinue = data["continue"]["pccontinue"]
        else:
            break


def fetch_revisions(wikipage, session):
    """
    Fetcher for `revisions`.
    """
    pid = str(wikipage.pid)

    rvcontinue = ""
    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "revisions",
        "rvprop": "ids|timestamp|user|size",
        "rvstart": wikipage.creation["timestamp"],
        "rvend": (wikipage.last_updated - datetime.timedelta(days=DEFAULT_DURATION)).isoformat(),
        "rvdir": "older",  # rvstart has to be later than rvend with that mode
        "rvlimit": GLOBAL_LIMIT,
    }

    while True:
        if rvcontinue != "":
            params["rvcontinue"] = rvcontinue

        results = session.get(url=url_full, params=params)
        data = results.json()

        if "query" in data and "pages" in data["query"] and "revisions" in data["query"]["pages"][pid]:
            rvdata = data["query"]["pages"][pid]["revisions"]
        else:
            wikipage.errors.append("Could not retrieve information (contributions)")
            break

        if rvdata:
            wikipage.add_revisions(rvdata)

        if "continue" in data:
            rvcontinue = data["continue"]["rvcontinue"]
        else:
            break


def fetch_pageviews(wikipage, session):
    return
    raise NotImplementedError


def fetch_text(wikipage, session):
    """
    Fetcher for the whole text.
    """
    pid = str(wikipage.pid)

    excontinue = ""
    url_full = URL_INFOS.format(lang=wikipage.lang)
    params = {
        "titles": wikipage.title,
        "prop": "extracts",
        "explaintext": 1,
        "exsectionformat": "plain",
    }

    while True:
        if excontinue != "":
            params["excontinue"] = excontinue

        results = session.get(url=url_full, params=params)
        data = results.json()

        if "query" in data and "pages" in data["query"] and "extract" in data["query"]["pages"][pid]:
            exdata = data["query"]["pages"][pid]["extract"]
        else:
            wikipage.errors.append("Could not retrieve information (extract)")
            break

        if wikipage.extract is None:
            wikipage.extract = ""

        if exdata:
            wikipage.extract += exdata

        if "continue" in data:
            excontinue = data["continue"]["excontinue"]
        else:
            break

    wikipage.make_text_stats()


FETCHERS = [
    fetch_base_info,
    fetch_backlinks,
    fetch_pageassessments,
    fetch_more_infos,
    fetch_contributors,
    fetch_revisions,
    fetch_pageviews,
    fetch_text,
]
