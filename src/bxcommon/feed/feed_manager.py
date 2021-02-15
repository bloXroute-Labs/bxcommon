from typing import Dict, Optional, List, Any, Set, TYPE_CHECKING, Tuple

from bxutils import logging

from bxcommon.feed.feed import Feed, FeedKey
from bxcommon.feed.subscriber import Subscriber

if TYPE_CHECKING:
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)


class FeedManager:
    feeds: Dict[FeedKey, Feed]
    _node: "AbstractNode"

    def __init__(self, node: "AbstractNode") -> None:
        self.feeds = {}
        self._node = node

    def __contains__(self, item):
        if isinstance(item, FeedKey):
            return item in self.feeds
        else:
            return FeedKey(item) in self.feeds

    def register_feed(self, feed: Feed) -> None:
        if feed.feed_key in self.feeds:
            raise ValueError(
                f"Cannot register two feeds with the same name: {feed.name}"
            )
        self.feeds[feed.feed_key] = feed

    def subscribe_to_feed(
        self, feed_key: FeedKey, options: Dict[str, Any]
    ) -> Optional[Subscriber]:
        if feed_key in self.feeds:
            subscriber = self.feeds[feed_key].subscribe(options)
            logger.debug(
                "Creating new subscriber ({}) to {}", subscriber.subscription_id, feed_key.name
            )
            self._node.reevaluate_transaction_streamer_connection()
            return subscriber
        else:
            return None

    def unsubscribe_from_feed(
        self, feed_key: FeedKey, subscriber_id: str
    ) -> Optional[Subscriber]:
        subscriber = self.feeds[feed_key].unsubscribe(subscriber_id)
        if subscriber is not None:
            logger.debug(
                "Unsubscribing subscriber ({}) from {}",
                subscriber.subscription_id,
                feed_key.name,
            )
        self._node.reevaluate_transaction_streamer_connection()
        return subscriber

    def publish_to_feed(self, feed_key: FeedKey, message: Any) -> None:
        if feed_key in self.feeds:
            self.feeds[feed_key].publish(message)

    def get_feed_fields(self, feed_key: FeedKey) -> List[str]:
        return self.feeds[feed_key].FIELDS

    def get_feed(self, feed_key: FeedKey):
        return self.feeds.get(feed_key)

    def get_feed_keys(self, network_num: int = 0) -> List[FeedKey]:
        return [key for key in self.feeds if key.network_num == network_num]

    def any_subscribers(self) -> bool:
        return any(feed.subscriber_count() > 0 for feed in self.feeds.values())

    def get_valid_feed_filters(self, feed_key: FeedKey) -> Set[str]:
        return self.feeds[feed_key].FILTERS

    def validate_feed_filters(self, feed_key: FeedKey, filters: str) -> Tuple[str, List[str]]:
        return self.feeds[feed_key].validate_filters(filters)
