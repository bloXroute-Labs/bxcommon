from typing import Optional, Tuple, Dict, Any

from bxcommon.rpc.rpc_errors import RpcError
from bxcommon.rpc.provider.abstract_ws_provider import AbstractWsProvider
from bxutils import log_messages
from bxutils import logging

logger = logging.get_logger(__name__)


class EthWsSubscriber(AbstractWsProvider):
    """
    Subscriber to Ethereum websockets RPC interface.

    Requires Ethereum startup arguments:
    --ws --wsapi eth --wsport 8546

    See https://geth.ethereum.org/docs/rpc/server for more info.
    (--ws-addr 127.0.0.1 maybe a good idea too)

    Requires Gateway startup arguments:
    --eth-ws-uri ws://127.0.0.1:8546
    """

    def __init__(
        self,
        ws_uri: str,
    ) -> None:
        super().__init__(ws_uri, True)

    async def reconnect(self) -> None:
        logger.warning(log_messages.ETH_WS_SUBSCRIBER_CONNECTION_BROKEN)
        try:
            await super().reconnect()
        except ConnectionRefusedError:
            self.running = False

        if self.running:
            logger.info("Reconnected to Ethereum websocket feed")
        else:
            logger.warning(log_messages.ETH_RPC_COULD_NOT_RECONNECT)

    async def subscribe(self, channel: str, options: Optional[Dict[str, Any]] = None) -> str:
        response = await self.call_rpc(
            "eth_subscribe",
            [channel]
        )
        subscription_id = response.result
        assert isinstance(subscription_id, str)
        self.subscription_manager.register_subscription(subscription_id)
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> Tuple[bool, Optional[RpcError]]:
        response = await self.call_rpc(
            "eth_unsubscribe",
            [subscription_id]
        )
        if response.result is not None:
            self.subscription_manager.unregister_subscription(subscription_id)
            return True, None
        else:
            return False, response.error
