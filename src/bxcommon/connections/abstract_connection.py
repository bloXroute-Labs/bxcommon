import asyncio
import time
from abc import ABCMeta, abstractmethod
from asyncio import Future
from collections import defaultdict
from typing import ClassVar, Generic, TypeVar, TYPE_CHECKING, Optional, Union, NamedTuple

from bxcommon import constants
from bxcommon.connections.connection_state import ConnectionState
from bxcommon.connections.connection_type import ConnectionType
from bxcommon.exceptions import PayloadLenError, UnauthorizedMessageError, ConnectionStateError
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.messages.abstract_message_factory import AbstractMessageFactory
from bxcommon.messages.validation.control_flag_validation_error import ControlFlagValidationError
from bxcommon.messages.validation.default_message_validator import DefaultMessageValidator
from bxcommon.messages.validation.message_validation_error import MessageValidationError
from bxcommon.messages.versioning.nonversion_message_error import NonVersionMessageError
from bxcommon.models.node_type import NodeType
from bxcommon.models.outbound_peer_model import OutboundPeerModel
from bxcommon.models.authenticated_peer_info import AuthenticatedPeerInfo
from bxcommon.network.abstract_socket_connection_protocol import AbstractSocketConnectionProtocol
from bxcommon.network.network_direction import NetworkDirection
from bxcommon.utils import convert, performance_utils
from bxcommon.utils import memory_utils
from bxcommon.utils.alarm_queue import AlarmId
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.buffers.output_buffer import OutputBuffer
from bxcommon.utils.stats import hooks, stats_format
from bxutils import log_messages
from bxutils import logging
from bxutils.constants import HAS_PREFIX
from bxutils.exceptions.connection_authentication_error import ConnectionAuthenticationError
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_record_type import LogRecordType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)
memory_logger = logging.get_logger(LogRecordType.BxMemory, __name__)
msg_handling_logger = logging.get_logger(LogRecordType.MessageHandlingTroubleshooting, __name__)
Node = TypeVar("Node", bound="AbstractNode")


class ConnectionMessagePreview(NamedTuple):
    is_full_message: bool
    should_process_message: bool
    msg_type: Optional[bytes]
    payload_len: Optional[int]


# pylint: disable=too-many-public-methods
class AbstractConnection(Generic[Node]):
    __metaclass__ = ABCMeta

    CONNECTION_TYPE: ClassVar[ConnectionType] = ConnectionType.NONE
    node: Node
    message_factory: AbstractMessageFactory
    format_connection_desc: str
    connection_repr: str

    # performance critical attribute, has been pulled out of connection state
    established: bool

    def __init__(self, socket_connection: AbstractSocketConnectionProtocol, node: Node) -> None:
        self.socket_connection = socket_connection
        self.file_no = socket_connection.file_no

        # (IP, Port) at time of socket creation.
        # If the version/hello message contains a different port (i.e. connection is not from me), this will
        # be updated to the one in the message.
        self.endpoint = self.socket_connection.endpoint
        self.peer_ip, self.peer_port = self.endpoint
        self.peer_id: Optional[str] = None
        self.external_ip = node.opts.external_ip
        self.external_port = node.opts.external_port
        self.direction = self.socket_connection.direction
        self.from_me = self.direction == NetworkDirection.OUTBOUND

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.state = ConnectionState.CONNECTING
        self.established = False

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0
        self.peer_desc = repr(self.endpoint)

        self.can_send_pings = False
        self.pong_timeout_enabled = False

        self.hello_messages = []
        self.header_size = 0
        self.message_factory = self.connection_message_factory()
        self.message_handlers = {}

        self.log_throughput = True

        self.pong_message = None
        self.ack_message = None

        self.ping_alarm_id: Optional[AlarmId] = None
        self.ping_interval_s = constants.PING_INTERVAL_S
        self.pong_timeout_alarm_id: Optional[AlarmId] = None

        # Default network number to network number of current node. But it can change after hello message is received
        self.network_num = node.network_num

        self.message_validator = DefaultMessageValidator()

        self._debug_message_tracker = defaultdict(int)
        self._last_debug_message_log_time = time.time()

        self.processing_message_index = 0

        self.peer_model: Optional[OutboundPeerModel] = None

        self._is_authenticated = False
        self.account_id: Optional[str] = None
        self.tier_name: Optional[str] = None

        self._close_waiter: Optional[Future] = None
        self.format_connection()

        self.log_debug("Connection initialized.")

    def __repr__(self):
        if logger.isEnabledFor(LogLevel.DEBUG):
            details = f"file_no: {self.file_no}, address: {self.peer_desc}, network_num: {self.network_num}"
        else:
            details = f"file_no: {self.file_no}, address: {self.peer_desc}"

        return f"{self.CONNECTION_TYPE} ({details})"

    @abstractmethod
    def ping_message(self) -> AbstractMessage:
        """
        Define ping message characteristics for pinging on connection.

        This function may have side-effects; only call this if the ping message will
        be used.
        """

    @abstractmethod
    def connection_message_factory(self) -> AbstractMessageFactory:
        pass

    def log_trace(self, message, *args, **kwargs):
        if logger.isEnabledFor(LogLevel.TRACE):
            self._log_message(LogLevel.TRACE, message, *args, **kwargs)

    def log_debug(self, message, *args, **kwargs):
        if logger.isEnabledFor(LogLevel.DEBUG):
            self._log_message(LogLevel.DEBUG, message, *args, **kwargs)

    def log_info(self, message, *args, **kwargs):
        self._log_message(LogLevel.INFO, message, *args, **kwargs)

    def log_warning(self, message, *args, **kwargs):
        self._log_message(LogLevel.WARNING, message, *args, **kwargs)

    def log_error(self, message, *args, **kwargs):
        self._log_message(LogLevel.ERROR, message, *args, **kwargs)

    def log(self, level: LogLevel, message, *args, **kwargs):
        self._log_message(level, message, *args, **kwargs)

    def is_active(self) -> bool:
        """
        Indicates whether the connection is established and ready for normal messages.

        This function is very frequently called. Avoid doing any sort of complex
        operations, inline function calls, and avoid flags.
        """
        return self.established and self.socket_connection is not None and self.socket_connection.alive

    def is_alive(self) -> bool:
        """
        Indicates whether the connection's socket is alive.

        This function is very frequently called. Avoid doing any sort of complex
        operations, inline function calls, and avoid flags.
        """
        if self.socket_connection is None:
            return False
        return self.socket_connection.alive

    def on_connection_established(self):
        if not self.is_active():
            self.state |= ConnectionState.HELLO_RECVD
            self.state |= ConnectionState.HELLO_ACKD
            self.state |= ConnectionState.ESTABLISHED
            self.established = True

            self.log_info("Connection established.")

            # Reset num_retries when a connection established in order to support resetting the Fibonnaci logic
            # to determine next retry
            self.node.num_retries_by_ip[(self.peer_ip, self.peer_port)] = 0

            for peer_model in self.node.outbound_peers:
                if (
                    (
                        peer_model.ip == self.peer_ip
                        and peer_model.port == self.peer_port
                    )
                    or peer_model.node_id == self.peer_id
                ):
                    self.peer_model = peer_model

    def add_received_bytes(self, bytes_received: Union[bytearray, bytes]):
        """
        Adds bytes received from socket connection to input buffer

        :param bytes_received: new bytes received from socket connection
        """
        assert self.is_alive()

        self.inputbuf.add_bytes(bytes_received)

    def get_bytes_to_send(self):
        assert self.is_alive()

        return self.outputbuf.get_buffer()

    def advance_sent_bytes(self, bytes_sent):
        self.advance_bytes_on_buffer(self.outputbuf, bytes_sent)

    def enqueue_msg(self, msg: AbstractMessage, prepend: bool = False):
        """
        Enqueues the contents of a Message instance, msg, to our outputbuf and attempts to send it if the underlying
        socket has room in the send buffer.

        :param msg: message
        :param prepend: if the message should be bumped to the front of the outputbuf
        """
        self._log_message(msg.log_level(), "Enqueued message: {}", msg)
        self.enqueue_msg_bytes(msg.rawbytes(), prepend)

    def enqueue_msg_bytes(
        self,
        msg_bytes: Union[bytearray, memoryview],
        prepend: bool = False,
    ):
        """
        Enqueues the raw bytes of a message, msg_bytes, to our outputbuf and attempts to send it if the
        underlying socket has room in the send buffer.

        This function is very frequently called. Avoid doing any sort of complex
        operations, inline function calls, and avoid flags.

        :param msg_bytes: message bytes
        :param prepend: if the message should be bumped to the front of the outputbuf
        """

        if not self.socket_connection.alive:
            return

        self.log_trace("Enqueued {} bytes.", len(msg_bytes))

        if prepend:
            self.outputbuf.prepend_msgbytes(msg_bytes)
        else:
            self.outputbuf.enqueue_msgbytes(msg_bytes)

        self.socket_connection.send()

    def pre_process_msg(self) -> ConnectionMessagePreview:
        is_full_msg, msg_type, payload_len = self.message_factory.get_message_header_preview_from_input_buffer(
            self.inputbuf
        )

        return ConnectionMessagePreview(is_full_msg, True, msg_type, payload_len)

    def process_msg_type(self, message_type, is_full_msg, payload_len):
        """
        Processes messages that require changes to the regular message handling flow
        (pop off single message, process it, continue on with the stream)

        :param message_type: message type
        :param is_full_msg: flag indicating if full message is available on input buffer
        :param payload_len: length of payload
        :return:
        """

    def process_message(self):
        """
        Processes the next bytes on the socket's inputbuffer.
        Returns 0 in order to avoid being rescheduled if this was an alarm.
        """
        # pylint: disable=too-many-return-statements, too-many-branches, too-many-statements

        logger.trace("START PROCESSING from {}", self)

        start_time = time.time()
        messages_processed = defaultdict(int)
        total_bytes_processed = 0

        self.processing_message_index = 0

        while True:
            input_buffer_len_before = self.inputbuf.length
            is_full_msg = False
            payload_len = None
            msg = None
            msg_type = None

            try:
                # abort message processing if connection has been closed
                if not self.socket_connection.alive:
                    return

                is_full_msg, should_process, msg_type, payload_len = self.pre_process_msg()

                if not should_process and is_full_msg:
                    self.pop_next_bytes(payload_len)
                    continue

                self.message_validator.validate(
                    is_full_msg,
                    msg_type,
                    self.header_size,
                    payload_len,
                    self.inputbuf
                )

                self.process_msg_type(msg_type, is_full_msg, payload_len)

                if not is_full_msg:
                    break

                msg = self.pop_next_message(payload_len)
                total_bytes_processed += len(msg.rawbytes())

                # If there was some error in parsing this message, then continue the loop.
                if msg is None:
                    if self._report_bad_message():
                        return
                    continue

                # Full messages must be one of the handshake messages if the connection isn't established yet.
                if (
                    not self.established and msg_type not in self.hello_messages
                ):
                    self.log_warning(log_messages.UNEXPECTED_MESSAGE, msg_type)
                    self.mark_for_close()
                    return

                if self.log_throughput:
                    hooks.add_throughput_event(
                        NetworkDirection.INBOUND,
                        msg_type,
                        len(msg.rawbytes()),
                        self.peer_desc,
                        self.peer_id
                    )

                if not logger.isEnabledFor(msg.log_level()) and logger.isEnabledFor(LogLevel.INFO):
                    self._debug_message_tracker[msg_type] += 1
                elif len(self._debug_message_tracker) > 0:
                    self.log_debug(
                        "Processed the following messages types: {} over {:.2f} seconds.",
                        self._debug_message_tracker,
                        time.time() - self._last_debug_message_log_time
                    )
                    self._debug_message_tracker.clear()
                    self._last_debug_message_log_time = time.time()

                self._log_message(msg.log_level(), "Processing message: {}", msg)

                if msg_type in self.message_handlers:
                    msg_handler = self.message_handlers[msg_type]

                    handler_start = time.time()
                    msg_handler(msg)
                    performance_utils.log_operation_duration(
                        msg_handling_logger,
                        "Single message handler",
                        handler_start,
                        constants.MSG_HANDLERS_CYCLE_DURATION_WARN_THRESHOLD_S,
                        connection=self,
                        handler=msg_handler,
                        message=msg
                    )
                messages_processed[msg_type] += 1

            # TODO: Investigate possible solutions to recover from PayloadLenError errors
            except PayloadLenError as e:
                self.log_error(log_messages.COULD_NOT_PARSE_MESSAGE, e.msg)
                self.mark_for_close()
                return

            except MemoryError as e:
                self.log_error(log_messages.OUT_OF_MEMORY, e, exc_info=True)
                self.log_debug(
                    "Failed message bytes: {}",
                    self._get_last_msg_bytes(msg, input_buffer_len_before, payload_len)
                )
                raise

            except UnauthorizedMessageError as e:
                self.log_error(log_messages.UNAUTHORIZED_MESSAGE, e.msg.MESSAGE_TYPE, self.peer_desc)
                self.log_debug(
                    "Failed message bytes: {}",
                    self._get_last_msg_bytes(msg, input_buffer_len_before, payload_len)
                )

                # give connection a chance to restore its state and get ready to process next message
                self.clean_up_current_msg(payload_len, input_buffer_len_before == self.inputbuf.length)

                if self._report_bad_message():
                    return

            except MessageValidationError as e:
                if self.node.NODE_TYPE not in NodeType.GATEWAY_TYPE:
                    if isinstance(e, ControlFlagValidationError):
                        if e.is_cancelled_cut_through:
                            self.log_debug(
                                "Message validation failed for {} message: {}. Probably cut-through cancellation",
                                msg_type, e.msg)
                        else:
                            self.log_warning(log_messages.MESSAGE_VALIDATION_FAILED, msg_type, e.msg)
                    else:
                        self.log_warning(log_messages.MESSAGE_VALIDATION_FAILED, msg_type, e.msg)
                else:
                    self.log_debug("Message validation failed for {} message: {}.", msg_type, e.msg)
                self.log_debug("Failed message bytes: {}",
                               self._get_last_msg_bytes(msg, input_buffer_len_before, payload_len))

                if is_full_msg:
                    self.clean_up_current_msg(payload_len, input_buffer_len_before == self.inputbuf.length)
                else:
                    self.log_error(log_messages.UNABLE_TO_RECOVER_PARTIAL_MESSAGE)
                    self.mark_for_close()
                    return

                if self._report_bad_message():
                    return

            except NonVersionMessageError as e:
                if e.is_known:
                    self.log_debug("Received invalid handshake request on {}:{}, {}", self.peer_ip, self.peer_port,
                                   e.msg)
                else:
                    self.log_warning(log_messages.INVALID_HANDSHAKE, self.peer_ip, self.peer_port, e.msg)
                self.log_debug("Failed message bytes: {}",
                               self._get_last_msg_bytes(msg, input_buffer_len_before, payload_len))

                self.mark_for_close()
                return

            # TODO: Throw custom exception for any errors that come from input that has not been
            # validated and only catch that subclass of exceptions
            # pylint: disable=broad-except
            except Exception as e:

                # Attempt to recover connection by removing bad full message
                if is_full_msg:
                    self.log_error(log_messages.TRYING_TO_RECOVER_MESSAGE, e, exc_info=True)
                    self.log_debug("Failed message bytes: {}",
                                   self._get_last_msg_bytes(msg, input_buffer_len_before, payload_len))

                    # give connection a chance to restore its state and get ready to process next message
                    self.clean_up_current_msg(payload_len, input_buffer_len_before == self.inputbuf.length)

                # Connection is unable to recover from message processing error if incomplete message is received
                else:
                    self.log_error(log_messages.UNABLE_TO_RECOVER_FULL_MESSAGE, e, exc_info=True)
                    self.log_debug("Failed message bytes: {}",
                                   self._get_last_msg_bytes(msg, input_buffer_len_before, payload_len))
                    self.mark_for_close()
                    return

                if self._report_bad_message():
                    return
            else:
                self.num_bad_messages = 0

            self.processing_message_index += 1

        performance_utils.log_operation_duration(msg_handling_logger,
                                                 "Message handlers",
                                                 start_time,
                                                 constants.MSG_HANDLERS_DURATION_WARN_THRESHOLD_S,
                                                 connection=self, count=messages_processed)
        duration_ms = (time.time() - start_time) * 1000
        logger.trace("DONE PROCESSING from {}. Bytes processed: {}. Messages processed: {}. Duration: {}",
                     self, total_bytes_processed, messages_processed, stats_format.duration(duration_ms))

    def pop_next_message(self, payload_len: int) -> AbstractMessage:
        """
        Pop the next full message off of the buffer given the message length.
        Preserves invariant of self.inputbuf always containing the start of a
        valid message. The caller of this function is responsible for ensuring
        there is a valid message on the buffer.

        :param payload_len: length of payload
        :return: message object
        """
        return self.message_factory.create_message_from_buffer(
            self.pop_next_bytes(payload_len)
        )

    def pop_next_bytes(self, payload_len: int) -> Union[memoryview, bytearray, bytes]:
        msg_len = self.message_factory.base_message_type.HEADER_LENGTH + payload_len
        return self.inputbuf.remove_bytes(msg_len)

    def advance_bytes_on_buffer(self, buf, bytes_written):
        hooks.add_throughput_event(NetworkDirection.OUTBOUND, None, bytes_written, self.peer_desc, self.peer_id)
        try:
            buf.advance_buffer(bytes_written)
        except ValueError as e:
            raise RuntimeError("Connection: {}, Failed to advance buffer".format(self)) from e

    def schedule_pings(self) -> None:
        """
        Schedules ping on the connection. Multiple calls of this method will
        override the existing alarm.
        """
        self._unschedule_pings()

        if self.can_send_pings:
            self.ping_alarm_id = self.node.alarm_queue.register_alarm(
                self.ping_interval_s, self.send_ping
            )

    def send_ping(self) -> float:
        """
        Send a ping (and reschedule if called from alarm queue)
        """
        if self.can_send_pings and self.is_alive():
            self.enqueue_msg(self.ping_message())

            if self.pong_timeout_enabled:
                self.schedule_pong_timeout()

            return self.ping_interval_s
        return constants.CANCEL_ALARMS

    def msg_hello(self, msg):
        self.state |= ConnectionState.HELLO_RECVD
        if msg.node_id() is None:
            self.log_debug("Received hello message without peer id.")
        if self.peer_id is None:
            self.peer_id = msg.node_id()

        # This should only be necessary for pre1.6 connections.
        if self.peer_id in self.node.connection_pool.by_node_id and \
                self.socket_connection.endpoint.ip_address[0:3] != "172":
            existing_connection = self.node.connection_pool.get_by_node_id(
                self.peer_id
            )
            if existing_connection != self:
                if self.from_me:
                    self.mark_for_close()

                if existing_connection.from_me:
                    existing_connection.mark_for_close()

                self.log_warning(log_messages.DUPLICATE_CONNECTION, self.peer_id, existing_connection)

        self.enqueue_msg(self.ack_message)
        if ConnectionState.INITIALIZED | ConnectionState.HELLO_ACKD in self.state:
            self.on_connection_established()

    def msg_ack(self, _msg):
        """
        Handle an Ack Message
        """
        self.state |= ConnectionState.HELLO_ACKD
        if ConnectionState.INITIALIZED | ConnectionState.HELLO_RECVD in self.state:
            self.on_connection_established()

    def msg_ping(self, _msg):
        self.enqueue_msg(self.pong_message)

    def msg_pong(self, _msg):
        self.cancel_pong_timeout()

    def mark_for_close(self, should_retry: Optional[bool] = None):
        """
        Marks a connection for close, so AbstractNode can dispose of this class.
        Use this where possible for a clean shutdown.
        """
        loop = asyncio.get_event_loop()
        self._close_waiter = loop.create_future()

        if should_retry is None:
            should_retry = self.from_me

        self.log_debug("Marking connection for close, should_retry: {}.", should_retry)
        self.socket_connection.mark_for_close(should_retry)

    def dispose(self):
        """
        Performs any need operations after connection object has been discarded by the AbstractNode.
        """
        if self._close_waiter is not None:
            self._close_waiter.set_result(True)
        self._unschedule_pings()
        self.node = None
        self.socket_connection = None

    def clean_up_current_msg(self, payload_len: int, msg_is_in_input_buffer: bool) -> None:
        """
        Removes current message from the input buffer and resets connection to a state ready to process next message.
        Called during the handling of message processing exceptions.

        :param payload_len: length of the payload of the currently processing message
        :param msg_is_in_input_buffer: flag indicating if message bytes are still in the input buffer
        :return:
        """

        if msg_is_in_input_buffer:
            self.inputbuf.remove_bytes(self.header_size + payload_len)

    def on_input_received(self) -> bool:
        """handles an input event from the event loop

        :return: True if the connection is receivable, otherwise False
        """
        return True

    def log_connection_mem_stats(self) -> None:
        """
        logs the connection's memory stats
        """
        class_name = self.__class__.__name__
        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self.inputbuf,
            "input_buffer",
            memory_utils.ObjectSize("input_buffer", 0,
                                    is_actual_size=False),
            object_item_count=len(self.inputbuf.input_list),
            object_type=memory_utils.ObjectType.BASE,
            size_type=memory_utils.SizeType.TRUE
        )
        hooks.add_obj_mem_stats(
            class_name,
            self.network_num,
            self.outputbuf,
            "output_buffer",
            memory_utils.ObjectSize("output_buffer", 0,
                                    is_actual_size=False),
            object_item_count=len(self.outputbuf.output_msgs),
            object_type=memory_utils.ObjectType.BASE,
            size_type=memory_utils.SizeType.TRUE
        )

    def update_model(self, model: OutboundPeerModel):
        self.log_trace("Updated connection model: {}", model)
        self.peer_model = model

    def schedule_pong_timeout(self) -> None:
        if self.pong_timeout_alarm_id is None:
            self.log_trace(
                "Schedule pong reply timeout for ping message in {} seconds",
                constants.PING_PONG_REPLY_TIMEOUT_S
            )
            self.pong_timeout_alarm_id = self.node.alarm_queue.register_alarm(
                constants.PING_PONG_REPLY_TIMEOUT_S, self._pong_msg_timeout
            )

    def cancel_pong_timeout(self):
        if self.pong_timeout_alarm_id is not None:
            self.node.alarm_queue.unregister_alarm(self.pong_timeout_alarm_id)
            self.pong_timeout_alarm_id = None

    def on_connection_authenticated(self, peer_info: AuthenticatedPeerInfo) -> None:
        self.peer_id = peer_info.peer_id
        if self.CONNECTION_TYPE != peer_info.connection_type:
            self.node.connection_pool.update_connection_type(self, peer_info.connection_type)
        self.account_id = peer_info.account_id
        self._is_authenticated = True

    async def wait_closed(self):
        if self._close_waiter is not None:
            await self._close_waiter
            self._close_waiter = None
        else:
            await asyncio.sleep(0)

        if self.is_alive():
            raise ConnectionStateError("Connection is still alive after closed", self)

    def set_account_id(self, account_id: Optional[str], tier_name: str):
        if self._is_authenticated and account_id != self.account_id:
            raise ConnectionAuthenticationError(
                f"Invalid account id {account_id} is different than connection account id: {self.account_id}")

        if not self._is_authenticated:
            self.account_id = account_id
        self.tier_name = tier_name

    def get_backlog_size(self) -> int:
        output_buffer_backlog = self.outputbuf.length
        socket_buffer_backlog = self.socket_connection.get_write_buffer_size()
        self.log_trace("Output backlog: {}, socket backlog: {}", output_buffer_backlog, socket_buffer_backlog)
        return output_buffer_backlog + socket_buffer_backlog

    def format_connection(self) -> None:
        self.format_connection_desc = "{} - {}".format(
            self.peer_desc, self.CONNECTION_TYPE.format_short()
        )
        self.connection_repr = repr(self)

    def _unschedule_pings(self) -> None:
        existing_alarm = self.ping_alarm_id
        if existing_alarm:
            self.node.alarm_queue.unregister_alarm(existing_alarm)
            self.ping_alarm_id = None

    def _pong_msg_timeout(self) -> None:
        if self.is_alive():
            self.log_info(
                "Connection appears to be broken. Peer did not reply to PING message within allocated time. "
                "Closing connection."
            )
            self.mark_for_close()
            self.pong_timeout_alarm_id = None

    def _report_bad_message(self):
        """
        Increments counter for bad messages. Returns True if connection should be closed.
        :return: if connection should be closed
        """
        if self.num_bad_messages == constants.MAX_BAD_MESSAGES:
            self.log_warning(log_messages.TOO_MANY_BAD_MESSAGES)
            self.mark_for_close()
            return True
        else:
            self.num_bad_messages += 1
            return False

    def _get_last_msg_bytes(self, msg, input_buffer_len_before, payload_len):

        if msg is not None:
            return convert.bytes_to_hex(msg.rawbytes()[:constants.MAX_LOGGED_BYTES_LEN])

        # bytes still available on input buffer
        if input_buffer_len_before == self.inputbuf.length and payload_len is not None:
            return convert.bytes_to_hex(
                self.inputbuf.peek_message(min(self.header_size + payload_len, constants.MAX_LOGGED_BYTES_LEN)))

        return "<not available>"

    def _log_message(self, level: LogLevel, message, *args, **kwargs):
        logger.log(
            level, message, HAS_PREFIX, self.connection_repr, *args, **kwargs
        )
