from typing import Callable, Dict, List
import pycond as pc
from bxutils import logging

logger = logging.get_logger(__name__)


pc.ops_use_symbolic_and_txt(allow_single_eq=True)


def get_validator(filter_string: str) -> Callable[[Dict], bool]:
    logger.trace("Getting validator for filters {}", filter_string)
    res = pc.qualify(filter_string.lower(), brkts="()", add_cached=True)
    return res


def get_keys(filter_string: str) -> List[str]:
    logger.trace("Getting keys for filters {}", filter_string)
    _, nfos = pc.parse_cond(filter_string.lower(), brkts="()", add_cached=True)
    return nfos["keys"]
