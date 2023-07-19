import time
from functools import reduce


def formated_date(timestamp: float) -> str:
    lc = time.localtime(timestamp)

    return f"{lc.tm_mday:02}.{lc.tm_mon:02}.{lc.tm_year:04}"


def formated_time(timestamp: float) -> str:
    lc = time.localtime(timestamp)

    return f"{lc.tm_hour:02}:{lc.tm_min:02}:{lc.tm_sec:02}"


def formated_duration(seconds: float, short=False) -> str:
    s = int(seconds % 60)

    minutes = (seconds - s) / 60
    m = int(minutes % 60)

    hours = (minutes - m) / 60
    h = int(hours % 24)

    days = (hours - h) / 24
    d = int(days)

    if short:
        return f"{(d * 24 + h)}:{m:02}.{s:02}"
    return f"{d} days, {h:02} hours, {m:02} minutes and {s:02} seconds"


def list_flatt(lst: list, recursive=False) -> list:
    if not lst:
        return lst
    if not any(map(lambda l: isinstance(l, list), lst)):
        return lst

    if recursive:
        return list_flatt(reduce(lambda a, b: a + b, map(lambda l: l if isinstance(l, list) else [l], lst), []), True)
    return reduce(lambda a, b: a + b, map(lambda l: l if isinstance(l, list) else [l], lst), [])


def list_str(lst: list) -> str:
    if not lst:
        return ""
    return ", ".join(map(lambda l: str(l), lst))
