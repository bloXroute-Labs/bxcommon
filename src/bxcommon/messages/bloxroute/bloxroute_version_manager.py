from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.protocol_version import PROTOCOL_VERSION
from bxcommon.messages.bloxroute.v4.bloxroute_message_factory_v4 import bloxroute_message_factory_v4
from bxcommon.messages.bloxroute.v4.message_converter_factory_v4 import message_converter_factory_v4
from bxcommon.messages.bloxroute.v5.bloxroute_message_factory_v5 import bloxroute_message_factory_v5
from bxcommon.messages.bloxroute.v5.message_converter_factory_v5 import message_converter_factory_v5
from bxcommon.messages.bloxroute.v6.bloxroute_message_factory_v6 import bloxroute_message_factory_v6
from bxcommon.messages.bloxroute.v6.message_converter_factory_v6 import message_converter_factory_v6
from bxcommon.messages.versioning.abstract_version_manager import AbstractVersionManager


class _BloxrouteVersionManager(AbstractVersionManager):
    CURRENT_PROTOCOL_VERSION = PROTOCOL_VERSION
    MIN_SUPPORTED_PROTOCOL_VERSION = 4
    VERSION_MESSAGE_MAIN_LENGTH = constants.VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN
    _PROTOCOL_TO_CONVERTER_FACTORY_MAPPING = {
        4: message_converter_factory_v4,
        5: message_converter_factory_v5,
        6: message_converter_factory_v6
    }
    _PROTOCOL_TO_FACTORY_MAPPING = {
        4: bloxroute_message_factory_v4,
        5: bloxroute_message_factory_v5,
        6: bloxroute_message_factory_v6,
        7: bloxroute_message_factory
    }

    def __init__(self):
        super(_BloxrouteVersionManager, self).__init__()
        self.protocol_to_factory_mapping = self._PROTOCOL_TO_FACTORY_MAPPING
        self.protocol_to_converter_factory_mapping = self._PROTOCOL_TO_CONVERTER_FACTORY_MAPPING
        self.version_message_command = BloxrouteMessageType.HELLO


bloxroute_version_manager = _BloxrouteVersionManager()
