import datetime
from typing import Optional

from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest, Node
from bxcommon.rpc.rpc_errors import RpcInvalidParams
from bxcommon.utils import convert
from bxcommon.utils.object_hash import Sha256Hash


TRANSACTION_HASH_KEY = "transaction_hash"
NETWORK_NUM_KEY = "network_num"


class TransactionStatusRpcRequest(AbstractRpcRequest[Node]):
    help = {
        "params": f"[Required - {TRANSACTION_HASH_KEY}: Transaction hash to check status of] ",
        "description": "Reports status of transaction: "
                       "time received, short id assigned, etc."
    }

    def __init__(self, request: BxJsonRpcRequest, node: Node):
        self.transaction_hash: Optional[Sha256Hash] = None
        self.network_num: Optional[int] = None

        super().__init__(request, node)

    def validate_params(self) -> None:
        params = self.params
        if not isinstance(params, dict):
            raise RpcInvalidParams(
                self.request_id,
                "Params request field is either missing or not a dictionary type."
            )

        if TRANSACTION_HASH_KEY not in params:
            raise RpcInvalidParams(
                self.request_id,
                "Transaction hash was missing from RPC params."
            )

        transaction_hash = params[TRANSACTION_HASH_KEY]
        if transaction_hash.startswith("0x"):
            transaction_hash = transaction_hash[2:]

        try:
            transaction_hash = Sha256Hash(convert.hex_to_bytes(transaction_hash))
        except Exception as _e:
            raise RpcInvalidParams(
                self.request_id,
                f"Invalid transaction hash: {transaction_hash}"
            )
        else:
            self.transaction_hash = transaction_hash

    async def process_request(self) -> JsonRpcResponse:
        transaction_hash = self.transaction_hash
        assert transaction_hash is not None

        transaction_service = self.node.get_tx_service(self.get_network_num())

        status = "unknown"
        short_ids = []
        assigned_time = "n/a"
        if transaction_service.has_transaction_contents(transaction_hash):
            status = "pending short ID"

        if transaction_service.has_transaction_short_id(transaction_hash):
            status = "assigned short ID"
            short_ids = transaction_service.get_short_ids(transaction_hash)
            most_recent_timestamp = max([
                transaction_service.get_short_id_assign_time(short_id)
                for short_id in short_ids
            ])
            assigned_time = datetime.datetime.fromtimestamp(most_recent_timestamp).isoformat()

        payload = {
            "status": status,
            "short_ids": short_ids,
            "assignment_time": assigned_time
        }
        return JsonRpcResponse(self.request_id, payload)

    def get_network_num(self) -> Optional[int]:
        return self.network_num
