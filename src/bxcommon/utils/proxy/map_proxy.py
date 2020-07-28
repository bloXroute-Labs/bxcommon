import typing

from bxcommon.utils.object_encoder import ObjectEncoder
from bxcommon.utils.proxy.default_map_proxy import DefaultMapProxy, TKeyRaw, TKeyEncoded, \
    TValueRaw, TValueEncoded


class MapProxy(DefaultMapProxy[TKeyRaw, TKeyEncoded, TValueRaw, TValueEncoded]):

    def __init__(
            self,
            map_obj: typing.Dict[TKeyRaw, TValueRaw],
            key_encoder: ObjectEncoder[TKeyRaw, TKeyEncoded],
            val_encoder: ObjectEncoder[TValueRaw, TValueEncoded]
    ):
        super(MapProxy, self).__init__(map_obj, key_encoder, val_encoder)

    def __setitem__(self, key: TKeyEncoded, value: TValueEncoded) -> None:
        self.map_obj[self._key_encoder.decode(key)] = self._val_encoder.decode(value)
