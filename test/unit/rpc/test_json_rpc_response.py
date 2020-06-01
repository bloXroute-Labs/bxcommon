from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.rpc_errors import RpcInvalidParams, RpcError
from bxcommon.test_utils.abstract_test_case import AbstractTestCase


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
