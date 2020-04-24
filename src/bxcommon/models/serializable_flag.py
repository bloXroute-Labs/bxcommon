from enum import Flag
from functools import reduce


class SerializableFlag(Flag):
    def __str__(self):
        if self.name is not None:
            return str(self.name)
        else:
            return '|'.join([str(m.name) for m in self.__class__ if m in self])

    @classmethod
    def from_string(cls, string_value: str):
        string_values = {w.strip().upper() for w in str(string_value).split("|")}
        flag_elements = [item for item in cls if item.name in string_values]
        if flag_elements:
            return reduce(lambda x, y: x | y, flag_elements)
        raise ValueError("{0} is not a valid {1}".format(string_value, cls.__name__))
