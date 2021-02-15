import asyncio
import uuid
import dataclasses
from typing import Generic, TypeVar, Union, Dict, Any, List, Callable

from bxcommon import constants
from bxcommon.feed import filter_parsing

T = TypeVar("T")


class Subscriber(Generic[T]):
    """
    Subscriber object for asynchronous listening to a feed, with functionality
    to filter received messages on certain fields.

    Any object can published on a feed (and received by this subscriber), though
    users should be careful about ensuring that the object is serializable if
    the object should be received over the websocket or IPC subscriptions.

    If `options` is None, the message will be passed onward with no changes.

    Make sure to update documentation page with any input format change
    """

    subscription_id: str
    messages: "asyncio.Queue[Union[T, Dict[str, Any]]]"
    options: Dict[str, Any]
    filters: str
    validator: Callable[[Dict], bool]
    should_exit: bool

    def __init__(self, options: Dict[str, Any]) -> None:
        self.options = options
        self.subscription_id = str(uuid.uuid4())
        self.messages = asyncio.Queue(constants.RPC_SUBSCRIBER_MAX_QUEUE_SIZE)
        filters = options.get("filters", None)
        self.filters = filters if filters else ""
        self.validator = filter_parsing.get_validator(self.filters)
        self.should_exit = False

    async def receive(self) -> Union[T, Dict[str, Any]]:
        """
        Receives the next message in the queue.

        This function will block until a new message is posted to the queue.
        """
        message = await self.messages.get()
        return message

    def queue(self, message: T) -> Union[T, Dict[str, Any]]:
        """
        Queues up a message, releasing all receiving listeners.

        If too many messages are queued without a listener, this task
        will eventually fail and must be handled.
        """
        include_fields = self.options.get("include", None)
        if include_fields:
            if isinstance(message, dict):
                filtered_message = filter_message(message, include_fields)

            elif dataclasses.is_dataclass(message):
                filtered_message = filter_message(dataclasses.asdict(message), include_fields)
            else:
                filtered_message = filter_message(message.__dict__, include_fields)

            self.messages.put_nowait(filtered_message)
            return filtered_message
        else:
            if hasattr(message, "__dict__"):
                self.messages.put_nowait(message.__dict__)
                return message.__dict__
            else:
                self.messages.put_nowait(message)
                return message

    def fast_queue(self, message: Union[T, Dict[str, Any]]) -> None:
        """
        Queue a message, skipping include validation.

        This method should be used judiciously, ensuring the expected content is
        added. The goal is have objects with a common Python ID for later reference
        when serializing.
        """
        self.messages.put_nowait(message)

    def same_options(self, other: "Subscriber") -> bool:
        self_includes = self.options.get("include", None)
        other_includes = other.options.get("include", None)
        return self_includes == other_includes

    def validate(self, state: Dict[str, Any]) -> bool:
        should_publish = False
        try:
            should_publish = self.validator(state)
        except TypeError:
            self.should_exit = True
        return should_publish


def filter_message(message: Dict[str, Any], include_fields: List[str]) -> Dict[str, Any]:
    output = {}
    for key in include_fields:
        value = message
        partial_message = output
        field_keys = key.split(".")
        for key_element in field_keys:
            value = value[key_element]
            if isinstance(value, dict) and len(field_keys) > 1 and key_element != field_keys[-1]:
                partial_message = partial_message.setdefault(key_element, {})
            else:
                partial_message = partial_message.setdefault(key_element, value)
    return output
