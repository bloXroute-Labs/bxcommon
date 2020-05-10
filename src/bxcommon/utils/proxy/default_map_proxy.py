from typing import TypeVar, Iterator, Generic, Dict, Optional, Tuple

from bxcommon.utils.object_encoder import ObjectEncoder

TKeyRaw = TypeVar("TKeyRaw")
TKeyEncoded = TypeVar("TKeyEncoded")
TValueRaw = TypeVar("TValueRaw")
TValueEncoded = TypeVar("TValueEncoded")


class DefaultMapProxy(Generic[TKeyRaw, TKeyEncoded, TValueRaw, TValueEncoded]):

    def __init__(
            self,
            map_obj: Dict[TKeyRaw, TValueRaw],
            key_encoder: ObjectEncoder[TKeyRaw, TKeyEncoded],
            val_encoder: ObjectEncoder[TValueRaw, TValueEncoded]
    ):
        self.map_obj = map_obj
        self._key_encoder = key_encoder
        self._val_encoder = val_encoder
        if hasattr(self.map_obj, "__contains__"):
            self._contains = self._item_exists
        else:
            self._contains = self._item_exists_no_exception

    def __repr__(self):
        return self.map_obj.__repr__()

    def __str__(self) -> str:
        return self.map_obj.__str__()

    def __getitem__(self, key: TKeyEncoded) -> TValueEncoded:
        return self._val_encoder.encode(self.map_obj[self._key_encoder.decode(key)])

    def __len__(self) -> int:
        return len(self.map_obj)

    def __iter__(self) -> Iterator[TKeyEncoded]:
        for key in self.map_obj:
            yield self._key_encoder.encode(key)

    def __delitem__(self, key: TKeyEncoded):
        del self.map_obj[self._key_encoder.decode(key)]

    def __contains__(self, key: TKeyEncoded) -> bool:
        return self._contains(key)

    def pop(self, key: TKeyEncoded) -> TValueEncoded:
        if hasattr(self.map_obj, "pop"):
            return self._val_encoder.encode(self.map_obj.pop(self._key_encoder.decode(key)))
        else:
            val = self.__getitem__(key)
            self.__delitem__(key)
            return val

    def get(
            self, key: TKeyEncoded, default: Optional[TValueEncoded] = None
    ) -> Optional[TValueEncoded]:
        if self._contains(key):
            return self.__getitem__(key)
        else:
            return default

    def popitem(self) -> Tuple[TKeyEncoded, TValueEncoded]:
        key, val = next(iter(self.items()))
        self.__delitem__(key)
        return key, val

    def items(self) -> Iterator[Tuple[TKeyEncoded, TValueEncoded]]:
        for key, val in self.map_obj.items():
            yield self._key_encoder.encode(key), self._val_encoder.encode(val)

    def keys(self) -> Iterator[TKeyEncoded]:
        return self.__iter__()

    def values(self) -> Iterator[TValueEncoded]:
        for _, value in self.items():
            yield value

    def clear(self) -> None:
        self.map_obj.clear()

    def _item_exists_no_exception(self, key: TKeyEncoded) -> bool:
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def _item_exists(self, key: TKeyEncoded) -> bool:
        return self._key_encoder.decode(key) in self.map_obj
