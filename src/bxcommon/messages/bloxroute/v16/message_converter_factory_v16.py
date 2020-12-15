from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v16.bdn_performance_stats_message_converter_v16 import \
    bdn_performance_stats_message_converter_v16
from bxcommon.messages.bloxroute.v17.message_converter_factory_v17 import message_converter_factory_v17
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV16(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        # pylint: disable=protected-access
        **message_converter_factory_v17._MESSAGE_CONVERTER_MAPPING,
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: bdn_performance_stats_message_converter_v16,
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v16 = _MessageConverterFactoryV16()
