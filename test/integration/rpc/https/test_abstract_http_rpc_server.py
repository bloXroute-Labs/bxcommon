import json
from typing import Any

from aiohttp import ClientSession, ClientResponse
from aiohttp.web_request import Request

from bxcommon import constants
from bxcommon.rpc import rpc_constants
from bxcommon.rpc.https.abstract_http_rpc_server import AbstractHttpRpcServer
from bxcommon.rpc.https.http_rpc_handler import HttpRpcHandler
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_errors import RpcInvalidParams, RpcErrorCode
from bxcommon.rpc.rpc_request_type import RpcRequestType
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import async_test
from bxcommon.test_utils.mocks.mock_node import MockNode


class RpcRequest(AbstractRpcRequest):

    def validate_params(self) -> None:
        params = self.params
        if not isinstance(params, dict):
            raise RpcInvalidParams(self.request_id, "Must be dict param")

    async def process_request(self) -> JsonRpcResponse:
        params = self.params
        if "crash" in params:
            raise Exception("boom!")

        return self.ok(
            {
                "foo": "bar"
            }
        )


class HttpRpcHandlerImpl(HttpRpcHandler):
    def __init__(self, node):
        super().__init__(node)
        self.request_handlers = {
            RpcRequestType.PING: RpcRequest
        }


class HttpRpcServer(AbstractHttpRpcServer):
    def authenticate_request(self, request: Request) -> None:
        pass

    def request_handler(self) -> HttpRpcHandler:
        return HttpRpcHandlerImpl(self.node)


class AbstractHttpRpcServerTest(AbstractTestCase):
    @async_test
    async def setUp(self) -> None:
        self.rpc_port = 8001
        self.rpc_url = f"http://{constants.LOCALHOST}:{self.rpc_port}"
        self.node = MockNode(
            helpers.get_common_opts(8000, rpc_port=self.rpc_port)
        )
        self.rpc_server = HttpRpcServer(self.node)
        await self.rpc_server.start()

    @async_test
    async def test_server_process_handler_success(self):
        json_data = {
            "method": RpcRequestType.PING.name.lower(),
            "id": 1,
            "params": {}
        }
        result = await self.post(json_data)
        self.assertEqual(200, result.status)
        expected_result = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "foo": "bar"
            }
        }
        result = await result.json()
        self.assertEqual(expected_result, json.loads(result))

    @async_test
    async def test_server_malformed_json(self):
        result = await self.post("{'foo':")
        self.assertEqual(400, result.status)
        expected_result = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": RpcErrorCode.PARSE_ERROR.value,
                "message": "Parse error"
            }
        }
        result = await result.json()
        self.assertEqual(expected_result, json.loads(result))

    @async_test
    async def test_server_method_not_found(self):
        json_data = {
            "method": "madeupmethod",
            "id": 1,
            "params": {}
        }
        result = await self.post(json_data)
        self.assertEqual(400, result.status)
        expected_result = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": RpcErrorCode.METHOD_NOT_FOUND.value,
                "message": "Method not found"
            }
        }
        result = json.loads(await result.json())
        self.assertEqual(expected_result["jsonrpc"], result["jsonrpc"])
        self.assertEqual(expected_result["id"], result["id"])
        self.assertEqual(expected_result["error"]["code"], result["error"]["code"])
        self.assertEqual(expected_result["error"]["message"], result["error"]["message"])

    @async_test
    async def test_server_no_method(self):
        json_data = {
            "id": 1,
            "params": {}
        }
        result = await self.post(json_data)
        self.assertEqual(400, result.status)
        expected_result = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": RpcErrorCode.METHOD_NOT_FOUND.value,
                "message": "Method not found"
            }
        }
        result = json.loads(await result.json())
        self.assertEqual(expected_result["jsonrpc"], result["jsonrpc"])
        self.assertEqual(expected_result["id"], result["id"])
        self.assertEqual(expected_result["error"]["code"], result["error"]["code"])
        self.assertEqual(expected_result["error"]["message"], result["error"]["message"])

    @async_test
    async def test_server_method_invalid_params(self):
        json_data = {
            "method": RpcRequestType.PING.name.lower(),
            "id": 1,
            "params": "foo"
        }
        result = await self.post(json_data)
        self.assertEqual(400, result.status)
        expected_result = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": RpcErrorCode.INVALID_PARAMS.value,
                "message": "Invalid params"
            }
        }
        result = json.loads(await result.json())
        self.assertEqual(expected_result["jsonrpc"], result["jsonrpc"])
        self.assertEqual(expected_result["id"], result["id"])
        self.assertEqual(expected_result["error"]["code"], result["error"]["code"])
        self.assertEqual(expected_result["error"]["code"], result["error"]["code"])
        self.assertEqual(expected_result["error"]["message"], result["error"]["message"])

    @async_test
    async def test_server_method_internal_error(self):
        json_data = {
            "method": RpcRequestType.PING.name.lower(),
            "id": 1,
            "params": {"crash": True}
        }
        result = await self.post(json_data)
        self.assertEqual(500, result.status)
        expected_result = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": RpcErrorCode.INTERNAL_ERROR.value,
                "message": "Internal error",
                "data": "boom!"
            }
        }
        result = json.loads(await result.json())
        self.assertEqual(expected_result["jsonrpc"], result["jsonrpc"])
        self.assertEqual(expected_result["id"], result["id"])
        self.assertEqual(expected_result["error"]["code"], result["error"]["code"])
        self.assertEqual(expected_result["error"]["message"], result["error"]["message"])
        self.assertEqual(expected_result["error"]["data"], result["error"]["data"])

    async def post(self, data: Any) -> ClientResponse:
        async with ClientSession() as session:
            async with session.post(
                self.rpc_url,
                data=json.dumps(data),
                headers={
                    rpc_constants.CONTENT_TYPE_HEADER_KEY: rpc_constants.PLAIN_HEADER_TYPE,
                }
            ) as response:
                # parse json body
                await response.json()
                return response

    @async_test
    async def tearDown(self) -> None:
        await self.rpc_server.stop()
