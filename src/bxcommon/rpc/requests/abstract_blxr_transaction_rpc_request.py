from abc import ABCMeta, abstractmethod
from typing import Dict, Any, Generic

from bxcommon.models.quota_type_model import QuotaType

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest, Node
from bxcommon.rpc.rpc_errors import RpcInvalidParams


class AbstractBlxrTransactionRpcRequest(AbstractRpcRequest, Generic[Node], metaclass=ABCMeta):
    QUOTA_TYPE: str = "quota_type"
    SYNCHRONOUS = rpc_constants.SYNCHRONOUS_PARAMS_KEY
    help = {
        "params": f"[Required - {rpc_constants.TRANSACTION_PARAMS_KEY}: [transaction payload in hex string format]\n"
                  f"{SYNCHRONOUS}: [True (wait for response from the relay - default), "
                  "False (don't wait for response)]",
        "description": "send transaction to the bloXroute BDN"
    }

    def validate_params(self) -> None:
        params = self.params
        if params is None or not isinstance(params, dict):
            raise RpcInvalidParams(
                self.request_id,
                "Params request field is either missing or not a dictionary type!"
            )
        if rpc_constants.TRANSACTION_PARAMS_KEY not in params:
            raise RpcInvalidParams(
                self.request_id,
                f"Invalid transaction request params type: {self.params}!"
            )

    async def process_request(self) -> JsonRpcResponse:
        params = self.params
        assert isinstance(params, dict)

        transaction_str: str = params[rpc_constants.TRANSACTION_PARAMS_KEY]
        network_num = self.get_network_num()
        account_id = self.get_account_id()
        quota_type = self._get_quota_type(params)
        return await self.process_transaction(network_num, account_id, quota_type, transaction_str)

    def _get_quota_type(self, params: Dict[str, Any]) -> QuotaType:
        account_id = self.get_account_id()
        quota_type_str = params.get(self.QUOTA_TYPE, QuotaType.PAID_DAILY_QUOTA.name).upper()
        if quota_type_str.lower() in [quota.name.lower() for quota in QuotaType]:
            quota_type = QuotaType[quota_type_str]
        elif account_id is None:
            quota_type = QuotaType.FREE_DAILY_QUOTA
        else:
            quota_type = QuotaType.PAID_DAILY_QUOTA
        if account_id is None and quota_type == QuotaType.PAID_DAILY_QUOTA:
            raise RpcInvalidParams("Cannot mark transaction as paid without an account")
        return quota_type

    @abstractmethod
    async def process_transaction(
        self, network_num: int, account_id: str, quota_type: QuotaType, transaction_str: str
    ) -> JsonRpcResponse:
        pass

    @abstractmethod
    def get_network_num(self) -> int:
        pass

    @abstractmethod
    def get_account_id(self) -> str:
        pass
