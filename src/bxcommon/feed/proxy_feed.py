from typing import Any, List, Set, Dict

from bxcommon import constants
from bxcommon.feed.feed import Feed

from bxutils import logging

logger = logging.get_logger(__name__)


class ProxyFeed(Feed[Dict[str, Any], Dict[str, Any]]):

    def __init__(
        self,
        name: str,
        fields: List,
        # pyre-fixme[11]: Annotation `Set` is not defined as a type.
        filters: Set,
        network_num: int = constants.ALL_NETWORK_NUM,
    ) -> None:
        # pylint: disable=invalid-name
        self.NAME = name
        self.FIELDS = fields
        self.FILTERS = filters

        super().__init__(self.NAME, network_num)

    def serialize(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        return raw_message
