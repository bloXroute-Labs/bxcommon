import unittest

from bxcommon.utils.class_json_encoder import ClassJsonEncoder
from bxutils.encoding.json_encoder import EnhancedJSONEncoder
from bxcommon.utils import convert
import json
import random
from hashlib import sha256
import task_pool_executor as tpe
from collections import defaultdict
from bxcommon.utils.stats.stat_event_logic_flags import StatEventLogicFlags


class EncodedTestClass(object):

    def __init__(self, item=None):
        self.a = 1
        self.b = [2, 3]
        self.c = {"a": 6, "b": 7}
        self.item = item


class EnhancedJSONEncoderTest(unittest.TestCase):

    def test_encode_sha256(self):
        hash_ = "96e900d13d89eb12219e18ddc7aae8ec173a3cff196f09556b5d730df4a10732"
        items = [sha256(hash_.encode())]
        js = json.dumps(items, cls=EnhancedJSONEncoder)
        self.assertEqual(json.loads(js), [sha256(hash_.encode()).hexdigest()])

    def test_encode_sha256_tpe(self):
        hash_ = "96e900d13d89eb12219e18ddc7aae8ec173a3cff196f09556b5d730df4a10732"
        items = [tpe.Sha256(tpe.InputBytes(convert.hex_to_bytes(hash_)))]
        js = json.dumps(items, cls=EnhancedJSONEncoder)
        self.assertEqual(json.loads(js), [hash_])

    def test_encode_sha256(self):
        hash_ = "96e900d13d89eb12219e18ddc7aae8ec173a3cff196f09556b5d730df4a10732"
        items = [sha256(hash_.encode())]
        js = json.dumps(items, cls=ClassJsonEncoder)
        self.assertEqual(json.loads(js), [sha256(hash_.encode()).hexdigest()])

    def test_encode_sha256_tpe(self):
        hash_ = "96e900d13d89eb12219e18ddc7aae8ec173a3cff196f09556b5d730df4a10732"
        items = [tpe.Sha256(tpe.InputBytes(convert.hex_to_bytes(hash_)))]
        js = json.dumps(items, cls=ClassJsonEncoder)
        self.assertEqual(json.loads(js), [hash_])

    def test_encode_list(self):
        items = list(random.getrandbits(10) for _ in range(100))
        js = json.dumps(items)
        self.assertEqual(js, json.dumps(items, cls=EnhancedJSONEncoder))

    def test_encode_dict(self):
        d = {"a": 1, b"b": 2}
        ref_d = {"a": 1, "b": 2}
        self.assertEqual(json.dumps(ref_d), json.dumps(d, cls=EnhancedJSONEncoder))

    def test_encode_default_dict(self):
        d = defaultdict(int)
        d.update({"a": 1, b"b": 2})
        ref_d = {"a": 1, "b": 2}
        self.assertEqual(json.dumps(ref_d), json.dumps(d, cls=EnhancedJSONEncoder))

    def test_encode_dicts_list(self):
        items = [{"a": 1, "b": 2}, {"c": 3, "d": 4}]
        self.assertEqual(json.dumps(items), json.dumps(items, cls=EnhancedJSONEncoder))

    def test_encode_lists_dict(self):
        d = {"a": [1, 2], "b": [3, 4]}
        self.assertEqual(json.dumps(d), json.dumps(d, cls=EnhancedJSONEncoder))

    def test_encode_dicts_dict(self):
        d = {"d1": {"a": [1, 2], "b": [3, 4]}, "d2": {b"c": [5, 6], b"d": [7, 8]}}
        ref_d = {"d1": {"a": [1, 2], "b": [3, 4]}, "d2": {"c": [5, 6], "d": [7, 8]}}
        self.assertEqual(json.dumps(ref_d), json.dumps(d, cls=EnhancedJSONEncoder))

    def test_encode_object(self):
        obj = EncodedTestClass()
        self.assertEqual(json.dumps(obj.__dict__), json.dumps(obj, cls=EnhancedJSONEncoder))

    def test_encode_nested_object(self):
        nested = EncodedTestClass()
        obj = EncodedTestClass(nested)
        ref_obj = EncodedTestClass(nested.__dict__)
        self.assertEqual(json.dumps(ref_obj.__dict__), json.dumps(obj, cls=EnhancedJSONEncoder))

    def test_encode_nested_dict_object(self):
        nested = EncodedTestClass()
        obj = EncodedTestClass({b"a": nested})
        ref_obj = EncodedTestClass({"a": nested.__dict__})
        self.assertEqual(json.dumps(ref_obj.__dict__), json.dumps(obj, cls=EnhancedJSONEncoder))

    def test_encode_nested_objects_list(self):
        nested_obj_list = [EncodedTestClass({str(i).encode("utf-8"): [1, 2, 3, 4]}) for i in range(5)]
        ref_nested_list = [obj.__dict__.copy() for obj in nested_obj_list]
        for ref in ref_nested_list:
            ref["item"] = {key.decode("utf-8"): val for key, val in ref["item"].items()}
        obj = EncodedTestClass(nested_obj_list)
        ref_obj = EncodedTestClass(ref_nested_list)
        self.assertEqual(json.dumps(ref_obj.__dict__), json.dumps(obj, cls=EnhancedJSONEncoder))

    def test_encode_iterable(self):
        gen = (random.getrandbits(10) for _ in range(100))
        items = list(gen)
        gen = (item for item in items)
        self.assertEqual(json.dumps(items), json.dumps(gen, cls=EnhancedJSONEncoder))

    def test_encode_class_object(self):
        self.assertEqual(
            json.dumps(str(EncodedTestClass)),
            json.dumps(EncodedTestClass, cls=EnhancedJSONEncoder)
        )

    def test_encode_byte_array(self):
        ba = bytearray(b"hello world")
        self.assertEqual(json.dumps(ba.decode("utf-8")), json.dumps(ba, cls=EnhancedJSONEncoder))

    def test_encode_memory_view(self):
        b = b"hello world"
        mv = memoryview(b)
        self.assertEqual(json.dumps(b.decode("utf-8")), json.dumps(mv, cls=EnhancedJSONEncoder))

    def test_special_types(self):
        d = {"a": 1, "b": 2, "c": 3}
        values = d.values()
        keys = d.keys()
        self.assertEqual(json.dumps(list(values)), json.dumps(values, cls=EnhancedJSONEncoder))
        self.assertEqual(json.dumps(list(keys)), json.dumps(keys, cls=EnhancedJSONEncoder))

    def test_event_logic_flags(self):
        self.assertEqual(json.dumps(StatEventLogicFlags.SUMMARY, cls=EnhancedJSONEncoder),
                         json.dumps(str(StatEventLogicFlags.SUMMARY.value)))
        self.assertEqual(json.dumps(StatEventLogicFlags.SUMMARY | StatEventLogicFlags.BLOCK_INFO, cls=EnhancedJSONEncoder),
                         json.dumps(str((StatEventLogicFlags.SUMMARY | StatEventLogicFlags.BLOCK_INFO).value))
                         )
        self.assertEqual(json.dumps(StatEventLogicFlags.SUMMARY | StatEventLogicFlags.BLOCK_INFO, cls=EnhancedJSONEncoder),
                         json.dumps(str(5))
                         )
