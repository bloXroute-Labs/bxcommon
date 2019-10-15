#
# Copyright (C) 2017, bloXroute Labs, All rights reserved.
# See the file COPYING for details.
#
# Exceptions
#


class ParseError(Exception):
    def __init__(self, msg):
        super(ParseError, self).__init__(msg)

        self.msg = msg


class UnrecognizedCommandError(ParseError):
    def __init__(self, msg, raw_data):
        super(UnrecognizedCommandError, self).__init__(msg)

        self.raw_data = raw_data


class PayloadLenError(ParseError):
    pass


class UnauthorizedMessageError(ParseError):
    def __init__(self, msg):
        super(UnauthorizedMessageError, self).__init__(msg)


class ChecksumError(ParseError):
    def __init__(self, msg, raw_data):
        super(ChecksumError, self).__init__(msg)

        self.raw_data = raw_data


class TerminationError(Exception):
    pass


class DecryptionError(Exception):
    pass
