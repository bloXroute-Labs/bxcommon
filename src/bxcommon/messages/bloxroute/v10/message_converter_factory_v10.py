from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v10.bdn_performance_stats_message_converter_v10 \
    import bdn_performance_stats_message_converter_v10
from bxcommon.messages.bloxroute.v11.message_converter_factory_v11 import message_converter_factory_v11
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV10(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        # pylint: disable=protected-access
        **message_converter_factory_v11._MESSAGE_CONVERTER_MAPPING,
        BloxrouteMessageType.BDN_PERFORMANCE_STATS: bdn_performance_stats_message_converter_v10,
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v10 = _MessageConverterFactoryV10()
