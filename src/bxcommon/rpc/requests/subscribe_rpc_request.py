import fnmatch
from typing import TYPE_CHECKING, Callable, Any, List, Optional

from bxcommon.feed.feed import FeedKey
from bxcommon.feed.feed_manager import FeedManager
from bxcommon.feed.subscriber import Subscriber
from bxcommon.models.bdn_account_model_base import BdnAccountModelBase
from bxcommon.models.bdn_service_model_config_base import BdnFeedServiceModelConfigBase
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_errors import RpcInvalidParams, RpcAccountIdError, RpcError
from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)
logger_filters = logging.get_logger(LogRecordType.TransactionFiltering, __name__)


class SubscribeRpcRequest(AbstractRpcRequest["AbstractNode"]):
    help = {
        "params":
        '[feed_name, {"include": [field_1, field_2], "duplicates": false, "include_from_blockchain": true}].\n'
        "Available feeds: newTxs, pendingTxs, newBlocks, ethOnBlock\n"
        "Available fields for transaction feeds: tx_hash, tx_contents (default: all)\n"
        "Available fields for block feed: hash, block (default: all)\n"
        "duplicates: false (filter out duplicates from feed, typically low fee "
        "transactions, default), true (include all duplicates)\n"
        "include_from_blockchain: include transactions received from the connected blockchain node (default: true)\n",
        "description": "Subscribe to a named feed for notifications",
    }

    def __init__(
        self,
        request: BxJsonRpcRequest,
        node: "AbstractNode",
        feed_manager: FeedManager,
        subscribe_handler: Callable[[Subscriber, FeedKey], None],
        feed_network: int = 0,
        account_details: Optional[BdnAccountModelBase] = None
    ) -> None:
        self.feed_name = ""
        self.feed_network = feed_network
        self.feed_key = FeedKey(self.feed_name, self.feed_network)
        self.feed_manager = feed_manager
        self.subscribe_handler = subscribe_handler
        self.options = {}
        self.available_fields = []
        self.all_fields = []
        self.account_details = account_details
        self.service_model: Optional[BdnFeedServiceModelConfigBase] = None

        super().__init__(request, node)

        assert self.feed_name != ""

    def validate_params(self) -> None:
        try:
            if not self.feed_manager.feeds:
                raise RpcAccountIdError(
                    self.request_id,
                    f"Account does not have access to the transaction streaming service.",
                )

            self.validate_params_get_options()
            self.validate_params_feed_details()
            self.validate_params_service_details()
            self.validate_params_include_fields()
            self.validate_params_filters()
            assert self.feed_name != ""
        except RpcError as e:
            logger.debug({"msg": "Failed to validate subscribe request", "params": self.params, **e.to_json()})
            raise e

    def validate_params_get_options(self):
        params = self.params

        if not isinstance(params, list) or len(params) != 2:
            raise RpcInvalidParams(
                self.request_id,
                "Subscribe RPC request params must be a list of length 2.",
            )
        feed_name, options = params
        self.feed_name = feed_name
        self.feed_key = FeedKey(self.feed_name, self.feed_network)

        self.options = options

    def validate_params_feed_details(self):
        feed = self.feed_manager.get_feed(self.feed_key)
        if feed is None:
            raise RpcInvalidParams(
                self.request_id,
                f"{self.feed_name} is an invalid feed. "
                f"Available feeds: {[key.name for key in self.feed_manager.get_feed_keys(self.feed_network)]}",
            )
        self.available_fields = feed.FIELDS
        self.all_fields = feed.ALL_FIELDS

    def validate_params_include_fields(self):
        if self.service_model and self.service_model.available_fields:
            self.available_fields = [
                field for field in self.available_fields if allowed_field(field, self.service_model.available_fields)
            ]

        invalid_options = RpcInvalidParams(
            self.request_id,
            f"{self.options} Invalid feed include parameter. "
            "Your plan does not support all requested include parameters "
            'Valid format/fields: {"include": '
            f"{self.available_fields}"
            "}.",
        )
        if not isinstance(self.options, dict):
            raise invalid_options

        include = self.options.get("include", self.all_fields)
        if not isinstance(include, list):
            raise invalid_options
        # check for empty list
        if not include:
            include = self.all_fields

        if self.available_fields:
            if any(
                included_field not in self.available_fields for included_field in include
            ):
                raise invalid_options

            # update options["include"] to support if was not specified
            self.options["include"] = include
        else:
            self.options["include"] = self.available_fields

    def validate_params_filters(self):
        if "filters" in self.options and (not self.service_model or not self.service_model.allow_filtering):
            raise RpcAccountIdError(
                self.request_id,
                f"Account does not have filtering enabled for {self.feed_name} service.",
            )

        filters = self.options.get("filters", None)
        if filters:
            logger_filters.debug(filters)
            formatted_filters = self.format_filters(filters)
            logger_filters.debug("Validated filters: {}", formatted_filters)
            self.options["filters"] = formatted_filters

    def validate_params_service_details(self):
        if self.account_details is None:
            return

        service = self.account_details.get_feed_service_config_by_name(self.feed_name)
        if service:
            service_model = service.feed
        else:
            service_model = None
        if not service or not service.is_service_valid():
            raise RpcAccountIdError(
                self.request_id,
                f"Account does not have access to the {self.feed_name} service.",
            )
        self.service_model = service_model

    async def process_request(self) -> JsonRpcResponse:
        params = self.params
        assert isinstance(params, list)

        subscriber = self.feed_manager.subscribe_to_feed(self.feed_key, self.options)
        assert subscriber is not None  # already validated
        self.subscribe_handler(subscriber, self.feed_key)

        return JsonRpcResponse(self.request_id, subscriber.subscription_id)

    def format_filters(self, filters: Any) -> str:
        valid_filters = self.feed_manager.get_valid_feed_filters(self.feed_key)
        invalid_filters = RpcInvalidParams(
            self.request_id,
            f"{filters} is not a valid set of filters. "
            'Valid format/filters: {"include": '
            f"{valid_filters}"
            "}.",
        )
        if not isinstance(filters, str):
            logger.error("Wrong filter type")
            raise invalid_filters
        if not valid_filters:
            raise invalid_filters
        logger_filters.debug("Validating filters")
        try:
            filters, keys = self.feed_manager.validate_feed_filters(self.feed_key, filters)
        except Exception:
            raise invalid_filters
        # for key in filters, if not in valid_filters, raise
        for key in keys:
            if key not in valid_filters:
                raise RpcInvalidParams(
                    self.request_id,
                    f"{key} is not a valid filter. "
                    'Valid format/filters: {"include": '
                    f"{valid_filters}"
                    "}.",
                )
        return filters


def allowed_field(field: str, available_fields: List[str]):
    for available_field in available_fields:
        if fnmatch.fnmatch(field, available_field) or available_field == "all":
            return True
    return False
