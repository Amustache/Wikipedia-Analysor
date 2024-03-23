from collections.abc import Iterable
from dataclasses import dataclass
import datetime


from textstat import textstat


@dataclass
class WikiPage:
    # Base parameters
    title: str
    lang: str
    pid: int = None  # Set later; negative = error
    description: str = None

    last_updated: datetime.datetime = datetime.datetime.today()
    errors: Iterable[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = list()

        self.langlinks = None
        self.backlinks = None
        self.contributors = None
        self.revisions = None
        self.pageassessments = None
        self.pwikidata = None
        self.creation = {
            "timestamp": None,
            "user": None,
        }
        self.pageviews = None
        self.extract = None
        self.stats = None
        self.readability = None

    def add_langs(self, langlinks: str | Iterable[str]):
        """
        self.langlinks is a set of language codes

        :param langlinks:
        :return: self
        """
        if not hasattr(self, "langlinks") or self.langlinks is None:
            self.langlinks = {self.lang}

        if isinstance(langlinks, str):
            langlinks = [langlinks]

        self.langlinks.update(langlinks)

        return self

    def add_backlinks(self, backlinks: str | Iterable[str]):
        """
        self.backlinks is a list of page titles

        :param backlinks:
        :return: self
        """
        if not hasattr(self, "backlinks") or self.backlinks is None:
            self.backlinks = set()

        if isinstance(backlinks, str):
            backlinks = [backlinks]

        self.backlinks.update(backlinks)

        return self

    def add_contributors(self, contributors: str | Iterable[str]):
        """
        self.contributors is a list of usernames

        :param contributors:
        :return: self
        """
        if not hasattr(self, "contributors") or self.contributors is None:
            self.contributors = set()

        if isinstance(contributors, str):
            contributors = [contributors]

        self.contributors.update(contributors)

        return self

    def add_revisions(self, revisions):
        """
        self.contributions is a list of revisions (= contributions)

        :param revisions:
        :return: self
        """
        if not hasattr(self, "revisions") or self.revisions is None:
            self.revisions = list()

        if isinstance(revisions, dict):
            revisions = [revisions]

        for revision in revisions:
            self.revisions.append(
                {
                    "revid": revision["revid"],
                    "parentid": revision["parentid"],
                    "timestamp": revision["timestamp"],
                    "username": revision["user"],
                    "size": revision["size"],
                }
            )

        return self

    def add_pageassessments(self, pageassessments):
        """
        self.pageassessments is a list of page assessments

        :param contributors:
        :return: self
        """
        if not hasattr(self, "pageassessments") or self.pageassessments is None:
            self.pageassessments = {}

        self.pageassessments.update(pageassessments)

        return self

    def make_text_stats(self):
        if self.extract is None or self.extract == "":
            raise AttributeError("No text to work with!")

        self.stats = {
            "num_words": textstat.lexicon_count(self.extract),
            "num_sentences": textstat.sentence_count(self.extract),
            "reading_time": textstat.reading_time(self.extract),
        }

        # Using textstat
        # Here, "min" means harder to read, while "max" means easier to read
        # "minimum readability" vs. "maximum readability"
        textstat.set_lang(self.lang)
        self.readability = {
            "fres": {
                "name": "Flesch Reading Ease Score",
                "link": "https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests#Flesch_reading_ease",
                "result": textstat.flesch_reading_ease(self.extract),
                "min": 0,
                "max": 100,
            }
        }

        if self.lang == "it":
            self.readability["it_gi"] = {
                "name": "Gulpease Index",
                "link": "https://it.wikipedia.org/wiki/Indice_Gulpease",
                "result": textstat.gulpease_index(self.extract),
                "min": 0,
                "max": 100,
            }

        if self.lang == "de":
            self.readability["de_ws"] = {
                "name": "Wiener Sachtextformel",
                "link": "https://de.wikipedia.org/wiki/Lesbarkeitsindex#Wiener_Sachtextformel",
                "result": textstat.wiener_sachtextformel(self.extract, 1),  # Magic number... What are the variants?
                "min": 15,
                "max": 4,
            }
