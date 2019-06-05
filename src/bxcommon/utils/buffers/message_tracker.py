import time
from collections import deque
from typing import Deque, Optional, TYPE_CHECKING

from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.utils import logger
from bxcommon.utils.log_level import LogLevel

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
            return self.message.log_level()
        else:
            return LogLevel.INFO

    def __repr__(self):
        return "MessageTrackerEntry<message: {}, sent_bytes: {}, length: {}>".format(self.message, self.sent_bytes,
                                                                                     self.length)


class MessageTracker:
    messages: Deque[MessageTrackerEntry]
    connection: "AbstractConnection"
    is_working: bool = True

    def __init__(self, connection: "AbstractConnection"):
        self.connection = connection
        self.messages = deque()

    def __repr__(self):
        return "MessageTracker<connection: {}, messages: {}>".format(self.connection, repr(self.messages))

    def advance_bytes(self, num_bytes: int):
        if not self.is_working:
            return

        bytes_left = num_bytes
        while bytes_left > 0:

            if not self.messages:
                logger.error("Message tracker somehow got out of sync on connection: {}. Attempted to send {} bytes"
                             "when none left in tracker.".format(self.connection, bytes_left))
                self.is_working = False

            if bytes_left >= (self.messages[0].length - self.messages[0].sent_bytes):
                sent_message = self.messages.popleft()
                logger.log(sent_message.message_log_level(), "Sent {} to socket on connection: {}. Took {:.2f}ms.",
                           sent_message.message, self.connection, 1000 * (time.time() - sent_message.queued_time))
                bytes_left -= (sent_message.length - sent_message.sent_bytes)
            else:
                in_progress_message = self.messages[0]
                in_progress_message.sent_bytes += bytes_left
                logger.log(in_progress_message.message_log_level(),
                           "Sent {} out of {} bytes of {} to socket on connection: {}. Elapsed time: {:.2f}ms.",
                           in_progress_message.sent_bytes, in_progress_message.length, in_progress_message.message,
                           self.connection, 1000 * (time.time() - in_progress_message.queued_time))
                bytes_left = 0

    def append_message(self, num_bytes: int, message: Optional[AbstractMessage]):
        if not self.is_working:
            return

        if message is not None and num_bytes != len(message.rawbytes()):
            raise ValueError("Message does not match byte length.")

        self.messages.append(MessageTrackerEntry(message, num_bytes))

    def prepend_message(self, num_bytes: int, message: Optional[AbstractMessage]):
        if not self.is_working:
            return

        if message is not None and num_bytes != len(message.rawbytes()):
            raise ValueError("Message does not match byte length.")

        if self.messages and self.messages[0].sent_bytes != 0:
            in_progress_message = self.messages.popleft()
            self.messages.appendleft(MessageTrackerEntry(message, num_bytes))
            self.messages.appendleft(in_progress_message)
        else:
            self.messages.append(MessageTrackerEntry(message, num_bytes))
