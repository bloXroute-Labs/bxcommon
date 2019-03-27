import unittest
from bxcommon.utils.class_json_encoder import ClassJsonEncoder
import json
import random
from collections import defaultdict


class EncodedTestClass(object):

    def __init__(self, item=None):
        self.a = 1
        self.b = [2, 3]
        self.c = {"a": 6, "b": 7}
        self.item = item


class ClassJsonEncoderTest(unittest.TestCase):

    def test_encode_list(self):
        items = list(random.getrandbits(10) for _ in range(100))
        js = json.dumps(items)
        self.assertEqual(js, json.dumps(items, cls=ClassJsonEncoder))

    def test_encode_dict(self):
        d = {"a": 1, b"b": 2}
        ref_d = {"a": 1, "b": 2}
        self.assertEqual(json.dumps(ref_d), json.dumps(d, cls=ClassJsonEncoder))

    def test_encode_default_dict(self):
        d = defaultdict(int)
        d.update({"a": 1, b"b": 2})
        ref_d = {"a": 1, "b": 2}
        self.assertEqual(json.dumps(ref_d), json.dumps(d, cls=ClassJsonEncoder))

    def test_encode_dicts_list(self):
        items = [{"a": 1, "b": 2}, {"c": 3, "d": 4}]
        self.assertEqual(json.dumps(items), json.dumps(items, cls=ClassJsonEncoder))

    def test_encode_lists_dict(self):
        d = {"a": [1, 2], "b": [3, 4]}
        self.assertEqual(json.dumps(d), json.dumps(d, cls=ClassJsonEncoder))

    def test_encode_dicts_dict(self):
        d = {"d1": {"a": [1, 2], "b": [3, 4]}, "d2": {b"c": [5, 6], b"d": [7, 8]}}
        ref_d = {"d1": {"a": [1, 2], "b": [3, 4]}, "d2": {"c": [5, 6], "d": [7, 8]}}
        self.assertEqual(json.dumps(ref_d), json.dumps(d, cls=ClassJsonEncoder))

    def test_encode_object(self):
        obj = EncodedTestClass()
        self.assertEqual(json.dumps(obj.__dict__), json.dumps(obj, cls=ClassJsonEncoder))

    def test_encode_nested_object(self):
        nested = EncodedTestClass()
        obj = EncodedTestClass(nested)
        ref_obj = EncodedTestClass(nested.__dict__)
        self.assertEqual(json.dumps(ref_obj.__dict__), json.dumps(obj, cls=ClassJsonEncoder))

    def test_encode_nested_dict_object(self):
        nested = EncodedTestClass()
        obj = EncodedTestClass({b"a": nested})
        ref_obj = EncodedTestClass({"a": nested.__dict__})
        self.assertEqual(json.dumps(ref_obj.__dict__), json.dumps(obj, cls=ClassJsonEncoder))

    def test_encode_nested_objects_list(self):
        nested_obj_list = [EncodedTestClass({str(i).encode("utf-8"): [1, 2, 3, 4]}) for i in range(5)]
        ref_nested_list = [obj.__dict__.copy() for obj in nested_obj_list]
        for ref in ref_nested_list:
            ref["item"] = {key.decode("utf-8"): val for key, val in ref["item"].items()}
        obj = EncodedTestClass(nested_obj_list)
        ref_obj = EncodedTestClass(ref_nested_list)
        self.assertEqual(json.dumps(ref_obj.__dict__), json.dumps(obj, cls=ClassJsonEncoder))

    def test_encode_iterable(self):
        gen = (random.getrandbits(10) for _ in range(100))
        items = list(gen)
        gen = (item for item in items)
        self.assertEqual(json.dumps(items), json.dumps(gen, cls=ClassJsonEncoder))

    def test_encode_class_object(self):

        self.assertEqual(
            json.dumps(EncodedTestClass().__dict__),
            json.dumps(EncodedTestClass(), cls=ClassJsonEncoder)
        )

    def test_encode_byte_array(self):
        ba = bytearray(b"hello world")
        self.assertEqual(json.dumps(ba.decode("utf-8")), json.dumps(ba, cls=ClassJsonEncoder))

    def test_encode_memory_view(self):
        b = b"hello world"
        mv = memoryview(b)
        self.assertEqual(json.dumps(b.decode("utf-8")), json.dumps(mv, cls=ClassJsonEncoder))