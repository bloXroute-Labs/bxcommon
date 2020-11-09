from typing import Any, List, Set, Dict

from bxcommon.feed.feed import Feed

from bxutils import logging

logger = logging.get_logger(__name__)


class ProxyFeed(Feed[Dict[str, Any], Dict[str, Any]]):

    def __init__(
        self,
        name: str,
        fields: List,
        # pyre-fixme[11]: Annotation `Set` is not defined as a type.
        filters: Set
    ) -> None:
        # pylint: disable=invalid-name
        self.NAME = name
        self.FIELDS = fields
        self.FILTERS = filters

        super().__init__(self.NAME)

    def serialize(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        return raw_message

    def publish(self, raw_message: Dict[str, Any]) -> None:
        logger.trace(
            "attempting to publish message: {} for feed {}", raw_message, self.name
        )

        if self.subscriber_count() == 0:
            return

        super(ProxyFeed, self).publish(raw_message)
