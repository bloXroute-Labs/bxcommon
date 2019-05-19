import unittest
from bxcommon.utils.proxy.map_proxy import MapProxy
from bxcommon.utils.object_encoder import ObjectEncoder


class MapProxyText(unittest.TestCase):

    def setUp(self):
        self._map_obj = {}
        self._encoder = ObjectEncoder(
            lambda raw: raw.decode("utf-8"), lambda decoded: decoded.encode("utf-8")
        )
        self._map = MapProxy(self._map_obj, self._encoder, self._encoder)

    def test_indexing(self):
        self._map["one"] = "1"
        self._map["two"] = "2"
        self.assertEqual(self._encoder.encode(self._map_obj[b"one"]), self._map["one"])
        self.assertEqual(self._encoder.encode(self._map_obj[b"two"]), self._map["two"])

    def test_del(self):
        key = "test key"
        val = "test val"
        self._map[key] = val
        self.assertEqual(self._map[key], val)
        del self._map[key]
        self.assertRaises(KeyError, self._map.__getitem__,  key)

    def test_in_map(self):
        key = "test key"
        val = "test val"
        self.assertFalse(key in self._map)
        self._map[key] = val
        self.assertTrue(key in self._map)
