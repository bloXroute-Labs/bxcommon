from typing import Iterable
from bxcommon.models.serializable_flag import SerializableFlag


class TxValidationStatus(SerializableFlag):
    """
    Flag used to track transaction validation

    IMPORTANT: Members with explicit values are also defined in extensions.
               Need to be changed in both places if changed here.
    """

    VALID_TX = 1 << 0
    INVALID_FORMAT = 1 << 1
    INVALID_SIGNATURE = 1 << 2
    LOW_FEE = 1 << 3
    REUSE_SENDER_NONCE = 1 << 4

    def __str__(self) -> str:
        # pylint: disable=using-constant-test
        if self.name:
            return str(self.name)
        else:
            return super().__str__()

    def get_subtypes(self) -> Iterable["TxValidationStatus"]:
        for subtype in self.__class__:
            if subtype in self:
                yield subtype
