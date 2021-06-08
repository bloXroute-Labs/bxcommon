import asyncio
from typing import Iterable, AsyncIterable, Union, Optional, Dict, Any, Tuple

import websockets

from bxcommon.rpc.provider.abstract_ws_provider import AbstractWsProvider
from bxcommon.rpc.rpc_errors import RpcError
from bxcommon.rpc.ws.ws_client import WsClient


class MockWebSocket(websockets.WebSocketClientProtocol):
    def __init__(self):
        super().__init__()
        self.alive_event = asyncio.Event()
        self.send_messages = []
        self.recv_messages: 'asyncio.Queue[websockets.Data]' = asyncio.Queue()
        self.transfer_data_exc = None

    async def wait_closed(self) -> None:
        await self.alive_event.wait()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.alive_event.set()

    async def send(
        self,
        message: Union[websockets.Data, Iterable[websockets.Data], AsyncIterable[websockets.Data]],
    ) -> None:
        self.send_messages.append(message)

    async def recv(self) -> websockets.Data:
        return await self.recv_messages.get()


class MockWsProvider(AbstractWsProvider):
    def __init__(self, uri: str):
        super().__init__(uri)
        self.fail_connect = False

    async def subscribe(self, channel: str, options: Optional[Dict[str, Any]] = None) -> str:
        pass

    async def unsubscribe(self, subscription_id: str) -> Tuple[bool, Optional[RpcError]]:
        pass

    async def connect_websocket(self) -> websockets.WebSocketClientProtocol:
        if self.fail_connect:
            raise ConnectionRefusedError
        return MockWebSocket()

    # just for autocompletion
    def get_test_websocket(self) -> Optional[websockets.client.WebSocketClientProtocol]:
        return self.ws


class MockWsClient(WsClient):
    def __init__(self, uri: str):
        super().__init__(uri)
        self.fail_connect = False

    async def subscribe(self, channel: str, options: Optional[Dict[str, Any]] = None) -> str:
        pass

    async def unsubscribe(self, subscription_id: str) -> Tuple[bool, Optional[RpcError]]:
        pass

    async def connect_websocket(self) -> websockets.WebSocketClientProtocol:
        self.ws = MockWebSocket()
        self.connected_event.set()
        wait_event = asyncio.Event()
        self.ws_status_check = asyncio.create_task(
            wait_event.wait()
        )
        ws = self.ws
        assert ws is not None
        return ws

    async def close(self) -> None:
        self.running = False
        super().close()

    # just for autocompletion
    def get_test_websocket(self) -> Optional[websockets.client.WebSocketClientProtocol]:
        return self.ws
