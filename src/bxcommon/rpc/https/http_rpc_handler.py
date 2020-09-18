from typing import Any, Dict, TYPE_CHECKING, Generic, TypeVar

from aiohttp import web
from aiohttp.web import Request, Response
from aiohttp.web_exceptions import HTTPBadRequest, HTTPOk

from bxcommon.rpc import rpc_constants
from bxcommon.rpc.abstract_rpc_handler import AbstractRpcHandler
from bxcommon.rpc.bx_json_rpc_request import BxJsonRpcRequest
from bxcommon.rpc.json_rpc_response import JsonRpcResponse
from bxcommon.rpc.requests.abstract_rpc_request import AbstractRpcRequest
from bxcommon.rpc.rpc_constants import ContentType
from bxcommon.rpc.rpc_errors import RpcParseError
from bxutils import logging

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


logger = logging.get_logger(__name__)
Node = TypeVar("Node", bound="AbstractNode")


class HttpRpcHandler(Generic[Node], AbstractRpcHandler[Node, Request, Response]):
    def __init__(self, node: Node):
        super().__init__(node)
        self.content_type = ContentType.PLAIN

    def parse_content_type(self, request: Request):
        try:
            # pyre-fixme[16]: Callable `aiohttp.web_request.BaseRequest.headers` has no attribute `__getitem__`
            content_type = request.headers[rpc_constants.CONTENT_TYPE_HEADER_KEY]
        except KeyError:
            pass
        else:
            try:
                content_type_enum = ContentType.from_string(content_type)
                self.content_type = content_type_enum
            except ValueError:
                raise HTTPBadRequest(
                    text=f"Unrecognized content type: {content_type}. "
                         f"Accepted values: {ContentType.PLAIN.value}, {ContentType.JSON.value}"
                )

    async def parse_request(self, request: Request) -> Dict[str, Any]:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise RpcParseError(None, f"Unable to parse the request: {payload}")
        return payload

    def get_request_handler(self, request: BxJsonRpcRequest) -> AbstractRpcRequest:
        # seems to be pyre bug: https://github.com/facebook/pyre-check/issues/267
        # pyre-fixme[45]: Cannot instantiate abstract class `Abstract` with abstract method `run`.
        return self.request_handlers[request.method](request, self.node)

    def serialize_response(self, response: JsonRpcResponse) -> Response:
        if response.error is None:
            status_code = HTTPOk.status_code
        else:
            status_code = HTTPBadRequest.status_code

        if self.content_type == ContentType.PLAIN:
            return web.json_response(
                response.to_jsons(self.case),
                status=status_code,
                content_type=ContentType.PLAIN.value
            )
        else:
            return web.json_response(text=response.to_jsons(self.case), status=status_code)
