from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v15.tx_message_converter_v15 import tx_message_converter_v15
from bxcommon.messages.bloxroute.v15.tx_sync_message_converter_v15 import tx_sync_message_converter_v15
from bxcommon.messages.bloxroute.v16.message_converter_factory_v16 import message_converter_factory_v16
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV15(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        # pylint: disable=protected-access
        **message_converter_factory_v16._MESSAGE_CONVERTER_MAPPING,
        BloxrouteMessageType.TRANSACTION: tx_message_converter_v15,
        BloxrouteMessageType.TX_SERVICE_SYNC_TXS: tx_sync_message_converter_v15,
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v15 = _MessageConverterFactoryV15()
