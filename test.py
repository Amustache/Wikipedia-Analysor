from pprint import pprint
import random
import string
import unittest


from wikiscrapper.helpers import DEFAULT_LANGS, Verbose
from wikiscrapper.WikiPage import WikiPage
from wikiscrapper.WikiQuery import WikiQuery


def randomword(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


TEST_MULTIPLE_PAGES = [
    "https://en.wikipedia.org/wiki/Linked_data",
    "https://fr.wikipedia.org/wiki/%C3%89cole_polytechnique_f%C3%A9d%C3%A9rale_de_Lausanne",
    "https://en.wikipedia.org/wiki/%C3%89cole_polytechnique_f%C3%A9d%C3%A9rale_de_Lausanne",
    "Voynich manuscript",
    "https://als.wikipedia.org/wiki/Elsass",
    "https://fr.wikipedia.org/wiki/Lisp",
    "Thsi sis ian error lol",
    "https://it.wikipedia.org/wiki/tHIds is also cna errorr hahah",
]

TEST_ONE_PAGE = "https://de.wikipedia.org/wiki/H._P._Lovecraft"

TEST_TOTAL_PAGES = TEST_MULTIPLE_PAGES.copy()
TEST_TOTAL_PAGES.append(TEST_ONE_PAGE)

TEST_EXPECTED_TOTAL = {
    "de": {
        "Voynich manuscript",
        "Thsi sis ian error lol",
        "H._P._Lovecraft",
    },
    "en": {
        "Linked_data",
        "École_polytechnique_fédérale_de_Lausanne",
        "Voynich manuscript",
        "Thsi sis ian error lol",
    },
    "fr": {
        "École_polytechnique_fédérale_de_Lausanne",
        "Voynich manuscript",
        "Lisp",
        "Thsi sis ian error lol",
    },
    "als": {"Elsass"},
    "it": {
        "tHIds is also cna errorr hahah",
    },
}


class TestQuery(unittest.TestCase):
    def test_query_empty(self):
        query = WikiQuery()

        self.assertIsInstance(query.targets, set)
        self.assertEqual(len(query.targets), 0)

        self.assertIsInstance(query.target_langs, set)
        self.assertEqual(query.target_langs, set(DEFAULT_LANGS))

        self.assertIsInstance(query.results, dict)
        self.assertEqual(len(query.results), 0)

        self.assertIsInstance(query.links_to_find, dict)
        self.assertEqual(len(query.links_to_find), 0)

    def test_query_simple(self):
        pages = [randomword(random.randint(1, 32)) for i in range(random.randint(1, 16))]

        query = WikiQuery(pages)

        self.assertIsInstance(query.targets, set)
        self.assertEqual(len(query.targets), len(pages))

        self.assertIsInstance(query.results, dict)
        self.assertEqual(len(query.results), 0)

        self.assertIsInstance(query.links_to_find, dict)
        self.assertEqual(len(query.links_to_find), len(DEFAULT_LANGS))

        for _, links_to_find in query.links_to_find.items():
            self.assertEqual(links_to_find, set(pages))

    def test_query_add_links(self):
        query = WikiQuery()
        query.add_targets(TEST_MULTIPLE_PAGES)
        query.add_targets(TEST_ONE_PAGE)

        self.assertEqual(query.targets, set(TEST_TOTAL_PAGES))
        self.assertEqual(query.links_to_find, TEST_EXPECTED_TOTAL)

        query.add_targets(TEST_ONE_PAGE)
        self.assertEqual(query.targets, set(TEST_TOTAL_PAGES))
        self.assertEqual(query.links_to_find, TEST_EXPECTED_TOTAL)

    def test_query_add_langs(self):
        query = WikiQuery(target_langs="fr")
        self.assertEqual(len(query.target_langs), 1)

        query.add_langs("en")
        self.assertEqual(len(query.target_langs), 2)

        query.add_langs(["de", "it"])
        self.assertEqual(len(query.target_langs), 4)
        self.assertEqual(query.target_langs, {"de", "en", "fr", "it"})

        query.add_langs("en")
        self.assertEqual(len(query.target_langs), 4)
        self.assertEqual(query.target_langs, {"de", "en", "fr", "it"})

    def test_verbose(self):
        query = WikiQuery(verbose=Verbose.TRACE)
        query.add_targets(TEST_MULTIPLE_PAGES)
        query.add_targets(TEST_ONE_PAGE)

        query.update()

        pprint(query)


if __name__ == "__main__":
    unittest.main()
