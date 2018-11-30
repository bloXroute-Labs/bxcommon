import struct

from bxcommon.constants import VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN, VERSION_NUM_LEN
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.hello_message import HelloMessage
from bxcommon.messages.bloxroute.v1.bloxroute_message_factory_v1 import bloxroute_message_factory_v1
from bxcommon.messages.bloxroute.v1.message_converter_factory_v1 import message_converter_factory_v1
from bxcommon.utils.buffers.input_buffer import InputBuffer

CURRENT_PROTOCOL_VERSION = 2
MIN_SUPPORTED_PROTOCOL_VERSION = 1

_MESSAGE_CONVERTER_FACTORY_MAPPING = {
    1: message_converter_factory_v1
}


def is_protocol_supported(protocol_version):
    return protocol_version >= MIN_SUPPORTED_PROTOCOL_VERSION


def get_message_factory_for_version(protocol_version):
    """
    Returns message factory for provided protocol version

    :param protocol_version: protocol version
    :return: message factory
    """

    if not is_protocol_supported(protocol_version):
        raise ValueError("Protocol of version {} is not supported".format(protocol_version))

    if protocol_version == 1:
        return bloxroute_message_factory_v1

    if protocol_version == 2:
        return bloxroute_message_factory

    raise ValueError("Factory for protocol version {} is not implemented.".format(protocol_version))


def convert_message_to_older_version(convert_to_version, msg):
    """
    Converts message from current version to provided version

    :param convert_to_version: version to convert to
    :param msg: message
    :return: converted message
    """

    if not convert_to_version:
        raise ValueError("convert_to_version is required")

    if not msg:
        raise ValueError("msg is required")

    msg_converter = _get_message_converter(convert_to_version, msg.msg_type())

    return msg_converter.convert_to_older_version(msg)


def convert_message_from_older_version(convert_from_version, msg):
    """
    Converts message from older version to current version

    :param convert_from_version: version to convert from
    :param msg: message
    :return: converted message
    """

    if not convert_from_version:
        raise ValueError("convert_from_version is required")

    if not msg:
        raise ValueError("msg is required")

    msg_converter = _get_message_converter(convert_from_version, msg.msg_type())

    return msg_converter.convert_from_older_version(msg)


def convert_message_first_bytes_to_older_version(convert_to_version, msg_type, first_message_bytes):
    """
    Converts first message bytes from current version to provided version

    :param convert_to_version: version to convert to
    :param msg_type: message type
    :param first_message_bytes: message bytes
    :return: converted message bytes
    """

    if not convert_to_version:
        raise ValueError("convert_to_version is required")

    if not msg_type:
        raise ValueError("msg_type is required")

    if not first_message_bytes:
        raise ValueError("first_message_bytes is required")

    msg_converter = _get_message_converter(convert_to_version, msg_type)

    return msg_converter.convert_first_bytes_to_older_version(first_message_bytes)


def convert_message_first_bytes_from_older_version(convert_from_version, msg_type, first_message_bytes):
    """
    Converts first message bytes from older version to current version

    :param convert_from_version: version to convert from
    :param msg_type: message type
    :param first_message_bytes: message bytes
    :return: converted message bytes
    """

    if not convert_from_version:
        raise ValueError("convert_from_version is required")

    if not msg_type:
        raise ValueError("msg_type is required")

    if not first_message_bytes:
        raise ValueError("first_message_bytes is required")

    msg_converter = _get_message_converter(convert_from_version, msg_type)

    return msg_converter.convert_first_bytes_from_older_version(first_message_bytes)


def get_message_size_change_to_older_version(convert_to_version, msg_type):
    """
    Returns the difference in size between current protocol version and older version

    :param convert_to_version: version to conver to
    :param msg_type: message type
    :return: size difference
    """

    if not convert_to_version:
        raise ValueError("convert_to_version is required")

    if not msg_type:
        raise ValueError("msg_type is required")

    msg_converter = _get_message_converter(convert_to_version, msg_type)

    return msg_converter.get_message_size_change_to_older_version()


def get_message_size_change_from_older_version(convert_from_version, msg_type):
    """
    Returns the difference in size between older version and current protocol version

    :param convert_from_version: version to convert from
    :param msg_type: message type
    :return: size difference
    """

    if not convert_from_version:
        raise ValueError("convert_to_version is required")

    if not msg_type:
        raise ValueError("msg_type is required")

    msg_converter = _get_message_converter(convert_from_version, msg_type)

    return msg_converter.get_message_size_change_from_older_version()


def get_connection_protocol_version(input_buffer):
    if not isinstance(input_buffer, InputBuffer):
        raise TypeError("Argument input_buffer expected to have type InputBuffer but was {}"
                        .format(type(input_buffer)))

    if input_buffer.length < HelloMessage.HEADER_LENGTH + VERSION_NUM_LEN:
        return None

    header_buf = input_buffer.peek_message(HelloMessage.HEADER_LENGTH)

    args = HelloMessage.unpack(header_buf)

    payload_len = args[-1]

    if payload_len < VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN:
        return 1

    version_buf = input_buffer.get_slice(HelloMessage.HEADER_LENGTH, HelloMessage.HEADER_LENGTH + VERSION_NUM_LEN)

    version, = struct.unpack_from("<L", version_buf, 0)

    return version


def _get_message_converter_factory(protocol_version):
    if protocol_version not in _MESSAGE_CONVERTER_FACTORY_MAPPING:
        raise ValueError("Conversion for version {} is not supported".format(protocol_version))

    return _MESSAGE_CONVERTER_FACTORY_MAPPING[protocol_version]


def _get_message_converter(protocol_version, msg_type):
    msg_converter_factory = _get_message_converter_factory(protocol_version)
    return msg_converter_factory.get_message_converter(msg_type)
