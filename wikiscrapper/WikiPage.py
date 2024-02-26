import datetime
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class WikiPage:
    title: str
    lang: str
    pid: int = None  # Set later; negative = error
    description: str = None

    errors: Iterable[str] = None
    last_updated: datetime.datetime = datetime.datetime.today()

    def __post_init__(self):
        self.langlinks = None
        self.backlinks = None
        self.contributors = None
        self.revisions = None

    def add_langs(self, langlinks: str | Iterable[str]):
        """
        self.langlinks is a set of language codes
        """
        if not hasattr(self, "langlinks") or self.langlinks is None:
            self.langlinks = {self.lang}

        if isinstance(langlinks, str):
            langlinks = [langlinks]

        self.langlinks.update(langlinks)

    def add_backlinks(self, backlinks: str | Iterable[str]):
        """
        self.backlinks is a list of page titles
        """
        if not hasattr(self, "backlinks") or self.backlinks is None:
            self.backlinks = set()

        if isinstance(backlinks, str):
            backlinks = [backlinks]

        self.backlinks.update(backlinks)

    def add_contributors(self, contributors: str | Iterable[str]):
        """
        self.contributors is a list of usernames
        """
        if not hasattr(self, "contributors") or self.contributors is None:
            self.contributors = set()

        if isinstance(contributors, str):
            contributors = [contributors]

        self.contributors.update(contributors)

    def add_revisions(self, revisions):
        """
        self.contributions is a list of revisions (= contributions)
        """
        if not hasattr(self, "revisions") or self.revisions is None:
            self.revisions = list()

        if isinstance(revisions, dict):
            revisions = [revisions]

        for revision in revisions:
            self.revisions.append({
                "revid": revision["revid"],
                "parentid": revision["parentid"],
                "timestamp": revision["timestamp"],
                "username": revision["user"],
                "size": revision["size"],
            })

    def add