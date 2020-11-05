import functools


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        return func(*args, **kwargs)
    return new_func
