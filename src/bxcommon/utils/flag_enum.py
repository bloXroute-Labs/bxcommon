from typing import Dict, List, Optional, Tuple


class Flag:
    names_map: Optional[Dict["Flag", str]] = None
    last_used_bitwise_shift = 0

    def __init__(self, bitwise_shift_value: Optional[int] = None, value: Optional[int] = None):
        if bitwise_shift_value:
            self.value = 1 << bitwise_shift_value
        elif value:
            self.value = value
        else:
            self.__class__.last_used_bitwise_shift += 1
            self.value = 1 << self.__class__.last_used_bitwise_shift

    def __hash__(self):
        return hash(self.value)

    def __contains__(self, other: "Flag"):
        return other.value & self.value == other.value

    def __bool__(self):
        return bool(self.value)

    def __or__(self, other):
        return self.__class__(value=self.value | other.value)

    def __and__(self, other):
        return self.__class__(value=self.value & other.value)

    def __xor__(self, other):
        return self.__class__(value=self.value ^ other.value)

    def __invert__(self):
        return self.__class__(value=~self.value)

    def __str__(self):
        flags = self._decompose()
        return "|".join(map(lambda flag: self.names_map[flag], flags))

    def __repr__(self):
        return str(self)

    def _decompose(self) -> List["Flag"]:
        result = []

        names_map = self.names_map
        assert names_map is not None

        for flag in names_map:
            if flag in self:
                result.append(flag)

        return result


class FlagCollection:

    @classmethod
    def init(cls, item_class):
        if item_class.names_map is None:
            item_class.names_map = {}

            for item, name in cls._get_items_names():
                item_class.names_map[item] = name

    @classmethod
    def _get_items_names(cls) -> List[Tuple[Flag, str]]:
        results = []

        for attribute in dir(cls):
            if attribute in cls.__dict__:
                item = cls.__dict__[attribute]

                if isinstance(item, Flag):
                    results.append((item, attribute))

        return results
