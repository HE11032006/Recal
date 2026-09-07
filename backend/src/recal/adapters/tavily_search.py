from __future__ import annotations

import httpx

from recal.application.ports import SearchResult


class TavilySearchAdapter:
    """Adaptateur HTTP minimal pour Tavily.

    La clé reste côté backend. Le timeout et le nombre de résultats sont bornés
    afin qu’un cycle de veille ne puisse pas consommer des ressources sans limite.
    """

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://api.tavily.com/search",
        timeout_seconds: float = 20.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("TAVILY_API_KEY est obligatoire")
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("La requête Tavily ne peut pas être vide")
        max_results = max(1, min(max_results, 10))
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
        return [
            SearchResult(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                content=str(item.get("content", "")),
                source="tavily",
            )
            for item in data.get("results", [])
            if item.get("url")
        ]
