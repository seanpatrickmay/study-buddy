"""Agent-driven LaTeX cheat sheet generation with multi-agent orchestration."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Iterable, List, Optional

from crewai import Crew

from app.agents.cheatsheet_agent import cheatsheet_agent, cheatsheet_task
from app.agents.cheatsheet_aggregator_agent import (
    cheatsheet_aggregator_agent,
    cheatsheet_aggregator_task,
)
from app.services.models import DocumentBundle, Flashcard


class CheatSheetBuilder:
    """Coordinate specialised agents to produce a dense LaTeX cheat sheet."""

    def __init__(self, vector_search=None, web_search=None) -> None:
        self._vector_search = vector_search
        self._web_search = web_search
        self._generation_crew = Crew(agents=[cheatsheet_agent], tasks=[cheatsheet_task], verbose=False)
        self._aggregator_crew = Crew(agents=[cheatsheet_aggregator_agent], tasks=[cheatsheet_aggregator_task], verbose=False)
        self._template = self._sample_document()
        self._base_guidelines = self._guidelines()

    async def build(
        self,
        cards: Iterable[Flashcard],
        key_terms: Optional[List[dict]] = None,
        documents: Optional[Iterable[DocumentBundle]] = None,
    ) -> str:
        cards = list(cards)
        base_payload = self._build_base_payload(cards, key_terms or [], list(documents or []))
        chunks = self._chunk_cards(base_payload["topics"], max_cards_per_chunk=15)
        variant_outputs = []
        for index, chunk in enumerate(chunks, start=1):
            chunk_payload = self._build_chunk_payload(base_payload, chunk, index)
            variant_latex = await self._generate_variant(chunk_payload, index)
            variant_outputs.append({"name": f"Chunk {index}", "latex": variant_latex})

        combined = await self._combine_variants(base_payload, variant_outputs)
        return combined

    @staticmethod
    def save(content: str, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _build_base_payload(
        self,
        cards: List[Flashcard],
        key_terms: List[dict],
        documents: List[DocumentBundle],
    ) -> dict:
        topics: List[dict] = []
        grouped: dict[str, List[Flashcard]] = {}
        for card in cards:
            tags = card.tags or ["general"]
            primary = self._format_tag(tags[0])
            grouped.setdefault(primary, []).append(card)

        for label, items in sorted(grouped.items()):
            topic_cards = []
            for card in items:
                topic_cards.append(
                    {
                        "term": card.front.strip(),
                        "definition": card.back.strip(),
                        "bullet_points": self._split_definition(card.back),
                        "raw_tags": card.tags,
                    }
                )
            topics.append({
                "name": label,
                "cards": topic_cards,
            })

        if not topics and cards:
            topics.append({
                "name": "General",
                "cards": [
                    {
                        "term": card.front.strip(),
                        "definition": card.back.strip(),
                        "bullet_points": self._split_definition(card.back),
                        "raw_tags": card.tags,
                    }
                    for card in cards
                ],
            })

        supplementary = self._supplementary_notes(key_terms, documents)

        return {
            "template": self._template,
            "topics": topics,
            "supplementary_notes": supplementary,
            "guidelines": self._base_guidelines,
        }

    def _build_chunk_payload(self, base_payload: dict, chunk_topics: List[dict], index: int) -> dict:
        payload = json.loads(json.dumps(base_payload))
        payload["chunk_index"] = index
        payload["topics"] = json.loads(json.dumps(chunk_topics))
        payload["guidelines"] = payload["guidelines"] + [
            f"Chunk {index}: ensure these topics fill the columns and retain all bullet_points provided."
        ]
        return payload

    async def _generate_variant(self, payload: dict, index: int) -> str:
        attempt_payload = payload
        last_latex = ""
        for attempt in range(3):
            result = await asyncio.to_thread(
                self._generation_crew.kickoff,
                {"flashcards": json.dumps(attempt_payload, indent=2)},
            )
            latex = self._sanitize_output(str(getattr(result, "output", result)).strip())
            if latex:
                last_latex = latex
            if self._looks_dense(latex, attempt_payload):
                return latex
            attempt_payload = self._reinforce_guidelines(attempt_payload, attempt + 1)
        if not last_latex:
            raise RuntimeError(f"Chunk {index} agent returned empty output")
        return last_latex

    async def _combine_variants(self, base_payload: dict, variants: List[dict]) -> str:
        queue = variants[:]
        while len(queue) > 1:
            first = queue.pop(0)
            second = queue.pop(0)
            combined = await self._aggregate_pair(base_payload, first, second)
            queue.append({"name": f"Merge({first['name']}+{second['name']})", "latex": combined})
        return queue[0]["latex"]

    async def _aggregate_pair(self, base_payload: dict, first: dict, second: dict) -> str:
        aggregator_payload = {
            "template": base_payload["template"],
            "pair": [first, second],
            "guidelines": base_payload["guidelines"],
            "topics": base_payload.get("topics", []),
        }
        result = await asyncio.to_thread(
            self._aggregator_crew.kickoff,
            {"flashcards": json.dumps(aggregator_payload, indent=2)},
        )
        latex = self._sanitize_output(str(getattr(result, "output", result)).strip())
        if not latex:
            raise RuntimeError("Aggregator returned empty LaTeX")
        return latex

    def _supplementary_notes(
        self,
        key_terms: List[dict],
        documents: List[DocumentBundle],
        max_notes: int = 6,
    ) -> List[dict]:
        notes: List[dict] = []
        for term in key_terms:
            name = (term.get("term") or term.get("name") or "").strip()
            if not name:
                continue
            context: List[str] = []
            if self._vector_search:
                try:
                    docs = self._vector_search(name, 1) or []
                except TypeError:
                    docs = self._vector_search(name, k=1)  # type: ignore[arg-type]
                for doc in docs or []:
                    snippet = getattr(doc, "page_content", "").strip()
                    if snippet:
                        context.append(snippet[:360])
                        break
            if not context and self._web_search:
                summary = self._web_search(f"{name} exam essentials concise")
                if summary:
                    context.append(summary[:360])
            if context:
                notes.append({"heading": name, "points": context})
            if len(notes) >= max_notes:
                break

        highlights = self._document_highlights(documents, max(4, max_notes - len(notes)))
        if highlights:
            notes.append({"heading": "Quick Reference", "points": highlights})
        return notes

    def _document_highlights(self, documents: List[DocumentBundle], limit: int) -> List[str]:
        highlights: List[str] = []
        for bundle in documents:
            for line in bundle.markdown.splitlines():
                stripped = line.strip("-• \u2022 ")
                if len(stripped) < 45:
                    continue
                highlights.append(stripped[:360])
                if len(highlights) >= limit:
                    return highlights
        return highlights

    def _guidelines(self) -> List[str]:
        return [
            "Group related concepts together; each topic should contain coherent subsections.",
            "Fill all three columns of the template. If space remains, expand on complex cards using provided bullet_points or supplementary notes.",
            "Include formulas, enumerations, and mnemonics where they appear in the source content.",
            "Supplementary notes must be cited inline (e.g., '(supplementary)').",
            "Never invent new facts; rely on card definitions or supplementary notes only.",
        ]

    def _chunk_cards(self, topics: List[dict], max_cards_per_chunk: int) -> List[List[dict]]:
        chunks: List[List[dict]] = []
        current_chunk: List[dict] = []
        current_count = 0
        for topic in topics:
            topic_card_count = len(topic.get("cards", []))
            if current_chunk and current_count + topic_card_count > max_cards_per_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_count = 0
            current_chunk.append(topic)
            current_count += topic_card_count
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _sample_document(self) -> str:
        return "\n".join([
            r"\documentclass[8pt]{extarticle}",
            r"\usepackage[a4paper,margin=0.7cm]{geometry}",
            r"\usepackage{multicol}",
            r"\usepackage{enumitem}",
            r"\setlength{\parindent}{0pt}",
            r"\setlist[itemize]{leftmargin=*}",
            r"\begin{document}",
            r"\pagestyle{empty}",
            r"\begin{multicols*}{3}",
            r"\section*{High Yield Concepts}",
            r"\subsection*{Example Heading}",
            r"\begin{itemize}[noitemsep]\small",
            r"  \item Definition and key formula.",
            r"  \item Critical insight or checklist.",
            r"\end{itemize}",
            r"\section*{Quick Reference}",
            r"\begin{itemize}[noitemsep]\small",
            r"  \item Important constant.",
            r"  \item Process overview.",
            r"\end{itemize}",
            r"\section*{Glossary}",
            r"\begin{itemize}[noitemsep]\small",
            r"  \item $\alpha$ \textemdash meaning.",
            r"  \item $\beta$ \textemdash usage.",
            r"\end{itemize}",
            r"\end{multicols*}",
            r"\end{document}",
        ])

    def _sanitize_output(self, text: str) -> str:
        escaped = re.sub(r"(?<!\\)&", r"\\&", text)
        return escaped

    def _looks_dense(self, latex: str, payload: dict) -> bool:
        if "\\begin{document}" not in latex:
            return False
        card_count = sum(len(topic.get("cards", [])) for topic in payload.get("topics", []))
        topic_count = len(payload.get("topics", []))
        length_threshold = max(2200, card_count * 45)
        section_count = latex.count("\\section*")
        column_indicator = latex.count("multicols*")
        return (
            len(latex) >= length_threshold
            and section_count >= max(topic_count, card_count // 2, 5)
            and column_indicator >= 1
        )

    def _reinforce_guidelines(self, payload: dict, attempt: int) -> dict:
        updated = json.loads(json.dumps(payload))
        guidelines = list(updated.get("guidelines", []))
        guidelines.append(
            f"Attempt {attempt}: Previous output left empty space. Expand explanations for advanced topics, add worked examples from the provided bullet_points, and ensure each topic fills its allocated column space."
        )
        updated["guidelines"] = guidelines
        return updated

    @staticmethod
    def _split_definition(text: str) -> List[str]:
        fragments: List[str] = []
        for sentence in re.split(r"(?<=[.!?;])\s+", text):
            cleaned = sentence.strip("-• \u2022 ")
            if cleaned:
                fragments.append(cleaned[:240])
        return fragments or [text[:240]]

    @staticmethod
    def _format_tag(tag: str) -> str:
        label = str(tag).strip().replace("_", " ").replace("-", " ")
        return label.title() if label else "General"
