from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v1.bloxroute_message_factory_v1 import bloxroute_message_factory_v1
from bxcommon.messages.bloxroute.v1.message_converter_factory_v1 import message_converter_factory_v1
from bxcommon.messages.versioning.abstract_version_manager import AbstractVersionManager


class _BloxrouteVersionManager(AbstractVersionManager):
    CURRENT_PROTOCOL_VERSION = 2
    VERSION_MESSAGE_MAIN_LENGTH = constants.VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN
    _PROTOCOL_TO_CONVERTER_FACTORY_MAPPING = {
        1: message_converter_factory_v1
    }
    _PROTOCOL_TO_FACTORY_MAPPING = {
        1: bloxroute_message_factory_v1,
        2: bloxroute_message_factory
    }

    def __init__(self):
        super(_BloxrouteVersionManager, self).__init__()
        self.protocol_to_factory_mapping = self._PROTOCOL_TO_FACTORY_MAPPING
        self.protocol_to_converter_factory_mapping = self._PROTOCOL_TO_CONVERTER_FACTORY_MAPPING
        self.version_message_command = BloxrouteMessageType.HELLO


bloxroute_version_manager = _BloxrouteVersionManager()
