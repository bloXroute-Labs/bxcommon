import datetime
import time
from typing import Any
from unittest.mock import MagicMock

from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.transaction_status_rpc_request import TransactionStatusRpcRequest
from bxcommon.rpc.rpc_errors import RpcInvalidParams
from bxcommon.rpc.rpc_request_type import RpcRequestType
from bxcommon.test_utils import helpers
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import async_test
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.utils import convert
from bxcommon.utils.object_hash import Sha256Hash


class TransactionStatusRpcRequestTest(AbstractTestCase):

    def setUp(self) -> None:
        self.node = MockNode(helpers.get_common_opts(1000))

    async def _process_request(self, params: Any) -> JsonRpcResponse:
        rpc_request = BxJsonRpcRequest("1", RpcRequestType.TX_STATUS, params)
        request_handler = TransactionStatusRpcRequest(rpc_request, self.node)
        return await request_handler.process_request()

    @async_test
    async def test_invalid_params(self):
        with self.assertRaises(RpcInvalidParams):
            await self._process_request([])

        with self.assertRaises(RpcInvalidParams):
            await self._process_request(123)

        with self.assertRaises(RpcInvalidParams):
            await self._process_request({"foo": "bar"})

        with self.assertRaises(RpcInvalidParams):
            await self._process_request({"transaction_hash": "not a hash"})

    @async_test
    async def test_unknown_transaction(self):
        response = await self._process_request(
            {"transaction_hash": convert.bytes_to_hex(helpers.generate_hash())}
        )

        self.assertIsNone(response.error)
        self.assertEqual("unknown", response.result["status"])
        self.assertEqual([], response.result["short_ids"])
        self.assertEqual("n/a", response.result["assignment_time"])

    @async_test
    async def test_transaction_no_short_id(self):
        transaction_hash = helpers.generate_object_hash()
        transaction_contents = helpers.generate_bytearray(250)

        self.node.get_tx_service().set_transaction_contents(transaction_hash, transaction_contents)

        response = await self._process_request(
            {"transaction_hash": convert.bytes_to_hex(transaction_hash.binary)}
        )

        self.assertIsNone(response.error)
        self.assertEqual("pending short ID", response.result["status"])
        self.assertEqual([], response.result["short_ids"])
        self.assertEqual("n/a", response.result["assignment_time"])

    @async_test
    async def test_transaction_short_id(self):
        time.time = MagicMock(return_value=time.time())
        expected_assignment_time = datetime.datetime.fromtimestamp(time.time()).isoformat()

        short_id = 123
        transaction_hash = helpers.generate_object_hash()
        transaction_contents = helpers.generate_bytearray(250)

        tx_service = self.node.get_tx_service()
        tx_service.set_transaction_contents(transaction_hash, transaction_contents)
        tx_service.assign_short_id(transaction_hash, short_id)

        response = await self._process_request(
            {"transaction_hash": convert.bytes_to_hex(transaction_hash.binary)}
        )

        self.assertIsNone(response.error)
        self.assertEqual("assigned short ID", response.result["status"])
        self.assertEqual({123}, response.result["short_ids"])
        self.assertEqual(expected_assignment_time, response.result["assignment_time"])

    @async_test
    async def test_transaction_multiple_short_id(self):
        short_id_1 = 123
        short_id_2 = 124
        transaction_hash = helpers.generate_object_hash()
        transaction_contents = helpers.generate_bytearray(250)

        tx_service = self.node.get_tx_service()
        tx_service.set_transaction_contents(transaction_hash, transaction_contents)
        tx_service.assign_short_id(transaction_hash, short_id_1)

        time.time = MagicMock(return_value=time.time() + 5)
        expected_assignment_time = datetime.datetime.fromtimestamp(time.time()).isoformat()
        tx_service.assign_short_id(transaction_hash, short_id_2)

        response = await self._process_request(
            {"transaction_hash": f"0x{convert.bytes_to_hex(transaction_hash.binary)}"}
        )

        self.assertIsNone(response.error)
        self.assertEqual("assigned short ID", response.result["status"])
        self.assertEqual({123, 124}, response.result["short_ids"])
        self.assertEqual(expected_assignment_time, response.result["assignment_time"])

    @async_test
    async def test_sanitizes_0x(self):
        transaction_hash_normal = "0000579c2492a4a4b168a0da2d01a076649adef13ace238dcb81289aca532184"
        transaction_hash_0x = "0x0000579c2492a4a4b168a0da2d01a076649adef13ace238dcb81289aca532184"
        transaction_hash_object = Sha256Hash(convert.hex_to_bytes(transaction_hash_normal))

        tx_service = self.node.get_tx_service()
        tx_service.set_transaction_contents(
            transaction_hash_object, helpers.generate_bytearray(250)
        )

        response_normal = await self._process_request(
            {"transaction_hash": transaction_hash_normal}
        )
        self.assertEqual("pending short ID", response_normal.result["status"])

        response_0x = await self._process_request(
            {"transaction_hash": transaction_hash_0x}
        )
        self.assertEqual("pending short ID", response_0x.result["status"])
