from typing import Dict, Optional, List, Any, Set, TYPE_CHECKING, Tuple

from bxutils import logging

from bxcommon.feed.feed import Feed, FeedKey
from bxcommon.feed.subscriber import Subscriber

if TYPE_CHECKING:
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)


class FeedManager:
    feeds: Dict[FeedKey, Feed]
    accounts: Dict[str, Dict[int, int]]
    _node: "AbstractNode"

    def __init__(self, node: "AbstractNode") -> None:
        self.feeds = {}
        self.accounts = {}
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

    def subscribe_to_feed(self, feed_key: FeedKey, options: Dict[str, Any]) -> Optional[Subscriber]:
        if feed_key in self.feeds:
            subscriber = self.feeds[feed_key].subscribe(options)
            logger.debug(
                "Creating new subscriber ({}) to {}", subscriber.subscription_id, feed_key
            )
            self._node.reevaluate_transaction_streamer_connection()
            account_id = options.get("account_id", None)
            if account_id is not None:
                if account_id in self.accounts:
                    open_feeds = self.accounts.get(account_id)
                    assert open_feeds is not None
                    if feed_key.network_num in open_feeds:
                        open_feeds[feed_key.network_num] += 1
                    else:
                        open_feeds[feed_key.network_num] = 1
                else:
                    self.accounts[account_id] = {feed_key.network_num: 1}
            return subscriber
        else:
            return None

    def unsubscribe_from_feed(
        self,
        feed_key: FeedKey,
        subscriber_id: str,
        account_id: Optional[str] = None
    ) -> Optional[Subscriber]:
        subscriber = self.feeds[feed_key].unsubscribe(subscriber_id)
        if subscriber is not None:
            logger.debug(
                "Unsubscribing subscriber ({}) from {}",
                subscriber.subscription_id,
                feed_key,
            )

            # Subtract the feed from the account counting
            if account_id is not None:
                if account_id in self.accounts:
                    open_feeds = self.accounts.get(account_id)
                    if open_feeds is not None and feed_key.network_num in open_feeds:
                        if open_feeds[feed_key.network_num] == 1:
                            open_feeds.pop(feed_key.network_num)
                            if len(open_feeds) == 0:
                                self.accounts.pop(account_id)
                        else:
                            open_feeds[feed_key.network_num] -= 1

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

    def open_feeds_count(self, account_id: str) -> Optional[Dict[int, int]]:
        return self.accounts.get(account_id, {})
