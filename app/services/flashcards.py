"""Flashcard generation utilities."""
from __future__ import annotations

import re
from typing import Iterable, List

from app.services.models import DocumentBundle, Flashcard


class FlashcardGenerator:
    """Compose flashcards directly from the extraction agent notes."""

    def __init__(self) -> None:
        self._stopwords = {
            "summary",
            "introduction",
            "overview",
            "concept",
            "idea",
            "term",
            "information",
            "definition",
            "topic",
            "section",
        }

    async def generate(self, key_terms: Iterable[dict], documents: Iterable[DocumentBundle]) -> List[Flashcard]:
        documents = list(documents)
        combined_text = "\n".join(doc.markdown for doc in documents).lower()
        filtered_terms = self._filter_terms(key_terms, combined_text)
        cards = self._cards_from_terms(filtered_terms)
        return self._deduplicate(cards)

    def _cards_from_terms(self, key_terms: Iterable[dict]) -> List[Flashcard]:
        cards: List[Flashcard] = []
        for index, term in enumerate(key_terms, start=1):
            definition = (term.get("definition") or "").strip()
            term_name = (term.get("term") or "").strip()
            context = (term.get("context") or "").strip()
            difficulty = term.get("difficulty_score")
            if not term_name or not definition:
                continue

            front = term_name
            back = definition if not context else f"{definition}\n\nContext: {context}"

            tags = self._build_tags(context)
            tags.update({"study_buddy", "key_term"})

            cards.append(
                Flashcard(
                    front=front,
                    back=back,
                    tags=sorted(tags),
                    identifier=f"sb-{index:03d}",
                    difficulty=difficulty,
                )
            )
        return cards

    def _filter_terms(self, key_terms: Iterable[dict], combined_text: str) -> List[dict]:
        filtered: List[dict] = []
        for term in key_terms:
            name = (term.get("term") or "").strip()
            definition = (term.get("definition") or "").strip()
            if not name or not definition:
                continue
            if len(name) < 3 or len(definition) < 20:
                continue
            normalized = name.lower()
            if normalized in self._stopwords:
                continue
            if any(token.isdigit() for token in normalized.split()):
                continue
            if any(bad in definition.lower() for bad in {"not_found", "missing", "tbd", "n/a"}):
                continue
            pattern = re.compile(rf"\b{re.escape(normalized)}\b")
            if combined_text and not pattern.search(combined_text):
                continue
            filtered.append(term)
        return filtered

    def _build_tags(self, context: str) -> set[str]:
        if not context:
            return set()
        tokens = re.findall(r"[\w-]+", context.lower())
        tags = set()
        for token in tokens:
            clean = re.sub(r"[^a-z0-9_]", "", token.replace("-", "_")).strip("_")
            if not clean or clean in self._stopwords or len(clean) < 3:
                continue
            tags.add(clean)
            if len(tags) >= 4:
                break
        return tags

    @staticmethod
    def _deduplicate(cards: List[Flashcard]) -> List[Flashcard]:
        seen = set()
        unique: List[Flashcard] = []
        for card in cards:
            key = (card.front.lower(), card.back.lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(card)
        return unique
