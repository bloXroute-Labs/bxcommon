from typing import Callable, Dict
import pycond as pc
from bxutils import logging

logger = logging.get_logger(__name__)


pc.ops_use_symbolic_and_txt(allow_single_eq=True)


def get_validator(filter_string: str) -> Callable[[Dict], bool]:
    logger.debug("Getting validator for filters {}", filter_string)
    return pc.qualify(filter_string, brkts="()", add_cached=True)
