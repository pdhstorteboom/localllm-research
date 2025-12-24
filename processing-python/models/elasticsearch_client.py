"""Minimal Elasticsearch client used to persist structured logs."""

from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib import error, request

logger = logging.getLogger(__name__)


class ElasticsearchError(RuntimeError):
    """Raised when Elasticsearch interactions fail."""


@dataclass
class ElasticsearchConfig:
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout_s: float = 10.0


class ElasticsearchClient:
    def __init__(self, config: ElasticsearchConfig) -> None:
        self.base_url = config.base_url.rstrip("/")
        self.timeout_s = config.timeout_s
        self._headers = {"Content-Type": "application/json"}
        if config.api_key:
            self._headers["Authorization"] = f"ApiKey {config.api_key}"
        elif config.username and config.password:
            credentials = f"{config.username}:{config.password}".encode("utf-8")
            token = base64.b64encode(credentials).decode("utf-8")
            self._headers["Authorization"] = f"Basic {token}"

    def index_document(self, index: str, document: Mapping[str, Any]) -> dict:
        path = f"/{index}/_doc"
        url = f"{self.base_url}{path}"
        data = json.dumps(document, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=data, headers=self._headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout_s) as response:
                body = response.read().decode("utf-8") or "{}"
                payload = json.loads(body)
                if getattr(response, "status", 200) >= 400:
                    raise ElasticsearchError(f"Elasticsearch rejected document: {payload}")
                return payload
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ElasticsearchError(f"Elasticsearch HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:  # pragma: no cover - network specific failures
            raise ElasticsearchError(f"Elasticsearch unreachable: {exc.reason}") from exc


_DEFAULT_CLIENT: Optional[ElasticsearchClient] = None
_DEFAULT_CONFIG_SNAPSHOT: Optional[tuple[str, str, str, str]] = None


def get_default_elasticsearch_client() -> Optional[ElasticsearchClient]:
    """Return a cached client if configuration is provided."""
    global _DEFAULT_CLIENT, _DEFAULT_CONFIG_SNAPSHOT
    base_url = (os.getenv("ELASTICSEARCH_URL") or "").strip()
    if not base_url:
        return None
    api_key = (os.getenv("ELASTICSEARCH_API_KEY") or "").strip()
    username = (os.getenv("ELASTICSEARCH_USERNAME") or "").strip()
    password = (os.getenv("ELASTICSEARCH_PASSWORD") or "").strip()
    timeout = float(os.getenv("ELASTICSEARCH_TIMEOUT_S", "10.0"))
    snapshot = (base_url, api_key, username, password)
    if _DEFAULT_CLIENT and _DEFAULT_CONFIG_SNAPSHOT == snapshot:
        return _DEFAULT_CLIENT
    if username and not password:
        logger.warning("ELASTICSEARCH_USERNAME is set without ELASTICSEARCH_PASSWORD")
    config = ElasticsearchConfig(
        base_url=base_url,
        api_key=api_key or None,
        username=username or None,
        password=password or None,
        timeout_s=timeout,
    )
    _DEFAULT_CLIENT = ElasticsearchClient(config)
    _DEFAULT_CONFIG_SNAPSHOT = snapshot
    return _DEFAULT_CLIENT


def index_if_configured(index: str, document: Mapping[str, Any]) -> None:
    """Helper to index a document when Elasticsearch is configured."""
    client = get_default_elasticsearch_client()
    if not client:
        return
    try:
        client.index_document(index=index, document=document)
    except ElasticsearchError as exc:
        logger.warning("Failed to index document into %s: %s", index, exc)
