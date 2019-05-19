import typing

TRaw = typing.TypeVar("TRaw")
TEncoded = typing.TypeVar("TEncoded")


class ObjectEncoder(typing.Generic[TRaw, TEncoded]):

    def __init__(
            self,
            encode: typing.Callable[[TRaw], TEncoded],
            decode: typing.Callable[[TEncoded], TRaw]
    ):
        self.encode = encode
        self.decode = decode

    @classmethod
    def raw_encoder(cls):
        return cls(lambda x: x, lambda x: x)
