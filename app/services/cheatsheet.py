"""Agent-driven LaTeX cheat sheet generation with multi-agent orchestration."""
from __future__ import annotations

import asyncio
import json
import math
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


UNICODE_LATEX_MAP: dict[str, str] = {
    "Δ": r"\Delta",
    "δ": r"\delta",
    "Γ": r"\Gamma",
    "γ": r"\gamma",
    "Θ": r"\Theta",
    "θ": r"\theta",
    "Λ": r"\Lambda",
    "λ": r"\lambda",
    "Π": r"\Pi",
    "π": r"\pi",
    "Σ": r"\Sigma",
    "σ": r"\sigma",
    "Ω": r"\Omega",
    "ω": r"\omega",
    "×": r"\times",
    "·": r"\cdot",
    "±": r"\pm",
    "≤": r"\leq",
    "≥": r"\geq",
    "–": "--",
    "—": "---",
    "’": "'",
    "“": "``",
    "”": "''",
    "…": r"\ldots",
}


class CheatSheetBuilder:
    """Coordinate specialised agents to produce a dense LaTeX cheat sheet."""

    def __init__(self, vector_search=None, web_search=None) -> None:
        self._vector_search = vector_search
        self._web_search = web_search
        self._generation_crew = Crew(agents=[cheatsheet_agent], tasks=[cheatsheet_task], verbose=False)
        self._aggregator_crew = Crew(agents=[cheatsheet_aggregator_agent], tasks=[cheatsheet_aggregator_task], verbose=False)
        self._template = self._latex_template()
        self._base_guidelines = self._base_guidelines_text()

    async def build(
        self,
        cards: Iterable[Flashcard],
        key_terms: Optional[List[dict]] = None,
        documents: Optional[Iterable[DocumentBundle]] = None,
    ) -> str:
        cards = list(cards)
        if not cards:
            raise ValueError("No flashcards available for cheat sheet generation.")

        cards_sorted = sorted(cards, key=lambda c: (c.difficulty or 0.0), reverse=True)
        supplementary = self._supplementary_notes(key_terms or [], list(documents or []))

        chunks = [chunk for chunk in self._split_into_thirds(cards_sorted) if chunk]
        if not chunks:
            raise ValueError("No flashcard chunks available for cheatsheet generation.")
        variant_snippets: List[dict] = []
        for idx, chunk in enumerate(chunks, start=1):
            payload = self._build_chunk_payload(chunk, supplementary, idx)
            snippet = await self._generate_variant(payload, idx)
            variant_snippets.append({"name": f"Chunk {idx}", "latex": snippet})

        merged_snippet = await self._aggregate_variants(variant_snippets)
        return self._wrap_with_template(merged_snippet)

    @staticmethod
    def save(content: str, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    async def _generate_variant(self, payload: dict, index: int) -> str:
        attempt_payload = payload
        last = ""
        for attempt in range(3):
            result = await asyncio.to_thread(
                self._generation_crew.kickoff,
                {"flashcards": json.dumps(attempt_payload, indent=2)},
            )
            latex = self._sanitize_output(str(getattr(result, "output", result)).strip())
            if latex:
                last = latex
            if self._snippet_has_content(latex):
                return latex
            attempt_payload = self._reinforce_guidelines(attempt_payload, attempt + 1)
        if not last:
            raise RuntimeError(f"Chunk {index} agent returned empty output")
        return last

    async def _aggregate_variants(self, variants: List[dict]) -> str:
        queue = variants[:]
        if not queue:
            raise RuntimeError("No variant snippets to aggregate")
        while len(queue) > 1:
            first = queue.pop(0)
            second = queue.pop(0)
            payload = {
                "template": self._template_prompt_hint(),
                "pair": [first, second],
                "guidelines": self._base_guidelines,
            }
            result = await asyncio.to_thread(
                self._aggregator_crew.kickoff,
                {"flashcards": json.dumps(payload, indent=2)},
            )
            snippet = self._sanitize_output(str(getattr(result, "output", result)).strip())
            if not snippet:
                raise RuntimeError("Aggregator returned empty LaTeX snippet")
            queue.append({"name": f"merge({first['name']}+{second['name']})", "latex": snippet})
        return queue[0]["latex"]

    def _build_chunk_payload(self, cards: List[Flashcard], supplementary: List[dict], index: int) -> dict:
        topics = self._group_cards_by_primary_tag(cards)
        return {
            "template": self._template_prompt_hint(),
            "topics": topics,
            "supplementary_notes": supplementary,
            "guidelines": self._base_guidelines
            + [
                f"Chunk {index}: focus on the provided cards only, using their bullet_points to expand content as required.",
                "Return only LaTeX snippets (no preamble) so they can be combined later.",
            ],
        }

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
                        context.append(snippet[:320])
                        break
            if not context and self._web_search:
                summary = self._web_search(f"{name} exam essentials concise")
                if summary:
                    context.append(summary[:320])
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

    def _group_cards_by_primary_tag(self, cards: List[Flashcard]) -> List[dict]:
        grouped: dict[str, List[Flashcard]] = {}
        for card in cards:
            tags = card.tags or ["general"]
            label = self._format_tag(tags[0])
            grouped.setdefault(label, []).append(card)

        topics: List[dict] = []
        for label, members in sorted(grouped.items()):
            topic_cards = []
            for card in members:
                topic_cards.append(
                    {
                        "term": card.front.strip(),
                        "definition": card.back.strip(),
                        "bullet_points": self._split_definition(card.back),
                        "raw_tags": card.tags,
                        "difficulty": card.difficulty or 0.0,
                    }
                )
            topics.append({"name": label, "cards": topic_cards})
        return topics

    def _split_into_thirds(self, cards: List[Flashcard]) -> List[List[Flashcard]]:
        if not cards:
            return []
        chunk_size = math.ceil(len(cards) / 3)
        slices = [cards[i : i + chunk_size] for i in range(0, len(cards), chunk_size)]
        while len(slices) < 3:
            slices.append([])
        return slices[:3]

    def _wrap_with_template(self, snippet: str) -> str:
        body = snippet.strip()
        if "\\begin{document}" in body:
            return body
        # Sanitise wrappers that agents sometimes reintroduce
        body = body.lstrip()
        while body.startswith("\\\\"):
            body = body[2:].lstrip()
        body = re.sub(r"(?:\\\\)?\\begin\{multicols\*\}\{\d+\}", "", body)
        body = body.lstrip()
        body = body.replace("\\end{multicols*}", "")
        body = body.replace("\\end{document}", "")
        return "\n".join([
            self._template,
            body,
            r"\end{multicols*}",
            r"\end{document}",
        ])

    def _sanitize_output(self, text: str) -> str:
        if not text:
            return text
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```[a-zA-Z]*\n", "", stripped)
            stripped = stripped.rstrip('`')
            stripped = stripped.replace("```", "")
        sanitised = re.sub(r"(?<!\\)&", r"\\&", stripped)
        protected = self._protect_texttt_literals(sanitised)
        return self._replace_unicode_symbols(protected)

    def _protect_texttt_literals(self, latex: str) -> str:
        """Escape control sequences that appear inside ``\texttt`` blocks."""

        def _repl(match: re.Match) -> str:
            content = match.group(1)
            # Avoid double escaping sequences that are already handled.
            escaped = re.sub(r"\\(?!textbackslash\b)", r"\\textbackslash ", content)
            escaped = escaped.replace("{", r"\{").replace("}", r"\}")
            return rf"\texttt{{{escaped}}}"

        return re.sub(r"\\texttt\{([^{}]*)\}", _repl, latex)

    def _replace_unicode_symbols(self, latex: str) -> str:
        """Map common Unicode characters to LaTeX-safe sequences."""

        def _translate(segment: str) -> str:
            for char, replacement in UNICODE_LATEX_MAP.items():
                segment = segment.replace(char, replacement)
            return segment

        pieces: List[str] = []
        last = 0
        for match in re.finditer(r"\\texttt\{[^{}]*\}", latex):
            pieces.append(_translate(latex[last:match.start()]))
            pieces.append(match.group(0))
            last = match.end()
        pieces.append(_translate(latex[last:]))
        return "".join(pieces)

    def _snippet_has_content(self, snippet: str) -> bool:
        return bool(snippet and ("\\section" in snippet or "\\subsection" in snippet or "\\item" in snippet))

    def _reinforce_guidelines(self, payload: dict, attempt: int) -> dict:
        updated = json.loads(json.dumps(payload))
        guidelines = list(updated.get("guidelines", []))
        guidelines.append(
            f"Attempt {attempt}: Expand on the provided bullet_points, combine related items, and ensure the output can occupy a full column when assembled."
        )
        updated["guidelines"] = guidelines
        return updated

    def _latex_template(self) -> str:
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
        ])

    def _template_prompt_hint(self) -> str:
        """Return template text padded so CrewAI templating does not expand the document placeholder."""

        return self._template.replace("{", "{ ").replace("}", " }")

    def _base_guidelines_text(self) -> List[str]:
        return [
            "Use only the supplied flashcard content and supplementary notes.",
            "Organise material by topic headings and concise subsections.",
            "Keep bullet points tight and information-dense, preserving formulas and notation.",
            "Do not include meta-guidance or difficulty scores—subject matter only.",
            "Combine glossary entries and deduplicate overlapping bullets whenever possible.",
        ]

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
