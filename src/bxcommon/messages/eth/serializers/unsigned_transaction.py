from typing import Optional

import blxr_rlp as rlp

from bxcommon.utils.blockchain_utils.eth import eth_common_constants


# pyre-fixme[13]: Attribute `data` is never initialized.
# pyre-fixme[13]: Attribute `gas_price` is never initialized.
# pyre-fixme[13]: Attribute `nonce` is never initialized.
# pyre-fixme[13]: Attribute `start_gas` is never initialized.
# pyre-fixme[13]: Attribute `to` is never initialized.
# pyre-fixme[13]: Attribute `value` is never initialized.
class UnsignedTransaction(rlp.Serializable):
    fields = [
        ("nonce", rlp.sedes.big_endian_int),
        ("gas_price", rlp.sedes.big_endian_int),
        ("start_gas", rlp.sedes.big_endian_int),
        ("to", rlp.sedes.Binary.fixed_length(eth_common_constants.ADDRESS_LEN, allow_empty=True)),
        ("value", rlp.sedes.big_endian_int),
        ("data", rlp.sedes.binary),
    ]

    nonce: int
    gas_price: int
    start_gas: int
    to: Optional[bytearray]
    value: int
    data: bytearray
