from abc import abstractmethod
from typing import Generic, Union, Dict, Any, List

from bxcommon.models.transaction_flag import TransactionFlag
from bxcommon.rpc import rpc_constants
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest, Node
from bxcommon.rpc.rpc_errors import RpcInvalidParams, RpcAccountIdError
from bxcommon.utils import convert


class AbstractBlxrTransactionRpcRequest(AbstractRpcRequest, Generic[Node]):
    SYNCHRONOUS = rpc_constants.SYNCHRONOUS_PARAMS_KEY
    track_flag: TransactionFlag = TransactionFlag.PAID_TX

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
        assert params is not None
        self.validate_transaction_param(params)

    def validate_transaction_param(self, params: Union[Dict[str, Any], List[Any], None]) -> None:
        assert params is not None
        assert isinstance(params, dict)

        if rpc_constants.TRANSACTION_PARAMS_KEY not in params:
            raise RpcInvalidParams(
                self.request_id,
                f"Invalid transaction request params type: {self.params}"
            )

    def parse_track_flag(self, params: Union[Dict[str, Any], List[Any], None]):
        assert params is not None
        assert isinstance(params, dict)

        if not self.track_flag:
            self.track_flag = TransactionFlag.PAID_TX

        if rpc_constants.STATUS_TRACK_PARAMS_KEY in params:
            track_flag_str = params[rpc_constants.STATUS_TRACK_PARAMS_KEY]
            track_flag = convert.str_to_bool(str(track_flag_str).lower(), default=False)
            if track_flag:
                self.track_flag |= TransactionFlag.STATUS_TRACK

        if rpc_constants.NONCE_MONITORING_PARAMS_KEY in params:
            nonce_flag_str = params[rpc_constants.NONCE_MONITORING_PARAMS_KEY]
            nonce_flag = convert.str_to_bool(str(nonce_flag_str).lower(), default=False)
            if nonce_flag:
                self.track_flag |= TransactionFlag.NONCE_TRACK

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
        self.parse_track_flag(params)

        return await self.process_transaction(network_num, account_id, transaction_str)

    @abstractmethod
    async def process_transaction(
        self, network_num: int, account_id: str, transaction_str: str
    ) -> JsonRpcResponse:
        pass

    @abstractmethod
    def get_network_num(self) -> int:
        pass

    @abstractmethod
    def get_account_id(self) -> str:
        pass
