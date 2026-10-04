"""STAC client for Lantmäteriets raster services.

All requests go through QgsBlockingNetworkRequest with an authcfg, so QGIS
handles tokens and proxy settings. Safe to use from a QgsTask worker thread.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from qgis.core import QgsBlockingNetworkRequest, QgsFeedback
from qgis.PyQt.QtCore import QByteArray, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest


class StacError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status

    def describe(self) -> str:
        return f"HTTP {self.status}: {self}" if self.status else str(self)


class StacClient:
    def __init__(self, base_url: str, authcfg: str, feedback: QgsFeedback | None = None):
        self.base_url = base_url.rstrip("/")
        self.authcfg = authcfg
        self.feedback = feedback

    def _request(self, method: str, url: str, body: dict | None = None) -> dict[str, Any]:
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"Accept", b"application/geo+json, application/json")

        blocking = QgsBlockingNetworkRequest()
        blocking.setAuthCfg(self.authcfg)

        if method == "POST":
            request.setHeader(
                QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
            )
            payload = QByteArray(json.dumps(body or {}).encode("utf-8"))
            error = blocking.post(request, payload, True, self.feedback)
        else:
            error = blocking.get(request, True, self.feedback)

        reply = blocking.reply()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if error != QgsBlockingNetworkRequest.ErrorCode.NoError:
            detail = bytes(reply.content()).decode("utf-8", "replace")[:500]
            raise StacError(f"{blocking.errorMessage()} {detail}".strip(), status)

        try:
            return json.loads(bytes(reply.content()).decode("utf-8"))
        except ValueError as e:
            raise StacError(f"Ogiltigt JSON-svar från {url}: {e}", status) from e

    def search(self, body: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """POST /search and follow `next` links. Yields one page at a time."""
        url: str | None = f"{self.base_url}/search"
        method, page_body = "POST", body

        while url:
            if self.feedback and self.feedback.isCanceled():
                return
            page = self._request(method, url, page_body)
            yield page

            next_link = next(
                (l for l in page.get("links", []) if l.get("rel") == "next"), None
            )
            if not next_link:
                return
            url = next_link["href"]
            # STAC allows next links that must be POSTed with a (merged) body.
            method = next_link.get("method", "GET").upper()
            if method == "POST":
                extra = next_link.get("body") or {}
                page_body = {**body, **extra} if next_link.get("merge") else extra or body
            else:
                page_body = None
