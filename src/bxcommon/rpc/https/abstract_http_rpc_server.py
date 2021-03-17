import asyncio
import base64
import os
import ssl
from collections import defaultdict
from ssl import Purpose
from abc import abstractmethod
from asyncio import Future
from typing import Callable, Awaitable, Optional, TYPE_CHECKING, TypeVar, Generic, List, Dict, cast
from aiohttp import web
from aiohttp.abc import StreamResponse
from aiohttp.web import Application, Request, Response, AppRunner, TCPSite, WebSocketResponse
from aiohttp.web_exceptions import HTTPClientError, HTTPBadRequest, HTTPInternalServerError
from aiohttp.web_exceptions import HTTPUnauthorized

from bxcommon import constants
from bxcommon.rpc import rpc_constants
from bxcommon.rpc.abstract_ws_rpc_handler import AbstractWsRpcHandler
from bxcommon.rpc.https.http_rpc_handler import HttpRpcHandler
from bxcommon.rpc.https.request_formatter import RequestFormatter
from bxcommon.rpc.https.response_formatter import ResponseFormatter
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.rpc_constants import ContentType
from bxcommon.rpc.ws.ws_connection import WsConnection

from bxcommon.rpc.rpc_errors import RpcError, RpcParseError, RpcMethodNotFound, \
    RpcInvalidParams, RpcAccountIdError
from bxutils.encoding import json_encoder

from bxutils import logging

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode

logger = logging.get_logger(__name__)
Node = TypeVar("Node", bound="AbstractNode")


@web.middleware
async def request_middleware(
    request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]
) -> StreamResponse:
    request_formatter = RequestFormatter(request)
    logger.trace("Handling RPC request: {}.", request_formatter)
    response = await handler(request)
    if isinstance(response, Response):
        logger.trace(
            "Finished handling request: {}, returning response: {}.",
            request_formatter,
            ResponseFormatter(response),
        )
    else:
        logger.trace(
            "Finished handling web scoket: {}.",
            request_formatter,
        )

    return response


def format_http_error(
    client_error: HTTPClientError, content_type: ContentType
) -> HTTPClientError:
    err_msg = client_error.text
    code = client_error.status_code
    response_json = {
        "result": None,
        "error": err_msg,
        "code": code,
        "message": err_msg,
    }
    client_error.content_type = content_type.value
    client_error.text = json_encoder.to_json(response_json)
    return client_error


def format_rpc_error(
    rpc_error: RpcError, status_code: int, content_type: ContentType
) -> Response:
    if content_type == ContentType.PLAIN:
        return web.json_response(
            JsonRpcResponse(rpc_error.id, error=rpc_error).to_jsons(),
            status=status_code,
            content_type=ContentType.PLAIN.value
        )
    else:
        return web.json_response(
            text=JsonRpcResponse(rpc_error.id, error=rpc_error).to_jsons(),
            status=status_code,
        )


class AbstractHttpRpcServer(Generic[Node]):
    RUN_SLEEP_INTERVAL_S: int = 5

    node: Node
    _app: Application
    _runner: AppRunner
    _site: Optional[TCPSite]
    _handler: HttpRpcHandler[Node]
    _stop_requested: bool
    _stop_waiter: Future
    _started: bool
    _encoded_auth: Optional[str]
    _ws_connections: Dict[str, List[WsConnection]] = defaultdict(list)

    def __init__(
        self,
        node: Node,
    ) -> None:
        self.node = node
        self._app = Application(middlewares=[request_middleware])
        self._app.add_routes(
            [web.post("/", self.handle_request), web.get("/", self.handle_get_request)]
        )
        self._app.add_routes(
            [web.post("/ws", self.handle_ws_request),
             web.get("/ws", self.handle_ws_request)]
        )
        self._runner = AppRunner(self._app)
        self._site = None
        self._handler = self.request_handler()
        self._stop_requested = False
        self._stop_waiter = asyncio.get_event_loop().create_future()
        self._started = False
        self._encoded_auth = None
        self._ws_connections: Dict[str, List[WsConnection]] = defaultdict(list)

        rpc_user = self.node.opts.rpc_user
        if rpc_user:
            rpc_password = self.node.opts.rpc_password
            self._encoded_auth = base64.b64encode(
                f"{rpc_user}:{rpc_password}".encode("utf-8")
            ).decode("utf-8")

    @abstractmethod
    def authenticate_request(self, request: Request) -> None:
        pass

    @abstractmethod
    def request_handler(self) -> HttpRpcHandler:
        pass

    @abstractmethod
    def request_ws_handler(self) -> Optional[AbstractWsRpcHandler]:
        pass

    def status(self) -> bool:
        return self._started

    async def run(self) -> None:
        try:
            await self._start()
            while not self._stop_requested:
                await asyncio.sleep(self.RUN_SLEEP_INTERVAL_S)
        finally:
            self._stop_waiter.set_result(True)

    async def start(self) -> None:
        if self._started:
            return
        try:
            await self._start()
        finally:
            self._stop_waiter.set_result(True)

    async def stop(self) -> None:
        self._stop_requested = True
        if self._started:
            await asyncio.gather(
                *(connection.close() for ip, connections in self._ws_connections.items() for connection in connections)
            )
        await self._stop_waiter
        await self._runner.cleanup()
        self._started = False

    async def handle_request(self, request: Request) -> Response:
        try:
            self._handler.parse_content_type(request)
            self.authenticate_request(request)
            return await self._handler.handle_request(request)
        except HTTPClientError as e:
            return format_http_error(e, self._handler.content_type)
        except RpcAccountIdError as e:
            return format_rpc_error(e, HTTPUnauthorized.status_code, self._handler.content_type)
        except (RpcParseError, RpcMethodNotFound, RpcInvalidParams) as e:
            return format_rpc_error(e, HTTPBadRequest.status_code, self._handler.content_type)
        except RpcError as e:
            return format_rpc_error(e, HTTPInternalServerError.status_code, self._handler.content_type)

    async def handle_get_request(self, request: Request) -> Response:
        try:
            self.authenticate_request(request)
        except HTTPUnauthorized as e:
            return format_http_error(e, self._handler.content_type)
        except RpcAccountIdError as e:
            return format_rpc_error(
                e,
                HTTPUnauthorized.status_code,
                self._handler.content_type
            )
        else:
            response_dict = {
                "result": {
                    "required_request_type": "POST",
                    "required_headers": [
                        {
                            rpc_constants.CONTENT_TYPE_HEADER_KEY: ContentType.PLAIN.value
                        }
                    ],
                    "payload_structures": await self._handler.help(),
                }
            }
            json_response = JsonRpcResponse.from_json(response_dict)
            return web.json_response(json_response.to_jsons(), dumps=json_encoder.to_json)

    async def handle_ws_request(self, request: Request) -> WebSocketResponse:
        try:
            self.authenticate_request(request)
        except RpcError as e:
            websocket_response = web.WebSocketResponse()
            await websocket_response.prepare(request)
            error_message = e.data
            assert error_message is not None
            # WebSockets close event code 1008: Policy Violation.
            await websocket_response.close(
                code=1008, message=bytes(error_message.encode(constants.DEFAULT_TEXT_ENCODING))
            )
            return websocket_response
        else:
            ws_response = web.WebSocketResponse()
            websocket_handler = self.request_ws_handler()
            assert websocket_handler is not None
            path = cast(str, request.path)
            ws_connection = WsConnection(
                ws_response,
                path,
                websocket_handler
            )
            # casting for pyre check tests
            remote_ip = cast(str, request.remote)
            if remote_ip is None:
                remote_ip = rpc_constants.DEFAULT_RPC_HOST
            # this coroutine may close by the http server. use try/finally
            # to force cleanup
            try:
                self._ws_connections[remote_ip].append(ws_connection)
                websocket_response = await ws_connection.handle(request)
            finally:
                await ws_connection.close()
                self._ws_connections[remote_ip].remove(ws_connection)
                logger.debug("websocket connection for {} closed and removed", remote_ip)

            return websocket_response

    async def _start(self) -> None:
        self._started = True
        await self._runner.setup()
        opts = self.node.opts

        # TODO: add ssl certificate
        ssl_context = None
        if opts.rpc_use_ssl:
            ssl_context = ssl.create_default_context(
                Purpose.CLIENT_AUTH,
                cafile=os.path.join(opts.rpc_ssl_base_url, "ca_bundle.pem")
            )
            ssl_context.load_cert_chain(
                certfile=os.path.join(opts.rpc_ssl_base_url, "cert.pem"),
                keyfile=os.path.join(opts.rpc_ssl_base_url, "key.pem")
            )
            ssl_context.check_hostname = False
        logger.info("Starting listening on RPC {}:{} SSL:{}",
                    opts.rpc_host, opts.rpc_port, opts.rpc_use_ssl)
        site = TCPSite(self._runner, opts.rpc_host, opts.rpc_port, ssl_context=ssl_context)
        self._site = site
        await site.start()
