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

    def add_langs(self, langlinks: str | Iterable[str]):
        if not hasattr(self, "langs"):
            self.__setattr__("langlinks", {self.lang})

        if isinstance(langlinks, str):
            langs = [langlinks]

        self.langlinks.update(langs)

    def add_backlinks(self, backlinks: str | Iterable[str]):
        if not hasattr(self, "backlinks"):
            self.__setattr__("backlinks", set())

        if isinstance(backlinks, str):
            backlinks = [backlinks]

        self.backlinks.update(backlinks)

    def add_contributors(self, contributors: str | Iterable[str]):
        if not hasattr(self, "contributors"):
            self.__setattr__("contributors", set())

        if isinstance(contributors, str):
            contributors = [contributors]

        self.backlinks.update(contributors)

    def add_contributions(self, contributions: dict):
        if not hasattr(self, "contributions"):
            self.__setattr__("contributions", {"items": []})

        for contribution in contributions:
            pass
