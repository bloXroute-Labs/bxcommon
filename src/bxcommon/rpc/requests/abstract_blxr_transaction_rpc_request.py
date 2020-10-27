from abc import abstractmethod
from typing import Generic

from bxcommon.models.transaction_flag import TransactionFlag

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest, Node
from bxcommon.rpc.rpc_errors import RpcInvalidParams, RpcAccountIdError


class AbstractBlxrTransactionRpcRequest(AbstractRpcRequest, Generic[Node]):
    SYNCHRONOUS = rpc_constants.SYNCHRONOUS_PARAMS_KEY
    help = {
        "params": f"[Required - {rpc_constants.TRANSACTION_PARAMS_KEY}: [transaction payload in hex string format]]. "
                  f"Optional - {SYNCHRONOUS}: [True (wait for response from the relay - default), "
                  "False (don't wait for response)].",
        "description": "send transaction to the bloXroute BDN"
    }

    def validate_params(self) -> None:
        params = self.params
        if params is None or not isinstance(params, dict):
            raise RpcInvalidParams(
                self.request_id,
                "Params request field is either missing or not a dictionary type."
            )
        if rpc_constants.TRANSACTION_PARAMS_KEY not in params:
            raise RpcInvalidParams(
                self.request_id,
                f"Invalid transaction request params type: {self.params}"
            )

    async def process_request(self) -> JsonRpcResponse:
        params = self.params
        assert isinstance(params, dict)

        account_id = self.get_account_id()
        if not account_id:
            raise RpcAccountIdError(
                self.request_id,
                "Account ID is missing."
            )

        transaction_str: str = params[rpc_constants.TRANSACTION_PARAMS_KEY]
        network_num = self.get_network_num()
        transaction_flag = TransactionFlag.PAID_TX
        return await self.process_transaction(network_num, account_id, transaction_flag, transaction_str)

    @abstractmethod
    async def process_transaction(
        self, network_num: int, account_id: str, transaction_flag: TransactionFlag, transaction_str: str
    ) -> JsonRpcResponse:
        pass

    @abstractmethod
    def get_network_num(self) -> int:
        pass

    @abstractmethod
    def get_account_id(self) -> str:
        pass
