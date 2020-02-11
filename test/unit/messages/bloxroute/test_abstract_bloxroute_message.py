from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags


class TestAbstractBloxrouteMessage(AbstractTestCase):

    def test_asbstract_bloxroute_message(self):
        total_msg_len = 1000
        msg_type = b"dummy_msg"

        payload_len = total_msg_len - constants.BX_HDR_COMMON_OFF - constants.STARTING_SEQUENCE_BYTES_LEN
        buffer = bytearray(total_msg_len)
        message = AbstractBloxrouteMessage(msg_type=msg_type, payload_len=payload_len, buf=buffer)

        raw_bytes = message.rawbytes()
        self.assertEqual(total_msg_len, len(raw_bytes))
        self.assertEqual(msg_type, message.msg_type())
        self.assertEqual(payload_len, message.payload_len())
        self.assertEqual(payload_len, len(message.payload()))

        self.assertTrue(BloxrouteMessageControlFlags.VALID in BloxrouteMessageControlFlags(message.get_control_flags()))

        message.remove_control_flag(BloxrouteMessageControlFlags.VALID)
        self.assertFalse(BloxrouteMessageControlFlags.VALID in BloxrouteMessageControlFlags(message.get_control_flags()))

        message.set_control_flag(BloxrouteMessageControlFlags.VALID)
        self.assertTrue(BloxrouteMessageControlFlags.VALID in BloxrouteMessageControlFlags(message.get_control_flags()))

        # Trying set already set flag
        message.set_control_flag(BloxrouteMessageControlFlags.VALID)
        self.assertTrue(BloxrouteMessageControlFlags.VALID in BloxrouteMessageControlFlags(message.get_control_flags()))
