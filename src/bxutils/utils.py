import time
from datetime import datetime, timedelta
from datetime import time as dttime
from typing import TypeVar, Optional, Callable, Any

from bxutils import constants

T = TypeVar("T")
R = TypeVar("R")


def fibonacci(sequence_number: int) -> int:
    return int((constants.FIBONACCI_GOLDEN_RATIO ** sequence_number - (1 - constants.FIBONACCI_GOLDEN_RATIO) ** sequence_number) / 5 ** .5)


def optional_map(val: Optional[T], mapper: Callable[[T], R]) -> Optional[R]:
    if val is None:
        return val
    else:
        return mapper(val)


def or_else(val: Optional[T], default: T) -> T:
    if val is None:
        return default
    else:
        return val


def identity(val: T) -> T:
    return val


def time_to_date_str(epoch_time: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time))


def seconds_until_eod() -> float:
    dt = datetime.now()
    tomorrow = dt + timedelta(days=1)
    timedelta_until_eod = datetime.combine(tomorrow, dttime.min) - dt
    return timedelta_until_eod.total_seconds()


def memoize(fn: Callable) -> Callable:
    cache = {}

    async def memo_fn(*args):
        if args not in cache:
            cache[args] = await fn(*args)
        return cache[args]

    return memo_fn


class LazyBind:
    def __init__(self) -> None:
        self.bound_fn: Optional[Callable[..., Any]] = None

    def bind(self, bound_fn: Callable[..., Any]) -> None:
        self.bound_fn = bound_fn

    def call(self, *args, **kwargs) -> Any:
        bound_fn = self.bound_fn
        assert bound_fn is not None
        return bound_fn(*args, **kwargs)


def is_greater_or_eq_version(version1: str, version2: str) -> bool:
    """
    :param version1: version number ex) "v1.61.13"
    :param version2: version number ex) "v1.61.12"
    :return: True if version1 >= version2 else False
    """
    v1_list = [int(x) for x in version1.strip("v").split(".")]
    v2_list = [int(x) for x in version2.strip("v").split(".")]
    for i in range(min(len(v1_list), len(v2_list))):
        if v1_list[i] > v2_list[i]:
            return True
        elif v1_list[i] < v2_list[i]:
            return False
    return True


def safe_divide(value1: float, value2: float) -> float:
    if value2 == 0:
        return 0

    return value1 / value2


def bind_range(min_value: float, max_value: float, value: float) -> float:
    return min(max_value, max(min_value, value))
