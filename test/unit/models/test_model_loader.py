from dataclasses import dataclass
from typing import List, Dict, Optional, ForwardRef
from unittest import skip

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils import model_loader, convert
from bxcommon.utils.object_hash import Sha256Hash
from bxutils.encoding import json_encoder
from bxutils.encoding.json_encoder import Case


@dataclass
class BasicModel:
    foo: int
    bar: str
    baz: List[int]


@dataclass
class NestedModel:
    foo: int
    bar: List[BasicModel]
    baz: Dict[str, BasicModel]


@dataclass
class OtherModelWithLongNames:
    foo_bar_baz_qux: List[int]


@dataclass
class ModelWithLongNames:
    foo_bar_baz_qux: List[OtherModelWithLongNames]


@dataclass
class CustomParsedAttribute:
    foo: str

    @classmethod
    def from_string(cls, s: str) -> "CustomParsedAttribute":
        if s == "123":
            return cls("foobarbaz")
        else:
            return cls("qux")


@dataclass
class ModelWithCustomAttribute:
    attribute: CustomParsedAttribute


@dataclass
class HexadecimalModel:
    hash: Sha256Hash
    data: bytearray
    value: int


class ModelLoaderTest(AbstractTestCase):
    def test_basic_model(self):

        model_dict = {"foo": 1, "bar": "123", "baz": [1, 2, 3]}
        model_json = json_encoder.to_json(model_dict)

        dict_result = model_loader.load_model(BasicModel, model_dict)
        json_result = model_loader.load_model_from_json(BasicModel, model_json)

        self.assertEqual(dict_result, json_result)
        self.assertEqual(1, dict_result.foo)
        self.assertEqual("123", dict_result.bar)
        self.assertEqual([1, 2, 3], dict_result.baz)

    def test_nested_model(self):

        model_dict = {
            "foo": 1,
            "bar": [{"foo": 1, "bar": "123", "baz": [1, 2, 3]}, {"foo": 2, "bar": 234, "baz": [5]}],
            "baz": {"qux": {"foo": 12, "bar": "999", "baz": []}},
        }
        model_json = json_encoder.to_json(model_dict)

        dict_result = model_loader.load_model(NestedModel, model_dict)
        json_result = model_loader.load_model_from_json(NestedModel, model_json)

        self.assertEqual(dict_result, json_result)
        self.assertEqual(1, dict_result.foo)

        bar_field = dict_result.bar
        self.assertEqual(2, len(bar_field))
        self.assertEqual(1, bar_field[0].foo)
        self.assertEqual("123", bar_field[0].bar)
        self.assertEqual([1, 2, 3], bar_field[0].baz)

        baz_field = dict_result.baz
        self.assertEqual(1, len(baz_field))
        self.assertEqual(12, baz_field["qux"].foo)
        self.assertEqual("999", baz_field["qux"].bar)
        self.assertEqual([], baz_field["qux"].baz)

    def test_camel_case_model(self):
        model_dict_snake_case = {"foo_bar_baz_qux": [{"foo_bar_baz_qux": []}]}
        model_dict_camel_case = {"fooBarBazQux": [{"fooBarBazQux": []}]}
        snake_result = model_loader.load_model(ModelWithLongNames, model_dict_snake_case)
        camel_result = model_loader.load_model(
            ModelWithLongNames, model_dict_camel_case, Case.CAMEL
        )

        self.assertEqual(snake_result, camel_result)

    def test_loading_custom_parser(self):
        model_dict_1 = {
            "attribute": "123"
        }
        model_dict_2 = {
            "attribute": "000"
        }
        result_1 = model_loader.load_model(ModelWithCustomAttribute, model_dict_1)
        self.assertEqual("foobarbaz", result_1.attribute.foo)

        result_2 = model_loader.load_model(ModelWithCustomAttribute, model_dict_2)
        self.assertEqual("qux", result_2.attribute.foo)

    @skip
    def test_loading_hex_model(self):
        model_dict = {
            "hash": "0xdee4fc78545f68f2db6a538c887f8982bd37360b2986678c46f2ecf53e8b28d0",
            "data": "0xd883010914846765746888676f312e31342e37856c696e7578",
            "value": "0xbcb1d1"
        }
        result = model_loader.load_model(HexadecimalModel, model_dict)

        self.assertEqual(
            Sha256Hash(convert.hex_to_bytes(model_dict["hash"])),
            result.hash
        )
        self.assertEqual(convert.hex_to_bytes(model_dict["data"]), result.data)
        self.assertEqual(int(model_dict["value"], 16), result.value)
