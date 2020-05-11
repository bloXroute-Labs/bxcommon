from typing import Dict, Any
from aiohttp.web_response import Response
from aiohttp.web_exceptions import HTTPBadRequest

from bxcommon.models.quota_type_model import QuotaType

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest


class BlxrTransactionRpcRequest(AbstractRpcRequest):
    TRANSACTION = rpc_constants.TRANSACTION_PARAMS_KEY
    QUOTA_TYPE: str = "quota_type"
    SYNCHRONOUS = rpc_constants.SYNCHRONOUS_PARAMS_KEY
    help = {
        "params": f"[Required - {TRANSACTION}: [transaction payload in hex string format]\n"
                  f"Optional - {QUOTA_TYPE}: [{QuotaType.PAID_DAILY_QUOTA.name.lower()} for binding with a paid account"
                  f"(default) or {QuotaType.FREE_DAILY_QUOTA.name.lower()}]\n"
                  f"{SYNCHRONOUS}: [True (wait for response from the relay - default), "
                  "False (don't wait for response)]",
        "description": "send transaction to the bloXroute BDN"
    }

    async def process_request(self) -> Response:
        try:
            assert self.params is not None and isinstance(self.params, dict)
            # pyre-ignore
            transaction_str = self.params[self.TRANSACTION]
        except TypeError:
            raise HTTPBadRequest(text=f"Invalid transaction request params type: {self.params}!")
        except KeyError:
            raise HTTPBadRequest(text=f"Missing {self.TRANSACTION} field in params object: {self.params}!")
        except AssertionError:
            raise HTTPBadRequest(text="Params request field is either missing or not a dictionary type!")
        network_num = self._get_network_num()
        account_id = self._get_account_id()
        # pyre-ignore
        quota_type = self._get_quota_type(self.params)
        return self._process_message(network_num, account_id, quota_type, transaction_str)

    def _get_quota_type(self, params: Dict[str, Any]) -> QuotaType:
        account_id = self._get_account_id()
        quota_type_str = params.get(self.QUOTA_TYPE, QuotaType.PAID_DAILY_QUOTA.name).upper()
        if quota_type_str.lower() in [quota.name.lower() for quota in QuotaType]:
            quota_type = QuotaType[quota_type_str]
        elif account_id is None:
            quota_type = QuotaType.FREE_DAILY_QUOTA
        else:
            quota_type = QuotaType.PAID_DAILY_QUOTA
        if account_id is None and quota_type == QuotaType.PAID_DAILY_QUOTA:
            raise HTTPBadRequest(text="Cannot mark transaction as paid without an account!")
        return quota_type

    def _process_message(self, network_num, account_id, quota_type, transaction_str):
        # pylint: disable=unused-argument
        return Response()

    def _get_network_num(self):
        return self._node.network_num

    def _get_account_id(self):
        return self._node.account_id
