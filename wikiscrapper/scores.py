def normalise(value, in_min=1, in_max=100, out_min=1, out_max=100) -> int:
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def _score_language(langlinks: set) -> int:
    # Cf. https://en.wikipedia.org/wiki/Wikipedia:Multilingual_statistics
    top_langs = ["en", "de", "fr", "it"]  # Top languages on Wikipedia + Swiss, lower score
    score_top = 1
    score_not_top = 2

    # At least one language
    min_score = 1
    # https://en.wikipedia.org/wiki/Wikipedia:Wikipedia_articles_written_in_the_greatest_number_of_languages
    max_score = (score_not_top * (316 - len(top_langs))) + (score_top * len(top_langs))
    score = 0

    score += sum(1 for lang in langlinks if lang in top_langs)
    score += sum(2 for lang in langlinks if lang not in top_langs)

    return normalise(score, min, max)


def _score_contributors(contributors: list) -> int:
    # At least one contributor
    min_score = 1
    # https://en.wikipedia.org/wiki/Wikipedia:Wikipedians
    max_score = 125_000
    score = len(contributors)

    return normalise(score, min, max)


def _score_revisions(revisions: list) -> int:
    # At least one revision
    min_score = 1
    # https://en.wikipedia.org/wiki/Special:MostRevisions
    max_score = 50_000
    score = len(revisions)

    return normalise(score, min, max)


def _score_recent_revisions(revisions: list) -> int:
    return NotImplementedError
    min_score = 1
    max_score = 100
    score = 50


def _score_backlinks(revisions: list) -> int:
    return NotImplementedError
    min_score = 1
    max_score = 100
    score = 50

    return normalise(score, min, max)


def _score_pageviews(revisions: list) -> int:
    return NotImplementedError
    min_score = 1
    # https://en.wikipedia.org/wiki/Wikipedia:Popular_pages#Top-100_list
    max_score = 100
    score = 50

    return normalise(score, min, max)


def _score_pageassessments(pageassessments: list) -> int:
    return NotImplementedError
    min_score = 1
    #
    max_score = 100
    score = 50

    return normalise(score, min, max)


def _score_fres(fres: dict) -> int:
    min_score = fres["min"]
    max_score = fres["max"]
    score = fres["result"]

    return normalise(score, min, max)


def get_pop_score(wikipage) -> int:
    score = (
        _score_language(wikipage.langlinks)
        + _score_contributors(wikipage.contributors)
        + _score_revisions(wikipage.revisions)
        + _score_recent_revisions(wikipage.revisions)
        + _score_backlinks(wikipage.backlinks)
        + _score_pageviews(wikipage.pageviews)
    ) / 6

    return normalise(score)


def get_qual_score(wikipage) -> int:
    score = (
        _score_backlinks(wikipage.backlinks)
        + _score_revisions(wikipage.revisions)
        + _score_recent_revisions(wikipage.revisions)
        + _score_pageassessments(wikipage.pageassessments)
        + _score_fres(wikipage.readability["fres"])
    )

    return normalise(score)


def get_pri_score(wikipage) -> int:
    min_score = 1 / 100
    max_score = 100 / 1
    score = get_pop_score(wikipage) / get_qual_score(wikipage)

    return normalise(score, min_score, max_score)
