import datetime
from typing import Dict, Any
from aiohttp.web_response import Response
from aiohttp.web_exceptions import HTTPBadRequest, HTTPAccepted

from bxcommon.connections.connection_type import ConnectionType
from bxcommon.exceptions import ParseError
from bxcommon.models.quota_type_model import QuotaType
from bxcommon.utils.stats.transaction_stat_event_type import TransactionStatEventType
from bxcommon.utils.stats.transaction_statistics_service import tx_stats

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(__name__)
logger_process_request = logging.get_logger(LogRecordType.PublicApiPerformance, __name__)


class BlxrTransactionRpcRequest(AbstractRpcRequest):
    TRANSACTION = rpc_constants.TRANSACTION_PARAMS_KEY
    QUOTA_TYPE: str = "quota_type"
    help = {
        "params": f"[Required - {TRANSACTION}: [transaction payload in hex string format],"
        f"Optional - {QUOTA_TYPE}: [{QuotaType.PAID_DAILY_QUOTA.name.lower()} for binding with a paid account"
        f"(default) or {QuotaType.FREE_DAILY_QUOTA.name.lower()}]]"
    }

    async def process_request(self) -> Response:
        logger_process_request.debug({"component": "bxrelay",
                                      "type": "receiving",
                                      "sub_type": "request",
                                      "time": datetime.datetime.utcnow()})
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
        try:
            message_converter = self._node.message_converter
            assert message_converter is not None, "Invalid server state!"
            transaction = message_converter.encode_raw_msg(transaction_str)
            bx_tx = message_converter.bdn_tx_to_bx_tx(transaction, network_num, quota_type)
        except (ValueError, ParseError) as e:
            logger.error("Error parsing the transaction:\n{}", e)
            raise HTTPBadRequest(text=f"Invalid transaction param: {transaction_str} was provided!")
        tx_service = self._node.get_tx_service()
        tx_hash = bx_tx.tx_hash()
        if tx_service.has_transaction_contents(tx_hash):
            short_id = tx_service.get_short_id(tx_hash)
            tx_stats.add_tx_by_hash_event(
                tx_hash,
                TransactionStatEventType.BDN_TX_RECEIVED_FROM_CLIENT_ACCOUNT_IGNORE_SEEN,
                network_num,
                account_id=account_id, short_id=short_id
            )
            raise HTTPBadRequest(text=f"Transaction [{tx_hash} was already seen!")
        tx_stats.add_tx_by_hash_event(
            tx_hash,
            TransactionStatEventType.BDN_TX_RECEIVED_FROM_CLIENT_ACCOUNT,
            network_num,
            account_id=account_id
        )
        # All connections outside of this one is a bloXroute server
        broadcast_peers = self._node.broadcast(bx_tx, connection_types=[ConnectionType.RELAY_TRANSACTION])
        tx_stats.add_tx_by_hash_event(
            tx_hash,
            TransactionStatEventType.TX_SENT_FROM_GATEWAY_TO_PEERS,
            network_num,
            peers=map(lambda conn: (conn.peer_desc, conn.CONNECTION_TYPE), broadcast_peers)
        )
        tx_service.set_transaction_contents(tx_hash, bx_tx.tx_val())
        tx_json = {
            "tx_hash": repr(tx_hash),
            "quota_type": quota_type.name.lower(),
            "account_id": account_id
        }
        return self._format_response(
            tx_json,
            HTTPAccepted
        )

    def _get_network_num(self):
        return self._node.network_num

    def _get_account_id(self):
        return self._node.account_id

