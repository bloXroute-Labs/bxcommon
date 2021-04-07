#
# Copyright (C) 2017, bloXroute Labs, All rights reserved.
# See the file COPYING for details.
#
# Exceptions
#
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_connection import AbstractConnection


class ParseError(Exception):
    def __init__(self, msg) -> None:
        super(ParseError, self).__init__(msg)

        self.msg = msg


class UnrecognizedCommandError(ParseError):
    def __init__(self, msg, raw_data) -> None:
        super(UnrecognizedCommandError, self).__init__(msg)

        self.raw_data = raw_data


class PayloadLenError(ParseError):
    pass


class UnauthorizedMessageError(ParseError):
    pass


class ChecksumError(ParseError):
    def __init__(self, msg, raw_data) -> None:
        super(ChecksumError, self).__init__(msg)

        self.raw_data = raw_data


class HighMemoryError(Exception):
    pass


class TerminationError(Exception):
    pass


class DecryptionError(Exception):
    pass


class FeedSubscriptionTimeoutError(Exception):
    pass


class ConnectionStateError(Exception):
    def __init__(self, msg: str, conn: "AbstractConnection") -> None:
        super().__init__(msg)
        self.msg = msg
        self.conn = conn
