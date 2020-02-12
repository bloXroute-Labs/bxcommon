import time
from collections import deque
from typing import Deque, Optional, TYPE_CHECKING

from bxcommon.messages.abstract_block_message import AbstractBlockMessage
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.bloxroute.tx_message import TxMessage
from bxcommon.utils.stats.transaction_statistics_service import tx_stats
from bxutils import logging
from bxutils.logging.log_level import LogLevel

logger = logging.get_logger(__name__)

if TYPE_CHECKING:
    from bxcommon.connections.abstract_connection import AbstractConnection


class MessageTrackerEntry:
    message: Optional[AbstractMessage]
    sent_bytes: int = 0
    length: int
    queued_time: float

    def __init__(self, message: Optional[AbstractMessage], length: int):
        self.message = message
        self.length = length
        self.queued_time = time.time()

    def message_log_level(self) -> LogLevel:
        if self.message:
            if isinstance(self.message, TxMessage):
                if tx_stats.should_log_event_for_tx(
                    self.message.tx_hash().binary,
                    self.message.network_num(),
                    self.message.short_id()
                ):
                    return LogLevel.DEBUG

            return self.message.log_level()

        return LogLevel.DEBUG

    def __repr__(self):
        return "MessageTrackerEntry<message: {}, sent_bytes: {}, length: {}>".format(
            self.message, self.sent_bytes, self.length
        )


class MessageTracker:
    """
    Service to track when message bytes get fully written from the output buffer to the
    OS level socket.
    """

    messages: Deque[MessageTrackerEntry]
    connection: "AbstractConnection"
    is_working: bool = True
    bytes_remaining: int = 0

    def __init__(self, connection: "AbstractConnection"):
        self.connection = connection
        self.messages = deque()

    def __repr__(self):
        return (
            f"MessageTracker<connection: {self.connection}, "
            f"messages: {self.messages}>"
        )

    def is_sending_block_message(self) -> bool:
        if not self.messages:
            return False

        entry = self.messages[0]
        return entry.message is not None and isinstance(
            entry.message, AbstractBlockMessage
        )

    def advance_bytes(self, num_bytes: int):
        if not self.is_working:
            return

        bytes_left = num_bytes
        self.bytes_remaining -= num_bytes
        while bytes_left > 0:

            if not self.messages:
                self.connection.log_debug(
                    "Message tracker somehow got out of sync. "
                    "Attempted to send {} bytes when none left in tracker. "
                    "Disabling further tracking.",
                    bytes_left,
                )
                self.is_working = False

            if bytes_left >= (
                self.messages[0].length - self.messages[0].sent_bytes
            ):
                sent_message = self.messages.popleft()
                self.connection.log(
                    sent_message.message_log_level(),
                    "Sent {} to socket. Took {:.2f}ms. "
                    "{} bytes remaining on buffer.",
                    sent_message.message,
                    1000 * (time.time() - sent_message.queued_time),
                    self.bytes_remaining,
                )
                bytes_left -= sent_message.length - sent_message.sent_bytes
            else:
                in_progress_message = self.messages[0]
                in_progress_message.sent_bytes += bytes_left
                self.connection.log(
                    in_progress_message.message_log_level(),
                    "Sent {} out of {} bytes of {} to socket. "
                    "Elapsed time: {:.2f}ms. {} bytes remaining on buffer.",
                    in_progress_message.sent_bytes,
                    in_progress_message.length,
                    in_progress_message.message,
                    1000 * (time.time() - in_progress_message.queued_time),
                    self.bytes_remaining,
                )
                bytes_left = 0

    def append_message(
        self, num_bytes: int, message: Optional[AbstractMessage]
    ):
        """
        Appends a message entry to the tracker.

        This method trusts that that num_bytes matches the message, but does
        not verify it. This is useful for Ethereum, which frames and encrypts
        the message, which may change the length of the message.
        """
        if not self.is_working:
            return

        self.messages.append(MessageTrackerEntry(message, num_bytes))
        self.bytes_remaining += num_bytes

    def prepend_message(
        self, num_bytes: int, message: Optional[AbstractMessage]
    ):
        """
        Appends a message entry to the tracker.

        This method trusts that that num_bytes matches the message, but does
        not verify it. This is useful for Ethereum, which frames and encrypts
        the message, which may change the length of the message.
        """
        if not self.is_working:
            return

        if self.messages and self.messages[0].sent_bytes != 0:
            in_progress_message = self.messages.popleft()
            self.messages.appendleft(MessageTrackerEntry(message, num_bytes))
            self.messages.appendleft(in_progress_message)
        else:
            self.messages.append(MessageTrackerEntry(message, num_bytes))

        self.bytes_remaining += num_bytes

    def empty_bytes(self, skip_bytes: int):
        """
        Remove bytes from tracker starting at `skip_bytes`.

        Used when the output buffer is being emptied, to stop tracking of
        later bytes.
        """
        bytes_skipped = 0
        index = 0

        while self.messages:
            entry = self.messages[index]
            bytes_left = entry.length - entry.sent_bytes
            bytes_skipped += bytes_left
            index += 1
            if bytes_skipped == skip_bytes:
                break
            elif bytes_skipped > skip_bytes:
                index -= 1
                break

        while len(self.messages) > index:
            entry_removed = self.messages.pop()
            self.bytes_remaining -= (
                entry_removed.length - entry_removed.sent_bytes
            )
            self.connection.log(
                entry_removed.message_log_level(),
                "Removed {} bytes of {} from buffer. Message was queued for "
                "{}ms.",
                entry_removed.length,
                entry_removed.message,
                1000 * (time.time() - entry_removed.queued_time)
            )
