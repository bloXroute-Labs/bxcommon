import asyncio
from asyncio import Future
from typing import Optional, Union, cast

from aiohttp import WSMessage
from aiohttp.web import Request
from aiohttp.web_ws import WebSocketResponse
from websockets import WebSocketServerProtocol

from bxcommon.rpc.abstract_ws_rpc_handler import AbstractWsRpcHandler, WsRequest
from bxcommon.rpc.rpc_errors import RpcError
from bxcommon.rpc.json_rpc_response import JsonRpcResponse


class WsConnection:
    def __init__(
        self,
        websocket: Union[WebSocketResponse, WebSocketServerProtocol],
        path: str,
        ws_rpc_handler: AbstractWsRpcHandler,
    ) -> None:
        self.ws = websocket
        self.path = path  # currently unused
        self.ws_rpc_handler = ws_rpc_handler

        self.request_handler: Optional[Future] = None
        self.publish_handler: Optional[Future] = None
        self.alive_handler: Optional[Future] = None

    async def handle(self, request: Request) -> WebSocketResponse:
        request_handler = asyncio.ensure_future(self.handle_request(request))
        publish_handler = asyncio.ensure_future(self.handle_publications())
        alive_handler = asyncio.ensure_future(self.ws_rpc_handler.wait_for_close())

        self.request_handler = request_handler
        self.publish_handler = publish_handler
        self.alive_handler = alive_handler

        await asyncio.wait(
            [request_handler, publish_handler, alive_handler], return_when=asyncio.FIRST_COMPLETED
        )
        return self.ws

    async def handle_request(self, request: Request) -> None:
        websocket = self.ws
        await websocket.prepare(request)
        async for message in websocket:
            try:
                response = await self.ws_rpc_handler.handle_request(
                    # pyre-ignore[6] Expected `multidict.CIMultiDictProxy[typing.Any]`
                    WsRequest(cast(WSMessage, message), request.headers)
                )
            except RpcError as err:
                response = JsonRpcResponse(err.id, error=err).to_jsons()
            await websocket.send_str(response)

    async def handle_publications(self, ) -> None:
        websocket = self.ws
        while not websocket.closed:
            message = await self.ws_rpc_handler.get_next_subscribed_message()
            await websocket.send_bytes(
                self.ws_rpc_handler.serialize_cached_subscription_message(message)
            )

    async def close(self) -> None:
        self.ws_rpc_handler.close()

        request_handler = self.request_handler
        if request_handler is not None:
            request_handler.cancel()

        publish_handler = self.publish_handler
        if publish_handler is not None:
            publish_handler.cancel()

        alive_handler = self.alive_handler
        if alive_handler is not None:
            alive_handler.cancel()

        # cleanup to avoid circular reference and allow immediate GC.
        self.request_handler = None
        self.publish_handler = None
        self.alive_handler = None

        await self.ws.close()
