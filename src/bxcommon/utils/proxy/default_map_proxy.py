import typing
from bxcommon.utils.object_encoder import ObjectEncoder

TKeyRaw = typing.TypeVar("TKeyRaw")
TKeyEncoded = typing.TypeVar("TKeyEncoded")
TValueRaw = typing.TypeVar("TValueRaw")
TValueEncoded = typing.TypeVar("TValueEncoded")


class DefaultMapProxy(typing.Generic[TKeyRaw, TKeyEncoded, TValueRaw, TValueEncoded]):

    def __init__(
            self,
            map_obj: typing.Dict[TKeyRaw, TValueRaw],
            key_encoder: ObjectEncoder[TKeyRaw, TKeyEncoded],
            val_encoder: ObjectEncoder[TValueRaw, TValueEncoded]
    ):
        self._map_obj = map_obj
        self._key_encoder = key_encoder
        self._val_encoder = val_encoder
        if hasattr(self._map_obj, "__contains__"):
            self._contains = self._item_exists
        else:
            self._contains = self._item_exists_no_exception

    def __repr__(self):
        return self._map_obj.__repr__()

    def __str__(self) -> str:
        return self._map_obj.__str__()

    def __getitem__(self, key: TKeyEncoded) -> TValueEncoded:
        return self._val_encoder.encode(self._map_obj[self._key_encoder.decode(key)])

    def __len__(self) -> int:
        return len(self._map_obj)

    def __iter__(self) -> typing.Iterator[TKeyEncoded]:
        for key in self._map_obj:
            yield self._key_encoder.encode(key)

    def __delitem__(self, key: TKeyEncoded):
        del self._map_obj[self._key_encoder.decode(key)]

    def __contains__(self, key: TKeyEncoded) -> bool:
        return self._contains(key)

    def pop(self, key: TKeyEncoded) -> TValueEncoded:
        val = self.__getitem__(key)
        self.__delitem__(key)
        return val

    def get(
            self, key: TKeyEncoded, default: typing.Optional[TValueEncoded] = None
    ) -> typing.Optional[TValueEncoded]:
        if self._contains(key):
            return self.__getitem__(key)
        else:
            return default

    def popitem(self) -> typing.Tuple[TKeyEncoded, TValueEncoded]:
        key, val = next(iter(self.items()))
        self.__delitem__(key)
        return key, val

    def items(self) -> typing.Iterator[typing.Tuple[TKeyEncoded, TValueEncoded]]:
        for key, val in self._map_obj.items():
            yield self._key_encoder.encode(key), self._val_encoder.encode(val)

    def _item_exists_no_exception(self, key: TKeyEncoded) -> bool:
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def _item_exists(self, key: TKeyEncoded) -> bool:
        return self._key_encoder.decode(key) in self._map_obj
