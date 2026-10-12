"""ASGI middleware that caps request bodies while they stream in.

Checking ``Content-Length`` alone is not enough (chunked uploads have none), and waiting
for the framework to parse the body means a huge upload is already in memory or on disk.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodyTooLargeError(Exception):
    pass


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int, limit_label: str) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.limit_label = limit_label

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if self._declared_length(scope) > self.max_body_bytes:
            await self._reject(send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.max_body_bytes:
                raise BodyTooLargeError
            return message

        try:
            await self.app(scope, limited_receive, send)
        except BodyTooLargeError:
            await self._reject(send)

    @staticmethod
    def _declared_length(scope: Scope) -> int:
        for name, value in scope.get("headers", []):
            if name == b"content-length" and value.isdigit():
                return int(value)
        return 0

    async def _reject(self, send: Send) -> None:
        body = json.dumps({"detail": f"upload exceeds the {self.limit_label} limit"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})
