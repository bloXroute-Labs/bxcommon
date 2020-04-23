from bxcommon.utils import convert
from bxcommon.utils.blockchain_utils.btc.btc_object_hash import BtcObjectHash
from bxcommon.utils.blockchain_utils.ont.ont_common_constants import ONT_HASH_LEN


class OntObjectHash(BtcObjectHash):
    def __repr__(self):
        return "OntObjectHash<binary: {}>".format(convert.bytes_to_hex(self.binary))


NULL_ONT_BLOCK_HASH = OntObjectHash(binary=bytearray(ONT_HASH_LEN))
