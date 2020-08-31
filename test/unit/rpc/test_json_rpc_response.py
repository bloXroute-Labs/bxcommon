from bxcommon.rpc.json_rpc_request import JsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.rpc_errors import RpcInvalidParams, RpcError
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxutils.encoding.json_encoder import Case


class JsonRpcResponseTest(AbstractTestCase):

    def test_serialize_deserialize_result(self):
        rpc_response = JsonRpcResponse(
            "1", "result", None
        )

        serialized = rpc_response.to_jsons()
        deserialized = JsonRpcResponse.from_jsons(serialized)

        self.assertEqual(rpc_response.id, deserialized.id)
        self.assertEqual(rpc_response.result, deserialized.result)
        self.assertEqual(rpc_response.error, deserialized.error)

    def test_serialize_deserialize_error(self):
        rpc_response = JsonRpcResponse(
            "1", None, RpcInvalidParams("1", "bad message")
        )

        serialized = rpc_response.to_jsons()
        deserialized = JsonRpcResponse.from_jsons(serialized)

        self.assertEqual(rpc_response.id, deserialized.id)
        self.assertEqual(rpc_response.result, deserialized.result)

        self.assertNotEqual(rpc_response.error, deserialized.error)
        self.assertIsInstance(deserialized.error, RpcError)
        self.assertEqual(rpc_response.error.code, deserialized.error.code)
        self.assertEqual(rpc_response.error.message, deserialized.error.message)
        self.assertEqual(rpc_response.error.data, deserialized.error.data)

    def test_serialize_error_rpc_notification(self):
        rpc_notification = JsonRpcRequest(None, "sub", ["subid", {}])
        with self.assertRaises(ValueError):
            JsonRpcResponse.from_json(rpc_notification.to_json())

    def test_serialize_to_camelCase(self):
        result = {
            "field_name": "foo",
            "otherFieldName": "bar",
            "nested_field": {
                "nested_field_name": "baz"
            }
        }
        rpc_response = JsonRpcResponse("1", result, None)
        json_serialized = rpc_response.to_json(Case.CAMEL)
        self.assertEqual("foo", json_serialized["result"]["fieldName"])
        self.assertEqual("bar", json_serialized["result"]["otherFieldName"])
        self.assertEqual("baz", json_serialized["result"]["nestedField"]["nestedFieldName"])

        simple_rpc_response = JsonRpcResponse("1", "foo", None)
        simple_json = simple_rpc_response.to_json(Case.CAMEL)
        self.assertEqual("foo", simple_json["result"])
