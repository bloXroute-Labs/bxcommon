import typing
from bxcommon.utils.object_encoder import ObjectEncoder


TItemRaw = typing.TypeVar("TItemRaw")
TItemEncoded = typing.TypeVar("TItemEncoded")


class VectorProxy(typing.Generic[TItemRaw, TItemEncoded]):

    def __init__(
            self, vector: typing.List[TItemRaw], encoder: ObjectEncoder[TItemRaw, TItemEncoded]
    ):
        self.vector = vector
        self._encoder = encoder

    def __repr__(self):
        return self.vector.__repr__()

    def __str__(self) -> str:
        return self.vector.__str__()

    def __getitem__(self, idx: int) -> TItemEncoded:
        return self._encoder.encode(self.vector[idx])

    def __len__(self) -> int:
        return len(self.vector)

    def __iter__(self) -> typing.Iterator[TItemEncoded]:
        for item in self.vector:
            yield self._encoder.encode(item)

    def __delitem__(self, idx: int):
        del self.vector[idx]

    def pop(self, idx: int = -1) -> TItemEncoded:
        item = self.vector[idx]
        self.__delitem__(idx)
        return item

    def append(self, item: TItemEncoded):
        self.vector.append(self._encoder.decode(item))
