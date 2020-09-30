from enum import Enum


class BlockchainProtocol(Enum):
    BITCOIN = "bitcoin"
    BITCOINCASH = "bitcoincash"
    ETHEREUM = "ethereum"
    ONTOLOGY = "ontology"

    def __eq__(self, other) -> bool:
        return self is other or str(self) == str(other)

    def __str__(self) -> str:
        return str(self.value)

    def __hash__(self) -> int:
        return id(self)
