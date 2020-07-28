from typing import List, TypeVar, Generic, Iterator

from bxcommon.utils.object_encoder import ObjectEncoder

TItemRaw = TypeVar("TItemRaw")
TItemEncoded = TypeVar("TItemEncoded")


class VectorProxy(Generic[TItemRaw, TItemEncoded]):

    def __init__(
            self, vector: List[TItemRaw], encoder: ObjectEncoder[TItemRaw, TItemEncoded]
    ):
        self.vector = vector
        self._encoder = encoder

    def __repr__(self) -> str:
        return self.vector.__repr__()

    def __str__(self) -> str:
        return self.vector.__str__()

    def __getitem__(self, idx: int) -> TItemEncoded:
        return self._encoder.encode(self.vector[idx])

    def __len__(self) -> int:
        return len(self.vector)

    def __iter__(self) -> Iterator[TItemEncoded]:
        for item in self.vector:
            yield self._encoder.encode(item)

    def __delitem__(self, idx: int) -> None:
        del self.vector[idx]

    def pop(self, idx: int = -1) -> TItemEncoded:
        item = self.vector[idx]
        self.__delitem__(idx)
        return self._encoder.encode(item)

    def append(self, item: TItemEncoded) -> None:
        self.vector.append(self._encoder.decode(item))
