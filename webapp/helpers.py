import hashlib

LANGS = {
    "fr": "Français",
    "en": "English",
    "de": "Deutsch",
    "it": "Italiano"
}


# https://stackoverflow.com/a/1094933
def sizeof_fmt(num, suffix="B", sign=False):
    if abs(num) < 1024.0:
        return f"{int(num):+}{suffix}" if sign else f"{int(num)}{suffix}"
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:+3.1f}{unit}{suffix}" if sign else f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:+.1f}Yi{suffix}" if sign else f"{num:.1f}Yi{suffix}"


def get_color(lang):
    m = hashlib.sha256()
    m.update(lang.encode())
    return f"#{m.hexdigest()[:6]}"


def map_score(value, min_value, max_value, min_score=1, max_score=6):
    """
    Map a value from a range to another range.

    :param value:
    :param min_value:
    :param max_value:
    :param min_score:
    :param max_score:
    :return:
    """
    span_value = max_value - min_value
    span_score = max_score - min_score
    scaled_value = float(value - min_value) / float(span_value)
    return min_score + (scaled_value * span_score)