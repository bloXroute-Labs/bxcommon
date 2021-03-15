from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_factory import bloxroute_message_factory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.protocol_version import PROTOCOL_VERSION
from bxcommon.messages.bloxroute.v6.bloxroute_message_factory_v6 import bloxroute_message_factory_v6
from bxcommon.messages.bloxroute.v6.message_converter_factory_v6 import message_converter_factory_v6
from bxcommon.messages.bloxroute.v7.bloxroute_message_factory_v7 import bloxroute_message_factory_v7
from bxcommon.messages.bloxroute.v7.message_converter_factory_v7 import message_converter_factory_v7
from bxcommon.messages.bloxroute.v8.bloxroute_message_factory_v8 import bloxroute_message_factory_v8
from bxcommon.messages.bloxroute.v8.message_converter_factory_v8 import message_converter_factory_v8
from bxcommon.messages.bloxroute.v9.bloxroute_message_factory_v9 import bloxroute_message_factory_v9
from bxcommon.messages.bloxroute.v9.message_converter_factory_v9 import message_converter_factory_v9
from bxcommon.messages.bloxroute.v10.bloxroute_message_factory_v10 import bloxroute_message_factory_v10
from bxcommon.messages.bloxroute.v10.message_converter_factory_v10 import message_converter_factory_v10
from bxcommon.messages.bloxroute.v11.bloxroute_message_factory_v11 import bloxroute_message_factory_v11
from bxcommon.messages.bloxroute.v11.message_converter_factory_v11 import message_converter_factory_v11
from bxcommon.messages.bloxroute.v12.bloxroute_message_factory_v12 import bloxroute_message_factory_v12
from bxcommon.messages.bloxroute.v12.message_converter_factory_v12 import message_converter_factory_v12
from bxcommon.messages.bloxroute.v13.bloxroute_message_factory_v13 import bloxroute_message_factory_v13
from bxcommon.messages.bloxroute.v13.message_converter_factory_v13 import message_converter_factory_v13
from bxcommon.messages.bloxroute.v14.bloxroute_message_factory_v14 import bloxroute_message_factory_v14
from bxcommon.messages.bloxroute.v14.message_converter_factory_v14 import message_converter_factory_v14
from bxcommon.messages.bloxroute.v15.bloxroute_message_factory_v15 import bloxroute_message_factory_v15
from bxcommon.messages.bloxroute.v15.message_converter_factory_v15 import message_converter_factory_v15
from bxcommon.messages.bloxroute.v16.bloxroute_message_factory_v16 import bloxroute_message_factory_v16
from bxcommon.messages.bloxroute.v16.message_converter_factory_v16 import message_converter_factory_v16
from bxcommon.messages.bloxroute.v17.bloxroute_message_factory_v17 import bloxroute_message_factory_v17
from bxcommon.messages.bloxroute.v17.message_converter_factory_v17 import message_converter_factory_v17
from bxcommon.messages.bloxroute.v18.message_converter_factory_v18 import message_converter_factory_v18
from bxcommon.messages.bloxroute.v18.bloxroute_message_factory_v18 import bloxroute_message_factory_v18
from bxcommon.messages.bloxroute.v19.bloxroute_message_factory_v19 import bloxroute_message_factory_v19
from bxcommon.messages.bloxroute.v19.message_converter_factory_v19 import message_converter_factory_v19
from bxcommon.messages.bloxroute.v20.message_converter_factory_v20 import message_converter_factory_v20
from bxcommon.messages.bloxroute.v20.bloxroute_message_factory_v20 import bloxroute_message_factory_v20
from bxcommon.messages.bloxroute.v21.message_converter_factory_v21 import message_converter_factory_v21
from bxcommon.messages.bloxroute.v21.bloxroute_message_factory_v21 import bloxroute_message_factory_v21
from bxcommon.messages.versioning.abstract_version_manager import AbstractVersionManager


class _BloxrouteVersionManager(AbstractVersionManager):
    CURRENT_PROTOCOL_VERSION = PROTOCOL_VERSION
    MIN_SUPPORTED_PROTOCOL_VERSION = 6
    VERSION_MESSAGE_MAIN_LENGTH = constants.VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN
    _PROTOCOL_TO_CONVERTER_FACTORY_MAPPING = {
        6: message_converter_factory_v6,
        7: message_converter_factory_v7,
        8: message_converter_factory_v8,
        9: message_converter_factory_v9,
        10: message_converter_factory_v10,
        11: message_converter_factory_v11,
        12: message_converter_factory_v12,
        13: message_converter_factory_v13,
        14: message_converter_factory_v14,
        15: message_converter_factory_v15,
        16: message_converter_factory_v16,
        17: message_converter_factory_v17,
        18: message_converter_factory_v18,
        19: message_converter_factory_v19,
        20: message_converter_factory_v20,
        21: message_converter_factory_v21
    }
    _PROTOCOL_TO_FACTORY_MAPPING = {
        6: bloxroute_message_factory_v6,
        7: bloxroute_message_factory_v7,
        8: bloxroute_message_factory_v8,
        9: bloxroute_message_factory_v9,
        10: bloxroute_message_factory_v10,
        11: bloxroute_message_factory_v11,
        12: bloxroute_message_factory_v12,
        13: bloxroute_message_factory_v13,
        14: bloxroute_message_factory_v14,
        15: bloxroute_message_factory_v15,
        16: bloxroute_message_factory_v16,
        17: bloxroute_message_factory_v17,
        18: bloxroute_message_factory_v18,
        19: bloxroute_message_factory_v19,
        20: bloxroute_message_factory_v20,
        21: bloxroute_message_factory_v21,
        22: bloxroute_message_factory
    }

    def __init__(self) -> None:
        super(_BloxrouteVersionManager, self).__init__()
        self.protocol_to_factory_mapping = self._PROTOCOL_TO_FACTORY_MAPPING
        self.protocol_to_converter_factory_mapping = self._PROTOCOL_TO_CONVERTER_FACTORY_MAPPING
        self.version_message_command = BloxrouteMessageType.HELLO


bloxroute_version_manager = _BloxrouteVersionManager()
