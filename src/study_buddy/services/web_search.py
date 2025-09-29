"""Lightweight Tavily-powered web search helper."""
from __future__ import annotations

from typing import Optional

try:
    from tavily import TavilyClient
except ImportError:  # pragma: no cover
    TavilyClient = None  # type: ignore[misc]


class WebSearchAgent:
    """Fetch concise research snippets using the Tavily API."""

    def __init__(self, api_key: Optional[str], default_results: int = 3) -> None:
        self._client = TavilyClient(api_key=api_key) if (api_key and TavilyClient) else None
        self._default_results = default_results

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def search_summary(self, query: str, *, max_results: Optional[int] = None, max_chars: int = 480) -> str:
        """Return a compact textual summary for the given query."""
        if not self._client:
            return ""
        try:
            response = self._client.search(
                query=query,
                max_results=max_results or self._default_results,
                include_answer="basic",
            )
        except Exception:
            return ""

        snippets = []
        answer = response.get("answer")
        if answer:
            snippets.append(answer.strip())

        for result in response.get("results", []):
            content = (result.get("content") or "").strip()
            if not content:
                continue
            snippets.append(content)
            if sum(len(part) for part in snippets) >= max_chars:
                break

        joined = "\n".join(snippets)
        return joined[:max_chars].strip()
