from typing import Dict, Any, Optional

import blxr_rlp as rlp

from bxcommon.utils import convert
from bxcommon.utils.blockchain_utils.eth import eth_common_utils, crypto_utils, eth_common_constants
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.messages.eth.serializers.unsigned_transaction import UnsignedTransaction
from bxutils import utils


# pylint: disable=invalid-name
# pyre-fixme[13]: Attribute `data` is never initialized.
# pyre-fixme[13]: Attribute `gas_price` is never initialized.
# pyre-fixme[13]: Attribute `nonce` is never initialized.
# pyre-fixme[13]: Attribute `r` is never initialized.
# pyre-fixme[13]: Attribute `s` is never initialized.
# pyre-fixme[13]: Attribute `start_gas` is never initialized.
# pyre-fixme[13]: Attribute `to` is never initialized.
# pyre-fixme[13]: Attribute `v` is never initialized.
# pyre-fixme[13]: Attribute `value` is never initialized.
class Transaction(rlp.Serializable):
    fields = [
        ("nonce", rlp.sedes.big_endian_int),
        ("gas_price", rlp.sedes.big_endian_int),
        ("start_gas", rlp.sedes.big_endian_int),
        ("to", rlp.sedes.Binary.fixed_length(eth_common_constants.ADDRESS_LEN, allow_empty=True)),
        ("value", rlp.sedes.big_endian_int),
        ("data", rlp.sedes.binary),
        ("v", rlp.sedes.big_endian_int),
        ("r", rlp.sedes.big_endian_int),
        ("s", rlp.sedes.big_endian_int),
    ]

    nonce: int
    gas_price: int
    start_gas: int
    to: Optional[bytearray]
    value: int
    data: bytearray
    v: int
    r: int
    s: int

    def hash(self):
        """Transaction hash"""
        hash_bytes = eth_common_utils.keccak_hash(rlp.encode(self))
        return Sha256Hash(hash_bytes)

    def contents(self):
        return memoryview(rlp.encode(self))

    def is_eip_155_signed(self) -> bool:
        return self.v >= eth_common_constants.EIP155_CHAIN_ID_OFFSET

    def chain_id(self) -> int:
        if self.v % 2 == 0:
            v = self.v - 1
        else:
            v = self.v
        return (v - eth_common_constants.EIP155_CHAIN_ID_OFFSET) // 2

    def get_unsigned(self) -> bytes:
        if self.is_eip_155_signed():
            parts = rlp.decode(rlp.encode(self))
            parts_for_signing = parts[:-3] + [eth_common_utils.int_to_big_endian(self.chain_id()), b'', b'']
            return rlp.encode(parts_for_signing)
        else:
            return rlp.encode(
                UnsignedTransaction(
                    self.nonce,
                    self.gas_price,
                    self.start_gas,
                    self.to,
                    self.value,
                    self.data
                )
            )

    def to_json(self) -> Dict[str, Any]:
        """
        Serializes data to be close to Ethereum RPC spec for publishing to the transaction
        feed.

        see https://github.com/ethereum/wiki/wiki/JSON-RPC#eth_gettransactionbyhash

        Some fields are excluded, since they will never be populated by bxgateway.
        (mainly fields related to the block the transaction gets included in)
        - blockHash
        - blockNumber
        - transactionIndex
        """
        message_hash = self.hash()

        input_data = convert.bytes_to_hex(self.data)
        if not input_data:
            input_data = "0x"
        else:
            input_data = f"0x{input_data}"

        signature = crypto_utils.encode_signature(self.v, self.r, self.s)
        from_key = crypto_utils.recover_public_key(
            self.get_unsigned(), signature, eth_common_utils.keccak_hash
        )
        from_address = crypto_utils.public_key_to_address(from_key)
        serialized_output = {
            "from": convert.bytes_to_hex_string_format(from_address),
            "gas": hex(self.start_gas),
            "gas_price": hex(self.gas_price),
            "hash": f"0x{str(message_hash)}",
            "input": input_data,
            "nonce": hex(self.nonce),
            "value": hex(self.value),
            "v": hex(self.v),
            "r": hex(self.r),
            "s": hex(self.s)
        }

        to = self.to
        if to is not None:
            serialized_output["to"] = convert.bytes_to_hex_string_format(to)

        return serialized_output

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "Transaction":
        return cls(
            int(payload["nonce"], 16),
            int(payload["gasPrice"], 16),
            int(payload["gas"], 16),
            utils.or_else(
                utils.optional_map(
                    payload["to"],
                    lambda to: convert.hex_to_bytes(to[2:])
                ),
                bytes()
            ),
            int(payload["value"], 16),
            convert.hex_to_bytes(payload["input"][2:]),
            int(payload["v"], 16),
            int(payload["r"], 16),
            int(payload["s"], 16),
        )

    @classmethod
    def from_json_with_validation(cls, payload: Dict[str, Any]) -> "Transaction":
        """
        create a Transaction from a payload dict.
        this method support a less strict payload. and support input in both the Eth format and our own.

        """
        if "gas_price" in payload:
            payload["gasPrice"] = payload["gas_price"]
        for item in ["nonce", "gasPrice", "gas", "value", "v", "r", "s"]:
            value = payload[item]
            if isinstance(value, int):
                payload[item] = hex(value)
        return cls.from_json(payload)
