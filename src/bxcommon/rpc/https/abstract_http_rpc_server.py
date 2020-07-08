import asyncio
import base64
from abc import abstractmethod
from asyncio import Future
from typing import Callable, Awaitable, Optional, TYPE_CHECKING, TypeVar, Generic
from aiohttp import web
from aiohttp.abc import StreamResponse
from aiohttp.web import Application, Request, Response, AppRunner, TCPSite
from aiohttp.web_exceptions import HTTPClientError, HTTPBadRequest, HTTPInternalServerError
from aiohttp.web_exceptions import HTTPUnauthorized

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.https.http_rpc_handler import HttpRpcHandler
from bxcommon.rpc.https.request_formatter import RequestFormatter
from bxcommon.rpc.https.response_formatter import ResponseFormatter
from bxcommon.rpc.json_rpc_response import JsonRpcResponse

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
    logger.trace(
        "Finished handling request: {}, returning response: {}.",
        request_formatter,
        ResponseFormatter(response),
    )
    return response


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

    def __init__(self, node: Node) -> None:
        self.node = node
        self._app = Application(middlewares=[request_middleware])
        self._app.add_routes(
            [web.post("/", self.handle_request), web.get("/", self.handle_get_request)]
        )
        self._runner = AppRunner(self._app)
        self._site = None
        self._handler = self.request_handler()
        self._stop_requested = False
        self._stop_waiter = asyncio.get_event_loop().create_future()
        self._started = False
        self._encoded_auth = None
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
        await self._stop_waiter
        await self._runner.cleanup()
        self._started = False

    async def handle_request(self, request: Request) -> Response:
        try:
            self.authenticate_request(request)
            return await self._handler.handle_request(request)
        except HTTPClientError as e:
            return self._format_http_error(e)
        except RpcAccountIdError as e:
            return self._format_rpc_error(e, HTTPUnauthorized.status_code)
        except (RpcParseError, RpcMethodNotFound, RpcInvalidParams) as e:
            return self._format_rpc_error(e, HTTPBadRequest.status_code)
        except RpcError as e:
            return self._format_rpc_error(e, HTTPInternalServerError.status_code)

    async def handle_get_request(self, request: Request) -> Response:
        try:
            self.authenticate_request(request)
        except HTTPUnauthorized as e:
            return self._format_http_error(e)
        else:
            response_dict = {
                "result": {
                    "required_request_type": "POST",
                    "required_headers": [
                        {
                            rpc_constants.CONTENT_TYPE_HEADER_KEY: rpc_constants.PLAIN_HEADER_TYPE
                        }
                    ],
                    "payload_structures": await self._handler.help(),
                }
            }
            return web.json_response(json_encoder.to_json(response_dict))

    async def _start(self) -> None:
        self._started = True
        await self._runner.setup()
        opts = self.node.opts

        # TODO: add ssl certificate
        site = TCPSite(self._runner, opts.rpc_host, opts.rpc_port)
        self._site = site
        await site.start()

    def _format_http_error(self, client_error: HTTPClientError) -> HTTPClientError:
        err_msg = client_error.text
        code = client_error.status_code
        response_json = {
            "result": None,
            "error": err_msg,
            "code": code,
            "message": err_msg,
        }
        client_error.text = json_encoder.to_json(response_json)
        return client_error

    def _format_rpc_error(self, rpc_error: RpcError, status_code: int) -> Response:
        return web.json_response(
            JsonRpcResponse(rpc_error.id, error=rpc_error).to_jsons(),
            status=status_code
        )
