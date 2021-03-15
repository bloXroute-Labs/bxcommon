from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v20.tx_message_converter_v20 import tx_message_converter_v20
from bxcommon.messages.bloxroute.v21.message_converter_factory_v21 import message_converter_factory_v21
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV20(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        # pylint: disable=protected-access
        **message_converter_factory_v21._MESSAGE_CONVERTER_MAPPING,
        BloxrouteMessageType.TRANSACTION: tx_message_converter_v20,
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v20 = _MessageConverterFactoryV20()
