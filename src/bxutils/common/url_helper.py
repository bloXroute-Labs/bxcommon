import urllib.parse

DELIMITER = "/"


def append_suffix_if_needed(url: str) -> str:
    if url.endswith(DELIMITER):
        return url
    else:
        return "{}{}".format(url, DELIMITER)


def url_join(base: str, path: str, *extra: str) -> str:
    url = base
    sub_paths = [path, *extra]
    for sub_path in sub_paths:
        url = urllib.parse.urljoin(append_suffix_if_needed(url), sub_path)
    return url
