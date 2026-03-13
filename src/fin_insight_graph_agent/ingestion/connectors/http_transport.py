from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HttpTransport:
    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        response_text = self.get_text(url, headers=headers, params=params)
        return json.loads(response_text)

    def get_text(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> str:
        request_url = url
        if params:
            request_url = f"{url}?{urlencode(params)}"
        request = Request(request_url, headers=headers or {})
        with urlopen(request) as response:  # noqa: S310
            return response.read().decode("utf-8")