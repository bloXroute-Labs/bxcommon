from enum import Flag


class SerializableFlag(Flag):
    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, string_value: str):
        for item in cls:
            if string_value.upper() == str(item):
                return item

        raise ValueError("{0} is not a valid {1}".format(string_value, cls.__name__))
