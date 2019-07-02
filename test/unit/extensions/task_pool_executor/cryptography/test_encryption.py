import unittest
import task_pool_executor as tpe
from bxcommon.utils.proxy import task_pool_proxy
from nacl.secret import SecretBox
from nacl.exceptions import CryptoError
from bxcommon.utils.convert import bytes_to_hex
from bxcommon.test_utils import helpers


def wait_for_task(tsk):
    while not tsk.is_completed():
        continue


def run_encryption(plain, et=None):
    if et is None:
        et = tpe.EncryptionTask(len(plain))
    plain_text = tpe.InputBytes(bytearray(plain))
    et.init(plain_text)
    task_pool_proxy.run_task(et)
    return et


class EncryptionTest(unittest.TestCase):

    def setUp(self):
        helpers.set_extensions_parallelism()

    def test_text_encryption(self):
        plain_text = b"test text encryption"
        et = run_encryption(plain_text)
        k = bytes(bytearray(et.key()))
        self.assertEqual(len(k), SecretBox.KEY_SIZE)
        self._check_end_result(et, plain_text)

    def test_reinitialization(self):
        plain1 = b"test reinitialization 1"
        et1 = run_encryption(plain1)
        key1 = bytearray(et1.key())
        plain2 = b"test reinitialization 2"
        et2 = run_encryption(plain2, et1)
        self.assertEqual(et2, et1)
        self.assertNotEqual(key1, bytearray(et2.key()))
        self._check_end_result(et2, plain2)

    def test_encrypt_bytes(self):
        plain = b"\x01 \x04 \x88 abcd"
        et = run_encryption(plain)
        self._check_end_result(et, plain)

    def test_encrypt_with_nulls(self):
        plain = b"test encrypt \x00 with nulls \x00"
        et = run_encryption(plain)
        self._check_end_result(et, plain)

    def _check_end_result(self, et, plain):
        k = bytes(bytearray(et.key()))
        c = bytes(bytearray(et.cipher()))
        try:
            self.assertEqual(SecretBox(k).decrypt(c), plain)
        except CryptoError as e:
            self.fail(
                "failed to decrypt cipher: {}, with key: {}, "
                "for plain: {}\n{}".format(
                    bytes_to_hex(c), bytes_to_hex(k), bytes_to_hex(plain), e
                )
             )

