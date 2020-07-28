from cryptography import utils
from cryptography.x509.extensions import UnrecognizedExtension

from bxutils.ssl.extensions.extensions_object_ids import ExtensionsObjectIds


class AccountIdExtension(UnrecognizedExtension):

    def __init__(self, account_id: str) -> None:
        super(AccountIdExtension, self).__init__(ExtensionsObjectIds.ACCOUNT_ID, account_id.encode("utf-8"))
        self._account_id = account_id

    account_id = utils.read_only_property("_account_id")

    def __repr__(self):
        return f"{self.__class__.__name__} <account_id: {self._account_id}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, AccountIdExtension):
            return NotImplemented

        return self._account_id == other._account_id

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return hash(self._account_id)
