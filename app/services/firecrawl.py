"""Thin wrapper around the Firecrawl SDK used to fetch remote PDFs."""
from __future__ import annotations

from typing import Dict, Optional

try:
    from firecrawl import Firecrawl
except ImportError:  # pragma: no cover - optional dependency
    Firecrawl = None  # type: ignore[misc]


class FirecrawlClient:
    """Provide a minimal Firecrawl interface focused on markdown conversion."""

    def __init__(self, api_key: Optional[str]) -> None:
        self._api_key = api_key
        self._client: Optional[Firecrawl] = None
        if api_key and Firecrawl is not None:
            self._client = Firecrawl(api_key=api_key)

    @property
    def enabled(self) -> bool:
        """Return True when the client can make API calls."""
        return self._client is not None

    def scrape_markdown(self, url: str) -> Optional[str]:
        """Fetch markdown for the given URL, returning None on failure."""
        if not self._client:
            return None

        try:
            payload: Dict[str, str] = self._client.scrape(url=url, formats=["markdown"])  # type: ignore[call-arg]
        except Exception:
            return None
        return payload.get("markdown")
