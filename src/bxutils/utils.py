import time
from typing import TypeVar, Optional, Callable, Any

T = TypeVar("T")
R = TypeVar("R")


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