from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_factory import _BloxrouteMessageFactory
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.disconnect_relay_peer_message import DisconnectRelayPeerMessage
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


class DisconnectRelayTest(AbstractTestCase):
    def setUp(self):
        self.message_factory = _BloxrouteMessageFactory()
        self.message_factory._MESSAGE_TYPE_MAPPING = {
            BloxrouteMessageType.DISCONNECT_RELAY_PEER: DisconnectRelayPeerMessage
        }

    def test_message(self):
        msg = DisconnectRelayPeerMessage()

        self.assertTrue(msg)
        self.assertEqual(msg.msg_type(), BloxrouteMessageType.DISCONNECT_RELAY_PEER)
        self.assertEqual(msg.payload_len(), constants.CONTROL_FLAGS_LEN)

        msg_bytes = msg.rawbytes()
        self.assertTrue(msg_bytes)

        parsed_message = self.message_factory.create_message_from_buffer(msg_bytes)

        self.assertIsInstance(parsed_message, DisconnectRelayPeerMessage)

        self.assertEqual(parsed_message.msg_type(), BloxrouteMessageType.DISCONNECT_RELAY_PEER)
        self.assertEqual(parsed_message.payload_len(), constants.CONTROL_FLAGS_LEN)
