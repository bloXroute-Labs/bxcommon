from bxcommon.messages.bloxroute.v12.message_converter_factory_v12 import message_converter_factory_v12
from bxcommon.messages.versioning.abstract_version_converter_factory import AbstractMessageConverterFactory
from bxcommon.messages.versioning.no_changes_message_converter import no_changes_message_converter


class _MessageConverterFactoryV11(AbstractMessageConverterFactory):
    _MESSAGE_CONVERTER_MAPPING = {
        # pylint: disable=protected-access
        **message_converter_factory_v12._MESSAGE_CONVERTER_MAPPING,
    }

    def get_message_converter(self, msg_type):
        if not msg_type:
            raise ValueError("msg_type is required.")

        if msg_type not in self._MESSAGE_CONVERTER_MAPPING:
            return no_changes_message_converter

        return self._MESSAGE_CONVERTER_MAPPING[msg_type]


message_converter_factory_v11 = _MessageConverterFactoryV11()
