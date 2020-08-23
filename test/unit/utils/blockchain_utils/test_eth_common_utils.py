import unittest

from bxcommon.utils.blockchain_utils.eth import eth_common_utils


class TestEthCommonUtils(unittest.TestCase):

    def test_raw_tx_gas_price(self):
        tx_bytes = \
            b"\xf8k" \
            b"!" \
            b"\x85\x0b\xdf\xd6>\x00" \
            b"\x82R\x08\x94" \
            b"\xf8\x04O\xf8$\xc2\xdc\xe1t\xb4\xee\x9f\x95\x8c*s\x84\x83\x18\x9e" \
            b"\x87\t<\xaf\xacj\x80\x00\x80" \
            b"!" \
            b"\xa0-\xbf,\xa9+\xae\xabJ\x03\xcd\xfa\xe3<\xbf$\x00e\xe2N|\xc9\xf7\xe2\xa9\x9c>\xdfn\x0cO\xc0\x16" \
            b"\xa0)\x11K=;\x96X}a\xd5\x00\x06eSz\xd1,\xe4>\xa1\x8c\xf8\x7f>\x0e:\xd1\xcd\x00?'?"

        self.assertEqual(51000000000, eth_common_utils.raw_tx_gas_price(memoryview(tx_bytes), 0))

