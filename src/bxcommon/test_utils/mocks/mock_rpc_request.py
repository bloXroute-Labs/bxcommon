import json
from typing import Dict, Any, Optional


class MockRpcRequest:

    def __init__(self, headers: Dict[str, Any], json_body: str, text: Optional[str] = None) -> None:
        self.headers = headers
        self.raw_headers = headers
        self.remote = "test"
        self._json_body = json_body
        self.raw_path = "/"
        if text is None:
            text = json_body
        self._text = text

    async def text(self) -> str:
        assert self._text is not None
        # pyre-fixme[7]: Expected `str` but got `Optional[str]`.
        return self._text

    async def json(self) -> Dict[str, Any]:
        return json.loads(self._json_body)
