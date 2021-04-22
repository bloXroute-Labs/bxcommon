import asyncio
from abc import abstractmethod, ABCMeta
from asyncio import Future, Task
from typing import Optional, Union, List, Any, Dict, Tuple, Callable, TypeVar, Coroutine

import websockets

from bxcommon.rpc.json_rpc_request import JsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.rpc_errors import RpcError, RpcTimedOut
from bxcommon import constants
from bxcommon.rpc.provider.abstract_provider import AbstractProvider, SubscriptionNotification
from bxcommon.rpc.provider.response_queue import ResponseQueue
from bxcommon.rpc.provider.subscription_manager import SubscriptionManager
from bxutils import log_messages
from bxutils import logging

T = TypeVar("T")
logger = logging.get_logger(__name__)


class WsException(Exception):
    # pylint: disable=super-init-not-called
    def __init__(self, message: str):
        self.message = message


class AbstractWsProvider(AbstractProvider, metaclass=ABCMeta):
    def __init__(
        self,
        uri: str,
        retry_connection: bool = False,
        queue_limit: int = constants.WS_PROVIDER_MAX_QUEUE_SIZE,
        headers: Optional[Dict] = None,
        retry_callback: Optional[Callable[["AbstractWsProvider"], Coroutine[None, None, None]]] = None
    ):
        self.uri = uri
        self.retry_connection = retry_connection
        self.retry_callback = retry_callback

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.listener_task: Optional[Future] = None
        self.ws_status_check: Optional[Future] = None
        self.connected_event = asyncio.Event()

        self.subscription_manager = SubscriptionManager(queue_limit)
        self.response_messages = ResponseQueue()

        self.running = False
        self.current_request_id = 1
        if headers:
            self.headers = headers
        else:
            self.headers = {}

    async def initialize(self) -> None:
        await self.connect()

        # on initial connect, exception will be raised if self.ws is not set
        ws = self.ws
        assert ws is not None

    async def connect(self) -> None:
        logger.debug("Initiating websockets connection to: {}", self.uri)

        connection_attempts = 0
        while True:
            self.ws = None

            try:
                self.ws = await asyncio.wait_for(
                    self.connect_websocket(), constants.WS_MAX_CONNECTION_TIMEOUT_S
                )
            except (asyncio.TimeoutError, ConnectionRefusedError) as e:
                # immediately raise an error if this is the first attempt,
                # or not attempting to retry connections
                if not self.retry_connection or not self.running:
                    logger.warning(log_messages.WS_COULD_NOT_CONNECT, self.uri)
                    raise e
                if self.retry_connection:
                    logger.debug(
                        "Connection was rejected from websockets endpoint: {}. Attempts: {}. Retrying...",
                        self.uri,
                        connection_attempts
                    )
                    await asyncio.sleep(
                        constants.WS_RECONNECT_TIMEOUTS[connection_attempts]
                    )
                else:
                    logger.error(log_messages.WS_COULD_NOT_CONNECT_AFTER_RETRIES, self.uri, connection_attempts)
                    break
            # pylint: disable=broad-except
            except Exception as e:
                logger.error(log_messages.WS_UNEXPECTED_ERROR, e)
            else:
                break

            connection_attempts = min(connection_attempts, len(constants.WS_RECONNECT_TIMEOUTS) - 1)

        if self.ws is None:
            logger.debug("Could not reconnect websocket. Exiting.")
            self.running = False
        else:
            logger.debug("Connected to websockets endpoint: {}", self.uri)
            self.running = True
            ws_status_check = self.ws_status_check
            if ws_status_check is not None and not ws_status_check.done():
                ws_status_check.cancel()
            self.ws_status_check = asyncio.create_task(self._ensure_websocket_alive())

            self.connected_event.set()

            listener_task = self.listener_task
            if listener_task is not None and not listener_task.done():
                listener_task.cancel()
            self.listener_task = asyncio.create_task(self.receive())

    async def connect_websocket(self) -> websockets.WebSocketClientProtocol:
        return await websockets.connect(self.uri, extra_headers=self.headers)

    @abstractmethod
    async def subscribe(self, channel: str, options: Optional[Dict[str, Any]] = None) -> str:
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> Tuple[bool, Optional[RpcError]]:
        pass

    async def call_rpc(
        self,
        method: str,
        params: Union[List[Any], Dict[Any, Any], None],
        request_id: Optional[str] = None
    ) -> JsonRpcResponse:
        if request_id is None:
            request_id = str(self.current_request_id)
            self.current_request_id += 1

        return await self.call(
            JsonRpcRequest(request_id, method, params)
        )

    async def call(
        self,
        request: JsonRpcRequest
    ) -> JsonRpcResponse:
        request_id = request.id
        assert request_id is not None

        await self.connected_event.wait()

        if not self.running:
            raise WsException(
                "Connection was broken when trying to call RPC method. "
                "Try reconnecting."
            )

        ws = self.ws
        assert ws is not None

        serialized_request = request.to_jsons()
        logger.trace("Sending message to websocket: {}", serialized_request)
        await ws.send(serialized_request)
        response = await self.get_rpc_response(request_id)
        if response is None:
            raise RpcTimedOut(None, "Please try again.")
        error = response.error
        if error:
            logger.error(
                log_messages.ETH_RPC_ERROR, error.message, error.data)
            raise error

        return response

    def subscribe_with_callback(
        self,
        callback: Callable[[SubscriptionNotification], None],
        channel: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Task:
        if options is None:
            options = {}
        return asyncio.create_task(
            self._handle_subscribe_callback(callback, channel, options)
        )

    async def _handle_subscribe_callback(
        self,
        callback: Callable[[SubscriptionNotification], None],
        channel: str,
        options: Dict[str, Any],
    ) -> None:
        subscription_id = await self.subscribe(channel, options)
        while self.running:
            notification = await self.subscription_manager.get_next_subscription_notification_for_id(
                subscription_id
            )
            try:
                callback(notification)
            # pylint: disable=broad-except
            except Exception as e:
                logger.exception(log_messages.WS_COULD_NOT_PROCESS_NOTIFICATION, e)

    async def receive(self) -> None:
        # TODO: preferably this would be an infinite loop that waits on
        # self.connected_event.wait(), but it seems that `async for` never
        # throws an exception, even when the websocket gets disconnected.

        logger.trace("Started receiving on websocket.")
        ws = self.ws
        assert ws is not None

        async for next_message in ws:
            logger.trace("Received message on websocket: {}", next_message)

            # process response messages
            # noinspection PyBroadException
            try:
                response_message = JsonRpcResponse.from_jsons(next_message)
            # pylint: disable=broad-except
            except Exception:
                pass
            else:
                await self.response_messages.put(response_message)
                continue

            # process notification messages
            try:
                subscription_message = JsonRpcRequest.from_jsons(next_message)
                params = subscription_message.params
                assert isinstance(params, dict)
                await self.subscription_manager.receive_message(
                    SubscriptionNotification(
                        params["subscription"], params["result"],
                    )
                )
            # pylint: disable=broad-except
            except Exception as e:
                logger.warning(
                    log_messages.ETH_RPC_PROCESSING_ERROR,
                    next_message,
                    e,
                    exc_info=True
                )

        logger.trace("Temporarily stopped receiving message on websocket. Awaiting reconnection.")

    async def get_next_subscription_notification(self) -> SubscriptionNotification:
        task = asyncio.create_task(
            self.subscription_manager.get_next_subscription_notification()
        )
        return await self._wait_for_ws_message(task)

    async def get_next_subscription_notification_by_id_timeout(
        self, subscription_id: str
    ) -> SubscriptionNotification:
        task = asyncio.create_task(
            self.subscription_manager.get_next_subscription_notification_for_id(
                subscription_id
            )
        )
        return await self._wait_for_ws_message(task, timeout=constants.WAIT_FOR_SUBSCRIPTION_TIMEOUT)

    async def get_next_subscription_notification_by_id(
        self, subscription_id: str
    ) -> SubscriptionNotification:
        task = asyncio.create_task(
            self.subscription_manager.get_next_subscription_notification_for_id(
                subscription_id
            )
        )
        return await self._wait_for_ws_message(task)

    async def get_rpc_response(self, request_id: str) -> JsonRpcResponse:
        task = asyncio.create_task(self.response_messages.get_by_request_id(request_id))
        return await self._wait_for_ws_message(task)

    async def _wait_for_ws_message(
        self, ws_waiter_task: "Future[T]", timeout: Optional[int] = None
    ) -> T:
        if not self.connected_event.is_set():
            ws_waiter_task.cancel()
            raise WsException("Cannot wait for a message on a broken socket.")

        ws_status_check = self.ws_status_check
        assert ws_status_check is not None

        await asyncio.wait(
            [ws_waiter_task, ws_status_check], return_when=asyncio.FIRST_COMPLETED, timeout=timeout
        )

        if ws_waiter_task.done():
            return ws_waiter_task.result()
        else:
            ws_waiter_task.cancel()
            raise WsException(
                "Websocket connection disconnected while waiting for a response. "
                "Try reconnecting or checking SSL certificates."
            )

    async def _ensure_websocket_alive(self) -> None:
        ws = self.ws
        assert ws is not None
        await ws.wait_closed()

        if ws.transfer_data_exc:
            logger.error(
                log_messages.RPC_TRANSPORT_EXCEPTION, ws.transfer_data_exc
            )

        self.connected_event.clear()

        if not self.retry_connection:
            listener = self.listener_task
            assert listener is not None
            listener.cancel()
            logger.debug("Websockets connection was broken. Closing...")
            self.running = False
            await self.close()
        elif self.running:
            logger.debug("Websockets connection was broken, reconnecting...")
            asyncio.create_task(self.reconnect())

    async def reconnect(self) -> None:
        await asyncio.sleep(constants.WS_MIN_RECONNECT_TIMEOUT_S)

        await self.connect()

        if self.ws is not None:
            logger.info("Websockets connection was re-established.")

            retry_callback = self.retry_callback
            if retry_callback:
                await retry_callback(self)

    async def close(self) -> None:
        logger.trace("Closing websockets provider")

        self.running = False

        ws = self.ws
        if ws is not None:
            await ws.close()
            await ws.wait_closed()

        listener = self.listener_task
        if listener is not None:
            listener.cancel()

        ws_status_check = self.ws_status_check
        if ws_status_check is not None:
            ws_status_check.cancel()

        self.connected_event.set()
