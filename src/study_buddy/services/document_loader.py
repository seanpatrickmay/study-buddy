"""Utilities for normalising input documents into markdown."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable, List, Optional

from pypdf import PdfReader

from study_buddy.services.conversion import StudyConverter
from study_buddy.services.firecrawl import FirecrawlClient
from study_buddy.core.models import DocumentBundle


class PdfMarkdownExtractor:
    """Convert local PDF files into lightweight markdown."""

    @staticmethod
    def extract(path: Path) -> str:
        reader = PdfReader(str(path))
        sections: List[str] = [f"# Document: {path.name}"]
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            sections.append(f"\n## Page {index}\n")
            sections.append(text)
        return "\n\n".join(sections) if len(sections) > 1 else ""


class DocumentLoader:
    """Load a heterogeneous collection of documents into markdown."""

    def __init__(self, firecrawl_api_key: Optional[str]) -> None:
        self._firecrawl = FirecrawlClient(api_key=firecrawl_api_key)
        self._converter = StudyConverter(PdfMarkdownExtractor.extract, self._html_to_markdown)

    async def load_many(self, sources: Iterable[str]) -> List[DocumentBundle]:
        """Load every provided source into a :class:`DocumentBundle`."""
        tasks = [self._load_single(source) for source in sources]
        return [doc for doc in await asyncio.gather(*tasks) if doc]

    async def _load_single(self, raw_source: str) -> Optional[DocumentBundle]:
        path = Path(raw_source)

        if raw_source.startswith("http"):
            if not self._firecrawl.enabled:
                raise ValueError("Remote URLs require a configured Firecrawl API key.")

            markdown = self._firecrawl.scrape_markdown(raw_source)
            if markdown:
                return DocumentBundle(
                    source_path=Path(raw_source),
                    display_name=raw_source,
                    markdown=markdown,
                    metadata={"ingestion": "firecrawl"},
                )

            raise ValueError("Firecrawl failed to fetch markdown for the remote PDF.")

        if not path.exists():
            raise FileNotFoundError(f"Document not found: {raw_source}")

        bundle = await asyncio.to_thread(self._converter.convert, path)
        bundle.metadata.setdefault("ingestion", "local")
        return bundle

    @staticmethod
    def _html_to_markdown(path: Path) -> str:
        from markdownify import markdownify

        html = path.read_text(encoding="utf-8")
        return markdownify(html, heading_style="ATX")
