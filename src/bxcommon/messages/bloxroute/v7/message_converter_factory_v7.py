from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v7.tx_message_converter_v7 import \
    tx_message_converter_v7
from bxcommon.messages.bloxroute.v8.message_converter_factory_v8 import message_converter_factory_v8
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter
from bxcommon.messages.versioning.abstract_message_converter import AbstractMessageConverter


class _MessageConverterFactoryV7(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        # pylint: disable=protected-access
        **message_converter_factory_v8._MESSAGE_CONVERTER_MAPPING,
        BloxrouteMessageType.TRANSACTION: tx_message_converter_v7,
    }

    def get_message_converter(self, msg_type) -> AbstractMessageConverter:
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v7 = _MessageConverterFactoryV7()
