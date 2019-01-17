import struct

from bxcommon.utils import logger
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.message_buffer_builder import PayloadElement, PayloadBlock
from bxcommon.utils import uuid_pack


class PayloadBlockTests(AbstractTestCase):
    def setUp(self):
        self.MESSAGE_BLOCK_HDR = PayloadBlock(0, "HDR", 0,
                                              PayloadElement(name="msg_type", structure="<12s",),
                                              PayloadElement(name="payload_len", structure="<L",)
                                              )
        self.MESSAGE_BLOCK_VERSION = PayloadBlock(0, "VersionMessage", 0,
                                                  self.MESSAGE_BLOCK_HDR,
                                                  PayloadElement(structure="<L", name="protocol_version"),
                                                  PayloadElement(structure="<L", name="network_num")
                                                  )
        self.MESSAGE_BLOCK_HELLO = PayloadBlock(0, "HelloMessage", 3,
                                                self.MESSAGE_BLOCK_VERSION,
                                                PayloadElement(name="node_id", structure="<16s",
                                                               encode=lambda x: uuid_pack.to_bytes(x),
                                                               decode=lambda x: uuid_pack.from_bytes(x))
                                                )
        self.kwargs = {
            "node_id": "31f93bcc-ad56-431f-9c14-28ffb0e8e41a",
            "msg_type": "HelloMessage",
            "protocol_version": 3,
            "network_num": 12345
        }

    def test_hello_block_build_read(self):
        self.kwargs["payload_len"] = self.MESSAGE_BLOCK_HELLO.size - self.MESSAGE_BLOCK_HDR.size

        # build message
        buf = bytearray(self.MESSAGE_BLOCK_HELLO.size)
        self.MESSAGE_BLOCK_HELLO.build(buf=buf, **self.kwargs)

        # verify buffer
        msg_type, payload_len, protocol_version, network_num, node_id = struct.unpack_from("<12sLLL16s", buf)
        self.assertEqual(len(buf), self.MESSAGE_BLOCK_HELLO.size)
        self.assertEqual(msg_type, "HelloMessage")
        self.assertEqual(payload_len, 24)
        self.assertEqual(protocol_version, 3)
        self.assertEqual(network_num, 12345)
        self.assertEqual(uuid_pack.from_bytes(node_id), "31f93bcc-ad56-431f-9c14-28ffb0e8e41a")

        # verify read
        result = self.MESSAGE_BLOCK_HELLO.read(buf)
        for item in self.MESSAGE_BLOCK_HELLO:
            self.assertEqual(result.pop(item.name), self.kwargs.pop(item.name))
        self.assertFalse(self.kwargs)  # check that all inputs were matched to the outputs
        self.assertFalse(result)  # check that all outputs were matched to the inputs
