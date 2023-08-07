# Incorporate data
import json


def get_data():
    try:
        with open("./webapp/samples/results.json", "r", encoding='utf8') as f:
            DATA = json.load(f)
            PEOPLE = list(DATA.keys())
    except:
        DATA, PEOPLE = None, None
    return DATA, PEOPLE
