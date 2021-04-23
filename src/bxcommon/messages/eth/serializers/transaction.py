from typing import Optional, Dict, Any, List

import blxr_rlp as rlp

from bxcommon.messages.eth.serializers.transaction_type import EthTransactionType
from bxcommon.messages.eth.serializers.unsigned_transaction import UnsignedTransaction
from bxcommon.utils import convert
from bxcommon.utils.blockchain_utils.eth import eth_common_utils, eth_common_constants, crypto_utils
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import utils


# pyre-fixme[13]: Attribute `address` is never initialized.
# pyre-fixme[13]: Attribute `storage_keys` is never initialized.
class AccessedAddress(rlp.Serializable):
    fields = [
        (
            "address",
            rlp.sedes.Binary.fixed_length(eth_common_constants.ADDRESS_LEN, allow_empty=True),
        ),
        ("storage_keys", rlp.sedes.CountableList(rlp.sedes.binary)),
    ]

    address: bytearray
    storage_keys: List[bytearray]

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "AccessedAddress":
        return AccessedAddress(
            utils.or_else(
                utils.optional_map(payload["address"], lambda addr: convert.hex_to_bytes(addr[2:])),
                bytes(),
            ),
            [
                utils.optional_map(key, lambda k: convert.hex_to_bytes(k[2:]))
                for key in payload["storageKeys"]
            ],
        )


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
    """
    Some notes on the Berlin implementation details:
    (see https://eips.ethereum.org/EIPS/eip-2718 for spec)

    Transaction can either be an RLP encoded list of all transaction attributes
    (e.g. `[nonce, gas_price, start_gas, ..., v, r, s]`), or an opaque byte string
    consisting of `"[transaction_type][nonce, gas_price, start_gas, ...]"`.

    As a result, `Transaction.serialize/deserialize` can return either the
    RLP list or the opaque byte string, and this can be confusing to work with.
    As a rule of thumb, LegacyTransactions will need to call `rlp.encode` to
    get the transaction byte representation for purposes such as calculating its
    hash, while new transaction should not, as that will result in double encoding.

    It's possible for LegacyTransaction to be in either representation. In our
    implementation, we currently choose to always serialize LegacyTransaction in
    the original, first representations, since this is easier on test cases to
    ensure we have a mix of old and new transactions in blocks. However, this
    code is capable of understanding LegacyTransaction in either format.
    """

    transaction_type: EthTransactionType = EthTransactionType.LEGACY

    nonce: int
    gas_price: int
    start_gas: int
    to: Optional[bytearray]
    value: int
    data: bytearray
    v: int
    r: int
    s: int

    @classmethod
    def serialize(cls, obj, type_parsed: bool = False, **kwargs):
        if type_parsed:
            result = super().serialize(obj)
            if obj.transaction_type == EthTransactionType.LEGACY:
                return result
            return obj.transaction_type.encode_rlp() + rlp.encode(result)
        else:
            return obj.__class__.serialize(obj, type_parsed=True, **kwargs)

    @classmethod
    def deserialize(cls, serial, type_parsed: bool = False, **extra_kwargs):
        if type_parsed:
            return super().deserialize(serial, **extra_kwargs)

        if isinstance(serial, (list, tuple)):
            return LegacyTransaction.deserialize(serial, type_parsed=True, **extra_kwargs)

        if isinstance(serial, memoryview):
            serial = serial.tobytes()

        if isinstance(serial, bytes):
            transaction_flag = serial[0]
            if transaction_flag <= eth_common_constants.MAX_TRANSACTION_TYPE:
                transaction_type = EthTransactionType(serial[0])
                payload = rlp.decode(serial[1:])
            else:
                payload = rlp.decode(serial)
                transaction_type = EthTransactionType.LEGACY

            if transaction_type == EthTransactionType.LEGACY:
                return LegacyTransaction.deserialize(payload, type_parsed=True, **extra_kwargs)
            elif transaction_type == EthTransactionType.ACCESS_LIST:
                return AccessListTransaction.deserialize(payload, type_parsed=True, **extra_kwargs)
        raise ValueError(f"Unexpected serial type: {type(serial)}")

    def hash(self) -> Sha256Hash:
        pass

    def contents(self) -> memoryview:
        return memoryview(rlp.encode(self))

    def is_eip_155_signed(self) -> bool:
        return self.v >= eth_common_constants.EIP155_CHAIN_ID_OFFSET

    def chain_id(self) -> int:
        if self.v % 2 == 0:
            v = self.v - 1
        else:
            v = self.v
        return (v - eth_common_constants.EIP155_CHAIN_ID_OFFSET) // 2

    def signature(self) -> bytes:
        return crypto_utils.encode_signature(self.v, self.r, self.s)

    def get_unsigned(self) -> bytes:
        pass

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

        serialized_output = {
            "from": self.from_address(),
            "gas": hex(self.start_gas),
            "gas_price": hex(self.gas_price),
            "hash": f"0x{str(message_hash)}",
            "input": input_data,
            "nonce": hex(self.nonce),
            "value": hex(self.value),
            "v": hex(self.v),
            "r": hex(self.r),
            "s": hex(self.s),
            "type": f"0x{self.transaction_type.value}",
        }

        to = self.to
        if to is not None:
            serialized_output["to"] = convert.bytes_to_hex_string_format(to)

        return serialized_output

    def from_address(self) -> str:
        from_key = crypto_utils.recover_public_key(
            self.get_unsigned(), self.signature(), eth_common_utils.keccak_hash
        )
        from_address = crypto_utils.public_key_to_address(from_key)
        return convert.bytes_to_hex_string_format(from_address)

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "Transaction":

        transaction_cls = LegacyTransaction

        try:
            transaction_type = EthTransactionType(int(payload.get("type", "0x0"), 16))
            if transaction_type == EthTransactionType.ACCESS_LIST:
                transaction_cls = AccessListTransaction
        except ValueError:
            # assume legacy transaction if transaction_type access fails
            pass

        return transaction_cls.from_json(payload)

    @classmethod
    def from_json_with_validation(cls, payload: Dict[str, Any]) -> "Transaction":
        """
        create a Transaction from a payload dict.
        this method support a less strict payload. and support input in both the Eth format and our own.
        """
        if "gas_price" in payload:
            payload["gasPrice"] = payload["gas_price"]
        if "access_list" in payload:
            payload["accessList"] = payload["access_list"]
        if "chain_id" in payload:
            payload["chainId"] = payload["chain_id"]

        for item in ["nonce", "gasPrice", "gas", "value", "v", "r", "s"]:
            value = payload[item]
            if isinstance(value, int):
                payload[item] = hex(value)

        for item in ["accessList", "chainId"]:
            if item in payload:
                value = payload[item]
                if isinstance(value, int):
                    payload[item] = hex(value)

        return cls.from_json(payload)


class LegacyTransaction(Transaction):
    transaction_type: EthTransactionType = EthTransactionType.LEGACY

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

    def hash(self):
        hash_bytes = eth_common_utils.keccak_hash(rlp.encode(self))
        return Sha256Hash(hash_bytes)

    def get_unsigned(self) -> bytes:
        """
        Returns unsigned transaction.

        EIP-155 protected transactions require the chain ID encoded in the v
        field, and the r/s fields to be empty.
        :return:
        """
        if self.is_eip_155_signed():
            parts = rlp.decode(rlp.encode(Transaction.serialize(self)))
            parts_for_signing = parts[:-3] + [
                eth_common_utils.int_to_big_endian(self.chain_id()),
                b"",
                b"",
            ]
            return rlp.encode(parts_for_signing)
        else:
            return rlp.encode(
                UnsignedTransaction(
                    self.nonce, self.gas_price, self.start_gas, self.to, self.value, self.data
                )
            )

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "Transaction":
        return LegacyTransaction(
            int(payload["nonce"], 16),
            int(payload["gasPrice"], 16),
            int(payload["gas"], 16),
            utils.or_else(
                utils.optional_map(payload["to"], lambda to: convert.hex_to_bytes(to[2:])), bytes()
            ),
            int(payload["value"], 16),
            convert.hex_to_bytes(payload["input"][2:]),
            int(payload["v"], 16),
            int(payload["r"], 16),
            int(payload["s"], 16),
        )


# pyre-fixme[13]: Attribute `_chain_id` is never initialized.
# pyre-fixme[13]: Attribute `access_list` is never initialized.
class AccessListTransaction(Transaction):
    transaction_type: EthTransactionType = EthTransactionType.ACCESS_LIST

    fields = [
        ("_chain_id", rlp.sedes.big_endian_int),
        ("nonce", rlp.sedes.big_endian_int),
        ("gas_price", rlp.sedes.big_endian_int),
        ("start_gas", rlp.sedes.big_endian_int),
        ("to", rlp.sedes.Binary.fixed_length(eth_common_constants.ADDRESS_LEN, allow_empty=True)),
        ("value", rlp.sedes.big_endian_int),
        ("data", rlp.sedes.binary),
        ("access_list", rlp.sedes.CountableList(AccessedAddress)),
        ("v", rlp.sedes.big_endian_int),
        ("r", rlp.sedes.big_endian_int),
        ("s", rlp.sedes.big_endian_int),
    ]

    _chain_id: int
    access_list: List[AccessedAddress]

    def hash(self):
        hash_bytes = eth_common_utils.keccak_hash(Transaction.serialize(self))
        return Sha256Hash(hash_bytes)

    def chain_id(self) -> int:
        return self._chain_id

    def get_unsigned(self) -> bytes:
        """
        Returns unsigned transaction. EIP-2930 transaction are always EIP-155
        protected. They do not require any of the v/r/s values included.
        :return:
        """

        parts = rlp.decode(Transaction.serialize(self)[1:])
        return EthTransactionType.ACCESS_LIST.encode_rlp() + rlp.encode(parts[:-3])

    def signature(self) -> bytes:
        return crypto_utils.encode_signature_y_parity(self.v, self.r, self.s)

    def to_json(self) -> Dict[str, Any]:
        serialized_transaction = super().to_json()
        serialized_transaction["chain_id"] = f"0x{self.chain_id()}"

        access_list = self.access_list
        accessed_addresses = []
        for accessed_address in access_list:
            accessed_addresses.append(
                {
                    "address": convert.bytes_to_hex_string_format(accessed_address.address),
                    "storage_keys": [
                        convert.bytes_to_hex_string_format(key)
                        for key in accessed_address.storage_keys
                    ],
                }
            )

        serialized_transaction["access_list"] = accessed_addresses
        return serialized_transaction

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "Transaction":
        return AccessListTransaction(
            int(payload["chainId"], 16),
            int(payload["nonce"], 16),
            int(payload["gasPrice"], 16),
            int(payload["gas"], 16),
            utils.or_else(
                utils.optional_map(payload["to"], lambda to: convert.hex_to_bytes(to[2:])), bytes()
            ),
            int(payload["value"], 16),
            convert.hex_to_bytes(payload["input"][2:]),
            [
                AccessedAddress.from_json(accessed_address)
                for accessed_address in payload["accessList"]
            ],
            int(payload["v"], 16),
            int(payload["r"], 16),
            int(payload["s"], 16),
        )
