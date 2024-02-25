from wikiscrapper.WikiPage import WikiPage
from wikiscrapper.WikiQuery import WikiQuery

truc = {1, 2, 3}
test = WikiQuery("Bonjour")
print(test)
print(test.links_to_find)
test.add_targets("https://en.wikipedia.org/wiki/H._P._Lovecraft")
test.add_targets(["Martin Vetterli", "Philippe Moris", "Bonjour"])
print(test)
print(test.links_to_find)
test.add_langs("it")
print(test)
print(test.links_to_find)

truc = WikiPage("Martin Vetterli", "fr", 42)
print(truc.langs)
