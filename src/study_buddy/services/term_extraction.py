"""Extraction helpers that collaborate with CrewAI agents."""
from __future__ import annotations

import asyncio
import json
import re
from typing import Iterable, List, Sequence

from crewai import Crew
from langchain_anthropic import ChatAnthropic

from study_buddy.agents.tav_agent import (
    extraction_agent,
    extraction_task,
    verification_agent,
    verification_task,
)
from study_buddy.core.models import DocumentBundle


class TermExtractor:
    """Derive key terms and their definitions from markdown sources."""

    def __init__(self, llm: ChatAnthropic, chunk_size: int = 6_000) -> None:
        self._llm = llm
        self._chunk_size = chunk_size

    async def extract(self, documents: Iterable[DocumentBundle]) -> List[dict]:
        chunks = self._paginate(documents)
        extracted: List[dict] = []

        for chunk in chunks:
            result = await asyncio.to_thread(self._run_crew, chunk)
            extracted.extend(await self._normalise_output(result))

        return self._deduplicate(extracted)

    def _run_crew(self, chunk: str):
        crew = Crew(
            agents=[extraction_agent, verification_agent],
            tasks=[extraction_task, verification_task],
            verbose=False,
        )
        return crew.kickoff({"markdown": chunk})

    async def _normalise_output(self, raw_result) -> List[dict]:
        payload = str(getattr(raw_result, "output", raw_result))
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            json_blob = self._extract_json_snippet(payload)
            if json_blob:
                try:
                    return json.loads(json_blob)
                except json.JSONDecodeError:
                    pass

        prompt = (
            "Convert the following extraction into a JSON array of objects with the keys "
            "'term', 'definition', and 'context'. Respond with JSON only.\n\n" + payload
        )
        response = await self._llm.ainvoke([{"role": "user", "content": prompt}])
        json_blob = self._extract_json_snippet(response.content)
        return json.loads(json_blob) if json_blob else []

    @staticmethod
    def _extract_json_snippet(text: str) -> str | None:
        match = re.search(r"\[[\s\S]*\]", text)
        return match.group(0) if match else None

    def _paginate(self, documents: Iterable[DocumentBundle]) -> Sequence[str]:
        combined = "\n\n".join(doc.markdown for doc in documents)
        chunks: List[str] = []
        pointer = 0
        while pointer < len(combined):
            next_pointer = min(pointer + self._chunk_size, len(combined))
            chunks.append(combined[pointer:next_pointer])
            pointer = next_pointer
        return chunks or [combined]

    @staticmethod
    def _deduplicate(items: List[dict]) -> List[dict]:
        seen = set()
        unique: List[dict] = []
        for item in items:
            key = item.get("term", "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
