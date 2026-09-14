from __future__ import annotations

import json
from typing import Any

import httpx

from recal.application.ports import SearchResult

_MCP_PROTOCOL_VERSION = "2025-03-26"
_MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


class ParallelSearchAdapter:
    """Recherche web via le serveur MCP Parallel Search.

    Gratuit et sans clé pour les agents. Le protocole MCP (JSON-RPC sur HTTP
    streamable) est implémenté ici au strict minimum : initialize, notification
    d’initialisation puis tools/call. Aucune dépendance au SDK MCP.
    """

    def __init__(
        self,
        *,
        endpoint: str = "https://search.parallel.ai/mcp",
        timeout_seconds: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("PARALLEL_SEARCH_ENDPOINT est obligatoire")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._client = client
        self._session_id: str | None = None

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("La requête Parallel Search ne peut pas être vide")
        max_results = max(1, min(max_results, 10))
        await self._ensure_session()
        response = await self._post(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "web_search",
                    "arguments": {
                        "objective": f"find opportunities matching: {query}",
                        "search_queries": [query],
                    },
                },
            }
        )
        try:
            results = await self._call_web_search(response, max_results)
        except _SessionExpired:
            self._session_id = None
            await self._ensure_session()
            response = await self._post(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "web_search",
                        "arguments": {
                            "objective": f"find opportunities matching: {query}",
                            "search_queries": [query],
                        },
                    },
                }
            )
            results = await self._call_web_search(response, max_results)
        return results

    async def _ensure_session(self) -> None:
        if self._session_id:
            return
        response = await self._post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": _MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "recal-backend", "version": "0.1.0"},
                },
            }
        )
        session_id = response.headers.get("mcp-session-id")
        if not session_id:
            raise RuntimeError("Parallel Search n’a pas renvoyé d’identifiant de session")
        self._session_id = session_id
        message = self._parse_message(response)
        if message.get("error"):
            raise RuntimeError(f"Initialisation MCP échouée : {message['error']}")
        await self._post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        )

    async def _post(self, payload: dict[str, Any]) -> httpx.Response:
        client = self._client or httpx.AsyncClient(timeout=self.timeout_seconds)
        self._client = client
        headers = dict(_MCP_HEADERS)
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        response = await client.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response

    async def _call_web_search(
        self, response: httpx.Response, max_results: int
    ) -> list[SearchResult]:
        message = self._parse_message(response)
        if message.get("error"):
            raise RuntimeError(f"Recherche Parallel échouée : {message['error']}")
        result = message.get("result", {})
        if result.get("isError"):
            text = json.dumps(result.get("content", []))[:200]
            if "session" in text.lower():
                raise _SessionExpired(text)
            raise RuntimeError(f"Erreur outil web_search : {text}")
        structured = result.get("structuredContent") or {}
        items = structured.get("results") or []
        return [
            SearchResult(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                content="\n".join(excerpt for excerpt in item.get("excerpts", []) if excerpt),
                source="parallel",
            )
            for item in items
            if item.get("url")
        ][:max_results]

    @staticmethod
    def _parse_message(response: httpx.Response) -> dict[str, Any]:
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("text/event-stream"):
            for line in response.text.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        parsed = json.loads(data)
                        if isinstance(parsed, dict) and ("result" in parsed or "error" in parsed):
                            return parsed
            raise RuntimeError("Réponse MCP SSE vide ou invalide")
        return response.json()

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class _SessionExpired(Exception):
    """La session MCP a expiré ; une réinitialisation est nécessaire."""
