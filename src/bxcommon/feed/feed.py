from abc import abstractmethod, ABCMeta
from asyncio import QueueFull

from typing import TypeVar, Generic, List, Dict, Optional, Any, Set, NamedTuple, Tuple

from bxcommon import log_messages, constants
from bxcommon.feed.subscriber import Subscriber
from bxcommon.feed import filter_parsing
from bxutils import logging

logger = logging.get_logger(__name__)
T = TypeVar("T")
S = TypeVar("S")


class FeedKey(NamedTuple):
    name: str
    network_num: int = 0


class Feed(Generic[T, S], metaclass=ABCMeta):
    FIELDS: List[str] = []
    FILTERS: Set[str] = set()
    ALL_FIELDS: List[str] = []
    name: str
    network_num: int
    subscribers: Dict[str, Subscriber[T]]
    feed_key: FeedKey

    def __init__(self, name: str, network_num: int = constants.ALL_NETWORK_NUM) -> None:
        self.name = name
        self.network_num = network_num
        self.subscribers = {}
        self.feed_key = FeedKey(name, network_num)

    def __repr__(self) -> str:
        return f"Feed<{self.name}>"

    def subscribe(self, options: Dict[str, Any]) -> Subscriber[T]:
        include_fields = options.get("include", "all")
        if include_fields == "all":
            options["include"] = self.ALL_FIELDS

        subscriber: Subscriber[T] = Subscriber(options)
        self.subscribers[subscriber.subscription_id] = subscriber
        return subscriber

    def unsubscribe(self, subscriber_id: str) -> Optional[Subscriber[T]]:
        return self.subscribers.pop(subscriber_id, None)

    def publish(self, raw_message: S) -> None:
        if self.subscriber_count() == 0:
            return

        try:
            serialized_message = self.serialize(raw_message)
        # pylint: disable=broad-except
        except Exception:
            logger.error(log_messages.COULD_NOT_SERIALIZE_FEED_ENTRY, exc_info=True)
            return

        bad_subscribers = []
        cached_subscription_items = {}
        for subscriber in self.subscribers.values():
            if subscriber.should_exit:
                logger.error(
                    log_messages.BAD_FEED_SUBSCRIBER_SHOULD_EXIT, subscriber.subscription_id, self
                )
                bad_subscribers.append(subscriber)
                continue
            if not self.should_publish_message_to_subscriber(
                subscriber, raw_message, serialized_message
            ):
                continue

            try:
                for cached_subscriber, cached_message in cached_subscription_items.items():
                    if subscriber.same_options(cached_subscriber):
                        subscriber.fast_queue(cached_message)
                        break
                else:
                    queued_message = subscriber.queue(serialized_message)
                    cached_subscription_items[subscriber] = queued_message
            except QueueFull:
                logger.error(
                    log_messages.BAD_FEED_SUBSCRIBER, subscriber.subscription_id, self
                )
                bad_subscribers.append(subscriber)

        for bad_subscriber in bad_subscribers:
            self.unsubscribe(bad_subscriber.subscription_id)

    @abstractmethod
    def serialize(self, raw_message: S) -> T:
        """
        Operations to serialize raw data for publication.

        Any potential CPU expensive operations should be moved here, to optimize
        serialization time.
        """
        # pylint: disable=unnecessary-pass
        pass

    def subscriber_count(self) -> int:
        return len(self.subscribers)

    # pylint: disable=unused-argument
    def should_publish_message_to_subscriber(
        self, subscriber: Subscriber[T], raw_message: S, serialized_message: T
    ) -> bool:
        return True

    def validate_filters(self, filters: str) -> Tuple[str, List[str]]:
        filter_parsing.get_validator(filters)
        keys = filter_parsing.get_keys(filters)
        logger.debug("Returning filters {} with keys {}", filters, keys)
        return filters, keys
